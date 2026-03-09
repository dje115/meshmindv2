# MeshMind v2 - Task runner

.PHONY: help deps infra-up infra-down full-up control-api web test lint ci

help:
	@echo "MeshMind v2 targets:"
	@echo "  deps        - Install dependencies (Rust, npm, pip)"
	@echo "  infra-up    - Start infra only (Postgres, Redis, Qdrant, Meilisearch)"
	@echo "  full-up     - Start full stack (infra + control-api + web)"
	@echo "  infra-down  - Stop Docker Compose services"
	@echo "  control-api - Build and run control-api"
	@echo "  web         - Run web dev server"
	@echo "  test        - Run all tests"
	@echo "  lint        - Lint Rust and web"
	@echo "  ci          - CI: lint + test"

deps:
	cargo fetch
	cd apps/web && npm install

infra-up:
	docker compose -f infrastructure/docker-compose.infra.yml up -d

full-up:
	docker compose -f infrastructure/docker-compose.yml up -d

infra-down:
	docker compose -f infrastructure/docker-compose.yml down

control-api:
	cargo run -p meshmind-control-api

web:
	cd apps/web && npm run dev

test:
	cargo test -p meshmind-control-api
	cd apps/web && npm run build

lint:
	cargo clippy -p meshmind-control-api
	cd apps/web && npm run lint

ci: lint test
