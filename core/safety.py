"""Deterministic safety layer. Runs BEFORE any LLM and never depends on one."""
from __future__ import annotations
import re

EMERGENCY_REPLY = (
    "⚠️ What you describe could be a medical emergency. Please call your local "
    "emergency number or go to the nearest emergency department right now. "
    "If you can, don't go alone and don't drive yourself. "
    "I can't help with emergencies, so please get help first."
)
CRISIS_REPLY = (
    "I'm really sorry you're feeling this way. You deserve support right now. "
    "Please contact your local emergency number or a crisis line, or reach out to "
    "someone you trust and stay with them. If you are in immediate danger, call emergency services."
)

_RED = [
    r"chest (pain|pressure|tightness)", r"pain.{0,30}(left arm|jaw)",
    r"(can'?t|cannot|hard to|difficulty|trouble) breath", r"short(ness)? of breath",
    r"\bfaint(ed|ing)?\b", r"passed out", r"slurred speech",
    r"(face|arm|leg).{0,20}(droop|numb|weak)", r"coughing (up )?blood",
]
_CRISIS = [r"suicid", r"kill myself", r"end my life", r"want to die"]


def check_text(text: str) -> str | None:
    t = text.lower()
    if any(re.search(p, t) for p in _CRISIS):
        return CRISIS_REPLY
    if any(re.search(p, t) for p in _RED):
        return EMERGENCY_REPLY
    return None


# ── Readings ────────────────────────────────────────────────
RANGES = {"bp": ((60, 260), (30, 160)), "glucose": ((20, 800), None), "hr": ((25, 240), None)}


def validate_reading(kind: str, v1: float, v2: float | None) -> None:
    if kind not in RANGES:
        raise ValueError(f"kind must be one of {list(RANGES)}")
    (lo1, hi1), r2 = RANGES[kind][0], RANGES[kind][1]
    if not lo1 <= v1 <= hi1:
        raise ValueError(f"{kind} value {v1} is outside the plausible range {lo1}-{hi1}; please re-measure")
    if r2:
        if v2 is None:
            raise ValueError("blood pressure needs systolic AND diastolic")
        if not r2[0] <= v2 <= r2[1] or v2 >= v1:
            raise ValueError("diastolic value looks wrong; please re-measure")


def classify_bp(sys_: float, dia: float) -> str:
    if sys_ > 180 or dia > 120: return "hypertensive_crisis"
    if sys_ >= 140 or dia >= 90: return "stage2"
    if sys_ >= 130 or dia >= 80: return "stage1"
    if sys_ >= 120: return "elevated"
    if sys_ < 90 or dia < 60: return "low"
    return "normal"


def classify_glucose(mg_dl: float, context: str = "random") -> str:
    if mg_dl < 54: return "very_low"
    if mg_dl < 70: return "low"
    if mg_dl >= 300: return "very_high"
    if context == "fasting":
        return "normal" if mg_dl < 100 else "prediabetes_range" if mg_dl < 126 else "diabetes_range"
    if context == "post_meal":
        return "normal" if mg_dl < 140 else "prediabetes_range" if mg_dl < 200 else "diabetes_range"
    return "normal" if mg_dl < 140 else "elevated" if mg_dl < 200 else "high"


def reading_alert(kind: str, category: str) -> dict | None:
    """Deterministic advice for dangerous categories. Returns None when no alert."""
    if kind == "bp" and category == "hypertensive_crisis":
        return {"level": "emergency", "message":
                "This blood pressure is dangerously high. Sit quietly and re-measure after 5 minutes. "
                "If it is still this high, contact a doctor right now. If you also have chest pain, "
                "breathlessness, vision changes, weakness or severe headache, call emergency services."}
    if kind == "bp" and category == "low":
        return {"level": "urgent", "message":
                "This reading is low. If you feel dizzy, faint or unwell, sit or lie down and seek medical help."}
    if kind == "glucose" and category in ("very_low", "low"):
        return {"level": "urgent", "message":
                "This glucose is low. If you take diabetes medication, follow your doctor's low-sugar plan "
                "(fast-acting sugar) and get help if you feel confused, shaky or faint."}
    if kind == "glucose" and category == "very_high":
        return {"level": "urgent", "message":
                "This glucose is very high. Contact your doctor today, and seek emergency care if you have "
                "vomiting, confusion, severe thirst or trouble breathing."}
    return None
