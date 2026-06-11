from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.assessment.exceptions import AssessmentError
from src.assessment.schemas import AssessmentInput, AssessmentOutput
from src.pipeline.exceptions import PipelineError
from src.pipeline.schemas import PipelineInput, PipelineOutput
from src.pipeline.service import PipelineService
from src.speech_to_text.exceptions import TranscriptionError
from src.speech_to_text.schemas import TranscriptOutput


def _make_pipeline_service(
    transcript: str = "hello world",
    score: float = 87.5,
    feedback: str = "good answer",
) -> tuple[PipelineService, MagicMock, MagicMock]:
    stt = MagicMock()
    stt.transcribe = AsyncMock(return_value=TranscriptOutput(transcript=transcript))

    assessment = MagicMock()
    assessment.assess = AsyncMock(
        return_value=AssessmentOutput(score=score, feedback=feedback)
    )

    return PipelineService(stt=stt, assessment=assessment), stt, assessment


class TestPipelineService:
    @pytest.mark.asyncio
    async def test_run_returns_pipeline_output(self):
        service, stt, assessment = _make_pipeline_service()
        meta = PipelineInput(statement="What is Python?", model_answer="A programming language.")

        result = await service.run(b"audio-bytes", "audio/wav", meta)

        assert result == PipelineOutput(
            transcript="hello world",
            score=87.5,
            feedback="good answer",
        )
        stt.transcribe.assert_awaited_once_with(b"audio-bytes", "audio/wav")
        assessment.assess.assert_awaited_once_with(
            AssessmentInput(
                transcript="hello world",
                statement="What is Python?",
                model_answer="A programming language.",
            )
        )

    @pytest.mark.asyncio
    async def test_run_propagates_stt_error(self):
        service, stt, assessment = _make_pipeline_service()
        stt.transcribe = AsyncMock(side_effect=TranscriptionError("transcription failed"))
        meta = PipelineInput(statement="What is Python?", model_answer="A programming language.")

        with pytest.raises(PipelineError) as excinfo:
            await service.run(b"audio-bytes", "audio/wav", meta)

        assert excinfo.value.detail == "transcription failed"
        assessment.assess.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_propagates_assessment_error(self):
        service, stt, assessment = _make_pipeline_service()
        assessment.assess = AsyncMock(side_effect=AssessmentError("assessment failed"))
        meta = PipelineInput(statement="What is Python?", model_answer="A programming language.")

        with pytest.raises(PipelineError) as excinfo:
            await service.run(b"audio-bytes", "audio/wav", meta)

        assert excinfo.value.detail == "assessment failed"
        stt.transcribe.assert_awaited_once_with(b"audio-bytes", "audio/wav")

    @pytest.mark.asyncio
    async def test_run_passes_transcript_to_assessment(self):
        service, stt, assessment = _make_pipeline_service(transcript="transcribed text")
        meta = PipelineInput(statement="What is Python?", model_answer="A programming language.")

        await service.run(b"audio-bytes", "audio/wav", meta)

        assessment.assess.assert_awaited_once_with(
            AssessmentInput(
                transcript="transcribed text",
                statement="What is Python?",
                model_answer="A programming language.",
            )
        )
        stt.transcribe.assert_awaited_once_with(b"audio-bytes", "audio/wav")


class TestPipelineEndpoint:
    def _post_pipeline(self, client, audio_bytes: bytes, statement: str, model_answer: str):
        return client.post(
            "/pipeline/speech-assess",
            files={"audio": ("test.wav", audio_bytes, "audio/wav")},
            data={"statement": statement, "model_answer": model_answer},
        )

    def test_endpoint_returns_200(self, client, wav_bytes):
        service, stt, assessment = _make_pipeline_service(
            transcript="this is a transcript",
            score=91.0,
            feedback="strong answer",
        )

        with patch("src.pipeline.router.SpeechToTextService", return_value=stt), patch(
            "src.pipeline.router.AssessmentService", return_value=assessment
        ), patch("src.pipeline.router.validate_audio", return_value="audio/mpeg") as mock_validate:
            resp = self._post_pipeline(
                client,
                wav_bytes,
                statement="What is Python?",
                model_answer="A programming language.",
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "transcript": "this is a transcript",
            "score": 91.0,
            "feedback": "strong answer",
        }
        mock_validate.assert_called_once_with("audio/wav", wav_bytes)
        stt.transcribe.assert_awaited_once_with(wav_bytes, "audio/mpeg")
        assessment.assess.assert_awaited_once_with(
            AssessmentInput(
                transcript="this is a transcript",
                statement="What is Python?",
                model_answer="A programming language.",
            )
        )

    def test_endpoint_returns_502_on_stt_failure(self, client, wav_bytes):
        service, stt, assessment = _make_pipeline_service()
        stt.transcribe = AsyncMock(side_effect=TranscriptionError("stt failed"))

        with patch("src.pipeline.router.SpeechToTextService", return_value=stt), patch(
            "src.pipeline.router.AssessmentService", return_value=assessment
        ), patch("src.pipeline.router.validate_audio", return_value="audio/mpeg"):
            resp = self._post_pipeline(
                client,
                wav_bytes,
                statement="What is Python?",
                model_answer="A programming language.",
            )

        assert resp.status_code == 502
        assert "detail" in resp.json()

    def test_endpoint_returns_502_on_assessment_failure(self, client, wav_bytes):
        service, stt, assessment = _make_pipeline_service()
        assessment.assess = AsyncMock(side_effect=AssessmentError("assessment failed"))

        with patch("src.pipeline.router.SpeechToTextService", return_value=stt), patch(
            "src.pipeline.router.AssessmentService", return_value=assessment
        ), patch("src.pipeline.router.validate_audio", return_value="audio/mpeg"):
            resp = self._post_pipeline(
                client,
                wav_bytes,
                statement="What is Python?",
                model_answer="A programming language.",
            )

        assert resp.status_code == 502
        assert "detail" in resp.json()

    def test_endpoint_missing_audio_returns_422(self, client):
        resp = client.post(
            "/pipeline/speech-assess",
            data={"statement": "What is Python?", "model_answer": "A programming language."},
        )

        assert resp.status_code == 422

    def test_endpoint_missing_statement_returns_422(self, client, wav_bytes):
        resp = client.post(
            "/pipeline/speech-assess",
            files={"audio": ("test.wav", wav_bytes, "audio/wav")},
            data={"model_answer": "A programming language."},
        )

        assert resp.status_code == 422

    def test_endpoint_response_schema(self, client, wav_bytes):
        service, stt, assessment = _make_pipeline_service(
            transcript="transcript",
            score=75.0,
            feedback="feedback",
        )

        with patch("src.pipeline.router.SpeechToTextService", return_value=stt), patch(
            "src.pipeline.router.AssessmentService", return_value=assessment
        ), patch("src.pipeline.router.validate_audio", return_value="audio/mpeg"):
            resp = self._post_pipeline(
                client,
                wav_bytes,
                statement="What is Python?",
                model_answer="A programming language.",
            )

        body = resp.json()
        assert set(body.keys()) == {"transcript", "score", "feedback"}
        assert isinstance(body["transcript"], str)
        assert isinstance(body["score"], (int, float))
        assert isinstance(body["feedback"], str)
