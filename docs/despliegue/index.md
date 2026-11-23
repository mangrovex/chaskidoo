# Stage y producción

Chaskidoo despliega instancias completas de Odoo en un VPS con Docker: imagen propia, base de datos,
Odoo con workers y proxy HTTPS. Stage y producción pueden estar en el mismo VPS o en servidores distintos.

## Requisitos del VPS

- Debian o Ubuntu con Docker y el plugin `compose`; el usuario SSH en el grupo `docker`.
- Acceso SSH con llave (recomendado) o contraseña.
- `sudo` sin contraseña si usas PostgreSQL en el VPS o Nginx (instalan paquetes y tocan `/etc`).
- DNS del dominio apuntando al VPS y puertos 80/443 abiertos, para el certificado.

## 1. Configurar los entornos

```bash
chk instance init
```

Por cada entorno (stage, prod) pregunta: conexión SSH, versión de Odoo, **proxy** (uno para todos los entornos),
dominio, correo para Let's Encrypt, **dónde corre PostgreSQL**, usuario y nombre de la base, Enterprise, gitman y
ruta remota. Guarda todo en `.rkd/instance.yaml` y las contraseñas en `.rkd/secrets/` (ignorado por git).

## 2. Ensayar

```bash
chk instance deploy --env stage --dry-run
```

Ejecuta las verificaciones previas (Docker y espacio en el VPS, memoria, proxy, acceso a PostgreSQL, repositorios)
y genera los archivos sin transferir nada.

## 3. Desplegar

```bash
chk instance deploy --env stage
```

Los siete pasos:

1. Genera `Dockerfile`, `docker-compose.yml` y `odoo.conf` del entorno.
2. Prepara el directorio remoto.
3. Transfiere archivos, addons y Enterprise (rsync).
4. Construye la imagen en el VPS.
5. Prepara PostgreSQL (lo instala si es `vps`), crea la base, instala `base` y fija la contraseña de `admin`.
6. Arranca los servicios.
7. Verifica que Odoo responde, y revisa la URL pública.

Al terminar muestra la URL y dónde está la contraseña del usuario `admin`.

## 4. Publicar con HTTPS

=== "Nginx"

    ```bash
    chk instance nginx --env stage
    ```

=== "Traefik"

    ```bash
    chk instance traefik --env stage
    ```

Más detalles en [Proxy](proxy.md).

## Partir de una base local

En `chk instance init` puedes elegir restaurar una base de tu entorno local (con su filestore) en lugar de empezar
de cero. En stage la base se neutraliza: crons, correo saliente y entrante y pasarelas de pago desactivados.
Un segundo despliegue no vuelve a restaurarla.
