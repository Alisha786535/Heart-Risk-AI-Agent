"""
/recommendations endpoint – Personalised healthy-habit recommendations.

Uses a rule-based recommendation engine that analyses all patient features
and generates prioritised, personalised advice. This mirrors how a
Transformer/LLM recommendation system works but runs fully offline.

To swap in a real HuggingFace model:
    Replace the `generate_recommendations()` function body with:
        from transformers import pipeline
        pipe = pipeline("text-generation", model="your-model-id")
        ...
"""

from fastapi import APIRouter, HTTPException
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from schemas import PatientInput, PredictionResponse, RecommendationRequest, RecommendationResponse

router = APIRouter()

# ─────────────────────────────────────────────────────────
# Recommendation engine (rule-based knowledge graph)
# Each rule: (condition_fn, category, priority 1-5, advice)
# ─────────────────────────────────────────────────────────
RULES = [
    # ── Smoking ─────────────────────────────────────────
    (lambda p: p.smoking,
     "Smoking Cessation", 5,
     "🚭 Quit smoking immediately. Smoking doubles the risk of heart attack. "
     "Seek nicotine replacement therapy or consult a cessation programme."),

    # ── Blood Pressure ───────────────────────────────────
    (lambda p: p.systolic_bp > 140 or p.diastolic_bp > 90,
     "Blood Pressure", 5,
     f"🩺 Your blood pressure is elevated (Stage 2 hypertension range). "
     "Reduce salt intake to <2.3g/day, follow a DASH diet, and consult your doctor about medication."),

    (lambda p: 130 <= p.systolic_bp <= 140 or 80 <= p.diastolic_bp <= 90,
     "Blood Pressure", 4,
     "🩺 Blood pressure is in the elevated/Stage 1 range. "
     "Reduce sodium, increase potassium-rich foods (bananas, spinach), and exercise regularly."),

    # ── Cholesterol ──────────────────────────────────────
    (lambda p: p.cholesterol > 240,
     "Cholesterol", 5,
     "🫀 High cholesterol detected. Avoid saturated & trans fats. "
     "Eat oats, nuts, and fatty fish. Ask your doctor about statins."),

    (lambda p: 200 < p.cholesterol <= 240,
     "Cholesterol", 3,
     "🫀 Borderline cholesterol. Increase fibre (oats, legumes, fruits) and reduce red meat consumption."),

    # ── Triglycerides ────────────────────────────────────
    (lambda p: p.triglycerides > 200,
     "Triglycerides", 4,
     "🩸 Elevated triglycerides. Cut sugar, refined carbs, and alcohol. "
     "Increase omega-3 fatty acids (fish oil, flaxseed)."),

    # ── BMI / Obesity ────────────────────────────────────
    (lambda p: p.bmi >= 30 or p.obesity,
     "Weight Management", 4,
     f"⚖️ BMI indicates obesity. Aim for 5–10% weight reduction in 6 months. "
     "Target 150 mins of moderate exercise per week and a calorie-controlled diet."),

    (lambda p: 25 <= p.bmi < 30,
     "Weight Management", 3,
     "⚖️ You are in the overweight BMI range. Combine aerobic and strength training 4x/week "
     "with a Mediterranean-style diet to reach a healthy BMI (18.5–24.9)."),

    # ── Exercise ─────────────────────────────────────────
    (lambda p: p.exercise_hours_per_week < 1.5,
     "Physical Activity", 5,
     "🏃 Very low exercise level. Start with 30-minute brisk walks 5x/week. "
     "WHO recommends ≥150 mins moderate aerobic activity per week."),

    (lambda p: 1.5 <= p.exercise_hours_per_week < 2.5,
     "Physical Activity", 3,
     "🏃 Exercise level is below optimal. Gradually increase to at least 2.5 hrs/week. "
     "Mix cardio (cycling, swimming) with resistance training."),

    (lambda p: p.sedentary_hours_per_day > 8,
     "Sedentary Behaviour", 4,
     "🪑 Excessive sedentary time significantly increases cardiovascular risk. "
     "Take a 5-minute standing/walking break every hour. Consider a standing desk."),

    (lambda p: p.physical_activity_days_per_week < 3,
     "Physical Activity", 3,
     "🏋️ You are active fewer than 3 days/week. Aim for at least 4–5 active days. "
     "Even light activity (yoga, stretching) counts."),

    # ── Diet ─────────────────────────────────────────────
    (lambda p: p.diet == "Unhealthy",
     "Diet & Nutrition", 5,
     "🥗 Poor diet is a major risk factor. Adopt a Mediterranean diet: "
     "olive oil, fish, whole grains, vegetables, legumes, and limited red meat."),

    (lambda p: p.diet == "Average",
     "Diet & Nutrition", 2,
     "🥗 Improve your diet quality. Add more fruits, vegetables, and whole grains. "
     "Reduce processed foods, added sugars, and trans fats."),

    # ── Sleep ────────────────────────────────────────────
    (lambda p: p.sleep_hours_per_day < 6,
     "Sleep", 4,
     "😴 Insufficient sleep (<6 hrs) is linked to increased heart attack risk. "
     "Aim for 7–9 hours. Establish a consistent sleep schedule and limit screen time before bed."),

    (lambda p: p.sleep_hours_per_day > 9,
     "Sleep", 2,
     "😴 Consistently sleeping >9 hours may indicate underlying conditions. "
     "Consult your doctor for a sleep study if you feel unrefreshed."),

    # ── Stress ───────────────────────────────────────────
    (lambda p: p.stress_level >= 8,
     "Stress Management", 4,
     "🧘 Very high stress level. Practice mindfulness, meditation, or yoga daily. "
     "Consider cognitive-behavioural therapy (CBT). Chronic stress raises cortisol and blood pressure."),

    (lambda p: 5 <= p.stress_level < 8,
     "Stress Management", 2,
     "🧘 Moderate stress detected. Try daily 10-minute mindfulness sessions, "
     "deep breathing exercises, or regular social activities."),

    # ── Diabetes ─────────────────────────────────────────
    (lambda p: p.diabetes,
     "Diabetes Management", 5,
     "💉 Diabetes significantly amplifies heart attack risk. "
     "Strictly control blood glucose (HbA1c <7%). Follow a low-glycaemic diet "
     "and ensure regular HbA1c testing."),

    # ── Alcohol ──────────────────────────────────────────
    (lambda p: p.alcohol_consumption,
     "Alcohol", 3,
     "🍷 Regular alcohol raises blood pressure and triglycerides. "
     "Limit to ≤14 units/week (men) or ≤7 units/week (women), with alcohol-free days."),

    # ── Heart Rate ───────────────────────────────────────
    (lambda p: p.heart_rate > 100,
     "Heart Rate", 4,
     "💓 Elevated resting heart rate. This can indicate poor cardiovascular fitness. "
     "Regular aerobic exercise will lower resting HR. Discuss with your cardiologist."),

    # ── Family History ───────────────────────────────────
    (lambda p: p.family_history,
     "Genetic Risk", 3,
     "🧬 Family history of heart disease increases your risk. "
     "Get a full lipid panel and cardiac screening annually. "
     "Lifestyle changes have a stronger impact when genetic risk is present."),

    # ── Previous Heart Problems ───────────────────────────
    (lambda p: p.previous_heart_problems,
     "Cardiac History", 5,
     "🏥 Previous heart problems make re-occurrence more likely. "
     "Adhere strictly to prescribed medications, attend follow-up appointments, "
     "and undergo annual ECG/echocardiogram screening."),

    # ── Medication non-compliance ─────────────────────────
    (lambda p: (p.previous_heart_problems or p.diabetes or p.systolic_bp > 140) and not p.medication_use,
     "Medication", 4,
     "💊 You have conditions that typically require medication but are not on any. "
     "Speak to your doctor about appropriate pharmacological management."),
]


