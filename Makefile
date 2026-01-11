# Storyboard Development Makefile
# This Makefile provides unified commands for development workflow

# Environment variables for pip warnings
export PIP_ROOT_USER_ACTION=ignore
PIP_ENV_VARS = -e PIP_ROOT_USER_ACTION=ignore

.PHONY: help setup dev stop restart test test-api test-web lint lint-api lint-web format format-api format-web db-migrate db-init db-revision db-status db-seed db-reset db-reset-migrations db-connect db-tables db-data clean clean-deep logs logs-api logs-web logs-db status disk-usage docker-cleanup volume-list volume-cleanup volume-cleanup-force

# Default target
help:
	@echo "Storyboard Development Commands:"
	@echo ""
	@echo "Setup and Environment:"
	@echo "  make setup          - 初期環境構築 (Initial environment setup)"
	@echo "  make clean          - 環境クリーンアップ (Environment cleanup)"
	@echo "  make clean-deep     - 徹底的なクリーンアップ (Deep cleanup including node_modules)"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - 開発サーバー起動 (Start development servers in background)"
	@echo "  make stop           - 開発サーバー停止 (Stop development servers)"
	@echo "  make restart        - 開発サーバー再起動 (Restart development servers)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - 全テスト実行 (Run all tests)"
	@echo "  make test-api   - バックエンドテスト (Run api tests)"
	@echo "  make test-web  - フロントエンドテスト (Run web tests)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - コード品質チェック (Run all linting)"
	@echo "  make lint-api   - バックエンドコード品質チェック (Run api linting)"
	@echo "  make lint-web  - フロントエンドコード品質チェック (Run web linting)"
	@echo ""
	@echo "Code Formatting:"
	@echo "  make format         - コードフォーマット (Format all code)"
	@echo "  make format-api - バックエンドコードフォーマット (Format api code)"
	@echo "  make format-web- フロントエンドコードフォーマット (Format web code)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate     - データベースマイグレーション (Run database migrations)"
	@echo "  make db-init        - Alembic初期化 (Initialize Alembic)"
	@echo "  make db-revision    - 新しいマイグレーション作成 (Create new migration)"
	@echo "  make db-status      - データベース状態確認 (Check database status)"
	@echo "  make db-seed        - テストデータ投入 (Seed test data)"
	@echo "  make db-reset       - データベースリセット (Reset database)"
	@echo "  make db-reset-migrations - マイグレーション履歴リセット (Reset migration history)"
	@echo "  make db-connect     - データベースに直接接続 (Connect to database directly)"
	@echo "  make db-tables      - データベース内のテーブル一覧表示 (List database tables)"
	@echo "  make db-data        - データベース内のデータ表示 (Show database data)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make status         - 開発環境状態確認 (Check development environment status)"
	@echo "  make disk-usage     - ディスク容量とDocker使用量確認 (Check disk and Docker usage)"
	@echo "  make docker-cleanup - Docker不要データ削除 (Clean up Docker unused data)"
	@echo "  make volume-list    - Dockerボリューム一覧表示 (List Docker volumes)"
	@echo "  make volume-cleanup - 未使用ボリューム削除 (Remove unused volumes)"
	@echo "  make volume-cleanup-force - 強制ボリューム削除 (Force remove volumes)"
	@echo "  make logs           - 全サービスログ表示 (Show logs for all services)"
	@echo "  make logs-api   - バックエンドログ表示 (Show api logs)"
	@echo "  make logs-web  - フロントエンドログ表示 (Show web logs)"
	@echo "  make logs-db        - データベースログ表示 (Show database logs)"

