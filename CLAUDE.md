# CLAUDE.md — medimage-eval operating charter

## Mission
Evaluation substrate for open-source medical imaging models. Models come and go; the substrate is what makes results trustworthy.

## Non-negotiables

1. **No `.env` reads.** Judge API keys come from the environment (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`). Verify keys via length-only checks (`awk -F= '/^KEY=/ {print $1, "len:", length($2)}'`); never print values.
2. **Judge pre-flight before any multi-hour run.** Silent 401s poison reward signals: every trajectory scores 0 and the run is wasted.
3. **No `git add -A`.** Stage by name. Evaluation outputs are artifact-class data; treat as immutable.
4. **Pre-commit `exclude` pattern protects `eval_outputs/`, `judge_traces/`, `golden_master/runs/`.**
5. **Reject reward signals when judges disagree beyond κ threshold.** Judge hallucination is the binding ceiling on judge-scored evals.
6. **Deterministic eval runs.** Manifest hash + judge model version + code commit + random seed all logged into the receipt for every run.

## Continuation contract
- Start of session: read `STATUS.md` for the active pickup point and exit criteria.
- End of session: update `STATUS.md` with the next-handoff state. Never leave it stale.

## Test discipline
- Hermetic unit tests in `tests/`. No real judge calls.
- Integration tests in `tests/integration/` are gated by env (real keys); skipped when keys absent.
- Smoke test must pass with no network.

## Receipts
- Every eval run produces `attestation.json` with: code commit, manifest hash, judge versions, results hash, seed.
- Attestations are append-only. Never edit a past attestation.

## Cross-repo
- Consumed by `medimage-model` and `medimage-model-research`. Public API must not break between minor versions without a deprecation window.
