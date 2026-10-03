# Piloto web de Arkhé en DigitalOcean

Antes llamado Enjambre. Esta guía prepara **una sola cuenta y un espacio nuevo vacío**.
No se copia la biblioteca del Mac ni se publica su servidor local. El alta masiva no está implementada.

## Diseño y límites del piloto

Navegador → HTTPS/Caddy → Arkhé → SQLite y archivos privados. Arkhé consulta Ollama/bge-m3
para embeddings y Mistral para generación. Solo Caddy publica puertos. Los servicios internos
no aceptan conexiones públicas; Arkhé exige el dominio y la IP de Caddy configurados.

| Elemento | Ubicación |
|---|---|
| Programa | `/opt/arkhe`, sin documentos ni claves |
| Espacio de trabajo | Volumen Docker `arkhe_data`, montado en `/datos/docente` |
| Modelos bge-m3 | Volumen distinto `ollama_models` |
| Hash de acceso | `/etc/arkhe/auth/user.json`, fuera del volumen docente |
| Clave de Mistral | `/etc/arkhe/.env`, permiso 0600; variable de entorno del contenedor |
| Copias diarias | `/var/backups/arkhe`, permiso 0700, catorce días |
| Certificados | Volúmenes de Caddy |

Una cuenta por instancia, un proceso y sesiones en memoria; un reinicio cierra las sesiones.
No hay recuperación de contraseña por correo, registro público ni balanceo entre réplicas.
Este despliegue no instala OCR. La imagen no incorpora herramientas OCR opcionales del Mac.

