"""Reusable Streamlit chat widget. Embed in your existing app.py with:

    from chat_ui import render_chat
    render_chat(user_id=st.session_state.user_email)      # after login
"""
from __future__ import annotations
import os
import requests
import streamlit as st

API = os.getenv("API_URL", "")          # empty → run in-process (no separate server needed)
HEADERS = {"X-API-Key": os.getenv("API_KEY", "")} if os.getenv("API_KEY") else {}

# (key, label, kind, default, extra)
PROFILE_FORM = [
    ("age", "Age", "int", 40, (1, 120)), ("sex", "Sex", "sel", "Male", ["Male", "Female"]),
    ("height_cm", "Height (cm)", "float", 170.0, (100.0, 250.0)), ("weight_kg", "Weight (kg)", "float", 70.0, (25.0, 300.0)),
    ("diet_preference", "Food preference", "sel", "nonveg", ["nonveg", "veg", "vegan"]),
    ("cholesterol", "Cholesterol (mg/dL)", "int", 200, (100, 600)), ("triglycerides", "Triglycerides (mg/dL)", "int", 150, (50, 1000)),
    ("systolic_bp", "Systolic BP", "int", 120, (60, 250)), ("diastolic_bp", "Diastolic BP", "int", 80, (40, 150)),
    ("heart_rate", "Resting heart rate", "int", 75, (30, 220)), ("bmi", "BMI", "float", 24.0, (10.0, 70.0)),
    ("stress_level", "Stress (1-10)", "int", 5, (1, 10)), ("exercise_hours_per_week", "Exercise hrs/week", "float", 3.0, (0.0, 40.0)),
    ("sedentary_hours_per_day", "Sitting hrs/day", "float", 6.0, (0.0, 24.0)),
    ("physical_activity_days_per_week", "Active days/week", "int", 3, (0, 7)), ("sleep_hours_per_day", "Sleep hrs/day", "int", 7, (1, 24)),
    ("diet", "Diet quality", "sel", "Average", ["Healthy", "Average", "Unhealthy"]), ("income", "Annual income (USD)", "int", 30000, (0, 10_000_000)),
]
FLAGS = [("diabetes", "Diabetes"), ("family_history", "Family history of heart disease"),
         ("previous_heart_problems", "Previous heart problems"), ("medication_use", "On cardiac medication"),
         ("smoking", "Smoker"), ("obesity", "Obesity"), ("alcohol_consumption", "Regular alcohol"),
         ("kidney_disease", "Kidney disease"), ("pregnant", "Pregnant")]
ALLERGIES = ["nuts", "dairy", "egg", "fish", "gluten", "soy"]


def _local(method, path, json=None, params=None):
    """Same contract as the HTTP API, but calls the code directly (single process, e.g. Streamlit Cloud)."""
    from core import db
    from chatbot import tools
    from chatbot.agent import handle_message
    try:
        if path == "/chat":
            return 200, handle_message(json["user_id"], json["message"])
        if path == "/history":
            return 200, {"messages": db.get_history(params["user_id"], 30)}
        if path == "/profile" and method == "GET":
            prof = db.get_profile(params["user_id"])
            return 200, {"profile": prof, "missing_for_risk": tools.missing_for_risk(prof)}
        if path == "/profile":
            return 200, tools.update_profile(json["user_id"], json["fields"])
        if path == "/readings" and method == "POST":
            r = tools.log_reading(json["user_id"], json["kind"], json["value1"], json.get("value2"),
                                  json.get("context", "random"), json.get("source", "manual"))
            return (422, {"detail": r["reason"]}) if r["status"] == "rejected" else (200, r)
        return 404, {"detail": "unknown path"}
    except Exception as e:
        return 0, {"detail": f"Assistant error: {e}"}


def _call(method, path, **kw):
    if not API:
        return _local(method, path, **kw)
    try:
        r = requests.request(method, f"{API}/assistant{path}", headers=HEADERS, timeout=60, **kw)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"detail": f"Cannot reach the API at {API} ({e})"}


