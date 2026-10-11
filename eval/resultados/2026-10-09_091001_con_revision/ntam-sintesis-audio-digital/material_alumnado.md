# Material de la sesión

## NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son

**Materia y grupo:** Grupo A
**Nivel:** 3º GP
**Duración:** 60 minutos

## Qué vamos a aprender

- Comprender a natureza da señal acústica e as etapas da conversión analóxico-dixital (ADC).
- Aplicar o teorema de Nyquist-Shannon para determinar a frecuencia de muestreo axeitada e evitar o aliasing.
- Relacionar a profundidade de bits co rango dinámico e o erro de cuantización, e empregar o dither.
- Identificar os osciladores básicos da síntese sustractiva e o seu contido harmónico.
- Configurar unha sesión DAW e deseñar un son elemental con filtro paso-baixo e bitcrusher.

## 01 · Contenido teórico de las fuentes

### 1. Punto clave

O son é unha onda continua, pero o ordenador necesita números. A conversión analóxico-dixital (ADC) fai dúas cousas: tomar mostras no tempo (muestreo) e asignar valores de amplitude (cuantización).

### 2. Punto clave

Para dixitalizar un son sen erro, a frecuencia de muestreo debe ser como mínimo o dobre da frecuencia máis aguda que queiras capturar. Se non, aparece o aliasing: frecuencias altas que se 'replegan' e soan como tons falsos. Os valores típicos son 44.1 kHz e 48 kHz.

### 3. Punto clave

Cada bit de resolución engade uns 6 dB de rango dinámico. Con 16 bit tes uns 96 dB; con 24 bit, uns 144 dB. O dither engádese antes de cuantizar para que o erro soe como ruído suave en vez de distorsión.

### 4. Punto clave

Os osciladores básicos xeran ondas con distintos contidos harmónicos: a senoidal non ten armónicos, a cuadrada e a triangular só impares (a triangular cae rápido), e a dente de sierra ten todos. Despois moldéanse con filtros e envolventes.

### 5. Punto clave

Aínda que as fontes non mencionan 96 kHz, pódese deducir que é unha frecuencia de alta resolución que captura ata 48 kHz. Do mesmo xeito, 16 bit dan uns 96 dB e 24 bit uns 144 dB de rango dinámico, aplicando a regra de 6 dB por bit.


## 02 · Esquemas de estudio

### Cadea de conversión analóxico-dixital (ADC)

*Etapas da conversión analóxico-dixital segundo as fontes: primeiro o muestreo, despois a cuantización.*

| Elemento / Sección | Estructura y funcionamiento |
| --- | --- |
| **Señal analóxica** | Onda de presión continua no tempo. |
| **Muestreo** | Discretización temporal a intervalos regulares (frecuencia de muestreo). |
| **Cuantización** | Asignación de valores de amplitude discretos (bit depth). |
| **Codificación dixital** | Secuencia de números binarios que representa a onda. |

### Osciladores básicos e contido harmónico

*Contido harmónico dos osciladores básicos empregados na síntese sustractiva.*

| Elemento / Sección | Estructura y funcionamiento |
| --- | --- |
| **Senoidal** | Onda pura sen armónicos. |
| **Cuadrada / pulso** | Armónicos impares. |
| **Triangular** | Armónicos impares con caída rápida. |
| **Dente de sierra** | Todos os armónicos enteiros. |


## 03 · Conceptos obligatorios para aprender

| Concepto Obligatorio | Definición y Aplicación en el Aula |
| --- | --- |
| **Señal analóxica** | Onda de presión continua no tempo. |
| **Muestreo** | Discretización temporal a intervalos regulares (frecuencia de muestreo). |
| **Cuantización** | Asignación de valores de amplitude discretos (bit depth). |
| **Codificación dixital** | Secuencia de números binarios que representa a onda. |
| **Senoidal** | Onda pura sen armónicos. |
| **Cuadrada / pulso** | Armónicos impares. |
| **Triangular** | Armónicos impares con caída rápida. |
| **Dente de sierra** | Todos os armónicos enteiros. |

## Cheat sheet de práctica

Consulta rápida para tener a mano durante el trabajo de hoy.

| Elemento | Para qué sirve |
| --- | --- |
| Señal analóxica | Onda de presión continua no tempo. |
| Muestreo | Discretización temporal a intervalos regulares (frecuencia de muestreo). |
| Cuantización | Asignación de valores de amplitude discretos (bit depth). |
| Codificación dixital | Secuencia de números binarios que representa a onda. |
| Senoidal | Onda pura sen armónicos. |
| Cuadrada / pulso | Armónicos impares. |
| Triangular | Armónicos impares con caída rápida. |
| Dente de sierra | Todos os armónicos enteiros. |

