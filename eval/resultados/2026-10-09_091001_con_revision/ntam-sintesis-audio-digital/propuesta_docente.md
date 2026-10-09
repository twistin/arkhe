# Propuesta pedagógica

Registro: run-2646af2d5c09403aa14b9c6708c894ce

Tema elegido: NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son
Grupo: Grupo A · Nivel: 3º GP
Duración solicitada: 60 minutos

Criterios del profesor: Sesion practica y teorica sobre la naturaleza de la señal acustica y su conversion analogico-dixital (ADC). Explicar claramente la frecuencia de muestreo (sample rate: 44.1 kHz, 48 kHz, 96 kHz) y el teorema de Nyquist-Shannon con el fenomeno de aliasing / repliegue espectral y filtros antialiasing. Explicar la resolucion en bits (bit depth: 16 bit, 24 bit) y su relacion con el rango dinamico (relacion señal-ruido: 6 dB por bit) y el error de cuantizacion / dither. Introducir los osciladores basicos en sintesis sustractiva: senoidal, cuadrada, triangular y diente de sierra con sus armonicos. Actividad práctica con estacion DAW / sintetizador software en el aula: configurar sesion, escuchar el efecto de reducir la resolucion (bitcrusher) y diseñar un sonido elemental con un filtro paso-bajo.

Unidad elegida: Escucha y contexto histórico

---

# PARTE 1 · GUÍA DOCENTE (Para el Profesor)

**Borrador generado por IA, pendiente de revisión del profesor.**

Las referencias y citas textuales se han comprobado; eso no garantiza que cada afirmación sea correcta o esté suficientemente sustentada.

## Cobertura de requisitos del profesor

| ID | Requisito / Petición | Tipo | Estado | Contenidos (claims) | Observaciones |
| --- | --- | --- | --- | --- | --- |
| **R1** | Explicar la naturaleza de la señal acústica y su conversión analógico-digital (ADC). | contenido | Cubierto | #1 | A fonte S1 describe a conversión ADC como muestreo e cuantización, e as NTAM como dixitalización e procesamento de audio. |
| **R2** | Explicar la frecuencia de muestreo (44.1 kHz, 48 kHz, 96 kHz) y el teorema de Nyquist-Shannon, incluyendo aliasing/repliegue espectral y filtros antialiasing. | contenido | Cubierto | #2, #5 | S1 explica o teorema de Nyquist-Shannon, aliasing, filtros antialiasing e os estándares 44.1 kHz e 48 kHz. O valor de 96 kHz non aparece nas fontes, indícase na inferencia. |
| **R3** | Explicar la resolución en bits (16 bit, 24 bit), su relación con el rango dinámico (6 dB por bit), el error de cuantización y el dither. | contenido | Cubierto | #3, #5 | S1 menciona bit depth (16, 24 bit), a regra de 6 dB por bit, o erro de cuantización e o dither. Os valores exactos de rango dinámico para 16 e 24 bit son inferidos. |
| **R4** | Introducir los osciladores básicos en síntesis sustractiva: senoidal, cuadrada, triangular y diente de sierra, con sus armónicos. | contenido | Cubierto | #4 | S1 describe os osciladores senoidal, cuadrada, triangular e dente de sierra co seu contido harmónico. |
| **R5** | Realizar una actividad práctica con estación DAW/sintetizador software: configurar sesión, escuchar el efecto de reducir la resolución (bitcrusher) y diseñar un sonido elemental con un filtro paso-bajo. | actividad | Parcial | #1, #2, #3, #4 | As fontes proporcionan a base teórica para a actividade práctica (configuración de sesión, bitcrusher, filtro paso-baixo), pero non describen a actividade en si. O plan de actividades cobre este requisito de forma práctica. |

## 1. Planificación didáctica y objetivos

### Objetivos de aprendizaje

- Comprender a natureza da señal acústica e as etapas da conversión analóxico-dixital (ADC).
- Aplicar o teorema de Nyquist-Shannon para determinar a frecuencia de muestreo axeitada e evitar o aliasing.
- Relacionar a profundidade de bits co rango dinámico e o erro de cuantización, e empregar o dither.
- Identificar os osciladores básicos da síntese sustractiva e o seu contido harmónico.
- Configurar unha sesión DAW e deseñar un son elemental con filtro paso-baixo e bitcrusher.

