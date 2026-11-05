"""Tiny vetted glossary. Replace/extend with a RAG index over guideline summaries later."""
GLOSSARY = {
    "blood pressure": "Blood pressure is the force of blood on artery walls, written as systolic/diastolic (e.g. 120/80 mmHg). Systolic is the pressure when the heart beats; diastolic is between beats.",
    "hypertension": "Hypertension means persistently high blood pressure. It strains the heart and arteries and raises heart attack and stroke risk. Diagnosis needs repeated readings checked by a clinician.",
    "cholesterol": "Cholesterol is a fatty substance in the blood. Too much 'bad' (LDL) cholesterol can build up in artery walls. A lipid blood test measures it.",
    "ldl": "LDL is often called 'bad' cholesterol because high levels can clog arteries.",
    "hdl": "HDL is often called 'good' cholesterol because it helps carry cholesterol away from arteries.",
    "triglycerides": "Triglycerides are a type of fat in the blood. High levels are linked to refined carbs, sugar, alcohol and excess weight.",
    "hba1c": "HbA1c reflects your average blood sugar over about 3 months. It is used to screen for and monitor diabetes; targets are set by your doctor.",
    "diabetes": "Diabetes is a condition where blood sugar stays too high. It raises heart disease risk, so blood sugar, blood pressure and cholesterol are managed together.",
    "bmi": "BMI is weight (kg) divided by height (m) squared. It is a rough screening tool and doesn't measure body fat or fitness directly.",
    "glycemic index": "Glycemic index (GI) ranks how fast a food raises blood sugar. Low-GI foods (oats, lentils, most vegetables) raise it more slowly.",
    "dash diet": "DASH is an eating pattern rich in vegetables, fruit, whole grains, legumes and low-fat dairy, with less salt, designed to lower blood pressure.",
    "sodium": "Sodium (mostly from salt) raises blood pressure in many people. Many guidelines suggest keeping it under about 2,300 mg/day, and lower for people with high blood pressure.",
    "heart attack": "A heart attack happens when blood flow to part of the heart is blocked. Warning signs include chest pain or pressure, breathlessness, pain in the arm or jaw, sweating and nausea. It is an emergency.",
}


def explain(term: str) -> str | None:
    t = term.lower().strip(" ?.!")
    for k, v in GLOSSARY.items():
        if k in t or t in k:
            return v
    return None