**Residencia:** elegir Frankfurt o Ámsterdam para documentos y embeddings. Se utiliza
`https://api.eu.mistral.ai/v1`; la documentación de Mistral describe centros en **UE y AELC**.
Para exigir UE estricta, confirmar las condiciones y localizaciones contractuales antes de
usar el piloto. No atribuirle retención cero ni exclusión de entrenamiento sin verificar el
plan contratado. El responsable debe validar el aviso de privacidad y los acuerdos aplicables.
[Región de Mistral](https://docs.mistral.ai/inference/regional-inference),
[retención cero](https://docs.mistral.ai/admin/monitor-comply/zero-data-retention).

## 1. Preparar clave SSH, dominio y droplet

En el Mac, crear una clave dedicada si no tienes una (elige una frase de paso):

```sh
ssh-keygen -t ed25519 -f ~/.ssh/arkhe_piloto -C arkhe-piloto
cat ~/.ssh/arkhe_piloto.pub
```

Subir **solo la clave pública** a DigitalOcean. Crear un droplet Ubuntu 24.04 LTS en Frankfurt
(FRA1) o Ámsterdam (AMS3), CPU x86_64, inicialmente 4 vCPU/8 GB RAM y al menos 50 GB de disco.
Es un punto de partida que hay que medir con el corpus del piloto, no una capacidad garantizada.
No se necesita GPU: Ollama solo ejecuta embeddings y la generación es remota.
Seleccionar acceso SSH con clave, sin contraseña. Anotar su IPv4 como `IP_DEL_DROPLET`.
[Crear droplet](https://docs.digitalocean.com/products/droplets/how-to/create/).

Crear en el proveedor DNS un registro A: `arkhe.tudominio.es` → IPv4 del droplet.
No añadir AAAA salvo que configures también IPv6 y su firewall. Usar DNS directo, sin otro
proxy/CDN en este piloto: Caddy es el único proxy de confianza.

Crear un **Cloud Firewall de DigitalOcean** y asignarlo al droplet:

- TCP 22 solo desde la IP pública de tu conexión de administración; actualizarla si cambia.
- TCP 80 y 443 desde Internet (para HTTPS y renovación automática).
- Salida DNS/HTTP/HTTPS habilitada; no abrir 8765 ni 11434.

SSH 22 se autentica exclusivamente por clave. Tener la consola de recuperación de DigitalOcean
como alternativa si cambia tu IP. Docker puede saltarse reglas de UFW para puertos publicados;
por eso el firewall cloud es la frontera principal.
[Docker y firewall](https://docs.docker.com/engine/network/packet-filtering-firewalls/).

Conectar desde el Mac:

```sh
ssh -i ~/.ssh/arkhe_piloto root@IP_DEL_DROPLET
```

## 2. Preparar un administrador y Ubuntu

Los siguientes comandos se ejecutan **en el droplet**. Crear `administrador`, asignarle una
contraseña para sudo y copiar la clave SSH pública ya instalada. Esa contraseña no habilita SSH
por contraseña:

```sh
adduser administrador
usermod -aG sudo administrador
install -d -m 700 -o administrador -g administrador /home/administrador/.ssh
install -m 600 -o administrador -g administrador /root/.ssh/authorized_keys /home/administrador/.ssh/authorized_keys
```

Abrir otra terminal del Mac y comprobar acceso y sudo **antes de cerrar la sesión root**:

```sh
ssh -i ~/.ssh/arkhe_piloto administrador@IP_DEL_DROPLET
sudo -v
```

En esa sesión administrativa configurar acceso por clave:

```sh
printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\n' | sudo tee /etc/ssh/sshd_config.d/00-arkhe.conf >/dev/null
sudo sshd -t
sudo systemctl reload ssh
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl
sudo timedatectl set-timezone UTC
```

Volver a probar una conexión nueva. No cerrar la sesión de recuperación hasta confirmar que
funciona. No agregar el administrador al grupo `docker`: equivale a acceso root; usar `sudo`.
[Configuración inicial](https://docs.digitalocean.com/products/droplets/getting-started/recommended-droplet-setup/).

## 3. Instalar Docker desde su repositorio oficial

En Ubuntu 24.04:

```sh
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<'DOCKER'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

No hace falta instalar Python ni uv en el droplet: están dentro de la imagen.
[Instalación oficial de Docker en Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

## 4. Transferir solo el código versionado

En el Mac, desde la carpeta del proyecto y con los cambios ya comprometidos:

```sh
git archive --format=tar HEAD | gzip > /tmp/arkhe-piloto.tar.gz
scp -i ~/.ssh/arkhe_piloto /tmp/arkhe-piloto.tar.gz administrador@IP_DEL_DROPLET:/tmp/
```

`git archive` excluye archivos ignorados: no usar una copia completa del directorio del Mac.
En el droplet, elegir un identificador de versión único; aquí se usa `piloto-001`:

```sh
sudo install -d /opt/arkhe-releases/piloto-001
sudo tar -xzf /tmp/arkhe-piloto.tar.gz -C /opt/arkhe-releases/piloto-001
sudo ln -s /opt/arkhe-releases/piloto-001 /opt/arkhe
sudo chown -R root:root /opt/arkhe-releases/piloto-001
cd /opt/arkhe
```

Conservar la correspondencia entre `piloto-001` y el commit enviado (`git rev-parse HEAD` en el
Mac). Los directorios de versiones permiten volver al programa anterior sin mover los datos.

## 5. Configurar claves y crear tu acceso

```sh
sudo install -d -m 700 /etc/arkhe
sudo install -d -m 700 -o 10001 -g 10001 /etc/arkhe/auth
sudo install -m 600 deploy/env.example /etc/arkhe/.env
sudo nano /etc/arkhe/.env
```

Completar dominio real, responsable, correo de borrado, región efectiva, nombre de instancia y
`DOCENTE_AI_MISTRAL_API_KEY`. Usar `ARKHE_IMAGE=arkhe:piloto-001`. No introducir la clave con un
comando `echo`, como build argument, en Git, en YAML o desde Ajustes. No ejecutar `compose config`
sin `--quiet`: podría imprimir variables secretas. El archivo `.env` pertenece a root y no se
monta dentro del espacio docente; Docker lo inyecta como entorno y los administradores del host
pueden verlo. Nunca dar acceso al daemon Docker a usuarios no administradores.

```sh
sudo docker compose --env-file /etc/arkhe/.env config --quiet
sudo docker compose --env-file /etc/arkhe/.env build arkhe
sudo docker compose --env-file /etc/arkhe/.env run --rm --no-deps --volume /etc/arkhe/auth:/run/arkhe-auth:rw arkhe server-user --auth-file /run/arkhe-auth/user.json --username docente
```

Escribir dos veces una contraseña única de al menos doce caracteres; no aparece en argumentos
ni logs. El archivo contiene un hash scrypt, no la contraseña. No se sobrescribe una cuenta
existente. Para cambiarla: detener Arkhé, retirar el hash anterior en el host protegido y repetir
el comando; arrancar revoca todas las sesiones. No hay botón de alta de otros profesores.

## 6. Primer arranque y descarga de bge-m3

```sh
sudo docker compose --env-file /etc/arkhe/.env up -d ollama
sudo docker compose --env-file /etc/arkhe/.env exec ollama ollama pull bge-m3
sudo docker compose --env-file /etc/arkhe/.env exec ollama ollama list
sudo docker compose --env-file /etc/arkhe/.env up -d
sudo docker compose --env-file /etc/arkhe/.env ps
```

Debe aparecer **solo bge-m3**. No descargar modelos generativos en este servicio. Ollama no está
publicado en el host y solo escucha en su IP interna. No usar `down --volumes`: eliminaría datos.
El primer arranque crea una base y biblioteca vacías, Mistral UE para generación y bge-m3 para
embeddings; no importa configuraciones ni documentos personales del Mac.

Caddy necesita DNS resuelto hacia el droplet y puertos 80/443 abiertos para emitir el certificado.
[HTTPS con Caddy](https://caddyserver.com/docs/quick-starts/reverse-proxy).

## 7. Comprobar HTTPS y el espacio vacío

En un navegador, abrir `https://arkhe.tudominio.es/privacy` antes de acceder. Verificar responsable,
correo y región. Después `/login`: contraseña incorrecta da rechazo; cinco intentos fallidos
bloquean esa IP durante quince minutos. No probar ese límite justo antes de una clase.

```sh
curl -I https://arkhe.tudominio.es/privacy
curl -I https://arkhe.tudominio.es/
```

Esperar HTTPS válido, aviso 200 y redirección de `/` al acceso. Tras entrar:

- Biblioteca sin fuentes, grupos ni materias. Crear tu materia y horario en Ajustes.
- No hay botones de Finder ni de cerrar el servidor. Subir documentos y descargar materiales.
- Generación Mistral y embeddings bge-m3; confirmar explícitamente el envío remoto antes de generar.
- No subir nombres, calificaciones, fotos ni datos identificativos del alumnado, tampoco al diario.
- Cerrar sesión impide acceder a la API; cookie Secure, HttpOnly y SameSite=Strict.
- En la consola de DigitalOcean, solo Caddy publica 80/443; ningún mapeo 8765/11434.

La prueba real de generación requiere tu clave y las condiciones regionales confirmadas. Las
pruebas del repositorio simulan proveedores: no certifican la conectividad del droplet ni Mistral.

## 8. Instalar la copia diaria

```sh
sudo install -d -m 700 -o 10001 -g 10001 /var/backups/arkhe
sudo install -m 644 deploy/arkhe-backup.service /etc/systemd/system/
sudo install -m 644 deploy/arkhe-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now arkhe-backup.timer
sudo systemctl start arkhe-backup.service
sudo systemctl list-timers arkhe-backup.timer
sudo ls -lh /var/backups/arkhe
```

Diaria a las 03:15 UTC con pequeño retraso aleatorio. Detiene Arkhé brevemente, ejecuta SQLite
`.backup`, copia originales/Conocimiento/configuración sin claves y vuelve a arrancar. Los
checksums verifican la copia; la rotación conserva catorce fechas. No incluye hashes ni `.env`,
que se recuperan por separado. Tras la copia tendrás que iniciar sesión de nuevo.

Una copia en el mismo droplet **no protege de su pérdida**. Antes de un piloto real, probar
restauración y acordar copia externa cifrada en almacenamiento UE, con igual retención. No
transferir claves o bibliotecas a servicios externos sin decidir previamente esa ubicación.

## 9. Logs, mantenimiento y actualización

```sh
cd /opt/arkhe
sudo docker compose --env-file /etc/arkhe/.env logs --tail 100 arkhe caddy
sudo journalctl -u arkhe-backup.service -n 50 --no-pager
sudo docker system df
```

Arkhé desactiva el access log de Uvicorn y enmascara patrones de claves en sus handlers. No
compartir dumps de entorno, `docker inspect`, archivos de configuración ni logs completos sin
revisarlos: pueden contener preguntas o información administrativa. No borrar volúmenes con
`prune --volumes`. Revisar parches del host y las versiones fijadas de imágenes periódicamente.

Para actualizar, comprobar suite y smoke en el Mac, enviar otro `git archive` y preparar un
nuevo directorio `/opt/arkhe-releases/piloto-002` como en el paso 4. En el servidor:

```sh
cd /opt/arkhe
sudo systemctl start arkhe-backup.service
sudo docker compose --env-file /etc/arkhe/.env stop arkhe
sudo ln -sfn /opt/arkhe-releases/piloto-002 /opt/arkhe
cd /opt/arkhe
sudo nano /etc/arkhe/.env
# Cambiar solo ARKHE_IMAGE a arkhe:piloto-002 y conservar el resto.
sudo docker compose --env-file /etc/arkhe/.env build arkhe
sudo docker compose --env-file /etc/arkhe/.env up -d
```

Mantener el mismo `ARKHE_INSTANCE` para conservar volúmenes y certificados. Comprobar acceso,
subida, consulta, descarga y copia. Rehacer la imagen recrea el proceso y revoca sesiones. Para
rotar la clave, editar `.env` y ejecutar `up -d --force-recreate arkhe`.
No usar actualizadores automáticos de imágenes en el piloto: revisar cada versión.

## 10. Restaurar sin sobrescribir el volumen activo

Elegir una copia concreta, por ejemplo `/var/backups/arkhe/arkhe-2026-10-03.tar.gz`, y un nombre
Docker **nuevo**. Usar la imagen correspondiente a esa copia para evitar incompatibilidades:

```sh
cd /opt/arkhe
sudo env ARKHE_RESTORE_IMAGE=arkhe:piloto-001 sh scripts/pilot-restore.sh /var/backups/arkhe/arkhe-2026-10-03.tar.gz arkhe-restaurado-20261003
```

El script rechaza volúmenes existentes y verifica rutas, checksums y SQLite. No cambia el servicio
activo. Si pasa, crear un override **fuera del repositorio**:

```sh
sudo tee /etc/arkhe/restauracion.yml >/dev/null <<'RESTORE'
volumes:
  arkhe_data:
    external: true
    name: arkhe-restaurado-20261003
RESTORE
sudo docker compose --env-file /etc/arkhe/.env stop arkhe
sudo nano /etc/arkhe/.env
# Añadir COMPOSE_FILE=/opt/arkhe/docker-compose.yml:/etc/arkhe/restauracion.yml
sudo docker compose --env-file /etc/arkhe/.env config --quiet
sudo docker compose --env-file /etc/arkhe/.env up -d arkhe
```

Compose lee `COMPOSE_FILE` del mismo archivo de entorno: todas las operaciones, incluido el
timer de copia, usarán el override. No quitar esa variable en una actualización. Verificar el
volumen con `docker volume ls` y conservar el anterior hasta comprobar biblioteca, citas y diario.
El montaje sigue siendo `/datos/docente`, así no cambian los localizadores almacenados.

Reaplicar el hash/clave externos si se pierde el host. Una vuelta atrás tras una migración de
base requiere restaurar la copia anterior y la imagen correspondiente, no solo cambiar el código.
Comprobar estos pasos con un corpus sintético antes de recuperar documentos reales.

## 11. Borrado y fase 2: una instancia por profesor

Recibir solicitudes en el contacto de `/privacy`, verificar identidad, detener la instancia y
borrar su volumen y cuenta. Purgar o dejar caducar sus copias (máximo catorce días según el aviso)
y evitar reintroducir datos borrados al restaurar. No ejecutar comandos destructivos de borrado
sobre volúmenes hasta identificar exactamente la instancia y la solicitud.

La fase 2 conserva este diseño, **sin implementar registro ni alta masiva**:

- Un dominio, proceso Arkhé, usuario scrypt, clave y volumen privado por profesor.
- Redes privadas distintas con subred/IP propias; ningún volumen docente compartido.
- Un Caddy frontal único en un droplet compartido, conectado a cada red y con una ruta por
  dominio. No lanzar varias copias de este Compose con todos los Caddy publicando 80/443.
- Ollama/modelos por instancia para el aislamiento inicial; compartir embeddings requeriría
  una decisión posterior sobre recursos, límites y aislamiento.
- Copia, restauración, límites de recursos y borrado por instancia; sin selector de profesores
  dentro de una base compartida. Credenciales administrativas fuera de todos los espacios.
- Alternativa inicial más simple: un droplet por profesor con este mismo Compose. La provisión
  manual y su coste se revisan antes de automatizarla.

Antes de ampliar: medir tiempos/memoria con 20, 100 y 1.000 fuentes sintéticas; ensayar restauración,
comprobar aislamiento entre dos cuentas y acordar residencia estricta, soporte y retención.
