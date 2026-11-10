# Encargo 02 · Requisitos fieles al texto del profesor

Lee `AGENTS.md` y cúmplelo durante todo el encargo.

Rutas: `agents/`, `generation/`, `rag/`, `teaching/`, `llm/`, `web/`, `config.py` y `storage.py` cuelgan de `src/docente_ai/`; `vistas/` y `componentes/` cuelgan de `src/docente_ai/web/static/js/`; `static/css/` de `src/docente_ai/web/`. El resto (`config/`, `eval/`, `scripts/`, `tests/`, `deploy/`) es relativo a la raíz del repositorio.

## Contexto

`rag/planning.py::extract_requirements` pide al modelo requisitos atómicos con `cita_profesor` y rechaza los que no citan literalmente el texto del profesor (`_verificar_cita_profesor`). Esa comprobación no basta. En la ejecución `eval/resultados/2026-10-10_140833/teoria-griega-seikilos`, con los criterios del caso `eval/casos/01_teoria_griega_seikilos.yaml`, aparecieron:

- **R6:** «Incluir actividades prácticas o ejercicios relacionados con la teoría musical, la notación o el análisis de obras». El profesor no lo pidió: toda propuesta lleva actividades.
- **R7:** «Especificar el formato de presentación del tema (documento escrito, presentación, vídeo…)». Tampoco se pidió. Su cita es probablemente «Creame un tema», una fórmula de petición, y luego se marcó como «Parcial» en la tabla de cobertura.
- **R2 y R3:** se solapan («principales autores y conceptos» frente a «teoría musical en Grecia»).

Cada requisito inventado añade búsquedas, ocupa contexto, aparece en la tabla de cobertura y empuja al modelo a rellenar.

## Tareas

1. **Fórmulas de petición.**
   - Rechaza un requisito cuya `cita_profesor`, normalizada, sea solo una fórmula de petición o de encargo: «créame un tema», «crea», «hazme», «prepara», «quiero una clase/sesión», «una propuesta sobre», con sus variantes sin tilde y con erratas habituales.
   - Mantén la lista en una constante del módulo, con tests. No uses regex por tema.
2. **Tipo `formato`.** Solo es válido si la cita contiene un término explícito de formato: presentación, diapositivas, ficha, dossier, cuaderno, examen, rúbrica, vídeo, documento, esquema, mapa conceptual, partitura para imprimir… Si no lo contiene, el requisito se descarta.
3. **Tipo `actividad`.** Solo es válido si la cita nombra una actividad o dinámica concreta: debate, audición, escucha, ejercicio, práctica, taller, juego, dictado, análisis en grupo, interpretación… «Incluir actividades» en abstracto nunca es un requisito.
4. **Duplicados.**
   - Dos requisitos no pueden apoyarse en el mismo tramo del texto del profesor, salvo que ese tramo enumere elementos (comas, «y», «/») y cada requisito corresponda a uno distinto.
   - Fusiona los duplicados conservando la descripción más concreta y el `id` más bajo, y renumera `R1…RN` como ya se hace.
5. **Trazabilidad del descarte.**
   - Devuelve los requisitos descartados con su motivo en un atributo de `RequirementsList`, por ejemplo `descartados=[{'description', 'cita_profesor', 'motivo'}]`.
   - Muéstralos plegados en la ventana «He entendido esto» (`web/static/js/vistas/propuestas.js::modalHeEntendidoEsto`) con un botón para recuperar cualquiera. El profesor decide; el filtro solo propone.
   - El endpoint `/api/planning/preview-requirements` debe incluir esa lista.
6. **Instrucción del extractor.** Ajusta el mensaje de sistema: no crear requisitos de formato ni de actividad salvo petición explícita, y no repetir como requisito el tema completo.
7. **Fallback.** El fallback por frases (`dividir_indicaciones_por_frases`) aplica los mismos filtros.

## Tests

- Fixture con los criterios literales del caso Seikilos y un extractor falso que devuelve los siete requisitos de la ejecución citada. Desaparecen R6 y R7, R2 y R3 se fusionan o se justifican por tramos distintos, y los descartados llevan motivo.
- Un `formato` con «hazme unas diapositivas» se conserva. Un `actividad` con «con un debate final» se conserva.
- Las citas con erratas («ana,isis», «lknea») siguen validándose como hoy.
- El fallback por frases no produce un requisito a partir de «Creame un tema».

## Entrega

- `uv run --locked pytest` en verde.
- Actualiza `README.md` (secciones «Extracción y cobertura de requisitos del profesor» y «Extracción transparente de requisitos docentes») y `ARCHITECTURE.md` (sección «Asignación de ejecutor por requisito y resolución previa al LLM»).
- Resumen con los filtros añadidos y ejemplos de entrada y salida.
