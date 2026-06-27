"""
Asset Dagster : transformation dbt (staging + marts), dépend de dlt_ingestion.
US-08 — Hajar
"""
import subprocess
from pathlib import Path

from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue

from .ingestion import dlt_ingestion

DBT_PROJECT_DIR = Path(__file__).parent.parent.parent.parent / "dbt_project"


@asset(
    group_name="transformation",
    deps=[dlt_ingestion],
    description="Exécute dbt deps puis dbt build (run + test) sur les modèles staging et marts",
)
def dbt_transformation(context: AssetExecutionContext) -> MaterializeResult:
    deps_result = subprocess.run(
        ["dbt", "deps", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
    )
    context.log.info(deps_result.stdout)
    if deps_result.returncode != 0:
        context.log.error(deps_result.stderr)
        raise Exception(f"dbt deps a échoué : {deps_result.stderr}")

    result = subprocess.run(
        ["dbt", "build", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception(f"dbt build a échoué : {result.stderr}")

    return MaterializeResult(
        metadata={
            "dbt_command": MetadataValue.text("dbt deps && dbt build"),
            "stdout_tail": MetadataValue.text(result.stdout[-2000:]),
        }
    )
