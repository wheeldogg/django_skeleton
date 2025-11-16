.PHONY: help install migrate createsuperuser run test lint format clean docker-build docker-up docker-down

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

migrate: ## Run database migrations
	poetry run python manage.py migrate

makemigrations: ## Create new migrations
	poetry run python manage.py makemigrations

createsuperuser: ## Create a superuser account
	poetry run python manage.py createsuperuser

run: ## Run the development server
	poetry run python manage.py runserver

shell: ## Open Django shell
	poetry run python manage.py shell

test: ## Run tests with pytest
	poetry run pytest

lint: ## Run code linting
	poetry run flake8 .
	poetry run mypy .

format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

collectstatic: ## Collect static files
	poetry run python manage.py collectstatic --noinput

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# Docker commands
docker-build: ## Build Docker containers
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in web container
	docker-compose exec web bash

docker-migrate: ## Run migrations in Docker
	docker-compose exec web python manage.py migrate

docker-createsuperuser: ## Create superuser in Docker
	docker-compose exec web python manage.py createsuperuser

docker-collectstatic: ## Collect static files in Docker
	docker-compose exec web python manage.py collectstatic --noinput

# Production Docker commands
prod-build: ## Build production Docker containers
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production Docker containers
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production Docker containers
	docker-compose -f docker-compose.prod.yml down