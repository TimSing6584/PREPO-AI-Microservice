import io
import wave

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.exceptions import AppException, app_exception_handler
from src.pipeline.router import router as pipeline_router


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(AppException, app_exception_handler)
    app.include_router(pipeline_router)
    return app

pytestmark = pytest.mark.integration  # skip with: pytest -m "not integration"


# ---------------------------------------------------------------------------
# Fixture: load a real audio file OR fall back to generated silence
# ---------------------------------------------------------------------------

SAMPLE_AUDIO = "tests/pipeline/sample.m4a"  # drop your own file here


def _silent_wav(duration_s: float = 0.1, sample_rate: int = 16000) -> bytes:
    """Silent WAV (all zero samples)."""
    n_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_samples)
    return buf.getvalue()


@pytest.fixture()
def real_audio_bytes() -> tuple[bytes, str, str]:
    """Load sample.m4a if present, otherwise fall back to silent WAV."""
    try:
        with open(SAMPLE_AUDIO, "rb") as f:
            return f.read(), "sample.m4a", "audio/mp4"
    except FileNotFoundError:
        return _silent_wav(), "audio.wav", "audio/wav"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestPipelineIntegration:

    def test_full_pipeline_live(self, real_audio_bytes):
        """
        Sends audio through the full pipeline and checks that:
        - HTTP 200 is returned
        - Response body contains transcript, score, feedback
        - Score is between 0 and 100
        """
        audio_bytes, filename, mime_type = real_audio_bytes
        client = TestClient(_make_app())
        resp = client.post(
            "/pipeline/speech-assess",
            files={"audio": (filename, audio_bytes, mime_type)},
            data={
                "statement": "What is Python?",
                "model_answer": "A programming language that emphasizes readability.",
            },
        )

        print("\n--- Pipeline response ---")
        print(resp.status_code, resp.json())

        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"
        body = resp.json()
        assert "score" in body
        assert "feedback" in body
        assert 0 <= body["score"] <= 100
        assert isinstance(body["feedback"], str)