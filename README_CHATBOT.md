# CardioGuide – chat assistant add-on

## Run
```bash
pip install -r requirements.txt
python train_models.py            # once (models/*.pkl are gitignored)
uvicorn main:app --reload         # API  → http://localhost:8000/docs
streamlit run app.py              # full app: login → risk check → 🫀 Assistant tab (single process)
streamlit run chat_app.py         # chat-only page (optional)
pytest                            # 22 tests
```
Default `LLM_PROVIDER=offline` needs no internet or API key. For a smarter assistant copy `.env.example`
to `.env` and point `openai_compat` at a local Ollama model or any OpenAI-compatible host.

## How it works
`user text → safety check (regex, no LLM) → LLM + tools → deterministic alerts/disclaimers → reply`
All numbers come from tools (`chatbot/tools.py`), never from the LLM.

## Sensors
`POST /assistant/readings {user_id, kind: bp|glucose|hr, value1, value2, context, source}`.
Manual entry works now; a BLE cuff/glucometer gateway or ESP32 only needs to POST here.
Use validated medical devices for BP and glucose; DIY sensors are not accurate enough.

## Accounts (app.py)
- Passwords: salted scrypt (stdlib), min 8 chars, 5 failed logins → 15-minute lock, one generic error message.
- Accounts live in SQLite (`data/app.db`). Old `data/users.csv` accounts are upgraded automatically on their next
  successful login; after that **delete users.csv** and purge it from git history.
- The Patient-ID-as-password login is gone. Use the "Try a demo patient" button (synthetic data, per-session id).
- All user-provided text shown via `unsafe_allow_html` is HTML-escaped.
- The app now uses the real RF+GB models and the shared rule engine (no more hand-written heuristic).
- Streamlit runs the assistant in-process. Set `API_URL` (+ `API_KEY`) only if you want it to call the FastAPI server instead.
- On hosts with ephemeral disks (e.g. Streamlit Community Cloud) SQLite data is lost on restart; use a persistent volume or a hosted DB.

## Before going public
If you expose the FastAPI `/assistant` endpoints, replace plain `user_id` with real tokens (JWT/sessions) and set `API_KEY`; add rate limiting,
retrain on real data, and have clinicians review `core/rules.py`, `core/safety.py` and `data/foods.csv`.