# 初期環境構築 (Initial environment setup)
setup:
	@echo "🚀 Setting up development environment..."
	@echo "📋 Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Please install Docker first."; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."; exit 1; }
	@echo "✅ Prerequisites check passed"
	@echo "📁 Creating .env file from template..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "✅ .env file created from template"; else echo "ℹ️ .env file already exists"; fi
	@echo "🐳 Building Docker containers..."
	docker-compose build
	@echo "📦 Installing api dependencies..."
	docker-compose run --rm $(PIP_ENV_VARS) api pip install -r requirements.txt
	@echo "📦 Installing web dependencies..."
	docker-compose run --rm web npm install
	@echo "🗄️ Setting up database..."
	$(MAKE) db-migrate
	@echo "🌱 Seeding initial data..."
	$(MAKE) db-seed
	@echo "✅ Setup complete! Run 'make dev' to start development servers."

# 開発サーバー起動 (Start development servers)
dev:
	@echo "🚀 Starting development servers in background..."
	@echo "📊 Backend API will be available at: http://localhost:8000"
	@echo "🌐 Frontend will be available at: http://localhost:3000"
	@echo "🗄️ Database will be available at: localhost:5432"
	@echo ""
	docker-compose up -d
	@echo "✅ All services started in background"
	@echo "📋 Use 'make logs' to view logs"
	@echo "🛑 Use 'make stop' to stop all services"

# 開発サーバー停止 (Stop development servers)
stop:
	@echo "🛑 Stopping development servers..."
	docker-compose stop
	@echo "✅ All services stopped"

# 開発サーバー再起動 (Restart development servers)
restart:
	@echo "🔄 Restarting development servers..."
	docker-compose restart
	@echo "✅ All services restarted"

# 全テスト実行 (Run all tests)
test: test-api test-web
	@echo "✅ All tests completed"

# バックエンドテスト (Run api tests)
test-api:
	@echo "🧪 Running api tests..."
	@if [ -d "api/tests" ]; then \
		docker-compose run --rm api python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-config=.coveragerc; \
	else \
		echo "ℹ️ No tests directory found. Create api/tests/ directory and add test files."; \
	fi

# フロントエンドテスト (Run web tests)
test-web:
	@echo "🧪 Running web tests..."
	docker-compose run --rm web npm test -- --coverage --watchAll=false --passWithNoTests

# コード品質チェック (Run all linting)
lint: lint-api lint-web
	@echo "✅ All linting completed"

# バックエンドコード品質チェック (Run api linting)
lint-api:
	@echo "🔍 Running api linting..."
	@echo "📝 Running flake8..."
	@if [ -d "api/tests" ]; then \
		docker-compose run --rm api flake8 models/ services/ routers/ tests/ config.py database.py manage_db.py main.py; \
	else \
		docker-compose run --rm api flake8 models/ services/ routers/ config.py database.py manage_db.py main.py; \
	fi
	@echo "🔍 Running mypy type checking..."
	docker-compose run --rm api mypy --explicit-package-bases models/ services/ routers/ config.py database.py manage_db.py main.py
	@echo "🛡️ Running bandit security check..."
	docker-compose run --rm api bandit -r models/ services/ routers/ -f json

# フロントエンドコード品質チェック (Run web linting)
lint-web:
	@echo "🔍 Running web linting..."
	@echo "📝 Running ESLint..."
	docker-compose run --rm web npm run lint
	@echo "✅ Web linting completed"
	@echo "ℹ️  Note: TypeScript type checking skipped (compatibility issue with TS 4.9.5)"
	@echo "ℹ️  Run 'npm run type-check' manually if needed (will show node_modules errors)"

# コードフォーマット (Format all code)
format: format-api format-web
	@echo "✅ All code formatting completed"

# バックエンドコードフォーマット (Format api code)
format-api:
	@echo "🎨 Formatting api code..."
	@echo "📝 Running black formatter..."
	@if [ -d "api/tests" ]; then \
		docker-compose run --rm api black models/ services/ routers/ tests/ config.py database.py manage_db.py main.py; \
	else \
		docker-compose run --rm api black models/ services/ routers/ config.py database.py manage_db.py main.py; \
	fi
	@echo "📦 Running isort import sorter..."
	@if [ -d "api/tests" ]; then \
		docker-compose run --rm api isort models/ services/ routers/ tests/ config.py database.py manage_db.py main.py; \
	else \
		docker-compose run --rm api isort models/ services/ routers/ config.py database.py manage_db.py main.py; \
	fi

