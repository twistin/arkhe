# Encargo 04 · Generación en dos pasos: estructura y desarrollo

Lee `AGENTS.md` y cúmplelo. Este encargo parte de los encargos 01 (reparación por parche, métricas por etapa) y 03 (perfiles).

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

Hoy una sola llamada (`agents/pedagogy.py::build_prompt` → `generate_validated` en `generation/service.py::ask`) produce de golpe:

- de 4 a 6 secciones de teoría con citas literales,
- resúmenes para el alumnado,
- ejemplos musicales,
- plan con actividades y minutos,
- cobertura, esquemas y componentes.

Son unos 5.000 tokens de salida. El modelo dedica la atención a cumplir el esquema y las citas, el orden didáctico queda en segundo plano, y la guía resultante del caso Seikilos ocupa 5.368 palabras para 60 minutos. El profesor no ve nada hasta que termina todo.

## Diseño

1. **Paso 1: estructura.**
   - Mismo contexto y mismas fuentes que hoy.
   - Salida JSON pequeña, con esquema cerrado:
     - `objectives`,
     - `secciones`: `[{id, title, key_points (2-4), source_ids, requirement_ids}]`,
     - `actividades`: `[{id, title, grouping, minutes, section_ids, requirement_ids}]`,
     - `cobertura_prevista`: requisitos sin sección ni actividad, con el motivo.
   - Límites del perfil (encargo 03).
   - Validación determinista: ids únicos, `source_ids` existentes, todo requisito asignado o declarado y orden didáctico explícito.
   - Si los minutos no suman la duración, corrígelos por código: reparto proporcional, redondeo a 5 y ajuste final en la actividad más larga. No pidas una reparación al modelo por esto.
   - Emite la estructura con `emit_live('estructura', ...)` y muéstrala en la ventana de progreso de la propuesta en cuanto llegue, para que el profesor vea el esquema en segundos.
2. **Paso 2: desarrollo.**
   - Entrada: la estructura validada y solo los pasajes de sus `source_ids`, más la programación, que siempre se conserva.
   - Salida: el contrato actual (`claims` con `text`, `student_summary`, `evidence`; plan con `teacher_notes`, `student_task`, `deliverable`, `solution`…), con un elemento por sección y por actividad, en el mismo orden.
   - Títulos, minutos, agrupamientos y `requirement_ids` se toman siempre de la estructura y se imponen por código: si el modelo los cambia, prevalece la estructura y queda constancia en `warnings`.
   - El presupuesto de extensión sale del perfil, por ejemplo `historia` 60 min ≈ 1.800 palabras de guía sin contar citas. Un exceso se repara con un parche de la sección afectada (encargo 01), no regenerando todo.
3. **Persistencia y trazabilidad.**
   - Guarda la estructura en `result['estructura']`.
   - Guarda los dos diálogos en `record_prompt` (prompt y respuesta de cada paso).
   - Mantén `run_id` único, la cancelación entre pasos y dentro de cada uno, y los eventos SSE existentes.
   - Sube `PROMPT_VERSION` a `pedagogy:13`.
4. **Compatibilidad.**
   - El render (`generation/render.py`), el material del alumnado y la UI siguen recibiendo el mismo `result`.
   - Las propuestas antiguas, sin `estructura`, se abren igual.
   - La revisión opcional (`enable_review`) se aplica al resultado final como hoy.
5. **Abstención.** Si el paso 1 concluye que no hay base documental y el perfil no permite generar sin fuentes, termina en `abstained` sin ejecutar el paso 2.

## Tests

- Con un generador falso de dos respuestas: el flujo completo produce un `result` válido y renderizable, y quedan dos diálogos registrados.
- Una estructura con minutos que no suman se corrige sin una llamada más.
- Si el paso 2 cambia un título o unos minutos, prevalece la estructura y aparece un aviso.
- El paso 2 recibe solo los pasajes referenciados más la programación (comprueba el prompt).
- La cancelación entre pasos deja la ejecución en `cancelled`.
- Un exceso de extensión en una sección provoca un parche de esa sección y no una regeneración completa.
- Siguen pasando `test_pedagogy.py`, `test_live_generation.py`, `test_requirements_fulfillment.py` y `test_ui_*`. Si una baseline visual cambia por la nueva vista de estructura, regénerala y lístala en el resumen.

## Entrega

- `uv run --locked pytest` en verde y `--offline` de la evaluación sin errores.
- Actualiza `ARCHITECTURE.md` (flujo de generación) y `README.md` (qué ve el profesor durante la generación).
- Resumen con tokens y segundos por paso en la evaluación offline. Deja indicado el comando de la evaluación real para que el profesor compare con `2026-10-10_140833`.

## Fuera de alcance

Pausar la generación para que el profesor edite la estructura antes del paso 2. Déjalo preparado (estructura persistida y separable), pero no lo implementes.
