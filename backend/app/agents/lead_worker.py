from __future__ import annotations

import json
from typing import Any

from app.db import fetch_all, fetch_one
from app.guardrails.engine import check_input
from app.llm.client import chat_completion, extract_json_payload
from app.llm.prompts import AGENT_PLAN_SYSTEM, EXPLOIT_SYNTHESIS_SYSTEM
from app.llm.router import ModelTier, select_tier
from app.llm.types import ChatMessage


async def get_active_run() -> dict[str, Any] | None:
    row = await fetch_one(
        """
        SELECT run_id, scan_id, title, region, autonomy_level, status
        FROM agent_runs
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    return dict(row) if row else None


async def get_trajectory(run_id: str) -> dict[str, Any]:
    run = await fetch_one(
        "SELECT run_id, scan_id, title, region, autonomy_level, status FROM agent_runs WHERE run_id = $1",
        run_id,
    )
    if not run:
        raise ValueError(f"Unknown run_id: {run_id}")

    steps = await fetch_all(
        """
        SELECT step_id, title, detail, duration_ms, step_type, status
        FROM agent_trajectory_steps
        WHERE run_id = $1
        ORDER BY step_order ASC
        """,
        run_id,
    )
    workers = await fetch_all(
        """
        SELECT agent_name, action, agent_role
        FROM agent_execution_logs
        WHERE run_id = $1 AND agent_role = 'worker'
        ORDER BY id ASC
        """,
        run_id,
    )

    return {
        "run": dict(run),
        "steps": [dict(step) for step in steps],
        "workers": [dict(worker) for worker in workers],
    }


async def execute_lead_worker_loop(scan_id: str) -> str:
    """Lead-Worker orchestration: guardrail gate, tier routing, trajectory persistence."""
    existing = await fetch_one(
        "SELECT run_id FROM agent_runs WHERE scan_id = $1 ORDER BY created_at DESC LIMIT 1",
        scan_id,
    )
    if existing:
        return existing["run_id"]

    scan = await fetch_one(
        """
        SELECT scan_id, scope, scanner, critical_findings, tru_risk_score, tru_risk_delta
        FROM scan_context WHERE scan_id = $1
        """,
        scan_id,
    )
    if not scan:
        raise ValueError(f"Unknown scan_id: {scan_id}")

    prompt = (
        f"Scan {scan['scan_id']} delta: TruRisk {scan['tru_risk_score']} "
        f"(+{scan['tru_risk_delta']}), {scan['critical_findings']} critical findings, "
        f"scope {scan['scope']}, scanner {scan['scanner']}."
    )
    guardrail = await check_input(prompt)
    if not guardrail.allowed:
        raise ValueError(f"Guardrail blocked agent run: {guardrail.reason}")

    tier = select_tier(task_type="exploit synthesis")
    system_prompt = EXPLOIT_SYNTHESIS_SYSTEM if tier == ModelTier.PHD_REASONER else AGENT_PLAN_SYSTEM
    llm_response = await chat_completion(
        tier,
        [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt),
        ],
    )
    payload = extract_json_payload(llm_response.content)

    run_id = "7f4c-92a1"
    title = payload.get("attack_path_summary") or payload.get("title") or "Investigate critical scan delta"
    await fetch_one(
        """
        INSERT INTO agent_runs (run_id, scan_id, title, region, autonomy_level, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (run_id) DO NOTHING
        RETURNING run_id
        """,
        run_id,
        scan_id,
        title[:255],
        "prod-us-east",
        2,
        "executing",
    )

    detail = payload.get("primary_mitigation") or payload.get("detail") or llm_response.content[:500]
    await fetch_one(
        """
        INSERT INTO agent_trajectory_steps (
            run_id, step_order, step_id, title, detail, duration_ms, step_type, status
        )
        VALUES ($1, 1, '01', 'Plan', $2, $3, 'plan', 'completed')
        ON CONFLICT (run_id, step_order) DO NOTHING
        RETURNING step_id
        """,
        run_id,
        detail,
        llm_response.latency_ms,
    )

    await fetch_one(
        """
        INSERT INTO agent_execution_logs (run_id, agent_role, agent_name, action, result)
        VALUES ($1, 'lead', 'Lead Agent', $2, $3::jsonb)
        RETURNING id
        """,
        run_id,
        f"Routed via {tier.value} ({llm_response.model})",
        json.dumps({"model": llm_response.model, "latency_ms": llm_response.latency_ms}),
    )

    return run_id
