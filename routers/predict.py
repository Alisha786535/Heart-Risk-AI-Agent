"""/predict – thin wrapper over the shared core.risk module."""
import logging
from fastapi import APIRouter, HTTPException
from schemas import PatientInput, PredictionResponse
from core.risk import predict_risk

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse, summary="Predict heart attack risk (demo model)")
def predict(patient: PatientInput):
    try:
        return PredictionResponse(**predict_risk(patient))
    except FileNotFoundError:
        raise HTTPException(500, "Model files missing. Run `python train_models.py` first.")
    except Exception:
        log.exception("prediction failed")
        raise HTTPException(500, "Prediction failed.")
