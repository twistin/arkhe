"""Interfaz local: autorización, archivos, aislamiento y recorridos reales sin red."""

from pathlib import Path
import re
from threading import Event

import pytest
from starlette.testclient import TestClient

from docente_ai.config import load
from docente_ai.generation.service import ask
from docente_ai.storage import import_config, read_config
from docente_ai.web.app import create_app
from docente_ai.web.workspace import Workspace, daily_agenda
from test_generation import FakeEmbedder, FakeGenerator, TEXT, EXAMPLE


@pytest.fixture
def web(tmp_path):
    import_config(tmp_path/'data/docente.sqlite3', load(EXAMPLE))
    config=tmp_path/'config'
    config.mkdir()
    (config/'rag.yaml').write_text('schema_version: 1\nembeddings:\n  model: embed:1\n')
    for name in ('generation', 'pedagogy'):
        (config/f'{name}.yaml').write_text('schema_version: 1\ngeneration:\n  model: gen:1\n  num_ctx: 6144\n  max_output_tokens: 1536\n')
    def fake_ask(*args, **kwargs):
        return ask(*args, **kwargs, embedder_factory=FakeEmbedder, generator_factory=FakeGenerator)
    ws=Workspace(tmp_path, embedder_factory=FakeEmbedder, ask_function=fake_ask)
    app=create_app(tmp_path, workspace=ws)
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        html=client.get('/').text
        token=re.search(r'name="docente-token" content="([^"]+)"',html).group(1)
        client.headers['X-Docente-Token']=token
        yield client,ws


def test_api_no_devuelve_credenciales_y_permite_borrado(web, monkeypatch):
    from docente_ai.secrets import get_secret
    client, ws = web
    key = 'sk-' + 'B' * 32
    monkeypatch.setattr('docente_ai.web.workspace.httpx.Client', lambda **kwargs: (_ for _ in ()).throw(ValueError('Sin red')))
    response = client.post('/api/models', json={'provider': 'deepseek', 'generation': 'deepseek-chat', 'api_key': key})
    assert response.status_code == 200, response.text
    assert key not in response.text
    for name in ('generation', 'pedagogy'):
        assert key not in (ws.root / f'config/{name}.yaml').read_text()
    state = client.get('/api/state')
    assert state.json()['api_key_configured'] is True
    assert key not in state.text
    status = ws.model_status()
    assert status['api_key_configured'] is True
    assert key not in str(status)
    assert get_secret('deepseek_api_key') == key
    response = client.post('/api/models', json={'provider': 'deepseek', 'api_key': ''})
    assert response.status_code == 200
    assert get_secret('deepseek_api_key') == key
    response = client.delete('/api/secrets/deepseek', headers={'X-Docente-Token': 'invalido'})
    assert response.status_code == 403
    assert get_secret('deepseek_api_key') == key
    response = client.delete('/api/secrets/deepseek')
    assert response.status_code == 200 and response.json()['api_key_configured'] is False
    assert get_secret('deepseek_api_key') is None
    monkeypatch.setenv('DOCENTE_AI_DEEPSEEK_API_KEY', key)
    response = client.delete('/api/secrets/deepseek')
    assert response.json()['api_key_configured'] is True
    assert key not in response.text


def test_stats_api_y_bloque_ajustes(web):
    client, _ = web
    response = client.get('/api/runs/stats?limit=20')
    assert response.status_code == 200 and response.json()['total'] == 0
    assert response.json()['limit'] == 20
    assert client.get('/api/runs/stats?limit=0').status_code == 400
    assert client.get('/api/state').json()['run_stats']['limit'] == 100
    assert 'Calidad de generación' in client.get('/assets/js/vistas/ajustes.js').text


def wait(ws):
    ws.pool.submit(lambda: None).result(timeout=5)
    return ws.job_list()[-1]


def add(web, text=TEXT, name='fuente.txt'):
    client,ws=web
    stored=client.post('/api/upload',params={'name':name},content=text).json()
    response=client.post('/api/import',json={'path':stored['path'],'category':'documental','subject':'historia-i'})
    assert response.status_code==202
    job=wait(ws)
    assert job['status']=='done',job
    doc_id=job['result']['document_id']
    source=client.get('/api/documents/'+doc_id).json()['versions'][-1]['source_path']
    return doc_id,str(Path(source).relative_to(ws.knowledge))


