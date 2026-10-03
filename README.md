# ARKHÉ IA DOCENTE LOCAL

Antes llamado Enjambre.

Asistente docente con biblioteca local y fuentes controladas por el profesor.
Los embeddings siempre se ejecutan en Ollama local (bge-m3 como modelo de referencia);
la generación puede ser local o remota según el proveedor elegido y confirmado.
Biblioteca de conocimiento y aplicación gráfica local para consultar fuentes y preparar
propuestas de clase con Ollama. El desarrollo por fases queda aparcado para priorizar
el espacio de trabajo del profesor.

## Abrir la aplicación

Haz doble clic en **Arkhe.app**, dentro de esta carpeta, o ejecuta:

```sh
uv run --locked docente-ai ui
```

La interfaz se abre en http://127.0.0.1:8765. Biblioteca, Asistente, Propuestas y
Ajustes reúnen el trabajo habitual. El lanzador utiliza el entorno `.venv` del
proyecto: debe permanecer junto a él; no es un instalador autónomo.
Abrirlo de nuevo reutiliza el servidor existente. Para detenerlo, utiliza
**Ajustes → Cerrar aplicación**. Cerrar la pestaña no detiene el servidor.

## Tu carpeta de conocimiento

La carpeta **Conocimiento**, en la raíz del proyecto, contiene:

- **00 Entrada**: archivos pendientes de clasificar.
- **01 Fuentes/<asignatura>**: bibliografía y documentos de referencia.
- **02 Material docente/<asignatura>**: materiales propios del profesor.

Puedes añadir documentos desde la interfaz o copiarlos con Finder y pulsar
**Revisar carpeta**. Se admiten PDF, DOCX, TXT y Markdown; la subida admite
hasta 8 archivos de 100 MiB cada uno. Los PDF escaneados requieren OCRmyPDF
opcional instalado en PATH y revisión explícita del texto reconocido.
Revisa el documento, su asignatura y sus datos antes de permitir su uso.
**Permitir y preparar** autoriza la fuente y crea su índice con Ollama.
Solo las fuentes autorizadas y preparadas se usan para responder.
Excluir una fuente impide su uso posterior; los resultados antiguos muestran
advertencias cuando sus fuentes dejan de estar disponibles.

La aplicación conserva copias verificables de los originales en `data/library`.
Modificar un archivo de conocimiento permite incorporar una nueva versión.
Los textos generados por IA se guardan aparte, nunca como bibliografía autorizada.
La carpeta empieza sin documentos de ejemplo. Las seis asignaturas iniciales
proceden del proyecto; crea tus grupos reales en **Ajustes** antes de preparar clases.

En **Asistente**, pregunta por tus documentos y abre las citas de cada respuesta.
La consulta combina búsqueda semántica y por términos, reformulación al inglés
y revisión de relevancia de hasta 24 pasajes completos. Después ordena definición,
funcionamiento y ejemplos según la pregunta. La interfaz indica la etapa y el lote
que está revisando. En libros extensos, este proceso puede tardar varios minutos
con el modelo local. La reformulación y la revisión de pasajes usan el proveedor
generativo elegido, por lo que también pueden ser remotas. No requiere volver a preparar tus fuentes.

En **Propuestas**, elige grupo, tema y duración; revisa el resultado y expórtalo
como Markdown. Las respuestas inválidas se registran como fallidas y no se
presentan como propuestas válidas. La revisión pedagógica sigue siendo del profesor.

**Ajustes** permite editar asignaturas y grupos y elegir modelos ya instalados en
Ollama. No descarga modelos. Un cambio de embeddings requiere preparar las fuentes
con el modelo seleccionado. La interfaz sirve sus recursos localmente, sin fuentes
tipográficas ni scripts externos. Ollama debe estar disponible para preparar
documentos y calcular embeddings; también genera respuestas si eliges el preset local.

