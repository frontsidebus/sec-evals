#!/usr/bin/env bash
# vendor-contracts.sh: refresh the contract copies sec-evals consumes, from tagged checkouts of their owners.
#
# Usage: scripts/vendor-contracts.sh [--check] [--judge DIR] DECK
#   DECK         a local-inference-deck checkout, at a release tag (C3 aliases, C4 serving identity)
#   --judge DIR  where judge/contracts/ comes from (C9 frontier-env, C10 infra-repo): an agent-judge checkout once
#                the judge is split out; default DECK (judge/ is still in the deck)
#   --check      compare only; exit 1 naming each copy that differs, change nothing
#
# The copies are byte-identical; evals/tests/fixtures/contracts/SOURCES records where they came from (name, tag
# or "untagged", commit; never a local path). Consumer tests read only the copies. None of them is a
# HARNESS_FILES entry, so a refresh never forces a re-baseline. Exit 0 ok, 1 a difference (--check), 2 usage or
# a source with uncommitted changes in the files copied.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
check=0 judge="" deck=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) check=1; shift ;;
    --judge) [ $# -ge 2 ] || { echo "vendor-contracts: --judge needs a dir" >&2; exit 2; }; judge=$2; shift 2 ;;
    -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "vendor-contracts: unknown option $1" >&2; exit 2 ;;
    *) [ -z "$deck" ] || { echo "vendor-contracts: one DECK only" >&2; exit 2; }; deck=$1; shift ;;
  esac
done
[ -n "$deck" ] || { echo "usage: scripts/vendor-contracts.sh [--check] [--judge DIR] DECK" >&2; exit 2; }
judge=${judge:-$deck}

# source repo | source path | copy (relative to this repo)
PAIRS=(
  "deck|contracts/aliases.json|evals/tests/fixtures/contracts/aliases.json"
  "deck|contracts/serving-identity/vectors.json|evals/tests/fixtures/contracts/serving-vectors.json"
  "deck|contracts/serving-identity/llama-swap.contract.yaml|evals/tests/fixtures/llama-swap.contract.yaml"
  "deck|contracts/serving-identity/serving.schema.json|evals/tests/fixtures/contracts/serving.schema.json"
  "judge|judge/contracts/frontier-env.json|evals/tests/fixtures/contracts/frontier-env.json"
  "judge|judge/contracts/infra-repo.json|evals/tests/fixtures/contracts/infra-repo.json"
)

src_dir() { if [ "$1" = deck ]; then echo "$deck"; else echo "$judge"; fi; }

identity() {   # identity NAME DIR PATHS...: "<name> <tag|untagged> <commit>"; exit 2 if the paths are dirty
  local name=$1 dir=$2; shift 2
  git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "vendor-contracts: $dir is not a git checkout" >&2; exit 2; }
  if [ -n "$(GIT_OPTIONAL_LOCKS=0 git -C "$dir" status --porcelain -- "$@")" ]; then
    echo "vendor-contracts: $dir has uncommitted changes in the contract files" >&2; exit 2
  fi
  local tag; tag=$(git -C "$dir" describe --tags --exact-match HEAD 2>/dev/null || echo untagged)
  echo "$name $tag $(git -C "$dir" rev-parse HEAD)"
}

diffs=0 deck_paths=() judge_paths=()
for p in "${PAIRS[@]}"; do
  IFS='|' read -r who src dst <<<"$p"
  from="$(src_dir "$who")/$src"
  [ -f "$from" ] || { echo "vendor-contracts: missing $who:$src" >&2; exit 2; }
  if [ "$who" = deck ]; then deck_paths+=("$src"); else judge_paths+=("$src"); fi
  if ! cmp -s "$from" "$root/$dst"; then
    diffs=$((diffs + 1))
    if [ "$check" = 1 ]; then echo "differs: $dst (from $who:$src)"; else install -m 644 "$from" "$root/$dst"; echo "updated: $dst"; fi
  fi
done
if [ "$check" = 1 ]; then
  [ "$diffs" = 0 ] && echo "vendor-contracts: all ${#PAIRS[@]} copies current" && exit 0
  exit 1
fi
{
  echo "# evals/tests/fixtures/contracts/SOURCES: where scripts/vendor-contracts.sh copied the contracts from."
  echo "# <owner> <tag|untagged> <commit>"
  identity local-inference-deck "$deck" "${deck_paths[@]}"
  if [ "$(cd "$judge" && pwd)" = "$(cd "$deck" && pwd)" ]; then
    echo "# judge/contracts/: from the local-inference-deck checkout above"
  else
    identity agent-judge "$judge" "${judge_paths[@]}"
  fi
} > "$root/evals/tests/fixtures/contracts/SOURCES"
echo "vendor-contracts: $diffs updated; wrote evals/tests/fixtures/contracts/SOURCES"
