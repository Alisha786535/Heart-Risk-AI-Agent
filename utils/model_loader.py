"""Load and cache ML models at startup."""

import joblib
from pathlib import Path
from functools import lru_cache

MODELS_DIR = Path(__file__).parent.parent / "models"


@lru_cache(maxsize=1)
def get_models():
    """Load all model artifacts (cached after first call)."""
    return {
        "rf":           joblib.load(MODELS_DIR / "rf_model.pkl"),
        "gb":           joblib.load(MODELS_DIR / "gb_model.pkl"),
        "scaler":       joblib.load(MODELS_DIR / "scaler.pkl"),
        "le_sex":       joblib.load(MODELS_DIR / "le_sex.pkl"),
        "le_diet":      joblib.load(MODELS_DIR / "le_diet.pkl"),
        "feature_names": joblib.load(MODELS_DIR / "feature_names.pkl"),
    }
