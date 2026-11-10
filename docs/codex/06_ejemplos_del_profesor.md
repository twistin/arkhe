# Encargo 06 · Ejemplos del profesor y ediciones que no se pierden

Lee `AGENTS.md` y cúmplelo. Parte de los encargos 03 (perfiles) y 04 (dos pasos).

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

- Nada del estilo del profesor entra en la generación. No hay ejemplos de clases suyas en el prompt.
- `generation/service.py::edit_run` sobrescribe `result_json` en el sitio: la versión generada se pierde y no se puede saber qué corrigió el profesor. Además solo permite editar campos del plan (`objectives`, `difficulty`, `activities`, `resources`, `observations`), no el texto de las secciones.
- `review_run` permite aprobar o rechazar, pero la aprobación no tiene ningún efecto posterior.
- Con proveedor remoto, `agents/pedagogy.py::remote_context` excluye a propósito registros, feedback y calendario. Ese principio se mantiene.

## Diseño

1. **Conservar el original.**
   - Migración 11 en `storage.py`: columna `result_original_json` en `generation_runs`.
   - Se rellena en la primera edición con el resultado tal como lo generó el modelo.
   - Las ediciones siguientes no la tocan.
   - Guarda en `metrics` o en una columna un resumen de la diferencia: campos cambiados, palabras antes y después por sección y por actividad, actividades añadidas o eliminadas.
2. **Editar también el texto.**
   - Amplía `edit_run` para editar `claims[i].title`, `claims[i].text`, `claims[i].student_summary` y `key_points`, nunca `evidence`.
   - Tras editar, vuelve a ejecutar las comprobaciones no documentales: longitudes, separación guía y alumnado, ausencia de metacomentarios en el material del alumnado.
   - Si el profesor edita un texto con citas, la evidencia se conserva, pero la sección se marca como «editada por el profesor» en la trazabilidad.
3. **Ejemplos de referencia.**
   - Acción «Usar como ejemplo» en una propuesta aprobada.
   - Nueva tabla `ejemplos_estilo` con los campos `id`, `run_id`, `perfil`, `subject_id`, `creado_en`, `payload_json`, `permitir_remoto` (falso por defecto) y `activo`.
   - `payload_json` se construye con lista permitida:
     - la estructura (encargo 04),
     - las actividades con `title`, `grouping`, `minutes`, `student_task` y `teacher_notes`,
     - los títulos de sección y una sección completa como muestra de redacción.
   - Nunca entran en `payload_json` el nombre del grupo, fechas, sesión, diario, nombres de alumnado ni citas de fuentes.
4. **Uso en la generación.**
   - En el paso 1 y en el paso 2, incluye hasta 2 ejemplos activos: primero de la misma materia, después del mismo perfil.
   - Van en la parte estable del prompt, tras el bloque del perfil, en orden determinista (`creado_en`), para aprovechar cachés de prefijo.
   - Instrucción explícita: son referencia de estilo, estructura y extensión, no fuentes. No se citan ni se copian sus datos fácticos.
   - Los ejemplos nunca entran en `bundle['evidence']`, así que el contrato de citas impide citarlos. Añade un test que lo compruebe.
   - Presupuesto: los ejemplos se recortan antes que los pasajes (igual que hoy `repertorio_disponible` en `build_prompt`).
   - Con proveedor remoto, solo se envían los que tengan `permitir_remoto = true`. Amplía `remote_context` de forma explícita y documentada.
5. **Preferencias breves por perfil.**
   - En Ajustes, un texto de hasta 600 caracteres por perfil, por ejemplo «Empiezo siempre con una audición. No más de tres actividades. Tuteo al alumnado».
   - Se incluye junto al bloque del perfil, con el mismo control de envío remoto que los ejemplos.
6. **UI.**
   - Botón «Usar como ejemplo» en la tarjeta de propuesta aprobada (`vistas/propuestas.js`).
   - Lista de ejemplos en Ajustes, con perfil, materia, interruptor «permitir con proveedor remoto», desactivar y eliminar.

## Tests

- Migración 11 sobre una base con propuestas existentes: no pierde datos y `result_original_json` se rellena solo en la primera edición.
- Saneamiento: el `payload_json` de un ejemplo no contiene nombre de grupo, fechas ni texto de evidencias.
- Con proveedor remoto y `permitir_remoto = false`, el prompt no contiene el ejemplo. Con `true`, sí.
- Con presupuesto justo, se recortan ejemplos antes que pasajes.
- Una respuesta que intente citar el ejemplo como fuente falla la validación de citas.
- Editar `claims[i].text` conserva `evidence` y marca la sección como editada.

## Entrega

- `uv run --locked pytest` en verde.
- Actualiza `README.md` (cómo crear y gestionar ejemplos y preferencias) y `ARCHITECTURE.md` (tabla nueva, migración, contrato remoto ampliado).
- Resumen con el texto exacto de la instrucción que acompaña a los ejemplos en el prompt.
