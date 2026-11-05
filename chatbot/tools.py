"""Tools the chatbot can call. ALL numbers come from here, never from the LLM."""
from __future__ import annotations
from typing import Annotated, Any
from pydantic import TypeAdapter, ValidationError
from schemas import PatientInput
from core import db, safety
from core.knowledge import explain
from core.risk import coerce_patient, predict_risk, DISCLAIMER as RISK_DISCLAIMER
from core.recommend import recommend
from core.diet import generate_diet_chart

from pydantic import Field
EXTRA = {
    "height_cm": TypeAdapter(Annotated[float, Field(ge=100, le=250)]),
    "weight_kg": TypeAdapter(Annotated[float, Field(ge=25, le=300)]),
    "diet_preference": TypeAdapter(Annotated[str, Field(pattern="^(vegan|veg|nonveg)$")]),
    "allergies": TypeAdapter(list[str]),
    "kidney_disease": TypeAdapter(bool),
    "pregnant": TypeAdapter(bool),
}


def _adapter(name: str) -> TypeAdapter:
    f = PatientInput.model_fields[name]
    ann = Annotated.__class_getitem__((f.annotation, *f.metadata)) if f.metadata else f.annotation
    return TypeAdapter(ann)


def missing_for_risk(profile: dict) -> list[str]:
    return [n for n, f in PatientInput.model_fields.items() if f.is_required() and n not in profile]


def build_patient(user_id: str) -> tuple[PatientInput | None, list[str]]:
    prof = dict(db.get_profile(user_id))
    bp = db.get_readings(user_id, "bp", days=30)
    if bp:  # newest measured BP overrides the typed-in value
        prof["systolic_bp"], prof["diastolic_bp"] = int(bp[0]["value1"]), int(bp[0]["value2"])
    miss = missing_for_risk(prof)
    if miss:
        return None, miss
    return coerce_patient(prof), []


# ── tool implementations ────────────────────────────────────
def update_profile(user_id: str, fields: dict) -> dict:
    ok, errors = {}, {}
    for k, v in (fields or {}).items():
        try:
            ad = EXTRA.get(k) or (_adapter(k) if k in PatientInput.model_fields else None)
            if ad is None:
                errors[k] = "unknown field"; continue
            ok[k] = ad.validate_python(v)
        except ValidationError as e:
            errors[k] = e.errors()[0]["msg"]
    merged = db.save_profile(user_id, ok) if ok else db.get_profile(user_id)
    return {"saved": list(ok), "errors": errors, "still_missing_for_risk": missing_for_risk(merged)}


def get_risk_assessment(user_id: str) -> dict:
    p, miss = build_patient(user_id)
    if not p:
        return {"status": "incomplete", "missing": miss}
    return {"status": "ok", **predict_risk(p)}


def get_recommendations(user_id: str) -> dict:
    p, miss = build_patient(user_id)
    if not p:
        return {"status": "incomplete", "missing": miss}
    return {"status": "ok", **recommend(p, predict_risk(p)["risk_level"]), "disclaimer": RISK_DISCLAIMER}


def make_diet_chart(user_id: str, days: int = 1) -> dict:
    prof = db.get_profile(user_id)
    p, _ = build_patient(user_id)
    need = [k for k in ("age", "sex", "height_cm", "weight_kg") if k not in prof]
    if need:
        return {"status": "incomplete", "missing": need}
    cond = [c for c, on in (("kidney_disease", prof.get("kidney_disease")), ("pregnant", prof.get("pregnant")),
            ("diabetes", prof.get("diabetes")), ("high_cholesterol", prof.get("cholesterol", 0) > 240),
            ("high_triglycerides", prof.get("triglycerides", 0) > 200),
            ("hypertension", p is not None and (p.systolic_bp >= 130 or p.diastolic_bp >= 80)
                              or prof.get("systolic_bp", 0) >= 130)) if on]
    return generate_diet_chart(age=prof["age"], sex=prof["sex"], height_cm=prof["height_cm"],
                               weight_kg=prof["weight_kg"], activity_days=prof.get("physical_activity_days_per_week", 2),
                               conditions=cond, diet_preference=prof.get("diet_preference", "nonveg"),
                               allergies=prof.get("allergies", []), days=int(days or 1))


