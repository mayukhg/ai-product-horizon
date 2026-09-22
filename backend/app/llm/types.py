from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tier: str
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    vector: list[float]
    model: str
    latency_ms: int
