from pydantic import BaseModel

class AssessmentInput(BaseModel):
    transcript: str
    statement: str
    model_answer: str

class AssessmentOutput(BaseModel):
    score: float        # 0.0 to 100.0
    feedback: str