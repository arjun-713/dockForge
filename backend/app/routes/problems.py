from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.models.problem import ProblemDetail, ProblemSummary
from app.services.problem_catalog import ProblemCatalog

router = APIRouter(tags=["problems"])


def get_problem_catalog() -> ProblemCatalog:
    settings = get_settings()
    return ProblemCatalog(problems_dir=settings.problems_dir)


@router.get("/problems")
async def list_problems(
    catalog: ProblemCatalog = Depends(get_problem_catalog),
) -> dict[str, list[ProblemSummary]]:
    return {"problems": catalog.list_problems()}


@router.get("/problems/{problem_id}")
async def get_problem(
    problem_id: str,
    catalog: ProblemCatalog = Depends(get_problem_catalog),
) -> ProblemDetail:
    problem = catalog.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem
