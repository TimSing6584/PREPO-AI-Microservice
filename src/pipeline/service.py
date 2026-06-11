from ..assessment.exceptions import AssessmentError
from ..assessment.schemas import AssessmentInput
from ..assessment.service import AssessmentService
from ..speech_to_text.exceptions import TranscriptionError
from ..speech_to_text.service import SpeechToTextService
from .exceptions import PipelineError
from .schemas import PipelineInput, PipelineOutput


class PipelineService:
    def __init__(self, stt: SpeechToTextService, assessment: AssessmentService):
        self.stt = stt
        self.assessment = assessment

    async def run(self, audio_bytes: bytes, mime_type: str, meta: PipelineInput) -> PipelineOutput:
        try:
            transcript_result = await self.stt.transcribe(audio_bytes, mime_type)
            if len(transcript_result.transcript) == 0:
                return PipelineOutput(
                    transcript="No speech detected in the audio.",
                    score=0.0,
                    feedback="No speech detected in the audio.",
                )
            
        except TranscriptionError as exc:
            raise PipelineError(exc.detail) from exc

        try:
            assessment_result = await self.assessment.assess(
                AssessmentInput(
                    transcript=transcript_result.transcript,
                    statement=meta.statement,
                    model_answer=meta.model_answer,
                )
            )
        except AssessmentError as exc:
            raise PipelineError(exc.detail) from exc

        return PipelineOutput(
            transcript=transcript_result.transcript,
            score=assessment_result.score,
            feedback=assessment_result.feedback,
        )