# フロントエンドコードフォーマット (Format web code)
format-web:
	@echo "🎨 Formatting web code..."
	@echo "📝 Running prettier..."
	docker-compose run --rm web npm run format
	@echo "📝 Running ESLint with --fix..."
	docker-compose run --rm web npm run lint:fix

# データベースマイグレーション (Run database migrations)
db-migrate:
	@echo "🗄️ Running database migrations..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo "🔍 Checking if Alembic is initialized..."
	@if [ ! -f api/alembic.ini ] || [ ! -d api/alembic ]; then \
		echo "📋 Initializing Alembic for the first time..."; \
		docker-compose run --rm api alembic init alembic; \
		echo "⚙️  Configuring Alembic database URL..."; \
		docker-compose run --rm api sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = postgresql://gs_user:gs_password@db:5432/gs_db|g' alembic.ini; \
		echo "ℹ️ Alembic initialized. Creating initial migration..."; \
		docker-compose run --rm api alembic revision --autogenerate -m "Initial migration"; \
	else \
		echo "✅ Alembic already initialized"; \
	fi
	@echo "📊 Running Alembic migrations..."
	@if docker-compose run --rm api alembic current >/dev/null 2>&1; then \
		docker-compose run --rm api alembic upgrade head; \
	else \
		echo "ℹ️ No migrations found. Creating initial migration..."; \
		docker-compose run --rm api alembic revision --autogenerate -m "Initial migration"; \
		docker-compose run --rm api alembic upgrade head; \
	fi
	@echo "✅ Database migrations completed"

# テストデータ投入 (Seed test data)
db-seed:
	@echo "🌱 Seeding test data..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo "📊 Running seed script..."
	docker-compose run --rm api python manage_db.py seed
	@echo "✅ Test data seeding completed"

# データベースリセット (Reset database)
db-reset:
	@echo "🔄 Resetting database..."
	@echo "⚠️ This will delete all data. Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "🛑 Stopping database container..."
	docker-compose stop db
	@echo "🗑️ Removing database volume..."
	docker-compose down -v
	@echo "🚀 Starting fresh database..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=15; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo "📊 Running migrations on fresh database..."
	$(MAKE) db-migrate
	@echo "🌱 Seeding fresh data..."
	$(MAKE) db-seed
	@echo "✅ Database reset completed"

# マイグレーション履歴リセット (Reset migration history)
db-reset-migrations:
	@echo "🔄 Resetting migration history to use unified schema..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $attempt -le $max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $attempt/$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$((attempt + 1)); \
	done; \
	if [ $attempt -gt $max_attempts ]; then \
		echo "❌ Database connection timeout after $max_attempts attempts!"; \
		exit 1; \
	fi
	@echo "🗑️ Dropping existing tables..."
	docker-compose run --rm api python -c "from database import engine; from models.database.base import Base; Base.metadata.drop_all(engine); print('Tables dropped')"
	@echo "📊 Running unified migration..."
	docker-compose run --rm api alembic upgrade head
	@echo "✅ Migration history reset completed"

# Alembic初期化 (Initialize Alembic)
db-init:
	@echo "🔧 Initializing Alembic configuration..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "🔍 Checking existing Alembic setup..."
	@if [ -f api/alembic.ini ] || [ -d api/alembic ]; then \
		echo "⚠️ Alembic already exists. Cleaning up first..."; \
		rm -rf api/alembic api/alembic.ini; \
		echo "🧹 Cleaned up existing Alembic files"; \
	fi
	@echo "📋 Initializing fresh Alembic setup..."
	docker-compose run --rm api alembic init alembic
	@echo "⚙️  Configuring Alembic database URL..."
	docker-compose run --rm api sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = postgresql://gs_user:gs_password@db:5432/gs_db|g' alembic.ini
	@echo "✅ Alembic initialization completed"
	@echo "ℹ️ Next step: Create your first migration with 'make db-revision'"

