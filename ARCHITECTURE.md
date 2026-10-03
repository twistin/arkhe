# ENJAMBRE IA DOCENTE LOCAL — Arquitectura

Fecha: 18 de septiembre de 2026. Arquitectura aprobada por el profesor al autorizar la fase 1.

Estado actual: fase 6 implementada, incluido un rol pedagógico que propone objetivos, actividades y tiempos con base documental, consultas con Ollama y recuperación semántica local. La biblioteca documental ya importa y versiona PDF, DOCX, TXT y Markdown, con OCR local opcional. La CLI, el diagnóstico, la configuración docente, el calendario y la programación están disponibles; el resto de este documento describe el diseño incremental previsto.

Este documento recoge el análisis original de fase 0 y el diseño aprobado. La inspección de la sección 1 es una instantánea previa a la implementación; el estado operativo actual se documenta en README.md. La primera entrega será una CLI local para preparar una clase con fuentes verificables y guardar un borrador revisable.

## 1. Entorno inspeccionado

Inspección de la carpeta de trabajo, ejecutables, versiones y endpoints locales de Ollama. No se han leído bibliotecas personales ni documentos docentes.

| Elemento | Resultado observado |
|---|---|
| Proyecto | Carpeta `enjambre-docencia` vacía; no existe repositorio Git ni código previo |
| Instrucciones locales | No se encontraron archivos AGENTS.md en el proyecto ni en los directorios ascendentes comprobados |
| Hardware | Apple M1 Pro, ARM64, 16 GiB de memoria unificada; el equipo concreto es M1 Pro |
| Sistema | macOS 15.7.9 |
| Disco | Aproximadamente 113 GiB disponibles según `df` |
| Python predeterminado `python3` | 3.14.2, Homebrew |
| Otro Python, `python` | 3.12.12, Miniforge |
| SQLite de Python | 3.53.3 en Python 3.14; 3.51.1 en Python 3.12; ambos exponen carga de extensiones |
| FTS5 | Creación de tabla en memoria comprobada con Python 3.12 |
| SQLite de terminal | 3.39.0; no es la biblioteca utilizada por los intérpretes anteriores |
| Herramientas | Git 2.48.1, uv 0.7.12, pipx 1.7.1, Homebrew 6.0.22 |
| Ollama | Servidor responde en `127.0.0.1:11434`; API informa 0.33.3; CLI avisa de cliente 0.15.4 |
| Modelo instalado | `qwen3:14b`, Q4_K_M, 14.8B parámetros, aproximadamente 9.3 GB en disco |
| Modelos cargados | Ninguno al consultar `/api/ps` |
| Embeddings | No aparece un modelo específico; el modelo instalado anuncia completion/tools/thinking |
| Aplicaciones en /Applications | Zotero 9.0.4, Obsidian 1.7.7, SuperCollider 3.14.1 |
| LilyPond | Ejecutable 2.24.4 disponible |
| SuperCollider CLI | `sclang` no está en PATH; esto no implica que falte dentro de la aplicación |
| Paquetes del futuro proyecto | No se detectaron pytest, pypdf, yaml, httpx, chromadb, qdrant_client, faiss, lancedb ni sqlite_vec en el Python 3.14 inspeccionado |

La disponibilidad de la API no demuestra rendimiento ni calidad pedagógica. No se ha ejecutado inferencia ni medido memoria bajo carga. No se ha verificado la versión de Better BibTeX ni habilitado la API de Zotero. La carga real de sqlite-vec queda pendiente: comprobar el método de carga de extensiones no equivale a probar el paquete.

## 2. Decisiones recomendadas

1. **Aplicación Python monousuario, CLI y ejecución secuencial.** Sin servidor web, Docker ni framework de agentes.
2. **Python 3.12 en un entorno virtual propio**, seleccionando explícitamente el intérprete disponible. No modificar los entornos globales. Resolver y bloquear dependencias con uv tras aprobar la fase 1.
3. **SQLite como fuente de verdad** de configuración docente importada, catálogo, fragmentos, índices y propuestas. Archivos originales y exportaciones en disco.
4. **SQLite + sqlite-vec para recuperación semántica inicial**, condicionada a una prueba ARM64 de instalación, filtrado y persistencia. Búsqueda exacta sobre el subconjunto autorizado; no empezar con un índice aproximado.
5. **Ollama nativo** para embeddings e inferencia, con modelos configurables por separado y sin servicios externos obligatorios.
6. **Un rol pedagógico y un orquestador determinista.** El orquestador es código que valida y coordina; no otro LLM que decide autónomamente qué ejecutar.
7. **Markdown como entrega inicial**, acompañado de un registro estructurado de procedencia. Toda generación nace como borrador.
8. **Separación explícita** entre documentación, material del profesor y generación de IA en almacenamiento, recuperación y presentación.

## 3. Componentes y flujo

```text
CLI
 └─ Servicio preparar clase / orquestador determinista
     ├─ Configuración, grupos, calendario y programación → SQLite
     ├─ Biblioteca → originales + extracción por localizador
     ├─ Recuperador → filtros SQL + embeddings + búsqueda vectorial
     ├─ Rol pedagógico → contexto delimitado → Ollama
     ├─ Validadores → estructura, referencias, citas y duración
     └─ Revisión del profesor → versión guardada + Markdown
```

El dominio no importa librerías de Ollama ni del motor vectorial. Interfaces pequeñas: `DocumentParser`, `Embedder`, `Retriever`, `LanguageModel` y `Renderer`. Un protocolo y una implementación cuando se necesiten; no un sistema de plugins dinámico anticipado.

El calendario, la programación, las autorizaciones y la persistencia se resuelven con código. El modelo propone objetivos y actividades, relaciona información recuperada y adapta el nivel. No modifica la biblioteca, marca contenidos como impartidos ni aprueba materiales.

### Comparación de arquitecturas de agentes

| Arquitectura | Ventaja | Coste y límite | Decisión |
|---|---|---|---|
| A. Un modelo con prompts especializados | Pocas dependencias; una generación principal por clase; fácil de inspeccionar | Menor diversidad de revisión; necesita validación externa | MVP |
| B. Roles secuenciales, mismo modelo o distintos | Etapas pedagógica, especialista y crítico evaluables por separado | Varias inferencias, más latencia y posible propagación de errores | Incorporar solo si mejora una evaluación docente |
| C. Roles paralelos + crítico + síntesis | Contraste de propuestas | Competencia por memoria, más contexto y coordinación; consenso no garantiza verdad | Posponer; poco adecuado como inicio en 16 GiB |

El crítico inicial será determinista: comprueba identificadores, campos y tiempos. No se presentará como verificador de verdad factual. Un crítico LLM posterior tampoco sustituirá al profesor.

## 4. Ollama y presupuesto del equipo

