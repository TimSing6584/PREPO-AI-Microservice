from fastapi import APIRouter, Depends
from .schemas import AssessmentInput, AssessmentOutput
from .service import AssessmentService
from .config import assessment_config  

router = APIRouter(prefix="/assessment", tags=["assessment"])

def get_assessment_service() -> AssessmentService:
    return AssessmentService(config=assessment_config)

@router.post("", response_model=AssessmentOutput)
async def assess(
    body: AssessmentInput,
    service: AssessmentService = Depends(get_assessment_service),
):
    return await service.assess(body)