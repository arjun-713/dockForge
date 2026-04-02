from datetime import datetime

from pydantic import BaseModel, Field


class LeaderboardEntry(BaseModel):
    submission_id: str = Field(alias="submissionId")
    problem_id: str = Field(alias="problemId")
    final_score: int = Field(alias="finalScore")
    build_time_score: int = Field(alias="buildTimeScore")
    image_size_score: int = Field(alias="imageSizeScore")
    best_practice_score: int = Field(alias="bestPracticeScore")
    difficulty_multiplier: float = Field(alias="difficultyMultiplier")
    created_at: datetime = Field(alias="createdAt")


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
