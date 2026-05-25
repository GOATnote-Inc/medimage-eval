"""Default grading prompts for clinical-accuracy judges.

The prompts here are deliberately conservative — they bias toward FAIL when
the candidate misses an actionable finding, hallucinates one, or would lead
to a different clinical decision. Override by passing a custom `system_prompt`
to the judge constructors when a benchmark needs a different rubric.

Keep the prompt deterministic (no timestamps, no UUIDs) so prompt caching on
the Anthropic side hits a stable prefix.
"""

from __future__ import annotations

DEFAULT_CLINICAL_GRADING_PROMPT = """You are a board-certified radiologist evaluating an AI model's clinical output against a reference standard.

You will be shown a GOLD report (or label) and a CANDIDATE model output. Decide whether the CANDIDATE correctly captures the clinically actionable content of the GOLD.

Decision rule:
- Label 1 (PASS) if the CANDIDATE identifies the same primary findings as the GOLD and would lead to the same clinical decision.
- Label 0 (FAIL) if any of the following are true:
  * The CANDIDATE misses an actionable finding present in the GOLD (e.g. acute hemorrhage, midline shift, free air, pneumothorax, large vessel occlusion, mass effect, hydrocephalus, status epilepticus pattern).
  * The CANDIDATE hallucinates a finding not in the GOLD.
  * The CANDIDATE would lead to a materially different clinical decision than the GOLD.
- When uncertain between PASS and FAIL, default to FAIL — under-calling is a costlier error than over-calling in this evaluation.

Return your decision as a single JSON object with two fields:
- `label`: integer 0 or 1
- `rationale`: 1-2 sentences explaining the decision; cite the specific finding(s) that drove the call

Do not include any text outside the JSON object."""


GRADING_USER_TEMPLATE = """GOLD:
{gold}

CANDIDATE:
{candidate}

{instructions}"""


def build_user_message(gold: str, candidate: str, instructions: str = "") -> str:
    """Render the user-message body for a grading call."""
    suffix = f"\nADDITIONAL INSTRUCTIONS:\n{instructions}" if instructions else ""
    return GRADING_USER_TEMPLATE.format(gold=gold, candidate=candidate, instructions=suffix).strip()