**Dificultad propuesta:** Nivel intermedio. Requírese comprensión de conceptos básicos de acústica e manexo inicial de DAW. A parte teórica (teorema de Nyquist, cuantización) pode presentar dificultade para quen non teña base matemática, polo que se apoia con exemplos auditivos e visuais.

**Evaluación de la sesión:** Avaliación continua mediante observación directa durante as actividades, revisión dos entregables (capturas, táboas, ficheiro de audio) e participación na posta en común. Rúbrica: comprensión conceptual (40%), aplicación práctica (40%), comunicación e reflexión (20%).

### Secuencia didáctica y actividades

**0–15 min · Configuración da sesión DAW e exploración de frecuencias de muestreo [Individual]**

**Pautas docentes:** Guiar a configuración inicial do DAW: selección de dispositivo de audio, frecuencia de muestreo (44.1 kHz, 48 kHz, 96 kHz) e profundidade de bits (16, 24). Explicar como cambiar estes parámetros e que implicacións teñen. Supervisar que todos os equipos estean operativos.

**Consigna del alumno:** Abre o teu DAW, crea unha sesión nova e configura a frecuencia de muestreo a 44.1 kHz e a profundidade a 16 bit. Despois cambia a 48 kHz/24 bit e a 96 kHz/24 bit. Anota as diferenzas que observes na interface e no rendemento.

**Entregable:** Captura de pantalla ou documento coas tres configuracións e unha breve nota das diferenzas observadas.

**Solución / Criterios de corrección:** As configuracións deben reflectir os valores indicados. As diferenzas poden incluír maior uso de CPU e maior tamaño de ficheiro a 96 kHz/24 bit, e limitacións do hardware. O obxectivo é familiarizarse cos parámetros.

Base documental: contenidos 1, 2, 3.

**15–35 min · Audición do aliasing e efecto do bitcrusher [Individual]**

**Pautas docentes:** Preparar un oscilador ou xerador de ton senoidal no DAW. Explicar o aliasing subindo a frecuencia por riba da metade da frecuencia de muestreo. Introducir un bitcrusher e reducir a profundidade de bits para escoitar o ruído de cuantización. Relacionar co dither.

**Consigna del alumno:** Xera un ton senoidal a 1 kHz. Sube a frecuencia gradualmente ata superar a metade da frecuencia de muestreo (22.05 kHz a 44.1 kHz) e escoita o aliasing. Despois insire un bitcrusher e reduce a resolución de 16 a 8, 4 e 2 bit, escoitando o aumento do ruído. Anota as túas impresións.

**Entregable:** Táboa coas frecuencias probadas, a aparición do aliasing e a descrición do son con cada redución de bits.

**Solución / Criterios de corrección:** O aliasing aparece cando a frecuencia supera a metade da frecuencia de muestreo (frecuencia de Nyquist). Co bitcrusher, a redución de bits aumenta o ruído de cuantización e a distorsión. A 2 bit o son é moi distorsionado. O dither suaviza a distorsión a baixos niveis.

Base documental: contenidos 2, 3.

**35–55 min · Deseño dun son elemental con osciladores e filtro paso-baixo [Individual]**

**Pautas docentes:** Demostrar o uso dun sintetizador software: selección de osciladores (senoidal, cuadrada, triangular, dente de sierra), visualización do espectro e aplicación dun filtro paso-baixo con resonancia. Explicar como o filtro moldea o contido harmónico.

**Consigna del alumno:** No teu sintetizador software, selecciona un oscilador de dente de sierra. Observa o seu espectro harmónico. Aplica un filtro paso-baixo e varía a frecuencia de corte e a resonancia. Repite con onda cuadrada, triangular e senoidal. Crea un son curto e gárdao.

**Entregable:** Ficheiro de audio cun son deseñado e unha captura do espectro antes e despois do filtro.

**Solución / Criterios de corrección:** A onda dente de sierra mostra todos os armónicos; a cuadrada e triangular só impares; a senoidal só o fundamental. O filtro paso-baixo atenúa os armónicos por riba da frecuencia de corte, escurecendo o timbre. A resonancia acentúa a frecuencia de corte.

Base documental: contenidos 4.

**55–60 min · Posta en común e reflexión sobre a calidade dixital [Colectivo]**

**Pautas docentes:** Moderar unha discusión sobre as diferenzas escoitadas entre frecuencias de muestreo e profundidades de bits. Relacionar co uso profesional (CD, vídeo, alta resolución) e coa percepción auditiva. Aclarar dúbidas sobre Nyquist, aliasing e dither.

