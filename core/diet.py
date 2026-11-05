"""Deterministic diet-chart generator. The LLM never invents numbers: it only explains this output.
Food values in data/foods.csv are APPROXIMATE; replace with verified composition data."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

FOODS_CSV = Path(__file__).resolve().parent.parent / "data" / "foods.csv"
SLOT_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
DIET_RANK = {"vegan": 0, "veg": 1, "nonveg": 2}
ALLERGENS = {"nuts", "dairy", "egg", "fish", "gluten", "soy"}
DISCLAIMER = ("General healthy-eating guidance, not a prescription. If you have diabetes, kidney disease, "
              "are pregnant, or take medication, have a doctor or registered dietitian review this plan.")


def _foods() -> pd.DataFrame:
    df = pd.read_csv(FOODS_CSV, keep_default_na=False)
    df["allergen_set"] = df["allergens"].apply(lambda s: {a for a in str(s).split(";") if a})
    return df


def calorie_target(age, sex, height_cm, weight_kg, activity_days) -> tuple[int, float]:
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "Male" else -161)
    factor = 1.2 if activity_days <= 1 else 1.375 if activity_days <= 3 else 1.55 if activity_days <= 5 else 1.725
    bmi = weight_kg / (height_cm / 100) ** 2
    target = bmr * factor * (0.85 if bmi >= 25 else 1.0)
    return int(round(max(target, 1500 if sex == "Male" else 1200), -1)), round(bmi, 1)


def generate_diet_chart(*, age, sex, height_cm, weight_kg, activity_days, conditions=(),
                        diet_preference="nonveg", allergies=(), days=1) -> dict:
    cond = set(conditions)
    if cond & {"kidney_disease", "pregnant"}:
        return {"status": "needs_clinician", "message":
                "With kidney disease or pregnancy, diet needs must be set by your doctor or dietitian, "
                "so I can't generate a chart for you.", "disclaimer": DISCLAIMER}
    target, bmi = calorie_target(age, sex, height_cm, weight_kg, activity_days)
    sodium_limit = 1500 if "hypertension" in cond else 2300
    df = _foods()
    df = df[df["diet"].map(DIET_RANK) <= DIET_RANK.get(diet_preference, 2)]
    bad = set(allergies) & ALLERGENS
    df = df[df["allergen_set"].apply(lambda s: not (s & bad))]
    if "diabetes" in cond or "high_triglycerides" in cond:
        df = df[df["gi"] != "high"]
    if "hypertension" in cond:
        df = df[df["sodium_mg"] <= 600]
    if "high_cholesterol" in cond:
        df = df[df["sat_fat_g"] <= 5]
    warnings, chart = [], []
    for d in range(max(1, min(days, 7))):
        meals, tot = {}, dict.fromkeys(("kcal", "carbs_g", "protein_g", "sat_fat_g", "sodium_mg"), 0.0)
        for slot, share in SLOT_SHARE.items():
            pool = df[df["meal"] == slot].copy()
            if pool.empty:
                warnings.append(f"No suitable {slot} foods for your constraints; add options to data/foods.csv.")
                continue
            pool["score"] = pool["sat_fat_g"] * 2 + pool["sodium_mg"] / 200 + (pool["gi"] == "high") * 3
            pool = pool.sort_values(["score", "name"]).reset_index(drop=True)
            budget, items = target * share, []
            for k in range(2):
                row = pool.iloc[(d + k) % len(pool)]
                if k and any(i["name"] == row["name"] for i in items):
                    break
                remaining = budget - sum(i["kcal"] for i in items)
                if k and remaining < 0.6 * row["kcal"]:
                    break
                sv = min(2.0, max(0.5, round(remaining / row["kcal"] * 2) / 2))
                it = {"name": row["name"], "servings": sv}
                for key in tot:
                    it[key] = round(float(row[key if key != "kcal" else "kcal"]) * sv, 1)
                    tot[key] += it[key]
                items.append(it)
            meals[slot] = items
        if tot["sodium_mg"] > sodium_limit:
            warnings.append(f"Day {d + 1}: sodium {int(tot['sodium_mg'])} mg exceeds your {sodium_limit} mg limit.")
        chart.append({"day": d + 1, "meals": meals, "totals": {k: round(v) for k, v in tot.items()}})
    return {"status": "ok", "target_kcal": target, "bmi": bmi, "sodium_limit_mg": sodium_limit,
            "days": chart, "warnings": sorted(set(warnings)), "disclaimer": DISCLAIMER}


def chart_to_text(c: dict) -> str:
    if c.get("status") != "ok":
        return c.get("message", "Could not generate a diet chart.")
    out = [f"Daily target about {c['target_kcal']} kcal (BMI {c['bmi']})."]
    for day in c["days"]:
        out.append(f"\nDay {day['day']}  ·  {day['totals']['kcal']} kcal, sodium {day['totals']['sodium_mg']} mg")
        for slot, items in day["meals"].items():
            out.append(f"• {slot.title()}: " + "; ".join(f"{i['name']} ×{i['servings']:g}" for i in items))
    out += [f"⚠️ {w}" for w in c["warnings"]]
    return "\n".join(out)
