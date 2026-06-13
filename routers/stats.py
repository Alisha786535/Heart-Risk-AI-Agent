"""
/stats endpoint – Dataset statistics & feature importances.
"""

from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.model_loader import get_models

router = APIRouter()
DATA_PATH = Path(__file__).parent.parent / "data" / "heart_attack_prediction_dataset.csv"


@router.get(
    "/stats",
    summary="Dataset statistics & model feature importances",
    description="Returns dataset overview, class distribution, and top predictive features.",
)
def get_stats():
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load dataset: {e}")

    total = len(df)
    at_risk = int(df["Heart Attack Risk"].sum())
    not_risk = total - at_risk

    numeric_cols = ["Age", "Cholesterol", "Heart Rate", "BMI", "Triglycerides",
                    "Stress Level", "Exercise Hours Per Week", "Sedentary Hours Per Day",
                    "Sleep Hours Per Day"]
    summary = {}
    for col in numeric_cols:
        summary[col] = {
            "mean":   round(float(df[col].mean()), 2),
            "std":    round(float(df[col].std()), 2),
            "min":    round(float(df[col].min()), 2),
            "max":    round(float(df[col].max()), 2),
            "median": round(float(df[col].median()), 2),
        }

    # Feature importances from RF
    try:
        models = get_models()
        feature_names = [
            "Age", "Sex", "Cholesterol", "Heart Rate", "Diabetes", "Family History",
            "Smoking", "Obesity", "Alcohol Consumption", "Exercise Hours Per Week",
            "Diet", "Previous Heart Problems", "Medication Use", "Stress Level",
            "Sedentary Hours Per Day", "Income", "BMI", "Triglycerides",
            "Physical Activity Days Per Week", "Sleep Hours Per Day",
            "SystolicBP", "DiastolicBP",
        ]
        importances = models["rf"].feature_importances_
        fi = sorted(
            [{"feature": f, "importance": round(float(i), 4)}
             for f, i in zip(feature_names, importances)],
            key=lambda x: x["importance"], reverse=True
        )
    except Exception:
        fi = []

    # Lifestyle factor prevalence
    prevalence = {
        "smoking_rate_pct":           round(df["Smoking"].mean() * 100, 1),
        "diabetes_rate_pct":          round(df["Diabetes"].mean() * 100, 1),
        "obesity_rate_pct":           round(df["Obesity"].mean() * 100, 1),
        "family_history_rate_pct":    round(df["Family History"].mean() * 100, 1),
        "alcohol_consumption_pct":    round(df["Alcohol Consumption"].mean() * 100, 1),
        "previous_heart_problems_pct":round(df["Previous Heart Problems"].mean() * 100, 1),
    }

    return {
        "dataset": {
            "total_records": total,
            "at_risk": at_risk,
            "not_at_risk": not_risk,
            "at_risk_pct": round(at_risk / total * 100, 1),
            "gender_distribution": df["Sex"].value_counts().to_dict(),
            "diet_distribution": df["Diet"].value_counts().to_dict(),
        },
        "feature_statistics": summary,
        "lifestyle_prevalence": prevalence,
        "model_feature_importances": fi[:12],
    }
