"""Manexware fork: deployment choices made once per project.

`rkd init` asks where PostgreSQL should run on stage/prod and which reverse
proxy to use, and stores the answers in `.rkd/instance_defaults.yaml`.
`rkd instance init` proposes them as the defaults of its own questions; the
value that counts at deploy time is the one in `.rkd/instance.yaml`.
"""

from pathlib import Path

import yaml

DEFAULTS_FILE = ".rkd/instance_defaults.yaml"

DB_MODES = ("container", "vps", "external")
PROXIES = ("nginx", "traefik")

# What a project created before this file existed gets proposed.
FALLBACK = {"db_mode": "vps", "proxy": "nginx"}

DB_MODE_LABELS = {
    "container": "En Docker   — contenedor postgres dentro del compose de cada entorno",
    "vps": "En el VPS   — PostgreSQL instalado en el servidor (fuera de Docker); rkd lo instala y configura",
    "external": "Externo     — otro servidor o servicio gestionado (RDS, Cloud SQL, servidor de BD propio)",
}
PROXY_LABELS = {
    "nginx": "Nginx    — en el host, con certbot (Let's Encrypt)",
    "traefik": "Traefik  — en contenedor, con labels y Let's Encrypt integrado (comportamiento original)",
}


def load(project_path: Path) -> dict:
    """The stored choices, with FALLBACK for whatever is missing or invalid."""
    path = Path(project_path) / DEFAULTS_FILE
    data = {}
    if path.is_file():
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            data = {}
    result = dict(FALLBACK)
    if data.get("db_mode") in DB_MODES:
        result["db_mode"] = data["db_mode"]
    if data.get("proxy") in PROXIES:
        result["proxy"] = data["proxy"]
    return result


def save(project_path: Path, *, db_mode: str, proxy: str) -> Path:
    if db_mode not in DB_MODES:
        raise ValueError(f"db_mode must be one of {DB_MODES}, got {db_mode!r}")
    if proxy not in PROXIES:
        raise ValueError(f"proxy must be one of {PROXIES}, got {proxy!r}")
    path = Path(project_path) / DEFAULTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Elecciones de despliegue (stage/prod) hechas en `rkd init`.\n"
        "# `rkd instance init` las propone por defecto; lo que vale al desplegar es .rkd/instance.yaml.\n"
        + yaml.safe_dump({"db_mode": db_mode, "proxy": proxy}, sort_keys=False)
    )
    return path
