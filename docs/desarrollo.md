# Desarrollo y licencia

## Contribuir

```bash
git clone https://github.com/mangrovex/chaskidoo.git
cd chaskidoo
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest mkdocs-material
pytest tests/test_manex_fork.py
mkdocs serve          # documentación en http://127.0.0.1:8000
```

La integración continua ejecuta las pruebas en Ubuntu y macOS (Apple Silicon) con Python 3.10 y 3.12.

## Estructura

- `rocketdoo/` — el paquete (conserva el nombre de upstream para facilitar la sincronización).
- `rocketdoo/templates/instance/` — compose, Dockerfile y `odoo.conf` de stage/prod.
- `rocketdoo/core/instance/` — despliegue: verificaciones previas, PostgreSQL en el VPS, Nginx, Traefik, restauración.
- `assets/brand/` — icono y logotipo; `build_icons.py` los regenera.
- `docs/` — este sitio.

## Sincronizar con Rocketdoo

El código original está en la etiqueta `upstream-3.14.1`. Para una versión nueva de Rocketdoo:

```bash
pip download rocketdoo==X.Y.Z --no-binary :all: --no-deps
git switch -c upstream-X.Y.Z upstream-3.14.1
# reemplazar el código por el del sdist, commit
git tag upstream-X.Y.Z
git switch main && git rebase upstream-X.Y.Z
```

## Licencia y créditos

Chaskidoo es software libre bajo la **GNU Lesser General Public License v3.0** (`LICENSE`), que se complementa con la
GNU GPL v3 (`COPYING`).

- Rocketdoo: © 2024-2026 Horacio Montaño, HDMSoft.
- Modificaciones de Chaskidoo: Manuel Vega · Manexware S.A. El historial de git documenta cada cambio.
