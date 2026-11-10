# Encargo 03 · Perfiles didácticos por materia

Lee `AGENTS.md` y cúmplelo durante todo el encargo.

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

El profesor da Historia de la Música I y II, NTAM y guitarra en el conservatorio, y Música en 2º y 3º de ESO en un colegio. Todas las propuestas usan el mismo prompt y los mismos límites.

- `agents/pedagogy.py::SYSTEM` empieza con «Eres profesor de Historia de la Música de conservatorio y musicólogo». Exige de 4 a 6 secciones de teoría de 150-300 palabras, de 2 a 5 ejemplos musicales y componentes de teoría griega.
- `validate` aplica a todas las materias los mismos límites: de 2 a 5 actividades, un máximo de 12 secciones y de 6 ejemplos musicales. Los mínimos de secciones solo están en el prompt.
- En `generation/service.py`, `es_tema_griego` añade tetracordos y Gran Sistema Perfecto según el texto del tema, sin mirar la materia.
- Las materias de `config.py::SCHEMAS['subjects']` no tienen ningún tipo (`'id name'`, `'description color periods'`).
- Si la recuperación no devuelve pasajes, `ask` se abstiene (`insufficient_sources`). Las carpetas de guitarra y conjunto están vacías, así que hoy esas materias no pueden generar nada.

Resultado: una clase de 3º ESO sale como una sesión de musicología, y una de guitarra no sale.

## Diseño

1. **Campo `perfil` en las materias.**
   - Valores: `historia`, `eso`, `instrumento`, `conjunto`, `tecnologia`.
   - Es opcional en `config.py` y se valida contra ese enum.
   - Si falta, vale `historia`, para no cambiar el comportamiento actual de nadie.
   - Añade ejemplos ficticios en `config/teaching.example.yaml` (una materia de cada perfil, con grupo y horario).
   - Edición desde Ajustes (`vistas/ajustes.js`, `componentes/configuracion.js`, `POST /api/subjects`), con un aviso visible «perfil sin asignar» en materias sin perfil explícito.
2. **Módulo `src/docente_ai/agents/perfiles.py`.**
   - Una definición inmutable por perfil, con:
     - `rol`: párrafo inicial del prompt.
     - `prioridades`: qué cuenta como buena clase en ese perfil.
     - Límites: secciones mín./máx., palabras por sección, `music_requests` mín./máx., tipos de `didactic_components` permitidos, actividades mín./máx.
     - Pautas de actividades.
     - `permite_sin_fuentes`.
   - Orientación de contenido, para que la redactes con precisión:
     - **historia:** el comportamiento actual.
     - **eso:** sesiones de 50-55 min con grupos numerosos y heterogéneos. Práctica musical activa (percusión corporal, instrumental Orff, boomwhackers, canto, movimiento), gestión del aula, transiciones cortas, atención a la diversidad. Teoría mínima y siempre ligada a lo que se toca o se escucha. Lenguaje del alumnado de 13-15 años.
     - **instrumento:** clase individual de grado profesional. Calentamiento y técnica, trabajo por pasajes de la obra en estudio, objetivos medibles por obra, plan de estudio en casa, preparación de audiciones. Sin secciones de historia salvo que se pidan.
     - **conjunto:** ensayo. Afinación, trabajo por secciones o cuerdas, equilibrio, entradas, distribución del tiempo de ensayo y montaje hacia un concierto.
     - **tecnologia:** práctica con software o código. Pasos reproducibles, requisitos técnicos, entregable verificable y resolución de errores típicos.
3. **Prompt.**
   - `SYSTEM` se construye con una parte invariante (solo JSON, no inventar datos, no notación musical, separación guía y alumnado, cobertura, contrato de citas) más el bloque del perfil.
   - Ordena el mensaje con lo estable primero (sistema y perfil) y lo variable después (contexto, fuentes), para que los proveedores con caché de prefijo lo aprovechen.
   - Sube `PROMPT_VERSION` a `pedagogy:12` y guarda el perfil usado en `request['pedagogy']` y en `metrics`.
4. **Esquema y validación.**
   - Mantén la misma forma de respuesta (`claims`, `plan`, `coverage`, `music_requests`, `visualizations`, `didactic_components`) para no romper el render ni el historial.
   - Cambia solo cardinalidades y límites, leídos del perfil, tanto en `RESPONSE_SCHEMA` (o un esquema generado por perfil) como en `validate`.
   - Los máximos del perfil se validan como hoy. Un mínimo no cumplido (por ejemplo, menos secciones de las pedidas) se registra en `warnings` y no provoca reparación, para no añadir regeneraciones.
   - Las propuestas antiguas sin perfil deben seguir abriéndose y renderizándose.
5. **Componentes griegos.** `es_tema_griego` y los componentes `tetracordos` y `gran_sistema_perfecto` solo se aplican con perfil `historia`.
6. **Sin fuentes.** Con `permite_sin_fuentes = true` (por defecto en `eso`, `instrumento` y `conjunto`; en `false` en `historia` y `tecnologia`), si no hay pasajes:
   - Se genera una propuesta solo metodológica: `claims = []`, plan completo y `coverage` con estado `sin_fuentes`. Puede apoyarse en la programación, la unidad, los criterios del profesor y la experiencia previa del grupo.
   - El render la etiqueta de forma visible como «Propuesta metodológica sin base documental».
   - El validador prohíbe en `teacher_notes` y `solution` datos fácticos concretos (fechas, atribuciones, cifras) en ese modo.

## Tests

- Un grupo de cada perfil produce un prompt con su bloque y sus límites. El de `eso` no contiene «musicólogo» ni exige secciones de teoría.
- `validate` acepta una propuesta de `instrumento` con 0-2 secciones y rechaza una de `eso` con más secciones de las que permite su perfil. Una de `historia` con menos secciones de las pedidas pasa con aviso.
- `es_tema_griego` no añade componentes en un grupo `eso` aunque el tema diga «Grecia».
- Con `permite_sin_fuentes` y corpus vacío, `ask` devuelve un borrador metodológico en lugar de abstenerse. Con `historia`, sigue absteniéndose.
- Compatibilidad: configuración sin `perfil`, propuestas antiguas, `test_pedagogy.py` y `test_teaching.py` en verde.
- Evaluación: añade `eval/casos/05_eso_percusion_corporal.yaml` (2º ESO, 55 min) y `06_guitarra_clase_individual.yaml` (guitarra, 4º GP, 60 min), con fuentes sintéticas en `scripts/run_eval.py::CASE_SOURCES` (o ninguna, para probar el modo sin fuentes) y grupos ficticios de `teaching.example.yaml`.

## Entrega

- `uv run --locked pytest` en verde y `--offline` de la evaluación sin errores.
- Actualiza `README.md` (cómo asignar perfil) y `ARCHITECTURE.md` (perfiles, versión de prompt, modo sin fuentes).
- Resumen con el texto final de cada bloque de perfil, para que el profesor lo revise.
