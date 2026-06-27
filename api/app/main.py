"""
Point d'entrée Flask — service d'inférence de recommandation de films.

API volontairement minimale, conformément aux consignes du projet :
- GET  /health   : vérifie la disponibilité du service et l'état du modèle
- POST /predict  : retourne le Top-N de films recommandés pour un utilisateur
- GET  /metrics  : métriques Prometheus (disponibilité, requêtes, latence, métriques ML)

Le modèle KNN est chargé une seule fois au démarrage du serveur (cf. core/model_loader.py),
avec fallback automatique sur le modèle local si MLflow est indisponible.
"""
import json
import os
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ML_SRC_PATH pointe vers le dossier ml/src. Calculé via une variable
# d'environnement plutôt qu'un nombre fixe de .parent, car la profondeur de
# ce fichier diffère entre l'exécution locale (api/app/main.py, sous la
# racine du repo) et l'exécution dans le conteneur Docker (/app/app/main.py,
# où ml/ est monté directement sous /app). Un nombre de .parent codé en dur
# donne un résultat différent selon le contexte -> bug silencieux sinon.
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).parent.parent.parent))
sys.path.append(str(PROJECT_ROOT / "ml" / "src"))

from recommend import recommender  # noqa: E402
from app.core.model_loader import load_recommender  # noqa: E402

ML_METRICS_PATH = PROJECT_ROOT / "ml" / "metrics.json"

app = Flask(__name__)

# Chargement du modèle au démarrage du processus (une seule fois)
load_recommender()

# --- Métriques Prometheus (point 9 : monitoring simple, cf. consignes projet) ---
PREDICT_REQUESTS_TOTAL = Counter(
    "predict_requests_total", "Nombre total d'appels à /predict", ["status"]
)
PREDICT_LATENCY_SECONDS = Histogram(
    "predict_latency_seconds", "Temps de réponse de /predict (secondes)"
)
MODEL_LOADED = Gauge(
    "model_loaded", "1 si le modèle de recommandation est chargé, 0 sinon"
)
MODEL_RMSE = Gauge("model_rmse", "RMSE du dernier modèle entraîné (ml/metrics.json)")
MODEL_PRECISION_AT_10 = Gauge(
    "model_precision_at_10", "Precision@10 du dernier modèle entraîné (ml/metrics.json)"
)


def _refresh_model_metrics() -> None:
    """Met à jour les gauges à partir de l'état courant du modèle et de ml/metrics.json."""
    MODEL_LOADED.set(1 if recommender.is_loaded else 0)
    if ML_METRICS_PATH.exists():
        try:
            with open(ML_METRICS_PATH) as f:
                ml_metrics = json.load(f)
            MODEL_RMSE.set(ml_metrics.get("rmse", 0))
            MODEL_PRECISION_AT_10.set(ml_metrics.get("precision_at_10", 0))
        except (json.JSONDecodeError, OSError):
            pass  # métriques ML non disponibles -> gauges laissées à leur dernière valeur


@app.route("/health", methods=["GET"])
def health():
    """Vérifie la disponibilité du service et l'état de chargement du modèle."""
    return jsonify(status="ok", model_loaded=recommender.is_loaded)


@app.route("/predict", methods=["POST"])
def predict():
    """
    Retourne le Top-N de films recommandés pour un utilisateur donné.

    Corps de requête JSON attendu :
        {"user_id": 1, "n": 10}   (n est optionnel, défaut 10, max 50)
    """
    start_time = time.time()

    payload = request.get_json(silent=True) or {}

    if "user_id" not in payload:
        PREDICT_REQUESTS_TOTAL.labels(status="400").inc()
        return jsonify(error="Le champ 'user_id' est requis dans le corps JSON."), 400

    try:
        user_id = int(payload["user_id"])
    except (TypeError, ValueError):
        PREDICT_REQUESTS_TOTAL.labels(status="400").inc()
        return jsonify(error="'user_id' doit être un entier."), 400

    n = payload.get("n", 10)
    try:
        n = int(n)
    except (TypeError, ValueError):
        PREDICT_REQUESTS_TOTAL.labels(status="400").inc()
        return jsonify(error="'n' doit être un entier."), 400
    n = max(1, min(n, 50))

    if not recommender.is_loaded:
        PREDICT_REQUESTS_TOTAL.labels(status="503").inc()
        return jsonify(error="Le modèle n'est pas encore chargé."), 503

    results = recommender.recommend(user_id=user_id, n=n)

    PREDICT_LATENCY_SECONDS.observe(time.time() - start_time)

    if results is None:
        PREDICT_REQUESTS_TOTAL.labels(status="404").inc()
        return jsonify(error=f"Utilisateur {user_id} introuvable dans les données d'entraînement."), 404

    PREDICT_REQUESTS_TOTAL.labels(status="200").inc()
    return jsonify(user_id=user_id, recommendations=results)


@app.route("/metrics", methods=["GET"])
def metrics():
    """Expose les métriques au format Prometheus (disponibilité, requêtes, latence, ML)."""
    _refresh_model_metrics()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
