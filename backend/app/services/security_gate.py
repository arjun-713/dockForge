import re

from app.models.submission import (
    SubmissionReviewResult,
    SubmissionViolation,
    SubmissionWarning,
)


class SubmissionPrecheckError(Exception):
    pass


class DockerfileSecurityGate:
    _override_comment_patterns = [
        re.compile(r"ignore all previous instructions", re.IGNORECASE),
        re.compile(r"\bapproved\b", re.IGNORECASE),
        re.compile(r"\bsystem:\b", re.IGNORECASE),
    ]

    _critical_patterns = [
        (
            re.compile(r"(curl|wget).*(\||&&).*\b(bash|sh)\b", re.IGNORECASE),
            "Fetches and executes a remote script at build time.",
            95,
        ),
        (
            re.compile(r"/dev/tcp|nc\s+-e|bash\s+-i", re.IGNORECASE),
            "Contains a reverse-shell pattern.",
            100,
        ),
        (
            re.compile(r"169\.254\.169\.254", re.IGNORECASE),
            "Attempts to contact the instance metadata endpoint.",
            100,
        ),
        (
            re.compile(r"\b(xmrig|minerd|coinhive)\b", re.IGNORECASE),
            "References known crypto-mining tools.",
            100,
        ),
        (
            re.compile(r"--privileged|--cap-add|SYS_ADMIN|SYS_PTRACE", re.IGNORECASE),
            "Requests privileged execution primitives.",
            100,
        ),
    ]

    _high_patterns = [
        (
            re.compile(r"base64\s+-d.*\|\s*(bash|sh)", re.IGNORECASE),
            "Decodes an obfuscated payload and executes it.",
            75,
        ),
        (
            re.compile(r"\bgit\s+clone\b", re.IGNORECASE),
            "Fetches a live repository during build instead of using the archived build context.",
            55,
        ),
    ]

    _medium_patterns = [
        (
            re.compile(r"pip\s+install\s+https?://", re.IGNORECASE),
            "Installs Python dependencies directly from a URL rather than a trusted package index.",
            35,
        ),
        (
            re.compile(r"ADD\s+https?://", re.IGNORECASE),
            "Downloads remote content directly into the image build context.",
            30,
        ),
    ]

    def review(self, dockerfile_content: str) -> SubmissionReviewResult:
        violations: list[SubmissionViolation] = []
        warnings: list[SubmissionWarning] = []
        risk_score = 0
        executable_lines: list[tuple[int, str]] = []

        for line_no, raw_line in enumerate(dockerfile_content.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                if any(pattern.search(stripped) for pattern in self._override_comment_patterns):
                    violations.append(
                        SubmissionViolation(
                            severity="high",
                            line=line_no,
                            instruction=stripped,
                            reason="Comment attempts to influence the security review process.",
                        )
                    )
                    risk_score = max(risk_score, 70)
                continue

            executable_lines.append((line_no, stripped))

        for line_no, instruction in executable_lines:
            for pattern, reason, score in self._critical_patterns:
                if pattern.search(instruction):
                    violations.append(
                        SubmissionViolation(
                            severity="critical",
                            line=line_no,
                            instruction=instruction,
                            reason=reason,
                        )
                    )
                    risk_score = max(risk_score, score)

            for pattern, reason, score in self._high_patterns:
                if pattern.search(instruction):
                    violations.append(
                        SubmissionViolation(
                            severity="high",
                            line=line_no,
                            instruction=instruction,
                            reason=reason,
                        )
                    )
                    risk_score = max(risk_score, score)

            for pattern, reason, score in self._medium_patterns:
                if pattern.search(instruction):
                    violations.append(
                        SubmissionViolation(
                            severity="medium",
                            line=line_no,
                            instruction=instruction,
                            reason=reason,
                        )
                    )
                    risk_score = max(risk_score, score)

            if instruction.upper().startswith("FROM ") and ":latest" in instruction.lower():
                warnings.append(
                    SubmissionWarning(
                        severity="low",
                        line=line_no,
                        reason="Using ':latest' is non-deterministic and weakens reproducibility.",
                    )
                )

        if not any(instruction.upper().startswith("USER ") for _, instruction in executable_lines):
            warnings.append(
                SubmissionWarning(
                    severity="low",
                    line=0,
                    reason="No USER instruction found; final image may run as root.",
                )
            )

        approved = risk_score <= 70 and not any(item.severity == "critical" for item in violations)
        educational_hint = self._educational_hint(violations, warnings)

        return SubmissionReviewResult(
            approved=approved,
            risk_score=risk_score,
            violations=violations,
            warnings=warnings,
            educational_hint=educational_hint,
        )

    @staticmethod
    def _educational_hint(
        violations: list[SubmissionViolation],
        warnings: list[SubmissionWarning],
    ) -> str:
        if violations:
            top_violation = violations[0]
            if "remote script" in top_violation.reason.lower():
                return "Avoid executing remote scripts during build. Copy version-controlled files into the image so the build remains auditable."
            if "repository" in top_violation.reason.lower():
                return "Use the archived challenge context instead of cloning repositories during build so scoring stays reproducible."
            return "Simplify the Dockerfile to auditable build steps only, then resubmit."

        if warnings:
            return "The Dockerfile is executable, but tightening reproducibility and runtime user configuration will improve its score."

        return "Submission cleared the local AI gate."


def enforce_prechecks(dockerfile_content: str, max_submission_size_bytes: int) -> None:
    encoded = dockerfile_content.encode("utf-8")
    if len(encoded) > max_submission_size_bytes:
        raise SubmissionPrecheckError(
            f"Dockerfile exceeds the {max_submission_size_bytes}-byte submission limit."
        )

    if "\x00" in dockerfile_content:
        raise SubmissionPrecheckError("Dockerfile contains null bytes and was rejected.")

    if not dockerfile_content.strip():
        raise SubmissionPrecheckError("Dockerfile submission is empty.")
