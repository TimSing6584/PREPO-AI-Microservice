from pydantic import BaseModel


class PipelineInput(BaseModel):
    statement: str
    model_answer: str


class PipelineOutput(BaseModel):
    transcript: str
    score: float
    feedback: str
