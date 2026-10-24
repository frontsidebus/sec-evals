import sys
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVALS))
sys.dont_write_bytecode = True

import llama_swap_template as LST  # noqa: E402


@pytest.fixture(autouse=True)
def _llama_swap_template(monkeypatch):
    """run.py's --llama-swap-config default is REPO_DIR/walter/llama-swap/config.yaml.tmpl, which is not in this
    repo: point it at $SPARK_LLAMA_SWAP_TEMPLATE or the vendored C4 fixture (llama_swap_template.py)."""
    import run
    monkeypatch.setattr(run, "LLAMA_SWAP_TEMPLATE", LST.path())
