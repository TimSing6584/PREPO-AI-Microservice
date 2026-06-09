import httpx
from .config import STTConfig
from .schemas import TranscriptOutput
from .exceptions import TranscriptionError

# Deepgram query params used on every request.
DEEPGRAM_PARAMS = {
    "model": "nova-3",

    # smart_format applies punctuation, paragraphs, number formatting,
    # and other readability improvements in one flag — replaces punctuate=true
    "smart_format": "true",

    # diarize labels each word with a speaker ID (speaker:0, speaker:1 …)
    # useful if audio contains multiple speakers (e.g. interview, conversation)
    "diarize": "false",

    # utterances splits the transcript into turn-based segments with
    # start/end timestamps — pairs well with diarize
    "utterances": "false",

    # language auto-detection
    "language": "en",
}

# Timeout config (seconds):
#   connect  — time to establish the TCP connection
#   write    — time to finish uploading the audio bytes
#   read     — time waiting for Deepgram to respond (transcription time)
#   pool     — time waiting to acquire a connection from the pool
DEEPGRAM_TIMEOUT = httpx.Timeout(
    connect=10.0,
    write=60.0,   # large files need more upload time
    read=120.0,   # 1–2 min audio can take a while to process
    pool=10.0,
)


class SpeechToTextService:
    def __init__(self, config: STTConfig):
        self.config = config

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptOutput:
        async with httpx.AsyncClient(timeout=DEEPGRAM_TIMEOUT) as client:
            response = await client.post(
                self.config.DEEPGRAM_URL,
                params=DEEPGRAM_PARAMS,
                headers={
                    "Authorization": f"Token {self.config.DEEPGRAM_API_KEY}",
                    "Content-Type": mime_type,
                },
                content=audio_bytes,
            )

        if response.status_code != 200:
            raise TranscriptionError(f"STT failed: {response.text}")

        transcript = (
            response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
        return TranscriptOutput(transcript=transcript)
