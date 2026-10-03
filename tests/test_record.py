"""Tests de registro de impartición, progreso por unidad, feedback y memoria del agente."""

from datetime import date, timedelta
import pytest

from docente_ai.record.service import (
    add_feedback, add_progress, add_record, get_record, list_records, recent_experience,
)
from test_generation import corpus, FakeEmbedder, FakeGenerator, TEXT  # noqa: F401


# ── Fixtures ─────────────────────────────────────────────────────────────────

SESSION_DATE = date(2026, 9, 19)


def make_record(corpus, **kwargs):
    db = corpus[0]
    defaults = {'group_id': 'historia-3gp', 'session_date': SESSION_DATE,
                'duration_minutes': 50, 'topic': 'Pulso y acento'}
    return add_record(db, **{**defaults, **kwargs})


# ── CRUD básico ───────────────────────────────────────────────────────────────

def test_add_record_returns_complete_record(corpus):
    rec = make_record(corpus, notes='Buena asistencia')
    assert rec['id'].startswith('sr-')
    assert rec['group_id'] == 'historia-3gp'
    assert rec['session_date'] == SESSION_DATE.isoformat()
    assert rec['duration_minutes'] == 50
    assert rec['topic'] == 'Pulso y acento'
    assert rec['notes'] == 'Buena asistencia'
    assert rec['feedback'] is None
    assert rec['progress'] == []


def test_get_record_returns_same_data(corpus):
    db = corpus[0]
    rec = make_record(corpus)
    fetched = get_record(db, rec['id'])
    assert fetched['id'] == rec['id']
    assert fetched['topic'] == rec['topic']


def test_add_record_with_linked_run(corpus):
    from docente_ai.generation.service import ask, list_runs
    db, _, rag, settings = corpus
    result = ask(db, rag, settings, '¿Qué es el pulso?', subject='historia-i',
                 embedder_factory=FakeEmbedder, generator_factory=FakeGenerator)
    run_id = result['id']
    rec = make_record(corpus, run_id=run_id)
    assert rec['run_id'] == run_id


def test_add_record_invalid_run_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='generativo'):
        add_record(db, 'historia-3gp', SESSION_DATE, 50, 'Pulso', run_id='run-inexistente')


def test_add_record_invalid_group_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='inexistente'):
        add_record(db, 'grupo-que-no-existe', SESSION_DATE, 50, 'Pulso')


def test_add_record_empty_topic_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='tema'):
        add_record(db, 'historia-3gp', SESSION_DATE, 50, '   ')


def test_add_record_invalid_duration_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='duración'):
        add_record(db, 'historia-3gp', SESSION_DATE, 0, 'Pulso')


# ── Progreso de unidad ────────────────────────────────────────────────────────

def test_add_progress_attaches_to_record(corpus):
    db = corpus[0]
    rec = make_record(corpus)
    updated = add_progress(db, rec['id'], 'unidad-1', note='Completada la introducción.')
    assert any(p['unit_id'] == 'unidad-1' for p in updated['progress'])
    assert updated['progress'][0]['progress_note'] == 'Completada la introducción.'


def test_add_progress_idempotent_on_same_unit(corpus):
    db = corpus[0]
    rec = make_record(corpus)
    add_progress(db, rec['id'], 'unidad-1', note='Primera nota.')
    updated = add_progress(db, rec['id'], 'unidad-1', note='Nota actualizada.')
    units = [p for p in updated['progress'] if p['unit_id'] == 'unidad-1']
    assert len(units) == 1
    assert units[0]['progress_note'] == 'Nota actualizada.'


def test_add_progress_unknown_record_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='inexistente'):
        add_progress(db, 'sr-inexistente', 'unidad-1')


# ── Feedback ──────────────────────────────────────────────────────────────────

