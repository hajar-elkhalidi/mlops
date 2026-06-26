"""
Point d'entrée du pipeline d'ingestion dlt : MovieLens -> DuckDB (schéma raw).

Usage :
    python dlt_pipeline/pipeline.py
"""
import sys
from pathlib import Path

import dlt
from dlt.pipeline.pipeline import Pipeline

sys.path.append(str(Path(__file__).parent))
from movielens_source import movielens_source  # noqa: E402

DUCKDB_PATH = Path(__file__).parent.parent / "data" / "duckdb" / "movielens.duckdb"


def run_pipeline() -> Pipeline:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="movielens_pipeline",
        destination=dlt.destinations.duckdb(str(DUCKDB_PATH)),
        dataset_name="raw",
    )

    load_info = pipeline.run(movielens_source())
    print(load_info)

    # Vérification rapide post-chargement
    with pipeline.sql_client() as client:
        for table in ["ratings", "movies", "users"]:
            result = client.execute_sql(f"SELECT COUNT(*) FROM raw.{table}")
            print(f"[dlt] raw.{table} -> {result[0][0]} lignes")

    return pipeline


if __name__ == "__main__":
    run_pipeline()
