"""
Job Dagster regroupant tout le pipeline + schedule quotidien.
US-10 — Imran
"""
from dagster import define_asset_job, ScheduleDefinition, AssetSelection

# Job qui matérialise tous les assets du pipeline (ingestion -> transformation -> ML)
movielens_pipeline_job = define_asset_job(
    name="movielens_pipeline_job",
    selection=AssetSelection.all(),
    description="Pipeline complet : ingestion dlt -> transformation dbt -> entraînement ML",
)

# Schedule quotidien à 02h00 (heure du conteneur / serveur)
daily_pipeline_schedule = ScheduleDefinition(
    job=movielens_pipeline_job,
    cron_schedule="0 2 * * *",
    name="daily_movielens_pipeline",
    description="Exécution quotidienne du pipeline complet à 02h00",
)
