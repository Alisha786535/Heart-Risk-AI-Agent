"""
Heart Risk AI Agent – FastAPI entry point (single app).

Run:   uvicorn main:app --reload --host 0.0.0.0 --port 8000
Docs:  http://localhost:8000/docs
UI:    streamlit run chat_app.py
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.model_loader import get_models
from routers.predict import router as predict_router
from routers.recommendations import router as recs_router
from routers.stats import router as stats_router
from routers.assistant import router as assistant_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_models()          # fail fast at boot if artefacts are missing/corrupt
    yield


app = FastAPI(
    title="❤️ Heart Risk AI Agent",
    description="Demo heart-risk model, personalised recommendations, diet charts and a safety-aware "
                "chat assistant. **Educational demo – not medical advice. The model is trained on synthetic data.**",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")],
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(predict_router, tags=["🔬 Prediction"])
app.include_router(recs_router, tags=["💊 Recommendations"])
app.include_router(stats_router, tags=["📊 Statistics"])
app.include_router(assistant_router)


@app.get("/", include_in_schema=False)
def root():
    return {"app": "Heart Risk AI Agent", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["⚙️ System"])
def health():
    models_dir = Path(__file__).parent / "models"
    return {"status": "healthy", "models_loaded": sorted(f.name for f in models_dir.glob("*.pkl")),
            "llm_provider": os.getenv("LLM_PROVIDER", "offline"), "api_version": app.version}
