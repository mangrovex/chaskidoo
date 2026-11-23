# Comandos

`chk`, `chaskidoo`, `rkd` y `rocketdoo` son el mismo programa. Cada comando tiene ayuda con `--help`.

## Proyecto local

| Comando | Qué hace |
|---|---|
| `chk build` | Construye la imagen local |
| `chk ci` | Genera un workflow de CI para el proyecto |
| `chk del` | Elimina archivos generados que no se usan |
| `chk deploy` | Despliega módulos a un VPS u Odoo.sh |
| `chk deploy-config` | Gestiona esa configuración |
| `chk deploy-init` | Configura el despliegue de módulos |
| `chk deploy-list` | Lista los módulos detectados |
| `chk deploy-run` | Despliega módulos a un destino |
| `chk deploy-validate` | Valida módulos antes de desplegar |
| `chk docker` | Atajos de Docker |
| `chk down` | Detiene y elimina los contenedores |
| `chk gitman` | Repositorios externos (gitman.yaml) |
| `chk gui` | Interfaz web local |
| `chk help` | Ayuda detallada de un comando |
| `chk info` | Información del proyecto actual |
| `chk init` | Crea el proyecto (interactivo o con `--profile`; opciones `--db-mode`, `--proxy`) |
| `chk logs` | Logs de Odoo |
| `chk mail` | Mailpit para correo de pruebas |
| `chk pack` | Empaqueta el entorno para compartirlo |
| `chk pause` | Pausa los contenedores |
| `chk profiles` | Combinaciones soportadas de Odoo, PostgreSQL y edición |
| `chk restart` | Reinicia los contenedores |
| `chk scaffold` | Genera la estructura base |
| `chk status` | Estado de los contenedores |
| `chk stop` | Detiene los contenedores |
| `chk traefik` | Traefik y dominios locales |
| `chk unpack` | Abre un entorno compartido por otra persona |
| `chk up` | Levanta el entorno (`docker compose up`) |

## Instancias (stage / prod)

| Comando | Qué hace |
|---|---|
| `chk instance init` | Asistente de entornos; escribe `.rkd/instance.yaml` |
| `chk instance deploy --env stage\|prod` | Despliega; `--dry-run` solo verifica y genera |
| `chk instance nginx --env …` | Nginx + certbot en el VPS (`--force`, `--no-certbot`, `--email`) |
| `chk instance traefik --env …` | Traefik en el VPS |
| `chk instance status` | Resumen de los entornos configurados |
