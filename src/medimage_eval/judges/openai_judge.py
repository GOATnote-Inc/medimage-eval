"""OpenAIJudge — GPT-5.4 wrapper that implements the `Judge` Protocol.

Notes:

* GPT-5.4 requires ``max_completion_tokens``, not the legacy ``max_tokens``.
  Sending ``max_tokens`` is silently ignored / rejected depending on the model
  (see scribegoat2 incident memory). We use the correct name.
* Structured outputs via ``response_format`` with a JSON schema.
* OpenAI applies prompt caching automatically for prefixes ≥ 1024 tokens.
  No explicit annotation is needed; the only thing under our control is
  keeping the system prompt deterministic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from medimage_eval.judges.anthropic_judge import JudgeAPIError
from medimage_eval.judges.base import JudgeQuery, JudgeVerdict
from medimage_eval.judges.clinical_prompts import (
    DEFAULT_CLINICAL_GRADING_PROMPT,
    build_user_message,
)
from medimage_eval.judges.decision import GRADING_DECISION_SCHEMA, parse_decision_text

if TYPE_CHECKING:
    import openai

DEFAULT_MODEL_ID = "gpt-5.4"
DEFAULT_MAX_COMPLETION_TOKENS = 400
DEFAULT_TIMEOUT_SECONDS = 30.0


class OpenAIJudge:
    """Adapter from the OpenAI SDK to the `Judge` Protocol.

    Args:
        model_id: OpenAI model ID. Defaults to ``"gpt-5.4"``.
        system_prompt: Override the default clinical-grading rubric.
        max_completion_tokens: Output cap. Note: the parameter name is
            ``max_completion_tokens``, not ``max_tokens`` — GPT-5+ rejects
            the legacy name.
        timeout_seconds: Per-request timeout.
        client: Inject an ``openai.OpenAI`` (or test double). When None,
            a default client is constructed lazily on first ``grade`` call.
    """

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        system_prompt: str = DEFAULT_CLINICAL_GRADING_PROMPT,
        max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: openai.OpenAI | None = None,
    ) -> None:
        if not model_id:
            raise ValueError("model_id is required")
        self.model_id = model_id
        self._system_prompt = system_prompt
        self._max_completion_tokens = max_completion_tokens
        self._timeout_seconds = timeout_seconds
        self._client = client

    def _ensure_client(self) -> openai.OpenAI:
        if self._client is not None:
            return self._client
        try:
            import openai
        except ImportError as exc:  # pragma: no cover - import failure path
            raise RuntimeError(
                "openai SDK is not installed. Install with `pip install medimage-eval[judges]`."
            ) from exc
        self._client = openai.OpenAI(timeout=self._timeout_seconds)
        return self._client

    def grade(self, query: JudgeQuery) -> JudgeVerdict:
        client = self._ensure_client()
        try:
            response = client.chat.completions.create(
                model=self.model_id,
                max_completion_tokens=self._max_completion_tokens,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {
                        "role": "user",
                        "content": build_user_message(
                            gold=query.gold,
                            candidate=query.candidate,
                            instructions=query.instructions,
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "grading_decision",
                        "strict": True,
                        "schema": GRADING_DECISION_SCHEMA,
                    },
                },
            )
        except Exception as exc:
            raise JudgeAPIError(f"openai judge call failed: {exc}") from exc

        text = _extract_first_message_content(response)
        label, rationale = parse_decision_text(text)
        return JudgeVerdict(
            prompt_id=query.prompt_id,
            label=label,
            rationale=rationale,
            raw=text,
        )


def _extract_first_message_content(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not choices:
        raise JudgeAPIError("openai response had no choices")
    message = getattr(choices[0], "message", None)
    if message is None:
        raise JudgeAPIError("openai response choice had no message")
    content = getattr(message, "content", None)
    if not content:
        raise JudgeAPIError("openai response message had empty content")
    return content
