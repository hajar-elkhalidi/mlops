"""
US-18 — Younes : chargement du modèle de recommandation au démarrage de l'API.

Stratégie :
1. Vérifie d'abord, via un test socket à timeout court, que le serveur MLflow
   est joignable (évite tout blocage DNS/connexion si l'hôte est absent).
2. Si joignable, tente de charger le modèle 'Production' depuis le MLflow
   Model Registry.
3. En cas d'échec à n'importe quelle étape (hôte injoignable, timeout, pas de
   modèle en Production), bascule immédiatement sur le modèle local sauvegardé
   par ml/src/train.py (fallback), pour ne jamais bloquer le démarrage de l'API.
"""
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "ml" / "src"))

from recommend import recommender  # noqa: E402

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "movielens-recommender")
MLFLOW_REQUEST_TIMEOUT_SECONDS = int(os.getenv("MLFLOW_REQUEST_TIMEOUT_SECONDS", "3"))
MLFLOW_MAX_RETRIES = int(os.getenv("MLFLOW_MAX_RETRIES", "1"))


def _is_mlflow_reachable(timeout: float = MLFLOW_REQUEST_TIMEOUT_SECONDS) -> bool:
    """Test de connectivité TCP rapide, sans attendre une résolution DNS lente."""
    parsed = urlparse(MLFLOW_TRACKING_URI)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError):
        return False


def load_recommender() -> None:
    """
    Charge le recommender, avec fallback local si MLflow est indisponible.

    Si aucun modèle n'est disponible nulle part (ni MLflow, ni fichier local —
    par exemple avant le premier entraînement), l'API démarre quand même,
    avec `recommender.is_loaded == False` : /health le signale, /predict
    répond 503. Cela évite un crash dur au démarrage dans un contexte de
    développement local où l'entraînement n'a pas encore été lancé.
    """
    os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = str(MLFLOW_REQUEST_TIMEOUT_SECONDS)
    os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = str(MLFLOW_MAX_RETRIES)

    if not _is_mlflow_reachable():
        print(f"[model_loader] Serveur MLflow injoignable ({MLFLOW_TRACKING_URI}). "
              f"Tentative de fallback sur le modèle local.")
        _load_local_fallback()
        return

    try:
        _load_from_mlflow_registry()
        print("[model_loader] Modèle chargé depuis le MLflow Model Registry (Production).")
    except Exception as exc:
        print(f"[model_loader] Échec du chargement depuis MLflow ({exc}). "
              f"Tentative de fallback sur le modèle local.")
        _load_local_fallback()


def _load_local_fallback() -> None:
    """Tente de charger le modèle local ; n'échoue jamais à l'appelant (API toujours démarrable)."""
    try:
        recommender.load()
        print("[model_loader] Modèle local chargé avec succès.")
    except FileNotFoundError:
        print(
            "[model_loader] Aucun modèle local trouvé "
            f"({recommender.model_path}). L'API démarre sans modèle chargé : "
            "/health le signalera, /predict répondra 503 jusqu'à l'entraînement "
            "(`make train` ou `dvc repro`)."
        )


def _load_from_mlflow_registry() -> None:
    import mlflow

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model_uri = f"models:/{MODEL_NAME}/Production"
    # Le chargement complet (user_factors, item_factors, mappings) reste géré
    # par recommender.load() ; ici on vérifie simplement que le registry répond.
    mlflow.sklearn.load_model(model_uri)
    recommender.load()