### Secuencia rápida de hoy

- **1. Configuración da sesión DAW e exploración de frecuencias de muestreo** · 15 min
- **2. Audición do aliasing e efecto do bitcrusher** · 20 min
- **3. Deseño dun son elemental con osciladores e filtro paso-baixo** · 20 min
- **4. Posta en común e reflexión sobre a calidade dixital** · 5 min
## 04 · Trabajos para el alumnado

### Trabajo 1: Análisis auditivo y sobre partitura
- **Objetivo:** Identificar en la partitura de estudio los elementos técnicos clave de NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son.
- **Instrucciones:** Marcar las entradas temáticas, cesuras y cambios de textura musical indicados en la sesión.

### Trabajo 2: Diagramación formal y estructural
- **Objetivo:** Realizar un esquema gráfico o mapa de la estructura formal de las obras trabajadas.
- **Instrucciones:** Delimitar las secciones principales, transiciones y puntos de articulación cadencial.

### Trabajo 3: Matriz comparativa de estilo y textura
- **Objetivo:** Contrastar dos pasajes o ejemplos musicales analizando sus rasgos diferenciales.
- **Instrucciones:** Elaborar una tabla comparando textura (homofonía vs. contrapunto), ritmo armónico y tratamiento melódico.

### Trabajo 4: Cuestionario de consolidación conceptual
- **Objetivo:** Afianzar el dominio de los conceptos obligatorios de la unidad.
- **Instrucciones:** Definir los términos clave trabajados y redactar una breve síntesis razonada con ejemplos concretos.

### Trabajo en clase

#### 1. Configuración da sesión DAW e exploración de frecuencias de muestreo [Individual] · 0–15 min

- **Tarea:** Abre o teu DAW, crea unha sesión nova e configura a frecuencia de muestreo a 44.1 kHz e a profundidade a 16 bit. Despois cambia a 48 kHz/24 bit e a 96 kHz/24 bit. Anota as diferenzas que observes na interface e no rendemento.
- **Entregable:** Captura de pantalla ou documento coas tres configuracións e unha breve nota das diferenzas observadas.

#### 2. Audición do aliasing e efecto do bitcrusher [Individual] · 15–35 min

- **Tarea:** Xera un ton senoidal a 1 kHz. Sube a frecuencia gradualmente ata superar a metade da frecuencia de muestreo (22.05 kHz a 44.1 kHz) e escoita o aliasing. Despois insire un bitcrusher e reduce a resolución de 16 a 8, 4 e 2 bit, escoitando o aumento do ruído. Anota as túas impresións.
- **Entregable:** Táboa coas frecuencias probadas, a aparición do aliasing e a descrición do son con cada redución de bits.

#### 3. Deseño dun son elemental con osciladores e filtro paso-baixo [Individual] · 35–55 min

- **Tarea:** No teu sintetizador software, selecciona un oscilador de dente de sierra. Observa o seu espectro harmónico. Aplica un filtro paso-baixo e varía a frecuencia de corte e a resonancia. Repite con onda cuadrada, triangular e senoidal. Crea un son curto e gárdao.
- **Entregable:** Ficheiro de audio cun son deseñado e unha captura do espectro antes e despois do filtro.

#### 4. Posta en común e reflexión sobre a calidade dixital [Colectivo] · 55–60 min

- **Tarea:** Comparte co grupo as túas observacións sobre o aliasing e o bitcrusher. Explica que configuración usarías para unha gravación musical e por que. Escoita as propostas dos demais e debate.
- **Entregable:** Participación na discusión e unha conclusión escrita breve sobre a configuración axeitada para distintos usos.

## Material necesario

- Ordenador con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Xerador de ton senoidal e plugin bitcrusher.
- Analizador de espectro.
- Fonte S1: documento sobre NTAM, ADC, Nyquist-Shannon, bit depth e osciladores.
- Guión de prácticas con pasos e táboas de rexistro.

## Fuentes de consulta

- Fuente de evaluación: ntam-sintesis-audio-digital — Musicología Académica
- Fuente de evaluación: polifonia-siglo-xv — Musicología Académica
- Fuente de evaluación: teoria-griega-seikilos — Musicología Académica
