import re

from app.models.problem import ProblemMetadata
from app.models.submission import SubmissionMetrics, SubmissionScore


class ScoringService:
    _secret_env_pattern = re.compile(
        r"^ENV\s+[A-Z0-9_]*(TOKEN|SECRET|KEY|PASSWORD)[A-Z0-9_]*\s*=",
        re.IGNORECASE,
    )

    def score_submission(
        self,
        metadata: ProblemMetadata,
        metrics: SubmissionMetrics,
        dockerfile_content: str,
    ) -> SubmissionScore | None:
        if not metrics.test_pass or metrics.build_time_ms is None or metrics.image_size_bytes is None:
            return None

        build_time_score = min(
            100,
            round((metadata.baseline_build_ms / max(metrics.build_time_ms, 1)) * 100),
        )
        image_size_score = min(
            100,
            round((metadata.baseline_size_bytes / max(metrics.image_size_bytes, 1)) * 100),
        )
        best_practice_score = self._best_practice_score(dockerfile_content)

        multiplier = {
            "basic": 1.0,
            "medium": 1.5,
            "hard": 2.0,
            "advanced": 3.0,
        }[metadata.tier or "basic"]

        final_score = round(
            (build_time_score * 0.30 + image_size_score * 0.40 + best_practice_score * 0.30) * multiplier
        )

        return SubmissionScore(
            buildTimeScore=build_time_score,
            imageSizeScore=image_size_score,
            bestPracticeScore=best_practice_score,
            difficultyMultiplier=multiplier,
            finalScore=final_score,
        )

    def _best_practice_score(self, dockerfile_content: str) -> int:
        score = 100
        upper_content = dockerfile_content.upper()

        if ":LATEST" in upper_content:
            score -= 15

        if "USER " not in upper_content:
            score -= 25

        if "HEALTHCHECK" not in upper_content:
            score -= 10

        for line in dockerfile_content.splitlines():
            if self._secret_env_pattern.search(line.strip()):
                score -= 20
                break

        return max(score, 0)
