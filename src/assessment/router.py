from fastapi import APIRouter, Depends
from .schemas import AssessmentInput, AssessmentOutput
from .service import AssessmentService
from .config import assessment_config  
from ..utils.security import verify_jwt
from ..utils.rate_limit import RateLimiter

router = APIRouter(prefix="/assessment", tags=["assessment"])

def get_assessment_service() -> AssessmentService:
    return AssessmentService(config=assessment_config)

@router.post("", response_model=AssessmentOutput, dependencies=[Depends(verify_jwt), Depends(RateLimiter("llm"))])
async def assess(
    body: AssessmentInput,
    service: AssessmentService = Depends(get_assessment_service),
):
    return await service.assess(body)