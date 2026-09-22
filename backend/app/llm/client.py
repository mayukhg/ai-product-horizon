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


def _tier_endpoint(tier: ModelTier) -> tuple[str, str, str]:
    if tier == ModelTier.SMART_INTERN:
        return settings.smart_intern_base_url, settings.smart_intern_model, settings.smart_intern_api_key
    if tier == ModelTier.PHD_REASONER:
        if not settings.openrouter_configured:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY is required for PhD Reasoner tasks. "
                "Set it in backend/.env and LLM_MODE=live, or use LLM_MODE=mock for offline runs."
            )
        return settings.openrouter_base_url, settings.phd_reasoner_model, settings.openrouter_api_key
    if tier == ModelTier.JUDGE:
        if not settings.openrouter_configured:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY is required for cross-family judge evals. "
                "Set OPENROUTER_API_KEY in backend/.env."
            )
        return settings.openrouter_base_url, settings.judge_model, settings.openrouter_api_key
    if tier == ModelTier.GUARDRAIL:
        return settings.guardrail_base_url, settings.guardrail_model, settings.guardrail_api_key
    if tier == ModelTier.EMBEDDING:
        return settings.embedding_base_url, settings.embedding_model, settings.embedding_api_key
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
    # Deterministic 384-dim pseudo-embedding for mock mode
    seed = sum(ord(c) for c in text[:256])
    vector = [round(((seed * (i + 1)) % 1000) / 1000.0 - 0.5, 6) for i in range(384)]
    return EmbeddingResponse(vector=vector, model="mock/nomic-embed-text", latency_ms=5)


async def chat_completion(
    tier: ModelTier,
    messages: list[ChatMessage],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> LLMResponse:
    if not settings.is_live_llm:
        return _mock_chat_response(tier, messages)

    base_url, model, api_key = _tier_endpoint(tier)
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {"Authorization": f"Bearer {api_key}"}
    if tier in (ModelTier.PHD_REASONER, ModelTier.JUDGE):
        headers["HTTP-Referer"] = "https://github.com/mayukhg/ai-product-horizon"
        headers["X-Title"] = "HorizonAI CyberRisk Resident"

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
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

    base_url, model, api_key = _tier_endpoint(ModelTier.EMBEDDING)
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/embeddings",
            json={"model": model, "input": text},
            headers={"Authorization": f"Bearer {api_key}"},
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
