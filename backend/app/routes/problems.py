import os

from fastapi import APIRouter, HTTPException
from app.models.problem import ProblemDetail, ProblemListResponse
from app.services.challenge_service import ChallengeService
from app.services.problem_catalog import ProblemCatalog

router = APIRouter(tags=["problems"])


def _challenge_service() -> ChallengeService:
    problems_dir = os.getenv("PROBLEMS_DIR", "/app/problems")
    catalog = ProblemCatalog(problems_dir=problems_dir)
    return ChallengeService(catalog)


@router.get("/problems", response_model=ProblemListResponse)
async def list_problems() -> ProblemListResponse:
    service = _challenge_service()
    return service.list_challenges()


@router.get("/problems/{problem_id}", response_model=ProblemDetail)
async def get_problem(problem_id: str) -> ProblemDetail:
    service = _challenge_service()
    problem = service.get_challenge(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem
