from __future__ import annotations

import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import settings
from app.db import apply_migrations, close_pool, get_pool, table_count


async def ensure_database_seeded() -> None:
    await apply_migrations()
    if await table_count("eval_cases") == 0:
        seed_script = Path(__file__).resolve().parents[1] / "scripts" / "seed_data.py"
        subprocess.run([sys.executable, str(seed_script)], check=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await get_pool()
    await ensure_database_seeded()
    yield
    await close_pool()


app = FastAPI(title="HorizonAI CyberRisk Resident API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"status": "error", "code": "INTERNAL_ERROR", "message": str(exc)},
    )
