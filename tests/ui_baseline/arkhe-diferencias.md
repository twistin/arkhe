# Arkhé: revisión de las doce referencias visuales

Comparación antes/después del cambio de marca con Chromium 153.0.8010.12, escritorio 1440×1000 y móvil 390×844, datos sintéticos. Las dimensiones completas de cada vista permanecen iguales. La distribución del contenido fuera de las zonas de marca permanece igual.

| Perfil | Vista | Píxeles distintos | Porcentaje | Píxeles fuera de marca | Delta fuera de marca | Zonas autorizadas |
|---|---|---:|---:|---:|---:|---|
| escritorio | biblioteca | 3981 | 0.270507 | 0 | 0 | marca y logo, pie |
| escritorio | asistente | 3981 | 0.256217 | 0 | 0 | marca y logo, pie |
| escritorio | propuestas | 3981 | 0.270507 | 0 | 0 | marca y logo, pie |
| escritorio | diario | 3981 | 0.270507 | 0 | 0 | marca y logo, pie |
| escritorio | ajustes | 4370 | 0.156027 | 0 | 0 | marca y logo, pie, Cerrar Arkhé |
| escritorio | impresion | 3659 | 0.033893 | 0 | 0 | pastilla de marca |
| movil | biblioteca | 3981 | 0.516061 | 0 | 0 | marca y logo, pie |
| movil | asistente | 3985 | 0.586564 | 4 | 1 | marca y logo, pie |
| movil | propuestas | 3981 | 0.66848 | 0 | 0 | marca y logo, pie |
| movil | diario | 3981 | 0.581304 | 0 | 0 | marca y logo, pie |
| movil | ajustes | 4370 | 0.400756 | 0 | 0 | marca y logo, pie, Cerrar Arkhé |
| movil | impresion | 1995 | 0.023039 | 0 | 0 | pastilla de marca |

El libro y el arco sustituyen a los hexágonos del logo. «Arkhé» sustituye a «enjambre» en la marca; «ARKHÉ» sustituye a «ENJAMBRE» en el pie y el material del alumnado. Ajustes cambia «Cerrar Enjambre» por «Cerrar Arkhé». El acortamiento del nombre desplaza el texto contiguo dentro del propio pie/pastilla, sin alterar su posición o altura.

Fuera de esas regiones, escritorio coincide exactamente. En móvil únicamente permanecen 4 píxeles en Asistente, con un nivel de variación por canal: las mismas diferencias de rasterización ya aceptadas antes del cambio, dentro de la tolerancia por defecto (≤0,01 % y ≤2 niveles).

Las doce capturas se revisaron antes de reemplazar las referencias. Las pruebas funcionales del smoke no registran errores de consola, excepciones JavaScript ni solicitudes externas. Los títulos de ventanas, impresión, mensajes y nombres internos de familias tipográficas también se revisaron en código; no alteran el cuerpo de las vistas.
