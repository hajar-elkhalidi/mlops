# Présentation Finale — MovieLens Recommender Platform
### Support de soutenance

---

## Slide 1 — Page de garde
- Titre : Système de Recommandation de Films — Plateforme DataOps/MLOps
- Master d'Excellence en Intelligence Artificielle
- Équipe : Imran, Hamza, Hajar, Abderrahman, Younes, Douae, Abdelkarim, Nohaila
- Encadrants : Prof. Nadia CHAFIQ, Prof. Mohammed AIT DAOUD

---

## Slide 2 — Contexte & Problématique
- Besoin : recommandations personnalisées pertinentes à partir de l'historique de notation
- Défi technique : industrialiser tout le cycle de vie (data → ML → production → monitoring)
- Approche : appliquer les pratiques DataOps/MLOps modernes sur un cas concret (MovieLens)

---

## Slide 3 — Objectifs du projet
1. Pipeline de données fiable, testé et orchestré
2. Modèle de recommandation reproductible et versionné
3. Service d'inférence performant et observable
4. Système entièrement reproductible en local (Docker Compose, une seule commande)

---

## Slide 4 — Architecture Globale
*(Insérer le diagramme : MovieLens 100K → dlt → DuckDB → dbt → Data Quality → Dagster →
Scikit-Learn (KNN) → MLflow → DVC → Flask → Streamlit → Docker → GitHub Actions → Monitoring)*

---

## Slide 5 — Méthodologie Agile/Scrum
- 3 sprints de 2 semaines
- Rôles : Scrum Master (Imran), Product Owner (Hamza), Data Engineers, ML Engineers, Data Analysts
- Backlog Jira : 11 epics, 29 user stories, ~118 story points
- Cérémonies : Daily standup, Sprint Planning, Sprint Review, Rétrospective

---

## Slide 6 — Couche DataOps : Ingestion (dlt)
- Extraction des fichiers MovieLens 100K (`u.data`, `u.item`, `u.user`)
- Chargement incrémental via `merge`/upsert (clé composite)
- Fallback synthétique automatique si le dataset officiel est inaccessible
- Destination : DuckDB, schéma `raw`
- Démo : `python dlt_pipeline/pipeline.py`

---

## Slide 7 — Couche DataOps : Transformation (dbt)
- **Staging** : nettoyage, typage, renommage (`stg_ratings`, `stg_movies`, `stg_users`)
- **Marts** : modèle dimensionnel (`dim_movies`, `dim_users`, `fact_ratings`, `agg_genre_popularity`)
- **Tests** : `unique`, `not_null`, `relationships`, `accepted_values` + 2 tests singuliers
- Résultat : `dbt build` → 43 tests, 100% passants

---

## Slide 8 — Orchestration (Dagster)
- 3 assets : `dlt_ingestion` → `dbt_transformation` → `ml_training`
- Asset Checks : `no_null_ratings`, `ratings_in_range`, `no_volume_drop`
- Schedule quotidien (02h00) — exécution automatique sans intervention manuelle
- Démo : graphe d'assets dans Dagster UI

---

## Slide 9 — Machine Learning
- Algorithme : KNN item-based (`sklearn.neighbors.NearestNeighbors`, similarité cosinus)
- Construction de la matrice creuse user-item, puis item-utilisateurs (scipy)
- Split train/test 80/20
- Métriques : RMSE, MAE, Precision@10
- Choisi pour sa simplicité d'explication : chaque recommandation est traçable
  à un film aimé par l'utilisateur (pas de boîte noire)

---

## Slide 10 — MLflow : Tracking & Registry
- Chaque run logue hyperparamètres (`n_neighbors`, ...) + métriques + artefact modèle
- Model Registry : versioning, comparaison de runs
- Promotion manuelle du meilleur modèle (RMSE minimal) en stage `Production`
  (`ml/src/promote_model.py`)
- Backend SQLite local — configuration minimale, sans dépendance externe
- Démo : MLflow UI — comparaison de runs

---

## Slide 11 — DVC : Versioning du pipeline
- `dvc.yaml` : 3 stages reproductibles (`ingest` → `transform` → `train`)
- `params.yaml` : hyperparamètres centralisés (modifiables sans toucher au code)
- `dvc.lock` : état exact de la dernière exécution (hash, paramètres)
- `dvc metrics show` : comparaison rapide des métriques entre runs
- Démo : `dvc repro` puis `dvc dag`

