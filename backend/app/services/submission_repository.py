import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.models.submission import (
    SubmissionMetrics,
    SubmissionRecord,
    SubmissionReviewResult,
    SubmissionScore,
)


def _sqlite_path_from_url(database_url: str) -> Path:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// database URLs are supported in local development.")

    raw_path = database_url[len(prefix) :]
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


class SubmissionRepository:
    def __init__(self, database_url: str) -> None:
        self.database_path = _sqlite_path_from_url(database_url)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def upsert_submission(self, record: SubmissionRecord) -> SubmissionRecord:
        payload = (
            record.submission_id,
            record.problem_id,
            record.dockerfile_content,
            record.state,
            int(record.passed),
            record.logs,
            json.dumps(record.review.model_dump(mode="json")),
            json.dumps(record.metrics.model_dump(by_alias=True)),
            json.dumps(record.score.model_dump(by_alias=True)) if record.score else None,
            record.created_at.isoformat(),
        )

        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO submissions (
                    id, problem_id, dockerfile_text, state, passed, logs,
                    review_json, metrics_json, score_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    problem_id = excluded.problem_id,
                    dockerfile_text = excluded.dockerfile_text,
                    state = excluded.state,
                    passed = excluded.passed,
                    logs = excluded.logs,
                    review_json = excluded.review_json,
                    metrics_json = excluded.metrics_json,
                    score_json = excluded.score_json,
                    created_at = excluded.created_at
                """,
                payload,
            )
            conn.execute(
                """
                INSERT INTO violations_log (submission_id, dockerfile_hash, risk_score, violations_json, created_at)
                VALUES (?, hex(randomblob(16)), ?, ?, ?)
                ON CONFLICT(submission_id) DO UPDATE SET
                    risk_score = excluded.risk_score,
                    violations_json = excluded.violations_json,
                    created_at = excluded.created_at
                """,
                (
                    record.submission_id,
                    record.review.risk_score,
                    json.dumps([item.model_dump() for item in record.review.violations]),
                    record.created_at.isoformat(),
                ),
            )
            if record.score is not None:
                conn.execute(
                    """
                    INSERT INTO scores (
                        submission_id, build_time_score, image_size_score, best_practice_score,
                        final_score, difficulty_multiplier, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(submission_id) DO UPDATE SET
                        build_time_score = excluded.build_time_score,
                        image_size_score = excluded.image_size_score,
                        best_practice_score = excluded.best_practice_score,
                        final_score = excluded.final_score,
                        difficulty_multiplier = excluded.difficulty_multiplier,
                        created_at = excluded.created_at
                    """,
                    (
                        record.submission_id,
                        record.score.build_time_score,
                        record.score.image_size_score,
                        record.score.best_practice_score,
                        record.score.final_score,
                        record.score.difficulty_multiplier,
                        record.created_at.isoformat(),
                    ),
                )

        return record

    def get_submission(self, submission_id: str) -> SubmissionRecord | None:
        with sqlite3.connect(self.database_path) as conn:
            row = conn.execute(
                """
                SELECT id, problem_id, dockerfile_text, state, passed, logs,
                       review_json, metrics_json, score_json, created_at
                FROM submissions
                WHERE id = ?
                """,
                (submission_id,),
            ).fetchone()

        if row is None:
            return None

        review = SubmissionReviewResult.model_validate(json.loads(row[6]))
        metrics = SubmissionMetrics.model_validate(json.loads(row[7]))
        score = SubmissionScore.model_validate(json.loads(row[8])) if row[8] else None

        return SubmissionRecord(
            submission_id=row[0],
            problem_id=row[1],
            dockerfile_content=row[2],
            state=row[3],
            passed=bool(row[4]),
            logs=row[5],
            review=review,
            metrics=metrics,
            score=score,
            created_at=datetime.fromisoformat(row[9]),
        )

    def _initialize(self) -> None:
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,
                    problem_id TEXT NOT NULL,
                    dockerfile_text TEXT NOT NULL,
                    state TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    logs TEXT NOT NULL,
                    review_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    score_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scores (
                    submission_id TEXT PRIMARY KEY,
                    build_time_score INTEGER NOT NULL,
                    image_size_score INTEGER NOT NULL,
                    best_practice_score INTEGER NOT NULL,
                    final_score INTEGER NOT NULL,
                    difficulty_multiplier REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS violations_log (
                    submission_id TEXT PRIMARY KEY,
                    dockerfile_hash TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )


def new_submission_record(
    submission_id: str,
    problem_id: str,
    dockerfile_content: str,
    state: str,
    review: SubmissionReviewResult,
    *,
    passed: bool = False,
    logs: str = "",
    metrics: SubmissionMetrics | None = None,
    score: SubmissionScore | None = None,
) -> SubmissionRecord:
    return SubmissionRecord(
        submission_id=submission_id,
        problem_id=problem_id,
        dockerfile_content=dockerfile_content,
        state=state,
        passed=passed,
        logs=logs,
        review=review,
        metrics=metrics or SubmissionMetrics(),
        score=score,
        created_at=datetime.now(tz=UTC),
    )
