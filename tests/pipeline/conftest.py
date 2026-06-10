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


def _silent_wav_bytes(duration_s: float = 1.0, sample_rate: int = 16000) -> bytes:
    n_frames = int(duration_s * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()


@pytest.fixture()
def wav_bytes() -> bytes:
    return _silent_wav_bytes()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(_make_app())
