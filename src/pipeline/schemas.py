from pydantic import BaseModel


class PipelineInput(BaseModel):
    statement: str
    model_answer: str

class PipelineOutput(BaseModel):
    score: float
    feedback: str
