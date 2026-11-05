"""Single source of truth for risk prediction (used by the API AND the chatbot)."""
from __future__ import annotations
import pandas as pd
from schemas import PatientInput
from utils.model_loader import get_models

SEX_MAP = {"Female": 0, "Male": 1}
DIET_MAP = {"Average": 0, "Healthy": 1, "Unhealthy": 2}
DISCLAIMER = ("Demo estimate from a model trained on synthetic data. It is NOT a diagnosis "
              "and not clinically validated. Please see a doctor for real medical advice.")
MESSAGES = {
    "LOW": "Your risk indicators are within acceptable ranges. Maintain your healthy habits.",
    "MODERATE": "Some risk factors detected. Lifestyle changes are recommended.",
    "HIGH": "Multiple risk factors present. Please consult a healthcare provider soon.",
    "VERY HIGH": "High risk level. Please arrange a medical consultation promptly.",
}


def coerce_patient(d: dict) -> PatientInput:
    """Build a PatientInput from loosely-typed form/profile data (e.g. 67.0 -> 67 for int fields)."""
    out = {}
    for k, f in PatientInput.model_fields.items():
        if k in d and d[k] is not None:
            v = d[k]
            out[k] = int(round(float(v))) if f.annotation is int and not isinstance(v, bool) else v
    return PatientInput(**out)


def risk_level_from_prob(p: float) -> str:
    return "LOW" if p < 0.30 else "MODERATE" if p < 0.50 else "HIGH" if p < 0.70 else "VERY HIGH"


def patient_row(p: PatientInput) -> dict:
    return {
        "Age": p.age, "Sex": SEX_MAP[p.sex], "Cholesterol": p.cholesterol, "Heart Rate": p.heart_rate,
        "Diabetes": int(p.diabetes), "Family History": int(p.family_history), "Smoking": int(p.smoking),
        "Obesity": int(p.obesity), "Alcohol Consumption": int(p.alcohol_consumption),
        "Exercise Hours Per Week": p.exercise_hours_per_week, "Diet": DIET_MAP[p.diet],
        "Previous Heart Problems": int(p.previous_heart_problems), "Medication Use": int(p.medication_use),
        "Stress Level": p.stress_level, "Sedentary Hours Per Day": p.sedentary_hours_per_day,
        "Income": p.income, "BMI": p.bmi, "Triglycerides": p.triglycerides,
        "Physical Activity Days Per Week": p.physical_activity_days_per_week,
        "Sleep Hours Per Day": p.sleep_hours_per_day, "SystolicBP": p.systolic_bp, "DiastolicBP": p.diastolic_bp,
    }


def risk_factors(p: PatientInput, n: int = 5) -> list[str]:
    """Only factors the patient ACTUALLY has, ranked by clinical weight."""
    checks = [
        (10, p.previous_heart_problems, "Previous heart problems"),
        (9, p.diabetes, "Diabetes"), (9, p.smoking, "Smoking"),
        (8, p.systolic_bp >= 140 or p.diastolic_bp >= 90, "High blood pressure"),
        (7, p.cholesterol > 240, "High cholesterol"),
        (6, p.family_history, "Family history of heart disease"),
        (6, p.bmi >= 30, "BMI in the obesity range"),
        (5, p.triglycerides > 200, "High triglycerides"),
        (5, p.age >= 55, "Age 55 or older"),
        (4, p.stress_level >= 8, "High stress level"),
        (4, p.exercise_hours_per_week < 1.5, "Low weekly exercise"),
        (3, p.sedentary_hours_per_day > 8, "Long sedentary time"),
        (3, p.sleep_hours_per_day < 6, "Short sleep"),
        (3, p.heart_rate > 100, "Elevated resting heart rate"),
        (2, p.alcohol_consumption, "Regular alcohol use"),
    ]
    return [label for _, ok, label in sorted(checks, key=lambda c: -c[0]) if ok][:n]


def predict_risk(p: PatientInput) -> dict:
    m = get_models()
    X = pd.DataFrame([patient_row(p)])[m["feature_names"]]
    Xs = m["scaler"].transform(X)
    rf = float(m["rf"].predict_proba(Xs)[0][1])
    gb = float(m["gb"].predict_proba(Xs)[0][1])
    prob = round(0.55 * rf + 0.45 * gb, 4)
    level = risk_level_from_prob(prob)
    return {
        "risk_probability": prob, "risk_score_percent": round(prob * 100, 2),
        "risk_level": level, "risk_label": 0 if level == "LOW" else 1,
        "rf_probability": round(rf, 4), "gb_probability": round(gb, 4),
        "top_risk_factors": risk_factors(p), "message": MESSAGES[level], "disclaimer": DISCLAIMER,
    }
