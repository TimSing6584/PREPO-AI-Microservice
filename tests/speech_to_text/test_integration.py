"""
Integration test — hits the real Deepgram API.

Run only when you want to verify the live connection:

    pytest tests/speech_to_text/test_integration.py -v -s

The test is marked with `integration` so you can skip it in CI:

    pytest -m "not integration"

It uses a 1-second silent WAV (all zeros), which Deepgram will transcribe as
an empty string.  If you want to verify an actual transcript, drop a real
audio file at tests/speech_to_text/sample.wav and adjust the fixture below.
"""

import io
import math
import struct
import wave

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.exceptions import AppException, app_exception_handler
from src.speech_to_text.router import router as stt_router


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(stt_router)
    return app

pytestmark = pytest.mark.integration  # skip with: pytest -m "not integration"


# ---------------------------------------------------------------------------
# Fixture: load a real audio file OR fall back to generated silence
# ---------------------------------------------------------------------------

SAMPLE_WAV = "tests/speech_to_text/sample.wav"   # drop your own file here


def _silent_wav(duration_s: float = 0.1, sample_rate: int = 16000) -> bytes:
    """1-second silent WAV (all zero samples)."""
    n_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)
    return buf.getvalue()


@pytest.fixture()
def real_audio_bytes() -> bytes:
    try:
        with open(SAMPLE_WAV, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return _silent_wav()


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestIntegrationTranscribe:

    def test_transcribe_live_audio(self, real_audio_bytes):
        """
        Sends audio to the real Deepgram endpoint and checks that:
        - HTTP 200 is returned
        - Response body contains a 'transcript' string key
        """
        client = TestClient(_make_app())
        resp = client.post(
            "/transcription",
            files={"audio": ("audio.wav", real_audio_bytes, "audio/wav")},
        )

        print("\n--- Deepgram response ---")
        print(resp.status_code, resp.json())

        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"
        body = resp.json()
        assert "transcript" in body
        assert isinstance(body["transcript"], str)

    def test_transcribe_rejects_mime_content_mismatch(self, real_audio_bytes):
        """WAV bytes declared as audio/mpeg must be rejected before Deepgram."""
        client = TestClient(_make_app())
        resp = client.post(
            "/transcription",
            files={"audio": ("audio.mp3", real_audio_bytes, "audio/mpeg")},
        )
        assert resp.status_code == 415
        assert "does not match" in resp.json()["detail"]