Los presets son **Ollama**, **DeepSeek**, **Mistral** y **Endpoint personalizado**.
El adaptador remoto común usa `base_url`, `model` y la capacidad declarada
`response_format`: `none`, `json_object` o `json_schema`. Los presets y capacidades
por modelo son datos de `llm/presets.py`; no se instalan SDK adicionales.
Mistral utiliza `https://api.eu.mistral.ai/v1`, su [endpoint regional europeo](https://docs.mistral.ai/inference/regional-inference).
El indicador permanente muestra la generación local o el proveedor y su residencia
declarada: UE, fuera de la UE o desconocida. Esta etiqueta identifica el destino
de inferencia; no certifica todas las condiciones de retención o subprocesamiento.

Antes de la primera consulta remota, la interfaz pide una confirmación explícita.
Se guarda en los ajustes para ese proveedor, endpoint, modelo y capacidad de
salida; cambiar cualquiera de ellos exige confirmarla de nuevo. El servidor, la
CLI y el adaptador bloquean el envío sin confirmación. Configuraciones antiguas
de DeepSeek tampoco quedan autorizadas automáticamente.

**Qué sale del equipo:** pregunta o tema, fragmentos recuperados de fuentes
autorizadas y sus títulos, autores, año, tipo y referencias de cita. El proveedor
también puede recibir consultas de búsqueda y pasajes para ordenar su relevancia.
En propuestas se envían nivel, idioma, duración, criterios escritos para esa
consulta y los campos de título, objetivos, contenidos, competencias y criterios
de la unidad seleccionada. Las reparaciones reenvían el diálogo de generación.
No se adjuntan archivos originales ni se extraen datos de `session_records` o
`session_feedback` para el prompt remoto; quedan excluidos experiencias previas,
notas del diario, feedback, identificadores personales y calendario del contexto.
Si pegas esos datos expresamente en la pregunta, criterios o fuentes autorizadas,
forman parte del contenido que has seleccionado para enviar.

Para proveedores remotos, Ajustes permite introducir o borrar la clave de API. El campo solo
escribe: la API devuelve únicamente `api_key_configured`, nunca la credencial.
Se guarda en el Llavero de macOS, servicio `docente-ai`, cuentas `deepseek_api_key`,
`mistral_api_key` o `custom_api_key`. Las variables `DOCENTE_AI_DEEPSEEK_API_KEY`,
`DOCENTE_AI_MISTRAL_API_KEY` y `DOCENTE_AI_CUSTOM_API_KEY` tienen prioridad; en otras plataformas es
la forma de configurarla. Borrar en Ajustes elimina la entrada del Llavero, pero
no elimina una variable de entorno: si existe, seguirá figurando como configurada.
Los YAML antiguos se migran al cargarse: primero se guarda la clave en el Llavero
y después se reescribe la configuración sin ella. Si el Llavero falla, la migración
se detiene sin borrar la clave original. No se guardan credenciales en YAML ni
en los registros de generación de SQLite. Los handlers de logging enmascaran
patrones de clave `sk-` seguidos de al menos 16 caracteres alfanuméricos, también
en excepciones. El filtro protege las nuevas entradas, no modifica logs históricos.

## Instalación

Requisitos: Python 3.12 y uv. Desde la raíz del proyecto:

```sh
uv sync --locked --python 3.12
uv run --locked docente-ai --help
uv run --locked docente-ai doctor
```

Se crea `.venv` dentro del proyecto. La primera instalación puede descargar
paquetes; no modifica Python global ni instala/actualiza Ollama.
El archivo `uv.lock` fija las dependencias. Python está limitado a 3.12 hasta
validar otras versiones. Las dependencias de ejecución son httpx, PyYAML, pypdf, sqlite-vec, Starlette y Uvicorn.

## Uso

```sh
uv run --locked docente-ai --version
uv run --locked docente-ai doctor --offline
uv run --locked docente-ai doctor --json
uv run --locked docente-ai doctor --ollama-host http://127.0.0.1:11434 --timeout 3
```

`doctor` comprueba Python, SQLite en memoria, FTS5, disponibilidad del método
para cargar extensiones y los endpoints `/api/version` y `/api/tags` de Ollama.
No descarga ni carga modelos, no ejecuta inferencia y no crea una base de datos.
Solo acepta HTTP de loopback; normaliza `localhost` a `127.0.0.1`, ignora
proxies del entorno y no sigue redirecciones. `--offline` evita todo HTTP.
No verifica que los modelos anunciados puedan ejecutarse offline ni que el
servidor tenga deshabilitado cloud. Tampoco compara la versión del cliente CLI.
El timeout es por operación HTTP, no un plazo máximo de todo el diagnóstico.

Códigos de salida: 0 sin errores (puede haber avisos o comprobaciones omitidas),
1 operación con errores, 2 argumentos inválidos y 130 cancelación.
Si Ollama no responde, abrir la aplicación Ollama y volver a ejecutar el
comando. No se arranca ningún servicio automáticamente.

## Pruebas

```sh
uv run --locked pytest
```

También se pueden utilizar directamente los ejecutables del entorno:

```sh
source .venv/bin/activate
pytest
docente-ai doctor --offline
python -m docente_ai --help
```

La suite usa respuestas HTTP simuladas; no necesita Ollama ni Internet y
bloquea conexiones de red reales. El diagnóstico real se ejecuta manualmente
con `docente-ai doctor`. Tras instalar, los comandos de `.venv/bin/` no necesitan
resolver dependencias; `uv run --offline --locked ...` permite usar la caché sin red.

## Organización y privacidad

- `src/docente_ai/`: CLI, diagnóstico, validación y almacenamiento.
- `src/docente_ai/teaching/`: calendario y consulta de programación.
- `config/teaching.example.yaml`: ejemplo ficticio, sin datos del profesor.
- `tests/`: CLI, HTTP local, configuración, calendario, programación y transacciones.
- `ARCHITECTURE.md`: diseño aprobado y plan incremental.
- `data/` y configuración personal: excluidos de Git. La configuración RAG local y el informe de prueba se guardan ahí; no hay datos docentes reales importados.

El módulo `agents/pedagogy.py` implementa el rol especializado en propuestas.
Las siguientes fases del plan permanecen aparcadas.

## Verificación de fase 1

Comprobado en macOS ARM64 con Python 3.12.12:

- 47 tests superados sin conexiones de red reales.
- `uv lock --check` correcto.
- Construcción de sdist y wheel correcta.
- Wheel instalado y diagnóstico offline ejecutado en un segundo entorno aislado.
- Diagnóstico real: SQLite 3.51.1, FTS5 disponible, Ollama 0.33.3 y `qwen3:14b` anunciado.

No se ha probado inferencia ni sqlite-vec; corresponden a fases posteriores.
Git está inicializado en `main`, sin remoto ni commits automáticos.


## Configurar la docencia

El archivo `config/teaching.example.yaml` es un ejemplo ficticio completo.
No se ha importado como calendario real. Copiarlo y adaptarlo:

```sh
cp config/teaching.example.yaml config/teaching.yaml
# Editar config/teaching.yaml con asignaturas, grupos y horarios reales.
uv run --locked docente-ai config validate config/teaching.yaml
uv run --locked docente-ai config import config/teaching.yaml
```

La importación crea `data/docente.sqlite3`. Todos los comandos de consulta e
importación aceptan `--db /ruta/a/docente.sqlite3`; la ruta por defecto es
relativa al directorio desde el que se ejecuta el comando. Validar no crea
archivos. Consultar una base inexistente devuelve un error y no la crea.

Tras editar la configuración, volver a validarla e importarla con `--replace`
si ya existe otra versión. La sustitución es **completa**, no una fusión: las
entidades omitidas se retiran del estado activo. Se hace en una transacción
y conserva la configuración anterior en `config_imports`. Importar otra vez
la misma configuración no duplica registros ni instantáneas. El orden de las
listas se conserva al exportar, pero reordenar una lista sin cambiar su contenido
no cuenta como una nueva importación; el orden docente depende de `order`.

```sh
uv run --locked docente-ai config export --output config/copia-local.yaml
uv run --locked docente-ai config import config/teaching.yaml --replace
```

La exportación nunca sobrescribe un archivo existente. Sin `--output` imprime
YAML en la terminal. Para volver a una copia exportada, validarla e importarla
con `--replace`. Las instantáneas internas son un registro adicional y no
sustituyen una copia de seguridad de la base.

### Formato de configuración

La raíz contiene `schema_version: 1`, `timezone` opcional (Europe/Madrid por
defecto) y todas estas listas; utilizar `[]` cuando todavía no haya datos:

| Lista | Contenido |
|---|---|
| `centers`, `teachers`, `subjects` | IDs estables y nombres editables; descripción opcional en asignaturas |
| `academic_years` | Nombre y fechas de inicio y fin; duración máxima de dos años |
| `groups` | Asignatura, centro, curso académico, profesor, nombre, nivel e idioma opcional |
| `schedule_rules` | Grupo, día ISO (1 lunes–7 domingo), hora, duración, vigencia, aula y zona horaria opcionales |
| `calendar_exceptions` | Regla y fecha; cancelación o cambio de hora, duración y/o aula para esa ocurrencia |
| `curricula` | Asignatura, curso académico, número de versión y nombre |
| `curriculum_units` | Programación, orden, título, objetivos y contenidos; otros campos pedagógicos opcionales |
| `group_curricula` | Asociación de un grupo a una programación activa |

IDs: letras ASCII, números, punto, guion y guion bajo; máximo 80 caracteres.
Fechas: `YYYY-MM-DD`. Horas: texto entre comillas, por ejemplo `'17:00'`.
Duraciones: enteros positivos en minutos, máximo 1440. Los objetivos,
contenidos, competencias, criterios, actividades, repertorio y recursos son
listas de textos. Las unidades pueden incluir `start_date` y `end_date`
para temporalización orientativa; deben aparecer juntos y estar dentro del curso.

Los IDs duplicados, campos desconocidos, referencias inexistentes, horarios
fuera del curso y solapamientos de grupo, profesor o aula se rechazan. También
se rechazan horas ambiguas o inexistentes por cambio de horario: añadir una
excepción que cambie o cancele esa sesión. Las aulas se comparan por texto exacto
dentro de un mismo centro. La duración se interpreta como tiempo transcurrido.
Una excepción cambia la sesión dentro de la misma fecha; moverla a otro día
requiere cancelar la original y añadir una regla con vigencia de un solo día.
Los festivos se introducen explícitamente; no se descargan de servicios externos.

### Consultar calendario y programación

Después de importar la configuración adaptada (IDs y fechas son del ejemplo):

```sh
uv run --locked docente-ai calendar list --from 2026-10-01 --to 2026-10-31
uv run --locked docente-ai calendar list --from 2026-10-01 --to 2026-10-31 --group historia-3gp --json
uv run --locked docente-ai curriculum show --group historia-3gp --date 2026-10-01
```

Las fechas del intervalo son inclusivas y seleccionan la fecha local de inicio.
Cada sesión tiene un identificador estable `regla:fecha` y estado `planned`.
Las sesiones se calculan desde SQLite; todavía no se guardan como registros de
impartición. Cambiar el YAML sin importarlo no modifica las consultas.

La programación muestra sus unidades y señala las que coinciden con la fecha
indicada. No presupone lo ya impartido, no avanza contenidos y no impone una
unidad siguiente. La edición se realiza en YAML y se importa explícitamente.

`config validate`, `config import`, `calendar list` y `curriculum show`
admiten `--json`. Los errores de esas operaciones se devuelven con código 1
(y objeto `ok: false` en modo JSON); argumentos incorrectos usan código 2.

## Verificación de fase 2

95 tests cubren las fases 1 y 2: configuración estricta, YAML seguro, claves
foráneas, persistencia, idempotencia, rollback, exportación, festivos, cambios
horarios, solapamientos y consulta de programación. Las pruebas utilizan datos
ficticios y bases temporales, sin Ollama ni acceso a Internet.

## Biblioteca documental (fase 3)

Importación local de PDF, DOCX, TXT UTF-8 y Markdown UTF-8.
Elige la categoría explícitamente: `documental` para bibliografía y `profesor`
para tus notas o materiales propios. No se admite contenido IA como fuente.

```sh
uv run --locked docente-ai library import /ruta/libro.pdf --category documental --title 'Título verificado' --author 'Autor verificado' --year 2000 --subject historia-i
uv run --locked docente-ai library import /ruta/notas.md --category profesor --subject historia-i
uv run --locked docente-ai library list
uv run --locked docente-ai library show DOCUMENT_ID --text
uv run --locked docente-ai library authorize DOCUMENT_ID
uv run --locked docente-ai library exclude DOCUMENT_ID
```

Sustituye `DOCUMENT_ID` por el identificador devuelto. Los IDs de asignatura
deben existir en la configuración docente; los del ejemplo no se crean solos.
La biblioteca también puede empezar antes de configurar la docencia: importar
sin asignatura y asociarla después. Solo se autoriza una fuente con asignaturas
asignadas o marcada explícitamente como `--shared` (compartida entre asignaturas).
Importar nunca autoriza automáticamente.

Metadatos adicionales: `--publisher`, `--doi`, `--url`, `--type`, `--origin`,
`--tag` y `--collection`. Autor, etiqueta, colección y asignatura admiten opciones
repetidas. Sin título se usa el nombre del archivo como etiqueta inicial;
autor, año, DOI y demás campos desconocidos quedan vacíos. La validación de DOI
y URL es sintáctica, no una comprobación bibliográfica en Internet. No se siguen
URLs ni enlaces Markdown y no se ejecuta código de los documentos.

```sh
uv run --locked docente-ai library update DOCUMENT_ID --title 'Título corregido' --author 'Autora'
uv run --locked docente-ai library update DOCUMENT_ID --clear year --clear doi
uv run --locked docente-ai library update DOCUMENT_ID --subject otra-asignatura
uv run --locked docente-ai library update DOCUMENT_ID --clear-subjects --shared
uv run --locked docente-ai library list --subject historia-i --authorized-only
```

Actualizar metadatos o ámbito retira la autorización hasta nueva revisión.
`--subject` en update sustituye la lista completa; `--clear-subjects` la vacía.
La categoría es inmutable. `--no-shared` retira el ámbito compartido. Excluir
conserva los originales y las versiones; no hay borrado destructivo en esta fase.

### Versiones y extracción

Cada importación conserva una copia original en
`library/originals/` junto a la base SQLite, con nombre SHA-256 y permisos de
solo lectura. No modifica el archivo de origen. La base guarda el hash, fecha,
ruta de origen, versión del extractor, metadatos de incorporación y extracción.
No modifiques manualmente ese almacén: autorizar verifica su integridad.

```sh
uv run --locked docente-ai library import /ruta/libro-revisado.pdf --category documental --document-id DOCUMENT_ID
uv run --locked docente-ai library show DOCUMENT_ID --text --version-id VERSION_ID
```

Sin `--document-id`, bytes idénticos dentro de la misma categoría son una
reimportación sin duplicar. Con ese ID, bytes distintos crean una versión.
Una versión nueva extraída retira la autorización. Si falla la nueva extracción,
la versión anterior y su autorización se conservan; el fallo queda visible en
el historial. Un hash ya registrado no se reextrae ni cambia la versión actual.
Cambios de metadatos deben hacerse con `library update`. Un mismo archivo puede
representarse por separado como documento y como material del profesor; nunca
se mezclan sus categorías, aunque la copia física se comparta.

Estados: `ready`, `needs_review` y `failed`. Un documento cifrado, ilegible o sin
texto queda registrado como fallido y no puede autorizarse. En PDF se detectan
páginas con menos de 20 caracteres alfanuméricos, incluidas páginas vacías:
pueden ser imágenes, portadas o páginas blancas. Si falta OCRmyPDF, la importación
se rechaza explicando cómo instalarlo; nunca se autoriza silenciosamente una
extracción parcial. Aun sin avisos, revisa orden de lectura y calidad.

PDF conserva página física (base 1) y etiqueta del archivo, pero nunca infiere
numeración impresa. TXT y Markdown conservan el texto, rangos de líneas y offsets;
no se les asignan páginas. DOCX conserva encabezados, listas y tablas en Markdown,
en el orden del cuerpo principal. Se cita por párrafo (incluidos los vacíos en la
numeración) o tabla, y por el encabezado precedente; no se inventan páginas Word.
Las imágenes, cuadros de texto, notas y encabezados/pies de página no forman parte
de esta extracción. Las tablas sin encabezado explícito reciben una fila Markdown
vacía, conservando todas las filas originales como datos.

### OCR opcional y procedencia

Instalación externa opcional en macOS: `brew install ocrmypdf tesseract-lang`.
En Debian/Ubuntu: `sudo apt install ocrmypdf tesseract-ocr-spa tesseract-ocr-eng`.
Consulta la [instalación oficial de OCRmyPDF](https://ocrmypdf.readthedocs.io/en/stable/installation.html).
`uv` no instala OCRmyPDF. `docente-ai doctor --offline` comprueba su presencia
en PATH sin ejecutar OCR ni comprobar los idiomas o todas sus dependencias.

Al importar, OCRmyPDF procesa localmente las páginas detectadas como escasas,
con idiomas `spa+eng` por defecto (configurables mediante
`DOCENTE_AI_OCR_LANGUAGES`, por ejemplo `spa+gal+eng` si están instalados).
El proceso se limita a dos trabajos simultáneos y 15 minutos por documento.
El original permanece inmutable: una versión derivada PDF con SHA-256 propio
guarda la procedencia **texto OCR**, el ID y hash de su versión de origen y la
herramienta utilizada. La ficha permite descargar ambas copias por separado.
Una importación fallida se puede reimportar después de instalar OCR, conservando
su historial. La derivada requiere revisión y `--accept-warnings` para autorizarla.
La autorización y la recuperación comprueban la integridad tanto de la derivada
como de su original previo al OCR.

Las citas y el anexo documental avisan de posibles errores de reconocimiento.
La coincidencia exacta se valida contra el texto almacenado de la versión
autorizada: el OCR no permite aproximar ni corregir las citas automáticamente.
Si quedan páginas vacías o escasas tras OCR, sus avisos requieren revisión; si
no queda texto utilizable o cambia el número de páginas, la importación falla.

Límite inicial de archivo: 100 MiB, configurable con `--max-mb` (1–1024).
Ese límite no garantiza un tope de RAM: un PDF comprimido puede requerir más
memoria al extraerse. EPUB y reconocimiento musical todavía no están implementados.
`python-docx` es la dependencia de lectura DOCX: interpreta los estilos de párrafo,
la numeración y las tablas del contenedor Word; incluye `lxml` como dependencia
transitiva. No se ejecuta contenido de los documentos. Los errores de lectura del archivo
antes de obtener sus bytes no crean una importación; los fallos de extracción sí.

Todos los comandos de biblioteca aceptan `--db` y `--json`. Las importaciones
fallidas salen con código 1 e incluyen documento, versión y motivo. No requieren
Ollama ni Internet. La migración SQLite 1→2 es transaccional y conserva la
configuración docente. Una sustitución docente no permite retirar asignaturas
vinculadas a documentos: primero hay que reasignar esas fuentes.

Conserva la base y su directorio `library/` juntos al mover/copiar la biblioteca.
La copia de archivo y la transacción SQLite no forman una transacción conjunta:
un fallo después de copiar y antes del commit puede dejar un original sin
referencia, pero nunca activa un registro incompleto; no se borra automáticamente.

### Verificación de fase 3

133 tests superados, incluidos PDF sintéticos con texto, páginas vacías,
cifrado, metadatos, localizadores, versiones, autorizaciones, integridad,
migración de una base de fase 2 y conservación de referencias docentes.

## Recuperación semántica (fase 4)

Motor probado: `sqlite-vec` 0.1.9 en macOS ARM64. Modelo elegido por el profesor:
`qwen3-embedding:0.6b`, instalado en Ollama (aproximadamente 639 MB en disco).
Su selección está en `config/rag.yaml`, fuera de Git; el ejemplo reproducible
está en `config/rag.example.yaml`. La aplicación no descarga modelos automáticamente.
El modelo generativo `qwen3:14b` no se usa en esta fase.

En otra instalación, después de elegir y descargar explícitamente el modelo:

```sh
cp config/rag.example.yaml config/rag.yaml
# Editar model y los prefijos si se elige otro modelo.
```

Tras configurar asignaturas e importar, revisar y autorizar documentos:

```sh
uv run --locked docente-ai library index
uv run --locked docente-ai search 'Ars Nova' --subject historia-i
uv run --locked docente-ai search 'síntesis sustractiva' --subject ntam --category profesor
uv run --locked docente-ai search 'ritmo' --subject historia-i --category all --top-k 6 --json
```

Los IDs anteriores son ejemplos: usa los que hayas configurado. Indexar procesa
solo versiones vigentes y autorizadas, de ambas categorías. Se puede restringir
con `--subject` y uno o varios `--document DOCUMENT_ID`. Buscar requiere una
asignatura, incluye también las fuentes expresamente compartidas y, por defecto,
consulta únicamente la categoría documental. `--category profesor` busca en los
materiales propios; `all` permite ambas y etiqueta cada resultado por procedencia.
No se amplían los permisos cuando no hay resultados.

Ambos comandos admiten `--db`, `--rag-config` y `--json`. El perfil configura
modelo, host de loopback, timeout, tamaño/solapamiento de fragmentos, lote y
prefijos de documento/consulta. El prefijo del ejemplo sigue el formato de
consulta con instrucción del modelo Qwen; no es un prompt generativo. Véase la
[ficha oficial Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).

### Índices y referencias

La migración SQLite 2→3 añade perfiles, fragmentos y registros de índices
completos por versión. El modelo se verifica por nombre y digest; sus vectores
se normalizan y guardan en float32. Dimensión, prefijos y fragmentación forman
parte del perfil. Un cambio de digest o configuración requiere otro índice;
no se comparan espacios vectoriales distintos. Cambiar host, timeout o tamaño
de lote no cambia el perfil semántico.

Indexar es reanudable por versión: se conservan las versiones ya completadas,
pero una interrupción no activa el índice parcial de la versión en curso.
Repetir el comando reutiliza los índices completos. Los históricos permanecen
para trazabilidad; las búsquedas solo consultan versiones actuales autorizadas.
Si hay documentos autorizados sin índice para el perfil seleccionado, la
búsqueda pide reindexar en vez de ocultar la falta de cobertura.

Los fragmentos respetan la página PDF de origen y conservan texto exacto,
offsets y líneas. El límite se expresa en caracteres, no en tokens: Ollama recibe
`truncate: false`. Si un fragmento excede su contexto, la operación falla de
forma explícita; reduce `chunk_chars` y, si procede, el solapamiento y reindexa.
Los prefijos no aparecen como texto de la fuente en los resultados.

Cada resultado muestra ID de fragmento, documento y versión, categoría,
localizador, texto y referencia ensamblada desde metadatos. No inventa autores,
años, DOI ni páginas. En PDF se cita la posición del archivo, no una página
impresa supuesta. Se vuelve a comprobar la autorización después de calcular el
embedding de consulta y antes de ordenar candidatos. Los filtros se aplican
antes del top-k; una exclusión tiene efecto aunque el vector siga almacenado.

### Qué significa una búsqueda

La salida son **fragmentos candidatos**, no una respuesta generada ni una
verificación factual. Distancia coseno menor significa mayor similitud; no es
una probabilidad de verdad. Sin corpus autorizado o sin candidatos que superen
el filtro se devuelve «No encuentro información suficiente en las fuentes
autorizadas».

`--max-distance 0.5` permite ensayar un umbral, pero ese valor es solo un ejemplo:
debe calibrarse con consultas respondibles y no respondibles de tu corpus.
No hay un umbral universal activado por defecto. Por ello, una pregunta ajena al
corpus puede devolver candidatos poco pertinentes y deberá ser rechazada por la
etapa posterior de generación/revisión. La evaluación docente amplia de 20
preguntas prevista para el MVP completo sigue pendiente.

El adaptador comprueba que el modelo anuncie embeddings, tamaño local y digest,
y rechaza metadatos de modelo remoto. Las peticiones son solo a loopback, sin
proxies ni redirecciones y sin fallback cloud. Se solicita descargar el modelo
de memoria al terminar cada lote, priorizando RAM frente a velocidad. No se ha
modificado la configuración global de Ollama; estas comprobaciones no constituyen
una auditoría de un servidor local alterado o de su tráfico. Las pruebas reales
han usado exclusivamente el modelo local seleccionado y textos sintéticos.

### Verificación de fase 4

171 tests de las fases 1–4 superados sin red real: filtros previos, cambios de
permisos durante consulta/indexación, fallos de lote, diferencias de dimensión y
digest, migración, localizadores, reanudación y contratos de Ollama.

Prueba manual con el Ollama instalado: 4 documentos sintéticos, 8 preguntas en
español/gallego, 8/8 fuentes esperadas en primer lugar. Indexación: 4.61 s;
consultas: 0.87–0.90 s incluyendo embeddings. Dimensión observada: 1024.
Es un smoke test reducido, no una medida de calidad sobre la biblioteca real.

Microbenchmark SQL independiente: 1 000/10 000 vectores sintéticos, filtrados a
500/5 000 candidatos. P95 de 20 consultas calientes: aproximadamente 0.004/0.061 s.
Máximo RSS del proceso Python del microbenchmark: 51.7 MiB; **no incluye Ollama**.
No es una medición de latencia completa sobre documentos reales.

Para repetir las comprobaciones manuales (Ollama solo para la primera):

```sh
uv run --locked python scripts/check_rag_local.py --report data/verification/rag-smoke.json
uv run --locked python scripts/benchmark_vector_store.py
```

Los scripts trabajan en bases temporales. El informe opcional se guarda bajo
`data/` y está excluido de Git. No se ha cargado tu biblioteca personal ni creado
un calendario ficticio en la base de trabajo. La generación de fase 5 se describe
a continuación; todavía no existe `prepare class`.

El wheel 0.4.0 también se instaló en un entorno Python 3.12 limpio usando las
versiones exportadas de `uv.lock`: CLI y carga de sqlite-vec verificadas.
La prueba inicial de instalación sin red encontró que sqlite-vec no estaba
resuelto completamente en caché; se completó la instalación normal desde el
registro. Esto afecta a la preparación del entorno, no a la búsqueda local.

## Generación documentada con Ollama (fase 5)

`ask` genera respuestas breves basadas en los fragmentos recuperados. Cada
resultado válido queda como **borrador**, nunca como material aprobado. No es
un plan de clase: objetivos, actividades y temporalización pedagógica se
incorporarán en fases 6 y 7.

Se ha preparado `config/generation.yaml` (local, excluido de Git) con
`qwen3:14b`, ya instalado. El modelo, temperatura, contexto, salida máxima y
timeout son configurables; no se descargan modelos automáticamente. En otra
instalación se puede copiar y adaptar `config/generation.example.yaml`.

Después de configurar asignaturas, importar/revisar/autorizar fuentes e indexarlas:

```sh
uv run --locked docente-ai ask '¿Qué caracteriza al Ars Nova según estas fuentes?' --subject historia-i
uv run --locked docente-ai ask '¿Qué dificultades registré al trabajar el pulso?' --subject musica-eso --category profesor
uv run --locked docente-ai ask 'Resume el papel del filtro en la síntesis sustractiva' --subject ntam --output respuesta.md
uv run --locked docente-ai generation list
uv run --locked docente-ai generation show RUN_ID
```

Usa tus IDs reales de asignatura y el identificador devuelto por la consulta.
No se ha importado ninguna biblioteca personal ni calendario ficticio en la
base de trabajo. `ask` admite `--db`, `--rag-config`, `--generation-config`,
`--document` repetible, `--category`, `--top-k`, `--max-distance` y `--json`.
La categoría por defecto es documental; las notas del profesor se incluyen solo
si se solicita `profesor` o `all`, y se mantienen etiquetadas.

### Respuesta, evidencia y control del profesor

El modelo recibe la pregunta y fragmentos delimitados como datos, sin herramientas,
navegación ni ejecución de código. Debe devolver JSON estructurado con un máximo
de tres afirmaciones, cada una marcada como síntesis o inferencia de IA y ligada
a una cita textual de las fuentes enviadas. El código comprueba el esquema,
los identificadores y la coincidencia de las citas (normalizando solo espacios).
Construye las referencias a partir de los metadatos y localizadores conservados.
Rechaza citas inexistentes, campos adicionales y referencias libres como páginas,
DOI o URL introducidas por el modelo. No se publica la respuesta cruda rechazada.

Esto **no demuestra** que una afirmación se deduzca de su cita o que sea verdadera:
la revisión semántica sigue correspondiendo al profesor. Un modelo podría adjuntar
una cita real a una inferencia errónea. Todas las síntesis se señalan como IA,
las inferencias se distinguen y los extractos originales se muestran aparte.
No se promueve contenido generado a fuente documental ni se incorpora al índice.

Sin fuentes autorizadas o sin resultados del filtro, el sistema se abstiene sin
abrir modelos generativos. Con candidatos, el modelo también puede declarar que
son insuficientes. La similitud vectorial no garantiza relevancia: el umbral
opcional y la revisión del contenido siguen siendo necesarios. No se promete una
detección infalible de preguntas ajenas al corpus a partir de estas pruebas.

### Presupuesto y errores

La configuración inicial usa contexto 4096, salida máxima 512 tokens, temperatura
0 y `think: false`. Se cuenta de forma conservadora el tamaño UTF-8 de mensajes y
esquema, con margen reservado para la plantilla chat y la salida. Es una estimación,
no un tokenizador universal. Se seleccionan fragmentos completos, retirando
textos duplicados y omitiendo los que no caben; el registro indica cuáles se
omitieron. Nunca se corta una cita ni se elimina una fuente silenciosamente.
Si no cabe ningún fragmento, la consulta falla con una explicación.

La respuesta se rechaza si falta el fin normal, se alcanza el límite de salida,
faltan métricas de tokens, se supera el presupuesto observado o aparece una
petición de herramientas. La API no proporciona una garantía universal de que
cualquier plantilla/modelo arbitrario conserve íntegro el prompt: el presupuesto
conservador y las comprobaciones reducen ese riesgo y deben reevaluarse al cambiar
modelo. Los cambios de identidad del modelo durante la llamada también se rechazan.

Se permite una llamada inicial y hasta dos reparaciones de errores recuperables
de JSON, contrato, campos extra, valores no permitidos, citas no resolubles o
salida truncada. Cada reparación añade la respuesta anterior y una instrucción
determinista con el error del validador; se conservan las fuentes originales.
Si se alcanza el límite de salida, se solicitan como máximo cinco claims breves
sin aumentar tokens. Nunca se publica un borrador sin superar de nuevo todas las
validaciones y comprobar la vigencia de las fuentes. Red, autorización, cambio de
fuentes y cancelación no activan reparaciones de contenido. DeepSeek puede repetir
una petición HTTP una sola vez, con espera de 0.5 s, ante 429, 5xx o timeout;
401 y 403 se detienen inmediatamente. Los intentos y sus tokens quedan en la
auditoría `metrics.attempts`; la interfaz indica cuándo repara la respuesta. Un
error de conexión, timeout, JSON inválido o cita incorrecta deja un registro
`failed`; repetir `ask` crea otro registro. Ctrl-C deja `cancelled` cuando el
proceso puede manejar la interrupción. Un cierre forzado puede dejar `running`,
que se muestra como operación incompleta, no como borrador. Cerrar la conexión
no garantiza cancelar inmediatamente el trabajo que Ollama ya recibió.

Embeddings y generación se ejecutan secuencialmente; el proveedor recibe
`keep_alive: 0`. No se altera la configuración global del servidor ni se arranca
otro servicio. El adaptador de transporte/identidad local se comparte con la fase
4. Ollama mantiene loopback y pesos locales verificados. El adaptador remoto usa
HTTPS hacia el destino confirmado, sin proxies heredados, redirecciones,
herramientas ni cambio automático de proveedor.

La discrepancia de versiones observada se ha identificado: Homebrew proporciona
el cliente CLI 0.15.4 y la aplicación Ollama proporciona el servidor 0.33.3,
escuchando en 127.0.0.1:11434. La aplicación docente utiliza directamente esa API
HTTP; no depende del cliente CLI ni se han actualizado herramientas globales.

### Registro local y exportación

La migración SQLite 3→4 añade `generation_runs` sin cambiar documentos ni índices.
Guarda pregunta, configuración, modelo/digest, versión de prompt/aplicación,
mensajes enviados, selección de evidencia con metadatos/localizadores, fragmentos
omitidos, perfil recuperador, métricas y resultado/estado. Los errores quedan
registrados; la respuesta cruda del modelo se conserva solo en SQLite para
inspección técnica local, no en la salida normal ni JSON de `generation show`.
No se almacena el campo interno `thinking`.

Estados: `running`, `draft`, `abstained`, `failed`, `cancelled`. No existe aprobación
automática. La autorización, integridad y vigencia de todas las fuentes enviadas
se comprueban antes y después de la generación. Si cambian durante la llamada,
la respuesta se rechaza. Consultar posteriormente un borrador cuyas fuentes ya
no están vigentes muestra un aviso histórico y conserva la trazabilidad original.

`--output archivo.md` exporta a un archivo nuevo dentro de un directorio existente;
no sobrescribe archivos ni permite exportar en el almacén de fuentes. El registro
principal permanece en SQLite. `generation show RUN_ID --output copia.md` permite
exportarlo después. La exportación de archivo y SQLite no constituyen una
transacción única: si falla escribir el archivo, el mensaje identifica el
registro que sí quedó guardado.

### Verificación de fase 5

220 tests offline superados. Incluyen el contrato HTTP, modelos remotos,
respuestas parciales, presupuesto, citas inventadas, exclusiones durante generación,
metadatos modificados, abstención, cancelación, historial, exportación y migración.

Prueba real con `qwen3:14b` sobre un texto sintético: respuesta documentada en
28.36 s (dos citas literales comprobadas) y abstención en 10.13 s ante una pregunta
sin respaldo. Excluir la fuente produjo abstención sin generación. Son tres
comprobaciones pequeñas, no una evaluación pedagógica ni una garantía general de
veracidad. No se ha medido el pico de memoria del servidor para esta fase.

```sh
uv run --locked python scripts/check_generation_local.py --report data/verification/generation-smoke.json
```

El script utiliza una base temporal y un texto sintético; necesita ambos modelos
instalados y Ollama operativo. El informe local incluye un ejemplo de Markdown.
Documentación de referencia: [API chat](https://docs.ollama.com/api/chat),
[JSON estructurado](https://docs.ollama.com/capabilities/structured-outputs) y
[control de thinking](https://docs.ollama.com/capabilities/thinking).

## Primer agente pedagógico (fase 6)

El comando `pedagogy` recibe un tema, un grupo y una duración elegidos por el
profesor. Consulta el corpus autorizado de la asignatura del grupo y pide una
propuesta a un único modelo Ollama. No necesita un framework de agentes ni
modelos simultáneos. La selección de sesión desde el calendario y el flujo de
edición/aprobación quedan para la fase 7.

Preparación: configura e importa tus grupos, importa y autoriza las fuentes e
indéxalas como se describe arriba. Los identificadores siguientes son ficticios;
no se ha importado un calendario personal ni una biblioteca real.

```sh
# Solo la primera vez; no sobrescribir una configuración propia.
cp -n config/pedagogy.example.yaml config/pedagogy.yaml

uv run --locked docente-ai pedagogy "Practicar el pulso regular" \
  --group historia-3gp --duration 30 \
  --criteria "Instrucciones breves y comprobación final del aprendizaje"

# Si el profesor quiere asociar una unidad de la programación:
uv run --locked docente-ai pedagogy "Escucha y contexto histórico" \
  --group historia-3gp --duration 60 --unit unidad-1 \
  --output propuesta-historia.md

uv run --locked docente-ai generation list
uv run --locked docente-ai generation show ID_DEL_REGISTRO
```

`--unit` solo acepta unidades de la programación del grupo. Si se omite, no se
elige automáticamente una unidad. `--criteria` admite hasta 2000 caracteres y
`--duration` entre 5 y 240 minutos. El nivel y el idioma proceden de la
configuración del grupo. Todavía no hay memoria de experiencias anteriores.

Se conservan los filtros `--category`, `--document`, `--top-k`, `--max-distance`,
`--db`, `--rag-config`, `--generation-config` y `--json`. Por defecto se usan fuentes
documentales; `--category all` permite además materiales autorizados del profesor,
identificados como tales en la salida.

La configuración pedagógica es independiente de `ask`: el ejemplo utiliza el
modelo local elegido, `qwen3:14b`, con contexto de 6144 y salida máxima de 1536
tokens, porque una propuesta necesita más espacio que una respuesta breve.
Estos valores son editables en YAML; no se descarga ningún modelo al ejecutar.
Se mantiene `keep_alive: 0` y se cierra el adaptador de embeddings antes de generar.

El contrato `pedagogy:1` contiene hasta tres síntesis o inferencias documentadas,
objetivos, dificultad propuesta, de dos a cinco actividades, recursos por preparar
y observaciones. Cada actividad enlaza con esos contenidos; los minutos deben
sumar exactamente la duración solicitada. Se rechazan citas no literales,
identificadores desconocidos, tiempos incorrectos, respuestas truncadas y campos
no permitidos. Una abstención no puede contener un plan.

La salida separa **criterios del profesor**, **propuesta pedagógica de IA** y
**contenidos con evidencias documentales o del profesor**. Se verifican estructura,
citas y procedencia, pero eso no demuestra la corrección factual, la adecuación
pedagógica ni que el vínculo entre actividad y fuente sea suficiente. El profesor
revisa esas cuestiones. Los recursos son propuestas por preparar, no un inventario
de material disponible.

El historial SQLite existente guarda el contexto docente elegido, los prompts,
fragmentos, modelo y digest, respuesta, métricas y errores. No se requiere una
migración nueva: los contratos versionados comparten `generation_runs`. Las
fuentes se comprueban antes y después de generar; un cambio de autorización o
versión impide publicar el borrador. El contexto docente guardado es una
instantánea de aquella ejecución. Para modificar criterios, duración o unidad,
ejecuta de nuevo el comando; cada intento queda separado. La exportación Markdown
no sobrescribe archivos existentes ni escribe en la biblioteca de fuentes.

### Estadísticas de generación

En **Ajustes → Calidad de generación**, elige cuántas ejecuciones recientes
consultar. Se muestran los porcentajes de borradores, fallos y abstenciones sobre
el total seleccionado, los borradores recuperados con reparación y los errores
agrupados por tipo. Canceladas y en curso también forman parte del total.
Los fallos anteriores que no tienen un tipo registrado se agrupan como
`legacy_untyped`; no se deduce su categoría comparando mensajes de error.

```sh
uv run --locked docente-ai runs stats --limit 100
uv run --locked docente-ai runs stats --limit 50 --json
```

Las estadísticas leen únicamente estados y métricas; no necesitan prompts ni
fuentes. La API equivalente es `GET /api/runs/stats?limit=100`.

Prueba manual aislada con Ollama, usando exclusivamente texto sintético:

```sh
uv run --locked python scripts/check_pedagogy_local.py \
  --report data/verification/pedagogy-smoke.json
```

Verificación de fase 6: 256 tests offline, incluidos tiempos incoherentes,
referencias inexistentes, exclusión de fuentes durante la generación, mezcla de
categorías, presupuestos, cancelación, historial y exportación. El paquete 0.6.0
se instala en un entorno independiente.

Durante la prueba real, el contexto inicial de 8192 provocó errores Metal de
memoria insuficiente en una segunda consulta con Qwen3 14B. Ollama devolvió una
respuesta vacía con `done: false`, que fue rechazada. El ejemplo se ajustó a 6144
de contexto y `num_batch: 128`; este último parámetro está validado y es editable
entre 1 y 512. Véase el [contrato de opciones de Ollama](https://github.com/ollama/ollama/blob/main/api/types.go).
No se cambió el servidor, el modelo ni la configuración global de Ollama.

Con la configuración ajustada, la prueba completa pasó: propuesta de 30 minutos
en 53.2 s, abstención en 13.1 s y abstención sin llamada generativa al excluir la
fuente. Son mediciones sobre texto sintético, no una garantía para todo corpus ni
para cualquier carga de memoria. Resultado local: `data/verification/pedagogy-smoke.json`;
ejemplo legible: `data/verification/pedagogy-example.md`.

### Smoke y referencias visuales de la interfaz

La comprobación opcional usa Playwright (navegador real) y Pillow (diferencia
exacta de píxeles), exclusivamente en el grupo de desarrollo `ui`:

```bash
uv sync --locked --group ui
uv run --locked --group ui playwright install chromium
uv run --locked --group ui python scripts/check_ui_local.py --output tmp/ui-smoke
```

`tests/test_ui_smoke.py` se salta si faltan las herramientas o Chromium. Recorre
las cinco vistas, fuentes, respuestas, pestañas de Egipto y la impresión, en
escritorio y móvil. Todas las peticiones se interceptan y se sirven con el cliente
ASGI en memoria sobre fixtures temporales: no abre sockets ni consulta servicios
o datos personales. Mantiene el bloqueo de red de `conftest.py`.

Las doce capturas originales están en `tests/ui_baseline/`, con reloj, idioma,
zona horaria y viewport fijos. La comparación aplica la tolerancia indicada abajo
en el mismo sistema y versión de Chromium (exacta con `--strict`); en otros entornos el smoke sigue activo y el informe indica
que la comparación visual no es aplicable. Los informes y diferencias PNG se
guardan en el directorio indicado. Solo `--update-baseline` permite renovar
explícitamente las referencias; no usarlo para ocultar regresiones.

Los estilos se organizan en `src/docente_ai/web/static/css/`; `style.css` mantiene
el orden de sus importaciones locales. No hay compilador CSS, dependencias npm
ni URL externas. Diario y Ajustes conservan su presentación mediante los estilos
compartidos existentes.

El frontend utiliza módulos ES nativos en `static/js`: `main.js` coordina la navegación y los eventos, `api.js` concentra las peticiones, `state.js` conserva un único estado y `ui.js` reúne utilidades. Las cinco secciones viven en `vistas/` y los documentos, trabajos, audiciones y materiales compartidos en `componentes/`. Los imports internos no llevan parámetros de versión y los assets se sirven con `Cache-Control: no-store`. Mermaid permanece como script clásico local, fuera del grafo ES.

`tests/test_frontend_modules.py` comprueba que no hay ciclos ni imports de otra vista: cada vista solo puede depender de `api.js`, `state.js`, `ui.js` y `componentes/`.

Los scripts se sirven desde archivos locales con `script-src 'self'`: no se permiten scripts inline. Los botones de láminas utilizan el mismo manejador de eventos delegado en `main.js`, sin atributos `onclick` ni funciones globales.

El panel Horario y Calendario de Ajustes se genera exclusivamente desde los grupos, reglas semanales y excepciones importados. Muestra días, horas, aulas, cancelaciones y cambios puntuales por grupo. Sin grupos invita a crear o importar la configuración; no contiene horarios personales de ejemplo.

Para mantener el JavaScript legible se usan funciones de panel/fila y fragmentos HTML unidos sin introducir espacios. Los módulos tienen líneas de hasta 120 caracteres. Como herramienta de desarrollo opcional, `uv tool run --from jsbeautifier==2.0.3 js-beautify` permite formatear código JS desde una herramienta Python sin npm; no es dependencia del proyecto. No aplicar el formateador directamente a plantillas HTML: puede modificar literales. Toda edición debe preservar las cadenas y superar la comparación visual estricta.

El smoke visual admite por defecto como máximo un 0,01 % de píxeles distintos y una diferencia máxima de 2 niveles en cada canal RGB; deben cumplirse ambos límites y las dimensiones deben coincidir. El informe siempre conserva el número exacto de diferencias. Ejecuta `uv run --locked --group ui python scripts/check_ui_local.py --strict` para exigir cero diferencias, o `DOCENTE_UI_STRICT=1 uv run --locked pytest` para la suite estricta. No se toma una captura adicional de calentamiento. Para una modificación visual intencionada puede actualizarse únicamente Ajustes mediante `--update-baseline --update-views ajustes`; nunca se actualizan referencias automáticamente.

El test de interpolaciones analiza todos los módulos, plantillas anidadas y fragmentos HTML unidos. Exige `e()` para datos o constructores incluidos en la lista explícita `HTML_SEGURO` de `tests/ui_templates.py`. Las excepciones internas de los constructores base están enumeradas y revisadas: texto previamente escapado de Markdown, SVG literal y parámetros de HTML compuesto de cabecera/diálogo. No pasar texto de la API como HTML compuesto. Este análisis léxico es una guarda para la sintaxis utilizada por el proyecto, no un analizador general de JavaScript; la sintaxis nueva requiere ampliar sus casos de prueba.

### Materias, colores y períodos configurables

En Ajustes se pueden editar el color opcional `#RRGGBB` y los períodos ordenados
de cada materia. `teaching.yaml` admite `color` y `periods: [{id, nombre}]`;
importación y exportación conservan ambos campos. El identificador del período
es el nombre de su carpeta, sin separadores ni rutas relativas; `nombre` es su
etiqueta visible. Una lista vacía permite trabajar sin períodos. Cambiar un
identificador crea otra carpeta y conserva los archivos anteriores.

Sin color se utiliza una paleta fija mediante un hash estable del identificador.
La interfaz aplica variables CSS, sin selectores específicos por asignatura.
La migración SQLite 8 y la lectura de YAML antiguo añaden únicamente los períodos
históricos de Historia I y II cuando falta `periods`, conservando exactamente sus
carpetas; una lista explícita vacía no se modifica. Las materias nuevas no
reciben carpetas temáticas predeterminadas.

La interfaz sigue utilizando módulos ES nativos, sin compilador ni dependencias
npm. Las acciones y formularios se mantienen en sus vistas o componentes;
`main.js` coordina el registro, los eventos y la navegación. La suite comprueba
que todos los controles tienen manejador y que no hay nombres duplicados.

### Marca y compatibilidad del lanzador

La marca visible es **Arkhé** (en mayúsculas, **ARKHÉ**). El símbolo representa
un arco y un libro abierto, con un trazo que recuerda el acento del nombre.
El bundle macOS es `Arkhe.app`, con nombre y nombre visible `Arkhé`. Para
generarlo junto al proyecto: `uv run --locked --group ui python scripts/build_macos_app.py`.
Utiliza Pillow del grupo opcional `ui` ya existente para crear el icono ICNS;
no añade dependencias. El lanzador sigue usando `.venv/bin/docente-ai`.

Se conserva `Enjambre.app`: puedes eliminarlo manualmente cuando quieras.
Durante esta versión el servidor publica tanto `X-Arkhe-Workspace` como
`X-Enjambre-Workspace`; el lanzador acepta cualquiera de las dos cabeceras para
reutilizar el servidor correcto. El paquete Python, comando, servicio del
Llavero, rutas de datos y esquema SQLite permanecen intactos. También se
conservan las claves internas de localStorage, eventos JS y UID del calendario
para mantener preferencias y evitar duplicar sesiones ya importadas.


### Progreso en directo y cancelación

Las consultas del Asistente y las propuestas muestran etapas, lotes de relevancia
revisados e intentos de reparación. Ollama, DeepSeek y Mistral entregan también
texto progresivo en el panel **Borrador sin verificar**. Se muestra únicamente como
texto: no es una respuesta validada, no tiene citas comprobadas y no se incluye
al imprimir ni exportar. Al reparar se descarta el texto del intento anterior;
al terminar se sustituye por la respuesta documentada o por el aviso de error.

El contador muestra caracteres mientras llega texto y tokens cuando el proveedor
informa del consumo real; no estima ni inventa tokens. El endpoint personalizado
conserva la entrega completa al terminar, con progreso de etapas, porque su
capacidad de streaming no está acreditada en el preset. No se cambia de proveedor
si falla el transporte. El botón **Cancelar consulta** interrumpe la petición
HTTP activa y registra `cancelled`, sin publicar el texto provisional. Una tarea
cancelada mientras espera en cola no llama al modelo ni crea un registro generativo.
Recargar o cerrar el canal de progreso no cancela una consulta: se recupera su
estado al volver a abrir la aplicación.

## Piloto servidor (en preparación)

`docente-ai serve --server --public-host arkhe.ejemplo.es --workspace /datos/usuario`
activa una frontera distinta del modo `ui`: IP privada de escucha, Host público
único y proxy HTTPS explícito. No publica acciones de Finder ni cierre del proceso;
la biblioteca se utiliza con subida y descarga. El modo local permanece igual.
No publicar este modo sin la autenticación y el despliegue completo del piloto.

El acceso del servidor utiliza una cuenta por instancia creada con `docente-ai
server-user --auth-file /ruta/protegida/user.json --username docente` (contraseña
interactiva). El hash scrypt vive fuera del volumen de la biblioteca. Sesiones
opacas de ocho horas, cookie Secure/HttpOnly/SameSite=Strict, cinco intentos por
IP cada quince minutos y cierre de sesión. Reiniciar revoca todas las sesiones.


El piloto Docker usa Python 3.12 y `uv sync --locked --no-dev`, UID 10001,
workspace persistente nuevo y dos redes: privada interna y salida. Solo Caddy
publica 80/443; Arkhé y Ollama escuchan en sus IP privadas. Caddy entrega HTTPS y
sustituye forwarded headers. El contenedor no incluye datos ni configuraciones
personales. El servicio Ollama del piloto se prepara únicamente con bge-m3.


En Docker las claves solo se inyectan por `env_file: /etc/arkhe/.env`, protegido
con 0600 en el host. El piloto fija Mistral UE y bge-m3; bloquea claves desde Ajustes
incluido su borrado. El arranque crea únicamente configuración sin secretos y
exige el consentimiento remoto habitual antes de generar. Ver deploy/env.example.

Las copias del piloto detienen Arkhé brevemente, ejecutan SQLite `.backup` y
archivan Conocimiento, originales internos y configuraciones sin credenciales.
Timer diario UTC y rotación de catorce días. La restauración valida checksums,
rutas y SQLite y solo admite un destino nuevo vacío; no pisa el volumen activo.
Se añade sqlite3 como herramienta del sistema en la imagen, sin dependencia Python.


El piloto publica `/privacy` antes del acceso. Describe almacenamiento en la región
UE elegida, retención de copias, envío a Mistral, prohibición de datos del alumnado
 y contacto de borrado. Completa responsable, región y correo antes de publicarlo.
Mistral declara región europea UE/AELC: confirmar contractualmente UE estricta si
es requisito; el dominio europeo no demuestra por sí solo todas las ubicaciones.
