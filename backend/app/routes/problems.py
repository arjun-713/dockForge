import os

from fastapi import APIRouter, HTTPException
from app.services.problem_catalog import ProblemCatalog

router = APIRouter(tags=["problems"])


def _problem_catalog() -> ProblemCatalog:
    problems_dir = os.getenv("PROBLEMS_DIR", "/app/problems")
    return ProblemCatalog(problems_dir=problems_dir)


@router.get("/problems")
async def list_problems() -> dict[str, list[dict[str, object]]]:
    catalog = _problem_catalog()
    problems = [item.model_dump() for item in catalog.list_problems()]
    return {"problems": problems}


@router.get("/problems/{problem_id}")
async def get_problem(
    problem_id: str,
) -> dict[str, object]:
    catalog = _problem_catalog()
    problem = catalog.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem.model_dump(by_alias=True)
