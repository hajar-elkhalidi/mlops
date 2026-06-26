# User Stories — Critères d'acceptation détaillés

Format : INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable)

---

## EPIC 1 — Ingestion des données MovieLens

### US-01 — Configurer le projet dlt et la source MovieLens
**Assigné :** Hajar
**En tant que** Data Engineer
**Je veux** extraire les fichiers MovieLens (`ratings.csv`, `movies.csv`, `tags.csv`, `links.csv`)
**Afin de** les charger automatiquement dans DuckDB

**Critères d'acceptation :**
- [ ] Un pipeline `dlt` nommé `movielens_pipeline` existe
- [ ] Les 4 tables sources sont chargées dans le schéma `raw` de DuckDB
- [ ] Le pipeline est exécutable via `python dlt_pipeline/pipeline.py`
- [ ] Les types de colonnes sont corrects (int, float, timestamp)

### US-02 — Chargement incrémental dlt
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] `write_disposition="merge"` configuré sur `ratings`
- [ ] Une clé primaire composite (`user_id`, `movie_id`, `timestamp`) est définie
- [ ] Une seconde exécution du pipeline ne duplique aucune ligne

### US-03 — Validation du schéma DuckDB
**Assigné :** Hajar
**Critères d'acceptation :**
- [ ] Un script `scripts/validate_schema.py` vérifie la présence des 4 tables
- [ ] Le script retourne un code de sortie non-zéro si une table est absente

---

## EPIC 2 — Transformation dbt

### US-04 — Modèles staging dbt
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] `stg_ratings`, `stg_movies`, `stg_tags`, `stg_links` créés
- [ ] Renommage des colonnes en `snake_case`
- [ ] Cast explicite des types

### US-05 — Modèles marts
**Assigné :** Hajar
**Critères d'acceptation :**
- [ ] `dim_movies`, `dim_users`, `fact_ratings` créés
- [ ] `fact_ratings` contient une clé étrangère vers `dim_movies` et `dim_users`
- [ ] Grain de `fact_ratings` = 1 ligne par (user, movie, rating)

### US-06 — Tests dbt
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] Tests `unique` + `not_null` sur les clés primaires
- [ ] Tests `relationships` entre `fact_ratings` et les dimensions
- [ ] Test `accepted_values` sur `rating` (0.5 à 5.0)
- [ ] `dbt test` retourne 100% de succès

### US-07 — Documentation dbt
**Assigné :** Abdelkarim
**Critères d'acceptation :**
- [ ] `schema.yml` documente chaque modèle et colonne
- [ ] `dbt docs generate` fonctionne sans erreur

---

## EPIC 3 — Orchestration Dagster

### US-08 — Assets Dagster du pipeline complet
**Assigné :** Hajar
**Critères d'acceptation :**
- [ ] Asset `dlt_ingestion`
- [ ] Asset `dbt_transformation` (dépend de `dlt_ingestion`)
- [ ] Asset `ml_training` (dépend de `dbt_transformation`)
- [ ] Le graphe de dépendances est visible dans Dagster UI

### US-09 — Asset Checks qualité de données
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] Check `no_null_ratings` bloque le pipeline si des notes sont nulles
- [ ] Check `ratings_in_range` vérifie que `0.5 <= rating <= 5.0`

### US-10 — Schedule quotidien
**Assigné :** Imran
**Critères d'acceptation :**
- [ ] Un `ScheduleDefinition` exécute le job complet chaque jour à 02h00
- [ ] Le schedule est visible et activable dans Dagster UI

---

## EPIC 4 — Machine Learning

### US-11 — Matrice user-item
**Assigné :** Younes
**Critères d'acceptation :**
- [ ] Fonction `build_user_item_matrix()` retourne une matrice creuse (scipy)
- [ ] Gère les utilisateurs/films absents (cold start) sans erreur

### US-12 — Entraînement du modèle
**Assigné :** Douae
**Critères d'acceptation :**
- [ ] Modèle KNN item-based (`sklearn.neighbors.NearestNeighbors`, cosinus) entraîné sur 80% des données
- [ ] Modèle sérialisé via `joblib`
- [ ] Hyperparamètres configurables via CLI/argparse et `params.yaml` (DVC)

### US-13 — Évaluation du modèle
**Assigné :** Younes
**Critères d'acceptation :**
- [ ] RMSE et MAE calculés sur le jeu de test (20%)
- [ ] Precision@10 calculée
- [ ] Résultats loggés dans MLflow

---

## EPIC 5 — MLflow

### US-14 — Tracking MLflow
**Assigné :** Douae
**Critères d'acceptation :**
- [ ] Chaque run logue : hyperparamètres, RMSE, MAE, Precision@10
- [ ] L'artefact modèle est sauvegardé via `mlflow.sklearn.log_model`

### US-15 — Model Registry
**Assigné :** Younes
**Critères d'acceptation :**
- [ ] Le modèle est enregistré sous le nom `movielens-recommender`
- [ ] Le meilleur run (RMSE le plus bas) peut être promu manuellement en stage
      `Production` via `ml/src/promote_model.py`

---

## EPIC 6 — API Flask

