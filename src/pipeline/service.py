from ..speech_to_text.service import SpeechToTextService
from ..assessment.service import AssessmentService
from ..assessment.schemas import AssessmentInput
from .schemas import PipelineInput, PipelineOutput

class PipelineService:
    def __init__(self, stt: SpeechToTextService, assessment: AssessmentService):
        self.stt = stt
        self.assessment = assessment

    async def run(self, audio_bytes: bytes, mime_type: str, meta: PipelineInput) -> PipelineOutput:
        # Step 1: Speech → Text
        transcript_result = await self.stt.transcribe(audio_bytes, mime_type)

        # Step 2: Text → Assessment
        assessment_result = await self.assessment.assess(
            AssessmentInput(
                transcript=transcript_result.transcript,
                statement=meta.statement,
                model_answer=meta.model_answer,
            )
        )

        return PipelineOutput(
            transcript=transcript_result.transcript,
            score=assessment_result.score,
            feedback=assessment_result.feedback,
        )
