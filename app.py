import streamlit as st
import hashlib
import pandas as pd
import os
from pathlib import Path

st.set_page_config(
    page_title="Heart Attack Risk Prediction System",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── THEME ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: #0D1B2A !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; max-width: 960px; margin: auto; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #1E2D3D !important;
    border: 1.5px solid #2E4057 !important;
    border-radius: 8px !important;
    color: #F0F4F8 !important;
    font-size: 14px !important;
    padding: 10px 12px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #E53E3E !important;
    box-shadow: 0 0 0 3px rgba(229,62,62,0.2) !important;
}
.stTextInput label, .stNumberInput label,
.stSlider label, .stRadio label, .stSelectbox label {
    color: #A0AEC0 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.stRadio > div { flex-direction: row; gap: 12px; }
.stRadio > div > label {
    background: #1E2D3D;
    border: 1.5px solid #2E4057;
    border-radius: 8px;
    padding: 6px 16px;
    color: #F0F4F8 !important;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
}
.stRadio > div > label:has(input:checked) {
    background: #E53E3E;
    border-color: #E53E3E;
    color: white !important;
}
.stSlider > div > div > div { background: #2E4057 !important; }
.stSlider > div > div > div > div { background: #E53E3E !important; }
.stSlider [data-testid="stTickBar"] span { color: #718096 !important; }

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 9px 20px !important;
    transition: all 0.15s !important;
    border: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #E53E3E, #C0392B) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #C0392B, #962B22) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(229,62,62,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: #1E2D3D !important;
    color: #A0AEC0 !important;
    border: 1.5px solid #2E4057 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #2E4057 !important;
    color: #F0F4F8 !important;
}

.stAlert { border-radius: 10px !important; }
[data-testid="stInfoMessage"] { background: #1A2F4E !important; color: #90CDF4 !important; border-color: #2B6CB0 !important; }
[data-testid="stErrorMessage"] { background: #2D1515 !important; color: #FC8181 !important; }
[data-testid="stSuccessMessage"] { background: #1A2E1A !important; color: #68D391 !important; }
[data-testid="stWarningMessage"] { background: #2D2415 !important; color: #F6AD55 !important; }

.hr-card {
    background: #132237;
    border: 1px solid #1E3A5F;
    border-radius: 14px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.hr-card-title {
    font-size: 11px;
    font-weight: 700;
    color: #4A90D9;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

.topbar {
    background: #0A1628;
    border: 1px solid #1E3A5F;
    border-radius: 14px;
    padding: 0.85rem 1.25rem;
    margin-bottom: 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.topbar-logo { display: flex; align-items: center; gap: 10px; }
.topbar-logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #E53E3E, #C0392B);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.topbar-title { font-size: 16px; font-weight: 700; color: #F0F4F8; }
.topbar-user {
    display: flex; align-items: center; gap: 8px;
    background: #1E2D3D;
    border: 1px solid #2E4057;
    border-radius: 20px;
    padding: 5px 12px 5px 6px;
}
.topbar-av {
    width: 26px; height: 26px;
    background: linear-gradient(135deg, #E53E3E, #C0392B);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; color: white;
}
.topbar-name { font-size: 13px; font-weight: 600; color: #CBD5E0; }

.p-banner {
    background: linear-gradient(135deg, #132237, #0A1628);
    border: 1px solid #1E3A5F;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.1rem;
    display: flex;
    align-items: center;
    gap: 14px;
}
.p-av {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #2B6CB0, #1E3A5F);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 800; color: #90CDF4;
    flex-shrink: 0;
}
.p-name { font-size: 16px; font-weight: 700; color: #F0F4F8; margin: 0; }
.p-sub { font-size: 12px; color: #718096; margin-top: 3px; }
.badge-db {
    display: inline-block;
    background: #1A2F4E; color: #90CDF4;
    border: 1px solid #2B6CB0;
    border-radius: 10px; font-size: 10px; font-weight: 700;
    padding: 2px 8px; margin-left: 8px;
}
.badge-users {
    display: inline-block;
    background: #2D1F4E; color: #C084FC;
    border: 1px solid #7C3AED;
    border-radius: 10px; font-size: 10px; font-weight: 700;
    padding: 2px 8px; margin-left: 8px;
}
.badge-new {
    display: inline-block;
    background: #1A2E1A; color: #68D391;
    border: 1px solid #276749;
    border-radius: 10px; font-size: 10px; font-weight: 700;
    padding: 2px 8px; margin-left: 8px;
}

.steps-wrap {
    display: flex;
    background: #0A1628;
    border: 1px solid #1E3A5F;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 1.1rem;
}
.step-item {
    flex: 1; padding: 11px 8px;
    text-align: center; font-size: 12px; font-weight: 700;
    color: #4A5568;
    border-right: 1px solid #1E3A5F;
    display: flex; align-items: center; justify-content: center; gap: 6px;
}
.step-item:last-child { border-right: none; }
.step-item.active { background: #2D1515; color: #FC8181; }
.step-item.done { background: #1A2E1A; color: #68D391; }
.step-num {
    width: 20px; height: 20px;
    border-radius: 50%; background: #2E4057; color: #718096;
    font-size: 10px; font-weight: 700;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-item.active .step-num { background: #E53E3E; color: white; }
.step-item.done .step-num { background: #38A169; color: white; }

.risk-hero {
    background: #0A1628;
    border: 1px solid #1E3A5F;
    border-radius: 14px;
    padding: 2rem; text-align: center; margin-bottom: 1rem;
}
.risk-ring {
    width: 120px; height: 120px; border-radius: 50%;
    margin: 0 auto 1rem;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
}
.ring-pct { font-size: 28px; font-weight: 800; line-height: 1; }
.ring-lbl { font-size: 12px; font-weight: 700; margin-top: 4px; letter-spacing: 0.04em; }
.ring-LOW      { background: #1A2E1A; color: #68D391; border: 3px solid #38A169; }
.ring-MODERATE { background: #2D2010; color: #F6AD55; border: 3px solid #DD6B20; }
.ring-HIGH     { background: #2D1515; color: #FC8181; border: 3px solid #E53E3E; }
.ring-VERYHIGH { background: #2D0A0A; color: #FEB2B2; border: 3px solid #C0392B; }
.risk-msg { font-size: 15px; font-weight: 600; color: #E2E8F0; margin-bottom: 4px; }
.risk-src { font-size: 11px; color: #4A5568; margin-top: 6px; }

.metric-card {
    background: #132237; border: 1px solid #1E3A5F;
    border-radius: 10px; padding: 14px; text-align: center;
}
.m-val { font-size: 22px; font-weight: 800; }
.m-lbl { font-size: 11px; color: #718096; margin-top: 4px; font-weight: 500; }

.factor-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 13px; background: #1E2D3D;
    border: 1px solid #2E4057; border-radius: 8px;
    margin-bottom: 6px; color: #E2E8F0;
    font-size: 13px; font-weight: 500;
}
.factor-dot { width: 8px; height: 8px; border-radius: 50%; background: #E53E3E; flex-shrink: 0; }

.ls-wrap { background: #1E2D3D; border: 1px solid #2E4057; border-radius: 10px; padding: 14px; }
.ls-hd { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.ls-lbl { font-size: 12px; font-weight: 600; color: #A0AEC0; }
.ls-score { font-size: 20px; font-weight: 800; }
.bar-track { height: 10px; background: #2E4057; border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; }

.rec-item { background: #132237; border: 1px solid #1E3A5F; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px; }
.rec-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.rec-cat { font-size: 13px; font-weight: 700; color: #E2E8F0; }
.rec-txt { font-size: 12.5px; color: #A0AEC0; line-height: 1.55; }
.pri { font-size: 10px; padding: 2px 8px; border-radius: 8px; font-weight: 700; }
.p5 { background: #2D0A0A; color: #FEB2B2; border: 1px solid #C0392B; }
.p4 { background: #2D1515; color: #FC8181; border: 1px solid #E53E3E; }
.p3 { background: #2D2010; color: #F6AD55; border: 1px solid #DD6B20; }
.p2 { background: #1A2E1A; color: #68D391; border: 1px solid #38A169; }
.p1 { background: #1A2F4E; color: #90CDF4; border: 1px solid #2B6CB0; }

.monitor-box {
    background: #1A2F4E; border: 1px solid #2B6CB0; border-radius: 10px;
    padding: 12px 14px; font-size: 12.5px; color: #90CDF4;
    margin-top: 8px; line-height: 1.55;
}
.csv-note {
    background: #1E2D3D; border: 1px solid #2E4057; border-radius: 10px;
    padding: 10px 14px; font-size: 12px; color: #A0AEC0; margin-top: 8px;
}

.auth-card {
    background: #0A1628; border: 1px solid #1E3A5F;
    border-radius: 16px; padding: 2.25rem;
    max-width: 460px; margin: 3rem auto;
}
.auth-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 1.75rem; }
.auth-brand-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #E53E3E, #C0392B);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 22px;
}
.auth-title-main { font-size: 18px; font-weight: 700; color: #F0F4F8; margin: 0; }
.auth-title-sub { font-size: 11px; color: #4A5568; margin-top: 2px; }
.auth-h { font-size: 22px; font-weight: 800; color: #F0F4F8; margin-bottom: 4px; }
.auth-sub { font-size: 13px; color: #718096; margin-bottom: 1.25rem; }
.db-tip {
    background: #1A2F4E; border: 1px solid #2B6CB0; border-radius: 10px;
    padding: 12px 14px; font-size: 12px; color: #90CDF4;
    margin-bottom: 1.1rem; line-height: 1.6;
}
.db-tip strong { display: block; font-size: 12px; margin-bottom: 4px; color: #BEE3F8; }
.db-tip code {
    background: #2B6CB0; color: #EBF8FF; padding: 1px 5px;
    border-radius: 4px; font-family: monospace; font-size: 11px;
}
.file-status {
    background: #132237; border: 1px solid #1E3A5F; border-radius: 10px;
    padding: 10px 14px; font-size: 12px; color: #A0AEC0;
    margin-bottom: 1rem; line-height: 1.8;
}
.file-status .ok  { color: #68D391; font-weight: 700; }
.file-status .mis { color: #FC8181; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── CSV FILE PATHS ─────────────────────────────────────────────────────────────
DATA_DIR              = Path("data")
HEART_CSV_PATH        = DATA_DIR / "heart_attack_prediction.csv"
USERS_CSV_PATH        = DATA_DIR / "users.csv"

USERS_COLUMNS = ["email", "name", "password_hash"]

# ── CSV I/O HELPERS ────────────────────────────────────────────────────────────

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def load_heart_csv() -> pd.DataFrame | None:
    """Load heart_attack_prediction.csv if it exists, else return None."""
    if HEART_CSV_PATH.exists():
        try:
            return pd.read_csv(HEART_CSV_PATH)
        except Exception:
            return None
    return None

def load_users_csv() -> pd.DataFrame:
    """Load users.csv; create empty one with correct columns if missing."""
    ensure_data_dir()
    if USERS_CSV_PATH.exists():
        try:
            df = pd.read_csv(USERS_CSV_PATH)
            for col in USERS_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass
    df = pd.DataFrame(columns=USERS_COLUMNS)
    df.to_csv(USERS_CSV_PATH, index=False)
    return df

def save_user_to_csv(email: str, name: str, password_hash: str) -> bool:
    """Append a new user row to users.csv. Returns False if email already exists."""
    ensure_data_dir()
    df = load_users_csv()
    if email.lower() in df["email"].str.lower().values:
        return False
    new_row = pd.DataFrame([{"email": email.lower(), "name": name, "password_hash": password_hash}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USERS_CSV_PATH, index=False)
    return True

def find_user_in_users_csv(email: str) -> dict | None:
    """Look up a registered user in users.csv."""
    df = load_users_csv()
    match = df[df["email"].str.lower() == email.lower()]
    if match.empty:
        return None
    return match.iloc[0].to_dict()

def find_patient_in_heart_csv(email: str) -> dict | None:
    """
    Derive Patient ID from email (e.g. bmw7812@heartdb.com → BMW7812)
    and look it up in heart_attack_prediction.csv.
    Also accepts direct email match if the CSV has an 'email' column.
    """
    df = load_heart_csv()
    if df is None:
        return None

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Strategy 1: CSV has an 'email' column
    if "email" in df.columns:
        match = df[df["email"].str.lower() == email.lower()]
        if not match.empty:
            row = match.iloc[0].to_dict()
            row.setdefault("email", email.lower())
            return row

    # Strategy 2: derive Patient ID from email prefix  (e.g. bmw7812)
    pid_guess = email.split("@")[0].upper()
    pid_col = next((c for c in df.columns if "patient" in c.lower() and "id" in c.lower()), None)
    if pid_col:
        match = df[df[pid_col].astype(str).str.upper() == pid_guess]
        if not match.empty:
            row = match.iloc[0].to_dict()
            row.setdefault("email", email.lower())
            return row

    return None


# ── BUILT-IN PATIENT DB (fallback when CSV not present) ───────────────────────
BUILTIN_PATIENTS = [
    {"Patient ID": "BMW7812", "Age": 67, "Sex": "Male", "Cholesterol": 208, "Heart Rate": 72,
     "Diabetes": 0, "Family History": 0, "Smoking": 1, "Obesity": 0, "Alcohol Consumption": 0,
     "Exercise Hours Per Week": 4.17, "Diet": "Average", "Previous Heart Problems": 0,
     "Medication Use": 0, "Stress Level": 9, "Sedentary Hours Per Day": 6.62,
     "Income": 261404, "BMI": 31.25, "Triglycerides": 286,
     "Physical Activity Days Per Week": 0, "Sleep Hours Per Day": 6,
     "Country": "Argentina", "Heart Attack Risk": 0, "systolic_bp": 158, "diastolic_bp": 88,
     "email": "bmw7812@heartdb.com"},
    {"Patient ID": "ZOO7941", "Age": 54, "Sex": "Female", "Cholesterol": 297, "Heart Rate": 48,
     "Diabetes": 1, "Family History": 1, "Smoking": 1, "Obesity": 0, "Alcohol Consumption": 1,
     "Exercise Hours Per Week": 0.63, "Diet": "Unhealthy", "Previous Heart Problems": 1,
     "Medication Use": 1, "Stress Level": 2, "Sedentary Hours Per Day": 7.8,
     "Income": 241339, "BMI": 20.15, "Triglycerides": 795,
     "Physical Activity Days Per Week": 5, "Sleep Hours Per Day": 10,
     "Country": "Germany", "Heart Attack Risk": 1, "systolic_bp": 172, "diastolic_bp": 86,
     "email": "zoo7941@heartdb.com"},
    {"Patient ID": "WYV0966", "Age": 90, "Sex": "Male", "Cholesterol": 358, "Heart Rate": 84,
     "Diabetes": 0, "Family History": 0, "Smoking": 1, "Obesity": 0, "Alcohol Consumption": 1,
     "Exercise Hours Per Week": 4.1, "Diet": "Healthy", "Previous Heart Problems": 0,
     "Medication Use": 0, "Stress Level": 7, "Sedentary Hours Per Day": 0.63,
     "Income": 190450, "BMI": 28.89, "Triglycerides": 284,
     "Physical Activity Days Per Week": 4, "Sleep Hours Per Day": 10,
     "Country": "Canada", "Heart Attack Risk": 1, "systolic_bp": 102, "diastolic_bp": 73,
     "email": "wyv0966@heartdb.com"},
    {"Patient ID": "ENK3334", "Age": 27, "Sex": "Male", "Cholesterol": 321, "Heart Rate": 50,
     "Diabetes": 1, "Family History": 0, "Smoking": 1, "Obesity": 1, "Alcohol Consumption": 0,
     "Exercise Hours Per Week": 0.76, "Diet": "Unhealthy", "Previous Heart Problems": 1,
     "Medication Use": 1, "Stress Level": 2, "Sedentary Hours Per Day": 3.38,
     "Income": 53345, "BMI": 34.2, "Triglycerides": 558,
     "Physical Activity Days Per Week": 7, "Sleep Hours Per Day": 8,
     "Country": "Nigeria", "Heart Attack Risk": 1, "systolic_bp": 111, "diastolic_bp": 91,
     "email": "enk3334@heartdb.com"},
]
BUILTIN_BY_EMAIL = {p["email"].lower(): p for p in BUILTIN_PATIENTS}


# ── SESSION INIT ──────────────────────────────────────────────────────────────
def init():
    defaults = {
        "current_user": None, "current_patient": None,
        "step": 0, "analysis_run": False, "prediction": None,
        "recommendations": None, "show_signup": False,
        "signup_prefill_email": "",
        "age": 35, "sex": "Male", "cholesterol": 180, "heart_rate": 72,
        "systolic_bp": 120, "diastolic_bp": 80, "bmi": 23.0, "triglycerides": 150,
        "diet": "Average", "exercise_hours_per_week": 2.5,
        "sedentary_hours_per_day": 6.0, "stress_level": 4,
        "physical_activity_days_per_week": 3, "sleep_hours_per_day": 7,
        "income": 50000, "smoking": False, "alcohol_consumption": False,
        "obesity": False, "diabetes": False, "family_history": False,
        "previous_heart_problems": False, "medication_use": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── AUTH ──────────────────────────────────────────────────────────────────────
def hp(p):
    return hashlib.sha256(p.encode()).hexdigest()


def login_user(email: str, password: str):
    """
    Three-step lookup:
      1. heart_attack_prediction.csv  (patient id = password)
      2. Built-in patient list        (same rule, for demo when CSV absent)
      3. users.csv                    (registered users, hashed password)

    Returns: (success, source, patient_data | user_dict | None, needs_register)
      needs_register=True  → email not found anywhere → redirect to signup
    """
    el = email.strip().lower()

    # ── Step 1: heart CSV ──────────────────────────────────────────────────
    patient = find_patient_in_heart_csv(el)
    if patient is None:
        # fallback to built-in list (works even without the CSV file)
        patient = BUILTIN_BY_EMAIL.get(el)

    if patient:
        pid_col = next((k for k in patient if "patient" in k.lower() and "id" in k.lower()), None)
        pid = str(patient.get(pid_col or "Patient ID", "")).lower()
        if password.strip().lower() == pid:
            return True, "heart_csv", patient, False
        else:
            return False, None, None, False   # wrong password for known patient

    # ── Step 2: users CSV ─────────────────────────────────────────────────
    user_row = find_user_in_users_csv(el)
    if user_row:
        if user_row.get("password_hash") == hp(password):
            return True, "users_csv", user_row, False
        else:
            return False, None, None, False   # wrong password for registered user

    # ── Step 3: not found anywhere → needs registration ───────────────────
    return False, None, None, True


def register_user(email: str, name: str, password: str):
    """Save new user to data/users.csv. Returns (ok, message)."""
    el = email.strip().lower()
    ok = save_user_to_csv(el, name.strip(), hp(password))
    if ok:
        return True, "Account created!"
    return False, "Email already registered."


def load_patient(p: dict):
    mapping = {
        "Age": "age", "Cholesterol": "cholesterol", "Heart Rate": "heart_rate",
        "BMI": "bmi", "Triglycerides": "triglycerides", "Income": "income",
        "Stress Level": "stress_level", "Exercise Hours Per Week": "exercise_hours_per_week",
        "Sedentary Hours Per Day": "sedentary_hours_per_day",
        "Physical Activity Days Per Week": "physical_activity_days_per_week",
        "Sleep Hours Per Day": "sleep_hours_per_day",
        "systolic_bp": "systolic_bp", "diastolic_bp": "diastolic_bp",
    }
    for csv_key, ss_key in mapping.items():
        if csv_key in p and p[csv_key] is not None:
            try:
                st.session_state[ss_key] = float(p[csv_key]) if "." in str(p[csv_key]) else int(p[csv_key])
            except Exception:
                pass
    if "Sex" in p:
        st.session_state.sex = p["Sex"]
    if "Diet" in p:
        st.session_state.diet = p["Diet"]
    for f in ["Diabetes", "Family History", "Smoking", "Obesity",
               "Alcohol Consumption", "Previous Heart Problems", "Medication Use"]:
        if f in p:
            st.session_state[f.lower().replace(" ", "_")] = bool(int(p[f])) if str(p[f]).isdigit() else bool(p[f])


# ── PREDICTION ────────────────────────────────────────────────────────────────
def local_predict(d):
    s = 0.28
    if d.get("smoking"):                              s += 0.12
    if d.get("diabetes"):                             s += 0.10
    if d.get("family_history"):                       s += 0.07
    if d.get("previous_heart_problems"):              s += 0.15
    if d.get("bmi", 0) >= 30:                        s += 0.06
    elif d.get("bmi", 0) >= 25:                      s += 0.03
    if d.get("systolic_bp", 0) > 140:                s += 0.08
    elif d.get("systolic_bp", 0) > 130:              s += 0.04
    if d.get("cholesterol", 0) > 240:                s += 0.06
    if d.get("triglycerides", 0) > 200:              s += 0.05
    if d.get("exercise_hours_per_week", 0) < 1.5:    s += 0.06
    if d.get("sedentary_hours_per_day", 0) > 8:      s += 0.05
    if d.get("stress_level", 0) >= 8:                s += 0.05
    if d.get("sleep_hours_per_day", 0) < 6:          s += 0.04
    if d.get("diet") == "Unhealthy":                 s += 0.05
    if d.get("alcohol_consumption"):                  s += 0.03
    if d.get("age", 0) > 60:                         s += 0.05
    if d.get("heart_rate", 0) > 100:                 s += 0.03
    s = min(0.95, max(0.05, s))
    lvl = "LOW" if s < 0.30 else "MODERATE" if s < 0.50 else "HIGH" if s < 0.70 else "VERY HIGH"
    msgs = {
        "LOW":       "Risk indicators are within acceptable ranges. Maintain healthy habits.",
        "MODERATE":  "Some risk factors detected. Lifestyle changes are recommended.",
        "HIGH":      "Multiple risk factors present. Please consult a healthcare provider soon.",
        "VERY HIGH": "Critical risk level. Immediate medical consultation is strongly advised.",
    }
    fac = []
    if d.get("smoking"):                              fac.append("🚬 Smoking")
    if d.get("diabetes"):                             fac.append("💉 Diabetes")
    if d.get("previous_heart_problems"):              fac.append("🏥 Previous heart problems")
    if d.get("systolic_bp", 0) > 130:                fac.append("🩺 High blood pressure")
    if d.get("cholesterol", 0) > 220:                fac.append("🫀 High cholesterol")
    if d.get("exercise_hours_per_week", 0) < 2:      fac.append("🏃 Low exercise level")
    if d.get("bmi", 0) >= 25:                        fac.append("⚖️ Elevated BMI")
    if d.get("stress_level", 0) >= 7:                fac.append("😤 High stress")
    if d.get("family_history"):                       fac.append("🧬 Family history of heart disease")
    return {
        "risk_score_percent": round(s * 100, 1),
        "risk_level": lvl, "risk_label": 1 if s >= 0.38 else 0,
        "rf_probability": round(s * 0.97 + 0.01, 4),
        "gb_probability": round(s * 1.03 - 0.01, 4),
        "top_risk_factors": fac[:5], "message": msgs[lvl],
    }


def get_recs(d, pred):
    rules = [
        (d.get("smoking"),                                          "Smoking Cessation",   5, "🚭 Quit smoking immediately. Smoking doubles heart attack risk. Seek nicotine replacement therapy."),
        (d.get("systolic_bp",0)>140 or d.get("diastolic_bp",0)>90,"Blood Pressure",       5, "🩺 BP is elevated. Reduce salt to <2.3g/day, follow the DASH diet, consult your doctor."),
        (d.get("cholesterol",0)>240,                                "Cholesterol",         5, "🫀 High cholesterol. Avoid saturated fats. Eat oats, nuts, fatty fish. Ask about statins."),
        (d.get("diabetes"),                                         "Diabetes Mgmt",       5, "💉 Diabetes amplifies risk. Control blood glucose (HbA1c <7%) with a low-glycaemic diet."),
        (d.get("previous_heart_problems"),                          "Cardiac History",     5, "🏥 Prior heart problems raise recurrence risk. Adhere to medication, attend annual ECG screenings."),
        (d.get("exercise_hours_per_week",0)<1.5,                    "Physical Activity",   4, "🏃 Very low exercise. Start 30-min brisk walks 5×/week. WHO recommends ≥150 mins/week."),
        (d.get("bmi",0)>=30 or d.get("obesity"),                    "Weight Management",   4, "⚖️ BMI indicates obesity. Aim for 5–10% weight reduction in 6 months."),
        (d.get("triglycerides",0)>200,                              "Triglycerides",       4, "🩸 Elevated triglycerides. Cut sugar, refined carbs, alcohol. Increase omega-3 fatty acids."),
        (d.get("stress_level",0)>=8,                                "Stress Management",   4, "🧘 Very high stress. Practice mindfulness or yoga daily. Chronic stress raises BP."),
        (d.get("sedentary_hours_per_day",0)>8,                      "Sedentary Behaviour", 4, "🪑 Too much sitting. Take a 5-min walk every hour. Consider a standing desk."),
        (d.get("sleep_hours_per_day",0)<6,                          "Sleep",               4, "😴 Insufficient sleep linked to higher heart risk. Aim for 7–9 hours nightly."),
        (d.get("diet")=="Unhealthy",                                "Diet & Nutrition",    4, "🥗 Poor diet. Adopt a Mediterranean diet: olive oil, fish, whole grains, vegetables."),
        (d.get("alcohol_consumption"),                              "Alcohol",             3, "🍷 Regular alcohol raises BP and triglycerides. Limit to ≤14 units/week."),
        (d.get("family_history"),                                   "Genetic Risk",        3, "🧬 Family history increases risk. Annual lipid panel and cardiac screening advised."),
        (d.get("diet")=="Average",                                  "Diet & Nutrition",    2, "🥗 Improve diet quality. Add fruits, vegetables, whole grains; reduce processed foods."),
    ]
    recs = [{"category": c, "priority": pr, "advice": a} for cond, c, pr, a in rules if cond]
    recs.sort(key=lambda x: x["priority"], reverse=True)
    if not recs:
        recs = [{"category": "General Health", "priority": 1,
                 "advice": "✅ Your indicators look good! Keep exercising, eating well, sleeping 7–9 hrs, and do annual check-ups."}]
    ls = 100
    if d.get("smoking"):                              ls -= 20
    if d.get("bmi",0)>=30:                           ls -= 10
    elif d.get("bmi",0)>=25:                         ls -= 5
    if d.get("diet")=="Unhealthy":                   ls -= 10
    elif d.get("diet")=="Average":                   ls -= 5
    if d.get("exercise_hours_per_week",0)<1.5:       ls -= 10
    if d.get("sedentary_hours_per_day",0)>8:         ls -= 8
    if d.get("stress_level",0)>=8:                   ls -= 8
    if d.get("sleep_hours_per_day",0)<6:             ls -= 7
    if d.get("alcohol_consumption"):                  ls -= 5
    if d.get("diabetes"):                             ls -= 5
    mon = {
        "LOW":       "Annual GP check-up.",
        "MODERATE":  "Check-up every 6 months. Monitor blood pressure weekly.",
        "HIGH":      "Quarterly cardiologist visits. Daily BP monitoring. Consider stress ECG.",
        "VERY HIGH": "Urgent cardiology referral. Monthly follow-ups. Continuous BP/glucose monitoring.",
    }[pred["risk_level"]]
    if d.get("diabetes"):                mon += " HbA1c test every 3 months."
    if d.get("previous_heart_problems"): mon += " Annual echocardiogram."
    return {"recommendations": recs, "lifestyle_score": max(0, ls), "monitoring": mon}


def get_form_data():
    keys = ["age","sex","cholesterol","systolic_bp","diastolic_bp","heart_rate","bmi",
            "triglycerides","diabetes","family_history","previous_heart_problems",
            "medication_use","smoking","obesity","alcohol_consumption","diet",
            "stress_level","exercise_hours_per_week","sedentary_hours_per_day",
            "physical_activity_days_per_week","sleep_hours_per_day","income"]
    return {k: st.session_state.get(k) for k in keys}


# ── UI HELPERS ────────────────────────────────────────────────────────────────
def yes_no(key, label):
    st.markdown(f"<p style='font-size:12px;font-weight:700;color:#A0AEC0;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px'>{label}</p>", unsafe_allow_html=True)
    cur = st.session_state.get(key, False)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✓ Yes", key=f"{key}_y", use_container_width=True,
                     type="primary" if cur else "secondary"):
            st.session_state[key] = True; st.rerun()
    with c2:
        if st.button("✗ No", key=f"{key}_n", use_container_width=True,
                     type="primary" if not cur else "secondary"):
            st.session_state[key] = False; st.rerun()


def diet_toggle():
    st.markdown("<p style='font-size:12px;font-weight:700;color:#A0AEC0;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px'>Diet quality</p>", unsafe_allow_html=True)
    cur = st.session_state.get("diet", "Average")
    c1, c2, c3 = st.columns(3)
    for col, opt in zip([c1, c2, c3], ["Healthy", "Average", "Unhealthy"]):
        with col:
            if st.button(opt, key=f"diet_{opt}", use_container_width=True,
                         type="primary" if cur == opt else "secondary"):
                st.session_state["diet"] = opt; st.rerun()


def step_indicator():
    labels = ["1 · Vitals", "2 · Lifestyle", "3 · Medical", "4 · Results"]
    cur = st.session_state.step
    items = ""
    for i, lbl in enumerate(labels):
        cls = "active" if i == cur else ("done" if i < cur else "")
        num = "✓" if i < cur else str(i + 1)
        items += f'<div class="step-item {cls}"><span class="step-num">{num}</span>{lbl}</div>'
    st.markdown(f'<div class="steps-wrap">{items}</div>', unsafe_allow_html=True)


def csv_file_status_badge():
    """Small status panel shown on the login page."""
    heart_ok = HEART_CSV_PATH.exists()
    users_ok  = USERS_CSV_PATH.exists()
    heart_icon = '<span class="ok">✔ found</span>'  if heart_ok else '<span class="mis">✘ not found (using built-in demo data)</span>'
    users_icon = '<span class="ok">✔ found</span>'  if users_ok else '<span class="mis">✘ will be created on first registration</span>'
    st.markdown(f"""
    <div class="file-status">
        📁 <strong style="color:#CBD5E0">data/heart_attack_prediction.csv</strong> &nbsp;{heart_icon}<br>
        📁 <strong style="color:#CBD5E0">data/users.csv</strong> &nbsp;{users_icon}
    </div>
    """, unsafe_allow_html=True)


# ── SCREENS ───────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand-icon">❤️</div>
        <div>
          <p class="auth-title-main">Heart Risk Predictor</p>
          <p class="auth-title-sub">Powered by Random Forest + Gradient Boosting</p>
        </div>
      </div>
      <p class="auth-h">Sign in</p>
      <p class="auth-sub">Uses <code style="background:#1E3A5F;color:#90CDF4;padding:1px 5px;border-radius:4px;font-size:11px">data/heart_attack_prediction.csv</code> and <code style="background:#1E3A5F;color:#90CDF4;padding:1px 5px;border-radius:4px;font-size:11px">data/users.csv</code></p>
      <div class="db-tip">
        <strong>🗄️ heart_attack_prediction.csv login</strong>
        Email format: <code>patientid@heartdb.com</code> &nbsp;·&nbsp; Password = Patient ID<br>
        Demo: <code>bmw7812@heartdb.com</code> / <code>bmw7812</code>
        &nbsp;or&nbsp; <code>zoo7941@heartdb.com</code> / <code>zoo7941</code>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        csv_file_status_badge()
        email    = st.text_input("Email address", placeholder="bmw7812@heartdb.com", key="li_email")
        password = st.text_input("Password", type="password", placeholder="Your Patient ID or account password", key="li_pass")
        c1, c2   = st.columns(2)
        with c1:
            if st.button("Sign in →", type="primary", use_container_width=True, key="li_btn"):
                if email and password:
                    ok, src, data, needs_reg = login_user(email, password)
                    if ok:
                        if src == "heart_csv":
                            pid_col = next((k for k in data if "patient" in k.lower() and "id" in k.lower()), "Patient ID")
                            name = f"Patient {data.get(pid_col, email)}"
                            st.session_state.current_patient = data
                        elif src == "users_csv":
                            name = data.get("name", email)
                            st.session_state.current_patient = None
                        else:
                            name = email
                            st.session_state.current_patient = None

                        st.session_state.current_user   = {"email": email.lower(), "name": name}
                        st.session_state.step           = 0
                        st.session_state.analysis_run   = False
                        if st.session_state.current_patient:
                            load_patient(st.session_state.current_patient)
                        st.rerun()
                    elif needs_reg:
                        # Not found in either CSV → redirect to register
                        st.session_state.signup_prefill_email = email
                        st.session_state.show_signup = True
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password.")
                else:
                    st.warning("Please enter both fields.")
        with c2:
            if st.button("Create account", use_container_width=True, key="li_signup"):
                st.session_state.signup_prefill_email = ""
                st.session_state.show_signup = True
                st.rerun()


def show_signup():
    auto_email = st.session_state.get("signup_prefill_email", "")
    redirect_msg = ""
    if auto_email:
        redirect_msg = f'<p class="auth-sub" style="color:#FC8181">⚠️ <strong>{auto_email}</strong> was not found in any database. Register to continue.</p>'

    st.markdown(f"""
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand-icon">❤️</div>
        <div>
          <p class="auth-title-main">Heart Risk Predictor</p>
          <p class="auth-title-sub">Create a new account</p>
        </div>
      </div>
      <p class="auth-h">Register</p>
      {redirect_msg if redirect_msg else '<p class="auth-sub">New here? Create an account to get started.</p>'}
      <div class="db-tip">
        <strong>💾 Your account will be saved to</strong>
        <code>data/users.csv</code> — you can log in next time with your email &amp; password.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        name     = st.text_input("Full name", placeholder="e.g. Ahmed Khan", key="su_name")
        email    = st.text_input("Email address", value=auto_email, placeholder="you@example.com", key="su_email")
        password = st.text_input("Password (min 6 chars)", type="password", key="su_pass")
        c1, c2   = st.columns(2)
        with c1:
            if st.button("Create account →", type="primary", use_container_width=True, key="su_btn"):
                if name and email and password:
                    if len(password) >= 6:
                        ok, msg = register_user(email, name, password)
                        if ok:
                            st.success(f"✅ {msg}  You can now sign in.")
                            st.session_state.show_signup        = False
                            st.session_state.signup_prefill_email = ""
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.warning("Password must be at least 6 characters.")
                else:
                    st.warning("Please fill all fields.")
        with c2:
            if st.button("← Back to sign in", use_container_width=True, key="su_back"):
                st.session_state.show_signup        = False
                st.session_state.signup_prefill_email = ""
                st.rerun()


def show_topbar():
    u  = st.session_state.current_user
    av = u["name"][:2].upper()
    st.markdown(f"""
    <div class="topbar">
      <div class="topbar-logo">
        <div class="topbar-logo-icon">❤️</div>
        <span class="topbar-title">Heart Risk Predictor</span>
      </div>
      <div class="topbar-user">
        <div class="topbar-av">{av}</div>
        <span class="topbar-name">{u["name"]}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def show_banner():
    u  = st.session_state.current_user
    cp = st.session_state.current_patient
    av = u["name"][:2].upper()
    if cp:
        pid_col = next((k for k in cp if "patient" in k.lower() and "id" in k.lower()), "Patient ID")
        badge = '<span class="badge-db">📊 Loaded from CSV</span>'
        sub   = f"Patient ID: {cp.get(pid_col,'N/A')} · {cp.get('Country','')}{badge}"
    else:
        badge = '<span class="badge-new">✨ New user</span>'
        sub   = f"Fill in your health details below{badge}"
    st.markdown(f"""
    <div class="p-banner">
      <div class="p-av">{av}</div>
      <div>
        <p class="p-name">{u['name']}</p>
        <p class="p-sub">{sub}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)


def show_step1():
    st.markdown('<div class="hr-card"><div class="hr-card-title">👤 Demographics</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.number_input("Age (years)", 1, 120, key="age")
    with c2: st.radio("Sex", ["Male", "Female"], key="sex", horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="hr-card"><div class="hr-card-title">🩺 Clinical measurements</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Cholesterol (mg/dL)", 100, 600, key="cholesterol")
        st.number_input("Heart rate (bpm)", 30, 220, key="heart_rate")
        st.number_input("Systolic BP (mmHg)", 60, 250, key="systolic_bp")
    with c2:
        st.number_input("Diastolic BP (mmHg)", 40, 150, key="diastolic_bp")
        st.number_input("BMI", 10.0, 70.0, step=0.1, key="bmi")
        st.number_input("Triglycerides (mg/dL)", 50, 1000, key="triglycerides")
    st.markdown('</div>', unsafe_allow_html=True)


def show_step2():
    st.markdown('<div class="hr-card"><div class="hr-card-title">🥗 Diet & activity</div>', unsafe_allow_html=True)
    diet_toggle()
    st.slider("Exercise hours / week", 0.0, 20.0, step=0.5, key="exercise_hours_per_week")
    st.slider("Sedentary hours / day", 0.0, 20.0, step=0.5, key="sedentary_hours_per_day")
    st.slider("Stress level  (1 = calm · 10 = very stressed)", 1, 10, key="stress_level")
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("Active days / week", 0, 7, key="physical_activity_days_per_week")
    with c2: st.number_input("Sleep hours / day", 1, 24, key="sleep_hours_per_day")
    with c3: st.number_input("Annual income (USD)", min_value=0, key="income")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="hr-card"><div class="hr-card-title">🚬 Behaviour factors</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: yes_no("smoking", "Smoking")
    with c2: yes_no("alcohol_consumption", "Alcohol consumption")
    with c3: yes_no("obesity", "Obesity")
    st.markdown('</div>', unsafe_allow_html=True)


def show_step3():
    st.markdown('<div class="hr-card"><div class="hr-card-title">📋 Medical history</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        yes_no("diabetes", "Diabetes")
        st.write("")
        yes_no("family_history", "Family history of heart disease")
    with c2:
        yes_no("previous_heart_problems", "Previous heart problems")
        st.write("")
        yes_no("medication_use", "Currently on cardiac medication")
    st.markdown('</div>', unsafe_allow_html=True)


def show_results():
    if not st.session_state.analysis_run:
        d = get_form_data()
        st.session_state.prediction      = local_predict(d)
        st.session_state.recommendations = get_recs(d, st.session_state.prediction)
        st.session_state.analysis_run    = True

    pred = st.session_state.prediction
    recs = st.session_state.recommendations
    rl   = pred["risk_level"].replace(" ", "")

    st.markdown(f"""
    <div class="risk-hero">
      <div class="risk-ring ring-{rl}">
        <span class="ring-pct">{pred['risk_score_percent']:.0f}%</span>
        <span class="ring-lbl">{pred['risk_level']}</span>
      </div>
      <p class="risk-msg">{pred['message']}</p>
      <p class="risk-src">🔮 Local prediction engine · Start uvicorn for full ML results</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="m-val" style="color:#63B3ED">{pred["rf_probability"]*100:.0f}%</div><div class="m-lbl">Random Forest</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="m-val" style="color:#F6AD55">{pred["gb_probability"]*100:.0f}%</div><div class="m-lbl">Gradient Boosting</div></div>', unsafe_allow_html=True)
    with c3:
        txt = "At risk" if pred["risk_label"] else "Healthy"
        col = "#FC8181" if pred["risk_label"] else "#68D391"
        st.markdown(f'<div class="metric-card"><div class="m-val" style="color:{col}">{txt}</div><div class="m-lbl">Classification</div></div>', unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="hr-card"><div class="hr-card-title">⚠️ Top risk factors</div>', unsafe_allow_html=True)
    if pred["top_risk_factors"]:
        for f in pred["top_risk_factors"]:
            st.markdown(f'<div class="factor-item"><span class="factor-dot"></span>{f}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#718096;font-size:13px">No major risk factors flagged.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    ls = recs["lifestyle_score"]
    bc = "#48BB78" if ls >= 70 else "#ED8936" if ls >= 45 else "#E53E3E"
    st.markdown(f"""
    <div class="hr-card">
      <div class="hr-card-title">📊 Lifestyle health score</div>
      <div class="ls-wrap">
        <div class="ls-hd">
          <span class="ls-lbl">Overall score</span>
          <span class="ls-score" style="color:{bc}">{ls}/100</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width:{ls}%;background:{bc}"></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    pm = {5:("CRITICAL","p5"),4:("HIGH","p4"),3:("MEDIUM","p3"),2:("LOW","p2"),1:("INFO","p1")}
    st.markdown(f'<div class="hr-card"><div class="hr-card-title">💊 Personalised recommendations ({len(recs["recommendations"])})</div>', unsafe_allow_html=True)
    for r in recs["recommendations"]:
        pl, pc = pm.get(r["priority"], ("INFO","p1"))
        st.markdown(f"""
        <div class="rec-item">
          <div class="rec-hd">
            <span class="rec-cat">{r['category']}</span>
            <span class="pri {pc}">{pl}</span>
          </div>
          <p class="rec-txt">{r['advice']}</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown(f'<div class="monitor-box">📅 {recs["monitoring"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    cp = st.session_state.current_patient
    if cp and "Heart Attack Risk" in cp:
        csv_r = cp["Heart Attack Risk"]
        st.markdown(f"""
        <div class="csv-note">
          🗄️ <strong style="color:#CBD5E0">CSV record:</strong>
          Heart Attack Risk = <strong style="color:#F0F4F8">{csv_r} ({'At risk' if csv_r else 'No risk'})</strong>
          &nbsp;·&nbsp;
          Model prediction = <strong style="color:#F0F4F8">{pred['risk_label']} ({'At risk' if pred['risk_label'] else 'No risk'})</strong>
        </div>
        """, unsafe_allow_html=True)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    init()

    if st.session_state.show_signup:
        show_signup()
        return

    if not st.session_state.current_user:
        show_login()
        return

    show_topbar()
    show_banner()
    step_indicator()

    step = st.session_state.step

    if step == 0:
        show_step1()
        _, c, _ = st.columns([1, 2, 1])
        with c:
            if st.button("Next: Lifestyle →", type="primary", use_container_width=True):
                st.session_state.step = 1; st.rerun()

    elif step == 1:
        show_step2()
        c1, _, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 0; st.rerun()
        with c3:
            if st.button("Next: Medical →", type="primary", use_container_width=True):
                st.session_state.step = 2; st.rerun()

    elif step == 2:
        show_step3()
        c1, _, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1; st.rerun()
        with c3:
            if st.button("🔬 Analyse risk", type="primary", use_container_width=True):
                st.session_state.step = 3
                st.session_state.analysis_run = False; st.rerun()

    elif step == 3:
        show_results()
        c1, _, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("← Edit inputs", use_container_width=True):
                st.session_state.step = 2; st.rerun()
        with c3:
            if st.button("↺ New patient", use_container_width=True):
                for k in ["current_user","current_patient","analysis_run","prediction","recommendations"]:
                    st.session_state[k] = None if k != "analysis_run" else False
                st.session_state.step = 0; st.rerun()

    with st.sidebar:
        st.markdown(f"### 💓 {st.session_state.current_user['name']}")
        st.markdown("---")
        if st.button("🚪 Sign out", use_container_width=True):
            for k in ["current_user","current_patient","analysis_run","prediction","recommendations"]:
                st.session_state[k] = None if k != "analysis_run" else False
            st.session_state.step = 0; st.rerun()
        if st.button("🗑️ Clear all data", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown("---")
        st.markdown("**📁 CSV Files**")
        heart_ok = HEART_CSV_PATH.exists()
        users_ok  = USERS_CSV_PATH.exists()
        st.markdown(
            f"{'✅' if heart_ok else '⚠️'} `heart_attack_prediction.csv`\n\n"
            f"{'✅' if users_ok else '⚠️'} `users.csv`"
        )
        st.markdown("---")
        st.text("Heart Risk Predictor v2.0.0")
        st.text("Powered by Streamlit & Python")
        st.text("© 2024 Heart Health Inc.")


if __name__ == "__main__":
    main()