---
hide:
  - navigation
---

<div class="chk-hero" markdown>
![Chaskidoo](assets/chaskidoo-lockup-light.svg){ .light }
![Chaskidoo](assets/chaskidoo-lockup-dark.svg){ .dark }
</div>

# De tu máquina a producción

Los **chaskis** llevaban los mensajes del Tawantinsuyu por el Qhapaq Ñan, de relevo en relevo.
**Chaskidoo** hace lo mismo con tus módulos de Odoo: los lleva de tu máquina a **stage** y de stage a **producción**.

Es una herramienta de línea de comandos (`chk`) para crear entornos de desarrollo de Odoo con Docker y desplegar
instancias completas en un VPS, con PostgreSQL y proxy HTTPS configurados.

## Qué hace

- **Entorno local en minutos**: `chk init` genera el proyecto (Dockerfile, compose, `odoo.conf`, depuración con VS Code)
  para Odoo 15 a 20, Community o Enterprise. `chk up` lo levanta.
- **Despliegue a stage y producción**: `chk instance deploy` construye la imagen en el VPS, crea la base de datos,
  arranca Odoo y verifica que responde.
- **PostgreSQL donde lo necesites**: en un contenedor, instalado en el mismo VPS o en un servidor externo
  (RDS, Cloud SQL, servidor propio). [Ver opciones](despliegue/postgresql.md).
- **HTTPS con Nginx o Traefik**, con certificados de Let's Encrypt. [Ver opciones](despliegue/proxy.md).
- **Linux, macOS y WSL2**, incluido Apple Silicon. [Ver macOS](macos.md).
- Repositorios de terceros con gitman, Mailpit para correo de pruebas, interfaz web (`chk gui`).

## Inicio rápido

```bash
pipx install chaskidoo
mkdir mi-proyecto && cd mi-proyecto
chk init        # proyecto local + dónde correrá PostgreSQL y qué proxy usar en stage/prod
chk up          # Odoo en http://localhost:8069
```

Y cuando quieras publicar:

```bash
chk instance init                 # datos de stage y prod (VPS, dominio, base de datos)
chk instance deploy --env stage
chk instance nginx  --env stage   # HTTPS con Let's Encrypt
```

## Origen

Chaskidoo es un fork de [Rocketdoo](https://pypi.org/project/rocketdoo/) (Horacio Montaño / HDMSoft), mantenido por
Manuel Vega en Manexware S.A. Se distribuye bajo la misma licencia, **LGPL-3.0**.
Los comandos `rkd` y `rocketdoo` siguen funcionando como alias de `chk`.
