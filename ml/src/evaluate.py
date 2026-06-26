"""
US-13 — Younes : évaluation standalone du modèle (utile en CI ou en comparaison de runs MLflow).

Usage :
    python ml/src/evaluate.py --model-path ml/models/svd_model.joblib
"""
import argparse
from pathlib import Path

import joblib
import numpy as np

DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "svd_model.joblib"


def evaluate_saved_model(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    from build_matrix import build_user_item_matrix

    bundle = joblib.load(model_path)
    user_factors = bundle["user_factors"]
    item_factors = bundle["item_factors"]

    matrix, _, _ = build_user_item_matrix()
    coo = matrix.tocoo()

    predictions = user_factors @ item_factors
    y_true = coo.data
    y_pred = predictions[coo.row, coo.col]

    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_true - y_pred)))

    print(f"[evaluate] RMSE global = {rmse:.4f}")
    print(f"[evaluate] MAE global  = {mae:.4f}")

    return {"rmse": rmse, "mae": mae}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Évaluation d'un modèle sauvegardé")
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH))
    args = parser.parse_args()
    evaluate_saved_model(Path(args.model_path))
