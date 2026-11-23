# Primeros pasos

## Crear un proyecto

```bash
mkdir cliente-erp && cd cliente-erp
chk init
```

El asistente pregunta:

1. Nombre del proyecto, versión de Odoo (15 a 20) y edición (Community o Enterprise).
2. Repositorios privados (llave SSH) y de terceros (gitman).
3. Versión de PostgreSQL, contraseña maestra, política de reinicio y puertos.
4. **Despliegue en VPS** (stage y prod; el entorno local no cambia):
    - ¿PostgreSQL en Docker, en el VPS o externo?
    - ¿Traefik o Nginx como proxy?

Las respuestas del punto 4 se guardan en `.rkd/instance_defaults.yaml` y se proponen después en `chk instance init`.

Sin preguntas, a partir de un perfil:

```bash
chk profiles list
chk init --profile odoo19-ee --db-mode vps --proxy nginx
```

## Levantar el entorno

```bash
chk up          # docker compose up -d
chk logs        # logs de Odoo
chk status      # estado de los contenedores
chk down        # detener y eliminar contenedores
```

Odoo queda en `http://localhost:8069` (o el puerto que elegiste). Tus módulos van en `addons/`.

## Edición Enterprise

Copia el repositorio `odoo/enterprise` de la versión correspondiente en la carpeta `enterprise/` del proyecto.
Chaskidoo la monta en el contenedor y la pone primero en `addons_path`.

## Interfaz web

```bash
chk gui
```

Abre una interfaz local para ver proyectos, contenedores, módulos e instancias.

## Depuración con VS Code

El proyecto incluye `.vscode/launch.json`: Odoo arranca con `debugpy` escuchando en el puerto de depuración
(8888 por defecto). En VS Code, *Run and Debug* → *Attach*.
