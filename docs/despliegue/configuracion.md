# Configuración: `.rkd/instance.yaml`

`chk instance init` escribe este archivo; puedes editarlo a mano. Un archivo del Rocketdoo original
(sin `proxy` ni `db_mode`) sigue funcionando: equivale a `container` + `traefik`.

```yaml
environments:
  stage:
    type: docker
    vps: {host: 203.0.113.10, port: 22, user: ubuntu, auth_method: ssh_key, ssh_key: ~/.ssh/id_ed25519}
    odoo_version: "19.0"
    domain: stage.cliente.com
    letsencrypt_email: soporte@cliente.com
    proxy: nginx
    db_mode: vps
    db_version: "16"
    db_user: odoo_stage
    db_name: cliente_stage
    host_http_port: 8169
    host_gevent_port: 8172
    use_enterprise: true
    enterprise_source: rsync
    remote_path: /opt/odoo-stage
  prod:
    type: docker
    vps: {host: 203.0.113.20, user: ubuntu, auth_method: ssh_key, ssh_key: ~/.ssh/id_ed25519}
    odoo_version: "19.0"
    domain: erp.cliente.com
    letsencrypt_email: soporte@cliente.com
    proxy: nginx
    db_mode: external
    db_host: pg.cliente.com
    db_sslmode: require
    db_max_connections: 200
    db_version: "16"
```

## Campos

| Campo | Valores | Para qué |
|---|---|---|
| `type` | `docker`, `native` | `native` instala los paquetes de Odoo sin Docker (sin proxy) |
| `vps` | `host`, `port`, `user`, `auth_method`, `ssh_key` o `password` | Conexión SSH; `password` puede ser `${VARIABLE}` |
| `odoo_version`, `odoo_tag` | `19.0`… | Versión e imagen base |
| `domain`, `letsencrypt_email` | | Dominio público y correo del certificado (`traefik_email` también se acepta) |
| `proxy` | `nginx`, `traefik` | [Proxy](proxy.md) |
| `host_http_port`, `host_gevent_port` | puerto | Solo con Nginx: puertos en `127.0.0.1` del VPS |
| `db_mode` | `container`, `vps`, `external` | [PostgreSQL](postgresql.md) |
| `db_host`, `db_port`, `db_sslmode`, `db_max_connections` | | Solo `external` (`db_port` también en `vps`) |
| `db_version` | `16`… | Imagen postgres, versión a instalar en el VPS o versión del servidor externo |
| `db_user`, `db_name` | identificadores | Rol y base; por defecto `odoo_<env>` |
| `pg_profile` | `small`, `medium`, `large` | Solo `container` |
| `seed_database` | nombre de una base local | Restaurarla en el primer despliegue |
| `use_enterprise`, `enterprise_source` | `rsync`, `clone` | Copiar `enterprise/` o clonarlo en el VPS con tu agente SSH |
| `use_gitman`, `gitman_config` | | Repositorios de terceros |
| `remote_path` | ruta | Carpeta del entorno en el VPS |

## Secretos

`.rkd/secrets/instance_<env>_db.env` (0600, ignorado por git):

| Clave | Qué es |
|---|---|
| `ODOO_PG_PASS` | Contraseña del rol de PostgreSQL |
| `ODOO_ADMIN_PASSWD` | Contraseña maestra de Odoo |
| `ODOO_ADMIN_LOGIN_PASSWD` | Contraseña del usuario `admin` |
