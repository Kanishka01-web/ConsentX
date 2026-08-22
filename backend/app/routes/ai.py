from fastapi import APIRouter

from .. import schemas
from ..services.ai_service import analyze_consent_text

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze", response_model=schemas.AIAnalysisResponse)
def analyze(payload: schemas.AIAnalysisRequest):
    return analyze_consent_text(payload.text)
