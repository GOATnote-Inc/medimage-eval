"""Judge orchestration: dual-judge clinical accuracy with κ floor.

The Anthropic and OpenAI adapters are lazily importable — calling them
without the optional SDK installed raises only when constructed, not when
the package is imported.
"""

from medimage_eval.judges.anthropic_judge import AnthropicJudge, JudgeAPIError
from medimage_eval.judges.base import Judge, JudgeQuery, JudgeVerdict
from medimage_eval.judges.decision import (
    GRADING_DECISION_SCHEMA,
    DecisionParseError,
    parse_decision_text,
)
from medimage_eval.judges.dual_judge import DualJudge, DualJudgeItem, DualJudgeResult
from medimage_eval.judges.openai_judge import OpenAIJudge

__all__ = [
    "GRADING_DECISION_SCHEMA",
    "AnthropicJudge",
    "DecisionParseError",
    "DualJudge",
    "DualJudgeItem",
    "DualJudgeResult",
    "Judge",
    "JudgeAPIError",
    "JudgeQuery",
    "JudgeVerdict",
    "OpenAIJudge",
    "parse_decision_text",
]
