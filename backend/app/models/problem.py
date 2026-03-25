from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["easy", "medium", "hard"]


class ProblemMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str] = Field(default_factory=list)
    app_port: int = Field(alias="appPort")
    base_image: str = Field(alias="baseImage")


class ProblemSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str]


class ProblemDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    difficulty: Difficulty
    concepts: list[str]
    app_port: int = Field(alias="appPort")
    base_image: str = Field(alias="baseImage")
    readme: str


class ProblemListResponse(BaseModel):
    problems: list[ProblemSummary]
