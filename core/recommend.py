"""Shared recommendation engine: de-duplicated per category, risk computed server-side."""
from __future__ import annotations
from schemas import PatientInput
from core.rules import RULES, compute_lifestyle_score, monitoring_advice


def recommend(p: PatientInput, risk_level: str) -> dict:
    best: dict[str, dict] = {}
    for cond, category, priority, advice in RULES:
        try:
            ok = cond(p)
        except Exception:
            ok = False
        if ok and (category not in best or priority > best[category]["priority"]):
            best[category] = {"category": category, "priority": priority, "advice": advice}
    items = sorted(best.values(), key=lambda r: -r["priority"]) or [{
        "category": "General Health", "priority": 1,
        "advice": "✅ Your indicators look healthy! Keep up regular exercise, a balanced diet, "
                  "good sleep and annual check-ups."}]
    return {
        "risk_level": risk_level,
        "personalised_recommendations": items,
        "lifestyle_score": compute_lifestyle_score(p),
        "priority_actions": [r["advice"] for r in items[:3]],
        "monitoring_advice": monitoring_advice(p, risk_level),
    }
