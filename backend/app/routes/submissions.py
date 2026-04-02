from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.submission import SubmissionRequest, SubmissionResponse
from app.services.docker_service import (
    DockerEvaluationError,
    DockerSubmissionService,
    ProblemNotFoundError,
)
from app.services.problem_catalog import ProblemCatalog
from app.services.scoring_service import ScoringService
from app.services.security_gate import DockerfileSecurityGate, SubmissionPrecheckError
from app.services.submission_repository import SubmissionRepository
from app.services.submission_service import SubmissionService

router = APIRouter(tags=["submissions"])


def _submission_service() -> SubmissionService:
    settings = get_settings()
    docker_socket = settings.docker_socket
    if docker_socket.startswith("/"):
        docker_socket = f"unix://{docker_socket}"

    execution_service = DockerSubmissionService(
        problems_dir=settings.problems_dir,
        docker_socket=docker_socket,
        max_build_timeout=settings.max_build_timeout,
        max_run_timeout=settings.max_run_timeout,
        submission_memory_limit=settings.submission_memory_limit,
        submission_cpu_quota=settings.submission_cpu_quota,
    )
    catalog = ProblemCatalog(problems_dir=settings.problems_dir)
    repository = SubmissionRepository(database_url=settings.database_url)
    return SubmissionService(
        catalog=catalog,
        execution_service=execution_service,
        repository=repository,
        scoring_service=ScoringService(),
        security_gate=DockerfileSecurityGate(),
        max_submission_size_bytes=settings.max_submission_size_bytes,
    )


@router.post("/submit", response_model=SubmissionResponse)
async def submit(payload: SubmissionRequest) -> SubmissionResponse:
    service = _submission_service()
    try:
        return service.submit(payload.problem_id, payload.dockerfile_content)
    except ProblemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SubmissionPrecheckError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DockerEvaluationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: str) -> SubmissionResponse:
    service = _submission_service()
    result = service.get_submission(submission_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Submission '{submission_id}' not found")
    return result
