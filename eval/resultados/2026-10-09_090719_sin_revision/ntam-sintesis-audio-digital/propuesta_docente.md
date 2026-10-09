# Propuesta pedagógica

Registro: run-8c1e75be5e584b4291fdbcd9f13664c3

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
| **R1** | Explicar la naturaleza de la señal acústica y su conversión analógico-digital (ADC). | contenido | Cubierto | #1 | A fonte S1 describe a conversión ADC como muestreo e cuantización, e a natureza da sinal acústica como onda dixitalizable. |
| **R2** | Explicar la frecuencia de muestreo (44.1 kHz, 48 kHz, 96 kHz) y el teorema de Nyquist-Shannon, incluyendo aliasing/repliegue espectral y filtros antialiasing. | contenido | Cubierto | #2 | S1 explica o teorema de Nyquist-Shannon, o aliasing e os filtros antialiasing, e menciona 44.1 kHz e 48 kHz. Non menciona 96 kHz explicitamente, pero o criterio do profesor inclúeo; indícase como parcial nese punto. |
| **R3** | Explicar la resolución en bits (16 bit, 24 bit), su relación con el rango dinámico (6 dB por bit), el error de cuantización y el dither. | contenido | Cubierto | #3 | S1 explica bit depth (16/24 bit), a relación de 6 dB por bit, o erro de cuantización e o dither. |
| **R4** | Introducir los osciladores básicos en síntesis sustractiva: senoidal, cuadrada, triangular y diente de sierra, con sus armónicos. | contenido | Cubierto | #4 | S1 describe os catro osciladores básicos e os seus harmónicos. |
| **R5** | Realizar una actividad práctica con estación DAW/sintetizador software: configurar sesión, escuchar el efecto de reducir la resolución (bitcrusher) y diseñar un sonido elemental con un filtro paso-bajo. | actividad | Parcial | #5 | As fontes non detallan a configuración dunha sesión DAW, o uso de bitcrusher nin parámetros concretos de filtro paso-baixo. A actividade práctica debe apoiarse no coñecemento do profesor e no equipamento do aula. |

## 1. Planificación didáctica y objetivos

### Objetivos de aprendizaje

- Comprender a natureza da sinal acústica e o proceso de conversión analóxico-dixital (ADC).
- Aplicar o teorema de Nyquist-Shannon para explicar a frecuencia de muestreo, o aliasing e os filtros antialiasing.
- Relacionar a profundidade de bits co rango dinámico, o erro de cuantización e o dither.
- Identificar os osciladores básicos da síntese sustractiva e o seu contido harmónico.
- Configurar unha sesión DAW e deseñar un son elemental con filtro paso-baixo, experimentando coa redución de resolución.

**Dificultad propuesta:** Nivel intermedio (3º Grao Profesional). Requírese familiaridade básica co manexo de ordenador e conceptos elementais de acústica. A parte teórica é accesible, pero a práctica con DAW/sintetizador require guía do profesor.

**Evaluación de la sesión:** Avaliación continua mediante observación directa durante as actividades prácticas. Avaliaranse: a correcta configuración da sesión DAW (48 kHz/24 bit), a capacidade de identificar os efectos da redución de resolución, o deseño coherente dun son elemental con filtro paso-baixo, e a ficha descritiva entregada. Tamén se valorará a participación nas respostas colectivas sobre a cadea ADC.

### Secuencia didáctica y actividades

**0–15 min · Análise da cadea ADC e parámetros de dixitalización [Colectivo]**

**Pautas docentes:** Presenta a cadea ADC cun esquema na pizarra ou proxector. Explica a diferenza entre muestreo e cuantización. Relaciona a frecuencia de muestreo co teorema de Nyquist-Shannon e introduce os valores 44.1 kHz, 48 kHz e 96 kHz. Explica o aliasing cun exemplo visual (dente de serra ou roda de carro). Finalmente, introduce bit depth, a regra de 6 dB por bit e o dither.

**Consigna del alumno:** Escoita tres exemplos de audio a distintas frecuencias de muestreo e profundidades de bits. Anota nunha táboa as diferenzas percibidas e responde: que parámetro afecta máis ao ruído de fondo? Que parámetro limita as frecuencias agudas?

**Entregable:** Táboa comparativa cos tres exemplos e respostas ás preguntas.

**Solución / Criterios de corrección:** A frecuencia de muestreo limita as frecuencias agudas (a 44.1 kHz o límite teórico é 22.05 kHz). A profundidade de bits afecta ao ruído de fondo e ao rango dinámico (16 bit ≈ 96 dB, 24 bit ≈ 144 dB). O dither reduce a distorsión de baixo nivel.

Base documental: contenidos 1, 2, 3.

**15–35 min · Configuración dunha sesión DAW e experimento con bitcrusher [Individual]**

