import pytest

from app.db import close_pool


@pytest.fixture(autouse=True)
async def reset_db_pool():
    yield
    await close_pool()
