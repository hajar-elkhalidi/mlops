.PHONY: install ingest dbt-build dbt-test train serve streamlit dagster mlflow-ui \
        docker-up docker-down docker-logs test lint clean dvc-repro

install:
	pip install -r requirements.txt
	cd dbt_project && dbt deps

ingest:
	python dlt_pipeline/pipeline.py
	python scripts/validate_schema.py

dbt-build:
	cd dbt_project && dbt build

dbt-test:
	cd dbt_project && dbt test

dbt-docs:
	cd dbt_project && dbt docs generate && dbt docs serve

train:
	python ml/src/train.py --n-neighbors 10

dvc-repro:
	dvc repro

promote:
	python ml/src/promote_model.py

serve:
	cd api && FLASK_APP=app.main flask run --host 0.0.0.0 --port 8000

streamlit:
	cd streamlit_app && streamlit run app.py

dagster:
	cd dagster_project && dagster dev -h 0.0.0.0 -p 3000

mlflow-ui:
	mlflow server --backend-store-uri sqlite:///mlflow/data/mlflow.db \
		--default-artifact-root ./mlflow/artifacts --host 0.0.0.0 --port 5000

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

test:
	pytest tests/ api/tests/ -v

lint:
	ruff check api/app ml/src dlt_pipeline streamlit_app

pipeline-full: ingest dbt-build train
	@echo "Pipeline complet exécuté avec succès."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf dbt_project/target dbt_project/logs