**Pautas docentes:** Guía a configuración dunha sesión nova no DAW do aula: frecuencia de muestreo 48 kHz, profundidade 24 bit. Insire un bitcrusher nunha pista con material musical e vai reducindo bits e sample rate para que se escoite o efecto. Relaciona o que se escoita coa teoría: aliasing, ruído de cuantización, perda de agudos.

**Consigna del alumno:** Configura unha sesión a 48 kHz/24 bit. Insire un bitcrusher nunha pista e experimenta reducindo a resolución (bits) e a frecuencia de muestreo. Grava un fragmento de 10 segundos con cada axuste e describe o que escoitas.

**Entregable:** Sesión DAW gardada con tres fragmentos (orixinal, 8 bit, 4 bit) e unha descrición escrita dos efectos.

**Solución / Criterios de corrección:** Ao reducir bits aparece ruído de cuantización e distorsión; ao reducir a frecuencia de muestreo aparece aliasing (frecuencias metálicas ou replegadas). A sesión debe gardarse co nome indicado.

Base documental: contenidos 2, 3, 5.

**35–60 min · Deseño dun son elemental con osciladores e filtro paso-baixo [Individual]**

**Pautas docentes:** Explica os catro osciladores básicos (senoidal, cuadrada, triangular, dente de sierra) e o seu contido harmónico. Mostra como un filtro paso-baixo moldea o timbre. Guía ao alumnado na creación dun son sinxelo: escolle un oscilador, axusta o filtro (corte e resonancia) e engade unha envolvente ADSR básica.

**Consigna del alumno:** No sintetizador software, escolle un oscilador (proba os catro) e deseña un son elemental usando un filtro paso-baixo. Axusta a frecuencia de corte e a resonancia. Garda o preset e describe o timbre resultante e a súa relación co contido harmónico do oscilador.

**Entregable:** Preset gardado e ficha descritiva co oscilador usado, axustes de filtro e descrición do timbre.

**Solución / Criterios de corrección:** A onda senoidal non ten harmónicos e soa pura; a cuadrada ten harmónicos impares e soa occa; a triangular ten impares con caída rápida e soa máis suave; a dente de sierra ten todos os harmónicos e soa brillante. O filtro paso-baixo atenúa os agudos e suaviza o timbre.

Base documental: contenidos 4, 5.

### Recursos y partituras por preparar

- Ordenadores con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Plugin bitcrusher (pode ser o incluído no DAW ou un gratuito).
- Proxector e sistema de son do aula.
- Ficheiros de audio de exemplo a distintas frecuencias de muestreo e bits.
- Fichas de traballo impresas ou dixitais para as actividades.

**Observaciones didácticas:** As fontes S1 non detallan parámetros concretos de filtros paso-baixo nin o uso de bitcrusher; o profesorado deberá concretar eses axustes segundo o software dispoñible. A fonte S1 menciona 44.1 kHz e 48 kHz, pero non 96 kHz; este valor engádese por criterio do profesor. As fontes S2, S3 e S4 non son relevantes para este tema (tratan polifonía do século XV e teoría grega).

## 2. Fundamentación teórica y contenidos

**Contenido 1 — Síntesis respaldada por bibliografía:**

A señal acústica é unha onda de presión continua no tempo. A conversión analóxico-dixital (ADC) transforma esa onda en números mediante dous procesos: o muestreo (discretización temporal) e a cuantización (discretización en amplitude). O muestreo mide a amplitude da onda a intervalos regulares (frecuencia de muestreo) e a cuantización asigna cada mostra a un valor discreto segundo a profundidade de bits. Estes dous parámetros definen a calidade e os límites do audio dixital.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «Las Nuevas Tecnologías Aplicadas a la Música (NTAM) abarcan la digitalización y el procesamiento de audio.»
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La conversión analógico-digital (ADC) consta de muestreo y cuantización.»

**Contenido 2 — Síntesis respaldada por bibliografía:**

O teorema de Nyquist-Shannon establece que a frecuencia de muestreo debe ser polo menos o dobre da frecuencia máxima da sinal para poder reconstruíla sen perda. Se non se cumpre, prodúcese aliasing ou repliegue espectral: frecuencias altas aparecen como frecuencias máis baixas falsas. Para evitalo empréganse filtros pasabajos antialiasing antes do muestreo. Os estándares habituais son 44.1 kHz (calidade CD) e 48 kHz (vídeo/estudo); tamén se usa 96 kHz en contextos de alta resolución.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La frecuencia de muestreo (sample rate) determina el límite de frecuencias reproducibles según el teorema de muestreo de Nyquist-Shannon: la frecuencia de muestreo debe ser al menos el doble de la frecuencia máxima de la señal para evitar el fenómeno de aliasing o repliegue espectral, combatido con filtros pasabajos antialiasing.»
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «Los estándares comunes son 44.1 kHz (calidad CD) y 48 kHz (vídeo/estudio).»

