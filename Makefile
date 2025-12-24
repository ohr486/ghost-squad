# Storyboard Development Makefile
# This Makefile provides unified commands for development workflow

# Environment variables for pip warnings
export PIP_ROOT_USER_ACTION=ignore
PIP_ENV_VARS = -e PIP_ROOT_USER_ACTION=ignore

.PHONY: help setup dev stop restart test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend db-migrate db-init db-revision db-status db-seed db-reset clean logs logs-backend logs-frontend logs-db status disk-usage docker-cleanup volume-list volume-cleanup volume-cleanup-force

# Default target
help:
	@echo "Storyboard Development Commands:"
	@echo ""
	@echo "Setup and Environment:"
	@echo "  make setup          - 初期環境構築 (Initial environment setup)"
	@echo "  make clean          - 環境クリーンアップ (Environment cleanup)"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - 開発サーバー起動 (Start development servers in background)"
	@echo "  make stop           - 開発サーバー停止 (Stop development servers)"
	@echo "  make restart        - 開発サーバー再起動 (Restart development servers)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - 全テスト実行 (Run all tests)"
	@echo "  make test-backend   - バックエンドテスト (Run backend tests)"
	@echo "  make test-frontend  - フロントエンドテスト (Run frontend tests)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - コード品質チェック (Run all linting)"
	@echo "  make lint-backend   - バックエンドコード品質チェック (Run backend linting)"
	@echo "  make lint-frontend  - フロントエンドコード品質チェック (Run frontend linting)"
	@echo ""
	@echo "Code Formatting:"
	@echo "  make format         - コードフォーマット (Format all code)"
	@echo "  make format-backend - バックエンドコードフォーマット (Format backend code)"
	@echo "  make format-frontend- フロントエンドコードフォーマット (Format frontend code)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate     - データベースマイグレーション (Run database migrations)"
	@echo "  make db-init        - Alembic初期化 (Initialize Alembic)"
	@echo "  make db-revision    - 新しいマイグレーション作成 (Create new migration)"
	@echo "  make db-status      - データベース状態確認 (Check database status)"
	@echo "  make db-seed        - テストデータ投入 (Seed test data)"
	@echo "  make db-reset       - データベースリセット (Reset database)"
	@echo ""
	@echo "Monitoring:"
	@echo "  make status         - 開発環境状態確認 (Check development environment status)"
	@echo "  make disk-usage     - ディスク容量とDocker使用量確認 (Check disk and Docker usage)"
	@echo "  make docker-cleanup - Docker不要データ削除 (Clean up Docker unused data)"
	@echo "  make volume-list    - Dockerボリューム一覧表示 (List Docker volumes)"
	@echo "  make volume-cleanup - 未使用ボリューム削除 (Remove unused volumes)"
	@echo "  make volume-cleanup-force - 強制ボリューム削除 (Force remove volumes)"
	@echo "  make logs           - 全サービスログ表示 (Show logs for all services)"
	@echo "  make logs-backend   - バックエンドログ表示 (Show backend logs)"
	@echo "  make logs-frontend  - フロントエンドログ表示 (Show frontend logs)"
	@echo "  make logs-db        - データベースログ表示 (Show database logs)"

# 初期環境構築 (Initial environment setup)
setup:
	@echo "🚀 Setting up development environment..."
	@echo "📋 Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Please install Docker first."; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."; exit 1; }
	@echo "✅ Prerequisites check passed"
	@echo "📁 Creating .env file from template..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "✅ .env file created from template"; else echo "ℹ️  .env file already exists"; fi
	@echo "🐳 Building Docker containers..."
	docker-compose build
	@echo "📦 Installing backend dependencies..."
	docker-compose run --rm $(PIP_ENV_VARS) backend pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	docker-compose run --rm frontend npm install
	@echo "🗄️  Setting up database..."
	$(MAKE) db-migrate
	@echo "🌱 Seeding initial data..."
	$(MAKE) db-seed
	@echo "✅ Setup complete! Run 'make dev' to start development servers."

# 開発サーバー起動 (Start development servers)
dev:
	@echo "🚀 Starting development servers in background..."
	@echo "📊 Backend API will be available at: http://localhost:8000"
	@echo "🌐 Frontend will be available at: http://localhost:3000"
	@echo "🗄️  Database will be available at: localhost:5432"
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
test: test-backend test-frontend
	@echo "✅ All tests completed"

# バックエンドテスト (Run backend tests)
test-backend:
	@echo "🧪 Running backend tests..."
	@if [ -d "backend/tests" ]; then \
		docker-compose run --rm backend python -m pytest tests/ -v --cov=models --cov-report=term-missing --cov-report=html; \
	else \
		echo "ℹ️  No tests directory found. Create backend/tests/ directory and add test files."; \
	fi

