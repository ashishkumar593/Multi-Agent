.PHONY: help install test lint format run-api run-ui docker-up docker-down

help:
	@echo "AI Research & Report Agent — Available Commands:"
	@echo "  make install     Install all dependencies via pip"
	@echo "  make test        Execute full pytest test suite"
	@echo "  make lint        Run ruff linter checks"
	@echo "  make format      Auto-format source files"
	@echo "  make run-api     Launch FastAPI REST backend"
	@echo "  make run-ui      Launch Streamlit interactive frontend"
	@echo "  make docker-up   Start all multi-container services"
	@echo "  make docker-down Stop all running Docker services"

install:
	pip install -e .[dev]

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .

run-api:
	python backend/main.py

run-ui:
	streamlit run frontend/app.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