**Contenido 3 — Síntesis respaldada por bibliografía:**

A resolución ou profundidade de bits (bit depth) determina o rango dinámico cuantizado: aproximadamente 6 dB por bit. Así, 16 bit ofrecen uns 96 dB de rango dinámico e 24 bit uns 144 dB. A cuantización introduce un erro (ruído de cuantización) que se pode enmascarar co dither, unha pequena cantidade de ruído aleatorio engadido antes de cuantizar para evitar distorsión armónica de baixo nivel.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «La resolución o profundidad de bits (bit depth: 16 bit, 24 bit) determina el rango dinámico cuantizado (aproximadamente 6 dB por bit), introduciendo el dither para enmascarar la distorsión armónica de bajo nivel.»

**Contenido 4 — Síntesis respaldada por bibliografía:**

Na síntese sustractiva pártense de osciladores ricos en harmónicos e logo moldease o son con filtros e envolventes. Os osciladores básicos son: senoidal (onda pura, sen harmónicos), cuadrada ou pulso (só harmónicos impares), triangular (harmónicos impares con caída rápida) e dente de sierra (todos os harmónicos enteiros). Cada un ten un timbre característico segundo o seu contido harmónico.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «En la síntesis sustractiva se parte de osciladores ricos en armónicos: onda senoidal (onda pura sin armónicos), onda cuadrada o pulso (armónicos impares), onda triangular (armónicos impares con caída rápida) y onda diente de sierra (todos los armónicos enteros), moldeadas posteriormente mediante filtros resonantes y envolventes ADSR.»

**Contenido 5 — Inferencia de IA:**

Aínda que a fonte S1 describe os osciladores e a síntese sustractiva, non detalla parámetros concretos de filtros paso-baixo (frecuencia de corte, resonancia) nin o deseño paso a paso dun son elemental. Para a actividade práctica, o profesorado deberá concretar eses axustes no DAW/sintetizador, xa que as fontes non os especifican.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: ntam-sintesis-audio-digital*, líneas 1–1 [Bibliografía] — «En la síntesis sustractiva se parte de osciladores ricos en armónicos: onda senoidal (onda pura sin armónicos), onda cuadrada o pulso (armónicos impares), onda triangular (armónicos impares con caída rápida) y onda diente de sierra (todos los armónicos enteros), moldeadas posteriormente mediante filtros resonantes y envolventes ADSR.»

## Esquema documentado

### Cadea de conversión analóxico-dixital (ADC)

**Sinal analóxica** (Onda de presión continua no tempo.) → **Filtro antialiasing** (Filtro pasabajos que elimina frecuencias por riba de metade da frecuencia de muestreo.) → **Muestreo** (Toma de mostras a intervalos regulares (frecuencia de muestreo).) → **Cuantización** (Arredondamento da amplitude a valores discretos segundo a profundidade de bits.) → **Dither (opcional)** (Ruído aleatorio engadido antes de cuantizar para enmascarar a distorsión de baixo nivel.) → **Sinal dixital** (Secuencia de números que representa o son orixinal.)

Esquema da conversión analóxico-dixital: dende a onda continua ata a secuencia dixital, incluíndo o filtro antialiasing e o dither.

## Esquema documentado

### Osciladores básicos e contido harmónico

| Elemento | Relación o función |
| --- | --- |
| Senoidal | Onda pura, sen harmónicos. |
| Cuadrada / pulso | Só harmónicos impares. |
| Triangular | Harmónicos impares con caída rápida. |
| Dente de sierra | Todos os harmónicos enteiros. |

Comparación dos catro osciladores básicos da síntese sustractiva segundo o seu contido harmónico.


---

# PARTE 2 · DOSSIER Y ACTIVIDADES (Material para el Alumnado)

**Materia:** Grupo A · **Tema:** NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son

## 1. Conceptos clave y guía de estudio

- **Punto 1:** A señal acústica é unha onda de presión continua no tempo. A conversión analóxico-dixital (ADC) transforma esa onda en números mediante dous procesos: o muestreo (discretización temporal) e a cuantización (discretización en amplitude). O muestreo mide a amplitude da onda a intervalos regulares (frecuencia de muestreo) e a cuantización asigna cada mostra a un valor discreto segundo a profundidade de bits. Estes dous parámetros definen a calidade e os límites do audio dixital.

