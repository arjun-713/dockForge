from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.submission import SubmissionRequest, SubmissionResponse
from app.services.docker_service import (
    DockerEvaluationError,
    DockerSubmissionService,
    ProblemNotFoundError,
)

router = APIRouter(tags=["submissions"])


def _submission_service() -> DockerSubmissionService:
    settings = get_settings()
    docker_socket = settings.docker_socket
    if docker_socket.startswith("/"):
        docker_socket = f"unix://{docker_socket}"

    return DockerSubmissionService(
        problems_dir=settings.problems_dir,
        docker_socket=docker_socket,
        max_build_timeout=settings.max_build_timeout,
        max_run_timeout=settings.max_run_timeout,
        submission_memory_limit=settings.submission_memory_limit,
        submission_cpu_quota=settings.submission_cpu_quota,
    )


@router.post("/submit", response_model=SubmissionResponse)
async def submit(payload: SubmissionRequest) -> SubmissionResponse:
    service = _submission_service()
    try:
        result = service.evaluate_submission(payload.problem_id, payload.dockerfile_content)
    except ProblemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DockerEvaluationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SubmissionResponse(passed=result.passed, logs=result.logs)
