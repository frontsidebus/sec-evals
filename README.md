# sec-evals

The security eval harness and upgrade gate for the local models served by
[local-inference-deck](#relationship-to-local-inference-deck): suites x models through the LiteLLM gateway,
scorers, reports with confidence intervals, and the confirmatory C1 protocol. Stdlib-only Python.

The harness, its protocol and its docs are in [evals/](evals/README.md) ([PROTOCOL.md](evals/PROTOCOL.md));
findings and the roadmap are in [docs/evals-roadmap.md](docs/evals-roadmap.md). Repo rules:
[CONVENTIONS.md](CONVENTIONS.md).

## Origin

This repo was split out of local-inference-deck with
`git filter-repo --path evals/ --path docs/evals-roadmap.md` (plan step 3). The `evals/` prefix is kept on
purpose: the eval-liveness contract (C5) matches the argv suffixes `evals/run.py` and
`evals/tools/gpu-guard.sh` and the pid files `evals/results/_runs/*/*.pid`, and `HARNESS_FILES` are
`evals/...` paths. No harness file was edited in the split; `evals/harness.pin` records their sha256.

**Provenance refs are deck-repo commits.** Commit ids and paths recorded in the harness data, for example
`57ba4a5` and `3a0325a^` and `walter/llama-swap/config.yaml.tmpl` in `evals/plans/c1-interventions.json` and
`evals/PROTOCOL.md`, refer to local-inference-deck's history, not this one. The filtered history here keeps
only the commits that touched `evals/` or `docs/evals-roadmap.md`, under new ids. Runs check the recorded
sha256 values, so nothing depends on those commits resolving here.

## Running

Gates and runs are started from the deck so they read the same site.env and template as the rest of the deck:

```sh
# in the local-inference-deck checkout; this checkout is $SEC_EVALS_DIR, else ~/src/deck/sec-evals
bin/deck install evals                              # once: links <sec-evals>/site.env to the operator's site.env
bin/deck evals gate check --model coder --yes      # runs `python3 -B evals/gate.py ...` from this repo's root
```

`bin/deck evals` passes `--site-env` and `--llama-swap-config <deck>/walter/llama-swap/config.yaml.tmpl`. See
[evals/README.md](evals/README.md#upgrade-gate) for the gate itself. The site keys this repo reads are in
[evals.env.example](evals.env.example).

The workstation's `spark-model` refuses model swaps while an eval run is live; it looks in the checkouts listed
in `SPARK_EVAL_REPOS`, so add this checkout there before any model swap.

## Tests

```sh
OMP_NUM_THREADS=1 python3 -m pytest evals/tests evals/datasets/tests -q -p no:cacheprovider
```

Offline; no deck checkout is needed. Tests that check the deck's real llama-swap template (the C1 D8 flash pins)
skip unless `SPARK_LLAMA_SWAP_TEMPLATE` points at `<deck>/walter/llama-swap/config.yaml.tmpl`.

## Relationship to local-inference-deck

| Seam | Here | In the deck |
|---|---|---|
| C3 gateway aliases, C4 serving identity, C9 frontier env, C10 infra repo | vendored copies under `evals/tests/fixtures/` (`scripts/vendor-contracts.sh`) | sources and provider tests |
| C5 eval liveness, C6 gate CLI | `evals/contracts/` and provider tests | vendored copies and consumer tests |
| deck-tools (sanitizer engines) | `tools/deck-tools/`, pinned by `tools/tools.lock` | origin, released as `deck-tools-v*` tags |
| site keys | `evals.env.example` | `contracts/site-keys.yaml` (the registry) |
| pin | n/a | `deck.lock` (`sec-evals`, `mode: minimum`) |