- **Punto 2:** O teorema de Nyquist-Shannon establece que a frecuencia de muestreo debe ser polo menos o dobre da frecuencia máxima da sinal para poder reconstruíla sen perda. Se non se cumpre, prodúcese aliasing ou repliegue espectral: frecuencias altas aparecen como frecuencias máis baixas falsas. Para evitalo empréganse filtros pasabajos antialiasing antes do muestreo. Os estándares habituais son 44.1 kHz (calidade CD) e 48 kHz (vídeo/estudo); tamén se usa 96 kHz en contextos de alta resolución.

- **Punto 3:** A resolución ou profundidade de bits (bit depth) determina o rango dinámico cuantizado: aproximadamente 6 dB por bit. Así, 16 bit ofrecen uns 96 dB de rango dinámico e 24 bit uns 144 dB. A cuantización introduce un erro (ruído de cuantización) que se pode enmascarar co dither, unha pequena cantidade de ruído aleatorio engadido antes de cuantizar para evitar distorsión armónica de baixo nivel.

- **Punto 4:** Na síntese sustractiva pártense de osciladores ricos en harmónicos e logo moldease o son con filtros e envolventes. Os osciladores básicos son: senoidal (onda pura, sen harmónicos), cuadrada ou pulso (só harmónicos impares), triangular (harmónicos impares con caída rápida) e dente de sierra (todos os harmónicos enteiros). Cada un ten un timbre característico segundo o seu contido harmónico.

- **Punto 5:** Aínda que a fonte S1 describe os osciladores e a síntese sustractiva, non detalla parámetros concretos de filtros paso-baixo (frecuencia de corte, resonancia) nin o deseño paso a paso dun son elemental. Para a actividade práctica, o profesorado deberá concretar eses axustes no DAW/sintetizador, xa que as fontes non os especifican.

### Esquemas de estudio

#### Cadea de conversión analóxico-dixital (ADC)

**Sinal analóxica** (Onda de presión continua no tempo.) → **Filtro antialiasing** (Filtro pasabajos que elimina frecuencias por riba de metade da frecuencia de muestreo.) → **Muestreo** (Toma de mostras a intervalos regulares (frecuencia de muestreo).) → **Cuantización** (Arredondamento da amplitude a valores discretos segundo a profundidade de bits.) → **Dither (opcional)** (Ruído aleatorio engadido antes de cuantizar para enmascarar a distorsión de baixo nivel.) → **Sinal dixital** (Secuencia de números que representa o son orixinal.)

Esquema da conversión analóxico-dixital: dende a onda continua ata a secuencia dixital, incluíndo o filtro antialiasing e o dither.

#### Osciladores básicos e contido harmónico

| Concepto | Característica / Función |
| --- | --- |
| Senoidal | Onda pura, sen harmónicos. |
| Cuadrada / pulso | Só harmónicos impares. |
| Triangular | Harmónicos impares con caída rápida. |
| Dente de sierra | Todos os harmónicos enteiros. |

Comparación dos catro osciladores básicos da síntese sustractiva segundo o seu contido harmónico.

## 2. Repertorio, fuentes y audiciones de trabajo

- Ordenadores con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Plugin bitcrusher (pode ser o incluído no DAW ou un gratuito).
- Proxector e sistema de son do aula.
- Ficheiros de audio de exemplo a distintas frecuencias de muestreo e bits.
- Fichas de traballo impresas ou dixitais para as actividades.

## 3. Cuaderno de actividades y ejercicios prácticos

### Actividad 1: Análise da cadea ADC e parámetros de dixitalización [Colectivo] (15 min)

**Tarea:** Escoita tres exemplos de audio a distintas frecuencias de muestreo e profundidades de bits. Anota nunha táboa as diferenzas percibidas e responde: que parámetro afecta máis ao ruído de fondo? Que parámetro limita as frecuencias agudas?

**Entregable:** Táboa comparativa cos tres exemplos e respostas ás preguntas.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 2: Configuración dunha sesión DAW e experimento con bitcrusher [Individual] (20 min)

**Tarea:** Configura unha sesión a 48 kHz/24 bit. Insire un bitcrusher nunha pista e experimenta reducindo a resolución (bits) e a frecuencia de muestreo. Grava un fragmento de 10 segundos con cada axuste e describe o que escoitas.

**Entregable:** Sesión DAW gardada con tres fragmentos (orixinal, 8 bit, 4 bit) e unha descrición escrita dos efectos.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 3: Deseño dun son elemental con osciladores e filtro paso-baixo [Individual] (25 min)

**Tarea:** No sintetizador software, escolle un oscilador (proba os catro) e deseña un son elemental usando un filtro paso-baixo. Axusta a frecuencia de corte e a resonancia. Garda o preset e describe o timbre resultante e a súa relación co contido harmónico do oscilador.

**Entregable:** Preset gardado e ficha descritiva co oscilador usado, axustes de filtro e descrición do timbre.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```


Fragmentos no enviados al modelo por presupuesto o duplicación: 5.
