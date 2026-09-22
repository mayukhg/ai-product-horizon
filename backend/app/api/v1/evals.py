from fastapi import APIRouter, HTTPException

from app.evals.runner import get_eval_metrics, run_offline_baseline
from app.schemas import ErrorResponse, EvalMetricsResponse, EvalMetricPoint, EvalRunItem

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get("", response_model=EvalMetricsResponse, responses={503: {"model": ErrorResponse}})
async def list_eval_metrics() -> EvalMetricsResponse:
    payload = await get_eval_metrics()
    if not payload["series"]:
        raise HTTPException(status_code=503, detail={"status": "error", "code": "EVAL_GATE_FAILED", "message": "No eval runs available"})

    return EvalMetricsResponse(
        total_runs=payload["total_runs"],
        pass_rate_pct=payload["pass_rate_pct"],
        drift_embedding_pct=payload["drift_embedding_pct"],
        series=[EvalMetricPoint(**point) for point in payload["series"]],
        recent_runs=[
            EvalRunItem(
                id=row["run_id"],
                name=row["name"],
                score=f"{float(row['score']):.1f}%",
                state=row["status"],
            )
            for row in payload["recent_runs"]
        ],
        telemetry=payload["telemetry"],
    )


@router.post("/baseline")
async def trigger_baseline() -> dict:
    return await run_offline_baseline()
