from fastapi import APIRouter, UploadFile, File, Depends, Form
from .service import PipelineService
from .schemas import PipelineOutput
from ..speech_to_text.service import SpeechToTextService
from ..speech_to_text.config import stt_config
from ..assessment.service import AssessmentService
from ..assessment.config import assessment_config

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
):
    audio_bytes = await audio.read()
    from .schemas import PipelineInput
    return await service.run(audio_bytes, audio.content_type, PipelineInput(
        statement=statement,
        model_answer=model_answer,
    ))
