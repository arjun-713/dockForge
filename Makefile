.PHONY: backend-test frontend-typecheck frontend-lint dev-up dev-down

backend-test:
	cd backend && pytest -v

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-lint:
	cd frontend && npm run lint

dev-up:
	docker compose -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.dev.yml down