# フロントエンドテスト (Run frontend tests)
test-frontend:
	@echo "🧪 Running frontend tests..."
	docker-compose run --rm frontend npm test -- --coverage --watchAll=false --passWithNoTests

# コード品質チェック (Run all linting)
lint: lint-backend lint-frontend
	@echo "✅ All linting completed"

# バックエンドコード品質チェック (Run backend linting)
lint-backend:
	@echo "🔍 Running backend linting..."
	@echo "📝 Running flake8..."
	@if [ -d "backend/tests" ]; then \
		docker-compose run --rm backend flake8 models/ main.py tests/; \
	else \
		docker-compose run --rm backend flake8 models/ main.py; \
	fi
	@echo "🔍 Running mypy type checking..."
	docker-compose run --rm backend mypy models/ main.py
	@echo "🛡️  Running bandit security check..."
	docker-compose run --rm backend bandit -r models/ -f json

# フロントエンドコード品質チェック (Run frontend linting)
lint-frontend:
	@echo "🔍 Running frontend linting..."
	@echo "📝 Running ESLint..."
	docker-compose run --rm frontend npm run lint
	@echo "🔍 Running TypeScript type checking..."
	docker-compose run --rm frontend npm run type-check

# コードフォーマット (Format all code)
format: format-backend format-frontend
	@echo "✅ All code formatting completed"

# バックエンドコードフォーマット (Format backend code)
format-backend:
	@echo "🎨 Formatting backend code..."
	@echo "📝 Running black formatter..."
	@if [ -d "backend/tests" ]; then \
		docker-compose run --rm backend black models/ main.py tests/; \
	else \
		docker-compose run --rm backend black models/ main.py; \
	fi
	@echo "📦 Running isort import sorter..."
	@if [ -d "backend/tests" ]; then \
		docker-compose run --rm backend isort models/ main.py tests/; \
	else \
		docker-compose run --rm backend isort models/ main.py; \
	fi

# フロントエンドコードフォーマット (Format frontend code)
format-frontend:
	@echo "🎨 Formatting frontend code..."
	@echo "📝 Running prettier..."
	docker-compose run --rm frontend npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"
	@echo "📝 Running ESLint with --fix..."
	docker-compose run --rm frontend npm run lint:fix

# データベースマイグレーション (Run database migrations)
db-migrate:
	@echo "🗄️  Running database migrations..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "🔍 Checking if Alembic is initialized..."
	@if [ ! -f backend/alembic.ini ] || [ ! -d backend/alembic ]; then \
		echo "📋 Initializing Alembic for the first time..."; \
		docker-compose run --rm backend alembic init alembic; \
		echo "⚙️  Configuring Alembic database URL..."; \
		docker-compose run --rm backend sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = postgresql://gs_user:gs_password@db:5432/gs_db|g' alembic.ini; \
		echo "ℹ️  Alembic initialized. You may need to create your first migration with:"; \
		echo "    docker-compose run --rm backend alembic revision --autogenerate -m 'Initial migration'"; \
	else \
		echo "✅ Alembic already initialized"; \
	fi
	@echo "📊 Running Alembic migrations..."
	@if docker-compose run --rm backend alembic current >/dev/null 2>&1; then \
		docker-compose run --rm backend alembic upgrade head; \
	else \
		echo "ℹ️  No migrations found. Database schema may be empty or migrations need to be created."; \
		echo "    To create your first migration, run:"; \
		echo "    docker-compose run --rm backend alembic revision --autogenerate -m 'Initial migration'"; \
	fi
	@echo "✅ Database migrations completed"

# テストデータ投入 (Seed test data)
db-seed:
	@echo "🌱 Seeding test data..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "📊 Running seed script..."
	@if docker-compose run --rm backend python -c "import app.db.seed" >/dev/null 2>&1; then \
		docker-compose run --rm backend python -c "from app.db.seed import seed_data; seed_data()"; \
	else \
		echo "ℹ️  Seed script not found. Skipping data seeding."; \
		echo "    Create app/db/seed.py with seed_data() function to enable seeding."; \
	fi
	@echo "✅ Test data seeding completed"

# データベースリセット (Reset database)
db-reset:
	@echo "🔄 Resetting database..."
	@echo "⚠️  This will delete all data. Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "🛑 Stopping database container..."
	docker-compose stop db
	@echo "🗑️  Removing database volume..."
	docker-compose down -v
	@echo "🚀 Starting fresh database..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 10
	@echo "📊 Running migrations on fresh database..."
	$(MAKE) db-migrate
	@echo "🌱 Seeding fresh data..."
	$(MAKE) db-seed
	@echo "✅ Database reset completed"

