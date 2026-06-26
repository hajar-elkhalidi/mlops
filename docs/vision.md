# Vision du Projet — MovieLens Recommender Platform

## 1. Contexte

Construire une plateforme de recommandation de films de bout en bout, depuis
l'ingestion des données brutes MovieLens jusqu'au service d'inférence en
production, en appliquant les pratiques DataOps / MLOps modernes.

## 2. Problème

Les utilisateurs d'une plateforme de streaming fictive ("MovieLensFlix") ont
besoin de recommandations personnalisées pertinentes basées sur leur historique
de notation, sans pipeline manuel ni modèle non versionné.

## 3. Objectif produit

Fournir une API de recommandation (`/recommend/{user_id}`) qui retourne le
Top-N de films recommandés, alimentée par un pipeline de données automatisé,
orchestré, testé, monitoré, et un modèle ML versionné et reproductible.

## 4. Périmètre (Scope)

**Inclus :**
- Ingestion du dataset MovieLens 100K (`ml-100k`) via `dlt`
- Stockage analytique dans `DuckDB`
- Transformation et modélisation dimensionnelle via `dbt`
- Tests de qualité de données (`dbt tests` + Dagster Asset Checks)
- Orchestration complète via `Dagster`
- Entraînement d'un modèle de filtrage collaboratif KNN (`Scikit-Learn`)
- Tracking et registry de modèles (`MLflow`)
- Versioning des données, modèles et métriques (`DVC`)
- Service d'inférence (`Flask`)
- Interface utilisateur (`Streamlit`)
- Conteneurisation (`Docker` / `docker-compose`)
- Intégration continue (`GitHub Actions`)
- Exécution entièrement locale via `Docker Compose` (`git clone` + `docker compose up --build`)
- Monitoring (`Prometheus` + `Grafana`)

**Exclus (hors périmètre) :**
- Authentification utilisateur avancée (OAuth complet)
- Système de paiement
- Recommandations en temps réel (streaming Kafka) — V2
- Déploiement cloud (le projet est volontairement limité à une exécution locale)

## 5. Valeur métier

| Bénéfice | Description |
|---|---|
| Reproductibilité | Pipeline versionné, idempotent, rejouable |
| Qualité | Tests automatisés à chaque étage (raw → staging → marts) |
| Traçabilité ML | Chaque modèle est tracé, versionné, comparable (MLflow) |
| Time-to-production | CI/CD automatisé du commit au déploiement |
| Observabilité | Dashboards de latence API et dérive de données |

## 6. Parties prenantes

| Rôle | Nom(s) |
|---|---|
| Scrum Master | Imran |
| Product Owner | Hamza |
| Data Engineers | Hajar, Abderrahman |
| ML Engineers | Younes, Douae |
| Data Analysts | Abdelkarim, Nohaila |

## 7. Indicateurs de succès (KPIs)

- Pipeline Dagster exécutable de bout en bout sans intervention manuelle
- Couverture de tests dbt ≥ 90% des colonnes critiques
- RMSE du modèle de recommandation < 1.0 sur le jeu de test MovieLens
- API répondant en < 200ms (p95) en local
- CI verte sur 100% des PRs avant merge sur `main`
- Déploiement local reproductible en une seule commande (`docker compose up --build`)

## 8. Architecture cible (résumé)

```
MovieLens 100K → dlt → DuckDB → dbt → Data Quality → Dagster
   → Scikit-Learn (KNN) → MLflow → DVC → Flask → Streamlit
   → Docker Compose (local) → Monitoring
```

## 9. Risques identifiés

| Risque | Mitigation |
|---|---|
| Limite de ressources de la machine locale (CPU/RAM variables selon le poste) | Modèles légers, DuckDB (pas de cluster), images Docker optimisées |
| Dataset MovieLens figé (pas de nouvelles données) | Simulation d'incréments via partitionnement par timestamp |
| Dérive de schéma dlt | Tests dbt `not_null` / `unique` + schema contracts dlt |
