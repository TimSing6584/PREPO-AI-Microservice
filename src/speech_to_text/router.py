from fastapi import APIRouter, UploadFile, File, Depends
from .service import SpeechToTextService
from .schemas import TranscriptOutput
from .config import stt_config

router = APIRouter(prefix="/transcribe", tags=["speech-to-text"])

def get_stt_service() -> SpeechToTextService:
    return SpeechToTextService(config=stt_config)

@router.post("", response_model=TranscriptOutput)
async def transcribe(
    audio: UploadFile = File(...),
    service: SpeechToTextService = Depends(get_stt_service),
):
    audio_bytes = await audio.read()
    return await service.transcribe(audio_bytes, audio.content_type)
