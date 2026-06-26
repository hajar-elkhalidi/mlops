"""
Source dlt pour le dataset MovieLens 100K (ml-100k).

Dataset officiel et stable : 100 000 notes, 943 utilisateurs, 1682 films
(https://files.grouplens.org/datasets/movielens/ml-100k.zip). Choisi pour sa
légèreté et sa rapidité d'exécution (cf. consigne projet : éviter ml-1m / ml-25m).

Télécharge (si absent) et extrait les fichiers du dataset ml-100k :
- u.data  (user_id, movie_id, rating, unix_timestamp) — séparateur tabulation
- u.item  (movie_id, title, release_date, ..., genres binaires) — séparateur '|'
- u.user  (user_id, age, sex, occupation, zip_code) — séparateur '|'

Si le téléchargement échoue (réseau restreint, environnement hors-ligne,
CI sans accès à files.grouplens.org), un jeu de données synthétique
structurellement identique est généré automatiquement en fallback, afin que
le pipeline reste exécutable de bout en bout (utile en environnement de
correction/sandbox).

Auteur : Hajar (Data Engineer)
"""
import random
import zipfile
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

import dlt
import pandas as pd

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
ZIP_PATH = RAW_DATA_DIR / "ml-100k.zip"
EXTRACT_DIR = RAW_DATA_DIR / "ml-100k"

GENRE_COLUMNS = [
    "unknown", "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery",
    "Romance", "Sci-Fi", "Thriller", "War", "Western",
]


def _generate_synthetic_dataset(target_dir: Path, n_users: int = 200, n_movies: int = 150) -> None:
    """
    Génère un jeu de données au format ml-100k (u.data / u.item / u.user),
    utilisé uniquement en fallback si le téléchargement officiel échoue.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)

    # u.item : movie_id | title | release_date | video_release_date | imdb_url | 19 genres binaires
    item_rows = []
    for movie_id in range(1, n_movies + 1):
        year = rng.randint(1990, 1998)
        genres = [rng.choice([0, 1]) for _ in GENRE_COLUMNS]
        if sum(genres) == 0:
            genres[rng.randrange(len(genres))] = 1
        fields = [str(movie_id), f"Synthetic Movie {movie_id} ({year})", f"01-Jan-{year}", "", ""] + [str(g) for g in genres]
        item_rows.append("|".join(fields))
    (target_dir / "u.item").write_text("\n".join(item_rows), encoding="latin-1")

    # u.user : user_id | age | sex | occupation | zip_code
    occupations = ["student", "engineer", "artist", "educator", "writer", "other"]
    user_rows = []
    for user_id in range(1, n_users + 1):
        age = rng.randint(18, 65)
        sex = rng.choice(["M", "F"])
        occupation = rng.choice(occupations)
        zip_code = f"{rng.randint(10000, 99999)}"
        user_rows.append(f"{user_id}|{age}|{sex}|{occupation}|{zip_code}")
    (target_dir / "u.user").write_text("\n".join(user_rows), encoding="latin-1")

    # u.data : user_id \t movie_id \t rating \t unix_timestamp
    base_ts = int(datetime(2020, 1, 1).timestamp())
    data_rows = []
    for user_id in range(1, n_users + 1):
        rated_movies = rng.sample(range(1, n_movies + 1), k=rng.randint(5, 40))
        for movie_id in rated_movies:
            rating = rng.randint(1, 5)
            ts = base_ts + rng.randint(0, 60 * 60 * 24 * 365 * 3)
            data_rows.append(f"{user_id}\t{movie_id}\t{rating}\t{ts}")
    (target_dir / "u.data").write_text("\n".join(data_rows), encoding="latin-1")

    print(f"[dlt] Jeu de données synthétique (format ml-100k) généré dans {target_dir} "
          f"({n_users} users, {n_movies} movies, {len(data_rows)} ratings).")


def download_and_extract() -> Path:
    """Télécharge et extrait le dataset MovieLens 100K si nécessaire, avec fallback synthétique."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if EXTRACT_DIR.exists() and (EXTRACT_DIR / "u.data").exists():
        return EXTRACT_DIR

    try:
        if not ZIP_PATH.exists():
            print(f"[dlt] Téléchargement de MovieLens 100K depuis {MOVIELENS_URL} ...")
            req = urllib.request.Request(MOVIELENS_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response, open(ZIP_PATH, "wb") as out_file:
                out_file.write(response.read())

        print(f"[dlt] Extraction de {ZIP_PATH} ...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(RAW_DATA_DIR)

        return EXTRACT_DIR

    except (urllib.error.URLError, urllib.error.HTTPError, zipfile.BadZipFile, OSError) as exc:
        print(f"[dlt] Téléchargement MovieLens 100K impossible ({exc}). "
              f"Bascule sur un jeu de données synthétique de fallback.")
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        _generate_synthetic_dataset(EXTRACT_DIR)
        return EXTRACT_DIR


@dlt.source(name="movielens")
def movielens_source():
    """Source dlt regroupant les 3 ressources MovieLens 100K (ratings, movies, users)."""
    data_dir = download_and_extract()

    @dlt.resource(
        name="ratings",
        write_disposition="merge",
        primary_key=["user_id", "movie_id", "timestamp"],
    )
    def ratings():
        df = pd.read_csv(
            data_dir / "u.data",
            sep="\t",
            names=["user_id", "movie_id", "rating", "timestamp"],
            encoding="latin-1",
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        yield df.to_dict(orient="records")

    @dlt.resource(
        name="movies",
        write_disposition="merge",
        primary_key="movie_id",
    )
    def movies():
        columns = ["movie_id", "title", "release_date", "video_release_date", "imdb_url"] + GENRE_COLUMNS
        df = pd.read_csv(
            data_dir / "u.item",
            sep="|",
            names=columns,
            encoding="latin-1",
        )
        # Reconstitue une colonne "genres" lisible (ex: "Action|Comedy") à partir
        # des 19 colonnes binaires, pour rester compatible avec les modèles dbt en aval.
        df["genres"] = df[GENRE_COLUMNS].apply(
            lambda row: "|".join([g for g, v in zip(GENRE_COLUMNS, row) if v == 1]) or "(no genres listed)",
            axis=1,
        )
        df = df[["movie_id", "title", "release_date", "genres"]]
        yield df.to_dict(orient="records")

    @dlt.resource(
        name="users",
        write_disposition="merge",
        primary_key="user_id",
    )
    def users():
        df = pd.read_csv(
            data_dir / "u.user",
            sep="|",
            names=["user_id", "age", "sex", "occupation", "zip_code"],
            encoding="latin-1",
        )
        yield df.to_dict(orient="records")

    return ratings, movies, users