def _sidebar(uid):
    with st.sidebar:
        st.subheader("📏 Log a reading")
        c1, c2 = st.columns(2)
        sys_ = c1.number_input("Systolic", 0, 300, 0); dia = c2.number_input("Diastolic", 0, 200, 0)
        if st.button("Save BP") and sys_ and dia:
            code, r = _call("POST", "/readings", json={"user_id": uid, "kind": "bp", "value1": sys_, "value2": dia})
            st.error(r.get("detail", "")) if code != 200 else st.success(f"Saved ({r['category'].replace('_', ' ')})")
            if code == 200 and r.get("alert"): st.warning(r["alert"]["message"])
        g = st.number_input("Glucose (mg/dL)", 0, 800, 0)
        ctx = st.selectbox("When?", ["fasting", "post_meal", "random"])
        if st.button("Save glucose") and g:
            code, r = _call("POST", "/readings", json={"user_id": uid, "kind": "glucose", "value1": g, "context": ctx})
            st.error(r.get("detail", "")) if code != 200 else st.success(f"Saved ({r['category'].replace('_', ' ')})")
            if code == 200 and r.get("alert"): st.warning(r["alert"]["message"])
        st.caption("Sensor/gateway devices can POST to /assistant/readings with their own `source`.")

        with st.expander("👤 My profile", expanded=False):
            _, cur = _call("GET", "/profile", params={"user_id": uid})
            prof = cur.get("profile", {})
            with st.form("profile"):
                vals = {}
                for key, label, kind, default, extra in PROFILE_FORM:
                    d = prof.get(key, default)
                    if kind == "sel": vals[key] = st.selectbox(label, extra, index=extra.index(d) if d in extra else 0)
                    elif kind == "int": vals[key] = int(st.number_input(label, extra[0], extra[1], int(d)))
                    else: vals[key] = float(st.number_input(label, extra[0], extra[1], float(d)))
                for key, label in FLAGS: vals[key] = st.checkbox(label, bool(prof.get(key, False)))
                vals["allergies"] = st.multiselect("Food allergies", ALLERGIES, prof.get("allergies", []))
                if st.form_submit_button("Save profile"):
                    code, r = _call("PUT", "/profile", json={"user_id": uid, "fields": vals})
                    st.success("Profile saved") if not r.get("errors") else st.error(r["errors"])


def _render_tools(results):
    for x in results:
        r = x["result"]
        if x["name"] == "generate_diet_chart" and r.get("status") == "ok":
            tabs = st.tabs([f"Day {d['day']}" for d in r["days"]])
            for tab, d in zip(tabs, r["days"]):
                with tab:
                    st.table([{"Meal": s.title(), "Food": i["name"], "Servings": i["servings"], "kcal": i["kcal"]}
                              for s, items in d["meals"].items() for i in items])
                    st.caption(f"Total ≈ {d['totals']['kcal']} kcal · sodium {d['totals']['sodium_mg']} mg")


def render_chat(user_id: str, inject_theme: bool = True):
    if inject_theme:
        import theme; theme.inject()
    st.title("🫀 CardioGuide")
    st.caption("Demo assistant on a synthetic-data model. Not medical advice. In an emergency, call your local emergency number.")
    _sidebar(user_id)
    if "msgs" not in st.session_state or st.session_state.get("msgs_user") != user_id:
        _, h = _call("GET", "/history", params={"user_id": user_id})
        st.session_state.msgs, st.session_state.msgs_user = [{"role": m["role"], "content": m["content"], "tools": []}
                                                             for m in h.get("messages", [])], user_id
    quick = st.columns(4)
    pick = None
    for col, (label, text) in zip(quick, [("My risk", "What is my heart risk?"), ("Diet chart", "Make me a diet chart"),
                                          ("Weekly diet", "Make me a weekly diet chart"), ("Tips", "Give me recommendations")]):
        if col.button(label): pick = text
    for m in st.session_state.msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["content"]); _render_tools(m.get("tools", []))
    text = st.chat_input("Ask about your heart health, diet, or log a reading (e.g. 'BP 128/84')") or pick
    if text:
        st.session_state.msgs.append({"role": "user", "content": text, "tools": []})
        with st.chat_message("user"): st.markdown(text)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                code, r = _call("POST", "/chat", json={"user_id": user_id, "message": text})
            reply = r.get("reply") or f"⚠️ {r.get('detail', 'Something went wrong.')}"
            st.markdown(reply); _render_tools(r.get("tool_results", []))
        st.session_state.msgs.append({"role": "assistant", "content": reply, "tools": r.get("tool_results", [])})
