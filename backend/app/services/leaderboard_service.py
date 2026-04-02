from app.models.leaderboard import LeaderboardResponse
from app.services.submission_repository import SubmissionRepository


class LeaderboardService:
    def __init__(self, repository: SubmissionRepository) -> None:
        self.repository = repository

    def get_global_leaderboard(self, limit: int = 10) -> LeaderboardResponse:
        return LeaderboardResponse(entries=self.repository.list_leaderboard(limit=limit))

    def get_challenge_leaderboard(self, problem_id: str, limit: int = 10) -> LeaderboardResponse:
        return LeaderboardResponse(entries=self.repository.list_leaderboard(limit=limit, problem_id=problem_id))
