# Encargo 01 · Medir y recortar la latencia de una propuesta

Lee `AGENTS.md` y cúmplelo durante todo el encargo. En particular: no leas `data/`, `Conocimiento/` ni `config/*.yaml` reales; trabaja con `config/*.example.yaml` y fixtures en `tests/fixtures/`; los tests no hacen red; no rompas el contrato de citas `quote_XXX`.

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto medido

Las últimas ejecuciones reales del caso `teoria-griega-seikilos` (`eval/resultados/2026-10-10_*/teoria-griega-seikilos/run_result.json`, campo `metrics`) muestran:

- **Antes de redactar:** 53–68 s de unos 108 s totales. `metrics.retrieval_seconds` incluye extracción de requisitos, reformulación de consultas, búsqueda y relevancia, sin desglose. `retrieval_ranking.batches` vale 26–27 para 37–42 candidatos. La función `rerank` de `src/docente_ai/rag/planning.py` usa `rank_settings = replace(settings, num_ctx=6144, max_output_tokens=1024)` y llama a los lotes de forma secuencial, tanto con Ollama como con proveedores remotos. Después hay una llamada más al selector final.
- **Consultas:** hasta 12 (`retrieval_queries`). En `generation/service.py::ask` se añade además una búsqueda por requisito con `top_k=4`, una tras otra.
- **Generación:** todas las ejecuciones con éxito necesitaron 2 o 3 intentos (`metrics.attempts`). El primero falla siempre por `contract`. Cada reparación de `generation/repair.py::generate_validated` vuelve a generar el JSON completo, unos 5.000 tokens de salida por intento.
- **Errores que fuerzan esas regeneraciones:**
  - `Omisión en la línea temporal / autores canónicos documentados en las fuentes: Alipio` (y Platón, Aristóteles, Arquitas…), en `agents/pedagogy.py::validate`, bloque que usa `find_canonical_authors_in_text`. Cuando un requisito menciona línea de tiempo, cronología o autores, exige que todo autor canónico presente en los pasajes enviados figure en la propuesta o en una nota de cobertura, lo haya nombrado o no el profesor. Eso alarga la propuesta y produce errores: en `2026-10-10_140833`, la solución de la actividad de línea de tiempo pone a Boecio (c. 480-524) antes que a san Agustín (354-430), porque la cronología la escribe el modelo en texto libre.
  - `activities[3].student_task menciona fuentes o lagunas documentales`.
  - `quote_unresolved` en una sola evidencia.

## Objetivo

Reducir a la mitad el tiempo del caso Seikilos con proveedor remoto, sin relajar la verificación de citas ni la separación entre guía docente y material del alumnado. La cifra es orientativa: lo obligatorio es medir y dejar el antes y el después en el resumen.

## Tareas

1. **Métricas por etapa.**
   - Añade a `metrics` un objeto `stage_seconds` con las claves `requirements`, `query_planning`, `retrieval`, `rerank`, `fulfillment`, `generation` (lista con un valor por intento) y `review`.
   - Añade `rerank_calls` y `embedding_calls`.
   - Muestra una columna resumida en el informe de `scripts/run_eval.py`.
2. **Lotes de relevancia.**
   - Diagnostica por qué `rerank` crea casi un lote por candidato y documenta la causa en el resumen. Probablemente el presupuesto de 6144 tokens frente al tamaño estimado de cada pasaje y del esquema.
   - Con proveedor remoto, calcula el presupuesto de lote a partir del contexto real del proveedor, con un tope de salida suficiente para puntuar todos los ids del lote. El objetivo es 1–3 lotes.
   - Con proveedor remoto, ejecuta los lotes en paralelo con un límite configurable (por defecto 4), respetando `current_execution().check()`, los eventos `emit_live('relevance', ...)` y la cancelación.
   - Con Ollama se mantiene el comportamiento secuencial y el `keep_alive` actual.
   - Si la lista corta tiene `limit` elementos o menos, omite la llamada al selector final.
3. **Embeddings en bloque.** Agrupa en una sola llamada `embedder.embed(...)` los vectores de la consulta principal, las variantes y las búsquedas por requisito. Hoy `search()` se llama una vez por requisito y cada llamada vuelve a embeber. Mantén intactos los filtros de autorización y las comprobaciones de `verify_original` y del perfil de índice.
4. **Autores canónicos: de fallo a cálculo determinista.**
   - Exige solo los autores que el profesor nombra en el tema, los criterios o los requisitos (`cita_profesor`). Si pide «principales autores» sin nombrarlos, no exijas ninguno concreto.
   - Los autores que aparecen en los pasajes pero no se pidieron pasan a `warnings` o a métricas, nunca a `fail`.
   - Cuando un requisito tenga ejecutor `linea_temporal`, construye el orden cronológico por código a partir de `config/fichas/cronologia_autores.yaml` y de los pasajes, como ya prevé `teaching/fulfillment.py`.
   - Si una actividad trabaja sobre esa línea temporal, su `solution` remite al componente calculado y no reescribe fechas. Añade un validador que rechace una solución que ordene autores al revés de la cronología conocida.
5. **Reparación por parche.**
   - Cuando la validación falle en rutas concretas (`claims[i].evidence[j]`, `claims[i].student_summary`, `plan.activities[j].student_task`, etc.), pide al modelo solo los fragmentos afectados: un objeto `{ruta: valor}` con un esquema cerrado.
   - Fusiona el parche y vuelve a validar el documento completo.
   - Si el parche no es válido, recurre a la regeneración completa actual.
   - Para `quote_unresolved`, el parche solo puede tocar esa lista de evidencias y debe recibir los `quote_XXX` permitidos de esa fuente, como ya hace el mensaje actual.
   - Mantén el contrato descrito en `ARCHITECTURE.md`, sección «Contrato de reparación: grounded-answer:6 y pedagogy:7», y conserva los diálogos de reparación en `record_prompt`.
6. **Evaluación con cualquier preset.** En `scripts/run_eval.py`, cualquier `--provider` distinto de `ollama` se convierte hoy en DeepSeek. Respeta los presets de `llm/presets.py` (al menos `mistral`) y deja `--help` acorde.

## Tests

- `rerank`: con un generador falso remoto, 40 candidatos producen pocos lotes y ejecución concurrente. Con Ollama, el orden sigue siendo secuencial. Una cancelación a mitad detiene los lotes pendientes.
- Embeddings: una sola llamada para consulta, variantes y requisitos, con el mismo resultado de filtros que antes.
- Autores: un autor presente en los pasajes y no pedido ya no provoca fallo. Uno pedido y ausente sí lo provoca. Una solución con Boecio antes que san Agustín se rechaza.
- Parche: un fallo en `claims[4].evidence[4]` se repara sin regenerar el resto (el falso recibe un único diálogo de parche). Un parche inválido cae en la regeneración completa.
- Los tests existentes de `test_pedagogy.py`, `test_generation.py`, `test_repair.py` y `test_live_generation.py` siguen pasando. Si alguno codificaba el comportamiento antiguo de autores canónicos, actualízalo y explica por qué en el resumen.

## Entrega

- `uv run --locked pytest` en verde y `uv run --locked python scripts/run_eval.py --offline` sin errores.
- Actualiza `ARCHITECTURE.md` (recuperación, reparación, autores canónicos) y `README.md` (estadísticas de generación).
- Resumen final con las métricas nuevas, las causas encontradas y cualquier dependencia añadida, con su justificación. No se espera ninguna.

## Fuera de alcance

Cambiar el prompt pedagógico, el esquema de respuesta o la interfaz, salvo lo imprescindible para mostrar las métricas nuevas.
