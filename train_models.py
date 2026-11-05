"""
train_models.py
===============
Re-trains and saves all ML model artefacts.

Run:  python train_models.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
from pathlib import Path

DATA_PATH   = Path("data/heart_attack_prediction_dataset.csv")
MODELS_DIR  = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("Heart Attack Risk – Model Training Pipeline")
print("=" * 60)

# ── 1. Load & preprocess ────────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"\n✓ Loaded {len(df):,} records with {df.shape[1]} features.")
print(f"  Class balance: {df['Heart Attack Risk'].value_counts().to_dict()}")

# Parse Blood Pressure
df[["SystolicBP", "DiastolicBP"]] = (
    df["Blood Pressure"].str.split("/", expand=True).astype(int)
)
df.drop(columns=["Blood Pressure", "Patient ID", "Country", "Continent", "Hemisphere"],
        inplace=True)

le_sex  = LabelEncoder()
le_diet = LabelEncoder()
df["Sex"]  = le_sex.fit_transform(df["Sex"])
df["Diet"] = le_diet.fit_transform(df["Diet"])

X = df.drop(columns=["Heart Attack Risk"])
y = df["Heart Attack Risk"]

# ── 2. Train / test split ────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
# stratify=y ensures the same class distribution in train/test sets without any biases. This is crucial for imbalanced datasets to prevent skewed performance metrics.
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)
print(f"\n✓ Train: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── 3. Random Forest ─────────────────────────────────────────
print("\n[1/2] Training Random Forest …")
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=4,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
rf.fit(X_train_sc, y_train)

rf_prob  = rf.predict_proba(X_test_sc)[:, 1]
rf_pred  = (rf_prob >= 0.38).astype(int)
rf_auc   = roc_auc_score(y_test, rf_prob)
print(f"  ROC-AUC: {rf_auc:.4f}")
print(classification_report(y_test, rf_pred))

# ── 4. Gradient Boosting ─────────────────────────────────────
print("[2/2] Training Gradient Boosting …")
gb = GradientBoostingClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=5,
    min_samples_leaf=4,
    random_state=42,
)
gb.fit(X_train_sc, y_train)

gb_prob  = gb.predict_proba(X_test_sc)[:, 1]
gb_pred  = (gb_prob >= 0.38).astype(int)
gb_auc   = roc_auc_score(y_test, gb_prob)
print(f"  ROC-AUC: {gb_auc:.4f}")
print(classification_report(y_test, gb_pred))

# ── 5. Ensemble evaluation ───────────────────────────────────
ens_prob = 0.55 * rf_prob + 0.45 * gb_prob
ens_pred = (ens_prob >= 0.38).astype(int)
ens_auc  = roc_auc_score(y_test, ens_prob)
print(f"\nEnsemble ROC-AUC: {ens_auc:.4f}")
print(classification_report(y_test, ens_pred))

# ── 6. Feature importances ───────────────────────────────────
fi = pd.Series(rf.feature_importances_, index=X.columns)
print("\nTop-10 Feature Importances (RF):")
print(fi.sort_values(ascending=False).head(10).to_string())

# ── 7. Save artefacts ────────────────────────────────────────
joblib.dump(rf,             MODELS_DIR / "rf_model.pkl")
joblib.dump(gb,             MODELS_DIR / "gb_model.pkl")
joblib.dump(scaler,         MODELS_DIR / "scaler.pkl")
joblib.dump(le_sex,         MODELS_DIR / "le_sex.pkl")
joblib.dump(le_diet,        MODELS_DIR / "le_diet.pkl")
joblib.dump(list(X.columns),MODELS_DIR / "feature_names.pkl")

print("\n✅ All model artefacts saved to ./models/")
print("   rf_model.pkl | gb_model.pkl | scaler.pkl | le_sex.pkl | le_diet.pkl")