def log_reading(user_id: str, kind: str, value1: float, value2: float | None = None,
                context: str = "random", source: str = "manual") -> dict:
    try:
        safety.validate_reading(kind, value1, value2)
    except ValueError as e:
        return {"status": "rejected", "reason": str(e)}
    db.add_reading(user_id, kind, value1, value2, context, source)
    cat = (safety.classify_bp(value1, value2) if kind == "bp" else
           safety.classify_glucose(value1, context) if kind == "glucose" else "recorded")
    return {"status": "saved", "kind": kind, "value1": value1, "value2": value2, "context": context,
            "category": cat, "alert": safety.reading_alert(kind, cat),
            "note": "Categories are general screening references, not a diagnosis."}


def get_reading_trend(user_id: str, kind: str = "bp", days: int = 7) -> dict:
    rows = db.get_readings(user_id, kind, days)
    if not rows:
        return {"status": "empty", "kind": kind, "days": days}
    v1 = [r["value1"] for r in rows]
    out = {"status": "ok", "kind": kind, "days": days, "count": len(rows),
           "latest": {"value1": rows[0]["value1"], "value2": rows[0]["value2"], "time": rows[0]["time"]},
           "avg1": round(sum(v1) / len(v1), 1), "min1": min(v1), "max1": max(v1)}
    if kind == "bp":
        out["avg2"] = round(sum(r["value2"] for r in rows) / len(rows), 1)
    return out


def explain_term(user_id: str, term: str) -> dict:
    e = explain(term)
    return {"status": "ok", "term": term, "explanation": e} if e else {"status": "unknown", "term": term}


REGISTRY = {"update_profile": update_profile, "get_risk_assessment": get_risk_assessment,
            "get_recommendations": get_recommendations, "generate_diet_chart": make_diet_chart,
            "log_reading": log_reading, "get_reading_trend": get_reading_trend, "explain_term": explain_term}


def run_tool(name: str, args: dict, user_id: str) -> dict:
    fn = REGISTRY.get(name)
    if not fn:
        return {"status": "error", "reason": f"unknown tool {name}"}
    try:
        return fn(user_id, **(args or {}))
    except TypeError as e:
        return {"status": "error", "reason": f"bad arguments: {e}"}


def _fn(name, desc, props, req=()):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": list(req)}}}


TOOLS = [
    _fn("update_profile", "Save profile facts the user told you (age, sex, height_cm, weight_kg, cholesterol, "
        "systolic_bp, diastolic_bp, heart_rate, bmi, triglycerides, diabetes, family_history, "
        "previous_heart_problems, medication_use, smoking, obesity, alcohol_consumption, diet (Healthy/Average/Unhealthy), "
        "stress_level, exercise_hours_per_week, sedentary_hours_per_day, physical_activity_days_per_week, "
        "sleep_hours_per_day, income, diet_preference (vegan/veg/nonveg), allergies, kidney_disease, pregnant).",
        {"fields": {"type": "object"}}, ["fields"]),
    _fn("get_risk_assessment", "Compute the user's heart risk estimate from their saved profile.", {}),
    _fn("get_recommendations", "Get personalised lifestyle recommendations from the saved profile.", {}),
    _fn("generate_diet_chart", "Generate a diet chart (1-7 days).", {"days": {"type": "integer"}}),
    _fn("log_reading", "Record a blood pressure, glucose (mg/dL) or heart-rate reading.",
        {"kind": {"type": "string", "enum": ["bp", "glucose", "hr"]}, "value1": {"type": "number"},
         "value2": {"type": "number"}, "context": {"type": "string", "enum": ["fasting", "post_meal", "random"]}},
        ["kind", "value1"]),
    _fn("get_reading_trend", "Summarise recent readings.",
        {"kind": {"type": "string", "enum": ["bp", "glucose", "hr"]}, "days": {"type": "integer"}}, ["kind"]),
    _fn("explain_term", "Explain a medical term in plain language.", {"term": {"type": "string"}}, ["term"]),
]
