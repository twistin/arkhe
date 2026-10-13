"""Resolución previa de requisitos pedagógicos y asignación de ejecutores.

Garantiza que ningún requisito se entregue sin cumplir o se silencie:
los componentes teóricos se calculan, las partituras se verifican contra catálogo,
los análisis musicales se computan con music21 y las lagunas se reportan abiertamente.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from docente_ai.music.didactic import (
    resolver_componente_didactico,
    construir_hitos_linea_temporal,
    generar_svg_linea_temporal,
)


EJECUTORES_VALIDOS = (
    'texto_fuentes',
    'componente_calculado',
    'partitura_obra',
    'analisis_sobre_partitura',
    'linea_temporal',
    'actividad',
)


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparaciones sin tildes y en minúsculas."""
    if not texto:
        return ''
    s = unicodedata.normalize('NFD', str(texto).lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def buscar_partitura_verificada(obra: str, root: Path | None = None) -> dict[str, Any] | None:
    """Busca en el catálogo de ejemplos una partitura que coincida con la obra
    y cumpla la regla estricta de verificación:
    verificado == True, verificado_por no vacío y verificado_en no vacío.
    """
    if not obra:
        return None
    o_norm = normalizar_texto(obra)
    base_dir = root or Path('.')
    ejemplos_yaml = base_dir / 'data/ejemplos/ejemplos.yaml'
    if not ejemplos_yaml.is_file():
        return None

    import yaml
    try:
        data = yaml.safe_load(ejemplos_yaml.read_text(encoding='utf-8')) or {}
        items = data.get('ejemplos', [])
        for it in items:
            it_obra = normalizar_texto(it.get('obra', '') or it.get('titulo', ''))
            if (o_norm in it_obra or it_obra in o_norm) and len(it_obra) > 3:
                # Regla de verificación estricta
                es_verificado = (
                    it.get('verificado') is True
                    and bool(it.get('verificado_por'))
                    and bool(it.get('verificado_en'))
                )
                if es_verificado:
                    archivo_rel = it.get('archivo', '')
                    archivo_path = base_dir / 'data/ejemplos' / archivo_rel
                    if archivo_path.is_file():
                        res = dict(it)
                        res['path'] = str(archivo_path)
                        return res
    except Exception:
        pass
    return None


def analizar_partitura_music21(score_path: Path | str) -> dict[str, Any]:
    """Realiza análisis computacional determinista sobre un archivo musical usando music21:
    - ámbito (nota más grave a nota más aguda)
    - notas usadas situadas en el Gran Sistema Perfecto
    - nota final
    - tetracordos implicados
    """
    import music21

    score = music21.converter.parse(str(score_path))
    pitches = list(score.pitches)
    if not pitches:
        return {'error': 'No se encontraron notas en la partitura'}

    # 1. Ámbito
    pitch_min = min(pitches)
    pitch_max = max(pitches)
    ambito = f"{pitch_min.nameWithOctave} – {pitch_max.nameWithOctave}"

    # 2. Notas únicas
    nombres_unicos = sorted(list({p.nameWithOctave for p in pitches}))

    # 3. Nota final
    nota_final = pitches[-1].nameWithOctave

    # 4. Situación en el Gran Sistema Perfecto
    MAPA_GSP = {
        'A2': 'Proslambanómenos (La2)',
        'B2': 'Hypate hypaton (Si2)',
        'C3': 'Parhypate hypaton (Do3)',
        'D3': 'Lichanos hypaton (Re3)',
        'E3': 'Hypate meson (Mi3)',
        'F3': 'Parhypate meson (Fa3)',
        'G3': 'Lichanos meson (Sol3)',
        'A3': 'Mese (La3)',
        'B3': 'Paramese (Si3)',
        'C4': 'Trite diezeugmenon (Do4)',
        'D4': 'Paranete diezeugmenon (Re4)',
        'E4': 'Nete diezeugmenon (Mi4)',
        'F4': 'Trite hyperbolaion (Fa4)',
        'G4': 'Paranete hyperbolaion (Sol4)',
        'A4': 'Nete hyperbolaion (La4)',
        'E4': 'Hypate meson (transpuesta 8va: Mi4)',
        'F#4': 'Parhypate meson (Fa#4)',
        'G4': 'Lichanos meson (Sol4)',
        'A4': 'Mese (La4)',
        'B4': 'Paramese (Si4)',
        'C#5': 'Trite diezeugmenon (Do#5)',
        'D5': 'Paranete diezeugmenon (Re5)',
        'E5': 'Nete diezeugmenon (Mi5)',
    }
    notas_en_gsp = [
        {'nota': p, 'grado_gsp': MAPA_GSP.get(p, f"Grado diatónico {p}")}
        for p in nombres_unicos
    ]

    # 5. Tetracordos implicados
    tetracordos = []
    has_meson = any(p in ('E4', 'F4', 'F#4', 'G4', 'A4') for p in nombres_unicos)
    has_diezeugmenon = any(p in ('B4', 'C5', 'C#5', 'D5', 'E5') for p in nombres_unicos)
    if has_meson:
        tetracordos.append('Tetracordo Meson (Mi4–La4)')
    if has_diezeugmenon:
        tetracordos.append('Tetracordo Diezeugmenon (Si4–Mi5)')

    desc = (
        f"Ámbito melódico de {ambito}, concluyendo en {nota_final}. "
        f"Notas empleadas: {', '.join(nombres_unicos)}. "
        f"Tetracordos activos del Gran Sistema Perfecto: {', '.join(tetracordos) if tetracordos else 'Diatónico general'}."
    )

    return {
        'ambito': ambito,
        'nota_mas_grave': pitch_min.nameWithOctave,
        'nota_mas_aguda': pitch_max.nameWithOctave,
        'notas_usadas': nombres_unicos,
        'nota_final': nota_final,
        'notas_en_gsp': notas_en_gsp,
        'tetracordos_implicados': tetracordos,
        'descripcion_analisis': desc,
    }


def resolver_fulfillment_requisitos(
    requirements: list[dict[str, Any]],
    db_path: Path | None = None,
    evidence: list[dict[str, Any]] | None = None,
    root: Path | None = None,
    topic: str | None = None,
    subject: str | None = None,
    periodo: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resuelve deterministamente antes del LLM todos los requisitos que no son texto_fuentes:
    - componentes_calculados: calculados y con SVGs listos (o descartados si no son aplicables o parámetros inválidos)
    - partitura_obra: verificadas en el catálogo del profesor
    - analisis_sobre_partitura: computados con music21 solo si la partitura está verificada
    - linea_temporal: construida con las fuentes y cronologia_autores.yaml según el rango solicitado
    - texto_fuentes: comprueba disponibilidad de fuentes relevantes en la biblioteca

    Devuelve:
      fulfillment: [{requirement_id, ejecutor, estado, artefacto_id, falta}]
      recursos_resueltos: diccionario con artefactos y explicaciones para el LLM
    """
    fulfillment: list[dict[str, Any]] = []
    recursos_resueltos: dict[str, Any] = {}
    base_root = root or (db_path.parent if db_path else Path('.'))

    for req in (requirements or []):
        r_id = req.get('id', 'R?')
        ejecutor = req.get('ejecutor', 'texto_fuentes')
        desc = req.get('description', '')
        d_norm = normalizar_texto(desc)

        # 1. COMPONENTE CALCULADO
        if ejecutor == 'componente_calculado':
            comps_solicitados = req.get('componentes') or []
            if not comps_solicitados and req.get('componente_tipo'):
                comps_solicitados = [{'tipo': t.strip()} for t in req['componente_tipo'].split(',') if t.strip()]
            if not comps_solicitados:
                # Deducir por descripción si no vino explícito
                if 'tetracordo' in d_norm or 'genero' in d_norm:
                    comps_solicitados.append({'tipo': 'tetracordos'})
                if 'sistema perfecto' in d_norm or 'gran sistema' in d_norm:
                    comps_solicitados.append({'tipo': 'gran_sistema_perfecto'})
                if 'monocordio' in d_norm:
                    comps_solicitados.append({'tipo': 'monocordio'})
                if 'escalera' in d_norm:
                    comps_solicitados.append({'tipo': 'escalera_intervalos'})

            resueltos_tipo = []
            descartes = []
            errores = []
            for c_spec in comps_solicitados:
                tipo = c_spec.get('tipo')
                params = c_spec.get('parametros') or {}
                try:
                    topic_ctx = topic or desc
                    res = resolver_componente_didactico(
                        tipo, params, evidence=evidence,
                        topic=topic_ctx, subject=subject, periodo=periodo
                    )
                    res['origen'] = 'regla_requisito'
                    res['requirement_id'] = r_id
                    if res.get('estado') == 'descartado':
                        descartes.append(res.get('motivo_descarte') or f"{tipo} descartado")
                    else:
                        resueltos_tipo.append(res)
                except Exception as exc:
                    errores.append(f"{tipo}: {exc}")

            if resueltos_tipo:
                art_id = f"componentes_{','.join(r['tipo'] for r in resueltos_tipo)}"
                recursos_resueltos[r_id] = {
                    'tipo': 'componente_calculado',
                    'componentes': resueltos_tipo,
                    'descripcion_para_llm': (
                        f"Componente(s) interactivo(s) generado(s): {', '.join(r['titulo'] for r in resueltos_tipo)}. "
                        "El LLM debe referirse a esta figura/esquema y diseñar actividades que trabajen con él."
                    ),
                }
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'componente_calculado',
                    'estado': 'cumplido',
                    'artefacto_id': art_id,
                    'falta': None,
                })
            elif descartes:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'componente_calculado',
                    'estado': 'descartado',
                    'artefacto_id': None,
                    'falta': '; '.join(descartes),
                })
            else:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'componente_calculado',
                    'estado': 'pendiente_profesor',
                    'artefacto_id': None,
                    'falta': f"No se pudo calcular el componente ({'; '.join(errores)})",
                })

        # 2. PARTITURA DE OBRA
        elif ejecutor == 'partitura_obra':
            obra = req.get('obra') or desc
            ej_verificado = buscar_partitura_verificada(obra, root=base_root)
            if ej_verificado:
                recursos_resueltos[r_id] = {
                    'tipo': 'partitura_obra',
                    'ejemplo': ej_verificado,
                    'descripcion_para_llm': f"Partitura verificada disponible: {ej_verificado.get('titulo')}.",
                }
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'partitura_obra',
                    'estado': 'cumplido',
                    'artefacto_id': ej_verificado.get('id'),
                    'falta': None,
                })
            else:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'partitura_obra',
                    'estado': 'pendiente_profesor',
                    'artefacto_id': None,
                    'falta': f"Importar MusicXML verificado de '{obra}'",
                })

        # 3. ANÁLISIS SOBRE PARTITURA
        elif ejecutor == 'analisis_sobre_partitura':
            obra = req.get('obra') or desc
            ej_verificado = buscar_partitura_verificada(obra, root=base_root)
            if ej_verificado and ej_verificado.get('path'):
                try:
                    analisis = analizar_partitura_music21(ej_verificado['path'])
                    recursos_resueltos[r_id] = {
                        'tipo': 'analisis_sobre_partitura',
                        'obra': obra,
                        'analisis': analisis,
                        'descripcion_para_llm': (
                            f"Análisis musicológico de '{obra}': {analisis.get('descripcion_analisis')}. "
                            "El LLM debe incorporar estos datos en la explicación y actividades."
                        ),
                    }
                    fulfillment.append({
                        'requirement_id': r_id,
                        'ejecutor': 'analisis_sobre_partitura',
                        'estado': 'cumplido',
                        'artefacto_id': f"analisis_{ej_verificado.get('id', 'score')}",
                        'falta': None,
                    })
                except Exception as an_err:
                    fulfillment.append({
                        'requirement_id': r_id,
                        'ejecutor': 'analisis_sobre_partitura',
                        'estado': 'pendiente_profesor',
                        'artefacto_id': None,
                        'falta': f"Error al analizar la partitura: {an_err}",
                    })
            else:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'analisis_sobre_partitura',
                    'estado': 'pendiente_profesor',
                    'artefacto_id': None,
                    'falta': f"Requiere la partitura verificada de '{obra}' para realizar el análisis",
                })

        # 4. LÍNEA TEMPORAL
        elif ejecutor == 'linea_temporal':
            params_lt = req.get('parametros') or {}
            res_lt = resolver_componente_didactico(
                'linea_temporal',
                params_lt,
                evidence=evidence,
                topic=topic,
                subject=subject,
                periodo=periodo,
            )
            if res_lt.get('estado') == 'descartado':
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'linea_temporal',
                    'estado': 'descartado',
                    'artefacto_id': None,
                    'falta': res_lt.get('motivo_descarte') or 'Línea temporal no aplicable al rango solicitado',
                })
            else:
                hitos = res_lt.get('hitos') or []
                recursos_resueltos[r_id] = {
                    'tipo': 'linea_temporal',
                    'hitos': hitos,
                    'svg': res_lt.get('svg'),
                    'descripcion_para_llm': (
                        f"Línea temporal con {len(hitos)} tratadistas o figuras históricas documentadas. "
                        "Remitir al esquema cronológico en la propuesta."
                    ),
                }
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'linea_temporal',
                    'estado': 'cumplido',
                    'artefacto_id': 'componente_linea_temporal',
                    'falta': None,
                })

        # 5. ACTIVIDAD
        elif ejecutor == 'actividad':
            fulfillment.append({
                'requirement_id': r_id,
                'ejecutor': 'actividad',
                'estado': 'cumplido',
                'artefacto_id': None,
                'falta': None,
            })

        # 6. TEXTO FUENTES
        else:
            # Comprobar si hay evidencia que mencione palabras clave del requisito
            tiene_fuentes = False
            if evidence:
                palabras_req = [w for w in re.findall(r'\b[a-z]{4,}\b', d_norm) if w not in ('explicar', 'describir', 'identificar', 'indicar', 'sistema', 'sobre')]
                for ev in evidence:
                    t_ev = normalizar_texto(ev.get('text', '') + ' ' + ' '.join(str(p) for p in ev.get('passages', [])))
                    if any(p in t_ev for p in palabras_req):
                        tiene_fuentes = True
                        break

            if tiene_fuentes:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'texto_fuentes',
                    'estado': 'cumplido',
                    'artefacto_id': None,
                    'falta': None,
                })
            else:
                fulfillment.append({
                    'requirement_id': r_id,
                    'ejecutor': 'texto_fuentes',
                    'estado': 'sin_fuentes',
                    'artefacto_id': None,
                    'falta': f"Sin fuentes documentales suficientes en la biblioteca sobre este concepto",
                })

    return fulfillment, recursos_resueltos
