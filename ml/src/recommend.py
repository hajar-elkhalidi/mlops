"""
Module de génération de recommandations à partir du modèle KNN entraîné.
Utilisé par l'API Flask (point 7) et par ml/src/train.py.

Principe : pour un utilisateur donné, on part des films qu'il a le mieux notés,
puis on propose leurs plus proches voisins (films similaires selon KNN),
en excluant les films déjà notés par l'utilisateur.
"""
from pathlib import Path
from typing import List, Dict, Optional

import joblib
import numpy as np

MODEL_PATH = Path(__file__).parent.parent / "models" / "knn_model.joblib"


class Recommender:
    """Wrapper autour du modèle KNN entraîné, prêt pour l'inférence."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.bundle = None
        self.idx_to_movie_id: Dict[int, int] = {}

    def load(self):
        self.bundle = joblib.load(self.model_path)
        self.idx_to_movie_id = {v: k for k, v in self.bundle["movie_id_to_idx"].items()}
        return self

    @property
    def is_loaded(self) -> bool:
        return self.bundle is not None

    def recommend(self, user_id: int, n: int = 10) -> Optional[List[dict]]:
        """
        Retourne le Top-N de films recommandés pour un utilisateur donné, en
        agrégeant les voisins KNN des films que l'utilisateur a le mieux notés.
        """
        if not self.is_loaded:
            raise RuntimeError("Le modèle n'est pas chargé. Appelez .load() au démarrage.")

        user_id_to_idx = self.bundle["user_id_to_idx"]
        if user_id not in user_id_to_idx:
            return None  # utilisateur inconnu -> géré en 404 côté API

        u_idx = user_id_to_idx[user_id]
        item_matrix = self.bundle["item_matrix"]
        neighbor_indices = self.bundle["neighbor_indices"]
        neighbor_distances = self.bundle["neighbor_distances"]

        user_ratings = item_matrix[:, u_idx].toarray().ravel()
        rated_items = set(np.where(user_ratings > 0)[0])

        # Films notés >=4 par l'utilisateur, du mieux noté au moins bien noté
        liked_items = [i for i in np.argsort(user_ratings)[::-1] if user_ratings[i] >= 4]

        scores: Dict[int, float] = {}
        for item_idx in liked_items:
            for rank, neighbor_idx in enumerate(neighbor_indices[item_idx]):
                if neighbor_idx in rated_items:
                    continue  # ne pas recommander un film déjà noté
                similarity = 1 - neighbor_distances[item_idx][rank]
                scores[neighbor_idx] = scores.get(neighbor_idx, 0.0) + similarity

        if not scores:
            return []  # utilisateur sans note >=4 (cold start partiel) -> liste vide

        top_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]

        return [
            {
                "movie_id": int(self.idx_to_movie_id[item_idx]),
                "score": float(score),
            }
            for item_idx, score in top_items
        ]


# Instance singleton utilisée par l'API
recommender = Recommender()