---

## Slide 12 — API Flask
- `GET /health` → statut du service et du modèle
- `POST /predict` → Top-N films recommandés (`{"user_id": 1, "n": 10}`)
- `GET /metrics` → métriques Prometheus (requêtes, latence, qualité du modèle)
- Chargement du modèle `Production` au démarrage (fallback local si MLflow indisponible,
  fallback "non chargé" si aucun modèle n'existe encore)
- API volontairement minimale (2 routes métier), facile à expliquer en soutenance

---

## Slide 13 — Interface Streamlit
- Sélection d'un utilisateur MovieLens dans une liste déroulante
- Appel direct à l'API Flask (`POST /predict`) — aucune logique dupliquée
- Affichage des films recommandés avec leur score de similarité
- Démo : http://localhost:8501

---

## Slide 14 — Conteneurisation & CI
- Images Docker dédiées : API Flask, Streamlit, MLflow, Dagster
- `docker-compose.yml` : orchestration de 7 services (pipeline-init, mlflow, dagster,
  api, streamlit, prometheus, grafana)
- CI (GitHub Actions) : lint, tests, `dbt build`, build Docker, vérification du
  démarrage de `docker compose` — sur chaque PR
- Aucune étape de déploiement en CI : le projet reste volontairement local

---

## Slide 15 — Exécution 100% locale
- Aucune dépendance cloud : tout tourne sur la machine de l'utilisateur
- Installation en deux commandes : `git clone` puis `docker compose up --build`
- Le service `pipeline-init` exécute automatiquement dlt → dbt → entraînement KNN
  dès le premier démarrage, sans intervention manuelle
- Volumes Docker persistants (`./data`, `./ml`) pour les démarrages suivants

---

## Slide 16 — Monitoring
- Prometheus scrape `/metrics` de l'API Flask (15s)
- Grafana : dashboard provisionné automatiquement (requêtes /predict, latence p95,
  disponibilité, qualité du dernier modèle — RMSE, Precision@10)
- Observabilité de bout en bout : de la donnée brute jusqu'à la requête API, en local

---

## Slide 17 — Démonstration Live
1. `git clone <repo>` puis `docker compose up --build`
2. Le service `pipeline-init` s'exécute automatiquement : ingestion + transformation + entraînement
3. Modèle disponible pour l'API (registry MLflow ou fallback local)
4. Démo via Streamlit (http://localhost:8501) et/ou `curl -X POST http://localhost:8000/predict`
5. Visualisation du dashboard Grafana en temps réel
6. `dvc repro` et `dvc metrics show` pour la reproductibilité

---

## Slide 18 — Résultats & Limites
**Résultats :**
- Pipeline 100% automatisé et reproductible (Dagster + DVC)
- Tests de qualité de données à chaque étage (43 tests dbt)
- Installation et démarrage en une seule commande, sans cloud
- Modèle simple et explicable (KNN), adapté à une soutenance

**Limites identifiées :**
- Dataset MovieLens 100K statique (pas de nouvelles interactions réelles)
- Cold start non géré finement (pas de fallback "Top populaire" implémenté en V1)
- Ressources dépendantes de la machine locale (pas de garantie de performance uniforme)

---

## Slide 19 — Perspectives (V2)
- Gestion du cold start (recommandations basées sur le contenu / popularité)
- Passage à un modèle hybride (collaboratif + content-based)
- Ingestion en quasi temps réel (Kafka / CDC)
- A/B testing de modèles en production via MLflow
- Déploiement cloud optionnel (hors périmètre académique actuel, volontairement limité au local)

---

## Slide 20 — Conclusion
- Projet complet démontrant la maîtrise du cycle DataOps/MLOps de bout en bout
- Application concrète des méthodologies Agile/Scrum en contexte technique
- Stack industrielle reproductible, transposable à d'autres cas d'usage de recommandation

---

## Slide 21 — Questions / Remerciements
- Merci aux encadrants : Prof. Nadia CHAFIQ, Prof. Mohammed AIT DAOUD
- Questions ?
