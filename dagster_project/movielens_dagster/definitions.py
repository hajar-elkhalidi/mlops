"""
Définitions Dagster principales — point d'entrée chargé par `dagster dev`.
US-08, US-09, US-10 — Hajar / Abderrahman / Imran
"""
from dagster import Definitions

from .assets import dlt_ingestion, dbt_transformation, ml_training
from .checks import no_null_ratings, ratings_in_range, no_volume_drop
from .jobs import movielens_pipeline_job, daily_pipeline_schedule

defs = Definitions(
    assets=[dlt_ingestion, dbt_transformation, ml_training],
    asset_checks=[no_null_ratings, ratings_in_range, no_volume_drop],
    jobs=[movielens_pipeline_job],
    schedules=[daily_pipeline_schedule],
)