Ollama permite aislar la aplicación del modelo mediante HTTP local. Se utilizarán adaptadores para chat y embeddings; la API de embeddings admite entradas por lotes y permite rechazar truncamiento mediante `truncate: false`. [API de embeddings](https://docs.ollama.com/api/embed).

El modelo actual puede servir para una prueba posterior, pero 9.3 GB de archivo no equivalen a memoria total: hay pesos, contexto, cachés, sistema operativo y aplicaciones. Recomiendo evaluar también un modelo instruct cuantizado de aproximadamente 4–8B antes de fijar la configuración cotidiana; el nombre definitivo dependerá de calidad en español/gallego, formato estructurado, licencia y rendimiento medido. No se descargará ni seleccionará implícitamente.

Embeddings requieren selección independiente: modelo multilingüe pequeño, con pruebas sobre español, gallego, nombres musicales y textos técnicos. Registrar identificador, digest, dimensión y normalización. Cambiarlo exige reindexar; nunca comparar vectores de espacios diferentes.

Configuración inicial propuesta: una petición a la vez, contexto de partida de 4096 tokens y límite de salida explícito. Son parámetros a ajustar tras medir, no promesas de rendimiento. El presupuesto del prompt debe reservar espacio para instrucciones, programación, evidencias y salida; si no cabe, reducir contexto recuperado y explicitar qué quedó fuera. No usar automáticamente el contexto máximo anunciado por el modelo.

Embeddings e inferencia se ejecutarán secuencialmente, con lotes pequeños y descarga de modelos cuando proceda. Ollama documenta controles de contexto, concurrencia y permanencia en memoria. [Configuración y memoria](https://docs.ollama.com/faq).

Antes de la integración: investigar y alinear cliente y servidor sin actualizaciones globales automáticas. Probar timeouts, respuestas inválidas, modelo ausente y cancelación. No sustituir fallos por una API cloud.

## 5. Comparación de recuperación local

Evaluación de arquitectura, no benchmark. Los costes de RAM son relativos y dependen del corpus, dimensión e índice; no se atribuyen mediciones inexistentes.

| Opción | Instalación/local en macOS | RAM y mantenimiento | Filtros y metadatos | Escala y valoración |
|---|---|---|---|---|
| **SQLite + sqlite-vec** | Paquete Python y extensión nativa; verificar ARM64 y SQLite del entorno | Pocas piezas; una base; extensión joven que debe fijarse y probarse | SQL relacional; muy conveniente para asignaturas, permisos y procedencia | Búsqueda exacta adecuada como comienzo; coste lineal; recomendada |
| **Chroma persistente** | Uso embebido sin servidor obligatorio | Más dependencias y almacenamiento de índice separado del dominio | API de metadatos y filtros; embeddings suministrados explícitamente por la aplicación | Cómodo para RAG; alternativa si reduce trabajo medido |
| **Qdrant local** | Cliente Python con persistencia local, sin Docker obligatorio en este modo | Añade otro almacén; no confundir sus características con el servidor Qdrant | Payload y filtrado; conservar autoridad de permisos en SQLite | Buena alternativa; pasar a servidor implicaría una nueva decisión operativa |
| **FAISS CPU** | Biblioteca nativa; verificar distribución compatible | Índice y mapeo de IDs a cargo de la aplicación; RAM depende del índice | No resuelve por sí sola catálogo y relaciones docentes | Potente búsqueda, pero demasiada sincronización propia para este MVP |
| **LanceDB OSS embebido** | Biblioteca local con dependencias nativas | Motor y tablas adicionales; mayor superficie técnica que SQLite único | Metadatos y filtros SQL | Interesante al crecer; innecesario inicialmente |

Referencias de cada alternativa: [sqlite-vec](https://alexgarcia.xyz/sqlite-vec/), [Chroma](https://docs.trychroma.com/), [cliente Qdrant y modo local](https://github.com/qdrant/qdrant-client), [FAISS](https://github.com/facebookresearch/faiss), [LanceDB](https://docs.lancedb.com/), [filtros LanceDB](https://docs.lancedb.com/search/filtering/).

### Elección concreta y salida de emergencia

Usar vectores float32 en tablas SQLite normales y funciones de distancia de sqlite-vec. SQL selecciona primero fragmentos vigentes y autorizados; se ordenan esos candidatos por distancia y se limita el resultado. Así se conservan filtros muchos-a-muchos sin depender inicialmente de las restricciones de una tabla vectorial especial. [Modalidades de consulta sqlite-vec](https://alexgarcia.xyz/sqlite-vec/features/knn.html).

Las extensiones SQLite no están habilitadas en todos los Python de macOS; el entorno observado sí expone el método, pero faltan instalación y carga reales. Fijar una versión estable probada, no adoptar una versión alfa solo porque aparezca en documentación. [Integración Python](https://alexgarcia.xyz/sqlite-vec/python.html).

Puerta de decisión en fase 4: comprobar instalación limpia, persistencia, exclusión de documentos y búsqueda con relaciones de asignatura. Si falla o exige compilar componentes complejos, reevaluar Qdrant local; no mantener dos motores simultáneamente.

Como referencia aritmética, 10 000 vectores de dimensión 768 en float32 ocupan unos 29.3 MiB en bruto. No incluye texto, base, cachés ni proceso. Ensayar 1 000 y 10 000 fragmentos, medir latencia y memoria; objetivo provisional de búsqueda caliente p95 inferior a 2 s, sin contar generación del embedding. Si el corpus real o la latencia lo requieren, evaluar `vec0` u otro motor con mediciones.

FTS5 será una mejora posterior para nombres, fechas y términos exactos, combinada con búsqueda semántica. No sustituye la búsqueda semántica exigida para el MVP.

## 6. Ingesta, recuperación y trazabilidad

### Ingesta

Ingesta actual: TXT UTF-8, Markdown, DOCX mediante python-docx y PDF mediante pypdf, con OCRmyPDF opcional para páginas escaneadas. Los originales son inmutables y se identifican con SHA-256. EPUB continúa pendiente.

Pasos: registrar origen y categoría → validar archivo → calcular hash → extraer por página o sección → mostrar resumen de extracción → autorizar → fragmentar → generar embeddings → activar versión del índice. Una importación fallida queda visible como fallida, nunca como documento listo.

PDF cifrado o ilegible: informar y no producir falsa evidencia. Para páginas con menos de 20 caracteres alfanuméricos (también páginas blancas o portadas), utilizar OCRmyPDF únicamente si está en PATH; en su ausencia rechazar con instrucciones de instalación. El reconocimiento de partituras queda fuera. Los comentarios del profesor sobre una partitura pueden incorporarse como material propio.

DOCX se recorre por bloques del cuerpo principal en orden, conservando encabezados, listas de viñetas/numeradas y tablas como Markdown. Localizadores `docx_paragraph` con `paragraph_index` (párrafos vacíos incluidos) y `docx_table` con `table_index`, ambos con `section` y offsets. No se extraen imágenes, cuadros de texto, notas ni encabezados/pies de página. Una tabla sin fila de encabezado marcada recibe un encabezado Markdown vacío, sin convertir datos en títulos.

OCR se ejecuta en un directorio temporal privado, sin shell y sin registrar stdout/stderr, con `--force-ocr --pages … --output-type pdf --optimize 0 --jobs 2`, idiomas `spa+eng` (variable `DOCENTE_AI_OCR_LANGUAGES`) y timeout de 900 segundos. El diagnóstico solo comprueba PATH. No es una dependencia Python obligatoria ni se instala automáticamente. No se cambia el original. Tras validar la extracción y el número de páginas, se almacena otro `document_versions` con hash propio y extractor marcado `ocrmypdf:1`. Su `metadata_snapshot.extraction` contiene `text_origin: texto OCR`, `derived_from_version_id`, `original_sha256` y `tool`; el evento `derive_ocr` registra el vínculo. No requiere modificar el esquema SQLite. Solo la derivada se activa, inicialmente sin autorización y con revisión obligatoria. Al reimportar después de instalar OCR se reutiliza la versión original fallida. Las descargas diferencian original y derivada.

Los localizadores conservan `ocr_document` y, para páginas reconocidas, `text_origin: texto OCR`. Estos campos sobreviven a la fragmentación y acompañan citas en interfaz, CLI y anexos Markdown con aviso de posible error de reconocimiento. El validador de citas no cambia: coteja subcadenas exactas del texto almacenado autorizado. Un OCR inválido o que cambia el número de páginas falla; las páginas aún escasas requieren aceptación explícita de avisos.

La autorización, indexación, búsqueda y comprobaciones posteriores a la generación verifican el hash de la derivada y del original al que apunta su procedencia; un original ausente o alterado bloquea el uso de la fuente OCR.

Fragmentación inicial por párrafos dentro de una página, con tamaño y solapamiento configurables. Conservar texto extraído, offsets y versión del extractor. Respetar el límite real del modelo de embeddings, dividir al superar el límite y evitar truncamiento silencioso.

### Recuperación

1. Resolver asignatura y grupo por identificador; si hay ambigüedad, pedir selección.
2. Intersectar documentos activos, asociación a asignatura y selección explícita del profesor. Los documentos compartidos deben estar marcados como tales; nunca ampliar a toda la biblioteca por falta de resultados.
3. Aplicar por separado categorías documental y profesor. Generaciones previas no entran como evidencia.
4. Obtener embedding de consulta con el mismo perfil que el índice.
5. Recuperar candidatos, quitar redundancias y ajustar al presupuesto de contexto. Valor inicial de `top_k`: 6, ajustable tras evaluación.
6. Mostrar extractos, procedencia y limitaciones. Distancia vectorial no equivale a probabilidad de verdad.
7. Abstenerse si falta evidencia suficiente: «No encuentro información suficiente en las fuentes autorizadas.»

Un umbral universal no garantiza relevancia. Calibrarlo con consultas respondibles y no respondibles del corpus; exigir además soporte identificable para cada afirmación factual. Ante evidencia parcial, señalar lagunas y no completar con conocimiento interno del modelo. Se puede ofrecer una plantilla pedagógica vacía, claramente identificada, sin presentarla como explicación documentada.

### Contrato de referencias

El modelo devuelve IDs de fragmentos, no construye bibliografía libre. El código resuelve autores, fecha, título, localizadores y DOI desde el catálogo. Metadatos desconocidos permanecen vacíos; usar «sin autor identificado» o «s. f.» cuando corresponda.

Distinguir `pdf_page_index` (posición física, base 1), `page_label` (etiqueta del PDF) y `printed_page` (numeración impresa verificada). Solo esta última autoriza «Autor, año, p. XX». Si no está verificada: «Autor, año, página 12 del archivo PDF». Una etiqueta automática no prueba la numeración impresa. TXT/Markdown utilizan sección y líneas; DOCX utiliza párrafos o tablas y encabezados; nunca páginas ficticias.

Toda cita textual debe coincidir con el fragmento almacenado, salvo normalización controlada de espacios. IDs desconocidos o citas que no coinciden bloquean una salida válida. Las paráfrasis se etiquetan como síntesis/inferencia y las actividades como propuestas de IA. Una referencia existente no demuestra que la afirmación esté sustentada: la interfaz debe permitir revisar el extracto y el profesor debe validar el contenido.

Documentos y notas se delimitan como datos no confiables en el prompt. Las instrucciones incluidas en ellos no cambian permisos, herramientas ni política de fuentes. El LLM no tendrá ejecución de comandos, navegación ni acceso libre al disco.

## 7. Esquema de datos propuesto

SQLite con claves foráneas activadas, migraciones numeradas, transacciones y fechas ISO 8601. IDs internos estables; nombres editables nunca funcionan como claves. Campos JSON solo para estructuras acotadas y validadas, no para ocultar relaciones importantes.

| Entidad | Campos principales y relaciones |
|---|---|
| `centers` | id, nombre |
| `teachers` | id, nombre opcional; datos locales |
| `academic_years` | id, etiqueta, fecha_inicio, fecha_fin |
| `subjects` | id, nombre, descripción; sin enumeración fija de asignaturas |
| `groups` | id, subject_id, center_id, academic_year_id, teacher_id, nombre, nivel, idioma |
| `schedule_rules` | id, group_id, weekday ISO 1–7, hora local, duración positiva, aula, timezone, valid_from, valid_to |
| `calendar_exceptions` | id, schedule_rule_id, fecha, cancelación o sustitución de hora/duración/aula |
| `sessions` | id, group_id, schedule_rule_id opcional, inicio con zona, duración, estado planned/held/cancelled; instancia concreta |
| `curricula` | id, subject_id, academic_year_id, versión, documento_origen opcional |
| `curriculum_units` | id, curriculum_id, orden sugerido, título, objetivos, competencias, contenidos, criterios, actividades, repertorio, recursos y ventana temporal opcional |
| `group_curricula` | group_id, curriculum_id; programación aplicable |
| `documents` | id, categoría documental/profesor, título, autores ordenados, año opcional, editorial/revista, DOI, URL, tipo, origen, fecha_incorporación, enabled |
| `document_subjects` | document_id, subject_id; asociación muchos-a-muchos |
| `tags`, `collections` y relaciones | etiquetas y colecciones múltiples por documento |
| `document_versions` | id, document_id, sha256, ruta local, formato, número de páginas, fecha, extractor/version, estado de extracción |
| `chunks` | id, document_version_id, ordinal, texto, hash, página física/etiqueta/impresa verificable o sección/líneas, offsets |
| `embedding_profiles` | id, proveedor, modelo, digest, dimensión, normalización, versión de fragmentación |
| `chunk_embeddings` | chunk_id, profile_id, vector; unicidad por pareja; solo versiones activas en consulta |
| `generation_runs` | id, session_id, tema solicitado, fuentes autorizadas, modelo/digest, parámetros, versión prompt/aplicación, fecha, estado y advertencias |
| `retrieval_evidence` | run_id, chunk_id, rango, distancia, instantánea de metadatos y extracto utilizado |
| `proposals` | id, run_id, versión, estado draft/approved/rejected, contenido estructurado, Markdown, hash, versión_previa, fecha de revisión |
| `proposal_evidence` | proposal_id, bloque/afirmación, chunk_id, clase documental/profesor/inferencia/generación |

Las últimas dos clases describen la procedencia del bloque generado, no nuevas categorías de documento. Un libro y los apuntes que lo interpretan son registros distintos, enlazables mediante una relación de derivación.

Entidades reservadas para fase 8, sin crear todavía todas sus tablas: `session_records` (contenido realmente impartido, objetivos, actividades, material, tareas), `session_unit_progress` (grupo/unidad y progreso confirmado) y `feedback` (actividad, qué funcionó, qué falló, observaciones y próxima sesión). Feedback siempre es interpretación del profesor; no evidencia bibliográfica. Un plan aprobado no prueba que se haya impartido.

### Reglas de consistencia y conservación

- Calendario semanal acotado al curso, zona Europe/Madrid por defecto configurable; cancelar festivos mediante excepciones. Detectar solapamientos y horas inválidas o ambiguas por cambios horarios.
- La programación sugiere; no avanza sola. En el MVP el tema se elige explícitamente porque todavía no hay historial de impartición fiable.
- Reimportar el mismo hash no duplica fragmentos. Una modificación crea versión; solo activar el nuevo índice al completarse.
- Cambios de autorización se aplican en cada búsqueda y antes de generar. Excluir un documento no borra silenciosamente la evidencia histórica; propuestas previas quedan señaladas si sus fuentes ya no están autorizadas.
- Regenerar crea una nueva propuesta. Editar exige nueva versión; aprobar registra el hash exacto aprobado. Modificaciones posteriores invalidan esa aprobación.
- Una eliminación definitiva debe advertir qué trazabilidad se perderá. Por defecto, desactivar y conservar versiones usadas.

## 8. Configuración y carpetas

YAML para configuración de servicios y entrada docente; SQLite para estado operativo. Una importación validada actualiza SQLite transaccionalmente: el runtime no mezcla dos versiones contradictorias de YAML y base. Exportar configuración permite recuperar una vista editable.

Ejemplo conceptual, no configuración ya creada:

```yaml
schema_version: 1
privacy:
  local_only: true
ollama:
  host: http://127.0.0.1:11434
  generation_model: null  # elegir explícitamente tras evaluación
  embedding_model: null   # independiente del modelo generativo
  temperature: 0.2
  num_ctx: 4096
  timeout_seconds: 180
retrieval:
  backend: sqlite_vec
  top_k: 6
calendar:
  timezone: Europe/Madrid
storage:
  data_dir: ./data
teacher:
  name: null
```

Validar campos, versiones, IDs, referencias cruzadas, horarios y modelos ausentes con errores accionables. Configuración personal fuera de Git. Los valores anteriores son puntos de partida, no parámetros ajustados empíricamente.

```text
enjambre-docencia/
├── ARCHITECTURE.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── config/
│   ├── app.example.yaml
│   └── teaching.example.yaml
├── src/docente_ai/
│   ├── cli.py
│   ├── config.py
│   ├── domain.py
│   ├── storage.py
│   ├── migrations/
│   ├── teaching/         # calendario y programación
│   ├── library/          # catálogo, importación y parsers
│   ├── rag/              # embeddings, filtros y recuperación
│   ├── llm/              # adaptador Ollama
│   ├── agents/           # inicialmente solo rol pedagógico
│   ├── prompts/          # instrucciones versionadas
│   └── generation/       # orquestación, validación y Markdown
├── tests/
│   ├── fixtures/         # documentos sintéticos, sin datos privados
│   ├── unit/
│   └── integration/
└── data/                 # ignorado por Git; ruta configurable
    ├── docente.sqlite3
    ├── library/originals/
    ├── generated/
    └── backups/
```

Crear módulos cuando tengan una responsabilidad real, no llenar la estructura de carpetas vacías. Memoria, nuevos agentes y exportadores se incorporarán en sus fases.

Dependencias iniciales propuestas: PyYAML (lectura segura), httpx (HTTP con timeouts), pypdf (PDF textual), sqlite-vec (distancias vectoriales) y pytest para desarrollo. CLI con argparse; SQLite, dataclasses, pathlib, hashlib y zoneinfo de la biblioteca estándar. Validación explícita de datos; sin ORM ni LangChain. Fijar versiones tras verificar instalación y tests, no inventar un lockfile durante el análisis.

## 9. Zotero, Better BibTeX y Obsidian

**Primera integración posterior al núcleo:** importación explícita de exportación CSL-JSON o Better BibTeX JSON, conservando también el JSON original. BibTeX será un adaptador adicional; no es el formato canónico interno porque no representa con igual comodidad todos los metadatos y adjuntos.

Zotero seguirá siendo autoridad bibliográfica. Identidad externa compuesta por origen/instancia, biblioteca e item key cuando esté disponible; citekey útil para presentación, pero no identidad inmutable. Un PDF es adjunto/versionado del registro bibliográfico. Un archivo de metadatos no garantiza que el PDF esté presente: resolver rutas permitidas, mostrar ausencias y solicitar selección, sin descarga automática.

Better BibTeX puede mantener exportaciones locales actualizadas. El usuario elegirá colección y destino; la aplicación detectará cambios al importar, sin automatizaciones ocultas. [Exportación automática de Better BibTeX](https://retorque.re/zotero-better-bibtex/exporting/auto/).

**Segunda integración:** adaptador de lectura de la API local de Zotero en localhost:23119, activada explícitamente en Zotero. Comprobar capacidades de la versión instalada; la documentación actual incluye funciones de Zotero 10 que no deben suponerse disponibles en el Zotero 9 observado. No abrir ni modificar directamente su SQLite. [API local oficial](https://www.zotero.org/support/dev/web_api/v3/local_api).

Conflictos: refrescar metadatos externos conservando una capa separada de correcciones locales del profesor; mostrarlos antes de sobrescribir. Bajas externas desactivan registros importados tras revisión, sin destruir evidencia usada. Deduplicación de archivos por hash y de registros por identidad externa; no fusionar por título automáticamente.

Obsidian: importar Markdown desde archivos o carpetas expresamente elegidos, conservando ruta relativa, frontmatter y enlaces. Sus notas se clasifican como material del profesor; no importar todo el vault por defecto ni seguir enlaces fuera de la raíz autorizada. La API web de Zotero y otras integraciones cloud quedan fuera del MVP y siempre serán opcionales.

## 10. Privacidad, persistencia y mantenimiento

Solo loopback para Ollama por defecto, sin proxies heredados ni redirecciones a hosts externos. Verificar además que se usa un modelo local: un host localhost no basta para impedir que un servidor enrute hacia cloud. La documentación de Ollama permite desactivar funciones cloud con `OLLAMA_NO_CLOUD=1` o configuración equivalente; verificar soporte y estado durante la integración. No se ha cambiado esa configuración en esta fase. [Modo local de Ollama](https://docs.ollama.com/faq).

La instalación inicial de paquetes y modelos puede requerir Internet. La biblioteca,
extracción, índice, embeddings (bge-m3 como referencia) y diario se almacenan y
procesan localmente. Los modelos de embeddings configurados deben acreditar pesos
locales; no se sustituye Ollama por una API remota para embeddings. El modo Ollama
puede funcionar sin red externa; los presets remotos requieren conexión y confirmación.
No hay telemetría añadida ni acceso automático a URLs bibliográficas. Los proveedores
remotos reciben los datos enumerados en el contrato de privacidad al final de este
documento; ya no se afirma que toda generación permanece en el equipo.

Originales, SQLite y propuestas forman la copia de seguridad. Copia consistente mediante API de backup SQLite y manifiesto de hashes; no copiar solo el archivo principal mientras hay transacciones/WAL pendientes. Probar restauración. El índice puede reconstruirse, pero las versiones de originales y evidencia histórica no deben perderse.

Datos locales no significa datos cifrados: SQLite inicial no incorpora cifrado propio. Aprovechar permisos del usuario y protección del disco del sistema. Evitar identificadores personales de alumnos en el MVP; grupos y observaciones agregadas son suficientes.

## 11. MVP concreto y aceptación

### Incluido

- Configurar centros, asignaturas arbitrarias, grupos, curso, calendario semanal y excepciones básicas mediante YAML validado.
- Importar programación básica estructurada por unidades; no prometer interpretar automáticamente una programación PDF completa.
- Importar PDF textual, TXT y Markdown con metadatos editables y categoría explícita.
- Autorizar/excluir documentos, asociarlos a asignaturas, indexarlos y buscar semánticamente.
- Preparar una clase eligiendo grupo, fecha, tema, duración, dificultad, objetivos y fuentes; completar datos desde calendario cuando sean inequívocos.
- Consultar Ollama con evidencia; validar salida y guardar objetivos, contenidos, actividades, temporalización, recursos, fuentes y observaciones.
- Inspeccionar, editar, aprobar, rechazar o regenerar la propuesta; exportación Markdown y procedencia persistente.

CLI prevista: `docente-ai doctor`, `config validate`, `config import`, `calendar list`, `library import`, `library index`, `library exclude`, `search`, `prepare class`, `proposal show`, `proposal edit`, `proposal approve`, `proposal reject`. Los comandos de preparación y revisión de propuestas siguen previstos; config, calendar, library, search y ask ya están disponibles.

### Fuera del MVP

Preparación semanal automática, memoria adaptativa, agentes paralelos, integración viva con Zotero, EPUB, interfaz gráfica, exportaciones PDF/DOCX/PowerPoint, generación LilyPond/MIDI/SuperCollider, Whisper y análisis de audio. La arquitectura permite añadirlos sin convertirlos en requisitos iniciales.

### Pruebas y criterios de aceptación

1. Instalación reproducible en entorno limpio ARM64; `pytest` ejecuta la suite sin Internet ni Ollama mediante dobles de prueba. Las pruebas con Ollama real están marcadas y se ejecutan aparte, con resultado explícito.
2. Configuración: aceptar asignatura nueva sin cambiar código; rechazar IDs duplicados, referencias inexistentes y duraciones inválidas.
3. Calendario: resolver sesiones, excepciones, límites de curso y cambios horarios; no duplicar sesiones ni elegir ambiguamente un grupo.
4. Parsers: documentos sintéticos con páginas conocidas, TXT/Markdown, PDF vacío/escaneado/cifrado y errores de lectura; conservar localizadores comprobables.
5. Indexación: reimportación idempotente, cambio de versión, recuperación tras fallo parcial y rechazo de dimensiones incompatibles.
6. Recuperación: documentos excluidos y de asignaturas no autorizadas nunca aparecen, aunque sean los más cercanos. Prueba adicional de cambio de autorización entre búsqueda y generación.
7. Citas: rechazar IDs inventados, páginas no verificadas y citas textuales divergentes; comprobar ausencia de DOI/autor fabricados en la bibliografía renderizada.
8. Generación: sin corpus suficiente, abstenerse; ante timeout o JSON inválido conservar error y nunca marcar aprobado. No regenerar indefinidamente.
9. Revisión: edición crea versión, invalida aprobación anterior y conserva evidencia. Actividades deben sumar la duración solicitada y tener tiempos positivos.
10. Prueba completa real: importar un pequeño corpus autorizado, buscar, generar con Ollama, inspeccionar referencias, guardar, reiniciar y recuperar la misma propuesta. Repetir sin red externa.
11. Calidad: conjunto docente inicial de 20 preguntas, incluidas al menos 5 sin respuesta y consultas en los idiomas de trabajo. Objetivo provisional: evidencia correcta en top 6 en al menos 80% de las respondibles, ninguna referencia inexistente y abstención en todas las no respondibles del conjunto. Un conjunto pequeño no demuestra ausencia general de alucinaciones.
12. Rendimiento: medir búsqueda, tiempo total de generación, memoria y swap bajo carga. Objetivo provisional: propuesta sencilla en menos de 2 minutos sin presión sostenida de memoria; si no se cumple, ajustar modelo/contexto antes de declarar usable el MVP.

Estos son criterios de aceptación del MVP completo, todavía pendiente. Las fases 1–6 tienen 256 tests offline y comprobaciones con Ollama real. Ya existe una propuesta pedagógica explícita; falta el flujo coordinado con el calendario y la edición/aprobación del profesor para aceptar el MVP completo.

## 12. Riesgos y respuesta

| Riesgo | Respuesta y límite |
|---|---|
| Alucinación con citas reales | Referencias ensambladas por código, afirmaciones ligadas a extractos y revisión humana; no garantía automática de verdad |
| Corpus insuficiente o sesgado | Abstención, lagunas visibles y control de selección por el profesor |
| Extracción defectuosa, tablas o partituras | Vista de extractos y bloqueo de documentos ilegibles; OCR opcional con revisión; reconocimiento multimodal pendiente |
| Agotar 16 GiB con 14B y contexto amplio | Inferencia secuencial, modelo menor evaluado y contexto acotado |
| Extensión joven o incompatibilidad ARM64 | Prueba temprana, versión fijada y alternativa documentada |
| Pérdida de procedencia al editar o reindexar | Versiones, snapshots de evidencia y aprobaciones ligadas a hashes |
| Confundir propuestas con clases impartidas | Estados distintos; progreso solo confirmado por el profesor |
| Inyección de instrucciones en documentos | Fuentes delimitadas como datos, sin herramientas ejecutables y validación posterior |
| Divergencias entre Zotero y catálogo | IDs externos, importación idempotente y correcciones locales separadas |
| Cambios de API y de modelos | Adaptadores pequeños, digests y tests de contrato |
| Datos borrados o copia incompleta | Backup consistente y restauración probada |

## 13. Desarrollo incremental después de aprobar

| Fase | Entrega verificable |
|---|---|
| 0, completada | Arquitectura aprobada |
| 1, completada | Git, Python 3.12 aislado, CLI, doctor, lockfile y 47 tests |
| 2, completada | Configuración YAML estricta, SQLite transaccional, calendario, programación y pruebas |
| 3, completada | Biblioteca, versiones, extracción, metadatos y autorización; migración SQLite 2 |
| 4, completada | sqlite-vec, embeddings Ollama configurables, búsqueda filtrada, 171 tests y prueba real con Qwen3-Embedding 0.6B |
| 5, completada | Adaptador Ollama compartido, ask documentado, presupuestos, citas verificadas, auditoría y pruebas reales |
| 6, completada | Rol pedagógico, contrato de actividades/citas/tiempos, historial y exportación Markdown |
| 7 | Flujo completo preparar clase, revisión y persistencia; aceptación del MVP |
| 8 | Registro de impartición, feedback por grupo/actividad y preparación semanal apoyada en memoria |
| 9 | Exportadores adicionales e integración Zotero; LilyPond y SuperCollider con validadores específicos |
| 10 | Interfaz gráfica sobre los mismos servicios, cuando el núcleo sea estable |

Las descargas de modelos, elección definitiva de embeddings y parámetros de rendimiento quedan pendientes de evaluación con ejemplos reales. No bloquean la arquitectura: son configuración y pruebas de aceptación, no acoplamientos al dominio.

**Prioridad actual:** fases aparcadas por petición del profesor. Carpeta de conocimiento e interfaz gráfica local para trabajar con la funcionalidad disponible.

### Concreción de fase 2

Las tablas docentes tienen IDs y relaciones mediante claves foráneas; los campos
restantes de cada registro se guardan como JSON validado. La migración inicial
está numerada mediante `PRAGMA user_version = 1` en `storage.py`. No se han creado
las tablas de documentos, generación o memoria de fases posteriores. La vinculación
con un documento fuente se añadirá al existir la biblioteca.

La importación completa es transaccional, idempotente y conserva instantáneas;
una sustitución diferente exige `--replace`. Las consultas leen una instantánea
coherente en una conexión de solo lectura. Calendario y programación no consultan
Ollama ni la red. Las sesiones se calculan a partir de reglas y excepciones, sin
persistir todavía impartición o progreso. Un grupo admite una programación activa.
La temporalización sugiere unidades por fecha, sin decidir automáticamente el
contenido siguiente. Hay 95 tests superados para las fases 1 y 2.


### Concreción de fase 3

Se han añadido documents, document_versions, document_segments, document_subjects
y library_events mediante migración transaccional 2. Las relaciones de asignatura
tienen claves foráneas; autores, etiquetas y colecciones son listas JSON validadas
y acotadas en los metadatos, sin tablas adicionales hasta que sus consultas lo
justifiquen. Los documentos son inicialmente no autorizados. Cada cambio de
versión extraída o metadatos requiere nueva autorización; una extracción fallida
no sustituye la versión válida anterior. La categoría documental/profesor es fija.

Los originales se guardan por hash junto a la base. Se conservan metadatos de
incorporación por versión y eventos de corrección. Las extracciones tienen
localizadores de página física o líneas, sin numeración impresa inventada.
La fragmentación RAG, embeddings y citas renderizadas quedan para fases siguientes.
La sustitución de configuración docente usa upsert y retirada de entidades al
final de la transacción para conservar las asociaciones bibliográficas existentes.


### Concreción de fase 4

El profesor eligió `qwen3-embedding:0.6b`, instalado y probado con textos sintéticos.
La aplicación lee esa selección desde YAML; no fija un modelo ni descarga uno
implícitamente. Se ha validado sqlite-vec 0.1.9 en el Python 3.12 ARM64 local.
La migración 3 añade perfiles y vectores float32 a tablas SQLite normales; filtros
relacionales se materializan antes de calcular distancias coseno.

Modelo/digest, dimensión, prefijos y versión de fragmentación identifican el
espacio vectorial. Los fragmentos conservan offsets y localizadores; solo se
activa cada índice cuando toda su versión está completa. Una búsqueda con
fuentes vigentes sin indexar falla explícitamente para evitar cobertura parcial
oculta. Las citas se construyen con metadatos locales, sin pedirlas a un LLM.

La limitación de contexto se maneja sin truncamiento: un error de tamaño pide
reducir el tamaño configurable y reindexar; no se ha implementado un tokenizador
ni subdivisión automática específica de cada modelo. Se devuelven candidatos
etiquetados, no respuestas: calibración del umbral y suficiencia factual siguen
pendientes del corpus docente real y de las fases generativas.

Validación: 171 tests offline, 8/8 consultas de prueba en español/gallego con
fuente esperada en primer lugar, y microbenchmark de 1 000/10 000 vectores. Las
mediciones y sus límites están en README.md; no equivalen a la aceptación del
MVP completo.


### Concreción de fase 5

En la implementación inicial de fase 5, `ask` recuperaba evidencias y realizaba una llamada de generación
local; no prepara clases todavía. `llm/local.py` comparte transporte y validación
de identidad con embeddings. El adaptador generativo usa `/api/chat` con JSON
estructurado, salida limitada, sin herramientas, sin streaming de texto no
validado. El contrato actual de reparación se describe al final de este documento. El modelo de prueba qwen3:14b se selecciona
en YAML y no está fijado en código. No se descargaron modelos nuevos en esta fase.

La salida distingue síntesis/inferencia de IA y evidencia documental/material del
profesor. Referencias se construyen por código; citas literales e IDs se validan.
La comprobación no equivale a validación factual: todo resultado es borrador y
requiere revisión humana. Modelo y sistema pueden abstenerse por insuficiencia.

La migración 4 añade registros generativos con snapshots de evidencia y parámetros.
Se conservan fallos, cancelaciones, omisiones por presupuesto y resultados; un
proceso interrumpido abruptamente puede quedar incompleto, nunca aprobado.
Se comprueban permisos e integridad antes de generar y al guardar el resultado.
Los registros históricos advierten cuando sus fuentes dejan de estar vigentes.

El presupuesto usa bytes UTF-8 como estimación conservadora, reserva salida/margen
y comprueba las métricas reportadas; no incorpora un tokenizador específico de
modelo. Las limitaciones de truncamiento y suficiencia semántica están documentadas
en README.md. Validación: 220 tests, prueba real de respuesta y abstención con
qwen3:14b y comprobación de exclusión sin cargar el generativo.


### Concreción de fase 6

El rol pedagógico es un prompt especializado con contrato JSON estricto y una
subclase pequeña del adaptador Ollama. Reutiliza la recuperación, comprobación de
fuentes y auditoría de fase 5. No añade dependencias, migraciones de SQLite ni un
framework de agentes. La ejecución continúa siendo secuencial, con un solo modelo
generativo, y queda identificada mediante `prompt_version=pedagogy:1`.

El profesor elige tema, grupo, duración, criterios y, opcionalmente, una unidad
perteneciente a la programación del grupo. El sistema conserva esa instantánea,
pero no deduce progreso impartido ni experiencias previas. La unidad constituye
contexto docente; no sustituye al corpus autorizado para sustentar conocimientos.

La propuesta separa las síntesis/inferencias con citas literales de las actividades
y decisiones pedagógicas de IA. Cada actividad referencia al menos un contenido y
el programa exige una suma exacta de minutos. Los recursos se describen como
materiales por preparar. Estas comprobaciones no validan la adecuación pedagógica
ni demuestran implicación semántica entre citas, afirmaciones y actividades.

Las ejecuciones quedan como `draft`, `abstained`, `failed` o `cancelled`, sin
aprobación automática. Historial y exportación usan los mismos comandos de fase 5.
Una repetición crea otro registro; la edición y revisión explícitas, la selección
de sesión desde el calendario y el comando `prepare class` pertenecen a fase 7.

El presupuesto pedagógico se configura por separado en YAML; el ejemplo usa 6144
de contexto y 1536 tokens de salida para el modelo local actual. Un límite excedido
rechaza la respuesta completa y conserva el error; los reintentos actuales quedan auditados según el contrato de reparación.

La prueba con contexto 8192 reveló falta de memoria Metal al encadenar consultas.
La configuración de ejemplo se redujo a 6144 y se añadió `num_batch` validado
(valor predeterminado 128, también configurable para `ask`). Las respuestas vacías
con `done: false` se rechazan con un diagnóstico diferente del límite de tokens;
no se inventa una abstención para ocultar un fallo del servidor.

Validación final: 256 tests offline, wheel instalado de forma aislada y prueba real
completa con la configuración ajustada: propuesta de 30 minutos (53.2 s),
abstención (13.1 s) y exclusión de fuente sin generación. La prueba usa un corpus
sintético; falta la evaluación pedagógica con los materiales reales del profesor.


## Interfaz local y carpeta de conocimiento (0.7.0)

Starlette y Uvicorn sirven una aplicación con HTML, CSS y JavaScript nativos,
sin compilador ni dependencias JavaScript. El diseño utiliza tipografías locales,
colores discretos y navegación Biblioteca / Asistente / Propuestas / Ajustes.
El servidor escucha únicamente en loopback. Valida Host y Origin y exige un token
por proceso para la API; una política CSP limita los recursos al propio servidor.

Un único trabajador serializa la importación, los embeddings y la generación para
contener el consumo de memoria. Las notificaciones de trabajos viven en memoria;
los documentos y los registros de generación permanecen en SQLite. No hay
reanudación automática de tareas tras cerrar el proceso. La exclusión de fuentes
es inmediata y una tarea de indexación pendiente no puede volver a autorizarlas.

Conocimiento separa entrada, referencias y material docente por asignatura. El
escaneo detecta cambios mediante hash; las copias originales y su trazabilidad se
conservan en la biblioteca existente. La importación no autoriza automáticamente.
Las subidas no sobrescriben archivos existentes y se limitan a PDF, DOCX, TXT y Markdown.

El lanzador macOS Enjambre.app usa el entorno Python del proyecto y abre la interfaz
en el navegador. Reconoce una instancia del mismo espacio de trabajo para evitar
servidores duplicados. Ajustes permite cerrar el servidor cuando no hay tareas.

El esquema activo es el 5, incluida la revisión de propuestas ya presente en el
proyecto. Los borradores de migración de memoria no activan una nueva fase.
La autorización de una fuente y la aprobación de una propuesta son decisiones
independientes. Las actividades generadas no se incorporan al corpus documental.

Verificación: 300 tests offline y prueba real de subida desde el navegador,
revisión, embeddings y consulta documentada con Ollama en un espacio sintético
separado. Una propuesta en gallego sobre una fuente española alteró la cita:
el validador la rechazó, sin publicar un borrador inválido. El prompt insiste en
conservar el idioma original de las citas; el modelo puede incumplirlo y el control
estricto se mantiene. Hace falta evaluar los materiales reales del profesor.

La prueba posterior en castellano produjo una propuesta válida de 30 minutos en
54,47 segundos mediante la API de la interfaz, con citas literales verificadas.
El wheel 0.7.0 se construyó e instaló sin red en un entorno independiente.

## Recuperación orientada a relevancia (en evaluación local)

La consulta documental con el generador Ollama utiliza ahora una reformulación
local al inglés (máximo dos variantes), conserva la pregunta original y combina
rangos vectoriales con BM25 mediante reciprocal rank fusion. Ambos canales se
calculan únicamente sobre versiones vigentes, autorizadas y del ámbito elegido.
La reformulación solo propone términos de búsqueda: nunca se incorpora como fuente.
No cambia el perfil de embeddings ni exige reindexar los libros existentes.

Se amplía la selección a 24 candidatos y se da prioridad a páginas distintas.
El mismo modelo local evalúa los pasajes completos en lotes que caben en contexto:
0 irrelevante/índice, 1 mención o ejemplo aislado, 2 contexto explicativo, 3 respuesta
directa. Solo los niveles 2–3 pasan a la comparación final, que ordena definición,
mecanismo y ejemplos cuando corresponde. Es una clasificación de un modelo, no
una garantía de relevancia; se conserva su auditoría en las métricas de ejecución.

El contrato grounded-answer:3 usa referencias compactas quote_XXX dentro de cada
fuente. El programa las resuelve a subcadenas exactas del original, conservando el
texto bruto del modelo y verificando después procedencia y vigencia. Se evita
duplicar todas las citas en el esquema y en el prompt. Los textos de las fuentes
no se corrigen ni se sustituyen por resúmenes. Con los parámetros locales actuales
la prueba del motete admite dos fragmentos completos, frente a uno anteriormente.

La interfaz muestra las etapas de búsqueda y el lote de revisión de relevancia.
El proceso es secuencial. El generador conserva el modelo entre lotes de relevancia
con keep_alive=5m y el último lote lo libera; el resto conserva keep_alive=0.
Contrato documentado en https://docs.ollama.com/api/chat. Si un lote falla, no se
presenta silenciosamente una respuesta sin revisión; el modelo retenido expira
como máximo tras ese plazo. Este flujo prioriza calidad y añade latencia local.
# Credenciales de proveedores

`docente_ai.secrets` resuelve credenciales desde el entorno y después desde el
Llavero de macOS mediante `security`, sin dependencias adicionales. Los ajustes
generativos no contienen `api_key`; el adaptador DeepSeek la resuelve al abrir
su cliente. La migración de YAML antiguos guarda primero la credencial y elimina
el campo mediante sustitución atómica. Ajustes solo recibe claves para escritura,
expone un booleano y permite borrar la entrada del Llavero. La instantánea de
generación en SQLite contiene únicamente ese booleano. Un filtro global protege
handlers existentes y futuros y enmascara también el texto de las excepciones.

## Contrato de reparación: grounded-answer:6 y pedagogy:6

Ambos flujos pasan por `service.ask` y `generation.repair.generate_validated`.
Hay una llamada inicial y hasta dos reintentos de contenido. La decisión usa
excepciones tipadas, nunca comparaciones de mensajes:

| Tipo | Acción |
|---|---|
| `json_format`, `contract`, `extra_fields`, `invalid_enum`, `quote_unresolved` | Añadir respuesta anterior como assistant e instrucción determinista como user; validar el nuevo JSON completo |
| `length` | Igual, pero exigir un máximo de cinco claims breves sin subir tokens; ajustar vínculos del plan a los claims nuevos |
| `network`, `authorization`, `source_changed`, cancelación | Detener el flujo; no reparar contenido |
| `context_budget`, identidad del modelo, otros fallos de proveedor | Detener; nunca recortar fuentes ni aceptar respuestas parciales |

Se conserva el corpus seleccionado y se comprueba su autorización, versión,
metadatos y original antes y después de cada generación y dentro de la transacción
final. Una respuesta inválida no se convierte en draft. Al agotar las reparaciones,
la ejecución queda failed; get_run sigue ocultando la respuesta cruda. La cancelación
conserva cancelled. Una abstención válida finaliza como abstained.

Cada intento añade a `metrics_json.attempts` su `error_type` (null si tiene éxito),
`tokens.input` y `tokens.output` (null si el proveedor no los proporciona), y los
campos retirados por saneado en `sanitized_fields`. El error final se guarda también
en `metrics_json.error_type`. El diálogo de reparación se audita en messages_json.
Se mantiene el presupuesto de contexto y salida: si el diálogo de reparación no
cabe en Ollama, se detiene con context_budget en lugar de perder evidencia.

DeepSeek recibe siempre la palabra literal JSON en system y el esquema compacto
de response_schema, incluidas las combinaciones de source_id y quote_XXX autorizadas.
La selección pedagógica incluye plan; los esquemas de reformulación y ranking
conservan sus propios contratos. Los reintentos mantienen esas restricciones aunque
el último mensaje sea una instrucción de reparación. La respuesta pasa por un
saneado que solo elimina claves desconocidas dentro de evidence y visualizations
(incluidos sus items). No altera el texto de claims ni las citas, no completa campos
obligatorios y no reconstruye esquemas. La validación posterior sigue siendo
obligatoria. Las citas solo permiten normalización de espacios; cambios de
puntuación, elipsis, traducciones y aproximaciones se rechazan.

El transporte DeepSeek admite un único reintento por petición ante HTTP 429,
5xx o timeout, con backoff fijo de 0.5 segundos. No repite 401/403, otros 4xx ni
errores de conexión distintos de timeout. Este mecanismo es independiente de la
reparación de contenido: como máximo seis peticiones para tres intentos, sin contar
las llamadas separadas de recuperación. `transport_retries` registra las repeticiones
HTTP realizadas por el cliente generativo.

`docente-ai runs stats --limit N` y el bloque de Ajustes consultan las últimas N
ejecuciones (1–10000, por defecto 100), con porcentajes sobre el total, tipos de
fallo y borradores reparados. Los registros históricos sin clasificación permanecen
en legacy_untyped. No se cambia el esquema SQLite ni se necesitan dependencias nuevas.

## Proveedores y contrato de privacidad remoto

`llm/presets.py` declara nombres, transporte, endpoint, residencia, nombre del
secreto y capacidades por modelo. Ollama utiliza su adaptador local;
DeepSeek, Mistral y custom utilizan `OpenAICompatibleGenerator`. `deepseek.py`
solo conserva aliases de importación para compatibilidad. El endpoint de Mistral
es regional europeo (`https://api.eu.mistral.ai/v1`), según su
[documentación regional](https://docs.mistral.ai/inference/regional-inference).
Custom exige HTTPS y declara residencia desconocida; los presets fijos no permiten
cambiar el endpoint y conservar su etiqueta de residencia. Las URLs no pueden
contener credenciales ni parámetros. No se heredan proxies ni se siguen redirecciones.

`GenerationSettings` guarda `base_url`, `data_residency`, `response_format` y
`remote_consent`, nunca la clave. La capacidad explícita determina si se envía
json_schema, json_object o ninguna de las dos. Sigue enviándose el contrato compacto
en system y siguen siendo obligatorias las validaciones de citas y fuentes.
Las credenciales se resuelven en secrets mediante entorno y Llavero por proveedor.

El consentimiento es un hash de la versión del contrato, preset, endpoint, modelo,
residencia y capacidad. Solo la acción explícita de la interfaz lo guarda; se exige
antes de encolar consultas, antes de recuperar/generar en service.ask y al abrir el
cliente remoto. Cambiar destino o configuración invalida la confirmación. Si los
ajustes de respuestas y propuestas difieren, la cabecera muestra ambos indicadores
y cada flujo confirma su propio destino. Las configuraciones antiguas sin consentimiento
no pueden enviar contenido remoto.

La pregunta, criterios explícitos del profesor y los fragmentos autorizados con
título, autores, año, categoría y referencias de cita salen del equipo. Reformulación
y ranking también usan el proveedor elegido. Para propuestas, `remote_context`
construye una lista permitida: group.level, group.language, duration_minutes,
teacher_criteria y unit.title/objectives/contents/competencies/criteria. No serializa
prior_experience, session, nombres o identificadores del grupo ni ningún campo de
session_records o session_feedback. La memoria local y las instantáneas auditables
pueden conservar el contexto completo, pero el contexto enviado al proveedor se
construye aparte. Las pruebas insertan registros y feedback ficticios y verifican
su ausencia en los mensajes remotos de los tres presets. En Ollama la memoria previa
permanece disponible. No se adjuntan originales; si el usuario copia datos privados
en la pregunta, criterios o fuentes, estos pasan a formar parte del contenido elegido.

La cabecera muestra siempre «Generación local» o «Fragmentos enviados a proveedor
(residencia)». El indicador declara la ruta de generación, no certifica políticas
contractuales de retención o subprocesamiento. Biblioteca, SQLite, diario e índice
siguen locales; bge-m3 es el modelo de embeddings de referencia, con otros modelos
locales configurables. No hay fallback automático entre proveedores.

## Estilos locales separados

`static/style.css` es un manifiesto de `@import` locales sin parámetros de versión.
`static/css/` separa variables (`tokens.css`), base, componentes, las cinco vistas,
material del alumnado, infografías, impresión y responsive. Diario y Ajustes usan
actualmente estilos compartidos; sus archivos solo documentan esa situación y no
añaden reglas. Se conservan todas las declaraciones originales, sin eliminar
supuestas reglas muertas. Las capturas de referencia verifican la cascada y la
impresión en escritorio y móvil. El servidor mantiene `Cache-Control: no-store`.
