.PHONY: help dev down clean migrate seed test lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services (Docker Compose)
	@cp -n .env.example .env 2>/dev/null || true
	docker compose up -d
	@echo "✅  Services started"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost:8000/docs"
	@echo "   Neo4j:     http://localhost:7474"
	@echo "   Flower:    http://localhost:5555"

down: ## Stop all services
	docker compose down

clean: ## Remove all containers, volumes, and images
	docker compose down -v --remove-orphans

logs: ## Follow logs for all services
	docker compose logs -f

logs-backend: ## Follow backend logs
	docker compose logs -f backend

logs-worker: ## Follow worker logs
	docker compose logs -f worker

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

seed: ## Seed database with sample data
	docker compose exec backend python scripts/seed.py

test-backend: ## Run backend tests
	docker compose exec backend pytest tests/ -v --cov=. --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm run test

lint-backend: ## Lint backend
	docker compose exec backend ruff check . && mypy .

lint-frontend: ## Lint frontend
	cd frontend && npm run lint

shell-backend: ## Open Python shell in backend container
	docker compose exec backend python

shell-db: ## Open psql shell
	docker compose exec postgres psql -U mentor -d ai_mentor

shell-neo4j: ## Open Neo4j Cypher shell
	docker compose exec neo4j cypher-shell -u neo4j -p mentor_password

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

build: ## Build production Docker images
	docker compose build

restart-backend: ## Restart only the backend + worker
	docker compose restart backend worker

status: ## Show running container status
	docker compose ps