# 新しいマイグレーション作成 (Create new migration)
db-revision:
	@echo "📝 Creating new database migration..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@if [ ! -f api/alembic.ini ]; then \
		echo "❌ Alembic not initialized. Run 'make db-init' first."; \
		exit 1; \
	fi
	@read -p "Enter migration message: " message; \
	docker-compose run --rm api alembic revision --autogenerate -m "$$message"
	@echo "✅ Migration created successfully"

# Alembicステータス確認 (Check Alembic status)
db-status:
	@echo "📊 Checking database and Alembic status..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db >/dev/null 2>&1
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo ""
	@echo "📋 Alembic Configuration:"
	@if [ -f api/alembic.ini ]; then \
		echo "  ✅ alembic.ini exists"; \
	else \
		echo "  ❌ alembic.ini missing"; \
	fi
	@if [ -d api/alembic ]; then \
		echo "  ✅ alembic directory exists"; \
	else \
		echo "  ❌ alembic directory missing"; \
	fi
	@echo ""
	@echo "📊 Migration Status:"
	@if [ -f api/alembic.ini ] && [ -d api/alembic ]; then \
		docker-compose run --rm api alembic current 2>/dev/null || echo "  ℹ️ No migrations applied yet"; \
		echo ""; \
		echo "📋 Available migrations:"; \
		docker-compose run --rm api alembic history 2>/dev/null || echo "  ℹ️ No migrations created yet"; \
	else \
		echo "  ❌ Alembic not initialized"; \
	fi

# 環境クリーンアップ (Environment cleanup)
clean:
	@echo "🧹 Cleaning up development environment..."
	@echo "🛑 Stopping all containers..."
	docker-compose down
	@echo "🗑️ Removing containers and networks..."
	docker-compose down --remove-orphans
	@echo "🧹 Removing unused Docker images..."
	docker image prune -f
	@echo "🧹 Removing unused Docker volumes..."
	docker volume prune -f
	@echo "🧹 Removing unused Docker networks..."
	docker network prune -f
	@echo "🧹 Cleaning api cache and build artifacts..."
	@find api -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find api -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find api -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find api -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@if [ -f "api/.coverage" ]; then rm -f api/.coverage; fi
	@if [ -d "api/htmlcov" ]; then rm -rf api/htmlcov; fi
	@if [ -d "api/.bandit" ]; then rm -rf api/.bandit; fi
	@if [ -d ".pytest_cache" ]; then rm -rf .pytest_cache; fi
	@echo "🧹 Cleaning web cache and build artifacts..."
	@if [ -d "web/node_modules/.cache" ]; then rm -rf web/node_modules/.cache; fi
	@if [ -d "web/build" ]; then rm -rf web/build; fi
	@if [ -d "web/dist" ]; then rm -rf web/dist; fi
	@if [ -d "web/coverage" ]; then rm -rf web/coverage; fi
	@if [ -f "web/.eslintcache" ]; then rm -f web/.eslintcache; fi
	@echo "🧹 Cleaning system files..."
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# 徹底的なクリーンアップ (Deep cleanup including dependencies)
clean-deep:
	@echo "🧹 Starting deep cleanup..."
	@echo "⚠️  This will remove node_modules and require reinstallation (npm install)"
	@echo "⚠️  Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "🔄 Running standard cleanup first..."
	$(MAKE) clean
	@echo "🧹 Removing node_modules..."
	@if [ -d "web/node_modules" ]; then \
		echo "📦 Removing web/node_modules (this may take a moment)..."; \
		rm -rf web/node_modules; \
		echo "✅ node_modules removed"; \
	else \
		echo "ℹ️  node_modules not found, skipping"; \
	fi
	@echo "🧹 Removing package-lock files..."
	@if [ -f "web/package-lock.json" ]; then rm -f web/package-lock.json; fi
	@echo "✅ Deep cleanup completed"
	@echo "💡 Run 'make setup' or 'npm install' in web/ to reinstall dependencies"

# Development utilities
logs:
	@echo "📋 Showing logs for all services..."
	docker-compose logs -f

