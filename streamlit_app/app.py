"""
Interface Streamlit — point d'entrée utilisateur du système de recommandation.

Permet de :
- choisir un utilisateur MovieLens (liste lue depuis DuckDB)
- demander des recommandations (appel HTTP à l'API Flask : POST /predict)
- afficher les films recommandés (titres lus depuis DuckDB)

Architecture : Streamlit ne réimplémente aucune logique ML — il consomme
uniquement l'API Flask, conformément au principe "un seul point d'inférence".
"""
import os
from pathlib import Path

import duckdb
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", "/app/data/duckdb/movielens.duckdb"))

st.set_page_config(page_title="MovieLens Recommender", page_icon="🎬", layout="centered")


@st.cache_data(ttl=60)
def load_users() -> list[int]:
    """Lit la liste des utilisateurs disponibles depuis DuckDB (table marts.dim_users)."""
    if not DUCKDB_PATH.exists():
        return []
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        rows = con.execute("SELECT user_id FROM marts.dim_users ORDER BY user_id").fetchall()
        return [r[0] for r in rows]
    except duckdb.CatalogException:
        return []
    finally:
        con.close()


@st.cache_data(ttl=60)
def load_movie_titles() -> dict[int, str]:
    """Lit le mapping movie_id -> titre depuis DuckDB (table marts.dim_movies)."""
    if not DUCKDB_PATH.exists():
        return {}
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        rows = con.execute("SELECT movie_id, title FROM marts.dim_movies").fetchall()
        return {r[0]: r[1] for r in rows}
    except duckdb.CatalogException:
        return {}
    finally:
        con.close()


def call_predict_api(user_id: int, n: int) -> dict:
    """Appelle l'API Flask (POST /predict) et retourne la réponse JSON."""
    response = requests.post(
        f"{API_URL}/predict",
        json={"user_id": user_id, "n": n},
        timeout=10,
    )
    return {"status_code": response.status_code, "body": response.json()}


def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200 and response.json().get("model_loaded", False)
    except requests.exceptions.RequestException:
        return False


# --- Interface ---

st.title("🎬 MovieLens Recommender")
st.caption("Système de recommandation de films — filtrage collaboratif KNN")

api_healthy = check_api_health()
if api_healthy:
    st.success(f"API connectée ({API_URL}) — modèle chargé.", icon="✅")
else:
    st.error(
        f"API inaccessible ou modèle non chargé ({API_URL}). "
        f"Vérifiez que le service `api` est démarré (`docker compose up`).",
        icon="⚠️",
    )

users = load_users()
movie_titles = load_movie_titles()

if not users:
    st.warning(
        "Aucun utilisateur trouvé dans la base DuckDB. "
        "Le pipeline d'ingestion (dlt) et de transformation (dbt) doit s'exécuter "
        "au moins une fois avant de pouvoir utiliser cette interface.",
        icon="ℹ️",
    )
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_user = st.selectbox("Choisir un utilisateur MovieLens", options=users)
    with col2:
        n_recommendations = st.number_input(
            "Nombre de recommandations", min_value=1, max_value=50, value=10
        )

    if st.button("Obtenir des recommandations", type="primary", disabled=not api_healthy):
        with st.spinner("Calcul des recommandations..."):
            result = call_predict_api(selected_user, n_recommendations)

        if result["status_code"] == 200:
            recommendations = result["body"]["recommendations"]
            if not recommendations:
                st.info(
                    "Aucune recommandation disponible pour cet utilisateur "
                    "(pas assez de films notés positivement)."
                )
            else:
                st.subheader(f"Films recommandés pour l'utilisateur {selected_user}")
                for rank, rec in enumerate(recommendations, start=1):
                    movie_id = rec["movie_id"]
                    title = movie_titles.get(movie_id, f"Film #{movie_id}")
                    st.write(f"**{rank}. {title}** — score de similarité : `{rec['score']:.3f}`")
        elif result["status_code"] == 404:
            st.warning(result["body"].get("error", "Utilisateur introuvable."))
        else:
            st.error(result["body"].get("error", "Erreur inattendue de l'API."))

st.divider()
st.caption(
    "Cette interface consomme l'API Flask (`POST /predict`) — "
    "aucune logique de recommandation n'est dupliquée ici."
)
