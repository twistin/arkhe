---
titulo: "NTAM: Audio digital, teorema de Nyquist-Shannon y síntesis sustractiva"
tema: "Nuevas Tecnologías Aplicadas a la Música (NTAM)"
periodo: "ntam"
palabras_clave:
  - "ntam"
  - "audio digital"
  - "nyquist"
  - "shannon"
  - "muestreo"
  - "cuantizacion"
  - "aliasing"
  - "sintesis sustractiva"
  - "filtro"
  - "adsr"
tipo: "esquema"
origen: "notas_profesor"
fuente_bibliografica: "Curtis Roads (1996). The Computer Music Tutorial; Ken C. Pohlmann (2010). Principles of Digital Audio"
fecha_verificacion: "2026-10-08"
audiciones_recomendadas: []
---

# Nuevas Tecnologías Aplicadas a la Música (NTAM)

## 1. Cadena de digitalización de audio (Conversión A/D)
| Etapa | Parámetro técnico | Función y fenómeno físico | Estándares habituales |
| --- | --- | --- | --- |
| **Muestreo (Sampling)** | Frecuencia de muestreo ($f_s$) | Tomas temporales por segundo. Límite Nyquist: $f_s \ge 2 \cdot f_{max}$ para evitar aliasing. | 44.1 kHz (CD), 48 kHz (vídeo/pro), 96 kHz (alta resolución). |
| **Filtro Antialiasing** | Pasa-bajos previo | Corta frecuencias por encima de $f_s/2$ para evitar repliegue espectral inarmónico. | Pendiente pronunciada antes de 22.05 kHz / 24 kHz. |
| **Cuantización** | Profundidad de bits (bit depth) | Discretización de amplitud. Relación señal/ruido: $\approx 6\text{ dB}$ por bit. | 16 bits ($\approx 96\text{ dB}$), 24 bits ($\approx 144\text{ dB}$), 32-bit float. |
| **Dither** | Ruido de baja amplitud añadido | Elimina la distorsión de cuantización correlacionada convirtiéndola en ruido blanco analógico inocuo. | TPDF (Triangular Probability Density Function). |

## 2. Síntesis sustractiva de sonido
*De la riqueza armónica al timbre esculpido.*

### Componentes de la cadena sustractiva
1. **Generador / Oscilador (VCO / DCO):** Produce formas de onda periódicas ricas en armónicos:
   - *Senoidal:* Onda pura sin armónicos.
   - *Diente de sierra (Sawtooth):* Todos los armónicos enteros ($1, 2, 3, 4\dots$) con amplitud inversamente proporcional ($1/n$).
   - *Cuadrada / Pulso (Square/Pulse):* Solo armónicos impares ($1, 3, 5, 7\dots$). Ancho de pulso modulable (PWM).
   - *Triangular:* Armónicos impares con caída muy rápida de amplitud ($1/n^2$).
2. **Filtro (VCF / DCF):** Esculpe el espectro eliminando bandas de frecuencias (pasa-bajos, pasa-altos, pasa-banda, rechazo de banda).
   - *Frecuencia de corte ($f_c$):* Punto de atenuación a $-3\text{ dB}$.
   - *Resonancia ($Q$):* Enfatiza las frecuencias cercanas al punto de corte.
3. **Amplificador (VCA / DCA):** Modula el volumen final.
4. **Moduladores:**
   - *Generador de envolvente (ADSR):* Attack, Decay, Sustain, Release aplicados a amplitud o filtro.
   - *LFO (Low Frequency Oscillator):* Modulación cíclica subaudible ($<20\text{ Hz}$) para vibrato, trémolo o barrido de filtro.
