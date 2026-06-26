"""
Validation du schéma DuckDB après ingestion dlt (dataset ml-100k).

Vérifie que les 3 tables raw existent et contiennent des données.
Sortie non-zéro si une table est manquante ou vide -> utilisé en CI.
"""
import sys
from pathlib import Path

import duckdb

DUCKDB_PATH = Path(__file__).parent.parent / "data" / "duckdb" / "movielens.duckdb"
EXPECTED_TABLES = ["ratings", "movies", "users"]


def validate_schema() -> bool:
    if not DUCKDB_PATH.exists():
        print(f"[ERREUR] Base DuckDB introuvable : {DUCKDB_PATH}")
        return False

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    ok = True

    existing_tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'"
        ).fetchall()
    }

    for table in EXPECTED_TABLES:
        if table not in existing_tables:
            print(f"[ERREUR] Table manquante : raw.{table}")
            ok = False
            continue

        count = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        if count == 0:
            print(f"[ERREUR] Table vide : raw.{table}")
            ok = False
        else:
            print(f"[OK] raw.{table} : {count} lignes")

    con.close()
    return ok


if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)
