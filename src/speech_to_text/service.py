import httpx
from .config import STTConfig
from .schemas import TranscriptOutput
from .exceptions import TranscriptionError

class SpeechToTextService:
    def __init__(self, config: STTConfig):
        self.config = config

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptOutput:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.DEEPGRAM_URL,
                headers={"Authorization": f"Token {self.config.DEEPGRAM_API_KEY}"},
                content=audio_bytes,
            )
        if response.status_code != 200:
            raise TranscriptionError(f"STT failed: {response.text}")

        transcript = (
            response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
        return TranscriptOutput(transcript=transcript)
