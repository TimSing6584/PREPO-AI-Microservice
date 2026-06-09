"""
Unit tests for SpeechToTextService and the /transcription endpoint.

All external HTTP calls to Deepgram are mocked with pytest-mock / unittest.mock,
so these tests run offline without a real API key.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from fastapi.testclient import TestClient

from src.speech_to_text.service import SpeechToTextService
from src.speech_to_text.config import STTConfig
from src.speech_to_text.exceptions import TranscriptionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deepgram_response(transcript: str, status_code: int = 200) -> MagicMock:
    """Build a fake httpx.Response-like object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {
        "results": {
            "channels": [
                {"alternatives": [{"transcript": transcript}]}
            ]
        }
    }
    mock_resp.text = json.dumps({"error": "bad request"})
    return mock_resp


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------

class TestSpeechToTextService:

    @pytest.mark.asyncio
    async def test_transcribe_returns_transcript(self, wav_bytes):
        """Happy path: Deepgram returns 200 with a transcript."""
        expected = "hello world"
        config = STTConfig()

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response(expected))

            service = SpeechToTextService(config=config)
            result = await service.transcribe(wav_bytes, "audio/wav")

        assert result.transcript == expected

    @pytest.mark.asyncio
    async def test_transcribe_empty_transcript(self, wav_bytes):
        """Deepgram returns 200 but empty transcript (e.g. silence)."""
        config = STTConfig()

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response(""))

            service = SpeechToTextService(config=config)
            result = await service.transcribe(wav_bytes, "audio/wav")

        assert result.transcript == ""

    @pytest.mark.asyncio
    async def test_transcribe_raises_on_non_200(self, wav_bytes):
        """Non-200 response from Deepgram should raise TranscriptionError."""
        config = STTConfig()
        bad_resp = _deepgram_response("", status_code=401)

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=bad_resp)

            service = SpeechToTextService(config=config)
            with pytest.raises(TranscriptionError):
                await service.transcribe(wav_bytes, "audio/wav")

    @pytest.mark.asyncio
    async def test_transcribe_sends_correct_headers(self, wav_bytes):
        """Authorization header must include the configured API key."""
        config = STTConfig(DEEPGRAM_API_KEY="test-key-123")

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response("hi"))

            service = SpeechToTextService(config=config)
            await service.transcribe(wav_bytes, "audio/wav")

        _, call_kwargs = mock_client.post.call_args
        assert call_kwargs["headers"]["Authorization"] == "Token test-key-123"

    @pytest.mark.asyncio
    async def test_transcribe_sends_audio_bytes(self, wav_bytes):
        """The raw audio bytes must be forwarded as the request body."""
        config = STTConfig()

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response("test"))

            service = SpeechToTextService(config=config)
            await service.transcribe(wav_bytes, "audio/wav")

        _, call_kwargs = mock_client.post.call_args
        assert call_kwargs["content"] == wav_bytes


# ---------------------------------------------------------------------------
# Router / endpoint unit tests (mocked Deepgram)
# ---------------------------------------------------------------------------

class TestTranscribeEndpoint:

    def _post_audio(self, client: TestClient, audio_bytes: bytes, filename: str = "test.wav"):
        return client.post(
            "/transcription",
            files={"audio": (filename, audio_bytes, "audio/wav")},
        )

    def test_endpoint_returns_200_with_transcript(self, client, wav_bytes):
        expected = "this is a test"

        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response(expected))

            resp = self._post_audio(client, wav_bytes)

        assert resp.status_code == 200
        assert resp.json() == {"transcript": expected}

    def test_endpoint_returns_502_on_deepgram_error(self, client, wav_bytes):
        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response("", status_code=500))

            resp = self._post_audio(client, wav_bytes)

        assert resp.status_code == 502
        assert "detail" in resp.json()

    def test_endpoint_missing_file_returns_422(self, client):
        """Posting without the audio field should return 422 Unprocessable Entity."""
        resp = client.post("/transcription")
        assert resp.status_code == 422

    def test_endpoint_response_schema(self, client, wav_bytes):
        """Response must have exactly the 'transcript' key."""
        with patch("src.speech_to_text.service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_deepgram_response("ok"))

            resp = self._post_audio(client, wav_bytes)

        body = resp.json()
        assert set(body.keys()) == {"transcript"}
        assert isinstance(body["transcript"], str)
