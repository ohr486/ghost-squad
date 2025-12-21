.PHONY: db-reset

# --- Docker Control ---
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

restart:
	docker-compose down && docker-compose up -d

# --- Component Specific ---
cli:
	docker-compose run --rm cli

api-logs:
	docker-compose logs -f api

web-logs:
	docker-compose logs -f web

# --- Testing ---
test:
	@echo "\n=== 🧪 TESTING API (Backend) ==="
	$(MAKE) test-api
	@echo "\n=== 🧪 TESTING WEB (Frontend) ==="
	$(MAKE) test-web
	@echo "\n>>> 🎉 ALL SYSTEMS GO! Tests Completed."

test-api:
	@echo "-e PYTHONPATH=. でカレントディレクトリ(/app)をパスに追加して実行"
	docker-compose exec -T -e PYTHONPATH=. api pytest

test-web:
	docker-compose exec web npm test

# --- Code Quality ---
format:
	@echo ">>> 🎨 Formatting API (Black/Isort)..."
	docker-compose exec api black .
	docker-compose exec api isort .
	# Frontendの自動整形も入れたい場合はここに Prettier などを追加可能

lint:
	@echo "\n=== 🧹 LINTING API (Backend) ==="
	$(MAKE) lint-api
	@echo "\n=== 🧹 LINTING WEB (Frontend) ==="
	$(MAKE) lint-web
	@echo "\n>>> ✨ All code looks shiny! No issues found."

lint-api:
	@echo ">>> Running Flake8..."
	docker-compose exec api flake8 .
	@echo ">>> Checking Black..."
	docker-compose exec api black --check .
	@echo ">>> Checking Isort..."
	docker-compose exec api isort --check-only .

lint-web:
	# Next.js 標準の ESLint を実行
	docker-compose exec web npm run lint

# --- DB reset ---
db-reset:
	@echo "🧨 Stopping containers and removing volumes (DB Reset)..."
	docker compose down -v
	@echo "🚀 Restarting containers..."
	docker compose up -d
	@echo "⏳ Waiting for API to be ready..."
	@sleep 5
	@echo "✅ DB Reset Complete! You can now send requests."

# --- DB attach ---
db:
	docker compose exec db psql -U ghost -d ghost_memory

dbe:
	docker compose exec db psql -U ghost -d ghost_memory -c '$(Q)'

# --- Cleaning ---
clean:
	@echo ">>> [1/5] Stopping and removing containers/volumes..."
	docker-compose down -v

	@echo ">>> [2/5] Cleaning Python cache (__pycache__, .pytest_cache)..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

	@echo ">>> [3/5] Cleaning Node.js (node_modules, .next)..."
	rm -rf apps/web/node_modules
	rm -rf apps/web/.next

	@echo ">>> [4/5] Cleaning CLI binary..."
	rm -f apps/cli/gs

	@echo ">>> [5/5] Pruning Docker system (removing unused images/networks)..."
	docker system prune -f

	@echo ">>> ✨ All clean! System reset complete."