logs-api:
	@echo "📋 Showing api logs..."
	docker-compose logs -f api

logs-web:
	@echo "📋 Showing web logs..."
	docker-compose logs -f web

logs-db:
	@echo "📋 Showing database logs..."
	docker-compose logs -f db

# Quick status check
status:
	@echo "📊 Development environment status:"
	@echo ""
	@echo "🐳 Docker containers:"
	@docker-compose ps
	@echo ""
	@echo "🌐 Service connectivity:"
	@echo -n "Backend API: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null && echo " ✅ Responding" || echo " ❌ Not responding"
	@echo -n "Frontend: "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null && echo " ✅ Responding" || echo " ❌ Not responding"
	@echo -n "Database: "
	@docker-compose exec -T db pg_isready -U gs_user 2>/dev/null && echo "✅ Ready" || echo "❌ Not ready"

# ディスク容量とDocker使用量確認 (Check disk and Docker usage)
disk-usage:
	@echo "💾 Disk and Docker usage report:"
	@echo ""
	@echo "🖥️  System disk usage:"
	@df -h | head -1
	@df -h | grep -E "(/$|/System/Volumes/Data)" | head -2
	@echo ""
	@echo "🐳 Docker system usage:"
	@docker system df
	@echo ""
	@echo "📊 Docker detailed breakdown:"
	@echo "Images:"
	@docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | head -10
	@echo ""
	@echo "Containers:"
	@docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" | head -10
	@echo ""
	@echo "Volumes:"
	@docker volume ls --format "table {{.Driver}}\t{{.Name}}" | head -10
	@echo ""
	@echo "💡 Tips:"
	@echo "  - Run 'make docker-cleanup' to free up space"
	@echo "  - Consider removing unused images: docker image prune -a"
	@echo "  - Check large volumes: docker system df -v"

# Docker不要データ削除 (Clean up Docker unused data)
docker-cleanup:
	@echo "🧹 Docker cleanup utility:"
	@echo ""
	@echo "📊 Current Docker usage:"
	@docker system df
	@echo ""
	@echo "📋 Available cleanup options:"
	@echo "  1. Basic cleanup (safe)"
	@echo "     - Stopped containers"
	@echo "     - Unused networks"
	@echo "     - Dangling images"
	@echo "     - Build cache"
	@echo ""
	@echo "  2. Aggressive cleanup (removes unused images)"
	@echo "     - All of the above"
	@echo "     - ALL unused images (not just dangling)"
	@echo ""
	@echo "  3. Volume cleanup (⚠️  DESTRUCTIVE)"
	@echo "     - All of the above"
	@echo "     - ALL unused volumes (including named volumes)"
	@echo "     - ⚠️ This will delete database data if containers are stopped!"
	@echo ""
	@echo "  4. Nuclear cleanup (☢️  VERY DESTRUCTIVE)"
	@echo "     - Everything above"
	@echo "     - Stops all containers first"
	@echo "     - Removes ALL volumes (including active ones)"
	@echo ""
	@read -p "Select cleanup level (1-4) or 'q' to quit: " level; \
	case "$$level" in \
		1) \
			echo "🧹 Starting basic cleanup..."; \
			docker system prune -f; \
			echo "✅ Basic cleanup completed"; \
			;; \
		2) \
			echo "🧹 Starting aggressive cleanup..."; \
			docker system prune -a -f; \
			echo "✅ Aggressive cleanup completed"; \
			;; \
		3) \
			echo "⚠️  Volume cleanup will remove ALL unused volumes!"; \
			echo "This includes database data if containers are stopped."; \
			read -p "Are you absolutely sure? Type 'DELETE' to confirm: " confirm; \
			if [ "$$confirm" = "DELETE" ]; then \
				echo "🧹 Starting volume cleanup..."; \
				docker system prune -a -f; \
				docker volume prune -f; \
				echo "✅ Volume cleanup completed"; \
			else \
				echo "❌ Volume cleanup cancelled"; \
			fi; \
			;; \
		4) \
			echo "☢️  NUCLEAR CLEANUP WARNING!"; \
			echo "This will:"; \
			echo "  - Stop ALL containers"; \
			echo "  - Remove ALL containers"; \
			echo "  - Remove ALL images"; \
			echo "  - Remove ALL volumes (including database data)"; \
			echo "  - Remove ALL networks"; \
			echo "  - Remove ALL build cache"; \
			echo ""; \
			read -p "Type 'NUCLEAR' to confirm this destructive action: " confirm; \
			if [ "$$confirm" = "NUCLEAR" ]; then \
				echo "☢️  Starting nuclear cleanup..."; \
				docker stop $$(docker ps -aq) 2>/dev/null || true; \
				docker system prune -a -f --volumes; \
				echo "✅ Nuclear cleanup completed"; \
			else \
				echo "❌ Nuclear cleanup cancelled"; \
			fi; \
			;; \
		q|Q) \
			echo "❌ Cleanup cancelled"; \
			;; \
		*) \
			echo "❌ Invalid option. Cleanup cancelled"; \
			;; \
	esac; \
	echo ""; \
	echo "📊 Final Docker usage:"; \
	docker system df

