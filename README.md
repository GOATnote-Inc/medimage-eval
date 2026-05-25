# medimage-eval

**An open, hardened evaluation substrate for medical imaging AI.**

`medimage-eval` is the audit-grade evaluation layer for medical imaging models. Any open-source medical imaging model can plug in and produce a complete model card: standard benchmarks + cross-site generalization gauntlet + dual-judge clinical accuracy with Cohen's κ + physician adjudication harness + Merkle-chained receipts.

> Status: pre-v0.1 scaffold. The substrate is the moat of the GOATnote medical imaging stack — see [`medimage-model`](https://github.com/GOATnote-Inc/medimage-model) (commercial-OK reference model) and [`medimage-model-research`](https://github.com/GOATnote-Inc/medimage-model-research) (NC research track).

## What this is

- **Dual-judge clinical accuracy** with Cohen's κ floor, Wilson 95% CI, and judge-disagreement gating
- **Cross-site / cross-scanner / cross-population gauntlet** producing a headline CSGG (Cross-Site Generalization Gap) score
- **Physician adjudication harness** for blind hard-case review with κ vs consensus
- **Calibration ECE + abstention check** so the model card reports more than aggregate accuracy
- **Merkle-chained receipts** so every eval run produces a tamper-evident attestation usable by the [receipts](https://github.com/GOATnote-Inc/receipts) ledger

## What this is not

- It is not a benchmark suite by itself. It runs benchmarks defined elsewhere (BraTS, MIMIC-CXR, etc.) under a uniform contract.
- It is not a clinical decision tool. It evaluates models that should not be clinically used without a separate clearance process.

## Install (when published)

```bash
pip install medimage-eval
```

Until v0.1 lands, install from source:

```bash
pip install git+https://github.com/GOATnote-Inc/medimage-eval.git@main
```

## License

Code: Apache License 2.0. Outputs of judge runs may carry the licenses of the underlying judge model APIs.
