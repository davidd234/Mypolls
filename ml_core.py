from __future__ import annotations
import json
from pathlib import Path
from datetime import date
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
import joblib

# ============================
# DETECTARE ROOT (ca la calibration_agent)
# ============================
THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE

while ROOT != ROOT.parent:
    if (ROOT / "data").exists():
        break
    ROOT = ROOT.parent

if not (ROOT / "data").exists():
    raise FileNotFoundError("❌ Nu am putut găsi folderul 'data' în niciun director părinte.")

DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

POLLS_PATH = DATA_DIR / "polls_buc.json"
RESULTS_PATH = DATA_DIR / "results_buc.json"

MODEL_PATH = MODEL_DIR / "pmb_2024_rf.pkl"

ELECTION_DATE = date(2024, 6, 9)  # data oficială PMB 2024


# ============================
# UTILITĂȚI DE ÎNCĂRCARE
# ============================

def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_polls_and_results():
    polls = load_json(POLLS_PATH, [])
    results = load_json(RESULTS_PATH, {})

    if not polls:
        raise ValueError("❌ polls_buc.json este gol sau inexistent.")
    if not results:
        raise ValueError("❌ results_buc.json este gol sau inexistent.")

    return polls, results


# ============================
# DATASET ML
# ============================

def build_dataset(polls: List[Dict[str, Any]], final_results: Dict[str, float]) -> pd.DataFrame:
    """
    Fiecare rând = (sondaj X, candidat Y)
    Features:
      - institut (categorical)
      - metoda   (categorical)
      - candidat (categorical)
      - zile_pana_la_alegeri (numeric)
      - esantion (numeric)
      - procent_brut (numeric)
      - marja_eroare (numeric)

    Target:
      - procent_final (din results_buc.json)
    """

    rows = []

    for poll in polls:
        try:
            poll_date = date.fromisoformat(poll["data"])
        except Exception:
            # ignorăm sondajele cu dată coruptă
            continue

        days_to_election = (ELECTION_DATE - poll_date).days
        procentaje = poll.get("procentaje", {}) or {}

        for candidat, rezult_final in final_results.items():
            if candidat not in procentaje:
                # sondajul nu îl are pe candidatul ăsta
                continue

            rows.append({
                "institut": poll.get("institut", "necunoscut"),
                "metoda": poll.get("metoda", "necunoscut"),
                "candidat": candidat,
                "zile_pana_la_alegeri": days_to_election,
                "esantion": poll.get("esantion", 0),
                "procent_brut": procentaje[candidat],
                "marja_eroare": poll.get("marja_eroare", 3.0),
                "procent_final": rezult_final,
            })

    if not rows:
        raise ValueError("❌ Nu am putut construi niciun rând de training (rows=0).")

    df = pd.DataFrame(rows)
    return df


# ============================
# TRAIN MODEL
# ============================

def train_model(verbose: bool = True) -> Pipeline:
    polls, final_results = load_polls_and_results()
    df = build_dataset(polls, final_results)

    if verbose:
        print("📊 Dataset ML construit cu", len(df), "rânduri.")

    feature_cols = [
        "institut",
        "metoda",
        "candidat",
        "zile_pana_la_alegeri",
        "esantion",
        "procent_brut",
        "marja_eroare",
    ]
    target_col = "procent_final"

    X = df[feature_cols]
    y = df[target_col]

    categorical_features = ["institut", "metoda", "candidat"]
    numeric_features = ["zile_pana_la_alegeri", "esantion", "procent_brut", "marja_eroare"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("num", StandardScaler(), numeric_features),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1
    )

    pipe = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )

    if verbose:
        print("🧠 Antrenez modelul RandomForest...")

    pipe.fit(X, y)

    joblib.dump(pipe, MODEL_PATH)
    if verbose:
        print(f"✔ Model salvat în {MODEL_PATH}")

    return pipe


def load_model() -> Pipeline:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"❌ Modelul nu există ({MODEL_PATH}). Rulează mai întâi train_model()."
        )
    return joblib.load(MODEL_PATH)


# ============================
# PREDICȚIE AGREGATĂ
# ============================

def predict_aggregated(verbose: bool = True) -> Dict[str, float]:
    """
    Generează predicții finale pentru fiecare candidat:
      - ia toate sondajele din polls_buc.json
      - pentru fiecare (sondaj, candidat) generează o predicție a procentului final
      - agregă predicțiile pe candidat cu o medie ponderată (greutate = esantion)
    """

    polls, final_results = load_polls_and_results()
    model = load_model()

    # extragem lista de candidați din results_buc.json
    candidati = list(final_results.keys())

    rows_pred = []
    for poll in polls:
        try:
            poll_date = date.fromisoformat(poll["data"])
        except Exception:
            continue

        days_to_election = (ELECTION_DATE - poll_date).days
        procentaje = poll.get("procentaje", {}) or {}

        for candidat in candidati:
            if candidat not in procentaje:
                continue

            rows_pred.append({
                "institut": poll.get("institut", "necunoscut"),
                "metoda": poll.get("metoda", "necunoscut"),
                "candidat": candidat,
                "zile_pana_la_alegeri": days_to_election,
                "esantion": poll.get("esantion", 0),
                "procent_brut": procentaje[candidat],
                "marja_eroare": poll.get("marja_eroare", 3.0),
            })

    if not rows_pred:
        raise ValueError("❌ Nu am găsit sondaje valide pentru predicție.")

    df_pred = pd.DataFrame(rows_pred)

    feature_cols = [
        "institut",
        "metoda",
        "candidat",
        "zile_pana_la_alegeri",
        "esantion",
        "procent_brut",
        "marja_eroare",
    ]
    X_pred = df_pred[feature_cols]

    y_pred = model.predict(X_pred)
    df_pred["pred_procent_final"] = y_pred

    # agregăm pe candidat cu medie ponderată (greutate = esantion)
    rezultate: Dict[str, Dict[str, float]] = {}
    for _, row in df_pred.iterrows():
        cand = row["candidat"]
        w = max(float(row["esantion"]), 1.0)
        val = float(row["pred_procent_final"])

        if cand not in rezultate:
            rezultate[cand] = {"num": 0.0, "den": 0.0}

        rezultate[cand]["num"] += val * w
        rezultate[cand]["den"] += w

    aggregated: Dict[str, float] = {}
    for cand, agg in rezultate.items():
        if agg["den"] == 0:
            aggregated[cand] = None
        else:
            aggregated[cand] = agg["num"] / agg["den"]

    if verbose:
        print("\n===== PREDICȚII ML AGREGATE =====")
        for cand, val in sorted(aggregated.items(), key=lambda x: x[1] or 0, reverse=True):
            if val is None:
                print(f"{cand}: N/A")
            else:
                print(f"{cand}: {val:.2f}%")

    return aggregated
