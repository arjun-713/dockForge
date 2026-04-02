from uuid import uuid4

from app.models.submission import SubmissionMetrics, SubmissionRecord, SubmissionResponse, SubmissionReviewResult
from app.services.docker_service import (
    DockerEvaluationError,
    DockerSubmissionService,
    ProblemNotFoundError,
)
from app.services.problem_catalog import ProblemCatalog
from app.services.scoring_service import ScoringService
from app.services.security_gate import DockerfileSecurityGate, SubmissionPrecheckError, enforce_prechecks
from app.services.submission_repository import SubmissionRepository, new_submission_record


class SubmissionService:
    def __init__(
        self,
        *,
        catalog: ProblemCatalog,
        execution_service: DockerSubmissionService,
        repository: SubmissionRepository,
        scoring_service: ScoringService,
        security_gate: DockerfileSecurityGate,
        max_submission_size_bytes: int,
    ) -> None:
        self.catalog = catalog
        self.execution_service = execution_service
        self.repository = repository
        self.scoring_service = scoring_service
        self.security_gate = security_gate
        self.max_submission_size_bytes = max_submission_size_bytes

    def submit(self, problem_id: str, dockerfile_content: str) -> SubmissionResponse:
        metadata = self.catalog.get_metadata(problem_id)
        if metadata is None:
            raise ProblemNotFoundError(f"Problem '{problem_id}' not found")

        enforce_prechecks(dockerfile_content, self.max_submission_size_bytes)

        submission_id = uuid4().hex
        review = SubmissionReviewResult(approved=True, risk_score=0, educational_hint="")
        record = new_submission_record(
            submission_id=submission_id,
            problem_id=problem_id,
            dockerfile_content=dockerfile_content,
            state="ai_review",
            review=review,
            logs="Submission accepted for AI review.",
        )
        self.repository.upsert_submission(record)

        review = self.security_gate.review(dockerfile_content)
        record.review = review
        record.logs = review.educational_hint or "Submission reviewed."

        if not review.approved or review.risk_score > 70:
            record.state = "rejected"
            self.repository.upsert_submission(record)
            return record.to_response()

        if review.risk_score > 50:
            record.state = "manual_review"
            record.logs = "Submission queued for manual review because the AI gate marked it as high risk."
            self.repository.upsert_submission(record)
            return record.to_response()

        record.state = "building"
        record.logs = "Submission cleared review and is building."
        self.repository.upsert_submission(record)

        try:
            execution_result = self.execution_service.evaluate_submission(problem_id, dockerfile_content)
        except DockerEvaluationError as exc:
            record.state = "failed"
            record.logs = str(exc)
            self.repository.upsert_submission(record)
            raise

        record.state = "completed" if execution_result.passed else "failed"
        record.passed = execution_result.passed
        record.metrics = SubmissionMetrics(
            buildTimeMs=execution_result.build_time_ms,
            imageSizeBytes=execution_result.image_size_bytes,
            testPass=execution_result.passed,
        )
        record.score = self.scoring_service.score_submission(metadata, record.metrics, dockerfile_content)
        record.logs = execution_result.logs
        self.repository.upsert_submission(record)

        return record.to_response()

    def get_submission(self, submission_id: str) -> SubmissionResponse | None:
        record = self.repository.get_submission(submission_id)
        if record is None:
            return None
        return record.to_response()