def test_shell_local_assets_and_empty_state(web):
    client,ws=web
    response=client.get('/')
    assert response.status_code==200
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    directives = dict(part.strip().split(' ', 1) for part in response.headers['content-security-policy'].split(';'))
    assert directives['script-src'] == "'self'"
    assert client.get('/assets/js/main.js').headers['cache-control'] == 'no-store'
    assert client.get('/assets/js/main.js').status_code==200
    assert client.get('/assets/style.css').status_code==200
    state=client.get('/api/state').json()
    assert state['documents']==[] and state['runs']==[]
    assert state['config']['subjects'][0]['id']=='historia-i'
    assert (ws.knowledge/'01 Fuentes/historia-i').is_dir()
    assert (ws.knowledge/'02 Material docente/historia-i').is_dir()
    assert (ws.knowledge/'_LEEME.md').is_file()
    assert 'agenda' in state
    assert 'dailyAgenda' in client.get('/assets/js/componentes/agenda.js').text
    assert 'Material para el alumnado' in client.get('/assets/js/componentes/material-alumnado.js').text


def test_daily_agenda_and_proposal_keep_scheduled_session(web):
    from datetime import date
    client, ws = web
    agenda = daily_agenda(read_config(ws.db), date(2026, 9, 7))
    assert agenda['date'] == '2026-09-07'
    assert agenda['sessions'][0]['group_id'] == 'historia-3gp'
    assert agenda['sessions'][0]['duration_minutes'] == 60

    captured = {}
    def capture(*args, **kwargs):
        captured.update(kwargs)
        return {'id': 'run-scheduled', 'status': 'draft'}
    ws.ask_function = capture
    result = ws.generate({'mode': 'pedagogy', 'group': 'historia-3gp', 'duration': 60,
                          'session_date': '2026-09-07', 'question': 'El pulso'})
    assert result['run_id'] == 'run-scheduled'
    assert captured['pedagogy_context']['session']['date'] == '2026-09-07'


def test_upload_review_prepare_ask_and_exclude(web):
    client,ws=web
    doc,path=add(web)
    state=client.get('/api/state').json()
    assert state['documents'][0]['enabled'] is False
    assert client.get('/api/documents/'+doc).json()['segments'][0]['text']==TEXT
    assert client.get('/api/inbox').json()['files'][0]['imported'] is True
    assert client.post('/api/documents/'+doc+'/authorize',json={}).status_code==202
    assert wait(ws)['status']=='done'
    assert client.get('/api/state').json()['documents'][0]['indexed'] is True
    response=client.post('/api/generate',json={'mode':'ask','subject':'historia-i','question':'¿Qué es el pulso?'})
    assert response.status_code==202
    result=wait(ws)
    assert result['status']=='done',result
    run_id=result['result']['run_id']
    run=client.get('/api/runs/'+run_id).json()
    assert run['status']=='draft'
    assert 'messages' not in run and 'raw_response' not in run
    download=client.get('/api/runs/'+run_id+'?download=1')
    assert download.status_code==200 and TEXT in download.text
    assert 'attachment' in download.headers['content-disposition']
    sources=client.get('/api/runs/'+run_id+'?sources=1')
    assert sources.status_code==200 and 'Anexo documental' in sources.text and TEXT in sources.text
    assert 'anexo-fuentes-' in sources.headers['content-disposition']
    assert client.post('/api/documents/'+doc+'/exclude',json={}).status_code==200
    assert client.get('/api/state').json()['documents'][0]['enabled'] is False
    assert client.get('/api/runs/'+run_id).json()['warnings']


@pytest.mark.parametrize('headers', [{'X-Docente-Token':''}, {'X-Docente-Token':'wrong'},
    {'Origin':'https://evil.test'}, {'Host':'evil.test:8765'}, {'Origin':'null'}])
def test_cross_origin_and_missing_token_rejected(web,headers):
    client,_=web
    assert client.post('/api/subjects',json={'name':'No permitido'},headers=headers).status_code==403


@pytest.mark.parametrize('name',['../secret.txt','a/b.md','a\\b.md','program.py','test.exe','', 'a\x00.txt'])
def test_upload_invalid_paths_and_formats(web,name):
    client,_=web
    assert client.post('/api/upload',params={'name':name},content='example').status_code==400


