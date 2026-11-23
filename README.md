<p align="center">
  <img src="assets/brand/chaskidoo-lockup-light.svg" alt="chaskidoo" height="96">
</p>

# Chaskidoo

**Chaskidoo** lleva tus módulos de Odoo de desarrollo a stage y a producción, como los chaskis llevaban los mensajes
por el Qhapaq Ñan. Es el fork de Manexware de [rocketdoo](https://pypi.org/project/rocketdoo/) 3.14.1
(Horacio Montaño / HDMSoft, licencia **LGPL-3.0**), tomado del sdist publicado en PyPI. El original está documentado en
[README_ROCKETDOO.md](README_ROCKETDOO.md).

- Distribución: `chaskidoo`. Comandos: `chk` y `chaskidoo`; `rkd` y `rocketdoo` siguen funcionando como alias, así que
  los mensajes y la documentación que dicen `rkd …` valen tal cual.
- Paquete Python interno: `rocketdoo` (se conserva para poder sincronizar con upstream).
- Identidad: `assets/brand/` (icono, favicon, logotipo con nombre, PNG de 16 a 1024 px, `favicon.ico`) y
  `assets/brand/build_icons.py`, que los regenera. Paleta: índigo andino `#1D2E52`, marino `#14213D`, piedra `#F4E9D8`,
  terracota `#D2603F`, ocre `#E8A33D`.

Cambia el **despliegue de instancias Docker** (stage y prod) para elegir **dónde corre PostgreSQL** y **qué proxy inverso** se usa:

| Opción | Valores | Qué hace |
|---|---|---|
| `db_mode` | `container` | Contenedor `postgres` dentro del compose (comportamiento original) |
| | `vps` | PostgreSQL **instalado en el VPS**, fuera de Docker. rkd lo instala, crea el rol y abre el acceso a los contenedores |
| | `external` | Otro servidor o servicio gestionado (RDS, Cloud SQL, servidor de BD). rkd no lo administra |
| `proxy` | `nginx` | Nginx en el host + certbot. Odoo publicado en `127.0.0.1` (8069/8072 prod, 8169/8172 stage) |
| | `traefik` | Contenedor Traefik con labels y Let's Encrypt (comportamiento original) |

El entorno local de desarrollo (`rkd up`) **no cambia**: siempre tiene su contenedor de PostgreSQL.

## Dónde se pregunta

1. **`rkd init`** — al crear el proyecto pregunta:
   - *¿PostgreSQL en Docker o en el VPS?* (Docker / VPS / externo)
   - *¿Traefik o Nginx como proxy inverso?*

   Guarda las respuestas en `.rkd/instance_defaults.yaml`. Sin preguntas: `rkd init --profile odoo19-ee --db-mode vps --proxy nginx`.
2. **`rkd instance init`** — propone esas respuestas por defecto. El proxy se elige una vez para todos los entornos
   (stage y prod suelen compartir VPS y los dos proxies no pueden usar 80/443 a la vez). PostgreSQL se elige por entorno.
   Lo que vale al desplegar es `.rkd/instance.yaml`.

## Instalación

```bash
pip install git+ssh://git@github.com/<org>/chaskidoo.git
# o, desde el clon:
pip install -e .
```

## macOS

Chaskidoo corre en macOS (Intel y Apple Silicon M1–M4) además de Linux y WSL2. Los VPS siguen siendo Linux.

**Requisitos en el Mac**

| Herramienta | Cómo | Para qué |
|---|---|---|
| Python ≥ 3.10 | `brew install python@3.12` (el `python3` de Apple es 3.9) | rkd |
| Docker | Docker Desktop, OrbStack o Colima | entorno local |
| rsync, ssh, ssh-agent | vienen con macOS | despliegue |
| sshpass (opcional) | `brew install sshpass` | solo si el VPS usa contraseña en vez de llave |

Instalación recomendada, aislada del Python del sistema:

```bash
brew install pipx && pipx ensurepath
pipx install git+ssh://git@github.com/<org>/chaskidoo.git
```

**Qué hace distinto en Mac**

- **Apple Silicon + Odoo 15–17**: la imagen oficial `odoo` solo publica builds arm64 desde la 18. `rkd init` lo detecta
  y agrega `platform: linux/amd64` al servicio `web` del compose local, que corre emulado. Activar
  *Settings → General → Use Rosetta for x86_64/amd64 emulation* en Docker Desktop lo hace mucho más rápido.
  Odoo 18, 19 y 20 corren nativos en arm64. En Linux y en Mac Intel el compose queda igual que antes.
- **Archivos del Finder**: el despliegue excluye `.DS_Store`, `._*`, `__pycache__/` y `*.pyc` al subir addons y Enterprise.
- **Mensajes de instalación**: sugieren `brew install …` en vez de `apt`.
- **Dominios locales** (`rkd traefik`): en Mac el dominio propuesto termina en `.test` (`.local` es Bonjour y resuelve
  lento) y la guía incluye `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` después de editar `/etc/hosts`.
- Las opciones de rsync usadas (`-avz --delete --exclude`) funcionan con el rsync de macOS (2.6.9 y openrsync).

La integración continua (`.github/workflows/tests.yml`) ejecuta las pruebas y un `rkd init` real en
`macos-latest` (Apple Silicon) y `ubuntu-latest`, con Python 3.10 y 3.12.

## Ejemplo de `.rkd/instance.yaml`

```yaml
environments:
  stage:
    type: docker
    vps: {host: 203.0.113.10, user: ubuntu, auth_method: ssh_key, ssh_key: ~/.ssh/id_ed25519}
    odoo_version: "19.0"
    domain: stage.cliente.com
    letsencrypt_email: soporte@manexware.com   # traefik_email también se acepta
    proxy: nginx
    db_mode: vps            # PostgreSQL en el mismo VPS
    db_version: "16"        # versión a instalar en el VPS
    host_http_port: 8169
    host_gevent_port: 8172
  prod:
    type: docker
    vps: {host: 203.0.113.20, user: ubuntu, auth_method: ssh_key, ssh_key: ~/.ssh/id_ed25519}
    odoo_version: "19.0"
    domain: erp.cliente.com
    letsencrypt_email: soporte@manexware.com
    proxy: nginx
    db_mode: external
    db_host: pg.cliente.com
    db_port: 5432
    db_sslmode: require
    db_version: "16"
    db_max_connections: 200
```

Un `instance.yaml` del rocketdoo original (sin `proxy` ni `db_mode`) sigue funcionando igual: `container` + `traefik`.

## PostgreSQL en el VPS (`db_mode: vps`)

En cada despliegue (paso 5) rkd ejecuta en el VPS, con `sudo`, un script idempotente que:

1. instala PostgreSQL si no hay ninguno (la versión de `db_version`; si la distribución no la trae, habilita apt.postgresql.org);
2. escucha en `localhost` y en la IP del bridge de Docker (`172.17.0.1`), que es a donde apunta `host.docker.internal`;
3. agrega a `pg_hba.conf` el acceso del rol desde las redes de Docker (`172.16.0.0/12`, scram-sha-256);
4. si UFW está activo, abre el puerto solo para esas redes;
5. hace que `postgresql` arranque después de `docker.service` (para que la IP del bridge exista);
6. crea el rol con `LOGIN CREATEDB` o realinea su contraseña.

La contraseña se genera la primera vez y se guarda en `.rkd/secrets/instance_<env>_db.env` (ignorado por git).
Requisitos: Debian/Ubuntu, root o `sudo` sin contraseña. Stage y prod en el mismo VPS comparten el cluster, cada uno con su rol.

## PostgreSQL externo (`db_mode: external`)

- El **rol** debe existir; necesita `CREATEDB` **o** que la base ya exista con `OWNER <rol>`.
- `pg_hba.conf` del servidor debe permitir la IP del VPS.
- La contraseña **no** va en `instance.yaml`: el asistente la guarda en `.rkd/secrets/`, o se pasa con
  `INSTANCE_PROD_DB_PASSWORD` / `INSTANCE_STAGE_DB_PASSWORD`. Nunca se genera una aleatoria.

## Flujo de despliegue

```bash
rkd init                                # proyecto local + elecciones de despliegue
rkd instance init                       # stage/prod
rkd instance deploy --env stage --dry-run
rkd instance deploy --env stage
rkd instance nginx   --env stage        # si proxy: nginx
rkd instance traefik --env stage        # si proxy: traefik
```

Cada comando de proxy rechaza un entorno configurado con el otro proxy y dice cuál usar.

`rkd instance nginx` crea `/etc/nginx/sites-available/rkd-<proyecto>_<env>.conf`, valida con `nginx -t`, recarga y ejecuta
`certbot --nginx --redirect`. Si el DNS todavía no apunta al VPS queda en HTTP; repetir cuando esté listo. Opciones:
`--force`, `--no-certbot`, `--email`. Si los puertos 80/443 están ocupados (p. ej. un Traefik anterior) no toca nada.

## Cómo funciona por dentro

- `templates/instance/docker-compose.jinja`: ramas por `proxy` (ports en 127.0.0.1 o expose + labels + red `traefik-public`)
  y por `db_mode` (servicio `db` o `extra_hosts: host.docker.internal` + secreto `pgpass`).
- Con PostgreSQL fuera del compose, `psql`/`createdb`/`pg_restore`/`pg_isready` corren en contenedores efímeros de la imagen
  de Odoo (`docker compose run --rm --no-deps -l traefik.enable=false --user root --entrypoint <tool> web`).
- `odoo.conf`: `db_host`, `db_port`, `db_sslmode` y `dbfilter = ^<db_name>$`.
- Pre-flight: revisa el proxy configurado, sudo para `db_mode: vps` (bloqueante) y conectividad TCP a un PostgreSQL externo.

Archivos nuevos: `core/host_platform.py`, `core/instance/{defaults,external_db,vps_postgres,proxy_traefik}.py`,
`.github/workflows/tests.yml`. Modificados: `cli.py`,
`init_project.py`, `instance_cli.py`, `core/models/instance.py`, `core/instance/{config_manager,deployer_docker,db_seed,preflight,proxy}.py`,
`gui/api/instances.py`, `templates/instance/{docker-compose,odoo.conf}.jinja`.

## Verificado

- `tests/test_manex_fork.py` (44 pruebas, incluidas las de macOS con plataforma simulada): las 6 combinaciones `db_mode` × `proxy` pasan `docker compose config`; sitios
  Nginx de stage y prod juntos pasan `nginx -t`; todos los scripts generados pasan `bash -n`; `rkd init --profile` con opciones.
- El script de PostgreSQL en el VPS se ejecutó de verdad en Ubuntu 24.04 (PostgreSQL 16): conexión del rol por la IP del bridge,
  rechazo de contraseña incorrecta, segunda ejecución sin reinicio ni líneas duplicadas.
- Asistentes `rkd init` y `rkd instance init` recorridos de forma interactiva.

## Pendiente / limitaciones

- No se probó contra un VPS real con Docker en marcha (el sandbox no tiene daemon de Docker).
- macOS se verificó simulando la plataforma; la verificación en un Mac real es el CI de GitHub Actions al subir el repo.
- El formulario web (`rkd gui`) no muestra aún `proxy`/`db_mode`; usa los valores de `rkd init` para entornos nuevos y
  conserva los del archivo.
- El despliegue **nativo** (`type: native`) no cambia.
- Los tests originales del sdist no traen `conftest.py` ni snapshots, así que no se pueden ejecutar tal cual.

## Sincronizar con upstream

El commit base está etiquetado `upstream-3.14.1`. Para una versión nueva: descargar el sdist
(`pip download rocketdoo==X --no-binary :all: --no-deps`), crear una rama desde `upstream-3.14.1`, reemplazar el código,
commitear, etiquetar `upstream-X` y hacer `git rebase` de `main` sobre ella.

## Licencia

LGPL-3.0, igual que el original (ver `LICENSE`). Se conserva el aviso de copyright de Horacio Montaño y las modificaciones
quedan documentadas aquí y en el historial de git.
