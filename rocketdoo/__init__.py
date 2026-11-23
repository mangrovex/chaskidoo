"""
Chaskidoo - Odoo development and deployment (Manexware fork of Rocketdoo)
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chaskidoo")
except PackageNotFoundError:
    # Fallback for local development (pip install -e .)
    __version__ = "dev"
