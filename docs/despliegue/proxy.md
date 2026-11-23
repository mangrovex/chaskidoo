# Proxy: Nginx o Traefik

El proxy publica Odoo en el dominio con HTTPS. Se elige en `chk init` y en `chk instance init`, uno para todos los
entornos de un proyecto: Nginx y Traefik no pueden usar los puertos 80 y 443 a la vez en el mismo VPS.

| | Nginx | Traefik |
|---|---|---|
| Dónde corre | En el host, paquete del sistema | Contenedor |
| Certificados | certbot (`--nginx --redirect`) | Let's Encrypt integrado |
| Cómo llega a Odoo | Puertos en `127.0.0.1` | Red Docker `traefik-public` y labels |
| Comando | `chk instance nginx --env X` | `chk instance traefik --env X` |

## Nginx

```bash
chk instance nginx --env prod
```

1. Instala Nginx y certbot si faltan (Debian/Ubuntu).
2. Crea `/etc/nginx/sites-available/rkd-<proyecto>_<env>.conf`, con `/websocket` hacia el puerto gevent,
   cabeceras `X-Forwarded-*` para `proxy_mode` y tiempos largos para reportes e importaciones.
3. Valida con `nginx -t` y recarga.
4. Pide el certificado con certbot y agrega la redirección a HTTPS.

Puertos por defecto en el VPS: 8069/8072 en prod y 8169/8172 en stage (`host_http_port`, `host_gevent_port`).

Opciones:

- `--force`: reescribe el sitio aunque exista (certbot vuelve a instalar el certificado).
- `--no-certbot`: solo HTTP.
- `--email`: correo para Let's Encrypt, si no está en `instance.yaml`.

Si el DNS todavía no apunta al VPS, el sitio queda en HTTP; ejecuta el comando otra vez cuando esté listo.
Si los puertos 80/443 están ocupados (por ejemplo, un Traefik anterior), no cambia nada y lo indica.

## Traefik

```bash
chk instance traefik --env prod
```

Instala un contenedor Traefik en `/opt/traefik`, conectado a la red `traefik-public`. Los labels del servicio `web`
enrutan el dominio y `/websocket`, con certificados de Let's Encrypt.

Cada comando se niega a trabajar sobre un entorno configurado con el otro proxy y dice cuál usar.
