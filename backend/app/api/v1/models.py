from fastapi import APIRouter

from app.db import fetch_all
from app.schemas import ModelRoute, ModelRoutingResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/route", response_model=ModelRoutingResponse)
async def get_model_routes() -> ModelRoutingResponse:
    rows = await fetch_all(
        "SELECT task_label, model_name, detail, is_active FROM model_routes ORDER BY id ASC"
    )
    return ModelRoutingResponse(
        routes=[
            ModelRoute(
                label=row["task_label"],
                model=row["model_name"],
                detail=row["detail"],
                active=row["is_active"],
            )
            for row in rows
        ]
    )
