# Architecture

`medimage-eval` is the evaluation substrate intended for every GOATnote medical imaging model release. Only the dual-judge layer and the stats primitives exist today; the panels and the attestation layer are planned (see README and STATUS.md). The substrate is consumed by two model repos under a stable Python API: `medimage-model` (commercial-OK) and `medimage-model-research` (NC-constrained).

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Model card + Merkle attestation (receipts integration)      │
├─────────────────────────────────────────────────────────────┤
│  Panel A: benchmarks   │ Panel B: shift gauntlet (CSGG)      │
│                        │ Panel C: physician adjudication     │
├─────────────────────────────────────────────────────────────┤
│  Dual-judge runner (Cohen's κ floor, Wilson CI, disagreement │
│  gating) — claude-opus-4-7 + gpt-5.4 + optional Meditron     │
├─────────────────────────────────────────────────────────────┤
│  Primitives: cohens_kappa, wilson_ci, calibration ECE         │
└─────────────────────────────────────────────────────────────┘
```

## Public API stability
The judge runner contract and the stats primitives are stable surfaces. Internal layouts of benchmark adapters can change between minor versions.

## Why a separate repo
Model results are only as trustworthy as the eval rig that produced them. Extracting the substrate as its own package gives:

1. **Cross-model reuse** — same substrate runs the commercial and research models.
2. **Community adoption** — `pip install medimage-eval` is consumable by any open-source medical imaging project. Adopting one shared substrate is how the community gets comparable model cards.
3. **License clarity** — substrate is fully Apache 2.0, no data-license entanglement.
