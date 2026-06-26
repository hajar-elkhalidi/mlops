# Architecture technique — MovieLens Recommender

## Vue d'ensemble

Le projet suit un pipeline DataOps/MLOps linéaire, orchestré par Dagster et
reproductible via DVC, entièrement exécutable en local via Docker Compose.

```
MovieLens 100K → dlt → DuckDB → dbt → Data Quality → Dagster
   → Scikit-Learn (KNN) → MLflow → DVC → Flask → Streamlit
   → Docker Compose → GitHub Actions (CI) → Monitoring
```

---

## 1. Ingestion — dlt

**Rôle :** extraire les fichiers du dataset MovieLens 100K et les charger dans DuckDB.

- Source : `https://files.grouplens.org/datasets/movielens/ml-100k.zip`
- Fichiers lus : `u.data` (notes), `u.item` (films), `u.user` (utilisateurs)
- Chargement incrémental (`write_disposition="merge"`) avec clés primaires explicites
- **Fallback synthétique** : si le téléchargement échoue (réseau restreint, CI sans
  accès réseau), un jeu de données de même structure est généré automatiquement,
  pour que le pipeline reste exécutable de bout en bout dans n'importe quel
  environnement.
- Destination : DuckDB, schéma `raw` (tables `ratings`, `movies`, `users`)

## 2. Transformation — dbt

**Rôle :** nettoyer, typer et modéliser les données en schéma dimensionnel.

- **Staging** (vues) : `stg_ratings`, `stg_movies`, `stg_users` — renommage,
  typage, nettoyage minimal
- **Marts** (tables) :
  - `dim_movies` — catalogue de films avec genres explosés en tableau
  - `dim_users` — métadonnées démographiques (âge, sexe, profession) + agrégats
    comportementaux (nombre de notes, note moyenne)
  - `fact_ratings` — table de faits, grain = 1 ligne par (utilisateur, film, note)
  - `agg_genre_popularity` — agrégat analytique (popularité et note moyenne par genre)
- **43 tests dbt** : `not_null`, `unique`, `relationships`, `accepted_values`
  (notes entières 1-5), plus 2 tests singuliers (`no_duplicate_ratings`,
  `no_future_ratings`)
- Une macro `generate_schema_name` garantit des noms de schémas stables
  (`raw`, `staging`, `marts`) indépendamment du target dbt utilisé (`dev` ou `ci`)

## 3. Orchestration — Dagster

**Rôle :** orchestrer et superviser l'exécution du pipeline complet.

- 3 assets enchaînés : `dlt_ingestion` → `dbt_transformation` → `ml_training`
- 3 Asset Checks de qualité de données : `no_null_ratings`, `ratings_in_range`
  (1 à 5), `no_volume_drop`
- Un schedule quotidien (02h00) permet une exécution automatique récurrente
- Interface web (port 3000) pour visualiser le graphe d'assets et relancer
  le pipeline manuellement

## 4. Machine Learning — KNN (Scikit-Learn)

**Rôle :** générer des recommandations par filtrage collaboratif.

- **Algorithme :** KNN item-based (`sklearn.neighbors.NearestNeighbors`,
  métrique cosinus), volontairement simple pour rester explicable et rapide
  à entraîner (quelques secondes sur le dataset 100K)
- **Principe :** chaque film est représenté par son vecteur de notes (une ligne
  de la matrice item-utilisateurs). Pour un utilisateur donné, on part de ses
  films les mieux notés (≥ 4/5) et on recommande leurs k plus proches voisins,
  en excluant les films déjà vus.
- **Évaluation :** RMSE, MAE (sur un split train/test 80/20), Precision@10
- **Hyperparamètres** centralisés dans `params.yaml` (`n_neighbors`, `test_size`,
  `random_state`)

## 5. Tracking — MLflow

**Rôle :** suivre les expériences et versionner les modèles.

- Backend de tracking : SQLite local (`mlflow/data/mlflow.db`) — pas de base
  externe, configuration minimale adaptée à un contexte académique
