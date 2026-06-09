from fastapi import APIRouter, UploadFile, File, Depends
from .service import SpeechToTextService
from .schemas import TranscriptOutput
from .config import stt_config
from .utils import validate_audio

router = APIRouter(prefix="/transcription", tags=["speech-to-text"])

def get_stt_service() -> SpeechToTextService:
    return SpeechToTextService(config=stt_config)

@router.post("", response_model=TranscriptOutput)
async def transcribe(
    audio: UploadFile = File(...),
    service: SpeechToTextService = Depends(get_stt_service),
):
    audio_bytes = await audio.read()

    # validate MIME type, size, and magic bytes; returns canonical mime string
    canonical_mime = validate_audio(audio.content_type, audio_bytes)

    return await service.transcribe(audio_bytes, canonical_mime)
