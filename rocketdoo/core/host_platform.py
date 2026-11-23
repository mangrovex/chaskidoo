"""Manexware fork: facts about the machine rkd runs on (Linux, macOS, WSL).

The VPS side is always Linux; this module is about the developer's machine,
where `rkd init`, `rkd up` and the deploy commands run.
"""

import platform
import re
import shutil

# The official odoo image publishes arm64 builds only from this major on.
# Older ones run on Apple Silicon (and other arm64 hosts) under amd64
# emulation (Rosetta in Docker Desktop / OrbStack, QEMU elsewhere).
ARM64_ODOO_MIN_MAJOR = 18


def system() -> str:
    return platform.system()  # "Linux", "Darwin", "Windows"


def is_macos() -> bool:
    return system() == "Darwin"


def is_arm64() -> bool:
    return platform.machine().lower() in ("arm64", "aarch64")


def is_apple_silicon() -> bool:
    return is_macos() and is_arm64()


def _major(version: str) -> int:
    match = re.match(r"\d+", str(version or ""))
    return int(match.group()) if match else 0


def odoo_platform(odoo_version: str) -> str:
    """`linux/amd64` when this host must emulate the Odoo image, else ''.

    Without it, Docker on an arm64 host fails with "no matching manifest for
    linux/arm64/v8" for odoo:15.0-17.0.
    """
    if is_arm64() and 0 < _major(odoo_version) < ARM64_ODOO_MIN_MAJOR:
        return "linux/amd64"
    return ""


def install_hint(package: str) -> str:
    """How to install a command-line tool on this machine."""
    if is_macos():
        return f"brew install {package}" if shutil.which("brew") else f"install Homebrew (https://brew.sh), then: brew install {package}"
    if shutil.which("apt-get"):
        return f"sudo apt install {package}"
    if shutil.which("dnf"):
        return f"sudo dnf install {package}"
    return f"install '{package}' with your package manager"


def flush_dns_hint() -> str:
    """What makes a new /etc/hosts line take effect, or '' when nothing is needed."""
    if is_macos():
        return "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
    return ""
