from __future__ import annotations

from typing import Any

from app.db import fetch_all, fetch_one


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
    """Deterministic lead-worker orchestration stub for pilot runs."""
    existing = await fetch_one("SELECT run_id FROM agent_runs WHERE scan_id = $1 ORDER BY created_at DESC LIMIT 1", scan_id)
    if existing:
        return existing["run_id"]

    run_id = "7f4c-92a1"
    await fetch_one(
        """
        INSERT INTO agent_runs (run_id, scan_id, title, region, autonomy_level, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (run_id) DO NOTHING
        RETURNING run_id
        """,
        run_id,
        scan_id,
        "Investigate critical scan delta",
        "prod-us-east",
        2,
        "executing",
    )
    return run_id
