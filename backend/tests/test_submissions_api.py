import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.docker_service import (
    DockerEvaluationError,
    ProblemNotFoundError,
    SubmissionEvaluationResult,
)


@pytest.mark.anyio
async def test_submit_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def evaluate_submission(self, problem_id: str, dockerfile_content: str) -> SubmissionEvaluationResult:
            assert problem_id == "01-nginx-static"
            assert "FROM nginx" in dockerfile_content
            return SubmissionEvaluationResult(passed=True, logs="ok")

    monkeypatch.setattr(
        "app.routes.submissions._submission_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/submit",
            json={"problem_id": "01-nginx-static", "dockerfile_content": "FROM nginx:alpine"},
        )

    assert response.status_code == 200
    assert response.json() == {"passed": True, "logs": "ok"}


@pytest.mark.anyio
async def test_submit_problem_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def evaluate_submission(self, problem_id: str, dockerfile_content: str) -> SubmissionEvaluationResult:
            raise ProblemNotFoundError(f"Problem '{problem_id}' not found")

    monkeypatch.setattr(
        "app.routes.submissions._submission_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/submit",
            json={"problem_id": "does-not-exist", "dockerfile_content": "FROM scratch"},
        )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_submit_docker_evaluation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def evaluate_submission(self, problem_id: str, dockerfile_content: str) -> SubmissionEvaluationResult:
            raise DockerEvaluationError("build failed")

    monkeypatch.setattr(
        "app.routes.submissions._submission_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/submit",
            json={"problem_id": "01-nginx-static", "dockerfile_content": "FROM scratch"},
        )

    assert response.status_code == 400
    assert "build failed" in response.json()["detail"]
