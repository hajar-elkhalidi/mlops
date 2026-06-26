"""
Entraînement du modèle de recommandation : KNN item-based (filtrage collaboratif).
Tracking MLflow (paramètres, métriques, artefact modèle).

Principe (volontairement simple pour une soutenance universitaire) :
- Chaque film est représenté par son vecteur de notes (une ligne de la matrice
  item-users, c'est-à-dire la transposée de la matrice user-item).
- `NearestNeighbors` (Scikit-Learn) calcule, pour chaque film, ses k films les
  plus proches selon la similarité cosinus des profils de notation.
- Pour recommander des films à un utilisateur, on regarde les films qu'il a
  déjà bien notés, puis on propose leurs plus proches voisins.

Usage :
    python ml/src/train.py --n-neighbors 10 --test-size 0.2
"""
import argparse
import json
import os
import sys
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors

sys.path.append(str(Path(__file__).parent))
from build_matrix import build_user_item_matrix  # noqa: E402

# En Docker Compose, le serveur MLflow est joignable via le nom de service "mlflow".
# En local (hors conteneur), on retombe sur localhost:5000 (cf. `make mlflow-ui`).
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_REQUEST_TIMEOUT_SECONDS = int(os.getenv("MLFLOW_REQUEST_TIMEOUT_SECONDS", "5"))
MLFLOW_MAX_RETRIES = int(os.getenv("MLFLOW_MAX_RETRIES", "1"))
EXPERIMENT_NAME = "movielens-recommender"
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "knn_model.joblib"
METRICS_PATH = Path(__file__).parent.parent / "metrics.json"


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    return {"rmse": rmse, "mae": mae}


def _predict_rating(item_idx: int, user_row: np.ndarray, neighbor_indices: np.ndarray,
                     neighbor_distances: np.ndarray) -> float:
    """
    Prédit la note qu'un utilisateur donnerait à un film, comme la moyenne
    pondérée (par similarité) des notes qu'il a données aux films voisins.
    """
    similarities = 1 - neighbor_distances  # distance cosinus -> similarité
    rated_mask = user_row[neighbor_indices] > 0
    if not rated_mask.any():
        return 0.0
    weights = similarities[rated_mask]
    ratings = user_row[neighbor_indices][rated_mask]
    if weights.sum() == 0:
        return float(np.mean(ratings))
    return float(np.average(ratings, weights=weights))


def precision_at_k(matrix_true: csr_matrix, predictions: np.ndarray, k: int = 10) -> float:
    """Precision@K simplifiée : proportion des top-K prédits réellement notés >= 4."""
    precisions = []
    matrix_true_dense = matrix_true.toarray()
    for u in range(matrix_true.shape[0]):
        true_row = matrix_true_dense[u]
        rated_idx = np.where(true_row > 0)[0]
        if len(rated_idx) == 0:
            continue
        pred_row = predictions[u]
        top_k_idx = np.argsort(pred_row)[::-1][:k]
        relevant = sum(1 for idx in top_k_idx if idx in rated_idx and true_row[idx] >= 4.0)
        precisions.append(relevant / k)
    return float(np.mean(precisions)) if precisions else 0.0