**Consigna del alumno:** Comparte co grupo as túas observacións sobre o aliasing e o bitcrusher. Explica que configuración usarías para unha gravación musical e por que. Escoita as propostas dos demais e debate.

**Entregable:** Participación na discusión e unha conclusión escrita breve sobre a configuración axeitada para distintos usos.

**Solución / Criterios de corrección:** Para música, 44.1 kHz/16 bit é suficiente para CD; 48 kHz/24 bit para vídeo e estudo; 96 kHz/24 bit para alta resolución. O aliasing evítase cumprindo Nyquist. O dither úsase ao reducir bits. Non hai unha única resposta correcta, senón xustificación técnica.

Base documental: contenidos 1, 2, 3, 4.

### Recursos y partituras por preparar

- Ordenador con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Xerador de ton senoidal e plugin bitcrusher.
- Analizador de espectro.
- Fonte S1: documento sobre NTAM, ADC, Nyquist-Shannon, bit depth e osciladores.
- Guión de prácticas con pasos e táboas de rexistro.

**Observaciones didácticas:** As fontes non detallan o valor de 96 kHz nin os valores exactos de rango dinámico para 16 e 24 bit; estes infírense a partir da regra de 6 dB por bit. A actividade práctica non está descrita nas fontes, polo que se deseña a partir dos contidos teóricos. A unidade didáctica proporcionada ('Escucha y contexto histórico') non se corresponde cos contidos técnicos solicitados; os obxectivos e contidos da unidade non se empregan para esta sesión.

## 2. Fundamentación teórica y contenidos

**Contenido 1 — Síntesis respaldada por bibliografía:**

A señal acústica é unha onda de presión continua no tempo. Para procesala dixitalmente hai que realizar unha conversión analóxico-dixital (ADC), que consta de dúas etapas: o muestreo (discretización temporal) e a cuantización (discretización en amplitude). Este proceso é a base das NTAM (Novas Tecnoloxías Aplicadas á Música), que abarcan a dixitalización e o procesamento de audio.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «Las Nuevas Tecnologías Aplicadas a la Música (NTAM) abarcan la digitalización y el procesamiento de audio.»
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La conversión analógico-digital (ADC) consta de muestreo y cuantización.»

**Contenido 2 — Síntesis respaldada por bibliografía:**

A frecuencia de muestreo (sample rate) determina o límite de frecuencias reproducibles segundo o teorema de Nyquist-Shannon: a frecuencia de muestreo debe ser polo menos o dobre da frecuencia máxima da señal para evitar o aliasing ou repliegue espectral. Este fenómeno combátese con filtros pasabajos antialiasing. Os estándares comúns son 44.1 kHz (calidade CD) e 48 kHz (vídeo/estudo).

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La frecuencia de muestreo (sample rate) determina el límite de frecuencias reproducibles según el teorema de muestreo de Nyquist-Shannon: la frecuencia de muestreo debe ser al menos el doble de la frecuencia máxima de la señal para evitar el fenómeno de aliasing o repliegue espectral, combatido con filtros pasabajos antialiasing.»
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «Los estándares comunes son 44.1 kHz (calidad CD) y 48 kHz (vídeo/estudio).»

**Contenido 3 — Síntesis respaldada por bibliografía:**

A resolución ou profundidade de bits (bit depth: 16 bit, 24 bit) determina o rango dinámico cuantizado, aproximadamente 6 dB por bit. Isto significa que cada bit engadido aumenta o rango dinámico en 6 dB. A cuantización introduce un erro (ruído de cuantización) que se pode enmascarar co dither, que reduce a distorsión armónica de baixo nivel.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La resolución o profundidad de bits (bit depth: 16 bit, 24 bit) determina el rango dinámico cuantizado (aproximadamente 6 dB por bit), introduciendo el dither para enmascarar la distorsión armónica de bajo nivel.»

**Contenido 4 — Síntesis respaldada por bibliografía:**

Na síntese sustractiva pártense de osciladores ricos en armónicos: a onda senoidal é unha onda pura sen armónicos; a onda cuadrada ou pulso ten só armónicos impares; a onda triangular tamén ten armónicos impares pero con caída rápida; e a onda dente de sierra contén todos os armónicos enteiros. Estes osciladores moldeanse posteriormente mediante filtros resonantes e envolventes ADSR.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «En la síntesis sustractiva se parte de osciladores ricos en armónicos: onda senoidal (onda pura sin armónicos), onda cuadrada o pulso (armónicos impares), onda triangular (armónicos impares con caída rápida) y onda diente de sierra (todos los armónicos enteros), moldeadas posteriormente mediante filtros resonantes y envolventes ADSR.»

