from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app
from app.services.problem_catalog import ProblemCatalog

@pytest.mark.anyio
async def test_list_problems_returns_seed_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROBLEMS_DIR", str(Path("../problems").resolve()))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/problems")
    assert response.status_code == 200
    payload = response.json()
    assert "problems" in payload
    assert len(payload["problems"]) >= 3
    assert payload["problems"][0]["id"] == "01-nginx-static"


@pytest.mark.anyio
async def test_get_problem_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROBLEMS_DIR", str(Path("../problems").resolve()))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/problems/02-node-express-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "02-node-express-health"
    assert payload["appPort"] == 3000
    assert "Problem description" in payload["readme"]


@pytest.mark.anyio
async def test_get_problem_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROBLEMS_DIR", str(Path("../problems").resolve()))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/problems/does-not-exist")

    assert response.status_code == 404


def test_catalog_raises_on_invalid_problem_schema(tmp_path: Path) -> None:
    invalid_problem = tmp_path / "99-invalid"
    invalid_problem.mkdir(parents=True, exist_ok=True)
    (invalid_problem / "problem.json").write_text(
        '{"id":"99-invalid","title":"Broken","difficulty":"easy","concepts":[]}',
        encoding="utf-8",
    )

    catalog = ProblemCatalog(str(tmp_path))

    with pytest.raises(ValidationError):
        catalog.list_problems()