def train_model(n_neighbors: int = 10, test_size: float = 0.2, random_state: int = 42) -> dict:
    matrix, user_id_to_idx, movie_id_to_idx = build_user_item_matrix()

    # Split simple par notes (train/test sur les interactions non-nulles)
    coo = matrix.tocoo()
    rows, cols, data = coo.row, coo.col, coo.data
    idx_train, idx_test = train_test_split(
        np.arange(len(data)), test_size=test_size, random_state=random_state
    )

    train_matrix = csr_matrix(
        (data[idx_train], (rows[idx_train], cols[idx_train])), shape=matrix.shape
    )
    item_matrix = train_matrix.T.tocsr()  # KNN item-based : une ligne = un film

    try:
        os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = str(MLFLOW_REQUEST_TIMEOUT_SECONDS)
        os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = str(MLFLOW_MAX_RETRIES)
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(EXPERIMENT_NAME)
        mlflow_active = True
    except Exception:
        mlflow_active = False

    run_ctx = mlflow.start_run() if mlflow_active else _NullContext()

    with run_ctx:
        if mlflow_active:
            mlflow.log_param("model_type", "KNN (item-based, cosine)")
            mlflow.log_param("n_neighbors", n_neighbors)
            mlflow.log_param("test_size", test_size)
            mlflow.log_param("random_state", random_state)
            mlflow.log_param("n_users", matrix.shape[0])
            mlflow.log_param("n_movies", matrix.shape[1])

        # k+1 car le voisin le plus proche d'un film est toujours lui-même
        model = NearestNeighbors(n_neighbors=n_neighbors + 1, metric="cosine", algorithm="brute")
        model.fit(item_matrix)

        distances, indices = model.kneighbors(item_matrix)
        # On retire la première colonne (le film lui-même, distance = 0)
        distances, indices = distances[:, 1:], indices[:, 1:]

        train_matrix_dense = train_matrix.toarray()
        predictions = np.zeros(matrix.shape)
        for item_idx in range(item_matrix.shape[0]):
            neighbor_idx = indices[item_idx]
            neighbor_dist = distances[item_idx]
            for user_idx in range(matrix.shape[0]):
                predictions[user_idx, item_idx] = _predict_rating(
                    item_idx, train_matrix_dense[user_idx], neighbor_idx, neighbor_dist
                )

        y_true = data[idx_test]
        y_pred = predictions[rows[idx_test], cols[idx_test]]
        metrics = evaluate(y_true, y_pred)

        test_matrix = csr_matrix(
            (data[idx_test], (rows[idx_test], cols[idx_test])), shape=matrix.shape
        )
        metrics["precision_at_10"] = precision_at_k(test_matrix, predictions, k=10)

        print(f"[train] Modèle KNN (item-based, k={n_neighbors}) entraîné.")
        print(f"[train] RMSE={metrics['rmse']:.4f}  MAE={metrics['mae']:.4f}  "
              f"Precision@10={metrics['precision_at_10']:.4f}")

        if mlflow_active:
            mlflow.log_metric("rmse", metrics["rmse"])
            mlflow.log_metric("mae", metrics["mae"])
            mlflow.log_metric("precision_at_10", metrics["precision_at_10"])
            mlflow.sklearn.log_model(
                model,
                artifact_path="model",
                registered_model_name="movielens-recommender",
            )

        # Sauvegarde locale (utilisée en fallback par l'API si MLflow indisponible)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": model,
                "item_matrix": item_matrix,
                "neighbor_indices": indices,
                "neighbor_distances": distances,
                "user_id_to_idx": user_id_to_idx,
                "movie_id_to_idx": movie_id_to_idx,
            },
            MODEL_PATH,
        )
        print(f"[train] Modèle sauvegardé localement : {MODEL_PATH}")

        # Métriques exportées en JSON pour DVC (`dvc metrics show` / `dvc.yaml`)
        with open(METRICS_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"[train] Métriques exportées pour DVC : {METRICS_PATH}")

    return metrics


class _NullContext:
    """Context manager neutre utilisé si MLflow n'est pas disponible (ex: CI sans serveur)."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _load_params() -> dict:
    """
    Lit params.yaml à la racine du projet (utilisé par DVC pour piloter le
    pipeline). Retourne un dict vide si le fichier est absent, pour que le
    script reste utilisable indépendamment de DVC (valeurs par défaut argparse).
    """
    params_path = Path(__file__).parent.parent.parent / "params.yaml"
    if not params_path.exists():
        return {}
    import yaml
    with open(params_path) as f:
        return yaml.safe_load(f) or {}


if __name__ == "__main__":
    params = _load_params().get("train", {})

    parser = argparse.ArgumentParser(description="Entraînement du modèle de recommandation KNN")
    parser.add_argument("--n-neighbors", type=int, default=params.get("n_neighbors", 10))
    parser.add_argument("--test-size", type=float, default=params.get("test_size", 0.2))
    parser.add_argument("--random-state", type=int, default=params.get("random_state", 42))
    args = parser.parse_args()

    train_model(
        n_neighbors=args.n_neighbors,
        test_size=args.test_size,
        random_state=args.random_state,
    )