**Contenido 5 — Inferencia de IA:**

Aínda que as fontes non detallan os valores de 96 kHz nin a relación exacta entre bit depth e rango dinámico en dB para 16 e 24 bit, pódese inferir que 96 kHz é un estándar de alta resolución que permite maior ancho de banda (ata 48 kHz) e que 16 bit ofrece ~96 dB e 24 bit ~144 dB de rango dinámico, aplicando a regra de 6 dB por bit. Esta inferencia é coherente coa información proporcionada sobre 44.1 kHz, 48 kHz e a regra dos 6 dB por bit.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «Los estándares comunes son 44.1 kHz (calidad CD) y 48 kHz (vídeo/estudio).»
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La resolución o profundidad de bits (bit depth: 16 bit, 24 bit) determina el rango dinámico cuantizado (aproximadamente 6 dB por bit), introduciendo el dither para enmascarar la distorsión armónica de bajo nivel.»

## Esquema documentado

### Cadea de conversión analóxico-dixital (ADC)

**Señal analóxica** (Onda de presión continua no tempo.) → **Muestreo** (Discretización temporal a intervalos regulares (frecuencia de muestreo).) → **Cuantización** (Asignación de valores de amplitude discretos (bit depth).) → **Codificación dixital** (Secuencia de números binarios que representa a onda.)

Etapas da conversión analóxico-dixital segundo as fontes: primeiro o muestreo, despois a cuantización.

## Esquema documentado

### Osciladores básicos e contido harmónico

| Elemento | Relación o función |
| --- | --- |
| Senoidal | Onda pura sen armónicos. |
| Cuadrada / pulso | Armónicos impares. |
| Triangular | Armónicos impares con caída rápida. |
| Dente de sierra | Todos os armónicos enteiros. |

Contido harmónico dos osciladores básicos empregados na síntese sustractiva.


<details>
<summary><strong>🔍 Revisión automática (evaluación según rúbrica)</strong></summary>

> ℹ️ **Nota de verificación:** Esta revisión es un análisis preliminar automático basado en la rúbrica pedagógica de Arkhé. **No sustituye a la revisión ni al criterio del profesor.**

| Criterio evaluado | Puntuación (0–3) | Valoración |
| --- |:---:| --- |
| C1: Cobertura de lo solicitado | **3** | Excelente / Sobresaliente |
| C2: Rigor factual frente a fuentes | **2** | Bueno / Competente |
| C3: Separación guía docente / alumnado | **3** | Excelente / Sobresaliente |
| C4: Tareas prácticas activas del alumnado | **3** | Excelente / Sobresaliente |
| C5: Adecuación al nivel educativo | **2** | Bueno / Competente |
| C6: Temporización y coherencia horaria | **2** | Bueno / Competente |

**Dictamen del revisor:** La propuesta cubre todos los requisitos del profesor con actividades prácticas bien estructuradas y separación clara de roles. Sin embargo, presenta algunas debilidades en rigor factual (inferencias no respaldadas sobre 96 kHz y valores de rango dinámico), en la demostración del aliasing (poco realista) y en la temporización de algunas actividades. La adecuación al nivel es aceptable pero mejorable con adaptaciones explícitas.

**Incidencias y propuestas de mejora detectadas:**

