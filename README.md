# 🎬 MovieLens Recommender — Plateforme DataOps/MLOps de bout en bout

[![CI](https://github.com/<ORG>/<REPO>/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Système de recommandation de films basé sur le dataset **MovieLens 100K**, construit avec
une stack DataOps/MLOps complète : **dlt → DuckDB → dbt → Dagster → Scikit-Learn (KNN) →
MLflow → DVC → Flask → Streamlit → Docker → GitHub Actions → Monitoring**, **entièrement
exécutable en local via Docker Compose, en une seule commande**.

Projet réalisé dans le cadre du Master d'Excellence en Intelligence Artificielle.

---

## 📐 Architecture

```
MovieLens 100K (u.data, u.item, u.user)
   │
   ▼
  dlt  ───────────────►  DuckDB (raw : ratings, movies, users)
                            │
                            ▼
                           dbt  ──► staging ──► marts (dim_movies, dim_users, fact_ratings)
                            │
                            ▼
                     Data Quality (43 tests dbt + Dagster Asset Checks)
                            │
                            ▼
                        Dagster (orchestration : assets, schedule quotidien)
                            │
                            ▼
                   Scikit-Learn — KNN item-based (similarité cosinus)
                            │
                            ▼
                         MLflow (tracking : params, métriques, modèle)
                            │
                            ▼
                          DVC (versioning : dataset, modèle, métriques)
                            │
                            ▼
                     Flask (GET /health, POST /predict, GET /metrics)
                            │
                            ▼
                  Streamlit (interface utilisateur, consomme l'API Flask)
                            │
                            ▼
                    Docker / docker-compose (un seul `up --build`)
                            │
                            ▼
              GitHub Actions (CI : lint + tests + dbt build + build Docker)
                            │
                            ▼
                Monitoring (Prometheus + Grafana)
```

**Principe directeur :** chaque brique est volontairement la plus simple possible
(KNN plutôt qu'un modèle profond, dataset 100K plutôt que 1M/25M, API à 2 routes,
SQLite pour MLflow) — pour rester rapide à exécuter et facile à expliquer en
soutenance, tout en couvrant un cycle DataOps/MLOps complet.

---

## 🗂️ Structure du repository

```
movielens-reco/
├── .github/workflows/        # CI uniquement (ci.yml) — aucun déploiement automatique
├── dlt_pipeline/              # Extraction MovieLens 100K -> DuckDB (raw)
│   ├── movielens_source.py     # lecture u.data / u.item / u.user (+ fallback synthétique)
│   ├── pipeline.py
│   └── .dlt/config.toml
├── dbt_project/                # Transformation : staging + marts + tests
│   ├── models/staging/         # stg_ratings, stg_movies, stg_users
│   ├── models/marts/           # dim_movies, dim_users, fact_ratings, agg_genre_popularity
│   ├── macros/                 # generate_schema_name (schémas stables : raw/staging/marts)
│   ├── tests/                  # tests singuliers (no_duplicate_ratings, no_future_ratings)
│   └── dbt_project.yml, profiles.yml, packages.yml
├── dagster_project/            # Orchestration complète du pipeline
│   └── movielens_dagster/
│       ├── assets/              # dlt_ingestion, dbt_transformation, ml_training
│       ├── checks/              # Asset Checks qualité de données
│       ├── jobs/                 # job complet + schedule quotidien
│       └── definitions.py
├── ml/                            # Machine Learning
│   ├── src/                     # build_matrix, train (KNN), evaluate, recommend, promote_model
│   ├── models/                  # modèle sérialisé (knn_model.joblib, géré par DVC)
│   └── metrics.json             # métriques du dernier entraînement (géré par DVC)
├── mlflow/                     # Dockerfile serveur MLflow (SQLite local, config minimale)
├── api/                          # Service Flask
│   ├── app/
│   │   ├── main.py              # GET /health, POST /predict, GET /metrics
│   │   └── core/                # model_loader.py (MLflow Registry + fallback local)
│   └── tests/
├── streamlit_app/              # Interface utilisateur (consomme l'API Flask)
│   ├── app.py
│   └── requirements.txt
├── docker/                    # Dockerfiles individuels (API, Streamlit, Dagster)
├── docker-compose.yml         # Orchestration complète des conteneurs (100% local)
├── dvc.yaml                   # Pipeline DVC (ingest -> transform -> train)
├── dvc.lock                    # État résolu du pipeline DVC (généré par `dvc repro`)
├── params.yaml                  # Hyperparamètres centralisés (lus par dvc.yaml et train.py)
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/                 # provisioning + dashboard (requêtes, latence, métriques ML)
├── jira/                          # Backlog, user stories, sprint planning
├── docs/                         # Vision du projet, présentation
├── tests/                       # Tests unitaires et d'intégration
├── scripts/                     # Utilitaires (validate_schema.py)
├── Makefile
├── requirements.txt
└── README.md
```

---

## 👥 Équipe & Rôles

| Rôle | Membres | Responsabilités |
|---|---|---|
| Agile (Scrum Master / PO) | Imran, Hamza | Backlog Jira, sprints, vision, CI, Docker Compose |
| Data Engineers | Hajar, Abderrahman | dlt, DuckDB, dbt, Dagster, Data Quality, DVC |
| ML Engineers | Younes, Douae | Scikit-Learn (KNN), MLflow, évaluation modèle |
| Data Analysts | Abdelkarim, Nohaila | Marts analytiques, API, Streamlit, monitoring, présentation |

---

## 🚀 Guide d'installation

### Prérequis
- Docker & Docker Compose
- `git`

C'est tout. Aucun compte cloud, aucune dépendance externe à provisionner.

### Installation et lancement

```bash
git clone <URL_DU_REPO>
cd movielens-reco
docker compose up --build
```

Cette seule commande :
1. Construit toutes les images (API Flask, Streamlit, Dagster, MLflow)
2. Exécute automatiquement le pipeline d'amorçage (`pipeline-init`) :
   ingestion `dlt` (MovieLens 100K) → transformation `dbt` (staging + marts + 43 tests)
   → entraînement du modèle KNN
3. Démarre l'API Flask (avec le modèle entraîné), l'interface Streamlit, MLflow,
   Dagster, Prometheus et Grafana

Au premier démarrage, le pipeline d'amorçage prend de une à quelques minutes
(téléchargement du dataset MovieLens 100K, build dbt, entraînement KNN — volontairement
rapide). Les démarrages suivants sont plus rapides grâce aux volumes Docker persistants
(`./data`, `./ml`).

```bash
docker compose up --build -d     # lancer en arrière-plan
docker compose down              # arrêter
docker compose down -v           # tout réinitialiser (y compris les données)
```

| Service | URL |
|---|---|
| **Interface Streamlit** | http://localhost:8501 |
| API Flask | http://localhost:8000 |
| Dagster UI | http://localhost:3000 |
| MLflow UI | http://localhost:5000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/admin) |

### Installation locale sans Docker (développement)

```bash
make install          # installe toutes les dépendances + dbt deps
make ingest           # dlt : MovieLens 100K -> DuckDB (raw)
make dbt-build        # dbt : staging + marts + tests
make train            # entraîne le modèle KNN (+ MLflow si serveur lancé)
make serve            # lance l'API Flask sur http://localhost:8000
```

---

## 📖 Guide d'utilisation

### Via l'interface Streamlit (recommandé)

1. Ouvrir http://localhost:8501
2. Choisir un utilisateur MovieLens dans la liste déroulante
3. Choisir le nombre de recommandations souhaitées
4. Cliquer sur **"Obtenir des recommandations"**
5. Les films recommandés s'affichent avec leur score de similarité

### Via l'API Flask directement

```bash
# Vérifier que le service est opérationnel
curl http://localhost:8000/health

# Demander des recommandations pour l'utilisateur 1
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "n": 5}'

# Consulter les métriques (format Prometheus)
curl http://localhost:8000/metrics
```

Réponse attendue de `/predict` :
```json
{
  "user_id": 1,
  "recommendations": [
    {"movie_id": 144, "score": 0.51},
    {"movie_id": 114, "score": 0.30}
  ]
}
```

### Relancer le pipeline manuellement (Dagster)

Le pipeline tourne une fois automatiquement au démarrage. Pour le relancer
(nouvelles données, nouvel entraînement) sans tout redémarrer :

1. Ouvrir http://localhost:3000 (Dagster UI)
2. Lancer le job `movielens_pipeline_job`
3. Vérifier les Asset Checks (qualité de données) dans l'onglet "Asset Checks"

### Relancer le pipeline via DVC (reproductibilité)

```bash
dvc repro          # rejoue ingest -> transform -> train si une dépendance a changé
dvc metrics show   # affiche RMSE / MAE / Precision@10 du dernier entraînement
dvc dag            # affiche le graphe de dépendances du pipeline
```

Modifier un hyperparamètre (ex. nombre de voisins KNN) se fait dans `params.yaml`,
puis `dvc repro` ne rejoue que les étapes impactées.

---

## 🧪 Tests

```bash
make test     # pytest sur tests/ et api/tests/
make lint     # ruff
make dbt-test # tests dbt (unique, not_null, relationships, accepted_values)
```

---

## 🔄 Intégration Continue (CI)

- **CI** (`.github/workflows/ci.yml`) : à chaque PR — installation des dépendances,
  lint, tests, ingestion dlt, `dbt build`, entraînement du modèle, tests pytest de
  l'API, build des images Docker (API, Streamlit, Dagster), et vérification que
  `docker compose` démarre correctement.
- **Aucun déploiement automatique** : le projet reste volontairement local, conformément
  aux consignes académiques.

---

## 📊 Monitoring

- **Prometheus** scrape `/metrics` de l'API Flask toutes les 15 secondes.
- **Grafana** affiche un dashboard provisionné automatiquement avec :
  - taux de requêtes `/predict` (par code de statut)
  - latence p95 de `/predict`
  - nombre total de prédictions servies
  - disponibilité du service et du modèle (`model_loaded`)
  - qualité du dernier modèle entraîné (RMSE, Precision@10, lus depuis `ml/metrics.json`)

---

## 🗃️ Versioning des données et modèles (DVC)

Le pipeline DVC (`dvc.yaml`) définit 3 étapes reproductibles :

| Étape | Commande | Dépend de | Produit |
|---|---|---|---|
| `ingest` | `python dlt_pipeline/pipeline.py` | scripts dlt | `data/duckdb/movielens.duckdb` |
| `transform` | `dbt build` | base DuckDB, modèles dbt | schémas staging/marts |
| `train` | `python ml/src/train.py` | base transformée | `ml/models/knn_model.joblib`, `ml/metrics.json` |

```bash
dvc repro     # exécute le pipeline complet (ou seulement les étapes modifiées)
```

`dvc.lock` capture l'état exact (hash des dépendances, paramètres utilisés) de la
dernière exécution réussie, garantissant la reproductibilité.

---

## 📋 Gestion de projet (Agile/Scrum)

- [`jira/backlog.csv`](jira/backlog.csv) — backlog complet importable dans Jira
- [`jira/user_stories.md`](jira/user_stories.md) — user stories détaillées avec critères d'acceptation
- [`jira/sprint_planning.md`](jira/sprint_planning.md) — planning sur 3 sprints
- [`docs/vision.md`](docs/vision.md) — vision du projet
- [`docs/architecture.md`](docs/architecture.md) — détail de l'architecture technique

---

## 📈 Modèle de recommandation

**Algorithme :** KNN item-based (`sklearn.neighbors.NearestNeighbors`, similarité cosinus).

**Principe :** chaque film est représenté par son vecteur de notes (profil de notation
par tous les utilisateurs). Pour recommander des films à un utilisateur, on identifie
les films qu'il a le mieux notés (≥ 4/5), puis on propose leurs voisins les plus proches
(films notés de façon similaire par les autres utilisateurs), en excluant les films déjà vus.

Choisi pour sa simplicité d'implémentation et d'explication (pas de boîte noire :
chaque recommandation est directement traçable à un film aimé par l'utilisateur),
adapté à une démonstration en soutenance universitaire.

| Métrique (dataset 100K réel) | Ordre de grandeur attendu |
|---|---|
| RMSE | ~1.0 |
| MAE | ~0.8 |
| Precision@10 | variable selon `n_neighbors` |

*(Les métriques exactes dépendent du dataset réellement téléchargé et de `params.yaml` —
voir `dvc metrics show` ou `mlflow ui` pour les valeurs du dernier run.)*

---

## 📄 Licence

Projet académique — Master d'Excellence en Intelligence Artificielle.
