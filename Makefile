PY ?= .venv/bin/python
COMPOSE ?= docker compose

.PHONY: help up up-host-ollama down setup db corpus ingest api test lint eval eval-retrieval report web

help:  ## Show targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-16s %s\n", $$1, $$2}'

up:  ## Run the whole stack in Docker (UI :8080, API :8000)
	$(COMPOSE) up --build -d

up-host-ollama:  ## Same, but use the Ollama already running on this machine
	$(COMPOSE) -f docker-compose.yml -f docker-compose.host-ollama.yml up --build -d

down:  ## Stop the stack
	$(COMPOSE) down

setup:  ## Create the local Python venv and install backend deps
	python3 -m venv .venv
	$(PY) -m pip install -r backend/requirements-dev.txt

db:  ## Start only PostgreSQL+pgvector (for local development)
	$(COMPOSE) up -d db

corpus:  ## Re-download the sources and rebuild data/corpus/*.jsonl
	cd backend && ../$(PY) -m app.ingestion download && ../$(PY) -m app.ingestion build

ingest:  ## Chunk + embed the corpus into PostgreSQL
	cd backend && ../$(PY) -m app.ingestion ingest --reset

api:  ## Run the API locally with auto-reload
	cd backend && ../$(PY) -m uvicorn app.main:app --reload --port 8000

test:  ## Backend + Flutter tests
	cd backend && ../$(PY) -m pytest -q
	cd frontend/flutter_app && flutter test

lint:
	cd backend && ../$(PY) -m ruff check . && ../$(PY) -m ruff format --check .
	cd frontend/flutter_app && flutter analyze

eval:  ## Full benchmark (retrieval + generation + judge); slow on CPU
	cd backend && ../$(PY) -m app.evaluation
	$(PY) evaluation/generate_report.py

eval-retrieval:  ## Retrieval-only benchmark (no LLM, ~2 min)
	cd backend && ../$(PY) -m app.evaluation --retrieval-only

report:  ## Refresh README table + evaluation/results/report.md from latest.json
	$(PY) evaluation/generate_report.py

web:  ## Run the Flutter app against the local API
	cd frontend/flutter_app && flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
