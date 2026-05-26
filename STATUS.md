# STATUS

## Active task
**v0.2 — shift gauntlet + CSGG headline reporter.** The dual-judge core and the live judges are merged. Next is the cross-site generalization gauntlet — the substrate's most distinctive deliverable, and the headline metric every model card needs.

## Exit criteria for current pickup
- `src/medimage_eval/shift_gauntlet/runner.py` exposes `ShiftGauntlet.evaluate(...)` that stratifies a dataset by configurable axes (site, scanner, demographic) and produces per-stratum + worst-case CSGG metrics with Wilson 95% CI
- `src/medimage_eval/reporting/csgg.py` renders the headline number into a model-card section
- Hermetic test pinning the metric on a synthetic two-strata dataset
- `make lint` green; `make test` green

## Verify command
```
make lint && make test
```

## Already shipped (do not re-do)
- **PR #1** — `cohens_kappa`, `wilson_ci` (textbook-pinned), `DualJudge` runner with κ-floor reward rejection, judge-key preflight (length-only)
- **PR #2** — `AnthropicJudge` (claude-opus-4-7, no temperature/budget_tokens, prompt caching on system prompt), `OpenAIJudge` (gpt-5.4, max_completion_tokens), lenient JSON decision parser, real canary preflight that fail-fasts on 401

## Next-up after this pickup
1. Physician adjudication harness (`adjudication/`) — blind hard-case scoring with κ vs consensus
2. Receipts attestation writer (`receipts/attestation.py`) — Merkle leaf per eval run
3. Model-card generator consuming all three panels
4. Integration tests gated on real judge keys (skip when absent)

## Known constraints
- All tests must remain hermetic — judge calls go through injected stubs, not the live SDK
- `cache_control: {"type": "ephemeral"}` stays on the Anthropic system prompt; below 4096 tokens it's silently inert, above it pays off
- Branch protection on this repo is **NOT** yet enabled (follow-up: add the four-context baseline once shift_gauntlet ships)

## Last updated
2026-05-26 — end of scaffolding + live-judges session (PRs #1, #2 merged)
