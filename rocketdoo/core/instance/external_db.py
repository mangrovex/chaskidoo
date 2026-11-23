"""Manexware fork: helpers for a PostgreSQL server outside the compose.

Pure functions, no connections: the deployer and the pre-flight compose them
into the scripts they send.
"""

import shlex

from rocketdoo.core.service import ServiceError

# host.docker.internal is resolved by Docker (extra_hosts: host-gateway) inside
# the containers, but not on the VPS host where the pre-flight probe runs.
DOCKER_HOST_ALIAS = "host.docker.internal"


class ExternalDbPasswordMissing(ServiceError):
    pass


def external_password_var(env: str) -> str:
    """Environment variable that may carry the external role's password at deploy time."""
    return f"INSTANCE_{env.upper()}_DB_PASSWORD"


def _pgpass_escape(value: str) -> str:
    # libpq's .pgpass format: ':' and '\\' are escaped with a backslash.
    return value.replace("\\", "\\\\").replace(":", "\\:")


def pgpass_line(host: str, port: int, user: str, password: str) -> str:
    """One .pgpass line valid for every database of `user` on `host:port`."""
    if "\n" in password or "\r" in password:
        raise ValueError("The PostgreSQL password cannot contain a line break")
    return ":".join([_pgpass_escape(host), str(port), "*", _pgpass_escape(user), _pgpass_escape(password)])


def tcp_probe_script(host: str, port: int) -> list[str]:
    """Shell lines that print `db_tcp=yes|no` depending on whether the VPS reaches host:port.

    For host.docker.internal the probe targets the gateway of Docker's default
    bridge, which is what `host-gateway` resolves to inside the containers.
    """
    lines = []
    if host == DOCKER_HOST_ALIAS:
        lines.append(
            "target=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}' "
            "2>/dev/null </dev/null)"
        )
        lines.append('[ -n "$target" ] || target=172.17.0.1')
    else:
        lines.append(f"target={shlex.quote(host)}")
    lines.append(
        f"if timeout 5 bash -c \"</dev/tcp/$target/{int(port)}\" 2>/dev/null; "
        "then echo db_tcp=yes; else echo db_tcp=no; fi"
    )
    lines.append('echo db_target="$target"')
    return lines
