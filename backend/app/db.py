from __future__ import annotations

from pathlib import Path
from typing import Any

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def fetch_all(query: str, *args: Any) -> list[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetch_one(query: str, *args: Any) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute(query: str, *args: Any) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def apply_migrations() -> None:
    migration_path = Path(__file__).resolve().parents[1] / "db" / "migrations" / "001_initial.sql"
    sql = migration_path.read_text()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql)


async def table_count(table_name: str) -> int:
    row = await fetch_one(f"SELECT COUNT(*)::int AS count FROM {table_name}")
    return int(row["count"]) if row else 0