def test_add_feedback_stores_and_retrieves(corpus):
    db = corpus[0]
    rec = make_record(corpus)
    updated = add_feedback(db, rec['id'], what_worked='Buena participación',
                           what_failed='Faltó tiempo', next_session_note='Continuar con acento')
    fb = updated['feedback']
    assert fb is not None
    assert fb['what_worked'] == 'Buena participación'
    assert fb['what_failed'] == 'Faltó tiempo'
    assert fb['next_session_note'] == 'Continuar con acento'
    assert fb['created_at']


def test_add_feedback_overwrites_previous(corpus):
    db = corpus[0]
    rec = make_record(corpus)
    add_feedback(db, rec['id'], what_worked='Bien en general')
    updated = add_feedback(db, rec['id'], what_worked='Mejor de lo esperado', what_failed='Ruido')
    fb = updated['feedback']
    assert fb['what_worked'] == 'Mejor de lo esperado'
    assert fb['what_failed'] == 'Ruido'


def test_add_feedback_unknown_record_raises(corpus):
    db = corpus[0]
    with pytest.raises(ValueError, match='inexistente'):
        add_feedback(db, 'sr-inexistente', what_worked='OK')


# ── list_records ──────────────────────────────────────────────────────────────

def test_list_records_returns_group_records_only(corpus):
    db = corpus[0]
    make_record(corpus, topic='Sesión 1')
    make_record(corpus, topic='Sesión 2', session_date=SESSION_DATE + timedelta(days=7))
    items = list_records(db, 'historia-3gp')
    assert len(items) == 2
    # Orden descendente por fecha
    assert items[0]['session_date'] >= items[1]['session_date']


def test_list_records_empty_group_returns_empty(corpus):
    db = corpus[0]
    assert list_records(db, 'grupo-sin-registros') == []


def test_list_records_limit(corpus):
    db = corpus[0]
    for i in range(5):
        make_record(corpus, topic=f'Sesión {i}', session_date=SESSION_DATE + timedelta(days=i))
    assert len(list_records(db, 'historia-3gp', limit=3)) == 3


# ── recent_experience ─────────────────────────────────────────────────────────

def test_recent_experience_returns_compact_summary(corpus):
    db = corpus[0]
    rec = make_record(corpus, topic='Pulso y acento')
    add_feedback(db, rec['id'], what_worked='Bien', next_session_note='Pasar al ritmo')
    add_progress(db, rec['id'], 'unidad-1')
    experience = recent_experience(db, 'historia-3gp')
    assert len(experience) == 1
    exp = experience[0]
    assert exp['topic'] == 'Pulso y acento'
    assert exp['date'] == SESSION_DATE.isoformat()
    assert 'unidad-1' in exp['units_advanced']
    assert exp['feedback']['what_worked'] == 'Bien'
    assert exp['feedback']['next_session_note'] == 'Pasar al ritmo'


def test_recent_experience_empty_when_no_records(corpus):
    db = corpus[0]
    assert recent_experience(db, 'historia-3gp') == []


def test_recent_experience_respects_limit(corpus):
    db = corpus[0]
    for i in range(5):
        make_record(corpus, topic=f'Sesión {i}', session_date=SESSION_DATE + timedelta(days=i))
    assert len(recent_experience(db, 'historia-3gp', limit=2)) == 2


# ── Integración con el contexto pedagógico ─────────────────────────────────────

def test_context_for_includes_prior_experience_when_records_exist(corpus):
    from docente_ai.agents.pedagogy import context_for
    db = corpus[0]
    make_record(corpus, topic='Pulso básico')
    ctx = context_for(db, 'historia-3gp', 30)
    assert ctx['prior_experience'] is not None
    assert len(ctx['prior_experience']) == 1
    assert ctx['prior_experience'][0]['topic'] == 'Pulso básico'


def test_context_for_prior_experience_null_when_no_records(corpus):
    from docente_ai.agents.pedagogy import context_for
    db = corpus[0]
    ctx = context_for(db, 'historia-3gp', 30)
    assert ctx['prior_experience'] is None
