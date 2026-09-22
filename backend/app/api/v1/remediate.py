from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db import fetch_one
from app.schemas import ErrorResponse, RemediateApproveRequest, RemediateApproveResponse

router = APIRouter(prefix="/remediate", tags=["remediate"])


@router.post("/approve", response_model=RemediateApproveResponse, responses={404: {"model": ErrorResponse}})
async def approve_remediation(body: RemediateApproveRequest) -> RemediateApproveResponse:
    row = await fetch_one(
        "SELECT remediation_id, status FROM remediation_actions WHERE remediation_id = $1",
        body.remediation_id,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"status": "error", "code": "REMEDIATION_NOT_FOUND", "message": "Remediation action not found"},
        )

    approved_at = datetime.now(timezone.utc)
    await fetch_one(
        """
        UPDATE remediation_actions
        SET status = 'approved', approval_id = $2, approved_at = $3, approved_by = $4
        WHERE remediation_id = $1
        RETURNING remediation_id
        """,
        body.remediation_id,
        body.approval_id,
        approved_at,
        body.approved_by,
    )

    return RemediateApproveResponse(
        remediation_id=body.remediation_id,
        approval_id=body.approval_id,
        approved_at=approved_at,
        message="Remediation approved for execution. Canary rollout queued.",
    )
