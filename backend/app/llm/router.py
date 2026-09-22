from __future__ import annotations

from enum import Enum


class ModelTier(str, Enum):
    SMART_INTERN = "smart_intern"
    PHD_REASONER = "phd_reasoner"
    GUARDRAIL = "guardrail"
    JUDGE = "judge"
    EMBEDDING = "embedding"


def select_tier(task_type: str | None = None, eval_type: str | None = None) -> ModelTier:
    """Route tasks using the approved Four-Lens hybrid policy."""
    key = (eval_type or task_type or "").lower()

    if "human_in_the_loop" in key or "adversarial" in key or "guardrail" in key:
        return ModelTier.GUARDRAIL
    if "llm_as_judge" in key or key == "judge":
        return ModelTier.JUDGE
    if "exploit" in key or "synthesis" in key or "attack" in key or "phd" in key:
        return ModelTier.PHD_REASONER
    if key == "embedding":
        return ModelTier.EMBEDDING

    return ModelTier.SMART_INTERN
