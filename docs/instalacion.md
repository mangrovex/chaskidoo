# Instalación

Chaskidoo necesita **Python 3.10 o superior** y **Docker** con el plugin `compose` en tu máquina.
Los servidores (VPS) donde despliegas deben ser Debian o Ubuntu con Docker.

=== "Linux"

    ```bash
    sudo apt install pipx rsync openssh-client
    pipx ensurepath
    pipx install chaskidoo
    ```

    Docker: sigue la guía oficial de Docker Engine para tu distribución y agrega tu usuario al grupo `docker`.

=== "macOS"

    ```bash
    brew install pipx
    pipx ensurepath
    pipx install chaskidoo
    ```

    Docker: Docker Desktop, OrbStack o Colima. `rsync` y `ssh` vienen con macOS.
    Detalles para Apple Silicon en [macOS](macos.md).

=== "Windows (WSL2)"

    Instala Docker Desktop con integración WSL2 y, dentro de tu distribución WSL:

    ```bash
    sudo apt install pipx rsync
    pipx ensurepath
    pipx install chaskidoo
    ```

Comprueba la instalación:

```bash
chk --version
```

!!! tip "Contraseña en lugar de llave SSH"
    Si un VPS se conecta con contraseña y no con llave, instala `sshpass`
    (`sudo apt install sshpass` o `brew install sshpass`). Con llaves SSH no hace falta.

## Desde el código fuente

```bash
git clone https://github.com/mangrovex/chaskidoo.git
cd chaskidoo
pipx install -e .
```

## Actualizar

```bash
pipx upgrade chaskidoo
```
