"""Pre-flight check for judge API keys.

Silent 401s from a judge provider during a multi-hour run poison every reward
signal in the run — every trajectory comes back labelled 0, the resume cannot
detect it, and the entire run is wasted. This pre-flight makes a tiny, one-token
canary request against each configured provider before any long run starts.

Run via `make preflight` or `python -m medimage_eval.judges.preflight`.
"""

from __future__ import annotations

import os
import sys

REQUIRED_ENV_VARS = (
    ("ANTHROPIC_API_KEY", "claude-opus-4-7"),
    ("OPENAI_API_KEY", "gpt-5.4"),
)


def main() -> int:
    missing: list[str] = []
    for var, label in REQUIRED_ENV_VARS:
        value = os.environ.get(var, "")
        if not value:
            missing.append(f"{var} (used by {label})")
            continue
        # Length-only check — never echo the value itself.
        print(f"OK  {var:24s} len={len(value)} (judge: {label})")

    if missing:
        print("", file=sys.stderr)
        print("Missing judge API keys:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print(
            "\nSource your env (e.g. `set -a && source ~/lostbench/.env && set +a`) and re-run.",
            file=sys.stderr,
        )
        return 2

    # TODO(v0.2): make a real canary request against each provider.
    # Held until the live judge implementations land in PR #2.
    print("\nPreflight OK: all judge keys present (canary calls land in v0.2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
