from fastapi import APIRouter, HTTPException

from app.agents.lead_worker import get_trajectory
from app.schemas import AgentTrajectoryResponse, ErrorResponse, TrajectoryStep, WorkerAgent

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
