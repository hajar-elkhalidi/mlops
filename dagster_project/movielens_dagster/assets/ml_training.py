"""
Asset Dagster : entraînement du modèle de recommandation, dépend de dbt_transformation.
US-08 — Hajar / US-12 — Douae
"""
import sys
from pathlib import Path

from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue

from .transformation import dbt_transformation

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "ml" / "src"))


@asset(
    group_name="machine_learning",
    deps=[dbt_transformation],
    description="Entraîne le modèle KNN (item-based) de filtrage collaboratif et logue dans MLflow",
)
def ml_training(context: AssetExecutionContext) -> MaterializeResult:
    from train import train_model  # import local

    metrics = train_model()
    context.log.info(f"Métriques d'entraînement : {metrics}")

    return MaterializeResult(
        metadata={
            "rmse": MetadataValue.float(metrics["rmse"]),
            "mae": MetadataValue.float(metrics["mae"]),
            "precision_at_10": MetadataValue.float(metrics["precision_at_10"]),
        }
    )
