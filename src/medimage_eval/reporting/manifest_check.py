"""CI-gate manifest determinism check.

Verifies that the package version matches `pyproject.toml`, that the package
exports its public-API symbols, and that the directory layout matches the
expected substrate shape. Run by the `manifest-determinism` CI job.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import medimage_eval
from medimage_eval.reporting import cohens_kappa, wilson_ci

REQUIRED_SUBPACKAGES = (
    "judges",
    "benchmarks",
    "shift_gauntlet",
    "adjudication",
    "reporting",
    "receipts",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> int:
    root = _repo_root()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        print(f"missing {pyproject}", file=sys.stderr)
        return 1

    with pyproject.open("rb") as fh:
        meta = tomllib.load(fh)
    declared = meta["project"]["version"]
    if declared != medimage_eval.__version__:
        print(
            f"version mismatch: pyproject={declared!r} package={medimage_eval.__version__!r}",
            file=sys.stderr,
        )
        return 2

    pkg_dir = root / "src" / "medimage_eval"
    missing = [name for name in REQUIRED_SUBPACKAGES if not (pkg_dir / name).is_dir()]
    if missing:
        print(f"missing subpackages: {missing}", file=sys.stderr)
        return 3

    # smoke the primitives so this also acts as a basic import-graph check
    if not (callable(cohens_kappa) and callable(wilson_ci)):
        print("reporting primitives not callable", file=sys.stderr)
        return 4

    print(f"medimage_eval {medimage_eval.__version__} manifest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
