from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.guardrails.engine import check_input
from app.llm.client import chat_completion, extract_json_payload
from app.llm.prompts import EXPLOIT_SYNTHESIS_SYSTEM, JUDGE_SYSTEM, RAG_SYSTEM, TRIAGE_SYSTEM
from app.llm.router import ModelTier, select_tier
from app.llm.types import ChatMessage


@dataclass
class CaseScore:
    case_id: str
    slice: str
    eval_type: str
    groundedness: float
    passed: bool
    detail: str
    latency_ms: int


@dataclass
class EvalSummary:
    total_cases: int
    passed_cases: int
    pass_rate_pct: float
    mean_groundedness: float
    release_blocked: bool
    block_reason: str | None
    case_scores: list[CaseScore]


def _system_prompt_for_case(eval_type: str, slice_name: str) -> str:
    if "exploit" in eval_type or "synthesis" in slice_name.lower():
        return EXPLOIT_SYNTHESIS_SYSTEM
    if "retrieval" in slice_name.lower() or "rag" in eval_type:
        return RAG_SYSTEM
    return TRIAGE_SYSTEM


async def _score_with_judge(case: dict[str, Any], model_output: str) -> float:
    reference = json.dumps(case["expected_output"])
    response = await chat_completion(
        ModelTier.JUDGE,
        [
            ChatMessage(role="system", content=JUDGE_SYSTEM),
            ChatMessage(
                role="user",
                content=(
                    f"Input prompt:\n{case['input_prompt']}\n\n"
                    f"Expected reference:\n{reference}\n\n"
                    f"Model output:\n{model_output}"
                ),
            ),
        ],
        temperature=0.0,
        max_tokens=256,
    )
    payload = extract_json_payload(response.content)
    return float(payload.get("groundedness", 0.0))


async def score_case(case: dict[str, Any]) -> CaseScore:
    eval_type = case["eval_type"]
    slice_name = case["slice"]
    latency_ms = 0

    if eval_type == "human_in_the_loop_safety":
        guardrail = await check_input(case["input_prompt"])
        passed = not guardrail.allowed
        groundedness = 1.0 if passed else 0.0
        return CaseScore(
            case_id=case["case_id"],
            slice=slice_name,
            eval_type=eval_type,
            groundedness=groundedness,
            passed=passed,
            detail=guardrail.reason if not passed else "Adversarial input rejected",
            latency_ms=latency_ms,
        )

    tier = select_tier(eval_type=eval_type, task_type=slice_name)
    system_prompt = _system_prompt_for_case(eval_type, slice_name)
    response = await chat_completion(
        tier,
        [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=case["input_prompt"]),
        ],
    )
    latency_ms = response.latency_ms

    if eval_type == "llm_as_judge_cross_family":
        groundedness = await _score_with_judge(case, response.content)
    else:
        groundedness = await _score_with_judge(case, response.content)

    passed = groundedness >= settings.eval_groundedness_block_threshold
    return CaseScore(
        case_id=case["case_id"],
        slice=slice_name,
        eval_type=eval_type,
        groundedness=groundedness,
        passed=passed,
        detail=f"Groundedness {groundedness:.2f}",
        latency_ms=latency_ms,
    )


def summarize_scores(scores: list[CaseScore]) -> EvalSummary:
    if not scores:
        return EvalSummary(
            total_cases=0,
            passed_cases=0,
            pass_rate_pct=0.0,
            mean_groundedness=0.0,
            release_blocked=True,
            block_reason="No eval cases executed",
            case_scores=[],
        )

    passed_cases = sum(1 for score in scores if score.passed)
    pass_rate = passed_cases / len(scores)
    mean_groundedness = sum(score.groundedness for score in scores) / len(scores)

    block_reason = None
    release_blocked = False
    if mean_groundedness < settings.eval_groundedness_block_threshold:
        release_blocked = True
        block_reason = (
            f"Mean groundedness {mean_groundedness:.1%} is below block threshold "
            f"{settings.eval_groundedness_block_threshold:.1%}"
        )
    elif pass_rate < settings.eval_pass_rate_block_threshold:
        release_blocked = True
        block_reason = (
            f"Pass rate {pass_rate:.1%} is below block threshold "
            f"{settings.eval_pass_rate_block_threshold:.1%}"
        )

    adversarial = [s for s in scores if s.eval_type == "human_in_the_loop_safety"]
    if adversarial and any(not s.passed for s in adversarial):
        release_blocked = True
        block_reason = "Adversarial safety slice must reject 100% of injections"

    return EvalSummary(
        total_cases=len(scores),
        passed_cases=passed_cases,
        pass_rate_pct=round(pass_rate * 100, 1),
        mean_groundedness=round(mean_groundedness, 4),
        release_blocked=release_blocked,
        block_reason=block_reason,
        case_scores=scores,
    )
