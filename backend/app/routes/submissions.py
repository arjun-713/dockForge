from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["submissions"])


class SubmissionRequest(BaseModel):
    problem_id: str
    dockerfile_content: str


@router.post("/submit")
async def submit(_payload: SubmissionRequest) -> dict[str, object]:
    return {
        "passed": False,
        "logs": "Submission engine not implemented yet. Planned for Phase 3.",
    }
