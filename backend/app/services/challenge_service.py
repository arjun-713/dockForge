from app.models.problem import ProblemDetail, ProblemListResponse
from app.services.problem_catalog import ProblemCatalog


class ChallengeService:
    def __init__(self, catalog: ProblemCatalog) -> None:
        self.catalog = catalog

    def list_challenges(self) -> ProblemListResponse:
        return ProblemListResponse(problems=self.catalog.list_problems())

    def get_challenge(self, challenge_id: str) -> ProblemDetail | None:
        return self.catalog.get_problem(challenge_id)
