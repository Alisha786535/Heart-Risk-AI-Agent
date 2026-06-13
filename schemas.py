"""Shared Pydantic schemas used across routers."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal


class PatientInput(BaseModel):
    """All clinical and lifestyle features required for prediction."""

    # Demographics
    age: int = Field(..., ge=1, le=120, example=55, description="Patient age in years")
    sex: Literal["Male", "Female"] = Field(..., example="Male")

    # Vitals
    cholesterol: int = Field(..., ge=100, le=600, example=220,
                             description="Total cholesterol (mg/dL)")
    systolic_bp: int = Field(..., ge=60, le=250, example=130,
                             description="Systolic blood pressure (mmHg)")
    diastolic_bp: int = Field(..., ge=40, le=150, example=85,
                              description="Diastolic blood pressure (mmHg)")
    heart_rate: int = Field(..., ge=30, le=220, example=78,
                            description="Resting heart rate (bpm)")
    bmi: float = Field(..., ge=10.0, le=70.0, example=27.5,
                       description="Body Mass Index")
    triglycerides: int = Field(..., ge=50, le=1000, example=180,
                               description="Triglycerides level (mg/dL)")

    # Medical history
    diabetes: bool = Field(..., example=False)
    family_history: bool = Field(..., example=True,
                                 description="Family history of heart disease")
    previous_heart_problems: bool = Field(..., example=False)
    medication_use: bool = Field(..., example=False,
                                 description="Currently on cardiac medication")

    # Lifestyle
    smoking: bool = Field(..., example=False)
    obesity: bool = Field(..., example=False)
    alcohol_consumption: bool = Field(..., example=False,
                                      description="Regular alcohol consumption")
    diet: Literal["Healthy", "Average", "Unhealthy"] = Field(..., example="Average")
    stress_level: int = Field(..., ge=1, le=10, example=6,
                              description="Self-reported stress level (1=low, 10=high)")
    exercise_hours_per_week: float = Field(..., ge=0.0, le=40.0, example=3.5)
    sedentary_hours_per_day: float = Field(..., ge=0.0, le=24.0, example=6.0)
    physical_activity_days_per_week: int = Field(..., ge=0, le=7, example=3)
    sleep_hours_per_day: int = Field(..., ge=1, le=24, example=7)

    # Socioeconomic
    income: int = Field(..., ge=0, le=10_000_000, example=60000,
                        description="Annual income (USD)")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 55,
                "sex": "Male",
                "cholesterol": 220,
                "systolic_bp": 135,
                "diastolic_bp": 88,
                "heart_rate": 80,
                "bmi": 28.4,
                "triglycerides": 200,
                "diabetes": False,
                "family_history": True,
                "previous_heart_problems": False,
                "medication_use": False,
                "smoking": True,
                "obesity": False,
                "alcohol_consumption": False,
                "diet": "Average",
                "stress_level": 7,
                "exercise_hours_per_week": 2.0,
                "sedentary_hours_per_day": 8.0,
                "physical_activity_days_per_week": 2,
                "sleep_hours_per_day": 6,
                "income": 55000,
            }
        }


class PredictionResponse(BaseModel):
    risk_probability: float = Field(..., description="Probability of heart attack risk (0–1)")
    risk_score_percent: float = Field(..., description="Risk as percentage")
    risk_level: str = Field(..., description="LOW / MODERATE / HIGH / VERY HIGH")
    risk_label: int = Field(..., description="Binary risk label: 0=low, 1=at-risk")
    rf_probability: float = Field(..., description="Random Forest probability")
    gb_probability: float = Field(..., description="Gradient Boosting probability")
    top_risk_factors: list = Field(..., description="Top contributing risk factors")
    message: str


class RecommendationRequest(BaseModel):
    patient_data: PatientInput
    prediction_result: Optional[PredictionResponse] = None


class RecommendationResponse(BaseModel):
    risk_level: str
    personalised_recommendations: list
    lifestyle_score: float = Field(..., description="Lifestyle health score 0–100")
    priority_actions: list
    monitoring_advice: str
