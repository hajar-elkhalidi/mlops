"""
US-15 — Younes : promotion du meilleur run vers le stage 'Production' du
MLflow Model Registry.

Usage :
    python ml/src/promote_model.py
"""
import os

import mlflow
from mlflow.tracking import MlflowClient

# En Docker Compose, le serveur MLflow est joignable via le nom de service "mlflow".
# En local (hors conteneur), on retombe sur localhost:5000.
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = "movielens-recommender"


def promote_best_model():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    experiment = client.get_experiment_by_name("movielens-recommender")
    if experiment is None:
        raise RuntimeError("Expérience MLflow 'movielens-recommender' introuvable.")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.rmse ASC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError("Aucun run trouvé pour cette expérience.")

    best_run = runs[0]
    print(f"[promote] Meilleur run : {best_run.info.run_id} (RMSE={best_run.data.metrics.get('rmse')})")

    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    matching = [v for v in versions if v.run_id == best_run.info.run_id]
    if not matching:
        raise RuntimeError("Aucune version de modèle enregistrée ne correspond à ce run.")

    version = matching[0].version
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=version,
        stage="Production",
        archive_existing_versions=True,
    )
    print(f"[promote] Version {version} de '{MODEL_NAME}' promue en Production.")


if __name__ == "__main__":
    promote_best_model()
