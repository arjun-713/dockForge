import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.submission import SubmissionMetrics, SubmissionResponse, SubmissionReviewResult, SubmissionScore
from app.services.docker_service import DockerEvaluationError, ProblemNotFoundError


def _fake_response(**overrides: object) -> SubmissionResponse:
    payload = {
        "submissionId": "sub_123",
        "problemId": "01-nginx-static",
        "state": "completed",
        "passed": True,
        "logs": "ok",
        "review": SubmissionReviewResult(approved=True, risk_score=0, educational_hint=""),
        "metrics": SubmissionMetrics(buildTimeMs=1200, imageSizeBytes=20_000_000, testPass=True),
        "score": SubmissionScore(
            buildTimeScore=100,
            imageSizeScore=100,
            bestPracticeScore=90,
            difficultyMultiplier=1.0,
            finalScore=97,
        ),
        "createdAt": "2026-04-02T12:00:00+00:00",
    }
    payload.update(overrides)
    return SubmissionResponse.model_validate(payload)


@pytest.mark.anyio
async def test_submit_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def submit(self, problem_id: str, dockerfile_content: str) -> SubmissionResponse:
            assert problem_id == "01-nginx-static"
            assert "FROM nginx" in dockerfile_content
            return _fake_response()

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
    payload = response.json()
    assert payload["passed"] is True
    assert payload["logs"] == "ok"
    assert payload["state"] == "completed"
    assert payload["submissionId"] == "sub_123"
    assert payload["score"]["finalScore"] == 97


@pytest.mark.anyio
async def test_submit_problem_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def submit(self, problem_id: str, dockerfile_content: str) -> SubmissionResponse:
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
        def submit(self, problem_id: str, dockerfile_content: str) -> SubmissionResponse:
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


@pytest.mark.anyio
async def test_get_submission_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_submission(self, submission_id: str) -> SubmissionResponse | None:
            assert submission_id == "sub_123"
            return _fake_response()

    monkeypatch.setattr(
        "app.routes.submissions._submission_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/submissions/sub_123")

    assert response.status_code == 200
    assert response.json()["submissionId"] == "sub_123"


@pytest.mark.anyio
async def test_get_submission_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_submission(self, submission_id: str) -> SubmissionResponse | None:
            return None

    monkeypatch.setattr(
        "app.routes.submissions._submission_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/submissions/missing")

    assert response.status_code == 404
