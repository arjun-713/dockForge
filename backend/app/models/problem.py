from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Difficulty = Literal["easy", "medium", "hard"]
ChallengeTier = Literal["basic", "medium", "hard", "advanced"]
ChallengeCategory = Literal["python", "node", "nginx", "go", "java", "database", "compose", "kubernetes", "general"]


DIFFICULTY_TIER_MAP: dict[Difficulty, ChallengeTier] = {
    "easy": "basic",
    "medium": "medium",
    "hard": "hard",
}


def infer_category(problem_id: str, base_image: str) -> ChallengeCategory:
    normalized = f"{problem_id} {base_image}".lower()
    if "fastapi" in normalized or "flask" in normalized or "python" in normalized:
        return "python"
    if "node" in normalized or "express" in normalized or "next" in normalized:
        return "node"
    if "nginx" in normalized:
        return "nginx"
    if "golang" in normalized or "go:" in normalized:
        return "go"
    if "java" in normalized or "spring" in normalized:
        return "java"
    if "postgres" in normalized or "redis" in normalized or "mongo" in normalized:
        return "database"
    if "k8s" in normalized or "kubernetes" in normalized:
        return "kubernetes"
    return "general"


class ChallengeConstraint(BaseModel):
    id: str
    description: str
    kind: Literal["runtime", "best_practice", "optimization", "security"] = "runtime"


class ChallengeSnapshot(BaseModel):
    source: Literal["archived", "local-dev"] = "local-dev"
    snapshot_ref: str = "local-problems-directory"


class ProblemMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str] = Field(default_factory=list)
    app_port: int = Field(alias="appPort")
    base_image: str = Field(alias="baseImage")
    health_path: str = Field(default="/health", alias="healthPath")
    category: ChallengeCategory | None = None
    tier: ChallengeTier | None = None
    repo_url: str = Field(default="", alias="repoUrl")
    constraints: list[ChallengeConstraint] = Field(default_factory=list)
    baseline_build_ms: int = Field(default=30000, alias="baselineBuildMs")
    baseline_size_bytes: int = Field(default=250_000_000, alias="baselineSizeBytes")
    snapshot: ChallengeSnapshot = Field(default_factory=ChallengeSnapshot)

    @model_validator(mode="before")
    @classmethod
    def populate_architecture_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        difficulty = normalized.get("difficulty", "easy")
        normalized.setdefault("tier", DIFFICULTY_TIER_MAP.get(difficulty, "basic"))
        normalized.setdefault(
            "category",
            infer_category(
                problem_id=str(normalized.get("id", "")),
                base_image=str(normalized.get("baseImage", normalized.get("base_image", ""))),
            ),
        )
        normalized.setdefault("constraints", default_constraints_for_metadata(normalized))
        return normalized


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str]
    category: ChallengeCategory
    tier: ChallengeTier
    repo_url: str = Field(default="", alias="repoUrl")


class ProblemDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str]
    app_port: int = Field(alias="appPort")
    base_image: str = Field(alias="baseImage")
    health_path: str = Field(alias="healthPath")
    category: ChallengeCategory
    tier: ChallengeTier
    repo_url: str = Field(default="", alias="repoUrl")
    constraints: list[ChallengeConstraint] = Field(default_factory=list)
    baseline_build_ms: int = Field(alias="baselineBuildMs")
    baseline_size_bytes: int = Field(alias="baselineSizeBytes")
    snapshot: ChallengeSnapshot
    readme: str


class ProblemListResponse(BaseModel):
    problems: list[ProblemSummary]


def default_constraints_for_metadata(data: dict[str, Any]) -> list[dict[str, str]]:
    app_port = str(data.get("appPort", data.get("app_port", "the expected app port")))
    base_image = str(data.get("baseImage", data.get("base_image", "the declared base image")))

    return [
        {
            "id": "runtime-port",
            "description": f"Serve the application on port {app_port} and satisfy the configured health check.",
            "kind": "runtime",
        },
        {
            "id": "non-root",
            "description": "Run the final container as a non-root user whenever the base image allows it.",
            "kind": "best_practice",
        },
        {
            "id": "base-image",
            "description": f"Start from an image compatible with {base_image} or justify deviations through equivalent runtime behavior.",
            "kind": "optimization",
        },
        {
            "id": "reproducibility",
            "description": "Avoid non-deterministic tags and remote install scripts that reduce auditability.",
            "kind": "security",
        },
    ]
