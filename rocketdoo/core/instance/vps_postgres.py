"""Manexware fork: PostgreSQL installed on the VPS host, used by the Docker containers.

Pure: `vps_postgres_script` returns the `bash -s` the deployer sends. It is
idempotent, so every deploy runs it:

1. installs PostgreSQL if no cluster exists (the requested major from the
   distribution, or from apt.postgresql.org when the distribution lacks it);
2. listens on localhost and on the gateway of Docker's default bridge, which
   is where `host.docker.internal` (extra_hosts: host-gateway) points;
3. admits the role from the Docker networks (172.16.0.0/12) in pg_hba.conf;
4. orders postgresql after docker.service, so the bridge address exists when
   the cluster binds at boot;
5. creates the role (LOGIN CREATEDB) or realigns its password.

Debian/Ubuntu only (apt, /etc/postgresql/<ver>/main, pg_ctlcluster).
"""

import re

from .config_manager import invalid_identifiers

DOCKER_NETWORKS = "172.16.0.0/12"
CONF_NAME = "rkd-docker.conf"
SYSTEMD_DROPIN = "/etc/systemd/system/postgresql@.service.d/rkd-after-docker.conf"
_SQL_EOF = "RKD_ROLE_SQL"


def vps_postgres_script(*, db_user: str, password: str | None, version: str = "", port: int = 5432) -> str:
    if invalid_identifiers(db_user):
        raise ValueError(f"not a valid PostgreSQL identifier: {db_user}")
    if not password:
        raise ValueError("No password for the PostgreSQL role: the secret store has none")
    if "\n" in password or "\r" in password or _SQL_EOF in password:
        raise ValueError("The PostgreSQL password cannot contain a line break")
    major = re.match(r"\d+", version or "")
    major = major.group() if major else ""
    sql_password = password.replace("'", "''")
    hba_line = f"host all {db_user} {DOCKER_NETWORKS} $auth"

    lines = [
        "{",
        "set -eu",
        'if [ "$(id -u)" = 0 ]; then SUDO=""; AS_PG="runuser -u postgres --";',
        'elif sudo -n true 2>/dev/null; then SUDO="sudo -n"; AS_PG="sudo -n -u postgres";',
        "else echo 'PostgreSQL on the VPS needs root or passwordless sudo' >&2; exit 1; fi",
        "export DEBIAN_FRONTEND=noninteractive",
        # 1. install
        "if ! ls /usr/lib/postgresql/*/bin/postgres >/dev/null 2>&1; then",
        "  command -v apt-get >/dev/null 2>&1 || { echo 'Only Debian/Ubuntu (apt) is supported' >&2; exit 1; }",
        "  $SUDO apt-get update -qq >&2",
        f'  want="{major}"',
        '  if [ -n "$want" ] && ! apt-cache show "postgresql-$want" >/dev/null 2>&1; then',
        "    echo \"postgresql-$want is not in the distribution: enabling apt.postgresql.org\" >&2",
        "    $SUDO apt-get install -y -qq postgresql-common >&2",
        "    $SUDO /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y >&2",
        "  fi",
        '  if [ -n "$want" ] && apt-cache show "postgresql-$want" >/dev/null 2>&1; then',
        '    $SUDO apt-get install -y -qq "postgresql-$want" >&2',
        "  else",
        "    $SUDO apt-get install -y -qq postgresql >&2",
        "  fi",
        "  echo pg_installed=yes",
        "fi",
        "ver=$(ls /usr/lib/postgresql | sort -n | tail -1)",
        'conf_dir="/etc/postgresql/$ver/main"',
        '$SUDO test -d "$conf_dir" || { echo "No cluster in $conf_dir (expected the Debian layout)" >&2; exit 1; }',
        'echo "pg_version=$ver"',
        f'[ "$ver" -ge 14 ] 2>/dev/null && auth=scram-sha-256 || auth=md5',
        # 2. listen on the Docker bridge gateway
        "gw=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null </dev/null || true)",
        '[ -n "$gw" ] || gw=172.17.0.1',
        'echo "pg_listen=$gw"',
        "restart=no; reload=no",
        '$SUDO mkdir -p "$conf_dir/conf.d"',
        f"desired=\"# Managed by rkd (Manexware fork): Docker containers reach this cluster via host.docker.internal\n"
        f"listen_addresses = 'localhost,$gw'\nport = {int(port)}\"",
        f'current=$($SUDO cat "$conf_dir/conf.d/{CONF_NAME}" 2>/dev/null || true)',
        'if [ "$current" != "$desired" ]; then',
        f'  printf "%s\\n" "$desired" | $SUDO tee "$conf_dir/conf.d/{CONF_NAME}" >/dev/null',
        "  restart=yes",
        "fi",
        # Debian's postgresql.conf has include_dir = 'conf.d'; make sure.
        "if ! $SUDO grep -Eq \"^[[:space:]]*include_dir[[:space:]]*=[[:space:]]*'conf.d'\" \"$conf_dir/postgresql.conf\"; then",
        "  echo \"include_dir = 'conf.d'\" | $SUDO tee -a \"$conf_dir/postgresql.conf\" >/dev/null; restart=yes",
        "fi",
        # 3. pg_hba
        f'hba="{hba_line}"',
        'if ! $SUDO grep -qxF "$hba" "$conf_dir/pg_hba.conf"; then',
        '  echo "$hba" | $SUDO tee -a "$conf_dir/pg_hba.conf" >/dev/null; reload=yes',
        "fi",
        # 4. boot order
        f"if [ ! -f {SYSTEMD_DROPIN} ]; then",
        f"  $SUDO mkdir -p $(dirname {SYSTEMD_DROPIN})",
        f"  printf '[Unit]\\nAfter=docker.service\\n' | $SUDO tee {SYSTEMD_DROPIN} >/dev/null",
        "  $SUDO systemctl daemon-reload || true",
        "fi",
        f'if [ "$restart" = yes ]; then $SUDO systemctl restart "postgresql@$ver-main" || $SUDO pg_ctlcluster "$ver" main restart; echo pg_restarted=yes;',
        f'elif [ "$reload" = yes ]; then $SUDO systemctl reload "postgresql@$ver-main" || $SUDO pg_ctlcluster "$ver" main reload; fi',
        "$SUDO systemctl enable postgresql >/dev/null 2>&1 || true",
        # UFW's default INPUT policy drops container -> host traffic.
        "if command -v ufw >/dev/null 2>&1 && $SUDO ufw status 2>/dev/null | grep -q '^Status: active'; then",
        f"  $SUDO ufw allow from {DOCKER_NETWORKS} to any port {int(port)} proto tcp >/dev/null && echo ufw_rule=yes",
        "fi",
        # 5. role
        f"$AS_PG psql -p {int(port)} -v ON_ERROR_STOP=1 -q -f - <<'{_SQL_EOF}'",
        "DO $rkd$",
        "BEGIN",
        f"  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{db_user}') THEN",
        f"    ALTER ROLE \"{db_user}\" WITH LOGIN CREATEDB PASSWORD '{sql_password}';",
        "  ELSE",
        f"    CREATE ROLE \"{db_user}\" WITH LOGIN CREATEDB PASSWORD '{sql_password}';",
        "  END IF;",
        "END",
        "$rkd$;",
        _SQL_EOF,
        # the containers must be able to open a connection to gw:port
        "ok=no",
        f'for _ in $(seq 1 15); do if timeout 2 bash -c "</dev/tcp/$gw/{int(port)}" 2>/dev/null; then ok=yes; break; fi; sleep 1; done',
        f'if [ "$ok" != yes ]; then echo "PostgreSQL does not listen on $gw:{int(port)}" >&2; exit 1; fi',
        "echo pg_ready=yes",
        "}",
    ]
    return "\n".join(lines) + "\n"
