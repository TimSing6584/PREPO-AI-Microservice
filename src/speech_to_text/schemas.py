from pydantic import BaseModel

class TranscriptOutput(BaseModel):
    transcript: str
