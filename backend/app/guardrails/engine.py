from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm.client import chat_completion
from app.llm.router import ModelTier
from app.llm.types import ChatMessage

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+all\s+previous\s+instructions", re.I),
    re.compile(r"developer\s+mode\s+enabled", re.I),
    re.compile(r"bypass\s+hitl", re.I),
    re.compile(r"drop\s+table", re.I),
    re.compile(r"api\s+credentials", re.I),
    re.compile(r"system\s+override", re.I),
]


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
    source: str


async def check_input(text: str) -> GuardrailResult:
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return GuardrailResult(
                allowed=False,
                reason=f"Prompt injection pattern detected: {pattern.pattern}",
                source="rules",
            )

    response = await chat_completion(
        ModelTier.GUARDRAIL,
        [
            ChatMessage(role="system", content="Classify the user message as safe or unsafe for cyber operations."),
            ChatMessage(role="user", content=text),
        ],
        temperature=0.0,
        max_tokens=16,
    )
    verdict = response.content.strip().lower()
    if "unsafe" in verdict:
        return GuardrailResult(allowed=False, reason="Guardrail model flagged input as unsafe", source="llama_guard")
    return GuardrailResult(allowed=True, reason="Input passed guardrail checks", source="llama_guard")
