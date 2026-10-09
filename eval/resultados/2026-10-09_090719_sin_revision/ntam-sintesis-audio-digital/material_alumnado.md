# Material de la sesión

## NTAM: Audio dixital, teorema de Nyquist-Shannon e sintese de son

**Materia y grupo:** Grupo A
**Nivel:** 3º GP
**Duración:** 60 minutos

## Qué vamos a aprender

- Comprender a natureza da sinal acústica e o proceso de conversión analóxico-dixital (ADC).
- Aplicar o teorema de Nyquist-Shannon para explicar a frecuencia de muestreo, o aliasing e os filtros antialiasing.
- Relacionar a profundidade de bits co rango dinámico, o erro de cuantización e o dither.
- Identificar os osciladores básicos da síntese sustractiva e o seu contido harmónico.
- Configurar unha sesión DAW e deseñar un son elemental con filtro paso-baixo, experimentando coa redución de resolución.

## 01 · Contenido teórico de las fuentes

### 1. Punto clave

O son analóxico é unha onda continua; para gardalo en dixital hai que muestrear (tomar medidas no tempo) e cuantizar (arredondar a amplitude a valores discretos). Estes dous pasos son a base do ADC.

### 2. Punto clave

Para dixitalizar sen erros, a frecuencia de muestreo debe ser como mínimo o dobre da frecuencia máis alta do son. Se non, aparece aliasing (frecuencias falsas). Os valores típicos son 44.1 kHz, 48 kHz e 96 kHz, e os filtros antialiasing eliminan as frecuencias problemáticas antes de muestrear.

### 3. Punto clave

Cada bit de resolución engade uns 6 dB de rango dinámico: 16 bit ≈ 96 dB, 24 bit ≈ 144 dB. Ao cuantizar xérase un erro; o dither engádese para que ese erro soe como ruído suave en vez de distorsión.

### 4. Punto clave

Na síntese sustractiva úsanse osciladores con distintos harmónicos: a senoidal non ten harmónicos, a cuadrada só impares, a triangular impares que caen rápido e a dente de sierra todos os enteiros. Despois moldéanse con filtros e envolventes.

### 5. Punto clave

As fontes explican os tipos de oscilador, pero non dan valores concretos de filtro (corte, resonancia) para a práctica. Esa parte terá que concretala o profesor na sesión.


## 02 · Esquemas de estudio

### Cadea de conversión analóxico-dixital (ADC)

*Esquema da conversión analóxico-dixital: dende a onda continua ata a secuencia dixital, incluíndo o filtro antialiasing e o dither.*

| Elemento / Sección | Estructura y funcionamiento |
| --- | --- |
| **Sinal analóxica** | Onda de presión continua no tempo. |
| **Filtro antialiasing** | Filtro pasabajos que elimina frecuencias por riba de metade da frecuencia de muestreo. |
| **Muestreo** | Toma de mostras a intervalos regulares (frecuencia de muestreo). |
| **Cuantización** | Arredondamento da amplitude a valores discretos segundo a profundidade de bits. |
| **Dither (opcional)** | Ruído aleatorio engadido antes de cuantizar para enmascarar a distorsión de baixo nivel. |
| **Sinal dixital** | Secuencia de números que representa o son orixinal. |

### Osciladores básicos e contido harmónico

*Comparación dos catro osciladores básicos da síntese sustractiva segundo o seu contido harmónico.*

| Elemento / Sección | Estructura y funcionamiento |
| --- | --- |
| **Senoidal** | Onda pura, sen harmónicos. |
| **Cuadrada / pulso** | Só harmónicos impares. |
| **Triangular** | Harmónicos impares con caída rápida. |
| **Dente de sierra** | Todos os harmónicos enteiros. |


## 03 · Conceptos obligatorios para aprender