# Dockerボリューム一覧表示 (List Docker volumes)
volume-list:
	@echo "📦 Docker volumes report:"
	@echo ""
	@echo "📊 Volume summary:"
	@docker system df | grep -E "(TYPE|Local Volumes)"
	@echo ""
	@echo "📋 All volumes:"
	@docker volume ls --format "table {{.Driver}}\t{{.Name}}\t{{.Scope}}"
	@echo ""
	@echo "🔍 Volume details with sizes:"
	@echo "Name\t\t\t\t\t\tMountpoint\t\t\t\tSize"
	@echo "----\t\t\t\t\t\t----------\t\t\t\t----"
	@for vol in $$(docker volume ls -q); do \
		mountpoint=$$(docker volume inspect $$vol --format '{{.Mountpoint}}' 2>/dev/null || echo "N/A"); \
		if [ "$$mountpoint" != "N/A" ] && [ -d "$$mountpoint" ]; then \
			size=$$(du -sh "$$mountpoint" 2>/dev/null | cut -f1 || echo "N/A"); \
		else \
			size="N/A"; \
		fi; \
		printf "%-40s\t%-30s\t%s\n" "$$vol" "$$mountpoint" "$$size"; \
	done
	@echo ""
	@echo "🔍 Volumes in use by containers:"
	@docker ps -a --format "table {{.Names}}\t{{.Mounts}}" | grep -v "MOUNTS" | while read line; do \
		if echo "$$line" | grep -q "/"; then \
			echo "$$line"; \
		fi; \
	done || echo "No volumes currently mounted"
	@echo ""
	@echo "💡 Tips:"
	@echo "  - Run 'make volume-cleanup' to remove unused volumes"
	@echo "  - Use 'docker volume inspect <name>' for detailed volume info"
	@echo "  - Volumes with 'gs_' prefix are likely project-related"

# 未使用ボリューム削除 (Remove unused volumes)
volume-cleanup:
	@echo "🗑️  Volume cleanup utility:"
	@echo ""
	@echo "📊 Current volume usage:"
	@docker system df | grep -E "(TYPE|Local Volumes)"
	@echo ""
	@echo "📋 Unused volumes that will be removed:"
	@unused_volumes=$$(docker volume ls -q --filter dangling=true); \
	if [ -n "$$unused_volumes" ]; then \
		echo "$$unused_volumes" | while read vol; do \
			mountpoint=$$(docker volume inspect $$vol --format '{{.Mountpoint}}' 2>/dev/null || echo "N/A"); \
			if [ "$$mountpoint" != "N/A" ] && [ -d "$$mountpoint" ]; then \
				size=$$(du -sh "$$mountpoint" 2>/dev/null | cut -f1 || echo "N/A"); \
			else \
				size="N/A"; \
			fi; \
			printf "  - %-40s (Size: %s)\n" "$$vol" "$$size"; \
		done; \
	else \
		echo "  No unused volumes found"; \
	fi
	@echo ""
	@echo "⚠️  WARNING: This will permanently delete unused volumes!"
	@echo "⚠️  Make sure no important data is stored in these volumes."
	@echo ""
	@read -p "Continue with volume cleanup? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "🗑️  Removing unused volumes..."; \
		docker volume prune -f; \
		echo "✅ Volume cleanup completed"; \
		echo ""; \
		echo "📊 Updated volume usage:"; \
		docker system df | grep -E "(TYPE|Local Volumes)"; \
	else \
		echo "❌ Volume cleanup cancelled"; \
	fi

