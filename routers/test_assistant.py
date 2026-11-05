import pytest
from fastapi.testclient import TestClient

FULL = dict(age=55, sex="Male", cholesterol=250, systolic_bp=150, diastolic_bp=95, heart_rate=80, bmi=31.0,
            triglycerides=210, diabetes=True, family_history=True, previous_heart_problems=False,
            medication_use=False, smoking=True, obesity=False, alcohol_consumption=False, diet="Unhealthy",
            stress_level=8, exercise_hours_per_week=1.0, sedentary_hours_per_day=9.0,
            physical_activity_days_per_week=1, sleep_hours_per_day=5, income=40000,
            height_cm=172, weight_kg=90, diet_preference="nonveg", allergies=["nuts"])
HEALTHY = {**FULL, "age": 30, "sex": "Female", "cholesterol": 170, "systolic_bp": 110, "diastolic_bp": 70,
           "bmi": 22.0, "triglycerides": 100, "diabetes": False, "family_history": False, "smoking": False,
           "diet": "Healthy", "stress_level": 2, "exercise_hours_per_week": 10.0, "sedentary_hours_per_day": 3.0,
           "physical_activity_days_per_week": 6, "sleep_hours_per_day": 8}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("HEART_DB", str(tmp_path / "t.db"))
    monkeypatch.delenv("API_KEY", raising=False)
    from main import app
    with TestClient(app) as c:
        yield c


def chat(c, uid, msg):
    return c.post("/assistant/chat", json={"user_id": uid, "message": msg}).json()


def test_emergency_bypasses_llm(client):
    r = chat(client, "u1", "I have chest pain and I'm sweating")
    assert r["emergency"] and "emergency" in r["reply"].lower() and r["tool_results"] == []


def test_profile_validation_rejects_bad_values(client):
    r = client.put("/assistant/profile", json={"user_id": "u2", "fields": {"age": 500, "sex": "Male", "foo": 1}}).json()
    assert "age" in r["errors"] and "foo" in r["errors"] and r["saved"] == ["sex"]


def test_risk_flow_incomplete_then_complete(client):
    assert "still need" in chat(client, "u3", "what's my risk?")["reply"]
    r = client.put("/assistant/profile", json={"user_id": "u3", "fields": FULL}).json()
    assert not r["errors"] and r["still_missing_for_risk"] == []
    out = chat(client, "u3", "what's my risk?")
    assert "estimated risk" in out["reply"] and "synthetic" in out["reply"]


def test_risk_factors_only_those_present(client):
    from schemas import PatientInput
    from core.risk import risk_factors
    f = risk_factors(PatientInput(**{k: v for k, v in HEALTHY.items() if k in PatientInput.model_fields}))
    assert f == []                      # healthy patient: no fake factors


def test_bp_logging_and_crisis_alert(client):
    r = chat(client, "u4", "my BP is 190/125")
    assert "dangerously high" in r["reply"]
    ok = chat(client, "u4", "BP 118/76")
    assert "normal" in ok["reply"]
    assert "average" in chat(client, "u4", "show my bp trend")["reply"]


def test_implausible_reading_rejected(client):
    assert client.post("/assistant/readings", json={"user_id": "u5", "kind": "bp", "value1": 20, "value2": 10}).status_code == 422


def test_latest_bp_overrides_profile(client):
    client.put("/assistant/profile", json={"user_id": "u6", "fields": HEALTHY})
    client.post("/assistant/readings", json={"user_id": "u6", "kind": "bp", "value1": 165, "value2": 100})
    from chatbot.tools import build_patient
    p, _ = build_patient("u6")
    assert (p.systolic_bp, p.diastolic_bp) == (165, 100)


def test_diet_respects_constraints(client):
    client.put("/assistant/profile", json={"user_id": "u7", "fields": FULL})
    c = client.post("/assistant/diet-chart", json={"user_id": "u7", "days": 3}).json()
    assert c["status"] == "ok" and len(c["days"]) == 3
    from core.diet import _foods
    foods = _foods().set_index("name")
    for d in c["days"]:
        assert 0.75 * c["target_kcal"] <= d["totals"]["kcal"] <= 1.25 * c["target_kcal"]
        for items in d["meals"].values():
            for it in items:
                assert foods.loc[it["name"], "gi"] != "high"            # diabetic
                assert "nuts" not in foods.loc[it["name"], "allergen_set"]  # allergy


def test_diet_blocked_for_pregnancy():
    from core.diet import generate_diet_chart
    r = generate_diet_chart(age=30, sex="Female", height_cm=165, weight_kg=70, activity_days=3, conditions=["pregnant"])
    assert r["status"] == "needs_clinician"


def test_recommendations_dedup_and_server_side_risk(client):
    body = {"patient_data": {k: v for k, v in {**HEALTHY, "systolic_bp": 150, "diastolic_bp": 85, "obesity": True, "bmi": 27.0}.items()
                             if k in ("age", "sex", "cholesterol", "systolic_bp", "diastolic_bp", "heart_rate", "bmi", "triglycerides", "diabetes", "family_history", "previous_heart_problems", "medication_use", "smoking", "obesity", "alcohol_consumption", "diet", "stress_level", "exercise_hours_per_week", "sedentary_hours_per_day", "physical_activity_days_per_week", "sleep_hours_per_day", "income")},
            "prediction_result": {"risk_probability": .1, "risk_score_percent": 10, "risk_level": "LOW", "risk_label": 0, "rf_probability": .1, "gb_probability": .1, "top_risk_factors": [], "message": "x"}}
    r = client.post("/recommendations", json=body).json()
    cats = [x["category"] for x in r["personalised_recommendations"]]
    assert len(cats) == len(set(cats))                                  # no duplicate categories
    assert r["risk_level"] != "LOW" or r["risk_level"] == client.post("/predict", json=body["patient_data"]).json()["risk_level"]


def test_bp_stage_boundary():
    from core.safety import classify_bp
    assert classify_bp(140, 70) == "stage2" and classify_bp(139, 70) == "stage1" and classify_bp(181, 80) == "hypertensive_crisis"


def test_api_key_enforced(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    assert client.get("/assistant/profile", params={"user_id": "x"}).status_code == 401
    assert client.get("/assistant/profile", params={"user_id": "x"}, headers={"X-API-Key": "secret"}).status_code == 200


def test_llm_failure_falls_back_offline(client, monkeypatch):
    from chatbot import agent
    from chatbot.llm import LLMError
    class Broken:
        def chat(self, m, t): raise LLMError("down")
    r = agent.handle_message("u9", "explain cholesterol", llm=Broken())
    assert "basic mode" in r["reply"] and "cholesterol" in r["reply"].lower()
