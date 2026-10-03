# Distribución de Arkhé para macOS y Windows

**Fecha de investigación:** 3 de octubre de 2026. **Estado:** propuesta; no se ha implementado ningún cambio de empaquetado.

## Recomendación

Para la distribución estable recomiendo **Tauri 2 con el backend Python empaquetado mediante PyInstaller como sidecar**. Conserva el servidor y la interfaz actuales, proporciona una ventana propia y ofrece un mecanismo común de actualizaciones firmadas. No elimina Python: lo incluye dentro del programa. El profesorado no tendría que instalar Python, uv, Rust ni herramientas de desarrollo.

El primer paso debería ser una prueba técnica del backend congelado, en macOS y Windows, antes de desarrollar la envoltura Tauri. Ese trabajo es reutilizable. Si se necesita un piloto antes de completar las actualizaciones, **PyInstaller + pywebview** es la alternativa de menor cambio. Briefcase merece una prueba de compatibilidad, pero no lo elegiría inicialmente: facilita los instaladores, aunque no resuelve por sí mismo las actualizaciones en ejecución ni la integración de esta interfaz web.

La elección de Tauri responde al mantenimiento de una distribución profesional, no a una reducción garantizada del tamaño. Con Python incluido, sus cifras de aplicaciones mínimas no representan el tamaño de Arkhé. Tauri documenta tanto la inclusión de ejecutables externos como un actualizador con firmas obligatorias. [Sidecars de Tauri](https://v2.tauri.app/develop/sidecar/), [actualizador](https://v2.tauri.app/plugin/updater/), [tamaño de aplicaciones](https://v2.tauri.app/concept/size/).

## Situación comprobada en el repositorio

- El nombre actual del bundle es `Arkhe.app`, con marca visible **Arkhé**. `scripts/build_macos_app.py` genera un script zsh que encuentra el proyecto y ejecuta `.venv/bin/docente-ai`; no incluye un intérprete ni las dependencias.
- `web/launch.py` ya levanta Uvicorn, reconoce una instancia existente por su workspace y abre el navegador. El servidor es reutilizable en las tres opciones; el bundle actual solo sirve para macOS.
- El backend usa Python 3.12, Starlette/Uvicorn, httpx, PyYAML, pypdf, python-docx y la extensión nativa sqlite-vec. FTS5 y la carga de extensiones SQLite son comprobaciones obligatorias del binario distribuido.
- Los recursos HTML, CSS, módulos ES, Mermaid y SVG son locales. No hace falta incorporar npm ni un compilador de frontend. Tauri sí introduce una compilación Rust para la envoltura; podría invocarse mediante Cargo, conservando los módulos ES actuales. [Arquitectura de Tauri](https://v2.tauri.app/concept/architecture/).
- `Workspace(root)` sitúa `data/`, `config/` y `Conocimiento/` bajo la raíz elegida. Se puede mantener su organización interna, pero la raíz de usuario debe separarse de los recursos instalados.
- `secrets.py` conserva claves en el Llavero macOS, servicio `docente-ai`, o en variables de entorno. En Windows no existe todavía un almacén persistente accesible desde Ajustes. Algunas acciones para abrir carpetas usan exclusivamente `open` de macOS.
- OCR es opcional y depende de `ocrmypdf` externo. Ninguna opción de empaquetado hace desaparecer esta dependencia.

Esta investigación ha leído código y documentación; no ha inspeccionado bibliotecas, bases de datos ni configuraciones reales del usuario.

## Comparación de alternativas

Los tamaños siguientes son **estimaciones de planificación propias**, no mediciones de builds ni promesas de los fabricantes. Suponen un artefacto por arquitectura, Python y dependencias de producción, motor web del sistema y recursos actuales. Excluyen fuentes del usuario, modelos, Ollama, OCR, Playwright y herramientas de desarrollo. Habrá que medir descarga comprimida y espacio instalado por separado.

| Aspecto | A1. PyInstaller + pywebview | A2. Briefcase + ventana webview | B. Tauri + sidecar Python congelado |
| --- | --- | --- | --- |
| Instalador macOS, aproximado | 45–100 MB | 50–120 MB | 40–100 MB |
| Instalador Windows, aproximado | 40–100 MB | 45–120 MB | 40–100 MB |
| Programa instalado, aproximado | 100–220 MB | 110–260 MB | 90–220 MB |
| Motor web | WKWebView en macOS; WebView2 en Windows | El de la biblioteca GUI elegida; presupuestado pywebview nativo | WKWebView en macOS; WebView2 en Windows |
| Construcción | Python, hooks/spec de congelación, instalador adicional | Python embebido, plantillas y empaquetadores nativos | Build Python por destino, Rust, recursos del sidecar e instalador Tauri |
| Firma macOS | PyInstaller firma binarios; finalizar bundle, notarización y DMG | Integra firma y notarización al empaquetar | Integra firma/notarización; incluir todos los binarios Python y bibliotecas |
| Firma Windows | Authenticode para EXE/DLL propios y el instalador | Firma de ejecutables/instalador según configuración | Firma de sidecar y envoltura; firma del instalador |
| Actualizaciones automáticas | Integración adicional, por ejemplo Sparkle/WinSparkle | Integración adicional; `briefcase update` es una operación de desarrollo | Plugin updater con artefactos firmados y manifiesto remoto |
| Datos personales | Raíz de usuario común definida abajo | La misma raíz | La misma raíz, comunicada explícitamente al sidecar |
| Ollama | Detección y asistente propios | Detección y asistente propios | Detección y asistente propios; Tauri no suministra inferencia |
| Principal ventaja | Menor cambio sobre el código Python | Instaladores y estructura de aplicación gestionados | Ciclo de vida de escritorio y actualización multiplataforma |
| Principal coste | Integrar dos mecanismos nativos de actualización | Validar ruedas nativas, GUI e integración del servidor | Mantener Rust + Python y coordinar dos procesos |

**WebView2 se presupuesta aparte.** En Windows usar Evergreen compartido y detectar si existe. Tauri documenta un bootstrapper integrado de unos 1,8 MB que necesita Internet y un instalador offline de unos 127 MB adicionales; son cifras orientativas que pueden cambiar. El espacio del runtime instalado tampoco está incluido en la tabla. Para centros sin Internet ofrecer un instalador offline, evitando distribuir Chromium/Qt/CEF como sustituto por defecto. [Instaladores de Tauri](https://v2.tauri.app/distribute/windows-installer/), [distribución de WebView2 por Microsoft](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

### A1. PyInstaller y pywebview

Empaquetar inicialmente en modo **onedir**: intérprete, bibliotecas, extensión sqlite-vec y recursos de producción dentro del bundle/directorio instalado. Evitar que el usuario vea esa carpeta: se entrega un DMG o instalador Windows con acceso directo. El modo onefile extrae recursos temporales al arrancar; conviene reservarlo para una prueba comparativa, no asumir que será más rápido o más fácil de firmar. PyInstaller requiere generar el paquete en cada sistema operativo de destino. [Funcionamiento de PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html), [construcciones por plataforma](https://pyinstaller.org/en/stable/usage.html).

La ventana pywebview abriría el servidor loopback ya iniciado. Su integración debe respetar el hilo principal de la GUI y el cierre ordenado de Uvicorn; no basta con sustituir `webbrowser.open`. Usar exclusivamente los enlaces nativos necesarios: PyObjC/WebKit en macOS y pythonnet/WebView2 en Windows. Excluir dependencias GUI ajenas del entorno de build. La guía de pywebview recomienda py2app para macOS y PyInstaller para Windows/Linux: la combinación PyInstaller + WKWebView en macOS es, por tanto, una **hipótesis que debe superar el piloto**, no una compatibilidad ya comprobada aquí. [Instalación de pywebview](https://pywebview.flowrl.com/guide/installation.html), [congelación](https://pywebview.flowrl.com/guide/freezing.html).

Las actualizaciones no vienen resueltas por congelar el programa. Sparkle en macOS y WinSparkle en Windows son candidatos con firmas de actualizaciones, pero requieren integración, feeds y pruebas de reemplazo del programa. Para un piloto bastaría aviso de nueva versión y descarga del instalador firmado, identificado claramente como actualización manual. [Sparkle](https://sparkle-project.org/documentation/), [WinSparkle](https://winsparkle.org/guides/getting-started/).

### A2. Briefcase y ventana webview

Briefcase incluye Python y dependencias en una aplicación nativa. Produce DMG/PKG/ZIP en macOS y MSI/ZIP en Windows; la firma/notarización de macOS está integrada. No obliga a reescribir la lógica del backend. Habría que incorporar una GUI webview y validar su encaje con el runtime y las plantillas, sin confundir Briefcase con el motor de ventana. [Plataforma macOS](https://briefcase.beeware.org/en/stable/reference/platforms/macOS/), [plataforma Windows](https://briefcase.beeware.org/en/stable/reference/platforms/windows/).

Sus beneficios no dispensan de comprobar sqlite-vec, lxml de python-docx y soporte SQLite en cada Python embebido. No presupuestar recompilaciones improvisadas en el ordenador del profesor. Si se requieren ruedas propias, producirlas en CI. El instalador MSI también debe decidir instalación por usuario frente a instalación gestionada por el centro.

No considerar `briefcase update` como un actualizador instalado en el equipo del docente: actualiza el proyecto empaquetado durante el desarrollo. La distribución necesita un mecanismo adicional para consultar, verificar e instalar releases, igual que A1. [Comando update de Briefcase](https://briefcase.beeware.org/en/stable/reference/commands/update/). Es una opción razonable si se priorizan sus plantillas y herramientas nativas; aporta menos ventaja aquí que Tauri para la actualización multiplataforma.

### B. Tauri y sidecar Python

Tauri administra la ventana, instancia única, apertura de archivos y actualizaciones. El sidecar contiene Python y **todo** el backend; no depende de `.venv`. Congelarlo con PyInstaller permite conservar los contratos actuales. Tauri exige identificar el ejecutable externo por destino; distribuir también las DLL/dylib y recursos de un build onedir con sus rutas correctas. `externalBin` por sí solo no empaqueta mágicamente todas las dependencias de una carpeta. [Empaquetado de sidecars](https://v2.tauri.app/develop/sidecar/).

Propuesta de integración: iniciar el sidecar desde Rust, esperar un handshake por canal privado con el puerto y cargar en la ventana la página del servidor. Así se conservan origen único, rutas `/api`, CSP y SSE, con menos cambios que migrar las llamadas a IPC. Restringir navegación a ese origen y no conceder a páginas remotas permisos de shell, archivos o lanzamiento de procesos. Los enlaces externos se abren en el navegador del sistema tras validar su destino.

Preferir sidecar onedir para el piloto. Medir después si un ejecutable onefile compensa su extracción inicial y la complejidad de firma. El actualizador sustituye **envoltura y backend juntos**, con una versión de protocolo compatible. Necesita publicar artefactos, firmas y un manifiesto por plataforma/arquitectura; no es un servidor de actualizaciones ni un alojamiento gratuito. Su firma criptográfica es distinta de Developer ID y Authenticode. [Actualizador Tauri](https://v2.tauri.app/plugin/updater/).

## Firma, instalaciones y matriz de distribución

Para todas las opciones:

- **macOS:** Developer ID Application, firma desde los componentes interiores hasta el bundle final, hardened runtime y permisos mínimos justificados. Notarizar y adjuntar el ticket al artefacto de distribución cuando corresponda. Un PKG requiere identidad Developer ID Installer adicional. Incluir Python, sqlite-vec y cualquier biblioteca nativa en la comprobación; una firma ad hoc no sustituye este proceso. Probar una descarga real en un Mac limpio. [Notarización de Apple](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution), [firma/notarización Tauri](https://v2.tauri.app/distribute/sign/macos/), [notas macOS de PyInstaller](https://pyinstaller.org/en/stable/feature-notes.html).
- **Windows:** firmar con Authenticode y sellado de tiempo, mediante certificado o servicio de firma disponible para el editor. Comprobar editor visible, antivirus y SmartScreen: la firma no garantiza ausencia inmediata de avisos de reputación. No existe un trámite de notarización equivalente al de Apple. Instalación por usuario como opción inicial; MSI gestionado por TI si el centro lo requiere. [Firma Windows de Tauri](https://v2.tauri.app/distribute/sign/windows/).
- **CI:** builds nativos independientes para macOS arm64, macOS x86_64 y Windows x86_64. Windows arm64 queda para una segunda fase tras comprobar ruedas y Ollama. No prometer un macOS universal hasta verificar todas las bibliotecas de ambas arquitecturas.
- **Sistemas objetivo propuestos:** macOS 14+ y Windows 11 x64 para el primer piloto. La documentación de Ollama admite actualmente macOS 14+ y Windows 10 22H2+, pero eso no constituye certificación de Arkhé en todos ellos. Windows 10 necesitaría una decisión de soporte aparte. [Ollama macOS](https://docs.ollama.com/macos), [Ollama Windows](https://docs.ollama.com/windows).

Certificados, servicio de firma, alojamiento y sus costes se cotizarán al implementar; no se incluyen en las estimaciones de esfuerzo. Las claves de firma se conservan fuera del repositorio y separadas de las claves de los proveedores IA.

## Datos de usuario fuera del programa

Las tres opciones deben usar el mismo contrato, independiente del empaquetador:

| Contenido | macOS propuesto | Windows propuesto |
| --- | --- | --- |
| Raíz del espacio, biblioteca, SQLite y configuración | `~/Library/Application Support/Arkhe/` | `%LOCALAPPDATA%\Arkhe\` |
| Cachés regenerables | `~/Library/Caches/Arkhe/` | `%LOCALAPPDATA%\Arkhe\Cache\` |
| Logs con rotación y enmascarado | `~/Library/Logs/Arkhe/` | `%LOCALAPPDATA%\Arkhe\Logs\` |
| Material exportado para compartir | Carpeta elegida mediante diálogo Guardar | Carpeta elegida mediante diálogo Guardar |
| Credenciales | Llavero, servicio existente `docente-ai` | Credential Manager, espacio de nombres `docente-ai` |

Dentro de la raíz conservar `data/docente.sqlite3`, `config/` y `Conocimiento/`: reduce el alcance del cambio. Son rutas propuestas para instalaciones nuevas, **no una migración realizada ni autorizada por este documento**. Resolver los directorios mediante APIs del sistema, sin fijar usuarios ni depender del directorio de trabajo. No usar AppData Roaming/OneDrive/iCloud como ubicación automática de SQLite.

La carpeta del programa solo contiene ejecutables y recursos inmutables. En macOS será normalmente `/Applications/Arkhe.app`; en Windows, una carpeta de programas por usuario o gestionada por el centro. Actualizar/desinstalar el programa conserva la biblioteca y el diario; eliminar datos requiere una acción separada y explícita.

La incorporación del espacio existente necesita un asistente de importación con copia de seguridad y verificación: parar escrituras, copiar documentos y configuración sin claves, usar backup consistente de SQLite, revisar rutas absolutas `source_path` y conservar las rutas relativas de originales. No hacer un reemplazo indiscriminado de cadenas ni alterar citas/hashes. Mantener el espacio anterior hasta confirmar la copia. [Backup consistente de SQLite](https://sqlite.org/backup.html).

En Windows implementar lectura/escritura/borrado de credenciales con las APIs Credential Manager, por ejemplo mediante ctypes o una biblioteca justificada, respetando la resolución por entorno. El campo sigue siendo solo de escritura; ninguna clave pasa a YAML, SQLite, frontend o logs. Comprobar el acceso al Llavero después de cambios de identidad de firma en macOS. [API CredWriteW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew).

## Ollama y primera ejecución sin terminal

**Distinción decisiva:** hoy un proveedor remoto sustituye la generación, pero los embeddings siguen en Ollama local. Seleccionar Mistral o DeepSeek **no permite preparar ni consultar toda la biblioteca sin Ollama**. El empaquetador no modifica esta arquitectura.

Proponer tres recorridos claramente diferenciados:

1. **Local:** detectar Ollama por HTTP loopback, comprobar versión, modelos/digests y capacidades; guiar su instalación oficial si falta. Descargar embeddings y modelo generativo solo tras una elección explícita, mostrando volumen y progreso. Recomendar el modelo generativo después de probar RAM, CPU/GPU y latencia en el equipo; no imponer un modelo grande como requisito universal.
2. **Generación remota + embeddings locales, recomendado para equipos modestos:** instalar/detectar Ollama y únicamente `bge-m3`; introducir la clave en Ajustes y obtener el consentimiento remoto actual. Reduce recursos de generación, pero requiere Internet y gasto en la API. Las fuentes completas y el diario no se envían; se mantienen las restricciones actuales de prompts y validación.
3. **Sin Ollama:** alternativa futura separada. Para mantener embeddings locales, habría que integrar un runtime embebido de embeddings compatible y distribuir pesos: dependencia nueva, pruebas de calidad, rendimiento y perfiles/digests; si cambia el modelo o representación, reindexación explícita. Otra posibilidad es embeddings remotos, que amplía lo enviado durante la indexación y exige revisar privacidad, consentimiento y costes. No incluirla en el primer empaquetado ni presentarla como un simple interruptor de proveedor.

El instalador de Arkhé no incluiría inicialmente Ollama ni modelos. Abriría el instalador oficial mediante un botón y ofrecería «Comprobar de nuevo»; un centro podría preinstalarlos. No sobrescribir el Ollama de otra aplicación ni detener su proceso al cerrar Arkhé. No depender del PATH de una terminal para detectar un servicio operativo.

El modelo `bge-m3` publicado por Ollama ocupa aproximadamente **1,2 GB**, aparte del programa y del runtime. En Windows la documentación pide al menos **4 GB para los binarios de Ollama**, antes de modelos. Estos volúmenes dominan el espacio total y deben figurar en el asistente. Para uso offline se necesita preparar todo previamente; un bootstrapper online no basta. [Modelo bge-m3](https://ollama.com/library/bge-m3), [espacio y requisitos Windows](https://docs.ollama.com/windows).

OCR seguirá opcional en el piloto. DOCX y PDF con texto deben funcionar al instalar Arkhé. Para escaneados, explicar la ausencia de OCR sin pedir comandos; evaluar posteriormente un paquete administrado de OCRmyPDF/Tesseract y sus dependencias/licencias. No sumar ese volumen ocultamente a los tamaños anteriores.

## Arranque, actualizaciones y aceptación

Antes de distribuir, en cualquier alternativa:

- Arrancar únicamente en `127.0.0.1`, con puerto disponible elegido y comunicado a la ventana; adaptar la validación de origen/Host al puerto real. Mantener el token de sesión en cabeceras, SSE autenticado y CSP, sin abrir CORS global ni publicar el servicio en la red del centro.
- Instancia única por usuario/espacio; doble clic enfoca la ventana existente. El proceso GUI supervisa el backend y presenta un diagnóstico legible si falla. Al salir, cancela consultas y cierra solo el proceso que posee, sin matar servidores ajenos.
- Mantener el proceso de backend sin privilegios de administrador. Sustituir las acciones macOS de apertura de carpetas por apertura nativa en cada sistema. Resolver Guardar, impresión/PDF, portapapeles, descargas y ventanas emergentes: WKWebView/WebView2 no son idénticos a Chromium.
- Incluir sqlite-vec y verificar FTS5/carga de extensiones en el **programa congelado**. No aceptar solo que la suite pase bajo uv. [Carga de sqlite-vec en Python](https://alexgarcia.xyz/sqlite-vec/python.html).
- Descargar actualizaciones firmadas en segundo plano con información de versión, e instalarlas al cerrar o por elección del docente, nunca durante una clase activa. Actualizar programa y sidecar como unidad; mantener el espacio de usuario y hacer backup antes de migraciones.
- Si falla la instalación, conservar el programa anterior. Si ya migró SQLite, no prometer downgrade automático: recuperar un backup compatible o detenerse con diagnóstico. Ofrecer canal estable y piloto, con manifiestos por arquitectura y sin enviar biblioteca ni diario al servicio de actualizaciones.

Criterios de salida: arrancar sin Python/uv/proyecto en equipos limpios; abrir, importar DOCX/PDF, preparar fuentes, consultar con SSE, cancelar y verificar citas; imprimir y compartir material; trabajar sin Internet cuando todo es local y está instalado; superar actualización desde la versión anterior, doble arranque, puerto ocupado, rutas con tildes/espacios, falta de permisos, proveedor caído y reinstalación conservando datos. Las pruebas automatizadas siguen con red simulada; las pruebas de instaladores y notarización son una campaña separada en equipos/VM de distribución.

## Pasos y esfuerzo estimado

Estimaciones propias en **días de trabajo de una persona familiarizada con el proyecto**. Incluyen implementación y pruebas funcionales, no tiempos de espera de certificados, revisiones institucionales ni disponibilidad de equipos. No constituyen un calendario acordado.

| Paso | Entrega comprobable | Días |
| --- | --- | ---: |
| 1. Validar el backend congelado | Builds mínimos macOS arm64/x86_64 y Windows x64; Python 3.12, SQLite/FTS5/sqlite-vec, DOCX y assets; medir tamaño/arranque | 3–5 |
| 2. Separar recursos y espacio personal | Resolución de rutas, logs, copias e importación reversible; tests sintéticos | 3–5 |
| 3. Completar portabilidad Windows | Credential Manager, apertura/guardado de archivos y errores legibles | 2–4 |
| 4. Envoltura Tauri | Ventana, readiness, origen único, instancia única, supervisión/cierre, impresión y descargas | 4–7 |
| 5. Asistente de primera ejecución | Detección e instalación guiada de Ollama, modelos, proveedor, consentimiento y diagnóstico | 3–5 |
| 6. Pipeline de distribución | Instaladores, firmas, notarización, artefactos por destino y revisión de licencias | 3–5 |
| 7. Actualizador | Alojamiento/manifiestos, firmas independientes, cierre seguro, backups y fallos de instalación | 2–4 |
| 8. Campaña con profesorado | Máquinas limpias y redes de centro; arreglar impresión, permisos y rendimiento; guía de una página | 4–6 |
| **Total Tauri estable** | **Distribución con actualizaciones comprobadas** | **24–41** |

Alternativas orientativas: **PyInstaller + pywebview, piloto con actualizaciones manuales: 14–23 días**; añadir actualización automática y endurecimiento de distribución: **6–12 días más**. **Briefcase + webview: 17–28 días** para el piloto y **6–12 más** para actualizaciones y endurecimiento. No son tres proyectos acumulables: comparten buena parte de los pasos, pero requieren integraciones distintas. Un problema con ruedas nativas o entitlements puede ampliar los rangos.

Decisión tras el paso 1: continuar con Tauri si los tres binarios funcionan y existe capacidad para mantener Rust; elegir A1 para un piloto urgente si pywebview supera la prueba macOS. Antes de publicar hay que disponer de certificados y elegir el alojamiento, acordar soporte a equipos Intel y definir el recorrido de Ollama que se entregará. Este documento no instala herramientas, no mueve datos y no cambia el programa que está en uso.
