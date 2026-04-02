from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SubmissionState = Literal[
    "queued",
    "ai_review",
    "manual_review",
    "building",
    "testing",
    "completed",
    "failed",
    "rejected",
    "timed_out",
]

ViolationSeverity = Literal["low", "medium", "high", "critical"]


class SubmissionRequest(BaseModel):
    problem_id: str
    dockerfile_content: str


class SubmissionViolation(BaseModel):
    severity: ViolationSeverity
    line: int
    instruction: str = ""
    reason: str


class SubmissionWarning(BaseModel):
    severity: ViolationSeverity
    line: int
    reason: str


class SubmissionReviewResult(BaseModel):
    approved: bool
    risk_score: int
    violations: list[SubmissionViolation] = Field(default_factory=list)
    warnings: list[SubmissionWarning] = Field(default_factory=list)
    educational_hint: str = ""


class SubmissionMetrics(BaseModel):
    build_time_ms: int | None = Field(default=None, alias="buildTimeMs")
    image_size_bytes: int | None = Field(default=None, alias="imageSizeBytes")
    test_pass: bool | None = Field(default=None, alias="testPass")


class SubmissionScore(BaseModel):
    build_time_score: int = Field(alias="buildTimeScore")
    image_size_score: int = Field(alias="imageSizeScore")
    best_practice_score: int = Field(alias="bestPracticeScore")
    difficulty_multiplier: float = Field(alias="difficultyMultiplier")
    final_score: int = Field(alias="finalScore")


class SubmissionResponse(BaseModel):
    submission_id: str = Field(alias="submissionId")
    problem_id: str = Field(alias="problemId")
    state: SubmissionState
    passed: bool
    logs: str
    review: SubmissionReviewResult
    metrics: SubmissionMetrics
    score: SubmissionScore | None = None
    created_at: datetime = Field(alias="createdAt")


class SubmissionRecord(BaseModel):
    submission_id: str
    problem_id: str
    dockerfile_content: str
    state: SubmissionState
    passed: bool
    logs: str
    review: SubmissionReviewResult
    metrics: SubmissionMetrics = Field(default_factory=SubmissionMetrics)
    score: SubmissionScore | None = None
    created_at: datetime

    def to_response(self) -> SubmissionResponse:
        return SubmissionResponse(
            submissionId=self.submission_id,
            problemId=self.problem_id,
            state=self.state,
            passed=self.passed,
            logs=self.logs,
            review=self.review,
            metrics=self.metrics,
            score=self.score,
            createdAt=self.created_at,
        )
