"""
US-11 — Younes : construction de la matrice creuse user-item depuis fact_ratings.
"""
from pathlib import Path
from typing import Tuple

import duckdb
import numpy as np
from scipy.sparse import csr_matrix

DUCKDB_PATH = Path(__file__).parent.parent.parent / "data" / "duckdb" / "movielens.duckdb"


def load_ratings() -> "duckdb.DuckDBPyRelation":
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT user_id, movie_id, rating FROM marts.fact_ratings").df()
    con.close()
    return df


def build_user_item_matrix() -> Tuple[csr_matrix, dict, dict]:
    """
    Construit la matrice creuse user-item à partir de fact_ratings.

    Returns:
        matrix: scipy.sparse.csr_matrix de shape (n_users, n_movies)
        user_id_to_idx: mapping user_id -> index de ligne
        movie_id_to_idx: mapping movie_id -> index de colonne
    """
    df = load_ratings()

    user_ids = sorted(df["user_id"].unique())
    movie_ids = sorted(df["movie_id"].unique())

    user_id_to_idx = {uid: i for i, uid in enumerate(user_ids)}
    movie_id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}

    rows = df["user_id"].map(user_id_to_idx).values
    cols = df["movie_id"].map(movie_id_to_idx).values
    data = df["rating"].values.astype(np.float32)

    matrix = csr_matrix(
        (data, (rows, cols)),
        shape=(len(user_ids), len(movie_ids)),
    )

    return matrix, user_id_to_idx, movie_id_to_idx


if __name__ == "__main__":
    matrix, u_map, m_map = build_user_item_matrix()
    print(f"Matrice user-item : {matrix.shape[0]} users x {matrix.shape[1]} movies")
    print(f"Sparsité : {1 - matrix.nnz / (matrix.shape[0] * matrix.shape[1]):.4%}")
