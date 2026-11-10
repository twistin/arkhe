# Encargo 07 (opcional) · Preparar en segundo plano las sesiones de los próximos días

Lee `AGENTS.md` y cúmplelo. Parte de los encargos 03 y 04.

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

- El servidor puede quedar siempre en marcha (`deploy/com.sdcarr.arkhe.plist`).
- La cola de trabajos existe: `web/workspace.py::Workspace.submit`, un `ThreadPoolExecutor` de un hilo, `/api/jobs`, eventos SSE y cancelación.
- El planificador semanal (`Workspace.weekly_planner`, `vistas/diario.js`) ya vincula sesiones con propuestas.
- Aun así, cada propuesta se pide a mano y se espera delante de la pantalla.

## Diseño

1. **Acción explícita.**
   - Botón «Preparar próximos días» en el planificador semanal.
   - Abre una ventana con las sesiones de los próximos N días (por defecto 7) que no tienen propuesta vinculada. Cada una muestra grupo, fecha, unidad prevista según la programación y un campo opcional de indicaciones.
   - El profesor marca cuáles preparar. Nunca se genera nada sin esta acción.
2. **Cola.**
   - Cada sesión marcada se encola como un trabajo normal de propuesta, con fecha de sesión, unidad y perfil de la materia.
   - Se ejecutan de uno en uno, con la cola existente, y son cancelables uno a uno o en bloque.
   - Se respeta el consentimiento de proveedor remoto (`require_provider_consent`) antes de encolar.
   - Tope configurable de trabajos por lote (por defecto 10).
3. **Requisitos sin interrupciones.**
   - En este modo no se abre «He entendido esto».
   - Los requisitos se extraen como hoy y quedan visibles y editables en cada propuesta. «Regenerar» sigue el flujo normal con la ventana.
4. **Resultado.**
   - Cada propuesta terminada queda como borrador vinculado a su sesión en el planificador, con un distintivo «preparada automáticamente».
   - Al terminar el lote aparece un aviso en la bandeja (`/api/inbox`).
   - Los fallos se listan con su motivo y un botón para reintentar.
5. **Coste visible.** La ventana muestra una estimación del número de llamadas y del tiempo a partir de las métricas por etapa del encargo 01, y el resumen del lote muestra los reales.

## Tests

- Con un calendario ficticio de `teaching.example.yaml`: la ventana lista solo sesiones sin propuesta y respeta excepciones y festivos.
- Encolar tres sesiones produce tres trabajos secuenciales con `session_date` correcto. Cancelar el lote detiene los pendientes.
- Sin consentimiento remoto, no se encola nada.
- Las propuestas resultantes aparecen vinculadas en `weekly_planner`.

## Entrega

- `uv run --locked pytest` en verde.
- Actualiza `README.md` (cómo preparar la semana) y `ARCHITECTURE.md` (lotes en la cola).
