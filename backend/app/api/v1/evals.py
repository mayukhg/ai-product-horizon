from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import get_current_user
from app.evals.runner import get_eval_metrics, run_golden_dataset_eval, run_offline_baseline
from app.schemas import ErrorResponse, EvalMetricsResponse, EvalMetricPoint, EvalRunItem, EvalRunRequest, EvalRunResponse

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
        release_blocked=payload.get("release_blocked", False),
        block_reason=payload.get("block_reason"),
    )


@router.post("/baseline")
async def trigger_baseline(_user: dict = Depends(get_current_user)) -> dict:
    return await run_offline_baseline()


@router.post("/run", response_model=EvalRunResponse, responses={503: {"model": ErrorResponse}})
async def trigger_eval_run(
    body: EvalRunRequest = EvalRunRequest(),
    _user: dict = Depends(get_current_user),
) -> EvalRunResponse:
    try:
        payload = await run_golden_dataset_eval(limit=body.limit)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "code": "LLM_CONFIG_ERROR", "message": str(exc)},
        )

    return EvalRunResponse(
        status=payload["status"],
        run_id=payload["run_id"],
        llm_mode=payload["llm_mode"],
        total_cases=payload["total_cases"],
        passed_cases=payload["passed_cases"],
        pass_rate_pct=payload["pass_rate_pct"],
        mean_groundedness=payload["mean_groundedness"],
        mean_groundedness_pct=payload["mean_groundedness_pct"],
        release_blocked=payload["release_blocked"],
        block_reason=payload.get("block_reason"),
        thresholds=payload["thresholds"],
    )