- **`claims\[4\].text`:** La inferencia sobre 96 kHz y los valores de rango dinámico (96 dB para 16 bit, 144 dB para 24 bit) no está respaldada por los pasajes de evidencia. Aunque se marca como inferencia, se presenta como un dato cuantitativo que puede inducir a error si no se contextualiza adecuadamente (p. ej., el rango dinámico teórico no equivale al práctico). *(Propuesta: Reformular la inferencia para indicar que se trata de una extrapolación de la regla de 6 dB por bit y que los valores son teóricos; o eliminar los valores numéricos concretos y ceñirse a la regla general.)*
- **`plan.activities\[1\].student\_task`:** La tarea de subir la frecuencia de un tono senoidal hasta superar la frecuencia de Nyquist para escuchar aliasing es problemática: un oscilador digital que genera una senoidal a frecuencia superior a la de Nyquist normalmente no produce aliasing audible si el propio oscilador aplica limitación de banda; además, a 22 kHz la mayoría de sistemas de reproducción y oídos no perciben el tono. El aliasing se demuestra mejor con señales que ya contienen componentes de alta frecuencia o mediante un generador que no esté limitado en banda. *(Propuesta: Sustituir la demostración por una señal compleja (p. ej., ruido o una onda diente de sierra) muestreada a baja frecuencia, o utilizar una herramienta que permita reducir la frecuencia de muestreo manteniendo la señal de entrada, para que el aliasing sea audible y medible.)*
- **`plan.activities\[1\].solution`:** Se afirma que 'a 2 bit o son é moi distorsionado' y que 'o dither suaviza a distorsión a baixos niveis', pero no se ha realizado ninguna tarea con dither en la actividad. La mención al dither queda descontextualizada y no se evalúa su efecto. *(Propuesta: Incluir una tarea específica con dither (activar/desactivar dither al reducir bits) o eliminar la referencia al dither en la solución de esta actividad.)*
- **`plan.activities\[2\].student\_task`:** La tarea de 'observa o seu espectro harmónico' con un analizador de espectro puede ser difícil de interpretar para estudiantes de 3º de Grao Profesional sin una guía previa sobre qué mirar. Además, no se especifica si el analizador es una herramienta del DAW o un plugin externo, lo que puede generar confusión. *(Propuesta: Proporcionar una guía visual o una plantilla para identificar armónicos (p. ej., marcar las frecuencias esperadas) y asegurar que el analizador esté disponible y sea explicado antes de la tarea.)*
- **`plan.activities\[3\].student\_task`:** La actividad de 'posta en común' tiene una tarea de reflexión escrita de 5 minutos, pero el tiempo asignado es muy ajustado para una discusión colectiva y una conclusión escrita. Además, el entregable es una conclusión breve que puede no reflejar adecuadamente la discusión. *(Propuesta: Ampliar el tiempo a 10 minutos o reducir el alcance de la discusión; o asignar la conclusión escrita como tarea para casa.)*
- **`plan.difficulty`:** Se indica que la parte teórica puede presentar dificultad para quien no tenga base matemática, pero no se especifican adaptaciones concretas para el nivel 3º de Grao Profesional, donde la formación matemática puede ser heterogénea. El nivel 'intermedio' puede ser ambiguo. *(Propuesta: Concretar el nivel esperado (p. ej., 'usuario inicial de DAW con conocimientos básicos de acústica') y añadir estrategias de apoyo (ejemplos numéricos sencillos, analogías visuales) para los conceptos matemáticos.)*
- **`plan.activities\[0\].minutes`:** La actividad de configuración de sesión DAW se asigna a 15 minutos, pero incluye tres configuraciones diferentes y la toma de notas. En un contexto de aula con posibles incidencias técnicas, puede ser insuficiente. *(Propuesta: Ampliar a 20 minutos o simplificar la tarea a dos configuraciones (44.1/16 y 48/24) para asegurar que se complete.)*

</details>


---

# PARTE 2 · DOSSIER Y ACTIVIDADES (Material para el Alumnado)

**Materia:** Grupo A · **Tema:** NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son

## 1. Conceptos clave y guía de estudio

- **Punto 1:** A señal acústica é unha onda de presión continua no tempo. Para procesala dixitalmente hai que realizar unha conversión analóxico-dixital (ADC), que consta de dúas etapas: o muestreo (discretización temporal) e a cuantización (discretización en amplitude). Este proceso é a base das NTAM (Novas Tecnoloxías Aplicadas á Música), que abarcan a dixitalización e o procesamento de audio.

- **Punto 2:** A frecuencia de muestreo (sample rate) determina o límite de frecuencias reproducibles segundo o teorema de Nyquist-Shannon: a frecuencia de muestreo debe ser polo menos o dobre da frecuencia máxima da señal para evitar o aliasing ou repliegue espectral. Este fenómeno combátese con filtros pasabajos antialiasing. Os estándares comúns son 44.1 kHz (calidade CD) e 48 kHz (vídeo/estudo).

- **Punto 3:** A resolución ou profundidade de bits (bit depth: 16 bit, 24 bit) determina o rango dinámico cuantizado, aproximadamente 6 dB por bit. Isto significa que cada bit engadido aumenta o rango dinámico en 6 dB. A cuantización introduce un erro (ruído de cuantización) que se pode enmascarar co dither, que reduce a distorsión armónica de baixo nivel.

