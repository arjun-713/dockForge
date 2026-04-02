from fastapi import APIRouter, Query

from app.config import get_settings
from app.models.leaderboard import LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService
from app.services.submission_repository import SubmissionRepository

router = APIRouter(tags=["leaderboard"])


def _leaderboard_service() -> LeaderboardService:
    settings = get_settings()
    repository = SubmissionRepository(database_url=settings.database_url)
    return LeaderboardService(repository)


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    problem_id: str | None = Query(default=None, alias="problemId"),
    limit: int = Query(default=10, ge=1, le=100),
) -> LeaderboardResponse:
    service = _leaderboard_service()
    if problem_id:
        return service.get_challenge_leaderboard(problem_id=problem_id, limit=limit)
    return service.get_global_leaderboard(limit=limit)
