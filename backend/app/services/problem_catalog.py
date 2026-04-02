import json
from pathlib import Path

from app.models.problem import ProblemDetail, ProblemMetadata, ProblemSummary


class ProblemCatalog:
    def __init__(self, problems_dir: str) -> None:
        self.problems_dir = Path(problems_dir)

    def list_problems(self) -> list[ProblemSummary]:
        summaries: list[ProblemSummary] = []
        for problem_dir in sorted(self._problem_dirs()):
            metadata = self._read_metadata(problem_dir)
            summaries.append(
                ProblemSummary(
                    id=metadata.id,
                    title=metadata.title,
                    difficulty=metadata.difficulty,
                    concepts=metadata.concepts,
                    category=metadata.category or "general",
                    tier=metadata.tier or "basic",
                    repo_url=metadata.repo_url,
                )
            )
        return summaries

    def get_problem(self, problem_id: str) -> ProblemDetail | None:
        problem_dir = self.get_problem_dir(problem_id)
        if not problem_dir.is_dir():
            return None

        metadata = self._read_metadata(problem_dir)
        readme_path = problem_dir / "README.md"
        readme_content = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

        return ProblemDetail(
            id=metadata.id,
            title=metadata.title,
            difficulty=metadata.difficulty,
            concepts=metadata.concepts,
            app_port=metadata.app_port,
            base_image=metadata.base_image,
            health_path=metadata.health_path,
            category=metadata.category or "general",
            tier=metadata.tier or "basic",
            repo_url=metadata.repo_url,
            constraints=metadata.constraints,
            baseline_build_ms=metadata.baseline_build_ms,
            baseline_size_bytes=metadata.baseline_size_bytes,
            snapshot=metadata.snapshot,
            readme=readme_content,
        )

    def get_metadata(self, problem_id: str) -> ProblemMetadata | None:
        problem_dir = self.get_problem_dir(problem_id)
        if not problem_dir.is_dir():
            return None
        return self._read_metadata(problem_dir)

    def get_problem_dir(self, problem_id: str) -> Path:
        return self.problems_dir / problem_id

    def _problem_dirs(self) -> list[Path]:
        if not self.problems_dir.exists():
            return []
        return [path for path in self.problems_dir.iterdir() if path.is_dir() and (path / "problem.json").exists()]

    @staticmethod
    def _read_metadata(problem_dir: Path) -> ProblemMetadata:
        metadata_path = problem_dir / "problem.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return ProblemMetadata.model_validate(metadata)
