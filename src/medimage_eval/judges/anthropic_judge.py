"""AnthropicJudge — Claude Opus 4.7 wrapper that implements the `Judge` Protocol.

Design notes (per the claude-api guidance):

* Default model is `claude-opus-4-7`. The model ID is the bare alias — do not
  append a date suffix.
* Opus 4.7 removes `temperature`, `top_p`, `top_k`, and `budget_tokens`. We
  pass none of them. Adaptive thinking is off by default on 4.7 (matches
  4.6 behaviour) — we leave it off for grading because the rubric is short
  and we want deterministic-ish judgments.
* The system prompt is sent with `cache_control: {type: "ephemeral"}` so it
  caches across the many calls a single eval run makes. Below the 4096-token
  cache minimum, the marker is silently inert — it costs nothing and starts
  paying off once the rubric grows.
* Structured outputs via `output_config.format` (not a prefill — prefills
  400 on Opus 4.7).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from medimage_eval.judges.base import JudgeQuery, JudgeVerdict
from medimage_eval.judges.clinical_prompts import (
    DEFAULT_CLINICAL_GRADING_PROMPT,
    build_user_message,
)
from medimage_eval.judges.decision import GRADING_DECISION_SCHEMA, parse_decision_text

if TYPE_CHECKING:
    import anthropic

DEFAULT_MODEL_ID = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 400
DEFAULT_TIMEOUT_SECONDS = 30.0


class JudgeAPIError(RuntimeError):
    """Raised when the underlying provider returned a non-retryable error."""


class AnthropicJudge:
    """Adapter from the Anthropic SDK to the `Judge` Protocol.

    Args:
        model_id: Anthropic model ID. Defaults to ``"claude-opus-4-7"``.
        system_prompt: Override the default clinical-grading rubric.
        max_tokens: Output cap. Grading responses are short, so 400 is plenty.
        timeout_seconds: Per-request timeout. Fails fast if a judge call hangs.
        client: Inject an ``anthropic.Anthropic`` (or test double). When None,
            a default client is constructed lazily on first ``grade`` call.
    """

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        system_prompt: str = DEFAULT_CLINICAL_GRADING_PROMPT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: anthropic.Anthropic | None = None,
    ) -> None:
        if not model_id:
            raise ValueError("model_id is required")
        self.model_id = model_id
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._timeout_seconds = timeout_seconds
        self._client = client

    def _ensure_client(self) -> anthropic.Anthropic:
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - import failure path
            raise RuntimeError(
                "anthropic SDK is not installed. Install with `pip install medimage-eval[judges]`."
            ) from exc
        self._client = anthropic.Anthropic(timeout=self._timeout_seconds)
        return self._client

    def grade(self, query: JudgeQuery) -> JudgeVerdict:
        client = self._ensure_client()
        try:
            response = client.messages.create(
                model=self.model_id,
                max_tokens=self._max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": self._system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": build_user_message(
                            gold=query.gold,
                            candidate=query.candidate,
                            instructions=query.instructions,
                        ),
                    }
                ],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": GRADING_DECISION_SCHEMA,
                    }
                },
            )
        except Exception as exc:
            raise JudgeAPIError(f"anthropic judge call failed: {exc}") from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise JudgeAPIError(
                f"judge refused to grade prompt_id={query.prompt_id}: "
                f"{getattr(response, 'stop_details', None)}"
            )

        text = _extract_first_text_block(response)
        label, rationale = parse_decision_text(text)
        return JudgeVerdict(
            prompt_id=query.prompt_id,
            label=label,
            rationale=rationale,
            raw=text,
        )


def _extract_first_text_block(response: Any) -> str:
    content = getattr(response, "content", None)
    if not content:
        raise JudgeAPIError("anthropic response had no content blocks")
    for block in content:
        if getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if text:
                return text
    raise JudgeAPIError("anthropic response had no non-empty text block")
