"""/recommendations – risk level is recomputed server-side (client-supplied value is ignored)."""
from fastapi import APIRouter
from schemas import RecommendationRequest, RecommendationResponse
from core.risk import predict_risk
from core.recommend import recommend

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse,
             summary="Get personalised healthy-habit recommendations")
def get_recommendations(request: RecommendationRequest):
    p = request.patient_data
    return RecommendationResponse(**recommend(p, predict_risk(p)["risk_level"]))
