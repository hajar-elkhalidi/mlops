# Serveur MLflow Tracking + Model Registry — configuration minimale (SQLite + stockage local)
FROM python:3.11-slim

WORKDIR /mlflow

RUN pip install --no-cache-dir mlflow==2.16.0

# Backend store SQLite local (simple pour un projet universitaire)
# + dossier d'artefacts persistant via volume Docker
VOLUME ["/mlflow/data", "/mlflow/artifacts"]

EXPOSE 5000

CMD ["mlflow", "server", \
     "--backend-store-uri", "sqlite:///mlflow/data/mlflow.db", \
     "--default-artifact-root", "/mlflow/artifacts", \
     "--host", "0.0.0.0", \
     "--port", "5000"]
