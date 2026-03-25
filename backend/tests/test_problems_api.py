from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.routes.problems import get_problem_catalog
from app.services.problem_catalog import ProblemCatalog


client = TestClient(app)


def _override_catalog(path: Path) -> None:
    app.dependency_overrides[get_problem_catalog] = lambda: ProblemCatalog(str(path))


def _clear_override() -> None:
    app.dependency_overrides.pop(get_problem_catalog, None)


def test_list_problems_returns_seed_data() -> None:
    _override_catalog(Path("../problems").resolve())
    try:
        response = client.get("/api/problems")
    finally:
        _clear_override()

    assert response.status_code == 200
    payload = response.json()
    assert "problems" in payload
    assert len(payload["problems"]) >= 3
    assert payload["problems"][0]["id"] == "01-nginx-static"


def test_get_problem_detail() -> None:
    _override_catalog(Path("../problems").resolve())
    try:
        response = client.get("/api/problems/02-node-express-health")
    finally:
        _clear_override()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "02-node-express-health"
    assert payload["appPort"] == 3000
    assert "Problem description" in payload["readme"]


def test_get_problem_not_found() -> None:
    _override_catalog(Path("../problems").resolve())
    try:
        response = client.get("/api/problems/does-not-exist")
    finally:
        _clear_override()

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
