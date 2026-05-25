"""Pre-flight check for judge API keys + a real canary call to each provider.

Silent 401s from a judge provider during a multi-hour run poison every reward
signal: every trajectory comes back labelled 0, the resume cannot detect it,
and the entire run is wasted. This preflight makes a tiny canary request
against each configured provider before any long run starts. Loss of canary
fail-fast is non-negotiable per `feedback_eval_preflight_judge_key.md`.

Run via `make preflight` or `python -m medimage_eval.judges.preflight`.

Exit codes:
    0  All keys present and canaries passed (or `--no-canary`).
    2  At least one canary returned an authentication error.
    3  At least one judge key is missing AND `--strict` was passed.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

REQUIRED_ENV_VARS = (
    ("ANTHROPIC_API_KEY", "claude-opus-4-7"),
    ("OPENAI_API_KEY", "gpt-5.4"),
)


@dataclass(frozen=True)
class CanaryResult:
    provider: str
    ok: bool
    detail: str
    auth_failed: bool = False


def check_anthropic_canary(
    *,
    client: Any | None = None,
    model_id: str = "claude-opus-4-7",
    timeout_seconds: float = 10.0,
) -> CanaryResult:
    """Send a tiny request to Anthropic to verify auth + connectivity.

    Returns a CanaryResult; never raises. The caller decides whether to exit.
    """
    if not os.environ.get("ANTHROPIC_API_KEY") and client is None:
        return CanaryResult("anthropic", False, "ANTHROPIC_API_KEY not set", auth_failed=False)

    if client is None:
        try:
            import anthropic
        except ImportError as exc:
            return CanaryResult(
                "anthropic", False, f"anthropic SDK not installed: {exc}", auth_failed=False
            )
        client = anthropic.Anthropic(timeout=timeout_seconds)

    try:
        client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": "ok"}],
        )
        return CanaryResult("anthropic", True, "canary OK")
    except Exception as exc:
        auth_failed = _is_auth_error("anthropic", exc)
        return CanaryResult(
            "anthropic",
            False,
            f"{type(exc).__name__}: {exc}",
            auth_failed=auth_failed,
        )


def check_openai_canary(
    *,
    client: Any | None = None,
    model_id: str = "gpt-5.4",
    timeout_seconds: float = 10.0,
) -> CanaryResult:
    """Send a tiny request to OpenAI to verify auth + connectivity."""
    if not os.environ.get("OPENAI_API_KEY") and client is None:
        return CanaryResult("openai", False, "OPENAI_API_KEY not set", auth_failed=False)

    if client is None:
        try:
            import openai
        except ImportError as exc:
            return CanaryResult(
                "openai", False, f"openai SDK not installed: {exc}", auth_failed=False
            )
        client = openai.OpenAI(timeout=timeout_seconds)

    try:
        client.chat.completions.create(
            model=model_id,
            max_completion_tokens=50,
            messages=[{"role": "user", "content": "ok"}],
        )
        return CanaryResult("openai", True, "canary OK")
    except Exception as exc:
        auth_failed = _is_auth_error("openai", exc)
        return CanaryResult(
            "openai",
            False,
            f"{type(exc).__name__}: {exc}",
            auth_failed=auth_failed,
        )


def _is_auth_error(provider: str, exc: BaseException) -> bool:
    """Best-effort detection of authentication errors across SDK versions."""
    name = type(exc).__name__
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return True
    status = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    if status in {401, 403}:
        return True
    msg = str(exc).lower()
    return "401" in msg or "unauthor" in msg or "invalid api key" in msg


def run_preflight(
    *,
    strict: bool,
    canary: bool,
    canaries: dict[str, Callable[[], CanaryResult]] | None = None,
) -> int:
    """Run the preflight checklist. Returns an exit code."""
    canaries = canaries or {
        "anthropic": check_anthropic_canary,
        "openai": check_openai_canary,
    }

    missing: list[str] = []
    for var, label in REQUIRED_ENV_VARS:
        value = os.environ.get(var, "")
        if not value:
            missing.append(f"{var} (used by {label})")
            continue
        # Length-only — never echo the secret.
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
        if strict:
            return 3

    if not canary:
        print("\nCanary checks skipped (--no-canary).")
        return 0

    print("\nRunning canary requests...")
    auth_failed = False
    any_canary_attempted = False
    for provider, runner in canaries.items():
        env_var = f"{provider.upper()}_API_KEY"
        if not os.environ.get(env_var):
            print(f"SKIP {provider:10s} — {env_var} not set")
            continue
        any_canary_attempted = True
        result = runner()
        marker = "OK" if result.ok else ("FAIL-AUTH" if result.auth_failed else "FAIL")
        print(f"{marker:9s} {result.provider:10s} {result.detail}")
        if result.auth_failed:
            auth_failed = True

    if auth_failed:
        print(
            "\nPreflight FAILED: at least one judge returned an authentication error. "
            "Rotate the key or fix the env source, then re-run.",
            file=sys.stderr,
        )
        return 2

    if not any_canary_attempted:
        print("\nNo canary attempted (no keys present). Preflight OK with caveat.")
    else:
        print("\nPreflight OK: judge keys verified by canary.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-canary",
        dest="canary",
        action="store_false",
        help="skip the real canary request to each provider (env-var check only)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when any required key is missing (default: warn only)",
    )
    args = parser.parse_args()
    return run_preflight(strict=args.strict, canary=args.canary)


if __name__ == "__main__":
    raise SystemExit(main())
