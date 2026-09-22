from fastapi import APIRouter

from app.api.v1 import agent, evals, models, remediate, triage

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(triage.router)
api_router.include_router(agent.router)
api_router.include_router(evals.router)
api_router.include_router(models.router)
api_router.include_router(remediate.router)
