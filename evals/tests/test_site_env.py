"""Site-env lookup for the eval tools (evals/tools/lib.sh site_value, gpu-guard.sh, gateway-tunnel.sh), in a copy of
the checkout with example values only: no network, GPU or real site.env. The `deck evals` wrapper and
`deck install evals` (which links <sec-evals>/site.env to the operator's site.env) are tested in local-inference-deck
(tools/tests/), since bin/deck lives there."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


@pytest.fixture
def checkout(tmp_path):
    """A copy of the parts of the checkout these tools use, with no root site.env, and an empty HOME."""
    repo = tmp_path / "repo"
    shutil.copytree(EVALS / "tools", repo / "evals" / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    home = tmp_path / "home"
    home.mkdir()
    return repo, home


def _env(home, **extra):
    e = {k: v for k, v in os.environ.items() if k not in ("SITE_ENV", "REPO", "EVAL_GPU_SSH")}
    e.update(HOME=str(home), EVAL_RUN="sitetest", EVAL_STATE_DIR=str(home / "state"))
    e.update({k: str(v) for k, v in extra.items()})
    return e


def site_value(repo, home, key, **extra):
    r = subprocess.run(["bash", "-c", f'source "{repo}/evals/tools/lib.sh"; site_value {key}'],
                       env=_env(home, **extra), capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _site(path: Path, ip: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"BACKEND_SSH_USER=op\nBACKEND_LAN_IP={ip}   # example\n")
    return path


# ------------------------------------------------------------------------------------------- lib.sh site_value
def test_site_value_reads_SITE_ENV_without_a_root_site_env(checkout, tmp_path):
    repo, home = checkout
    site = _site(tmp_path / "example.env", "192.0.2.10")
    assert not (repo / "site.env").exists()
    assert site_value(repo, home, "BACKEND_LAN_IP", SITE_ENV=site) == "192.0.2.10"


def test_site_value_falls_back_to_the_user_config(checkout):
    repo, home = checkout
    _site(home / ".config" / "deck" / "site.env", "192.0.2.20")
    assert site_value(repo, home, "BACKEND_LAN_IP") == "192.0.2.20"


def test_site_value_order(checkout, tmp_path):
    repo, home = checkout
    assert site_value(repo, home, "BACKEND_LAN_IP") == ""                          # nothing anywhere
    _site(repo / "site.env", "192.0.2.30")
    assert site_value(repo, home, "BACKEND_LAN_IP") == "192.0.2.30"                # the repo root, last
    _site(home / ".config" / "deck" / "site.env", "192.0.2.20")
    assert site_value(repo, home, "BACKEND_LAN_IP") == "192.0.2.20"                # the user config beats it
    site = _site(tmp_path / "example.env", "192.0.2.10")
    assert site_value(repo, home, "BACKEND_LAN_IP", SITE_ENV=site) == "192.0.2.10"  # $SITE_ENV beats both
    # a SITE_ENV that names a missing file is used as given (empty), never silently replaced by a fallback
    assert site_value(repo, home, "BACKEND_LAN_IP", SITE_ENV=tmp_path / "missing.env") == ""


def test_guard_without_a_host_exits_2_and_names_the_file(checkout, tmp_path):
    repo, home = checkout
    missing = tmp_path / "missing.env"
    r = subprocess.run(["bash", str(repo / "evals" / "tools" / "gpu-guard.sh")], env=_env(home, SITE_ENV=missing),
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 2 and str(missing) in r.stderr


def test_tunnel_without_a_backend_exits_2_and_names_the_file(checkout, tmp_path):
    repo, home = checkout
    missing = tmp_path / "missing.env"
    r = subprocess.run(["bash", str(repo / "evals" / "tools" / "gateway-tunnel.sh"), "start"],
                       env=_env(home, SITE_ENV=missing), capture_output=True, text=True, timeout=30)
    assert r.returncode == 2 and str(missing) in r.stderr
