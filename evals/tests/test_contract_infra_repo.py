"""C10 consumer (sec-evals): this repo is a valid agent-judge infra repo (an entry of JUDGE_INFRA_REPOS), per the
vendored fixtures/contracts/infra-repo.json (a copy of judge/contracts/infra-repo.json; refresh with
`scripts/vendor-contracts.sh <deck checkout at a tag>`; agent-judge's provider test is
judge/tests/test_contract_infra_repo.py). `resolved_under_judge_repo_dir` (render.sh and the sanitizer probe) is
required only of the JUDGE_REPO_DIR repo, the deck, so it is not checked here.
Run: python3 -m pytest evals/tests/test_contract_infra_repo.py -q -p no:cacheprovider
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
C10 = json.loads((Path(__file__).resolve().parent / "fixtures" / "contracts" / "infra-repo.json").read_text())


def test_contract_version_is_accepted():
    assert C10["contract"] == "infra-repo" and C10["contract_version"].startswith("1.")


@pytest.mark.parametrize("rel", C10["repo_root_files"])
def test_required_files_are_at_the_root(rel):
    assert (REPO / rel).is_file(), rel


@pytest.mark.parametrize("rel", C10["executable"])
def test_required_scripts_are_executable_in_git_and_on_disk(rel):
    assert os.access(REPO / rel, os.X_OK), rel
    r = subprocess.run(["git", "ls-files", "-s", "--", rel], cwd=REPO, capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or not r.stdout:
        pytest.skip("not a git checkout")
    assert r.stdout.split()[0] == "100755", rel


def test_conventions_inherit_the_deck():
    text = (REPO / "CONVENTIONS.md").read_text()
    assert "Inherits local-inference-deck `CONVENTIONS.md` at `deck-tools-v" in text


def test_sanitizer_shim_execs_the_vendored_engine():
    text = (REPO / "scripts" / "check-sanitized.sh").read_text()
    assert 'exec "$here/../tools/deck-tools/check-sanitized.sh" "$@"' in text
    assert (REPO / "tools" / "deck-tools" / "check-sanitized.sh").is_file()
