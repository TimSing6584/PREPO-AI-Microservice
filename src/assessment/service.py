import json
from openai import AsyncOpenAI
from .config import AssessmentConfig
from .schemas import AssessmentInput, AssessmentOutput
from .utils import build_scoring_prompt
from .exceptions import AssessmentError

class AssessmentService:
    def __init__(self, config: AssessmentConfig):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL

    async def assess(self, input: AssessmentInput) -> AssessmentOutput:
        prompt = build_scoring_prompt(
            input.transcript,
            input.statement,
            input.model_answer
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                temperature=0.2,   # low temp = consistent scoring
                n=1,
                max_tokens=256
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            return AssessmentOutput(
                score=float(data["score"]),
                feedback=data["feedback"]
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise AssessmentError(f"Failed to parse LLM response: {e}")
        except Exception as e:
            raise AssessmentError(f"LLM call failed: {e}")