- Chaque run logue : paramètres (`model_type`, `n_neighbors`, ...), métriques
  (`rmse`, `mae`, `precision_at_10`), et l'artefact modèle complet
- Model Registry : le modèle est enregistré sous `movielens-recommender`,
  promotion manuelle possible vers le stage `Production` (`ml/src/promote_model.py`)

## 6. Versioning — DVC

**Rôle :** rendre le pipeline de données et de modèle reproductible.

- `dvc.yaml` définit 3 stages : `ingest` → `transform` → `train`
- `params.yaml` centralise les hyperparamètres (lus à la fois par DVC et par
  `train.py` directement, pour rester utilisable avec ou sans DVC)
- `dvc.lock` capture l'état exact (hash des fichiers, paramètres) de la
  dernière exécution réussie
- Les métriques (`ml/metrics.json`) sont trackées comme `metrics` DVC
  (visibles via `dvc metrics show`), distinctes des gros artefacts cachés
  (modèle `.joblib`)

## 7. API — Flask

**Rôle :** exposer le modèle pour l'inférence, de façon minimale.

- `GET /health` — disponibilité du service et état de chargement du modèle
- `POST /predict` — recommandations pour un utilisateur (`{"user_id": int, "n": int}`)
- `GET /metrics` — métriques Prometheus (requêtes, latence, disponibilité,
  qualité du dernier modèle)
- **Chargement du modèle :** tentative depuis le MLflow Model Registry
  (stage `Production`), avec timeout court et fallback automatique sur le
  modèle local (`ml/models/knn_model.joblib`) si MLflow est indisponible —
  garantit un démarrage rapide de l'API quelle que soit la disponibilité de MLflow.

## 8. Interface — Streamlit

**Rôle :** point d'entrée utilisateur, sans logique métier dupliquée.

- Lit la liste des utilisateurs et les titres de films directement depuis
  DuckDB (lecture seule)
- Délègue entièrement le calcul des recommandations à l'API Flask
  (`POST /predict`) — Streamlit ne réimplémente aucune logique de
  recommandation

## 9. Conteneurisation — Docker / Docker Compose

**Rôle :** rendre le projet exécutable en une seule commande, sur n'importe
quelle machine.

Services orchestrés par `docker-compose.yml` :

| Service | Rôle | Port |
|---|---|---|
| `pipeline-init` | amorce le pipeline complet une fois au démarrage | — |
| `mlflow` | serveur de tracking et registry | 5000 |
| `dagster` | interface d'orchestration | 3000 |
| `api` | service d'inférence Flask | 8000 |
| `streamlit` | interface utilisateur | 8501 |
| `prometheus` | collecte de métriques | 9090 |
| `grafana` | dashboard de monitoring | 3001 |

Le service `pipeline-init` s'exécute une fois (`restart: "no"`) puis se
termine ; l'API attend explicitement sa réussite (`condition:
service_completed_successfully`) avant de démarrer.

## 10. CI — GitHub Actions

**Rôle :** valider automatiquement chaque contribution, sans déploiement.

- Job `lint-and-test` : lint (`ruff`), ingestion dlt, validation de schéma,
  `dbt build`, entraînement du modèle, tests pytest de l'API
- Job `build-check` : build des images Docker (API, Streamlit, Dagster),
  validation de la syntaxe `docker-compose.yml`, démarrage de vérification
  d'un service (`mlflow`) pour confirmer que Docker Compose fonctionne
- **Aucune étape de déploiement** — conforme aux consignes d'un projet
  100% local

## 11. Monitoring — Prometheus & Grafana

**Rôle :** observer la santé du service et la qualité du modèle en production locale.

- Prometheus scrape `GET /metrics` de l'API toutes les 15 secondes
- Métriques exposées : `predict_requests_total` (par statut), `predict_latency_seconds`,
  `model_loaded`, `model_rmse`, `model_precision_at_10`
- Dashboard Grafana provisionné automatiquement au démarrage (pas de
  configuration manuelle requise)
