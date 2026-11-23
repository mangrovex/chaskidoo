# macOS

Chaskidoo funciona en macOS con Intel y con Apple Silicon (M1 a M4). Los servidores siguen siendo Linux.

## Requisitos

| Herramienta | Cómo | Para qué |
|---|---|---|
| Python ≥ 3.10 | `brew install python@3.12` (el `python3` de Apple es 3.9) | Chaskidoo |
| Docker | Docker Desktop, OrbStack o Colima | Entorno local |
| rsync, ssh, ssh-agent | Vienen con macOS | Despliegue |
| sshpass (opcional) | `brew install sshpass` | Solo si el VPS usa contraseña |

```bash
brew install pipx && pipx ensurepath
pipx install chaskidoo
```

## Apple Silicon y versiones de Odoo

La imagen oficial `odoo` publica builds para arm64 desde la versión 18. Para Odoo 15, 16 y 17, `chk init` agrega
`platform: linux/amd64` al servicio `web` del compose local y Docker lo ejecuta emulado.

!!! tip "Más rápido con Rosetta"
    En Docker Desktop: *Settings → General → Use Rosetta for x86_64/amd64 emulation on Apple Silicon*.

Odoo 18, 19 y 20 corren nativos en arm64. En Mac Intel y en Linux el compose no cambia.

## Diferencias que maneja Chaskidoo

- Al subir addons y Enterprise excluye `.DS_Store`, `._*`, `__pycache__/` y `*.pyc`.
- Los mensajes de instalación sugieren `brew install …`.
- Con `chk traefik` (dominios locales), el dominio propuesto termina en `.test`: `.local` es Bonjour en macOS y
  resuelve lento. Después de editar `/etc/hosts`:

    ```bash
    sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
    ```
