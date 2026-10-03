"""Verificar una propuesta mediante la API de la interfaz en el espacio sintético."""
import json
from pathlib import Path
import re
import time
import httpx

base='http://127.0.0.1:8766'
with httpx.Client(base_url=base,timeout=10,trust_env=False) as client:
    html=client.get('/').text
    token=re.search(r'name="docente-token" content="([^"]+)"',html).group(1)
    client.headers['X-Docente-Token']=token
    state=client.get('/api/state').json()
    assert state['knowledge_path'].endswith('data/verification/ui-workspace/Conocimiento'), 'Utiliza el servidor sintético en el puerto 8766.'
    start=time.monotonic()
    response=client.post('/api/generate',json={'mode':'pedagogy','group':'historia-3gp','duration':30,
        'question':'Practicar el pulso regular alternando palmas y silencios.',
        'criteria':'Instrucciones breves y una comprobación final del aprendizaje.'})
    response.raise_for_status()
    job_id=response.json()['job_id']
    while time.monotonic()-start<300:
        job=next(j for j in client.get('/api/jobs').json() if j['id']==job_id)
        if job['status'] in ('done','failed'):
            break
        time.sleep(2)
    assert job['status']=='done',job
    run=client.get('/api/runs/'+job['result']['run_id']).json()
    assert run['status']=='draft',run
    assert sum(a['minutes'] for a in run['result']['plan']['activities'])==30
    report={'passed':True,'seconds':round(time.monotonic()-start,2),'run_id':run['id'],
            'checks':['Propuesta por API gráfica','Citas literales comprobadas por el servidor','Suma exacta de 30 minutos'],
            'corpus':'Sintético, aislado de la biblioteca personal'}
    Path('data/verification/ui-smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
