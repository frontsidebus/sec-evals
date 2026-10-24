# Repo conventions

**Inherits local-inference-deck `CONVENTIONS.md` at `deck-tools-v1.0.0`** (the deck-tools release vendored in
`tools/tools.lock`). Its rules apply here unchanged: secrets and forbidden content, "before every commit",
branches, worktrees and PRs, and the deck-tools vendoring rules. This file adds only what is specific to
sec-evals. Where the two differ, this file wins for this repo.

This repo is **PUBLIC**. Everything committed must be generic and secret-free.

## Layout
```
evals/            the security eval harness, kept at its monorepo prefix (README.md, PROTOCOL.md)
  run.py ...      harness; HARNESS_FILES (run.py) are integrity-pinned, see "Harness files" below
  gate.py         the upgrade gate (exit codes 0-4, gate.json: evals/contracts/gate-cli.json, C6)
  contracts/      contracts this repo owns: eval-liveness.json (C5), gate-cli.json (C6)
  tests/fixtures/ vendored copies of other repos' contracts (C3, C4, C9, C10); see "Contracts"
  harness.pin     sha256 of every HARNESS_FILES entry; CI checks it (evals/tests/test_harness_pin.py)
  data/ results/  gitignored: converted benchmark data, run results and gate baselines
docs/             evals-roadmap.md
scripts/          check-sanitized.sh (executable shim into tools/deck-tools/, C10); vendor-contracts.sh
tools/            deck-tools/ (vendored engines) and tools.lock (their sha256 and mode)
evals.env.example the site.env keys this repo reads (example values)
CONVENTIONS.md    this file (C10 needs it at the root)
```

## Site values
- The keys are in [evals.env.example](evals.env.example). Their meaning and the registry of every key are owned by
  local-inference-deck (`contracts/site-keys.yaml`). Adding a key here means adding it to the deck's registry with
  `evals` among its consumers first, then here; the deck's C1 test compares the two.
- The real values come from the operator's site.env. In a checkout, `deck install evals` (run from the deck)
  makes the gitignored `site.env` at this repo's root a symlink to it, which `run.py`'s `--site-env` default reads.
  `evals/tools/lib.sh` also honours `$SITE_ENV` and `~/.config/deck/site.env`. Run gates with
  `bin/deck evals gate ...` from the deck: it exports `SITE_ENV`, runs `python3 -B evals/gate.py` from this repo's
  root and passes the deck's `walter/llama-swap/config.yaml.tmpl` as `--llama-swap-config`.

## Before every commit
As in the deck: `scripts/check-sanitized.sh --all; echo "exit=$?"` (0 clean, 1 finding, 2 no real-value source),
gitleaks on the changed paths, and a grep of the added lines for real domains, IPs, user names and home paths.
Install the hook once per clone with `tools/deck-tools/deck-tools install-hooks`.

## Harness files
- `HARNESS_FILES` in `evals/run.py` are pinned by the C1 freeze and by every baseline's `harness_sha256`. Changing
  any of them invalidates the gate baselines (about 7 GPU h to re-baseline, `docs/runbooks/upgrade.md` in the
  deck) and needs the owner's approval. Bundle such edits into one re-baseline.
- A deliberate harness change updates `evals/harness.pin` in the same commit
  (`python3 -B evals/tests/test_harness_pin.py --write`). CI fails when the files and the pin disagree.
- No vendored contract copy may be a harness file, so refreshing one never forces a re-baseline.

## Contracts
- This repo owns C5 (`evals/contracts/eval-liveness.json`) and C6 (`evals/contracts/gate-cli.json`) and their
  provider tests (`evals/tests/test_contract_liveness.py`, `test_contract_gate_cli.py`). A change bumps
  `contract_version` (minor: additive; major: rename, removal or change of meaning); the deck re-vendors them.
- It consumes vendored copies, refreshed only from a tagged deck checkout:
  `scripts/vendor-contracts.sh <local-inference-deck checkout at a tag>` (C3 aliases, C4 serving identity and its
  fixture template, C9 frontier-env, C10 infra-repo). Consumer tests read only these copies.
- Provenance refs inside the harness data (for example commits `3a0325a` and `57ba4a5`, and
  `walter/llama-swap/...` template paths in `plans/c1-interventions.json` and `PROTOCOL.md`) are
  **local-inference-deck commits and paths**, recorded as text and sha256. They do not resolve in this repo's
  history and do not need to: runs check hashes, not those commits.

## Tests
Offline and single-threaded: `OMP_NUM_THREADS=1 python3 -m pytest evals/tests evals/datasets/tests -q -p
no:cacheprovider`. Tests that check the deck's real template (the C1 D8 flash pins) skip unless
`SPARK_LLAMA_SWAP_TEMPLATE` names `<deck>/walter/llama-swap/config.yaml.tmpl`; the deck's integration run sets it.
