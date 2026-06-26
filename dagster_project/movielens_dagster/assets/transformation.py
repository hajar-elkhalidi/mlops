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
    description="Exécute dbt build (run + test) sur les modèles staging et marts",
)
def dbt_transformation(context: AssetExecutionContext) -> MaterializeResult:
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
            "dbt_command": MetadataValue.text("dbt build"),
            "stdout_tail": MetadataValue.text(result.stdout[-2000:]),
        }
    )