def test_upload_empty_and_no_overwrite(web):
    client,ws=web
    assert client.post('/api/upload',params={'name':'empty.txt'},content=b'').status_code==400
    first=client.post('/api/upload',params={'name':'test.txt'},content='first').json()
    second=client.post('/api/upload',params={'name':'test.txt'},content='second').json()
    assert first['path']!=second['path']
    assert (ws.knowledge/first['path']).read_text()=='first'
    assert not list((ws.knowledge/'00 Entrada').glob('.upload-*'))


def test_folder_scan_path_boundary_and_versions(web,tmp_path):
    client,ws=web
    doc,path=add(web)
    (ws.knowledge/path).write_text(TEXT+' Otro contenido.')
    item=client.get('/api/inbox').json()['files'][0]
    assert item['imported'] is False and item['document_id']==doc
    client.post('/api/import',json={'path':path,'document_id':doc})
    assert wait(ws)['status']=='done'
    assert len(client.get('/api/documents/'+doc).json()['versions'])==2
    outside=tmp_path/'outside.txt';outside.write_text('private')
    (ws.knowledge/'link.txt').symlink_to(outside)
    assert all(f['name']!='link.txt' for f in client.get('/api/inbox').json()['files'])
    for path in ('../outside.txt',str(outside),'link.txt'):
        assert client.post('/api/import',json={'path':path}).status_code==400


def test_import_failure_and_jobs_are_visible(web):
    client,ws=web
    stored=client.post('/api/upload',params={'name':'unknown.txt'},content=TEXT).json()
    client.post('/api/import',json={'path':stored['path'],'subject':'missing','category':'documental'})
    assert wait(ws)['status']=='failed'
    assert client.get('/api/jobs').json()[-1]['error']


def test_settings_subject_and_group_preserve_existing_configuration(web):
    client,ws=web
    before=read_config(ws.db)
    response=client.post('/api/subjects',json={'name':'Acústica musical'})
    assert response.status_code==200
    subject=response.json()['id']
    assert (ws.knowledge/'01 Fuentes'/subject).is_dir()
    assert client.post('/api/subjects',json={'id':subject,'name':'Acústica'}).status_code==200
    assert client.post('/api/groups',json={'name':'Grupo B','level':'2º ESO','subject':subject,'center':'Centro elegido',
        'teacher':'Docente de prueba','year':2026,'language':'gl'}).status_code==200
    after=read_config(ws.db)
    assert after['schedule_rules']==before['schedule_rules']
    assert len(after['groups'])==len(before['groups'])+1
    assert client.post('/api/groups',json={'name':'Grupo','level':'GP','subject':'missing','center':'Centro',
        'teacher':'Docente','year':2026}).status_code==400
    assert read_config(ws.db)==after


def test_metadata_and_subject_isolation(web):
    client,ws=web
    doc,_=add(web)
    assert client.post('/api/documents/'+doc+'/metadata',json={'title':'Pulso','authors':['Autora de prueba'],'year':2026,'subject':'historia-i'}).status_code==200
    item=client.get('/api/documents/'+doc).json()
    assert item['metadata']['authors']==['Autora de prueba']
    assert client.post('/api/documents/'+doc+'/metadata',json={'title':'No cambia','subject':'missing'}).status_code==400
    assert client.get('/api/documents/'+doc).json()['metadata']['title']=='Pulso'


def test_queue_serializes_expensive_operations(web):
    _,ws=web
    entered,release=Event(),Event()
    def task():
        entered.set()
        assert release.wait(5)
        return {'ok':True}
    ws.submit('one',task)
    assert entered.wait(2)
    try:
        ws.submit('two',lambda: {'ok':True})
        assert [j['status'] for j in ws.job_list()]==['running','queued']
    finally:
        release.set()
    assert wait(ws)['status']=='done'


def test_new_workspace_has_no_invented_teaching_data(tmp_path):
    ws=Workspace(tmp_path)
    try:
        assert not read_config(ws.db)['groups']
        assert not read_config(ws.db)['subjects']
    finally:
        ws.close()


def test_run_endpoint_includes_review_field(web):
    """El endpoint GET /api/runs/{id} debe incluir el campo review (null si no hay revisión)."""
    client,ws=web
    doc,_=add(web)
    client.post('/api/documents/'+doc+'/authorize',json={})
    wait(ws)
    client.post('/api/generate',json={'mode':'ask','subject':'historia-i','question':'¿Qué es el pulso?'})
    result=wait(ws)
    run_id=result['result']['run_id']
    run=client.get('/api/runs/'+run_id).json()
    assert 'review' in run
    assert run['review'] is None


