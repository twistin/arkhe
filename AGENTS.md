# Reglas permanentes para agentes

- El idioma del código, los comentarios, los mensajes y la documentación es el castellano, como en el resto del proyecto.
- Antes de terminar cualquier tarea, ejecutar `uv run --locked pytest` y comprobar que pasa la suite completa. Los tests no pueden hacer red real: respetar el bloqueo existente en `tests/conftest.py`.
- No añadir dependencias sin justificarlo en el resumen final. Si se añaden, actualizar `uv.lock` mediante `uv lock`.
- Nunca leer, imprimir ni mover datos de `data/`, `Conocimiento/` ni configuraciones reales de `config/*.yaml`. Utilizar únicamente `config/*.example.yaml` y fixtures temporales.
- No romper el contrato de citas verificadas: las referencias `quote_XXX` deben resolverse a subcadenas exactas. Mantener la separación entre fuentes documentales, material del profesor y texto generado por IA.
- Actualizar `README.md` y `ARCHITECTURE.md` cuando cambie el comportamiento visible de la aplicación.
