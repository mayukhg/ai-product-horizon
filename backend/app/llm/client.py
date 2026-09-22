from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from app.config import settings
from app.llm.router import ModelTier
from app.llm.types import ChatMessage, EmbeddingResponse, LLMResponse


class LLMConfigurationError(RuntimeError):
    pass


def _require_openrouter() -> None:
    if not settings.openrouter_configured:
        raise LLMConfigurationError(
            "OPENROUTER_API_KEY is required when LLM_MODE=live. "
            "Set OPENROUTER_API_KEY in backend/.env, or use LLM_MODE=mock for offline runs."
        )


def _openrouter_headers() -> dict[str, str]:
    _require_openrouter()
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }


def _tier_model(tier: ModelTier) -> str:
    if tier == ModelTier.SMART_INTERN:
        return settings.smart_intern_model
    if tier == ModelTier.PHD_REASONER:
        return settings.phd_reasoner_model
    if tier == ModelTier.JUDGE:
        return settings.judge_model
    if tier == ModelTier.GUARDRAIL:
        return settings.guardrail_model
    if tier == ModelTier.EMBEDDING:
        return settings.embedding_model
    raise ValueError(f"Unknown tier: {tier}")


def _mock_chat_response(tier: ModelTier, messages: list[ChatMessage]) -> LLMResponse:
    user_text = next((m.content for m in reversed(messages) if m.role == "user"), "")
    if tier == ModelTier.GUARDRAIL:
        blocked = any(
            phrase in user_text.upper()
            for phrase in ("IGNORE ALL PREVIOUS", "DROP TABLE", "API CREDENTIALS", "BYPASS HITL")
        )
        content = "unsafe" if blocked else "safe"
    elif tier == ModelTier.JUDGE:
        content = json.dumps({"groundedness": 0.94, "reasoning": "Mock judge: output aligns with reference."})
    elif tier == ModelTier.PHD_REASONER:
        content = json.dumps(
            {
                "attack_path_summary": "Attacker chains initial access CVE with privilege escalation vector.",
                "primary_mitigation": "Isolate affected gateway, patch primary CVE, then secondary.",
                "reasoning_depth": "High",
            }
        )
    else:
        content = json.dumps(
            {
                "cve_id": "CVE-2024-3094",
                "severity": "CRITICAL",
                "recommended_action": "Apply security update and restart affected services.",
                "tru_risk_score": 92,
                "requires_hitl": True,
            }
        )
    return LLMResponse(content=content, model=f"mock/{tier.value}", tier=tier.value, latency_ms=12)


def _mock_embedding(text: str) -> EmbeddingResponse:
    dims = settings.embedding_dimensions
    seed = sum(ord(c) for c in text[:256])
    vector = [round(((seed * (i + 1)) % 1000) / 1000.0 - 0.5, 6) for i in range(dims)]
    return EmbeddingResponse(vector=vector, model=f"mock/{settings.embedding_model}", latency_ms=5)


async def chat_completion(
    tier: ModelTier,
    messages: list[ChatMessage],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> LLMResponse:
    if not settings.is_live_llm:
        return _mock_chat_response(tier, messages)

    model = _tier_model(tier)
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=_openrouter_headers(),
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = int((time.perf_counter() - started) * 1000)
    choice = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return LLMResponse(
        content=choice,
        model=data.get("model", model),
        tier=tier.value,
        latency_ms=latency_ms,
        prompt_tokens=int(usage.get("prompt_tokens", 0)),
        completion_tokens=int(usage.get("completion_tokens", 0)),
        raw=data,
    )


async def embed_text(text: str) -> EmbeddingResponse:
    if not settings.is_live_llm:
        return _mock_embedding(text)

    model = _tier_model(ModelTier.EMBEDDING)
    payload: dict[str, Any] = {
        "model": model,
        "input": text,
        "dimensions": settings.embedding_dimensions,
    }

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/embeddings",
            json=payload,
            headers=_openrouter_headers(),
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = int((time.perf_counter() - started) * 1000)
    vector = data["data"][0]["embedding"]
    return EmbeddingResponse(vector=vector, model=data.get("model", model), latency_ms=latency_ms)


def extract_json_payload(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