def compute_lifestyle_score(p: PatientInput) -> float:
    """Score 0–100 based on healthy lifestyle indicators."""
    score = 100.0
    if p.smoking:             score -= 20
    if p.obesity or p.bmi >= 30: score -= 10
    if p.bmi >= 25:           score -= 5
    if p.diet == "Unhealthy": score -= 10
    if p.diet == "Average":   score -= 5
    if p.exercise_hours_per_week < 1.5: score -= 10
    if p.sedentary_hours_per_day > 8:   score -= 8
    if p.stress_level >= 8:   score -= 8
    if p.sleep_hours_per_day < 6:       score -= 7
    if p.alcohol_consumption: score -= 5
    if p.diabetes:            score -= 5
    return max(0.0, round(score, 1))


def monitoring_advice(p: PatientInput, risk_level: str) -> str:
    base = {
        "LOW":       "Annual check-up with your GP.",
        "MODERATE":  "Check-up every 6 months. Monitor blood pressure weekly at home.",
        "HIGH":      "Quarterly cardiologist visits. Daily BP monitoring. Consider stress ECG.",
        "VERY HIGH": "Urgent cardiology referral. Monthly follow-ups. "
                     "Continuous BP/glucose monitoring. Discuss preventive medication.",
    }
    extra = ""
    if p.diabetes:
        extra += " HbA1c test every 3 months."
    if p.previous_heart_problems:
        extra += " Annual echocardiogram."
    return base.get(risk_level, base["MODERATE"]) + extra


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get personalised healthy-habit recommendations",
    description="""
Analyses patient data and prediction results to generate prioritised,
personalised health recommendations.

Returns:
- **personalised_recommendations** – Ranked list of tailored advice items
- **lifestyle_score** – 0–100 score reflecting current lifestyle health
- **priority_actions** – Top 3 most urgent actions
- **monitoring_advice** – Follow-up and monitoring schedule
""",
)
def get_recommendations(request: RecommendationRequest):
    p = request.patient_data
    risk_level = request.prediction_result.risk_level if request.prediction_result else "MODERATE"

    matched = []
    for condition, category, priority, advice in RULES:
        try:
            if condition(p):
                matched.append({
                    "category": category,
                    "priority": priority,
                    "advice": advice,
                })
        except Exception:
            continue

    # Sort by priority descending
    matched.sort(key=lambda x: x["priority"], reverse=True)

    # If nothing matched: generic positive advice
    if not matched:
        matched = [{
            "category": "General Health",
            "priority": 1,
            "advice": "✅ Your indicators look healthy! Continue regular exercise, balanced diet, "
                      "quality sleep, and annual health check-ups.",
        }]

    priority_actions = [r["advice"] for r in matched[:3]]
    lifestyle_score  = compute_lifestyle_score(p)
    monitoring       = monitoring_advice(p, risk_level)

    return RecommendationResponse(
        risk_level=risk_level,
        personalised_recommendations=matched,
        lifestyle_score=lifestyle_score,
        priority_actions=priority_actions,
        monitoring_advice=monitoring,
    )
