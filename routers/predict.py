"""
/predict endpoint – Ensemble ML heart attack risk prediction.
"""

from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from schemas import PatientInput, PredictionResponse
from utils.model_loader import get_models

router = APIRouter()

DIET_MAP = {"Average": 0, "Healthy": 1, "Unhealthy": 2}
SEX_MAP  = {"Female": 0, "Male": 1}

FEATURE_ORDER = [
    "Age", "Sex", "Cholesterol", "Heart Rate", "Diabetes", "Family History",
    "Smoking", "Obesity", "Alcohol Consumption", "Exercise Hours Per Week",
    "Diet", "Previous Heart Problems", "Medication Use", "Stress Level",
    "Sedentary Hours Per Day", "Income", "BMI", "Triglycerides",
    "Physical Activity Days Per Week", "Sleep Hours Per Day",
    "SystolicBP", "DiastolicBP",
]

RISK_FACTOR_LABELS = {
    "Exercise Hours Per Week": "Low exercise hours",
    "Sedentary Hours Per Day": "High sedentary time",
    "BMI": "Elevated BMI",
    "Triglycerides": "High triglycerides",
    "SystolicBP": "High systolic blood pressure",
    "Cholesterol": "High cholesterol",
    "Stress Level": "High stress level",
    "Smoking": "Smoking",
    "Diabetes": "Diabetes",
    "Family History": "Family history of heart disease",
    "Previous Heart Problems": "Previous heart problems",
    "Age": "Advanced age",
    "Heart Rate": "Elevated heart rate",
    "DiastolicBP": "High diastolic blood pressure",
}


def patient_to_vector(p: PatientInput) -> np.ndarray:
    """Convert PatientInput to the feature vector expected by the models."""
    row = {
        "Age":                           p.age,
        "Sex":                           SEX_MAP[p.sex],
        "Cholesterol":                   p.cholesterol,
        "Heart Rate":                    p.heart_rate,
        "Diabetes":                      int(p.diabetes),
        "Family History":                int(p.family_history),
        "Smoking":                       int(p.smoking),
        "Obesity":                       int(p.obesity),
        "Alcohol Consumption":           int(p.alcohol_consumption),
        "Exercise Hours Per Week":       p.exercise_hours_per_week,
        "Diet":                          DIET_MAP[p.diet],
        "Previous Heart Problems":       int(p.previous_heart_problems),
        "Medication Use":                int(p.medication_use),
        "Stress Level":                  p.stress_level,
        "Sedentary Hours Per Day":       p.sedentary_hours_per_day,
        "Income":                        p.income,
        "BMI":                           p.bmi,
        "Triglycerides":                 p.triglycerides,
        "Physical Activity Days Per Week": p.physical_activity_days_per_week,
        "Sleep Hours Per Day":           p.sleep_hours_per_day,
        "SystolicBP":                    p.systolic_bp,
        "DiastolicBP":                   p.diastolic_bp,
    }
    return np.array([row[f] for f in FEATURE_ORDER]).reshape(1, -1)


def risk_level_from_prob(prob: float) -> str:
    if prob < 0.30:
        return "LOW"
    elif prob < 0.50:
        return "MODERATE"
    elif prob < 0.70:
        return "HIGH"
    else:
        return "VERY HIGH"


def top_risk_factors(p: PatientInput, models: dict, n: int = 5) -> list:
    """Return top contributing risk factors using RF feature importances."""
    rf = models["rf"]
    importances = rf.feature_importances_
    fi_series = dict(zip(FEATURE_ORDER, importances))

    # Weight importance by clinical flag
    flags = {
        "Smoking": p.smoking,
        "Diabetes": p.diabetes,
        "Family History": p.family_history,
        "Previous Heart Problems": p.previous_heart_problems,
    }
    # Numeric abnormality boosts
    numeric_boosts = {}
    if p.bmi > 30:             numeric_boosts["BMI"] = 1.5
    if p.cholesterol > 240:    numeric_boosts["Cholesterol"] = 1.5
    if p.systolic_bp > 140:    numeric_boosts["SystolicBP"] = 1.5
    if p.triglycerides > 200:  numeric_boosts["Triglycerides"] = 1.5
    if p.stress_level >= 8:    numeric_boosts["Stress Level"] = 1.3
    if p.exercise_hours_per_week < 1.5: numeric_boosts["Exercise Hours Per Week"] = 1.4

    scored = {}
    for feat, imp in fi_series.items():
        score = imp
        if flags.get(feat):
            score *= 2.0
        score *= numeric_boosts.get(feat, 1.0)
        scored[feat] = score

    top = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:n]
    return [RISK_FACTOR_LABELS.get(f, f) for f, _ in top]


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict heart attack risk",
    description="""
Submit patient clinical and lifestyle data.

Returns:
- **risk_probability** – Ensemble probability (0–1)
- **risk_level** – LOW / MODERATE / HIGH / VERY HIGH
- **top_risk_factors** – The most significant contributing factors
- Individual probabilities from Random Forest and Gradient Boosting models
""",
)
def predict(patient: PatientInput):
    try:
        models = get_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")

    vec = patient_to_vector(patient)
    vec_scaled = models["scaler"].transform(vec)

    rf_prob = float(models["rf"].predict_proba(vec_scaled)[0][1])
    gb_prob = float(models["gb"].predict_proba(vec_scaled)[0][1])

    # Soft ensemble: weight RF slightly higher
    ensemble_prob = round(0.55 * rf_prob + 0.45 * gb_prob, 4)
    level = risk_level_from_prob(ensemble_prob)

    label = 1 if ensemble_prob >= 0.38 else 0

    messages = {
        "LOW":       "Your risk indicators are within acceptable ranges. Maintain your healthy habits.",
        "MODERATE":  "Some risk factors detected. Lifestyle changes are recommended.",
        "HIGH":      "Multiple risk factors present. Please consult a healthcare provider soon.",
        "VERY HIGH": "Critical risk level. Immediate medical consultation is strongly advised.",
    }

    factors = top_risk_factors(patient, models)

    return PredictionResponse(
        risk_probability=ensemble_prob,
        risk_score_percent=round(ensemble_prob * 100, 2),
        risk_level=level,
        risk_label=label,
        rf_probability=round(rf_prob, 4),
        gb_probability=round(gb_prob, 4),
        top_risk_factors=factors,
        message=messages[level],
    )
