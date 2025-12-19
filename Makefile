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
test-api:
	@echo ">>> Running Pytest..."
	@echo "-e PYTHONPATH=. でカレントディレクトリ(/app)をパスに追加して実行"
	docker-compose exec -e PYTHONPATH=. api pytest

# --- Code Quality ---
format:
	@echo ">>> Running Black (Formatter)..."
	docker-compose exec api black .
	@echo ">>> Running Isort (Import Sorter)..."
	docker-compose exec api isort .

lint:
	@echo ">>> Running Flake8 (Linter)..."
	docker-compose exec api flake8 .
	@echo ">>> Checking Black..."
	docker-compose exec api black --check .
	@echo ">>> Checking Isort..."
	docker-compose exec api isort --check-only .

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