- **Punto 4:** Na síntese sustractiva pártense de osciladores ricos en armónicos: a onda senoidal é unha onda pura sen armónicos; a onda cuadrada ou pulso ten só armónicos impares; a onda triangular tamén ten armónicos impares pero con caída rápida; e a onda dente de sierra contén todos os armónicos enteiros. Estes osciladores moldeanse posteriormente mediante filtros resonantes e envolventes ADSR.

- **Punto 5:** Aínda que as fontes non detallan os valores de 96 kHz nin a relación exacta entre bit depth e rango dinámico en dB para 16 e 24 bit, pódese inferir que 96 kHz é un estándar de alta resolución que permite maior ancho de banda (ata 48 kHz) e que 16 bit ofrece ~96 dB e 24 bit ~144 dB de rango dinámico, aplicando a regra de 6 dB por bit. Esta inferencia é coherente coa información proporcionada sobre 44.1 kHz, 48 kHz e a regra dos 6 dB por bit.

### Esquemas de estudio

#### Cadea de conversión analóxico-dixital (ADC)

**Señal analóxica** (Onda de presión continua no tempo.) → **Muestreo** (Discretización temporal a intervalos regulares (frecuencia de muestreo).) → **Cuantización** (Asignación de valores de amplitude discretos (bit depth).) → **Codificación dixital** (Secuencia de números binarios que representa a onda.)

Etapas da conversión analóxico-dixital segundo as fontes: primeiro o muestreo, despois a cuantización.

#### Osciladores básicos e contido harmónico

| Concepto | Característica / Función |
| --- | --- |
| Senoidal | Onda pura sen armónicos. |
| Cuadrada / pulso | Armónicos impares. |
| Triangular | Armónicos impares con caída rápida. |
| Dente de sierra | Todos os armónicos enteiros. |

Contido harmónico dos osciladores básicos empregados na síntese sustractiva.

## 2. Repertorio, fuentes y audiciones de trabajo

- Ordenador con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Xerador de ton senoidal e plugin bitcrusher.
- Analizador de espectro.
- Fonte S1: documento sobre NTAM, ADC, Nyquist-Shannon, bit depth e osciladores.
- Guión de prácticas con pasos e táboas de rexistro.

## 3. Cuaderno de actividades y ejercicios prácticos

### Actividad 1: Configuración da sesión DAW e exploración de frecuencias de muestreo [Individual] (15 min)

**Tarea:** Abre o teu DAW, crea unha sesión nova e configura a frecuencia de muestreo a 44.1 kHz e a profundidade a 16 bit. Despois cambia a 48 kHz/24 bit e a 96 kHz/24 bit. Anota as diferenzas que observes na interface e no rendemento.

**Entregable:** Captura de pantalla ou documento coas tres configuracións e unha breve nota das diferenzas observadas.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 2: Audición do aliasing e efecto do bitcrusher [Individual] (20 min)

**Tarea:** Xera un ton senoidal a 1 kHz. Sube a frecuencia gradualmente ata superar a metade da frecuencia de muestreo (22.05 kHz a 44.1 kHz) e escoita o aliasing. Despois insire un bitcrusher e reduce a resolución de 16 a 8, 4 e 2 bit, escoitando o aumento do ruído. Anota as túas impresións.

**Entregable:** Táboa coas frecuencias probadas, a aparición do aliasing e a descrición do son con cada redución de bits.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 3: Deseño dun son elemental con osciladores e filtro paso-baixo [Individual] (20 min)

**Tarea:** No teu sintetizador software, selecciona un oscilador de dente de sierra. Observa o seu espectro harmónico. Aplica un filtro paso-baixo e varía a frecuencia de corte e a resonancia. Repite con onda cuadrada, triangular e senoidal. Crea un son curto e gárdao.

**Entregable:** Ficheiro de audio cun son deseñado e unha captura do espectro antes e despois do filtro.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 4: Posta en común e reflexión sobre a calidade dixital [Colectivo] (5 min)

**Tarea:** Comparte co grupo as túas observacións sobre o aliasing e o bitcrusher. Explica que configuración usarías para unha gravación musical e por que. Escoita as propostas dos demais e debate.

**Entregable:** Participación na discusión e unha conclusión escrita breve sobre a configuración axeitada para distintos usos.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```


Fragmentos no enviados al modelo por presupuesto o duplicación: 5.
