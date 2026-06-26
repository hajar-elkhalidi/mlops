"""
Tests unitaires du module Recommender (ml/src/recommend.py) — modèle KNN item-based.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

sys.path.append(str(Path(__file__).parent.parent.parent / "ml" / "src"))

from recommend import Recommender  # noqa: E402


@pytest.fixture
def fake_recommender(tmp_path):
    """
    Construit un Recommender avec un faux bundle KNN en mémoire (pas de fichier réel).

    Scénario : 2 utilisateurs (10, 20), 3 films (100, 200, 300).
    L'utilisateur 10 a noté le film 100 avec un 5 (>= 4, donc "aimé").
    Le film 100 a pour voisin le plus proche le film 200 (distance cosinus 0.2),
    donc on attend que le film 200 soit recommandé à l'utilisateur 10.
    """
    rec = Recommender(model_path=tmp_path / "fake_model.joblib")

    # item_matrix : lignes = films, colonnes = utilisateurs (transposée user-item)
    item_matrix = csr_matrix(np.array([
        [5.0, 0.0],  # film 100 : noté 5 par user 10, pas noté par user 20
        [0.0, 3.0],  # film 200 : pas noté par user 10, noté 3 par user 20
        [0.0, 0.0],  # film 300 : pas noté
    ]))

    # Pour chaque film (ligne), ses voisins triés par distance croissante
    neighbor_indices = np.array([
        [1, 2],  # voisins du film 100 (idx 0) : film 200 (idx 1), film 300 (idx 2)
        [0, 2],  # voisins du film 200 (idx 1) : film 100 (idx 0), film 300 (idx 2)
        [0, 1],  # voisins du film 300 (idx 2) : film 100 (idx 0), film 200 (idx 1)
    ])
    neighbor_distances = np.array([
        [0.2, 0.9],
        [0.2, 0.8],
        [0.9, 0.8],
    ])

    rec.bundle = {
        "item_matrix": item_matrix,
        "neighbor_indices": neighbor_indices,
        "neighbor_distances": neighbor_distances,
        "user_id_to_idx": {10: 0, 20: 1},
        "movie_id_to_idx": {100: 0, 200: 1, 300: 2},
    }
    rec.idx_to_movie_id = {v: k for k, v in rec.bundle["movie_id_to_idx"].items()}
    return rec


def test_recommend_known_user_returns_results(fake_recommender):
    results = fake_recommender.recommend(user_id=10, n=2)
    assert results is not None
    assert len(results) >= 1
    assert all("movie_id" in r and "score" in r for r in results)
    # Le film 100 (aimé par l'utilisateur 10) a pour plus proche voisin le film 200
    assert results[0]["movie_id"] == 200


def test_recommend_unknown_user_returns_none(fake_recommender):
    results = fake_recommender.recommend(user_id=999, n=5)
    assert results is None


def test_recommend_without_loading_raises():
    rec = Recommender()
    with pytest.raises(RuntimeError):
        rec.recommend(user_id=1, n=5)
