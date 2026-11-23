# PostgreSQL

Cada entorno elige dónde corre su base de datos con `db_mode`. Se pregunta en `chk init` (valor por defecto) y en
`chk instance init` (por entorno).

| `db_mode` | Dónde | Quién lo administra |
|---|---|---|
| `container` | Contenedor `postgres` dentro del compose del entorno | Chaskidoo |
| `vps` | Instalado en el mismo VPS, fuera de Docker | Chaskidoo lo instala y configura |
| `external` | Otro servidor o servicio gestionado | Tú o tu proveedor |

## En Docker (`container`)

El comportamiento original de Rocketdoo. Útil para stage o para instalaciones pequeñas.
El perfil de recursos (`pg_profile`: small, medium, large) ajusta `shared_buffers`, `work_mem` y conexiones.

## En el VPS (`vps`)

En cada despliegue, Chaskidoo ejecuta en el VPS (con `sudo`) un script que se puede repetir sin efectos:

1. Instala PostgreSQL si no existe, en la versión de `db_version`. Si la distribución no la tiene,
   habilita el repositorio oficial apt.postgresql.org.
2. Escucha en `localhost` y en la IP del bridge de Docker, a donde apunta `host.docker.internal` dentro de los contenedores.
3. Agrega en `pg_hba.conf` el acceso del rol desde las redes de Docker (`172.16.0.0/12`).
4. Si UFW está activo, abre el puerto solo para esas redes.
5. Hace que PostgreSQL arranque después de Docker.
6. Crea el rol con `LOGIN CREATEDB` o actualiza su contraseña.

La contraseña se genera en el primer despliegue y se guarda en `.rkd/secrets/instance_<env>_db.env`.
Stage y prod en el mismo VPS comparten el cluster, cada uno con su rol y su base.

## Externo (`external`)

```yaml
db_mode: external
db_host: pg.cliente.com
db_port: 5432
db_sslmode: require      # disable | allow | prefer | require | verify-ca | verify-full
db_max_connections: 200  # max_connections del servidor, para calcular db_maxconn
db_version: "16"
```

Antes del despliegue:

- Crea el rol: `CREATE ROLE odoo_prod LOGIN PASSWORD '…';`
- Dale `CREATEDB`, o crea la base con `OWNER odoo_prod`.
- Permite la IP del VPS en `pg_hba.conf` o en el firewall del servicio.

La contraseña no va en `instance.yaml`: el asistente la guarda en `.rkd/secrets/`, o se pasa al desplegar:

```bash
export INSTANCE_PROD_DB_PASSWORD='…'
chk instance deploy --env prod
```

## Cómo se conecta Odoo

Con `vps` o `external` no hay servicio `db` en el compose. Odoo lee `db_host`, `db_port` y `db_sslmode` de su
`odoo.conf`, y `dbfilter` limita la instancia a su propia base. Las herramientas `psql`, `createdb` y `pg_restore`
corren en contenedores efímeros de la misma imagen de Odoo, con un archivo `pgpass` (permisos 0600).
