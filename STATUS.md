# STATUS

## Active task
**Bootstrap v0.1 substrate.** Land the dual-judge runner + Cohen's κ + Wilson CI core. Make `make test` green on a hermetic smoke run.

## Exit criteria for current pickup
- `make lint` green
- `make test` green (hermetic, no network)
- `src/medimage_eval/judges/dual_judge.py` exposes `DualJudge.evaluate(...)` returning `{primary_score, secondary_score, kappa, agree, wilson_ci}`
- `src/medimage_eval/reporting/stats.py` exposes `cohens_kappa(...)` and `wilson_ci(...)` matching textbook test cases

## Verify command
```
make lint && make test
```

## Next-up after pickup
1. Cross-site gauntlet module skeleton (`shift_gauntlet/`).
2. Physician adjudication harness scaffold (`adjudication/`).
3. CSGG headline-metric reporter.
4. Receipts attestation writer.

## Known blockers
None.

## Last updated
2026-05-25 — initial scaffold