# 強制ボリューム削除 (Force volume cleanup)
volume-cleanup-force:
	@echo "🚀 Running force volume cleanup script..."
	@if [ ! -f "./bin/volume-cleanup-force.sh" ]; then \
		echo "❌ bin/volume-cleanup-force.sh not found"; \
		echo "Please make sure the script exists in the bin directory"; \
		exit 1; \
	fi
	@if [ ! -x "./bin/volume-cleanup-force.sh" ]; then \
		echo "🔧 Making script executable..."; \
		chmod +x ./bin/volume-cleanup-force.sh; \
	fi
	@./bin/volume-cleanup-force.sh

# Install pre-commit hooks
install-hooks:
	@echo "🪝 Installing pre-commit hooks..."
	docker-compose run --rm api pre-commit install
	@echo "✅ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit:
	@echo "🪝 Running pre-commit on all files..."
	docker-compose run --rm api pre-commit run --all-files

# データベース直接接続 (Connect to database directly)
db-connect:
	@echo "🔗 Connecting to database..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db >/dev/null 2>&1
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo "📊 Connecting to PostgreSQL database..."
	@echo "ℹ️  Use \\q to quit, \\dt to list tables, \\d <table> to describe table"
	docker-compose exec db psql -U gs_user -d gs_db

# データベーステーブル一覧表示 (List database tables)
db-tables:
	@echo "📋 Listing database tables..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db >/dev/null 2>&1
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo "📊 Database tables:"
	docker-compose exec -T db psql -U gs_user -d gs_db -c "\dt"
	@echo ""
	@echo "📋 Table details:"
	@for table in inquiries stories; do \
		echo ""; \
		echo "🔍 Table: $$table"; \
		docker-compose exec -T db psql -U gs_user -d gs_db -c "\d $$table" 2>/dev/null || echo "  Table $$table not found"; \
	done

# データベースデータ表示 (Show database data)
db-data:
	@echo "📊 Showing database data..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db >/dev/null 2>&1
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@max_attempts=10; \
	attempt=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if docker-compose run --rm api python manage_db.py check >/dev/null 2>&1; then \
			echo "✅ Database is ready!"; \
			break; \
		fi; \
		echo "   Attempt $$attempt/$$max_attempts - Database not ready, waiting 2s..."; \
		sleep 2; \
		attempt=$$((attempt + 1)); \
	done; \
	if [ $$attempt -gt $$max_attempts ]; then \
		echo "❌ Database connection timeout after $$max_attempts attempts!"; \
		echo "💡 Try running 'make logs-db' to check database logs"; \
		exit 1; \
	fi
	@echo ""
	@echo "📋 Inquiries (問い合わせ):"
	@docker-compose exec -T db psql -U gs_user -d gs_db -c "SELECT id, user_id, LEFT(content, 50) || '...' as content_preview, source_system, status, timestamp FROM inquiries ORDER BY timestamp DESC;" 2>/dev/null || echo "  No inquiries table found"
	@echo ""
	@echo "📋 Stories (ストーリー):"
	@docker-compose exec -T db psql -U gs_user -d gs_db -c "SELECT id, inquiry_id, LEFT(title, 40) || '...' as title_preview, priority, status, estimated_effort, created_at FROM stories ORDER BY created_at DESC;" 2>/dev/null || echo "  No stories table found"
	@echo ""
	@echo "💡 Use 'make db-connect' for interactive database access"
