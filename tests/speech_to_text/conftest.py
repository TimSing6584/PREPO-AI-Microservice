"""
Shared fixtures for speech-to-text tests.

generate_wav_bytes() builds a minimal valid WAV file in memory using only
the Python standard library (struct + wave), so no extra dependencies are
needed just for test fixtures.
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
    """Minimal app with only the STT router — avoids importing unfinished modules."""
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(stt_router)
    return app


# ---------------------------------------------------------------------------
# Audio fixture
# ---------------------------------------------------------------------------

def generate_wav_bytes(
    duration_s: float = 1.0,
    sample_rate: int = 16000,
    frequency: float = 440.0,
) -> bytes:
    """Return a minimal PCM WAV file as bytes (sine wave, no speech)."""
    n_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)          # mono
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wf.writeframes(struct.pack("<h", value))
    return buf.getvalue()


@pytest.fixture()
def wav_bytes() -> bytes:
    """A 1-second 440 Hz sine-wave WAV in memory."""
    return generate_wav_bytes()


@pytest.fixture()
def client() -> TestClient:
    """FastAPI test client — STT router only."""
    return TestClient(_make_app())
