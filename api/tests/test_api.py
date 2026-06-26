"""
Tests unitaires de l'API Flask (exécutés en CI via pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_predict_missing_user_id_returns_400(client):
    response = client.post("/predict", json={})
    assert response.status_code == 400


def test_predict_invalid_user_id_type_returns_400(client):
    response = client.post("/predict", json={"user_id": "not-an-int"})
    assert response.status_code == 400


def test_predict_unknown_user_returns_404_or_503(client):
    # 404 si le modèle est chargé mais l'utilisateur est inconnu,
    # 503 si le modèle n'a pas pu être chargé du tout (CI sans entraînement préalable)
    response = client.post("/predict", json={"user_id": 999999999, "n": 5})
    assert response.status_code in (404, 503)


def test_predict_no_json_body_returns_400(client):
    response = client.post("/predict")
    assert response.status_code == 400


def test_metrics_endpoint_exposed(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"model_loaded" in response.data
