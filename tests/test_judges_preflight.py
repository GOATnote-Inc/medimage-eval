"""Tests for the judge-key preflight."""

from __future__ import annotations

import sys

import pytest


def _reload_preflight():
    """Reload the preflight module so it re-reads os.environ."""
    if "medimage_eval.judges.preflight" in sys.modules:
        del sys.modules["medimage_eval.judges.preflight"]
    from medimage_eval.judges import preflight

    return preflight


def test_preflight_passes_when_keys_set(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-1234567890abcdef")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-0987654321")
    preflight = _reload_preflight()
    rc = preflight.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "Preflight OK" in out
    # Never print the value itself — just confirm length info is shown.
    assert "ANTHROPIC_API_KEY" in out
    assert "sk-ant-fake-1234567890abcdef" not in out


def test_preflight_fails_when_keys_missing(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    preflight = _reload_preflight()
    rc = preflight.main()
    captured = capsys.readouterr()
    assert rc == 2
    assert "Missing judge API keys" in captured.err
