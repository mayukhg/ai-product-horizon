import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_eval_baseline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/evals/baseline")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "llm_mode" in payload


@pytest.mark.asyncio
async def test_eval_run_mock_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/evals/run", json={"limit": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cases"] == 3
    assert "mean_groundedness" in payload
    assert "release_blocked" in payload
