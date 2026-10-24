"""evals/harness.pin holds the sha256 of every HARNESS_FILES entry (evals/run.py). CI fails when a harness file
changes without the pin, so an accidental harness edit (which invalidates every gate baseline and the C1 freeze)
fails before merge. A deliberate re-baseline updates the pin in the same commit:

    python3 -B evals/tests/test_harness_pin.py --write

The pin is not itself a harness file. Baselines record their own harness_sha256 (evals/results/, gitignored).
Run: python3 -m pytest evals/tests/test_harness_pin.py -q -p no:cacheprovider
"""
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PIN = REPO / "evals" / "harness.pin"
HEADER = ("# evals/harness.pin: sha256 of every HARNESS_FILES entry in evals/run.py, one \"<sha256>  <path>\" line\n"
          "# each (sha256sum format, so `sha256sum -c evals/harness.pin` from the repo root also checks it).\n"
          "# Update only with a deliberate harness change, in the same commit:\n"
          "#   python3 -B evals/tests/test_harness_pin.py --write\n")


def harness_files():
    m = re.search(r"^HARNESS_FILES = \((.*?)\)$", (REPO / "evals" / "run.py").read_text(), re.S | re.M)
    assert m, "HARNESS_FILES not found in evals/run.py"
    return re.findall(r'"([^"]+)"', m.group(1))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pin():
    pins = {}
    for line in PIN.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        digest, path = line.split(None, 1)
        assert path not in pins, f"{path} pinned twice"
        pins[path.strip()] = digest
    return pins


def render():
    return HEADER + "".join(f"{sha256(REPO / f)}  {f}\n" for f in harness_files())


def test_pin_lists_exactly_the_harness_files():
    files = harness_files()
    assert files and len(set(files)) == len(files)
    assert sorted(read_pin()) == sorted(files)
    assert "evals/harness.pin" not in files


def test_harness_files_match_the_pin():
    pins = read_pin()
    bad = [f for f in harness_files() if not (REPO / f).is_file() or sha256(REPO / f) != pins.get(f)]
    assert not bad, ("harness files differ from evals/harness.pin: " + ", ".join(bad) + ". An edit here "
                     "invalidates the gate baselines (re-baseline with owner approval) and needs the pin "
                     "updated in the same commit.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        PIN.write_text(render())
        print(f"wrote {PIN.relative_to(REPO)} ({len(harness_files())} files)")
    else:
        sys.exit("usage: python3 -B evals/tests/test_harness_pin.py --write")
