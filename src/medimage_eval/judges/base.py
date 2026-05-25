"""Judge interface and dataclasses shared across implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class JudgeQuery:
    """A single item for a judge to grade.

    `gold` is the reference (ground-truth report, label, or rubric).
    `candidate` is the model output under evaluation.
    `prompt_id` identifies the eval item; used for caching and traceability.
    """

    prompt_id: str
    gold: str
    candidate: str
    instructions: str = ""


@dataclass(frozen=True)
class JudgeVerdict:
    """A judge's per-item decision."""

    prompt_id: str
    label: int  # 0 = fail, 1 = pass (binary by convention; multi-class can extend)
    rationale: str = ""
    raw: str = ""  # full text the judge produced, for trace storage


class Judge(Protocol):
    """A judge is anything that can rate a JudgeQuery."""

    model_id: str

    def grade(self, query: JudgeQuery) -> JudgeVerdict:
        """Return a JudgeVerdict for a single query.

        Implementations are expected to be deterministic given the same
        (model_id, prompt_id, gold, candidate, instructions) tuple, modulo
        provider non-determinism. Caching is the implementation's concern.
        """
        ...
