"""Consulta de programación, sin inferir progreso ni imponer secuencias."""

from datetime import date


def show_curriculum(config: dict, group_id: str, on_date: date | None = None) -> dict:
    group = next((group for group in config['groups'] if group['id'] == group_id), None)
    if group is None:
        raise ValueError(f'Grupo inexistente: {group_id}.')
    binding = next((item for item in config['group_curricula'] if item['group_id'] == group_id), None)
    if binding is None:
        return {'group_id': group_id, 'curriculum': None, 'units': [], 'suggested_units': [],
                'note': 'Este grupo todavía no tiene programación asociada.'}
    curriculum = next(item for item in config['curricula'] if item['id'] == binding['curriculum_id'])
    units = sorted((item for item in config['curriculum_units'] if item['curriculum_id'] == curriculum['id']), key=lambda unit: unit['order'])
    selected = [] if on_date is None else [unit['id'] for unit in units if unit.get('start_date', '9999-12-31') <= on_date.isoformat() <= unit.get('end_date', '0001-01-01')]
    return {'group_id': group_id, 'curriculum': curriculum, 'units': units,
            'suggested_units': selected,
            'note': 'La temporalización sugiere unidades; el profesor elige. No se conoce aún qué contenidos se han impartido.'}
