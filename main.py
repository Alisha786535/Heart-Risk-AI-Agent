"""
Heart Attack Risk Prediction API
=================================
FastAPI application — serves the frontend AND the REST API.

Start:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
Then open:  http://localhost:8000           ← Beautiful UI
            http://localhost:8000/docs      ← Swagger
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from routers.predict import router as predict_router
from routers.recommendations import router as recs_router
from routers.stats import router as stats_router

# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="❤️ Heart Attack Risk Prediction API",
    description="""
## Heart Attack Risk Prediction System

ML-powered REST API + beautiful frontend UI.

### Models
| Model | Role |
|---|---|
| **Random Forest (200 trees)** | Primary classifier |
| **Gradient Boosting (300 trees)** | Secondary classifier |
| **Soft Ensemble** | Final probability score |

### Endpoints
- `POST /predict` – Risk prediction
- `POST /recommendations` – Personalised health advice
- `GET  /stats` – Dataset statistics
- `GET  /health` – Health check
- `GET  /` – Serves the frontend UI
""",
    version="1.0.0",
)

# ── CORS (allow browser calls from any origin) ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(predict_router,  tags=["🔬 Prediction"])
app.include_router(recs_router,     tags=["💊 Recommendations"])
app.include_router(stats_router,    tags=["📊 Statistics"])

# ── Serve frontend ─────────────────────────────────────────────
FRONTEND = Path(__file__).parent / "index.html"

@app.get("/ui", tags=["🖥️ Frontend"], include_in_schema=False)
@app.get("/",   tags=["🖥️ Frontend"], include_in_schema=False)
def serve_ui():
    """Serve the patient-facing UI."""
    if FRONTEND.exists():
        return FileResponse(FRONTEND, media_type="text/html")
    return {"message": "Frontend not found. Place heart_risk_app.html at static/index.html",
            "docs": "/docs"}

# ── Static files (CSS/JS/assets if needed) ─────────────────────
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ── Health ─────────────────────────────────────────────────────
@app.get("/health", tags=["⚙️ System"])
def health_check():
    models_dir = Path("models")
    return {
        "status": "healthy",
        "models_loaded": [f.name for f in models_dir.glob("*.pkl")],
        "frontend": FRONTEND.exists(),
        "api_version": "1.0.0",
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
