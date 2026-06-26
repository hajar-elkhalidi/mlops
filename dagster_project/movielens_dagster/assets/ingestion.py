"""
Asset Dagster : ingestion MovieLens via dlt -> DuckDB (schéma raw).
US-08 — Hajar
"""
import sys
from pathlib import Path

from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "dlt_pipeline"))


@asset(
    group_name="ingestion",
    description="Extraction MovieLens (ratings, movies, tags, links) vers DuckDB via dlt",
)
def dlt_ingestion(context: AssetExecutionContext) -> MaterializeResult:
    from pipeline import run_pipeline  # import local pour isoler dlt

    load_info = run_pipeline()
    context.log.info(f"dlt load info: {load_info}")

    return MaterializeResult(
        metadata={
            "pipeline_name": MetadataValue.text("movielens_pipeline"),
            "destination": MetadataValue.text("duckdb (schema: raw)"),
        }
    )