| Concepto Obligatorio | Definición y Aplicación en el Aula |
| --- | --- |
| **Sinal analóxica** | Onda de presión continua no tempo. |
| **Filtro antialiasing** | Filtro pasabajos que elimina frecuencias por riba de metade da frecuencia de muestreo. |
| **Muestreo** | Toma de mostras a intervalos regulares (frecuencia de muestreo). |
| **Cuantización** | Arredondamento da amplitude a valores discretos segundo a profundidade de bits. |
| **Dither (opcional)** | Ruído aleatorio engadido antes de cuantizar para enmascarar a distorsión de baixo nivel. |
| **Sinal dixital** | Secuencia de números que representa o son orixinal. |
| **Senoidal** | Onda pura, sen harmónicos. |
| **Cuadrada / pulso** | Só harmónicos impares. |

## Cheat sheet de práctica

Consulta rápida para tener a mano durante el trabajo de hoy.

| Elemento | Para qué sirve |
| --- | --- |
| Sinal analóxica | Onda de presión continua no tempo. |
| Filtro antialiasing | Filtro pasabajos que elimina frecuencias por riba de metade da frecuencia de muestreo. |
| Muestreo | Toma de mostras a intervalos regulares (frecuencia de muestreo). |
| Cuantización | Arredondamento da amplitude a valores discretos segundo a profundidade de bits. |
| Dither (opcional) | Ruído aleatorio engadido antes de cuantizar para enmascarar a distorsión de baixo nivel. |
| Sinal dixital | Secuencia de números que representa o son orixinal. |
| Senoidal | Onda pura, sen harmónicos. |
| Cuadrada / pulso | Só harmónicos impares. |
| Triangular | Harmónicos impares con caída rápida. |
| Dente de sierra | Todos os harmónicos enteiros. |

### Secuencia rápida de hoy

- **1. Análise da cadea ADC e parámetros de dixitalización** · 15 min
- **2. Configuración dunha sesión DAW e experimento con bitcrusher** · 20 min
- **3. Deseño dun son elemental con osciladores e filtro paso-baixo** · 25 min
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

#### 1. Análise da cadea ADC e parámetros de dixitalización [Colectivo] · 0–15 min

- **Tarea:** Escoita tres exemplos de audio a distintas frecuencias de muestreo e profundidades de bits. Anota nunha táboa as diferenzas percibidas e responde: que parámetro afecta máis ao ruído de fondo? Que parámetro limita as frecuencias agudas?
- **Entregable:** Táboa comparativa cos tres exemplos e respostas ás preguntas.

#### 2. Configuración dunha sesión DAW e experimento con bitcrusher [Individual] · 15–35 min

- **Tarea:** Configura unha sesión a 48 kHz/24 bit. Insire un bitcrusher nunha pista e experimenta reducindo a resolución (bits) e a frecuencia de muestreo. Grava un fragmento de 10 segundos con cada axuste e describe o que escoitas.
- **Entregable:** Sesión DAW gardada con tres fragmentos (orixinal, 8 bit, 4 bit) e unha descrición escrita dos efectos.

#### 3. Deseño dun son elemental con osciladores e filtro paso-baixo [Individual] · 35–60 min

- **Tarea:** No sintetizador software, escolle un oscilador (proba os catro) e deseña un son elemental usando un filtro paso-baixo. Axusta a frecuencia de corte e a resonancia. Garda o preset e describe o timbre resultante e a súa relación co contido harmónico do oscilador.
- **Entregable:** Preset gardado e ficha descritiva co oscilador usado, axustes de filtro e descrición do timbre.

## Material necesario

- Ordenadores con DAW (Reaper, Logic, Ableton, etc.) e sintetizador software (Serum, Vital, etc.).
- Plugin bitcrusher (pode ser o incluído no DAW ou un gratuito).
- Proxector e sistema de son do aula.
- Ficheiros de audio de exemplo a distintas frecuencias de muestreo e bits.
- Fichas de traballo impresas ou dixitais para as actividades.

## Fuentes de consulta

- Fuente de evaluación: ntam-sintesis-audio-digital — Musicología Académica
- Fuente de evaluación: polifonia-siglo-xv — Musicología Académica
- Fuente de evaluación: teoria-griega-seikilos — Musicología Académica
