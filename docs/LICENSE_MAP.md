# License map

## This repository

| Component | License |
|---|---|
| Code | Apache License 2.0 |
| Documentation | Apache License 2.0 |
| Test fixtures | Apache License 2.0 (no embedded clinical data) |

## Consumed model APIs (judges)

The substrate **calls** judge APIs; it does not redistribute their weights or outputs by default.

| Judge | License of API | Notes |
|---|---|---|
| `claude-opus-4-7` | Anthropic commercial terms | Pay-per-use; tier governed by your API key |
| `gpt-5.4` | OpenAI commercial terms | Pay-per-use |
| Meditron-class (optional) | Apache 2.0 / MIT (varies) | Open-weights, can run locally |

Outputs of judge calls (the per-trajectory rationale text) inherit the API provider's terms. Store with care; never publish raw judge outputs that contain user-identifying or protected data.

## Downstream consumers

This substrate is consumed by:
- [`medimage-model`](https://github.com/GOATnote-Inc/medimage-model) — Apache 2.0 code + commercial-OK weights
- [`medimage-model-research`](https://github.com/GOATnote-Inc/medimage-model-research) — Apache 2.0 code + research-only weights

The substrate does not propagate any license constraint downstream. Each consumer is responsible for its own data and weight licensing.
