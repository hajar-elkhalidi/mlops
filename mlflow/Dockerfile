# Serveur MLflow Tracking + Model Registry — configuration minimale (SQLite + stockage local)
FROM python:3.11-slim

WORKDIR /mlflow

RUN pip install --no-cache-dir mlflow==2.16.0

VOLUME ["/mlflow/data", "/mlflow/artifacts"]

EXPOSE 5000

# Le mkdir doit s'exécuter au démarrage du conteneur (pas au build) : un volume
# Docker monté sur /mlflow/data remplace entièrement le contenu créé dans
# l'image au moment du build, donc un `RUN mkdir` dans le Dockerfile n'a aucun
# effet une fois le volume attaché.
#
# IMPORTANT : sqlite:/// (3 slashes) est un chemin RELATIF au répertoire de
# travail courant (WORKDIR /mlflow), donc "sqlite:///mlflow/data/mlflow.db"
# résolvait en réalité vers /mlflow/mlflow/data/mlflow.db (sous-dossier
# inexistant) — pas /mlflow/data/mlflow.db comme prévu. Un chemin ABSOLU sur
# Linux nécessite 4 slashes : sqlite:////mlflow/data/mlflow.db.
CMD mkdir -p /mlflow/data /mlflow/artifacts && \
    mlflow server \
        --backend-store-uri sqlite:////mlflow/data/mlflow.db \
        --default-artifact-root /mlflow/artifacts \
        --host 0.0.0.0 \
        --port 5000