def test_approve_run_via_api(web):
    """POST /api/runs/{id}/review con action=approved guarda la revisión."""
    client,ws=web
    doc,_=add(web)
    client.post('/api/documents/'+doc+'/authorize',json={})
    wait(ws)
    client.post('/api/generate',json={'mode':'ask','subject':'historia-i','question':'¿Qué es el pulso?'})
    result=wait(ws)
    run_id=result['result']['run_id']
    response=client.post('/api/runs/'+run_id+'/review',json={'action':'approved','notes':'Revisada'})
    assert response.status_code==200
    data=response.json()
    assert data['review']['action']=='approved'
    assert data['review']['notes']=='Revisada'
    assert data['review']['approved_hash']


def test_reject_run_via_api(web):
    """POST /api/runs/{id}/review con action=rejected guarda el rechazo."""
    client,ws=web
    doc,_=add(web)
    client.post('/api/documents/'+doc+'/authorize',json={})
    wait(ws)
    client.post('/api/generate',json={'mode':'ask','subject':'historia-i','question':'¿Qué es el pulso?'})
    result=wait(ws)
    run_id=result['result']['run_id']
    response=client.post('/api/runs/'+run_id+'/review',json={'action':'rejected','notes':'Insuficiente'})
    assert response.status_code==200
    assert response.json()['review']['action']=='rejected'


def test_review_invalid_action_returns_400(web):
    """Acción desconocida en /review devuelve 400."""
    client,ws=web
    doc,_=add(web)
    client.post('/api/documents/'+doc+'/authorize',json={})
    wait(ws)
    client.post('/api/generate',json={'mode':'ask','subject':'historia-i','question':'¿Qué es el pulso?'})
    result=wait(ws)
    run_id=result['result']['run_id']
    assert client.post('/api/runs/'+run_id+'/review',json={'action':'pending'}).status_code==400


def test_uploaded_file_is_organized_and_original_can_be_downloaded(web):
    client,ws=web
    doc,path=add(web)
    assert path=='01 Fuentes/historia-i/fuente.txt'
    assert not list((ws.knowledge/'00 Entrada').iterdir())
    response=client.get('/api/documents/'+doc+'?download=1')
    assert response.status_code==200 and response.text==TEXT
    assert 'attachment' in response.headers['content-disposition']


def test_clear_year_and_edit_group(web):
    client,ws=web
    doc,_=add(web)
    for year in (2026,None):
        assert client.post('/api/documents/'+doc+'/metadata',json={'title':'Pulso','authors':[],'subject':'historia-i','year':year}).status_code==200
        assert client.get('/api/documents/'+doc).json()['metadata']['year']==year
    before=read_config(ws.db)
    assert client.post('/api/groups',json={'id':'historia-3gp','name':'Grupo revisado','level':'3º GP',
        'subject':'historia-i','center':'Conservatorio de ejemplo','teacher':'Profesor de ejemplo','year':2026,'language':'es'}).status_code==200
    after=read_config(ws.db)
    assert len(before['groups'])==len(after['groups'])
    assert after['groups'][0]['name']=='Grupo revisado'


def test_exclude_while_index_is_queued_cannot_reauthorize(web):
    client,ws=web
    doc,_=add(web)
    entered,release=Event(),Event()
    def hold():
        entered.set()
        assert release.wait(5)
    ws.submit('busy',hold)
    assert entered.wait(2)
    try:
        assert client.post('/api/documents/'+doc+'/authorize',json={}).status_code==202
        assert client.get('/api/documents/'+doc).json()['enabled'] is True
        assert client.post('/api/documents/'+doc+'/exclude',json={}).status_code==200
    finally:
        release.set()
    wait(ws)
    assert client.get('/api/documents/'+doc).json()['enabled'] is False
    assert client.get('/api/state').json()['documents'][0]['indexed'] is False


def test_model_preferences_preserve_other_settings(web,monkeypatch):
    from docente_ai.web import workspace as module
    from docente_ai.generation.settings import load_settings
    client,ws=web
    monkeypatch.setattr(module,'OllamaGenerator',FakeGenerator)
    assert client.post('/api/models',json={'generation':'gen:2','embeddings':'embed:2'}).status_code==200
    settings=load_settings(ws.root/'config/generation.yaml')
    assert settings.model=='gen:2' and settings.num_ctx==6144
    assert client.post('/api/models',json={'generation':'bad:cloud','embeddings':'embed:2'}).status_code==400
    assert load_settings(ws.root/'config/generation.yaml').model=='gen:2'


