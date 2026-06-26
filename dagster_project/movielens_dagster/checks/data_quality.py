"""
Asset Checks Dagster : qualité de données sur fact_ratings.
US-09 — Abderrahman

Ces checks bloquent le pipeline en aval si la donnée est corrompue,
en complément des tests dbt (couche SQL).
"""
import duckdb
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity
from pathlib import Path

from ..assets.transformation import dbt_transformation

DUCKDB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "duckdb" / "movielens.duckdb"


def _query(sql: str):
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    result = con.execute(sql).fetchone()[0]
    con.close()
    return result


@asset_check(
    asset=dbt_transformation,
    description="Vérifie qu'aucune note n'est nulle dans fact_ratings",
)
def no_null_ratings() -> AssetCheckResult:
    null_count = _query("SELECT COUNT(*) FROM marts.fact_ratings WHERE rating IS NULL")
    return AssetCheckResult(
        passed=null_count == 0,
        severity=AssetCheckSeverity.ERROR,
        metadata={"null_ratings_count": null_count},
    )


@asset_check(
    asset=dbt_transformation,
    description="Vérifie que toutes les notes sont comprises entre 1 et 5",
)
def ratings_in_range() -> AssetCheckResult:
    out_of_range = _query(
        "SELECT COUNT(*) FROM marts.fact_ratings WHERE rating < 1 OR rating > 5"
    )
    return AssetCheckResult(
        passed=out_of_range == 0,
        severity=AssetCheckSeverity.ERROR,
        metadata={"out_of_range_count": out_of_range},
    )


@asset_check(
    asset=dbt_transformation,
    description="Vérifie qu'il n'y a pas de chute brutale du volume de données (> 20%)",
)
def no_volume_drop() -> AssetCheckResult:
    current_count = _query("SELECT COUNT(*) FROM marts.fact_ratings")
    # Seuil minimal attendu pour MovieLens 100K (100 000 notes officielles)
    expected_min = 80_000
    return AssetCheckResult(
        passed=current_count >= expected_min,
        severity=AssetCheckSeverity.WARN,
        metadata={"current_count": current_count, "expected_min": expected_min},
    )
