"""Dual-judge clinical-accuracy runner with Cohen's kappa and Wilson CI.

This is the core moat: every free-text clinical output the substrate evaluates
goes through TWO independent judges. Per-item agreement is computed; per-batch
Cohen's kappa is computed; the runner can REJECT a batch's reward signal when
inter-judge kappa falls below a configured floor.

The reward-signal rejection is non-optional. The healthcraft V9 lesson —
judge hallucination is the binding ceiling — is what this guards against.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from medimage_eval.judges.base import Judge, JudgeQuery, JudgeVerdict
from medimage_eval.reporting.stats import cohens_kappa, wilson_ci


@dataclass(frozen=True)
class DualJudgeItem:
    """Aligned verdicts for a single eval item."""

    prompt_id: str
    primary: JudgeVerdict
    secondary: JudgeVerdict

    @property
    def agree(self) -> bool:
        return self.primary.label == self.secondary.label


@dataclass(frozen=True)
class DualJudgeResult:
    """Aggregated dual-judge outcome over a batch.

    Attributes:
        items: per-item verdicts.
        primary_pass_rate: fraction of items the primary judge labelled 1.
        secondary_pass_rate: fraction of items the secondary judge labelled 1.
        primary_pass_rate_ci: Wilson 95% CI for primary_pass_rate.
        secondary_pass_rate_ci: Wilson 95% CI for secondary_pass_rate.
        kappa: Cohen's kappa between the two judges over the batch.
        agreement_rate: simple fraction of items where labels matched.
        kappa_floor: the floor that was checked.
        reward_signal_accepted: True if kappa met or exceeded the floor.
    """

    items: list[DualJudgeItem] = field(default_factory=list)
    primary_pass_rate: float = 0.0
    secondary_pass_rate: float = 0.0
    primary_pass_rate_ci: tuple[float, float] = (0.0, 0.0)
    secondary_pass_rate_ci: tuple[float, float] = (0.0, 0.0)
    kappa: float = 0.0
    agreement_rate: float = 0.0
    kappa_floor: float = 0.0
    reward_signal_accepted: bool = False

    @property
    def n_items(self) -> int:
        return len(self.items)


class DualJudge:
    """Runs two judges over a stream of queries and aggregates."""

    DEFAULT_KAPPA_FLOOR = 0.6  # substantial agreement (Landis & Koch 1977)

    def __init__(
        self,
        primary: Judge,
        secondary: Judge,
        *,
        kappa_floor: float = DEFAULT_KAPPA_FLOOR,
    ) -> None:
        if primary.model_id == secondary.model_id:
            raise ValueError(
                "primary and secondary judges must be distinct models; got "
                f"both = {primary.model_id!r}"
            )
        if not 0.0 <= kappa_floor <= 1.0:
            raise ValueError("kappa_floor must be in [0, 1]")
        self.primary = primary
        self.secondary = secondary
        self.kappa_floor = kappa_floor

    def evaluate(self, queries: Iterable[JudgeQuery]) -> DualJudgeResult:
        items: list[DualJudgeItem] = []
        for q in queries:
            p = self.primary.grade(q)
            s = self.secondary.grade(q)
            if p.prompt_id != q.prompt_id or s.prompt_id != q.prompt_id:
                raise RuntimeError(
                    f"judge returned verdict for the wrong prompt_id: "
                    f"q={q.prompt_id!r} p={p.prompt_id!r} s={s.prompt_id!r}"
                )
            items.append(DualJudgeItem(prompt_id=q.prompt_id, primary=p, secondary=s))
        return self._aggregate(items)

    def _aggregate(self, items: Sequence[DualJudgeItem]) -> DualJudgeResult:
        n = len(items)
        if n == 0:
            # Empty batch: a degenerate but real case. Return zeros + rejected reward.
            return DualJudgeResult(items=[], kappa_floor=self.kappa_floor)

        primary_labels = [it.primary.label for it in items]
        secondary_labels = [it.secondary.label for it in items]

        primary_pass = sum(primary_labels)
        secondary_pass = sum(secondary_labels)
        primary_rate = primary_pass / n
        secondary_rate = secondary_pass / n
        primary_ci = wilson_ci(primary_pass, n)
        secondary_ci = wilson_ci(secondary_pass, n)

        kappa = cohens_kappa(primary_labels, secondary_labels)
        agree = sum(1 for it in items if it.agree) / n
        accepted = kappa >= self.kappa_floor

        return DualJudgeResult(
            items=list(items),
            primary_pass_rate=primary_rate,
            secondary_pass_rate=secondary_rate,
            primary_pass_rate_ci=primary_ci,
            secondary_pass_rate_ci=secondary_ci,
            kappa=kappa,
            agreement_rate=agree,
            kappa_floor=self.kappa_floor,
            reward_signal_accepted=accepted,
        )
