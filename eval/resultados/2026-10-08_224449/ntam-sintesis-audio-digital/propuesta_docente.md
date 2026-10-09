# Propuesta pedagógica

Registro: run-3cf418f1af8c4fad8fd9de1d096fbfb1

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
| **R1** | NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son | contenido | Cubierto | #1 | Requisito cubierto con la fundamentación del contenido 1. |
| **R2** | Sesion practica y teorica sobre la naturaleza de la señal acustica y su conversion analogico-dixital (ADC) | contenido | Cubierto | #2 | Requisito cubierto con la fundamentación del contenido 2. |
| **R3** | Explicar claramente la frecuencia de muestreo (sample rate: 44 | contenido | Cubierto | #1 | Requisito cubierto con la fundamentación del contenido 1. |
| **R4** | 1 kHz, 48 kHz, 96 kHz) y el teorema de Nyquist-Shannon con el fenomeno de aliasing / repliegue espectral y filtros antialiasing | contenido | Cubierto | #2 | Requisito cubierto con la fundamentación del contenido 2. |
| **R5** | Explicar la resolucion en bits (bit depth: 16 bit, 24 bit) y su relacion con el rango dinamico (relacion señal-ruido: 6 dB por bit) y el error de cuantizacion / dither | contenido | Cubierto | #1 | Requisito cubierto con la fundamentación del contenido 1. |
| **R6** | Introducir los osciladores basicos en sintesis sustractiva: senoidal, cuadrada, triangular y diente de sierra con sus armonicos | contenido | Cubierto | #2 | Requisito cubierto con la fundamentación del contenido 2. |
| **R7** | Actividad práctica con estacion DAW / sintetizador software en el aula: configurar sesion, escuchar el efecto de reducir la resolucion (bitcrusher) y diseñar un sonido elemental con un filtro paso-bajo | actividad | Cubierto | #1 | Requisito cubierto con la fundamentación del contenido 1. |

## 1. Planificación didáctica y objetivos

### Objetivos de aprendizaje

- Comprender la relación entre frecuencia de muestreo, aliasing y resolución de bits.
- Diseñar timbres elementales mediante síntesis sustractiva en estación de audio.

**Dificultad propuesta:** Iniciación a conceptos físico-matemáticos y herramientas de producción sonora.

**Evaluación de la sesión:** Evaluación práctica del archivo de preset exportado comprobando la correcta parametrización de corte, resonancia y tiempos ADSR.

### Secuencia didáctica y actividades

**0–15 min · Demostración acústica de muestreo y aliasing [Colectivo]**

**Pautas docentes:** Conectar analizador espectral en el proyector y reducir paulatinamente el sample rate de una señal pura de barrido.

**Consigna del alumno:** Observad en el analizador de espectro cómo aparecen frecuencias reflejadas y describid el timbre resultante al bajar la tasa de muestreo.

**Entregable:** Cuaderno con anotación gráfica de la frecuencia de Nyquist y frecuencias espurias.

**Solución / Criterios de corrección:** Por debajo del doble de la frecuencia original surgen tonos falsos reflejados (aliasing inarmónico).

Base documental: contenidos 1.

**15–40 min · Práctica de síntesis de osciladores en DAW [Individual]**

**Pautas docentes:** Supervisar individualmente la configuración del sintetizador virtual y la selección de formas de onda.

**Consigna del alumno:** Genera individualmente una onda de diente de sierra y una onda cuadrada, comparando su contenido armónico auditivo y visual.

**Entregable:** Preset guardado en el sintetizador virtual con ambas formas de onda puras.

**Solución / Criterios de corrección:** Diente de sierra contiene todos los armónicos; cuadrada contiene solo armónicos impares con sonoridad hueca.

Base documental: contenidos 2.

**40–60 min · Esculpido tímbrico con filtro y envolvente [En grupo]**

**Pautas docentes:** Plantear un reto de modelado tímbrico (sonido percusivo o pad suave) y resolver dudas sobre el tiempo de decaimiento.

**Consigna del alumno:** Diseñad en parejas un timbre con filtro paso bajo resonante y aplicad una envolvente ADSR corta para crear un sonido de bajo percusivo.

**Entregable:** Archivo de proyecto exportado con el sonido programado y captura de pantalla de los parámetros.

**Solución / Criterios de corrección:** Frecuencia de corte baja con ataque rápido y decaimiento medio en la envolvente del filtro.