### US-16 — Endpoint POST /predict
**Assigné :** Abdelkarim
**Critères d'acceptation :**
- [ ] Accepte un corps JSON `{"user_id": int, "n": int}` (`n` optionnel, défaut 10, max 50)
- [ ] Retourne un JSON avec le Top-N films recommandés
- [ ] Retourne 400 si `user_id` est absent ou de type invalide
- [ ] Retourne 404 si `user_id` est inconnu, 503 si le modèle n'est pas chargé

### US-17 — Endpoints GET /health et GET /metrics
**Assigné :** Nohaila
**Critères d'acceptation :**
- [ ] `/health` retourne `{"status": "ok", "model_loaded": bool}`
- [ ] `/metrics` exposé au format Prometheus (requêtes, latence, disponibilité,
      métriques ML lues depuis `ml/metrics.json`)

### US-18 — Chargement du modèle depuis MLflow Registry
**Assigné :** Younes
**Critères d'acceptation :**
- [ ] L'API tente de charger le modèle `Production` au démarrage du processus Flask
- [ ] Fallback automatique sur le modèle local si MLflow est indisponible
- [ ] L'API démarre normalement (sans planter) même si aucun modèle n'est disponible

---

## EPIC 7 — Docker

### US-19 — Dockerfile API Flask
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] Image basée sur `python:3.11-slim`
- [ ] Multi-stage build, taille < 300MB
- [ ] Serveur `gunicorn` (production), pas le serveur de développement Flask
- [ ] `HEALTHCHECK` configuré

### US-20 — Dockerfiles MLflow + Dagster + Streamlit
**Assigné :** Hajar
**Critères d'acceptation :**
- [ ] Conteneur MLflow expose le port 5000 avec backend SQLite
- [ ] Conteneur Dagster expose le port 3000
- [ ] Conteneur Streamlit expose le port 8501 et communique avec l'API via `API_URL`

### US-21 — docker-compose.yml
**Assigné :** Abderrahman
**Critères d'acceptation :**
- [ ] `docker compose up --build` démarre tous les services en une seule commande :
      pipeline-init, mlflow, dagster, api (Flask), streamlit, prometheus, grafana
- [ ] Le service `pipeline-init` exécute automatiquement dlt → dbt → entraînement KNN
      avant que l'API ne devienne disponible
- [ ] Volumes persistants pour DuckDB, MLflow artifacts, et le dossier `ml/`

---

## EPIC 8 — CI

### US-22 — Workflow CI
**Assigné :** Imran
**Critères d'acceptation :**
- [ ] Lint (`ruff`), tests unitaires (`pytest`), `dbt build` exécutés sur chaque PR
- [ ] Badge de statut dans le README

### US-23 — Build Docker de vérification en CI
**Assigné :** Hamza
**Critères d'acceptation :**
- [ ] La CI construit l'image Docker de l'API pour vérifier que le build ne casse pas
- [ ] Aucune étape de déploiement n'est exécutée en CI (le projet reste local)

---

## EPIC 9 — Exécution locale (Docker Compose)

### US-24 — Démarrage en une seule commande
**Assigné :** Hamza
**Critères d'acceptation :**
- [ ] `git clone` puis `docker compose up --build` suffisent à obtenir un système
      fonctionnel, sans étape manuelle supplémentaire
- [ ] Aucune dépendance à un compte ou service cloud externe

### US-25 — Documentation de l'exécution locale
**Assigné :** Imran
**Critères d'acceptation :**
- [ ] Le README ne mentionne plus aucune dépendance cloud (Oracle, SSH, VM)
- [ ] Les instructions d'installation se limitent à `git clone` + `docker compose up --build`

---

## EPIC 10 — Monitoring

### US-26 — Prometheus
**Assigné :** Nohaila
**Critères d'acceptation :**
- [ ] `prometheus.yml` scrape `/metrics` de l'API toutes les 15s

### US-27 — Dashboard Grafana
**Assigné :** Abdelkarim
**Critères d'acceptation :**
- [ ] Dashboard provisionné automatiquement au démarrage
- [ ] Panels : latence p95, taux de requêtes, erreurs 4xx/5xx

---

## EPIC 11 — Documentation

### US-28 — README
**Assigné :** Imran
**Critères d'acceptation :**
- [ ] Installation, lancement, architecture, structure du repo documentés

### US-29 — Présentation finale
**Assigné :** Hamza
**Critères d'acceptation :**
- [ ] Support de soutenance couvrant contexte, architecture, démo, résultats

---

## EPIC 12 — Interface Streamlit

### US-30 — Interface de recommandation Streamlit
**Assigné :** Abdelkarim
**Critères d'acceptation :**
- [ ] Liste déroulante pour choisir un utilisateur MovieLens (lue depuis DuckDB)
- [ ] Bouton pour demander des recommandations via l'API Flask (`POST /predict`)
- [ ] Affichage des films recommandés (titre + score), sans logique de recommandation dupliquée
- [ ] Message d'erreur clair si l'API est inaccessible ou si le modèle n'est pas chargé

---

## EPIC 13 — Versioning DVC

### US-31 — Pipeline DVC reproductible
**Assigné :** Hajar
**Critères d'acceptation :**
- [ ] `dvc.yaml` définit 3 stages : `ingest`, `transform`, `train`
- [ ] `params.yaml` centralise les hyperparamètres du pipeline
- [ ] `dvc repro` exécute le pipeline de bout en bout et génère `dvc.lock`
- [ ] `dvc metrics show` affiche RMSE / MAE / Precision@10 du dernier entraînement
