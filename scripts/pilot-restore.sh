#!/bin/sh
# Restaurar en un volumen NUEVO; no sobrescribir el espacio activo.
set -eu
if [ "$#" -ne 2 ]; then echo 'Uso: pilot-restore.sh /var/backups/arkhe/copia.tar.gz volumen-nuevo' >&2; exit 1; fi
archive=$(realpath "$1")
volume=$2
if docker volume inspect "$volume" >/dev/null 2>&1; then echo 'El volumen ya existe; elige otro nombre.' >&2; exit 1; fi
cd /opt/arkhe
image=${ARKHE_RESTORE_IMAGE:-arkhe:piloto}
docker volume create "$volume" >/dev/null
docker run --rm --user 0 --entrypoint chown --volume "$volume:/restaurado" "$image" 10001:10001 /restaurado
docker run --rm --entrypoint python --volume "$volume:/restaurado" \
  --mount "type=bind,src=$archive,dst=/copia.tar.gz,readonly" "$image" \
  -m docente_ai.web.backup restore --workspace /restaurado --archive /copia.tar.gz --volume-root
echo "Copia verificada en el volumen $volume. Cambia el volumen de Compose con el servicio detenido."
