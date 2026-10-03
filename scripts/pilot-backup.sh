#!/bin/sh
# Ejecutar desde el timer del host; no copiar bases ni archivos mientras hay escritores.
set -eu
umask 077
cd /opt/arkhe
compose() { docker compose --env-file /etc/arkhe/.env "$@"; }
# El bloqueo evita dos copias simultáneas. El directorio pertenece al administrador.
exec 9>/var/lock/arkhe-backup.lock
flock -n 9
trap 'compose start arkhe' EXIT
compose stop --timeout 60 arkhe
compose run --rm --no-deps --entrypoint python \
  --volume /var/backups/arkhe:/copias:rw arkhe -m docente_ai.web.backup create \
  --workspace /datos/docente --backup-dir /copias
