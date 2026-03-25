from pydantic import BaseModel


class SubmissionRequest(BaseModel):
    problem_id: str
    dockerfile_content: str


class SubmissionResponse(BaseModel):
    passed: bool
    logs: str