# Alembic初期化 (Initialize Alembic)
db-init:
	@echo "🔧 Initializing Alembic configuration..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@echo "🔍 Checking existing Alembic setup..."
	@if [ -f backend/alembic.ini ] || [ -d backend/alembic ]; then \
		echo "⚠️  Alembic already exists. Cleaning up first..."; \
		rm -rf backend/alembic backend/alembic.ini; \
		echo "🧹 Cleaned up existing Alembic files"; \
	fi
	@echo "📋 Initializing fresh Alembic setup..."
	docker-compose run --rm backend alembic init alembic
	@echo "⚙️  Configuring Alembic database URL..."
	docker-compose run --rm backend sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|sqlalchemy.url = postgresql://gs_user:gs_password@db:5432/gs_db|g' alembic.ini
	@echo "✅ Alembic initialization completed"
	@echo "ℹ️  Next step: Create your first migration with 'make db-revision'"

# 新しいマイグレーション作成 (Create new migration)
db-revision:
	@echo "📝 Creating new database migration..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db
	@echo "⏳ Waiting for database to be ready..."
	@sleep 5
	@if [ ! -f backend/alembic.ini ]; then \
		echo "❌ Alembic not initialized. Run 'make db-init' first."; \
		exit 1; \
	fi
	@read -p "Enter migration message: " message; \
	docker-compose run --rm backend alembic revision --autogenerate -m "$$message"
	@echo "✅ Migration created successfully"

# Alembicステータス確認 (Check Alembic status)
db-status:
	@echo "📊 Checking database and Alembic status..."
	@echo "🚀 Starting database container..."
	docker-compose up -d db >/dev/null 2>&1
	@echo "⏳ Waiting for database to be ready..."
	@sleep 3
	@echo ""
	@echo "📋 Alembic Configuration:"
	@if [ -f backend/alembic.ini ]; then \
		echo "  ✅ alembic.ini exists"; \
	else \
		echo "  ❌ alembic.ini missing"; \
	fi
	@if [ -d backend/alembic ]; then \
		echo "  ✅ alembic directory exists"; \
	else \
		echo "  ❌ alembic directory missing"; \
	fi
	@echo ""
	@echo "🗄️  Database Status:"
	@if docker-compose exec -T db pg_isready -U gs_user >/dev/null 2>&1; then \
		echo "  ✅ Database is ready"; \
	else \
		echo "  ❌ Database not ready"; \
	fi
	@echo ""
	@echo "📊 Migration Status:"
	@if [ -f backend/alembic.ini ] && [ -d backend/alembic ]; then \
		docker-compose run --rm backend alembic current 2>/dev/null || echo "  ℹ️  No migrations applied yet"; \
	else \
		echo "  ❌ Alembic not initialized"; \
	fi

# 環境クリーンアップ (Environment cleanup)
clean:
	@echo "🧹 Cleaning up development environment..."
	@echo "🛑 Stopping all containers..."
	docker-compose down
	@echo "🗑️  Removing containers and networks..."
	docker-compose down --remove-orphans
	@echo "🧹 Removing unused Docker images..."
	docker image prune -f
	@echo "🧹 Removing unused Docker volumes..."
	docker volume prune -f
	@echo "🧹 Removing unused Docker networks..."
	docker network prune -f
	@echo "🧹 Cleaning backend cache..."
	@if [ -d "backend/__pycache__" ]; then rm -rf backend/__pycache__; fi
	@if [ -d "backend/.pytest_cache" ]; then rm -rf backend/.pytest_cache; fi
	@if [ -d "backend/htmlcov" ]; then rm -rf backend/htmlcov; fi
	@echo "🧹 Cleaning frontend cache..."
	@if [ -d "frontend/node_modules/.cache" ]; then rm -rf frontend/node_modules/.cache; fi
	@if [ -d "frontend/build" ]; then rm -rf frontend/build; fi
	@if [ -d "frontend/coverage" ]; then rm -rf frontend/coverage; fi
	@echo "✅ Cleanup completed"

# Development utilities
logs:
	@echo "📋 Showing logs for all services..."
	docker-compose logs -f

logs-backend:
	@echo "📋 Showing backend logs..."
	docker-compose logs -f backend

logs-frontend:
	@echo "📋 Showing frontend logs..."
	docker-compose logs -f frontend

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
	@echo "     - ⚠️  This will delete database data if containers are stopped!"
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
	docker-compose run --rm backend pre-commit install
	@echo "✅ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit:
	@echo "🪝 Running pre-commit on all files..."
	docker-compose run --rm backend pre-commit run --all-files