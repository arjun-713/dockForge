import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.leaderboard import LeaderboardResponse


def _leaderboard_payload(problem_id: str) -> LeaderboardResponse:
    return LeaderboardResponse.model_validate(
        {
            "entries": [
                {
                    "submissionId": "sub_1",
                    "problemId": problem_id,
                    "finalScore": 180,
                    "buildTimeScore": 90,
                    "imageSizeScore": 100,
                    "bestPracticeScore": 95,
                    "difficultyMultiplier": 2.0,
                    "createdAt": "2026-04-02T12:00:00+00:00",
                }
            ]
        }
    )


@pytest.mark.anyio
async def test_global_leaderboard(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_global_leaderboard(self, limit: int = 10) -> LeaderboardResponse:
            assert limit == 5
            return _leaderboard_payload("03-fastapi-health")

    monkeypatch.setattr(
        "app.routes.leaderboard._leaderboard_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/leaderboard?limit=5")

    assert response.status_code == 200
    assert response.json()["entries"][0]["finalScore"] == 180


@pytest.mark.anyio
async def test_problem_leaderboard(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_challenge_leaderboard(self, problem_id: str, limit: int = 10) -> LeaderboardResponse:
            assert problem_id == "01-nginx-static"
            assert limit == 10
            return _leaderboard_payload(problem_id)

    monkeypatch.setattr(
        "app.routes.leaderboard._leaderboard_service",
        lambda: FakeService(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/leaderboard?problemId=01-nginx-static")

    assert response.status_code == 200
    assert response.json()["entries"][0]["problemId"] == "01-nginx-static"
