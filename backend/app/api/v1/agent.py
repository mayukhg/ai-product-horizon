from fastapi import APIRouter, Depends, HTTPException

from app.agents.lead_worker import execute_lead_worker_loop, get_trajectory
from app.auth.deps import get_current_user
from app.schemas import AgentRunResponse, AgentTrajectoryResponse, ErrorResponse, TrajectoryStep, WorkerAgent

router = APIRouter(prefix="/agent", tags=["agent"])


def _format_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


@router.get("/trajectory", response_model=AgentTrajectoryResponse, responses={404: {"model": ErrorResponse}})
async def get_agent_trajectory(run_id: str = "7f4c-92a1") -> AgentTrajectoryResponse:
    try:
        payload = await get_trajectory(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"status": "error", "code": "RUN_NOT_FOUND", "message": str(exc)})

    workers = [
        WorkerAgent(
            name=worker["agent_name"],
            detail=worker["action"][:40],
            tone="success" if worker["agent_name"] == "Asset mapper" else "primary",
        )
        for worker in payload["workers"]
    ] or [
        WorkerAgent(name="Asset mapper", detail="12 nodes", tone="success"),
        WorkerAgent(name="Threat intel", detail="3 feeds", tone="primary"),
        WorkerAgent(name="Policy verifier", detail="CIS 2.0", tone="agent"),
    ]

    return AgentTrajectoryResponse(
        run_id=payload["run"]["run_id"],
        scan_id=payload["run"]["scan_id"],
        title=payload["run"]["title"],
        region=payload["run"]["region"],
        autonomy_level=payload["run"]["autonomy_level"],
        status=payload["run"]["status"],
        steps=[
            TrajectoryStep(
                id=step["step_id"],
                title=step["title"],
                detail=step["detail"],
                time=_format_duration(step["duration_ms"]),
                step_type=step["step_type"],
                status=step["status"],
            )
            for step in payload["steps"]
        ],
        workers=workers,
    )


@router.post("/run", response_model=AgentRunResponse, responses={400: {"model": ErrorResponse}})
async def run_agent(scan_id: str = "CR-0922-0048", _user: dict = Depends(get_current_user)) -> AgentRunResponse:
    try:
        run_id = await execute_lead_worker_loop(scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"status": "error", "code": "AGENT_RUN_FAILED", "message": str(exc)})

    return AgentRunResponse(run_id=run_id, scan_id=scan_id, status="executing")
