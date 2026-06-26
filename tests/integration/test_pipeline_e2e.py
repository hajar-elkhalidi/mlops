"""
Test d'intégration : vérifie la cohérence de bout en bout
dlt -> DuckDB -> dbt (exécution manuelle requise au préalable, voir README).

Ce test est marqué 'integration' et exclu du CI rapide ; il est exécuté
sur demande ou en pipeline de validation complète.
"""
import sys
from pathlib import Path

import duckdb
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
DUCKDB_PATH = PROJECT_ROOT / "data" / "duckdb" / "movielens.duckdb"

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def duckdb_connection():
    if not DUCKDB_PATH.exists():
        pytest.skip("Base DuckDB introuvable — exécuter le pipeline dlt + dbt au préalable.")
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    yield con
    con.close()


def test_raw_tables_exist(duckdb_connection):
    tables = {
        row[0]
        for row in duckdb_connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'"
        ).fetchall()
    }
    assert {"ratings", "movies", "tags", "links"}.issubset(tables)


def test_marts_fact_ratings_has_data(duckdb_connection):
    count = duckdb_connection.execute("SELECT COUNT(*) FROM marts.fact_ratings").fetchone()[0]
    assert count > 0


def test_marts_referential_integrity(duckdb_connection):
    orphans = duckdb_connection.execute(
        """
        SELECT COUNT(*) FROM marts.fact_ratings f
        LEFT JOIN marts.dim_movies m ON f.movie_id = m.movie_id
        WHERE m.movie_id IS NULL
        """
    ).fetchone()[0]
    assert orphans == 0
