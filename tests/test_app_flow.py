"""End-to-end UI tests for the patched Streamlit app (auth, escaping, chat view)."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("HEART_DB", str(tmp_path / "t.db"))
    monkeypatch.delenv("API_URL", raising=False)
    return AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60).run()


def _login(at, email, pw):
    at.text_input(key="li_email").set_value(email); at.text_input(key="li_pass").set_value(pw)
    at.button(key="li_btn").click(); return at.run()


def _signup(at, name, email, pw):
    at.button(key="li_signup").click(); at.run()
    at.text_input(key="su_name").set_value(name); at.text_input(key="su_email").set_value(email)
    at.text_input(key="su_pass").set_value(pw); at.button(key="su_btn").click(); return at.run()


def test_patient_id_password_no_longer_works(app):
    at = _login(app, "bmw7812@heartdb.com", "bmw7812")
    assert not at.session_state["current_user"] and any("Incorrect" in e.value for e in at.error)


def test_signup_login_and_wrong_password_generic(app):
    at = _signup(app, "Sara", "sara@example.com", "correct-horse")
    assert not at.exception
    assert any("Incorrect" in e.value for e in _login(at, "ghost@example.com", "whatever1").error)   # unknown email: same msg
    at = _login(at, "sara@example.com", "wrong-password")
    assert any("Incorrect" in e.value for e in at.error)
    at = _login(at, "sara@example.com", "correct-horse")
    assert at.session_state["current_user"]["email"] == "sara@example.com"


def test_lockout_after_five_failures(app):
    _signup(app, "Lock", "lock@example.com", "correct-horse")
    at = app
    for _ in range(5):
        at = _login(at, "lock@example.com", "bad-password")
    at = _login(at, "lock@example.com", "correct-horse")          # even the right password is refused now
    assert any("Too many" in e.value for e in at.error)


def test_html_in_name_is_escaped(app):
    at = _signup(app, "<img src=x onerror=alert(1)>", "xss@example.com", "correct-horse")
    at = _login(at, "xss@example.com", "correct-horse")
    html = " ".join(m.value for m in at.markdown)
    assert "<img src=x" not in html and "&lt;img" in html


def test_demo_patient_runs_real_model_and_chat(app):
    at = app.button(key="li_demo").click().run()
    assert at.session_state["current_user"]["email"].startswith("demo_")
    at.radio(key="view").set_value("🫀 Assistant").run()
    assert not at.exception
    at.chat_input[0].set_value("BP 128/84").run()
    assert not at.exception and "Saved your bp reading" in at.chat_message[-1].markdown[0].value
    at.chat_input[0].set_value("I have chest pain").run()
    assert "emergency" in at.chat_message[-1].markdown[0].value.lower()


def test_real_model_replaces_heuristic(tmp_path, monkeypatch):
    monkeypatch.setenv("HEART_DB", str(tmp_path / "t.db"))
    from core.risk import coerce_patient, predict_risk
    d = dict(age=67.0, sex="Male", cholesterol=208.0, systolic_bp=150, diastolic_bp=95, heart_rate=72, bmi=31.25,
             triglycerides=286, diabetes=False, family_history=False, previous_heart_problems=False, medication_use=False,
             smoking=True, obesity=False, alcohol_consumption=False, diet="Average", stress_level=9,
             exercise_hours_per_week=4.17, sedentary_hours_per_day=6.62, physical_activity_days_per_week=0,
             sleep_hours_per_day=6, income=261404)
    r = predict_risk(coerce_patient(d))
    assert r["rf_probability"] != round(r["risk_probability"] * 0.97 + 0.01, 4)     # not the old fake derivation
    assert "disclaimer" in r
