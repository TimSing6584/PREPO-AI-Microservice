from fastapi import APIRouter, Depends
from .schemas import AssessmentInput, AssessmentOutput
from .service import AssessmentService
from .config import assessment_config  
from ..security import verify_jwt

router = APIRouter(prefix="/assessment", tags=["assessment"])

def get_assessment_service() -> AssessmentService:
    return AssessmentService(config=assessment_config)

@router.post("", response_model=AssessmentOutput, dependencies=[Depends(verify_jwt)])
async def assess(
    body: AssessmentInput,
    service: AssessmentService = Depends(get_assessment_service),
):
    return await service.assess(body)