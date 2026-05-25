"""Tests for the judge preflight (env-var check + canary calls)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from medimage_eval.judges.preflight import (
    CanaryResult,
    _is_auth_error,
    run_preflight,
)


def _reload_module():
    if "medimage_eval.judges.preflight" in sys.modules:
        del sys.modules["medimage_eval.judges.preflight"]
    from medimage_eval.judges import preflight

    return preflight


def test_preflight_passes_with_keys_and_no_canary(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-1234567890abcdef")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-0987654321")
    rc = run_preflight(strict=False, canary=False)
    out = capsys.readouterr().out
    assert rc == 0
    assert "ANTHROPIC_API_KEY" in out
    assert "sk-ant-fake-1234567890abcdef" not in out
    assert "skipped" in out.lower()


def test_preflight_warns_without_keys_when_not_strict(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    rc = run_preflight(strict=False, canary=False)
    captured = capsys.readouterr()
    assert rc == 0  # warning mode: missing keys do not block
    assert "Missing judge API keys" in captured.err


def test_preflight_fails_without_keys_when_strict(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    rc = run_preflight(strict=True, canary=False)
    assert rc == 3


def test_preflight_runs_injected_canaries_and_returns_zero_on_success(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    canaries = {
        "anthropic": lambda: CanaryResult("anthropic", True, "canary OK"),
        "openai": lambda: CanaryResult("openai", True, "canary OK"),
    }
    rc = run_preflight(strict=False, canary=True, canaries=canaries)
    out = capsys.readouterr().out
    assert rc == 0
    assert "judge keys verified" in out


def test_preflight_fails_on_auth_error_from_canary(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-bad")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    canaries = {
        "anthropic": lambda: CanaryResult("anthropic", False, "401 Unauthorized", auth_failed=True),
        "openai": lambda: CanaryResult("openai", True, "canary OK"),
    }
    rc = run_preflight(strict=False, canary=True, canaries=canaries)
    captured = capsys.readouterr()
    assert rc == 2
    assert "FAIL-AUTH" in captured.out
    assert "authentication error" in captured.err


def test_preflight_skips_canary_for_provider_without_key(monkeypatch, capsys):
    """If only one key is set, only that provider's canary runs."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    seen: list[str] = []

    def anthropic_canary():
        seen.append("anthropic")
        return CanaryResult("anthropic", True, "canary OK")

    def openai_canary():
        seen.append("openai")
        return CanaryResult("openai", True, "canary OK")

    canaries = {"anthropic": anthropic_canary, "openai": openai_canary}
    rc = run_preflight(strict=False, canary=True, canaries=canaries)
    out = capsys.readouterr().out
    assert rc == 0
    assert seen == ["anthropic"]
    assert "SKIP" in out and "openai" in out


# ---- _is_auth_error detection ------------------------------------------------


@dataclass
class _FakeAuthError(Exception):
    """Stand-in for SDK-specific AuthenticationError types."""


_FakeAuthError.__name__ = "AuthenticationError"


@dataclass
class _FakeStatusError(Exception):
    status_code: int = 401


def test_is_auth_error_detects_by_class_name():
    assert _is_auth_error("anthropic", _FakeAuthError()) is True


def test_is_auth_error_detects_by_status_code():
    err = _FakeStatusError(status_code=401)
    assert _is_auth_error("openai", err) is True


def test_is_auth_error_detects_by_message_substring():
    err = RuntimeError("server returned 401 Unauthorized")
    assert _is_auth_error("openai", err) is True


def test_is_auth_error_returns_false_for_unrelated_exception():
    assert _is_auth_error("anthropic", ValueError("connection reset")) is False
