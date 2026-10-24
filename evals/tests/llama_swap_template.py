"""The llama-swap config the tests read in place of run.py's default (REPO_DIR/walter/llama-swap/config.yaml.tmpl).

sec-evals has no walter/ tree: the template is the deck's. Tests read $SPARK_LLAMA_SWAP_TEMPLATE when it is set
(the deck's integration run points it at <deck>/walter/llama-swap/config.yaml.tmpl), else the vendored C4 fixture
fixtures/llama-swap.contract.yaml (a copy of the deck's contracts/serving-identity/llama-swap.contract.yaml).
conftest.py points run.LLAMA_SWAP_TEMPLATE at it for every test, so run.py's own --llama-swap-config default
(and its "from the repo template" labelling) is what the tests exercise. run.py itself is never edited.

Tests that check the real template's content against harness pins (the C1 D8 flash cmd in
plans/c1-interventions.json) need the deck's template: they are marked ``needs_deck_template`` and skip without
$SPARK_LLAMA_SWAP_TEMPLATE.
"""
import os
from pathlib import Path

import pytest

ENV = "SPARK_LLAMA_SWAP_TEMPLATE"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "llama-swap.contract.yaml"
DECK_TEMPLATE = bool(os.environ.get(ENV))


def path() -> Path:
    env = os.environ.get(ENV)
    return Path(env) if env else FIXTURE


# A model whose server cmd sets --presence-penalty 1.5 and serves from a .gguf with a parseable quant: coder-fast
# in the deck's template, example-moe (alias "fast") in the C4 fixture. "coder" (qwen3.8-27b, UD-Q4_K_XL) is in both.
MOE_ALIAS, MOE_ID = ("coder-fast", "qwen3.6-35b-a3b") if DECK_TEMPLATE else ("fast", "example-moe")
# a grader alias that the config serves from a .gguf file
GRADER_ALIAS = "big" if DECK_TEMPLATE else "fast"

needs_deck_template = pytest.mark.skipif(
    not DECK_TEMPLATE, reason=f"needs the deck's walter llama-swap template: set {ENV} (deck integration run)")