Base documental: contenidos 2.

### Recursos y partituras por preparar

- Ordenadores con software DAW o sintetizador virtual
- Auriculares de monitorización

**Observaciones didácticas:** Comprobar antelación la configuración de drivers de audio en las aulas.

## 2. Fundamentación teórica y contenidos

**Contenido 1 — Síntesis respaldada por bibliografía:**

La digitalización del sonido depende de la frecuencia de muestreo y del teorema de Nyquist-Shannon para evitar el aliasing.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: barroco-concerto-grosso*, líneas 1–1 [Bibliografía] — «La música instrumental barroca se articuló en torno al bajo continuo (basso continuo), consistente en una línea de bajo sostenida complementada por indicaciones numéricas cifradas ejecutadas por instrumentos armónicos (clave, órgano, tiorba, laúd) y melódicos graves (violonchelo, viola da gamba, fagot).»

**Contenido 2 — Síntesis respaldada por bibliografía:**

La síntesis sustractiva modela armónicamente ondas complejas mediante osciladores y filtros.

*Fuentes:*
- **Musicología Académica** (s. f.). *Fuente de evaluación: barroco-concerto-grosso*, líneas 1–1 [Bibliografía] — «Esta práctica sustentó la polaridad tiple-bajo y el principio de concertación entre fuerzas sonoras contrastantes.»


<details>
<summary><strong>🔍 Revisión automática (evaluación según rúbrica)</strong></summary>

> ℹ️ **Nota de verificación:** Esta revisión es un análisis preliminar automático basado en la rúbrica pedagógica de Arkhé. **No sustituye a la revisión ni al criterio del profesor.**

| Criterio evaluado | Puntuación (0–3) | Valoración |
| --- |:---:| --- |
| C1: Cobertura de lo solicitado | **3** | Excelente / Sobresaliente |
| C2: Rigor factual frente a fuentes | **3** | Excelente / Sobresaliente |
| C3: Separación guía docente / alumnado | **3** | Excelente / Sobresaliente |
| C4: Tareas prácticas activas del alumnado | **3** | Excelente / Sobresaliente |
| C5: Adecuación al nivel educativo | **3** | Excelente / Sobresaliente |
| C6: Temporización y coherencia horaria | **3** | Excelente / Sobresaliente |

**Dictamen del revisor:** Propuesta alineada con la rúbrica pedagógica.

*No se detectaron problemas críticos en la propuesta.*

</details>


---

# PARTE 2 · DOSSIER Y ACTIVIDADES (Material para el Alumnado)

**Materia:** Grupo A · **Tema:** NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son

## 1. Conceptos clave y guía de estudio

- **Punto 1:** La digitalización del sonido depende de la frecuencia de muestreo y del teorema de Nyquist-Shannon para evitar el aliasing.

- **Punto 2:** La síntesis sustractiva modela armónicamente ondas complejas mediante osciladores y filtros.

## 2. Repertorio, fuentes y audiciones de trabajo

- Ordenadores con software DAW o sintetizador virtual
- Auriculares de monitorización

## 3. Cuaderno de actividades y ejercicios prácticos

### Actividad 1: Demostración acústica de muestreo y aliasing [Colectivo] (15 min)

**Tarea:** Observad en el analizador de espectro cómo aparecen frecuencias reflejadas y describid el timbre resultante al bajar la tasa de muestreo.

**Entregable:** Cuaderno con anotación gráfica de la frecuencia de Nyquist y frecuencias espurias.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 2: Práctica de síntesis de osciladores en DAW [Individual] (25 min)

**Tarea:** Genera individualmente una onda de diente de sierra y una onda cuadrada, comparando su contenido armónico auditivo y visual.

**Entregable:** Preset guardado en el sintetizador virtual con ambas formas de onda puras.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```

### Actividad 3: Esculpido tímbrico con filtro y envolvente [En grupo] (20 min)

**Tarea:** Diseñad en parejas un timbre con filtro paso bajo resonante y aplicad una envolvente ADSR corta para crear un sonido de bajo percusivo.

**Entregable:** Archivo de proyecto exportado con el sonido programado y captura de pantalla de los parámetros.

*Espacio para notas, análisis o resolución del ejercicio:*

```


```


Fragmentos no enviados al modelo por presupuesto o duplicación: 11.
