# rocketdoo-manex — fork de Manexware

Fork de [rocketdoo](https://pypi.org/project/rocketdoo/) 3.14.1 (Horacio Montaño / HDMSoft, licencia **LGPL-3.0**),
tomado del sdist publicado en PyPI. Mantiene el comando `rkd` y el paquete `rocketdoo`; la distribución se llama `rocketdoo-manex`.

Cambia **solo el despliegue de instancias Docker** (`rkd instance ...`, stage y prod):

| | rocketdoo 3.14.1 | rocketdoo-manex |
|---|---|---|
| PostgreSQL | contenedor `db` dentro del compose | **servidor externo** (`db_mode: external`, por defecto); el contenedor sigue disponible con `db_mode: container` |
| Proxy inverso | Traefik en contenedor, red `traefik-public`, labels | **Nginx en el host** + certbot (Let's Encrypt) |
| Publicación de Odoo | `expose` hacia Traefik | `ports` en `127.0.0.1` (8069/8072 prod, 8169/8172 stage) |
| Comando del proxy | `rkd instance traefik --env X` | `rkd instance nginx --env X` |

El entorno local de desarrollo (`rkd init`, `rkd up`, `rkd traefik` local) **no cambia**: sigue usando su contenedor de PostgreSQL.

## Instalación

```bash
pip install git+ssh://git@github.com/<org>/rocketdoo-manex.git
# o, desde el clon:
pip install -e .
```

## Configuración (`.rkd/instance.yaml`)

```yaml
environments:
  prod:
    type: docker
    vps: {host: 203.0.113.10, user: ubuntu, auth_method: ssh_key, ssh_key: ~/.ssh/id_ed25519}
    odoo_version: "19.0"
    domain: erp.cliente.com
    letsencrypt_email: soporte@manexware.com   # traefik_email también se acepta
    db_mode: external          # external | container
    db_host: pg.cliente.com    # o host.docker.internal si PostgreSQL está en el mismo VPS
    db_port: 5432
    db_sslmode: require        # disable | allow | prefer | require | verify-ca | verify-full
    db_version: "16"           # versión del servidor externo (para validar seeds)
    db_max_connections: 200    # max_connections del servidor, para calcular db_maxconn
    db_user: odoo_prod
    db_name: cliente_prod
    # host_http_port / host_gevent_port: opcionales (por defecto 8069/8072 prod, 8169/8172 stage)
```

`rkd instance init` pregunta todo esto. **La contraseña del rol no va en `instance.yaml`**: el asistente la guarda en
`.rkd/secrets/instance_<env>_db.env` (0600, ignorado por git), o se puede pasar en el despliegue con
`INSTANCE_PROD_DB_PASSWORD` / `INSTANCE_STAGE_DB_PASSWORD`. Nunca se genera una contraseña aleatoria para un servidor externo.

### Requisitos del PostgreSQL externo

- El **rol** debe existir (`CREATE ROLE odoo_prod LOGIN PASSWORD '...'`).
- Necesita `CREATEDB` **o** que la base ya exista con `OWNER odoo_prod`.
- `pg_hba.conf` debe permitir la IP del VPS (o las redes de Docker, ej. `172.16.0.0/12`, si usas `host.docker.internal`).
- Para restaurar un seed, el servidor no puede ser de una versión mayor anterior a la del dump local.

## Flujo de despliegue

```bash
rkd instance init                      # configura stage/prod
rkd instance deploy --env stage --dry-run
rkd instance deploy --env stage        # build, BD, arranque, verificación
rkd instance nginx  --env stage        # instala nginx+certbot, crea el sitio, pide el certificado
```

`rkd instance nginx` necesita root o `sudo` sin contraseña en el VPS (solo Debian/Ubuntu para la instalación
automática). Crea `/etc/nginx/sites-available/rkd-<proyecto>_<env>.conf`, lo valida con `nginx -t`, recarga y ejecuta
`certbot --nginx --redirect`. Si el DNS todavía no apunta al VPS, el sitio queda en HTTP; vuelve a ejecutar el comando
cuando el DNS esté listo. Opciones: `--force` (reescribe el sitio), `--no-certbot`, `--email`.

Si el VPS tenía el Traefik de rocketdoo, el comando se detiene porque los puertos 80/443 están ocupados:
`docker rm -f traefik` y repetir.

## Cómo funciona por dentro

- `templates/instance/docker-compose.jinja`: sin servicio `db` en modo externo; Odoo publica `127.0.0.1:<puertos>`;
  `extra_hosts: host.docker.internal:host-gateway`; secreto `pgpass` para los clientes de PostgreSQL.
- `psql`, `createdb`, `pg_restore`, `pg_isready` corren en contenedores efímeros de la imagen de Odoo
  (`docker compose run --rm --no-deps --user root --entrypoint <tool> web`) con `PGHOST/PGPORT/PGUSER/PGSSLMODE/PGPASSFILE`.
- `odoo.conf`: `db_host`, `db_port`, `db_sslmode` y `dbfilter = ^<db_name>$`.
- Pre-flight: verifica Nginx (instalado, activo, sitio con el dominio) y conectividad TCP del VPS al PostgreSQL externo.

Archivos tocados: `core/models/instance.py`, `core/instance/{deployer_docker,db_seed,preflight,proxy,config_manager}.py`,
`core/instance/external_db.py` (nuevo), `instance_cli.py`, `gui/api/instances.py`, `templates/instance/{docker-compose,odoo.conf}.jinja`.

## Pendiente / limitaciones conocidas

- El formulario web (`rkd gui`) no muestra aún los campos nuevos; los preserva si ya están en `instance.yaml`.
- El despliegue **nativo** (`type: native`) no cambia: sigue instalando PostgreSQL local y sin proxy.
- Los tests originales del sdist no incluyen `conftest.py` ni snapshots, así que no se pueden ejecutar tal cual;
  los del fork están en `tests/test_manex_fork.py` (`pytest tests/test_manex_fork.py`).

## Sincronizar con upstream

El commit base está etiquetado `upstream-3.14.1`. Para una versión nueva: descargar el sdist
(`pip download rocketdoo==X --no-binary :all: --no-deps`), crear una rama desde `upstream-3.14.1`, reemplazar el código,
commitear, etiquetar `upstream-X` y hacer `git rebase` de `main` sobre ella.

## Licencia

LGPL-3.0, igual que el original (ver `LICENSE`). Este fork conserva el aviso de copyright de Horacio Montaño y documenta
sus modificaciones en este archivo y en el historial de git, como pide la licencia.
