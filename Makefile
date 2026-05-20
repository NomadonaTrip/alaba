.PHONY: help up down logs ps psql migrate migration backend-shell worker-shell test seed make-admin android-url web-dev clean reset-db build

COMPOSE := docker compose --env-file infra/.env -f infra/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Bring up the full stack
	$(COMPOSE) up -d
	@sh infra/scripts/wait-for-services.sh

down: ## Stop and remove containers (preserves volumes)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

build: ## Rebuild app images (backend-api, backend-worker, web)
	$(COMPOSE) build backend-api backend-worker web

psql: ## Open a psql shell against the dev database
	docker exec -it alaba-postgres psql -U alaba -d alaba

migrate: ## Apply pending Alembic migrations
	docker exec alaba-backend-api alembic upgrade head

migration: ## Create a new migration. Usage: make migration msg="add foo"
	@if [ -z "$(msg)" ]; then echo "Usage: make migration msg=\"description\""; exit 1; fi
	docker exec alaba-backend-api alembic revision --autogenerate -m "$(msg)"

backend-shell: ## Exec into backend-api container
	docker exec -it alaba-backend-api bash

worker-shell: ## Exec into backend-worker container
	docker exec -it alaba-backend-worker bash

test: ## Run backend pytest
	docker exec alaba-backend-api uv run --group dev pytest -v

seed: ## Seed sample films, producers, viewers, licenses (script arrives in Wave 3)
	@echo "make seed is not yet wired. The seed script (infra/scripts/seed_films.py) is created in Wave 3."
	@exit 1

make-admin: ## Bootstrap an admin user (script arrives in Wave 1)
	@echo "make make-admin is not yet wired. The script (infra/scripts/make_admin.py) is created in Wave 1."
	@exit 1

android-url: ## Print the backend URL Android should hit
	@echo "Android emulator → http://10.0.2.2:8000"
	@ip=$$(ip route get 1 2>/dev/null | awk '{print $$7; exit}' || hostname -I | awk '{print $$1}'); \
	  echo "Android real device → http://$$ip:8000"

web-dev: ## Run Next.js dev server locally (alternative to docker)
	cd web && npm run dev

reset-db: ## Drop and recreate the dev database, re-apply migrations
	docker exec alaba-postgres psql -U alaba -c "DROP DATABASE IF EXISTS alaba;"
	docker exec alaba-postgres psql -U alaba -c "CREATE DATABASE alaba;"
	docker exec alaba-backend-api alembic upgrade head

clean: ## Stop everything and DELETE all volumes (data loss!)
	$(COMPOSE) down -v