def test_tampered_original_is_not_downloaded(web):
    client,ws=web
    doc,_=add(web)
    data=client.get('/api/documents/'+doc).json()
    from docente_ai.library.service import original_file
    original=original_file(ws.db,data['versions'][0]['original_path'])
    original.chmod(0o600)
    original.write_text('changed')
    assert client.get('/api/documents/'+doc+'?download=1').status_code==400


@pytest.mark.parametrize("name", ["Un título bibliográfico extenso " * 7 + ".txt", "Á" * 180 + ".txt", "a" * 190 + ".txt"])
def test_upload_long_names_and_duplicates(web, name):
    client, ws = web
    paths = []
    for _ in range(2):
        response = client.post('/api/upload', params={'name': name}, content=TEXT)
        assert response.status_code == 200, response.text
        path = ws.knowledge / response.json()['path']
        assert path.read_text() == TEXT
        assert len(path.name.encode('utf-8')) <= 255
        paths.append(path)
    assert paths[0] != paths[1]


def test_duplicate_preparation_uses_same_job(web):
    _, ws = web
    release = Event()
    try:
        first = ws.submit('Preparar', lambda: release.wait(5), key='prepare:one')
        second = ws.submit('Preparar', lambda: None, key='prepare:one')
        assert first == second
        assert len(ws.job_list()) == 1
    finally:
        release.set()
        wait(ws)


# ── Fase 8: rutas de registro de impartición ──────────────────────────────────

def test_create_record_via_api(web):
    """POST /api/records crea un registro de sesión."""
    client,ws=web
    response=client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':'Pulso y acento'})
    assert response.status_code==200
    data=response.json()
    assert data['id'].startswith('sr-')
    assert data['topic']=='Pulso y acento'
    assert data['feedback'] is None


def test_get_record_via_api(web):
    """GET /api/records/{id} devuelve el registro completo."""
    client,ws=web
    rec=client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':'El ritmo'}).json()
    fetched=client.get('/api/records/'+rec['id']).json()
    assert fetched['id']==rec['id']
    assert fetched['topic']=='El ritmo'


def test_add_progress_via_api(web):
    """POST /api/records/{id}/progress añade progreso de unidad."""
    client,ws=web
    rec=client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':'Pulso'}).json()
    response=client.post('/api/records/'+rec['id']+'/progress',json={'unit_id':'unidad-1','note':'Introducción completada'})
    assert response.status_code==200
    assert any(p['unit_id']=='unidad-1' for p in response.json()['progress'])


def test_add_feedback_via_api(web):
    """POST /api/records/{id}/feedback guarda feedback del profesor."""
    client,ws=web
    rec=client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':'Pulso'}).json()
    response=client.post('/api/records/'+rec['id']+'/feedback',json={'what_worked':'Participación activa','what_failed':'Poco tiempo','next_session_note':'Continuar con acento'})
    assert response.status_code==200
    fb=response.json()['feedback']
    assert fb['what_worked']=='Participación activa'
    assert fb['next_session_note']=='Continuar con acento'


def test_list_group_records_via_api(web):
    """GET /api/groups/{id}/records devuelve historial del grupo."""
    client,ws=web
    client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':'Sesión A'})
    client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-26','duration_minutes':50,'topic':'Sesión B'})
    response=client.get('/api/groups/historia-3gp/records')
    assert response.status_code==200
    items=response.json()
    assert len(items)==2


def test_create_record_missing_topic_returns_400(web):
    """Crear registro sin tema devuelve 400."""
    client,ws=web
    response=client.post('/api/records',json={'group_id':'historia-3gp','session_date':'2026-09-19','duration_minutes':50,'topic':''})
    assert response.status_code==400


def test_export_calendar_ics_via_api(web):
    """GET /api/calendar.ics descarga el archivo iCalendar con avisos."""
    client,ws=web
    response=client.get('/api/calendar.ics')
    assert response.status_code==200
    assert response.headers['content-type'].startswith('text/calendar')
    assert 'attachment; filename="horario-docente.ics"' in response.headers['content-disposition']
    text=response.text
    assert 'BEGIN:VCALENDAR' in text
    assert 'BEGIN:VALARM' in text
    assert 'TRIGGER:-PT15M' in text
