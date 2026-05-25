# Evaluation protocol

## Three required panels

Every release that uses this substrate must clear all three gates before its model card can be tagged.

### Panel A — Benchmarks
- Standard public benchmarks under uniform contract.
- Reports point estimate + Wilson 95% CI per metric.
- Required: at least one in-distribution benchmark per modality.

### Panel B — Shift gauntlet
- Stratified by site, scanner manufacturer, scanner model, slice thickness, contrast protocol, patient age band, sex, reported ethnicity, BMI band.
- Headline metric: **Cross-Site Generalization Gap (CSGG)** = worst-case degradation across strata, Wilson 95% CI.
- Required: at least three stratification axes covered.

### Panel C — Physician adjudication
- ≥200 stratified hard cases per modality.
- ≥3 blind expert reviewers.
- Cohen's κ vs consensus + κ between physicians (noise floor).
- Gate: model-vs-consensus κ ≥ physician-vs-physician κ minus a small margin.

## Dual-judge clinical accuracy

For free-text outputs (impressions, findings):
- Primary judge: `claude-opus-4-7`
- Secondary judge: `gpt-5.4`
- Optional transparency judge: an open Med-LLM (Meditron-class)
- Inter-judge κ computed per stratum; reward signals **rejected** when below threshold.

## Pre-flight
Before any multi-hour eval run, `make preflight` verifies judge keys against a canary request. Silent 401s poison reward signals — this check is non-negotiable.

## Receipts
Every run produces `attestation.json` with: code commit, manifest hash, judge versions, results hash, seed. Attestations are append-only and chainable into the `receipts` ledger.
