# Sprint Planning — MovieLens Recommender (3 Sprints × 2 semaines)

## Vue d'ensemble

| Sprint | Durée | Objectif | Story Points |
|---|---|---|---|
| Sprint 1 | Semaines 1-2 | Fondations data : dlt → DuckDB → dbt + tests | 29 |
| Sprint 2 | Semaines 3-4 | Orchestration Dagster + ML + MLflow | 39 |
| Sprint 3 | Semaines 5-6 | API, Docker, CI, exécution locale, Monitoring, Docs | 50 |

**Vélocité moyenne visée :** ~39 points/sprint
**Cérémonies :** Daily standup (15 min), Sprint Planning (début), Sprint Review + Rétrospective (fin)

---

## SPRINT 1 — "Fondations Data" (29 pts)

**Objectif (Sprint Goal) :** Disposer d'un entrepôt DuckDB propre, testé et documenté,
prêt à être consommé par le ML et l'orchestration.

| User Story | Assigné | Points | Statut |
|---|---|---|---|
| US-01 Configurer dlt + source MovieLens | Hajar | 5 | To Do |
| US-02 Chargement incrémental dlt | Abderrahman | 5 | To Do |
| US-03 Validation schéma DuckDB | Hajar | 3 | To Do |
| US-04 Modèles staging dbt | Abderrahman | 5 | To Do |
| US-05 Modèles marts dbt | Hajar | 8 | To Do |
| US-06 Tests dbt | Abderrahman | 5 | To Do |
| US-07 Documentation dbt | Abdelkarim | 3 | To Do |

**Cérémonie de clôture :** Démo du pipeline `dlt run` → `dbt build` → `dbt test` (100% pass).

**Risques Sprint 1 :** Format MovieLens (séparateurs, encodage) — mitigation : tests dlt précoces.

---

## SPRINT 2 — "Orchestration & Intelligence" (39 pts)

**Objectif :** Pipeline orchestré par Dagster de bout en bout, modèle ML entraîné,
évalué et tracé dans MLflow.

| User Story | Assigné | Points | Statut |
|---|---|---|---|
| US-08 Assets Dagster pipeline complet | Hajar | 8 | To Do |
| US-09 Asset Checks qualité données | Abderrahman | 5 | To Do |
| US-10 Schedule quotidien | Imran | 3 | To Do |
| US-11 Matrice user-item | Younes | 5 | To Do |
| US-12 Entraînement modèle KNN | Douae | 8 | To Do |
| US-13 Évaluation modèle | Younes | 5 | To Do |
| US-14 Tracking MLflow | Douae | 5 | To Do |

**Cérémonie de clôture :** Démo Dagster UI (graphe d'assets) + MLflow UI (comparaison de runs).

**Risques Sprint 2 :** Cold start utilisateurs/films — mitigation : fallback "Top populaire".

---

## SPRINT 3 — "Mise en Production Locale" (50 pts)

**Objectif :** Système exécutable entièrement en local via `docker compose up --build`,
accessible via API, monitoré, avec CI et documentation de soutenance.

| User Story | Assigné | Points | Statut |
|---|---|---|---|
| US-15 Model Registry MLflow | Younes | 5 | To Do |
| US-16 Endpoint /recommend | Abdelkarim | 8 | To Do |
| US-17 Endpoints /health /metrics | Nohaila | 3 | To Do |
| US-18 Chargement modèle MLflow dans API | Younes | 5 | To Do |
| US-19 Dockerfile API | Abderrahman | 3 | To Do |
| US-20 Dockerfiles MLflow/Dagster | Hajar | 5 | To Do |
| US-21 docker-compose.yml + pipeline-init | Abderrahman | 5 | To Do |
| US-22 Workflow CI | Imran | 5 | To Do |
| US-23 Build Docker de vérification en CI | Hamza | 8 | To Do |
| US-24 Démarrage en une seule commande | Hamza | 5 | To Do |
| US-25 Documentation de l'exécution locale | Imran | 3 | To Do |
| US-26 Prometheus | Nohaila | 5 | To Do |
| US-27 Dashboard Grafana | Abdelkarim | 5 | To Do |
| US-28 README | Imran | 3 | To Do |
| US-29 Présentation finale | Hamza | 5 | To Do |

**Cérémonie de clôture :** Démo complète — `git clone` → `docker compose up --build` →
pipeline d'amorçage (dlt → dbt → ML) → appel API locale → dashboard Grafana live.

---

## Charge par membre (total des 3 sprints)

| Membre | Rôle | Total points |
|---|---|---|
| Hajar | Data Engineer | 29 |
| Abderrahman | Data Engineer | 28 |
| Younes | ML Engineer | 23 |
| Douae | ML Engineer | 18 |
| Abdelkarim | Data Analyst | 16 |
| Nohaila | Data Analyst | 8 |
| Imran | Scrum Master | 14 |
| Hamza | Product Owner | 18 |

## Definition of Done (DoD)

- [ ] Code revu (PR approuvée par au moins 1 pair)
- [ ] Tests unitaires/dbt passants
- [ ] CI verte
- [ ] Documentation à jour (docstrings + README si impact)
- [ ] Déployé/exécutable localement via Docker
