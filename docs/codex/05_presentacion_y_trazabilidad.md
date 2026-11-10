# Encargo 05 · La guía se lee como una clase; la auditoría va aparte

Lee `AGENTS.md` y cúmplelo. No cambies el contrato de citas: lo que se guarda y se verifica sigue siendo la subcadena exacta del original. Solo cambia cómo y dónde se muestra.

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

En la guía docente actual (`generation/render.py::render_pedagogy` y `web/static/js/componentes/documentos.js`), lo primero que lee el profesor es:

- el aviso de borrador,
- la tabla «Cobertura de requisitos del profesor» con siete filas,
- después las actividades, cada una con frases del tipo «cualquier dato adicional es aportación del profesor pendiente»,
- y cada sección de contenidos con un bloque «Fuentes:» de citas largas.

Esas citas arrastran ruido de OCR («aaa epa a las dos grandes corrientes musicológi- cas», «Piolomeo») y cortes de línea con guion.

La coletilla «aportación del profesor pendiente» la provoca la rúbrica del revisor (`agents/reviewer.py`, criterios de rigor y la comprobación `is_pending`), que la exige en texto libre. La trazabilidad es valiosa, pero su sitio no es el cuerpo de la clase.

## Tareas

1. **Orden de la guía docente**, en markdown, UI e impresión:
   1. Resumen de la sesión en una pantalla: objetivos y secuencia con minutos y agrupamiento.
   2. Actividades.
   3. Contenidos: texto de cada sección sin citas en línea, con una marca discreta (`[1]`, `[2]`) que enlaza a su evidencia.
   4. Recursos por preparar.
   5. Panel o anexo «Trazabilidad», plegado por defecto en la UI y al final en markdown e impresión. Reúne la tabla de cobertura, las citas por sección, los pasajes omitidos, los avisos de origen (`posible_generado_ia`, OCR) y la auditoría de relevancia.
   - El aviso de borrador queda en una línea bajo el título.
2. **Datos sin respaldo: de coletilla a campo.**
   - Añade a cada actividad un campo opcional `datos_por_verificar: [str]`, con frases breves de lo que el profesor debe comprobar.
   - El validador rechaza la coletilla en texto libre en `teacher_notes` y `solution` y pide usar el campo.
   - Adapta la rúbrica y `evaluate_deterministic_fallback` del revisor para leer el campo en lugar de buscar la frase.
   - La UI muestra un único distintivo «Verificar» por actividad, con la lista al desplegarlo.
3. **Citas legibles sin tocar el original.**
   - Crea una función de presentación que una palabras cortadas con guion a final de línea, colapse espacios y saltos y marque con un indicador las citas de texto OCR.
   - Se aplica solo al mostrar.
   - `evidence[].quote` guardado, la resolución de `quote_XXX` y la comprobación contra el original no cambian.
   - Ofrece «ver literal» para comparar.
4. **Material del alumnado** (`render_student`, `componentes/material-alumnado.js`). No debe heredar ninguna marca de trazabilidad. Comprueba que siguen pasando los tests de no filtración (`test_student_material_never_leaks_teacher_notes_or_solution` y similares).
5. **Impresión y PDF** (`static/css/print.css`). El anexo de trazabilidad se imprime solo si el profesor lo marca. Por defecto no se imprime.

## Tests

- El markdown de `render_pedagogy` empieza por el resumen de la sesión y la tabla de cobertura aparece solo dentro de «Trazabilidad».
- La normalización de citas para mostrar une «musicoló-\ngicas» y no altera `evidence[].quote` (compara antes y después de renderizar).
- Una `teacher_notes` con «aportación del profesor pendiente» se rechaza. Una actividad con `datos_por_verificar` pasa y se renderiza con el distintivo.
- El revisor puntúa igual una propuesta que usa el campo que una que antes usaba la coletilla.
- Baselines de `tests/ui_baseline/`: regenera solo las capturas afectadas (propuestas, impresión) y enuméralas en el resumen con el motivo.

## Entrega

- `uv run --locked pytest` en verde.
- Actualiza `README.md` (cómo leer una propuesta y dónde está la trazabilidad) y `ARCHITECTURE.md` (render y contrato de presentación de citas).
- Sube `PROMPT_VERSION` si cambia el esquema por `datos_por_verificar`.
