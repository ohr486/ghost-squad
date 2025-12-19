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
	# -e PYTHONPATH=. でカレントディレクトリ(/app)をパスに追加して実行
	@echo ">>> Running Pytest..."
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
	docker-compose down -v
	docker system prune -f
