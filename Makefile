# Makefile for common development tasks
# See .pre-commit-config.yaml for pre-commit hook configuration
.PHONY: help install install-dev run test lint format migrate clean docker-up docker-down

help:
	@echo "LogPulse Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install         - Install production dependencies"
	@echo "  make install-dev     - Install development dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run             - Run FastAPI development server"
	@echo "  make run-celery      - Run Celery worker"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            - Run code linting (Ruff + MyPy)"
	@echo "  make format          - Format code with Black/Ruff"
	@echo "  make test            - Run all tests with coverage"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         - Run database migrations"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up       - Start all services with Docker Compose"
	@echo "  make docker-down     - Stop all services"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove temporary files and caches"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn app:app --reload --host 0.0.0.0 --port 8000

run-celery:
	celery -A app.tasks worker --loglevel=info

lint:
	ruff check app/
	mypy app/

format:
	ruff format app/
	black app/

test:
	pytest --cov=app --cov-report=html

migrate:
	alembic upgrade head

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.mypy_cache' -delete
	rm -rf htmlcov/
	rm -f .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f app
