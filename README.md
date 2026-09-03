# medimage-eval

**An open evaluation substrate for medical imaging AI.**


> **Maintenance status (2026-09):** passive. This repository is kept available as a reference implementation; CI runs on pushes and pull requests only, Dependabot security alerts remain enabled, and no scheduled jobs or hosted services consume ongoing resources. No active development is planned.

`medimage-eval` aims to be a shared evaluation layer for medical imaging models: standard benchmarks, cross-site generalization, dual-judge clinical accuracy, physician adjudication, and receipted eval runs under one contract.

> Status: pre-v0.1 scaffold. The dual-judge core is implemented and hermetically tested; most of the surface described below is planned, not built. See STATUS.md for the precise, dated state.

## Implemented (v0.1)

- **Dual-judge clinical accuracy** — two independent judges per item, per-batch Cohen's κ with a configurable floor, Wilson 95% CI, and reward-signal rejection on judge disagreement (`judges/dual_judge.py`, `reporting/stats.py`). Stats primitives are pinned to textbook values in tests.
- **Live judge adapters** — `AnthropicJudge` and `OpenAIJudge` implementing the `Judge` protocol, fail-closed on refusals, auth errors, and unparseable verdicts. Tested via injected stubs; no real judge call has been made from this repo's test suite.
- **Judge-key preflight** — a canary request per provider before any long run, strict by default: missing keys or zero canaries attempted is a failure (`judges/preflight.py`).

## Planned (not yet built)

These exist today only as empty package stubs and protocol documents:

- **Cross-site / cross-scanner / cross-population gauntlet** with a CSGG (Cross-Site Generalization Gap) headline score (`shift_gauntlet/` — v0.2, in progress)
- **Physician adjudication harness** for blind hard-case review with κ vs consensus (`adjudication/`; protocol targets in `docs/EVAL_PROTOCOL.md`)
- **Calibration ECE + abstention reporting** (`benchmarks/`)
- **Receipted eval runs** — per-run attestation for the [receipts](https://github.com/GOATnote-Inc/receipts) ledger (`receipts/`)
- **Model-card generator** consuming all panels

No end-to-end evaluation of a real model has been run with this substrate yet.

## What this is not

- It is not a benchmark suite by itself. It runs benchmarks defined elsewhere (BraTS, MIMIC-CXR, etc.) under a uniform contract.
- It is not a clinical decision tool. It evaluates models that should not be clinically used without a separate clearance process.

## Install

Not yet on PyPI. Install from source, pinned to a tag:

```bash
pip install git+https://github.com/GOATnote-Inc/medimage-eval.git@v0.1.0.dev0
```

## Preflight before long runs

```bash
export ANTHROPIC_API_KEY=...   # primary judge
export OPENAI_API_KEY=...      # secondary judge
python -m medimage_eval.judges.preflight
```

The preflight is strict by default: it exits non-zero when a key is missing or when no canary request could be attempted. Pass `--allow-missing` for local development without keys.

## Related repos

[`medimage-model`](https://github.com/GOATnote-Inc/medimage-model) (commercial-OK track) and [`medimage-model-research`](https://github.com/GOATnote-Inc/medimage-model-research) (NC research track) are the intended consumers.

## License

Code: Apache License 2.0. Outputs of judge runs may carry the licenses of the underlying judge model APIs.
