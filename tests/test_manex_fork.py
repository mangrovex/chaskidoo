"""Tests for the Manexware fork: external PostgreSQL and Nginx instead of Traefik.

Self-contained (no conftest): the upstream sdist ships tests without their
conftest.py and snapshots.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from rocketdoo.core.instance import db_seed, preflight, proxy
from rocketdoo.core.instance.deployer_docker import DockerInstanceDeployer, instance_slug
from rocketdoo.core.instance.external_db import pgpass_line, tcp_probe_script
from rocketdoo.core.instance.config_manager import PG_PROFILES
from rocketdoo.core.models import InstanceConfig

TEMPLATES = Path(__file__).resolve().parent.parent / "rocketdoo" / "templates" / "instance"


def _ctx(external: bool, proxy: str = "nginx", db_mode: str | None = None) -> dict:
    db_mode = db_mode or ("external" if external else "container")
    return {
        "proxy": proxy,
        "db_mode": db_mode,
        "environment": "stage",
        "project_name": "demo",
        "slug": "demo_stage",
        "odoo_tag": "19.0",
        "domain": "stage.example.com",
        "external_db": external,
        "db_host": {"external": "pg.example.com", "vps": "host.docker.internal"}.get(db_mode, "db"),
        "db_port": 5433 if external else 5432,
        "db_sslmode": "require" if external else "prefer",
        "host_http_port": 8169,
        "host_gevent_port": 8172,
        "db_user": "odoo_stage",
        "db_name": "demo_stage",
        "db_password": "s3cr3t",
        "db_version": "16",
        "use_enterprise": True,
        "use_gitman": False,
        "gitman_config_file": "gitman.yaml",
        "install_script": False,
        "needs_ssh": False,
        "ssh_hosts": ["github.com"],
        "addons_path": "/mnt/enterprise,/mnt/extra-addons",
        "pg": PG_PROFILES["small"],
        "admin_passwd": "master",
        "workers": 1,
        "max_cron_threads": 1,
        "log_level": "info",
        "limit_memory_hard": 1,
        "limit_memory_soft": 1,
        "db_maxconn": 20,
    }


def _render(name: str, ctx: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined)
    return env.get_template(name).render(**ctx)


# ─── model ──────────────────────────────────────────────────────────────────


def test_upstream_file_keeps_upstream_behaviour():
    cfg = InstanceConfig.model_validate({"prod": {"vps": {"host": "h", "ssh_key": "k"}, "domain": "p.example.com"}})
    prod = cfg.get("prod")
    assert (prod.db_mode, prod.proxy, prod.effective_db_host) == ("container", "traefik", "db")
    assert prod.is_deployable


def test_vps_mode_needs_no_host_and_external_does():
    cfg = InstanceConfig.model_validate(
        {"stage": {"vps": {"host": "h", "ssh_key": "k"}, "domain": "s.example.com", "db_mode": "external"},
         "prod": {"vps": {"host": "h", "ssh_key": "k"}, "domain": "p.example.com", "db_mode": "vps"}}
    )
    stage, prod = cfg.get("stage"), cfg.get("prod")
    assert prod.effective_db_host == "host.docker.internal" and prod.external_db
    assert (stage.host_http_port, stage.host_gevent_port) == (8169, 8172)
    assert (prod.host_http_port, prod.host_gevent_port) == (8069, 8072)
    assert "db_host" in stage.missing_fields() and not stage.is_deployable
    assert prod.is_deployable


def test_upstream_traefik_email_is_read_as_letsencrypt_email():
    cfg = InstanceConfig.model_validate({"prod": {"traefik_email": "ops@example.com", "db_mode": "container"}})
    assert cfg.get("prod").letsencrypt_email == "ops@example.com"
    assert "traefik_email" not in cfg.to_yaml_dict()["environments"]["prod"]


def test_db_host_rejects_shell_metacharacters():
    with pytest.raises(Exception):
        InstanceConfig.model_validate({"prod": {"db_host": "pg; rm -rf /"}})


# ─── templates ──────────────────────────────────────────────────────────────


def test_compose_external_has_no_db_service_and_no_traefik():
    text = _render("docker-compose.jinja", _ctx(external=True))
    data = yaml.safe_load(text)
    assert set(data["services"]) == {"web"}
    web = data["services"]["web"]
    assert web["ports"] == ["127.0.0.1:8169:8069", "127.0.0.1:8172:8072"]
    assert web["environment"]["PGHOST"] == "pg.example.com"
    assert web["environment"]["PGPASSFILE"] == "/run/secrets/pgpass"
    assert "host.docker.internal:host-gateway" in web["extra_hosts"]
    assert data["secrets"] == {"pgpass": {"file": "./pgpass"}}
    assert "traefik" not in text.lower()
    assert "networks" not in data


def test_compose_container_mode_keeps_db_without_traefik():
    text = _render("docker-compose.jinja", _ctx(external=False))
    data = yaml.safe_load(text)
    assert set(data["services"]) == {"web", "db"}
    assert data["services"]["web"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert data["services"]["web"]["ports"][0].startswith("127.0.0.1:")
    assert "traefik" not in text.lower()
    assert "stage-internal" in data["networks"]


def test_odoo_conf_points_at_external_server():
    conf = _render("odoo.conf.jinja", _ctx(external=True))
    assert "db_host = pg.example.com" in conf
    assert "db_port = 5433" in conf
    assert "db_sslmode = require" in conf
    assert "dbfilter = ^demo_stage$" in conf
    assert "proxy_mode = True" in conf


@pytest.mark.skipif(not shutil.which("docker"), reason="docker CLI not available")
@pytest.mark.parametrize("external", [True, False])
def test_compose_validates_with_docker(tmp_path, external):
    env_dir = tmp_path / "stage"
    env_dir.mkdir()
    (env_dir / "docker-compose.yml").write_text(_render("docker-compose.jinja", _ctx(external)))
    (env_dir / "pgpass").write_text("x\n")
    (env_dir / "odoo_pg_pass").write_text("x")
    (tmp_path / "Dockerfile.stage").write_text("FROM odoo:19.0\n")
    result = subprocess.run(["docker", "compose", "config", "-q"], cwd=env_dir, capture_output=True, text=True)
    if "Cannot connect" in result.stderr or "not a docker command" in result.stderr:
        pytest.skip(result.stderr.strip())
    assert result.returncode == 0, result.stderr


# ─── external db helpers ────────────────────────────────────────────────────


def test_pgpass_escapes_colons_and_backslashes():
    assert pgpass_line("pg", 5432, "odoo", r"a:b\c") == r"pg:5432:*:odoo:a\:b\\c"
    with pytest.raises(ValueError):
        pgpass_line("pg", 5432, "odoo", "a\nb")


def test_pg_tool_runs_clients_in_a_one_off_web_container():
    assert db_seed.pg_tool("psql", external=True, db_user="u") == (
        "docker compose run --rm -T --no-deps -l traefik.enable=false --user root --entrypoint psql web"
    )
    assert db_seed.pg_tool("psql", external=False, db_user="u") == "docker compose exec -T db psql -U u"


def _bash_ok(script: str):
    result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_external_seed_scripts_never_touch_a_db_service():
    state = db_seed.docker_state_script("/opt/odoo-stage/stage", db_name="demo", db_user="odoo", external=True)
    restore = db_seed.docker_restore_script(
        "/opt/odoo-stage/stage", "/opt/odoo-stage/.seed", env="stage", source_db="dev", db_name="demo",
        db_user="odoo", domain="stage.example.com", external=True,
    )
    for script in (state, restore):
        _bash_ok(script)
        assert "exec -T db" not in script and "up -d db" not in script
    assert "--entrypoint pg_restore web -d demo" in restore
    assert "--entrypoint createdb web -E UTF8" in restore


def test_tcp_probe_maps_docker_host_alias_to_bridge_gateway():
    lines = tcp_probe_script("host.docker.internal", 5432)
    assert any("docker network inspect bridge" in line for line in lines)
    _bash_ok("\n".join(lines) + "\n")
    direct = tcp_probe_script("10.0.0.5", 6432)
    assert "target=10.0.0.5" in direct and any("/6432" in line for line in direct)


# ─── deployer ───────────────────────────────────────────────────────────────


def _deployer(tmp_path, **overrides) -> DockerInstanceDeployer:
    from rocketdoo.core.instance import deployer_docker

    env = {"vps": {"host": "h", "ssh_key": "k"}, "domain": "stage.example.com", "db_host": "pg.example.com", **overrides}
    cfg = InstanceConfig.model_validate({"stage": env}).to_yaml_dict()["environments"]["stage"]
    original = deployer_docker.resolve_auth
    deployer_docker.resolve_auth = lambda *a, **k: {}
    try:
        deployer = DockerInstanceDeployer("stage", cfg, tmp_path)
    finally:
        deployer_docker.resolve_auth = original
    deployer._resolve_admin_login_password = lambda: "adminpw"
    return deployer


@pytest.mark.parametrize("mode", ["external", "vps", "container"])
def test_ensure_database_script_is_valid_bash(tmp_path, mode):
    script = _deployer(tmp_path, db_mode=mode)._ensure_database_script()
    _bash_ok(script)
    if mode != "container":
        assert "up -d db" not in script and "exec -T db" not in script
        assert "--entrypoint createdb web" in script
    else:
        assert "docker compose up -d db" in script


def test_instance_slug_matches_nginx_rules(tmp_path):
    (tmp_path / "docker-compose.yaml").write_text("name: my-proj.v2\n")
    assert instance_slug(tmp_path, "prod") == "my_proj_v2_prod"


# ─── nginx ──────────────────────────────────────────────────────────────────


def test_site_routes_websocket_to_gevent_port():
    site = proxy.render_site(slug="demo_stage", domain="stage.example.com", http_port=8169, gevent_port=8172)
    assert "server 127.0.0.1:8169;" in site and "server 127.0.0.1:8172;" in site
    assert "location /websocket" in site and "server_name stage.example.com;" in site
    with pytest.raises(ValueError):
        proxy.render_site(slug="x", domain="bad domain;", http_port=1, gevent_port=2)


@pytest.mark.skipif(not shutil.which("nginx"), reason="nginx not installed")
def test_two_sites_on_one_vps_pass_nginx_t(tmp_path):
    sites = [
        proxy.render_site(slug="demo_stage", domain="stage.example.com", http_port=8169, gevent_port=8172),
        proxy.render_site(slug="demo_prod", domain="erp.example.com", http_port=8069, gevent_port=8072),
    ]
    (tmp_path / "logs").mkdir()
    body = "\n".join(s.replace("/var/log/nginx", str(tmp_path / "logs")) for s in sites)
    if not Path("/proc/net/if_inet6").exists() or not Path("/proc/net/if_inet6").read_text().strip():
        # What install_script does on a host without IPv6.
        body = body.replace("    listen [::]:80;\n", "")
    conf = tmp_path / "nginx.conf"
    conf.write_text(
        f"pid {tmp_path}/nginx.pid;\nerror_log {tmp_path}/error.log;\nevents {{}}\n"
        f"http {{\n  access_log off;\n{body}\n}}\n"
    )
    result = subprocess.run(["nginx", "-t", "-c", str(conf), "-p", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_install_script_is_valid_bash_and_embeds_the_site():
    script = proxy.install_script(
        slug="demo_prod", domain="erp.example.com", email="ops@example.com", http_port=8069, gevent_port=8072
    )
    _bash_ok(script)
    assert "certbot --nginx -d erp.example.com" in script
    assert "upstream rkd_demo_prod_odoo" in script
    with pytest.raises(ValueError):
        proxy.install_script(slug="d", domain="erp.example.com", email="x; rm", http_port=1, gevent_port=2)


# ─── pre-flight ─────────────────────────────────────────────────────────────


def test_preflight_reports_nginx_and_external_db():
    cfg = {"type": "docker", "db_mode": "external", "proxy": "nginx", "db_host": "pg", "db_port": 5432,
           "domain": "erp.example.com", "remote_path": "/opt/odoo-prod"}
    remote = {"reachable": "yes", "docker_ok": "yes", "compose": "2.29", "path_writable": "yes", "mem_kb": "8000000",
              "free_kb": "99999999", "nginx_installed": "yes", "nginx_running": "yes", "nginx_site": "no",
              "db_tcp": "no", "repo_ok": [], "repo_fail": []}
    checks = {c["name"]: c for c in preflight._remote_checks(cfg, remote, "prod", {})}
    assert not checks["nginx"]["ok"] and "rkd instance nginx --env prod" in checks["nginx"]["hint"]
    assert not checks["external postgresql"]["ok"]
    assert "traefik" not in checks
    script = preflight._remote_script(cfg, [])
    _bash_ok(script)
    assert "nginx_site" in script and "db_tcp" in script


def test_public_url_http_only_means_no_certificate_yet():
    check = preflight.public_url_check("erp.example.com", "http=200:0\nhttps=000:7\n", env="prod")
    assert not check["ok"] and "certificate" in check["detail"]


# ─── matrix: 3 PostgreSQL modes x 2 proxies ────────────────────────────────


@pytest.mark.parametrize("db_mode", ["container", "vps", "external"])
@pytest.mark.parametrize("proxy_name", ["nginx", "traefik"])
def test_compose_matrix(tmp_path, db_mode, proxy_name):
    external = db_mode != "container"
    text = _render("docker-compose.jinja", _ctx(external, proxy=proxy_name, db_mode=db_mode))
    data = yaml.safe_load(text)
    web = data["services"]["web"]
    assert ("db" in data["services"]) == (db_mode == "container")
    if proxy_name == "nginx":
        assert web["ports"] == ["127.0.0.1:8169:8069", "127.0.0.1:8172:8072"]
        assert "labels" not in web and "traefik-public" not in text
    else:
        assert "ports" not in web and web["expose"] == ["8069", "8072"]
        assert "traefik.enable=true" in web["labels"]
        assert data["networks"]["traefik-public"] == {"external": True}
    if db_mode == "vps":
        assert web["environment"]["PGHOST"] == "host.docker.internal"
    if shutil.which("docker"):
        env_dir = tmp_path / "stage"
        env_dir.mkdir()
        (env_dir / "docker-compose.yml").write_text(text)
        (env_dir / "pgpass").write_text("x\n")
        (env_dir / "odoo_pg_pass").write_text("x")
        result = subprocess.run(["docker", "compose", "config", "-q"], cwd=env_dir, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_vps_postgres_script_is_valid_and_quotes_the_password():
    from rocketdoo.core.instance.vps_postgres import vps_postgres_script

    script = vps_postgres_script(db_user="odoo_prod", password="it's", version="16", port=5432)
    _bash_ok(script)
    assert "PASSWORD 'it''s'" in script and "host all odoo_prod 172.16.0.0/12" in script
    with pytest.raises(ValueError):
        vps_postgres_script(db_user="bad name", password="x")
    with pytest.raises(ValueError):
        vps_postgres_script(db_user="odoo", password="")


def test_one_off_containers_are_never_routed_by_traefik(tmp_path):
    script = _deployer(tmp_path, db_mode="vps", proxy="traefik")._ensure_database_script()
    for line in script.splitlines():
        if "docker compose run" in line:
            assert "-l traefik.enable=false" in line, line


def test_preflight_traefik_and_vps_mode():
    cfg = {"type": "docker", "db_mode": "vps", "proxy": "traefik", "domain": "erp.example.com",
           "remote_path": "/opt/odoo-prod"}
    remote = {"reachable": "yes", "docker_ok": "yes", "compose": "2.29", "path_writable": "yes", "mem_kb": "8000000",
              "free_kb": "99999999", "traefik_running": "no", "traefik_attached": "no", "sudo": "no", "uid": "1000",
              "vps_pg": "no", "repo_ok": [], "repo_fail": []}
    checks = {c["name"]: c for c in preflight._remote_checks(cfg, remote, "prod", {})}
    assert "nginx" not in checks and not checks["traefik"]["ok"]
    assert checks["postgresql on the vps"]["level"] == "block" and not checks["postgresql on the vps"]["ok"]
    assert "external postgresql" not in checks
    _bash_ok(preflight._remote_script(cfg, []))


def test_init_defaults_roundtrip(tmp_path):
    from rocketdoo.core.instance import defaults

    assert defaults.load(tmp_path) == defaults.FALLBACK
    defaults.save(tmp_path, db_mode="container", proxy="traefik")
    assert defaults.load(tmp_path) == {"db_mode": "container", "proxy": "traefik"}
    with pytest.raises(ValueError):
        defaults.save(tmp_path, db_mode="cloud", proxy="nginx")


def test_rkd_init_profile_stores_choices(tmp_path):
    result = subprocess.run(
        ["rkd", "init", "--profile", "odoo19-ce", "--db-mode", "container", "--proxy", "traefik"],
        cwd=tmp_path, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr[-500:]
    stored = yaml.safe_load((tmp_path / ".rkd" / "instance_defaults.yaml").read_text())
    assert stored == {"db_mode": "container", "proxy": "traefik"}
