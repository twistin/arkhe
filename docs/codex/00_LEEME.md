# Encargos para Codex · calidad de las propuestas y fluidez

Siete encargos para dar a Codex de uno en uno y en este orden. Cada uno cabe en una rama y un PR. Todos dan por hecho que Codex lee y cumple `AGENTS.md`.

## Antes del primer encargo

- El árbol de trabajo tiene cambios sin confirmar (`render.py`, `pedagogy.py`, `service.py`, `presentacion.js`, baselines de UI…). Confírmalos o guárdalos antes de empezar, para que cada PR muestre solo su cambio.
- Una rama por encargo: `codex/01-latencia`, `codex/02-requisitos`, etc.
- Al terminar cada encargo, Codex ejecuta `uv run --locked pytest` y `uv run --locked python scripts/run_eval.py --offline`.
- Tú ejecutas después la evaluación real, que usa tu biblioteca y tu proveedor:
  `uv run --locked python scripts/run_eval.py --case teoria-griega-seikilos`
  El script usa DeepSeek por defecto. Después del encargo 01 podrás añadir `--provider mistral --model mistral-small-latest`.
  Referencia actual: `eval/resultados/2026-10-10_140833` (unos 108 s, 3 intentos de generación, 53 s antes de empezar a redactar, con 27 lotes de relevancia, guía docente de 5.368 palabras para 60 minutos).

## Orden

1. `01_latencia_y_reparacion.md`: medir por etapas, reducir lotes de relevancia y dejar de regenerar la propuesta entera por un fallo puntual. Va primero porque deja las métricas con las que se juzga el resto.
2. `02_requisitos_fieles.md`: que no aparezcan requisitos que no has pedido.
3. `03_perfiles_por_materia.md`: Historia, ESO, instrumento, conjunto y tecnología dejan de compartir prompt y límites.
4. `04_generacion_en_dos_pasos.md`: primero la estructura, después el desarrollo.
5. `05_presentacion_y_trazabilidad.md`: la guía se lee como una clase y la auditoría pasa a un panel aparte.
6. `06_ejemplos_del_profesor.md`: tus propuestas aprobadas sirven como referencia de estilo y tus ediciones dejan de perderse.
7. `07_preparar_semana.md` (opcional): preparar en segundo plano las sesiones de los próximos días.

## Decisiones tuyas antes de lanzar

- **Encargo 03.** Decide si instrumento, conjunto y ESO pueden generar una propuesta solo metodológica cuando no hay fuentes. Hoy la app se abstiene. El encargo lo propone activado para esos perfiles y desactivado para Historia. Las carpetas de guitarra y conjunto están vacías, así que sin esto no generarán nada.
- **Encargo 06.** Decide si los ejemplos de estilo pueden enviarse a proveedores remotos. El encargo los deja desactivados por defecto, con un interruptor por ejemplo.
- **Proveedor.** Para el piloto con compañeros, elige Mistral en Ajustes: el preset ya existe y usa endpoint de la UE. No requiere código. El encargo 01 corrige `scripts/run_eval.py` para que también se pueda evaluar con Mistral.

## Fuera de estos encargos

Multiusuario, Postgres, instalación en equipos Windows y embeddings remotos. Tendrán sentido cuando las propuestas funcionen bien con un solo profesor.
