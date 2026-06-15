from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..assessment.config import assessment_config
from ..assessment.service import AssessmentService
from ..speech_to_text.config import stt_config
from ..speech_to_text.service import SpeechToTextService
from ..speech_to_text.utils import validate_audio
from ..utils.security import verify_jwt
from .schemas import PipelineInput, PipelineOutput
from .service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

def get_pipeline_service() -> PipelineService:
    return PipelineService(
        stt=SpeechToTextService(config=stt_config),
        assessment=AssessmentService(config=assessment_config),
    )

@router.post("/speech-assess", response_model=PipelineOutput)
async def speech_assess(
    audio: UploadFile = File(...),
    statement: str = Form(...),
    model_answer: str = Form(...),
    service: PipelineService = Depends(get_pipeline_service),
    payload: dict = Depends(verify_jwt),
):
    user_id = payload.get("user_id")
    
    audio_bytes = await audio.read()
    canonical_mime = validate_audio(audio.content_type, audio_bytes)

    return await service.run(
        audio_bytes,
        canonical_mime,
        PipelineInput(statement=statement, model_answer=model_answer),
    )
