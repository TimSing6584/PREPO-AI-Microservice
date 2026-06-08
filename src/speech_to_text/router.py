from fastapi import APIRouter, UploadFile, File, Depends
from .service import SpeechToTextService
from .schemas import TranscriptOutput
from .config import stt_config
from .utils import validate_audio

router = APIRouter(prefix="/transcribe", tags=["speech-to-text"])

def get_stt_service() -> SpeechToTextService:
    return SpeechToTextService(config=stt_config)

@router.post("", response_model=TranscriptOutput)
async def transcribe(
    audio: UploadFile = File(...),
    service: SpeechToTextService = Depends(get_stt_service),
):
    audio_bytes = await audio.read()

    # validate MIME type and file size; returns canonical mime string
    canonical_mime = validate_audio(audio.content_type, len(audio_bytes))

    return await service.transcribe(audio_bytes, canonical_mime)
