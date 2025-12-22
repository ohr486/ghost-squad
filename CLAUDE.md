# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ghost-Squad is a multi-agent AI system inspired by Ghost in the Shell, featuring a "Living Kanban" concept. The system consists of three main applications:

- **API (Backend)**: FastAPI server with LangGraph-based agent orchestration
- **Web (Frontend)**: Next.js 14 application with drag-and-drop Kanban board
- **CLI**: Go-based TUI (Terminal User Interface) using Bubble Tea

The architecture uses LangGraph to create a "ghost brain" that processes missions through coordinated agent nodes (planner → worker → reporter). The frontend features real-time task visualization with drag-and-drop functionality and automatic backend synchronization.

## Development Commands

### Quick Start
```bash
# Start all services (recommended)
docker-compose up

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

### Docker Compose
```bash
# Start all services (API, Web, PostgreSQL, Redis)
docker-compose up
docker-compose up -d          # Detached mode

# Start specific service
docker-compose up api
docker-compose up web

# Stop all services
docker-compose down
docker-compose down -v        # Also remove volumes

# View logs
make logs                     # All services
make api-logs                 # API only
make web-logs                 # Web only

# Rebuild containers
make build
make restart                  # Down + Up
```

### Testing
```bash
make test           # Run all tests (API + Web)
make test-api       # API tests only (pytest with asyncio)
make test-web       # Web tests only (Jest)
```

**Note**: Tests use in-memory SQLite with `aiosqlite` for async testing. API tests currently pass but command may timeout (tests are skipped to bypass this issue).

### Code Quality
```bash
# Format Python code (Black + Isort)
make format

# Lint all code
make lint           # API (Flake8, Black, Isort) + Web (ESLint)
make lint-api       # API only
make lint-web       # Web only
```

### Database Management
```bash
# Reset database (drops volumes and recreates)
make db-reset

# Access PostgreSQL shell
make db

# Execute SQL query
make dbe Q='SELECT * FROM missions;'
```

Database credentials: `ghost/squad_password`, database name: `ghost_memory`.

### CLI
```bash
# Run CLI in Docker
make cli

# Or directly
docker-compose run --rm cli
```

### Cleanup
```bash
# Remove all containers, volumes, caches, node_modules
make clean
```

### Manual Development (without Docker)

**API:**
```bash
cd apps/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Requires: PostgreSQL (port 5432) and Redis (port 6379).

**Web:**
```bash
cd apps/web
npm install
npm run dev         # Development server
npm run build       # Production build
npm start           # Production server
```

## Architecture

### Core Data Flow

1. User submits mission instruction via Web UI or CLI
2. API creates mission in database, queues background task
3. Background task invokes LangGraph `ghost_brain` workflow
4. Planner node calls OpenAI LLM (or fallback simulation on error)
5. Tasks are created in database with status, assignee, energy cost
6. Frontend polls `/missions` every 2 seconds and updates UI
7. User can drag tasks in Kanban board, triggering PATCH updates to backend

### Agent System (LangGraph)

Located in `apps/api/agents/`:

**state.py** - Defines `AgentState` (shared memory structure):
- `mission_id`: Unique identifier
- `task_input`: User's instruction
- `current_plan`: AI-generated work breakdown structure (WBS)
- `logs`: Thought logs for debugging
- `status`: `'planning'`, `'working'`, or `'done'`
- `energy_used`: Cost tracking in USD

**graph.py** - LangGraph workflow with three sequential nodes:
- `node_planner`: Uses OpenAI LLM to break down instructions into 3-5 tasks (Japanese output). Falls back to simulation on API errors.
- `node_worker`: Simulates task execution with `time.sleep(1.5)` and random agent names like "tachikoma-01". **This is where real task processing logic should be implemented.**
- `node_reporter`: Finalizes mission and marks as complete.

The graph is compiled into `ghost_brain` which is invoked as a background task.

### API Structure (FastAPI)

**main.py** - FastAPI application with endpoints:
- `GET /`: Health check
- `POST /mission/start`: Create mission and trigger background agent execution
- `GET /mission/current`: Get latest mission with tasks
- `GET /missions`: Get mission history
- `PATCH /mission/tasks/{task_id}`: Update task status (for drag-and-drop)
- `DELETE /mission/{mission_id}`: Delete mission
- `POST /mission/reset`: Reset memory (legacy, consider removing per TODO.md)

CORS is configured for `http://localhost:3000`. Lifespan handler creates database tables on startup.

**database.py** - Async database setup:
- SQLAlchemy 2.0 async engine with `asyncpg` driver
- PostgreSQL connection from `DATABASE_URL` environment variable
- Dependency injection: `get_db()` for FastAPI routes

**models.py** - Database models (SQLAlchemy ORM):
- `MissionModel`: Stores mission metadata, status, logs (JSON column)
- `TaskModel`: Individual tasks with status, assignee, energy tracking
- Relationship: One mission → many tasks (cascade delete)

**schemas.py** - Pydantic validation:
- `MissionRequest`, `MissionResponse`, `MissionSchema`: Mission data
- `TaskSchema`, `TaskUpdate`: Task data
- `PlanSchema`: Structured LLM output format (used by Planner node)

**services.py** - Business logic layer:
- `create_mission()`: Insert mission into database
- `run_agent_for_mission()`: Execute LangGraph workflow and save results
- `get_latest_mission()`: Fetch most recent mission with tasks
- `get_all_missions()`: History with eager loading
- `update_task_status()`: Modify task status
- `delete_mission()`: Remove mission and cascaded tasks

### Frontend Structure (Next.js)

**app/page.tsx** - Main interface:
- Mission history sidebar with delete functionality
- Real-time log console (green text on black, cyberpunk theme)
- Command input with "司令官" (Commander) theme
- Mission selection and display
- **Polling mechanism**: Fetches `/missions` every 2 seconds to sync state
- **Smart updates**: Only re-renders when logs/tasks/status actually change (JSON comparison to prevent unnecessary renders)

**components/LivingKanban.tsx** - Interactive Kanban board:
- Three columns: Planning, Working, Done
- Drag-and-drop using `@dnd-kit/core` and `@dnd-kit/sortable`
- Features:
  - Draggable task cards with assignee and energy display
  - Progress bar animation for "working" tasks (Framer Motion)
  - Status-based column styling
  - **Automatic backend sync**: On drag-and-drop, sends PATCH to `/mission/tasks/{id}`
- Collision detection: `closestCorners` strategy

**app/layout.tsx** - Root layout with Inter font, metadata, and Tailwind CSS.

### CLI (Go + Bubble Tea)

Located in `apps/cli/`:
- Cyberpunk-styled TUI with cyan/magenta colors
- Two modes: Viewing and Input (press `i` to enter input mode)
- API integration: POST to `/mission/start`, polls GET `/` for health
- Commands: `i` (input), `q` (quit), `esc` (cancel)
- Environment variable: `API_URL` (defaults to `http://api:8000/`)

### Infrastructure

**docker-compose.yml** orchestrates four services:
- **api**: Python FastAPI backend (port 8000)
- **web**: Next.js frontend (port 3000)
- **db**: PostgreSQL 15 (port 5432) - "shared ghost-memory"
- **redis**: Redis (port 6379) - task queue and state cache
- **cli**: Go TUI (profile "tools", not started by default)

## Key Dependencies

**API (Python)**:
- Web: `fastapi`, `uvicorn`
- Database: `sqlalchemy>=2.0.0`, `asyncpg`, `greenlet`
- AI/LLM: `openai>=1.0.0`, `langchain`, `langchain-core`, `langchain-openai`, `langgraph`
- Cache: `redis>=4.5.0`
- Testing: `pytest`, `pytest-asyncio`, `pytest-mock`, `httpx`, `aiosqlite`
- Code quality: `black`, `isort`, `flake8`

**Web (TypeScript/React)**:
- Framework: `next@14.1.0`, `react@18`, `react-dom@18`
- Drag-and-drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- UI/Animation: `framer-motion@11.0.0`, `lucide-react`, `tailwindcss`
- Testing: `jest`, `@testing-library/react`, `@testing-library/jest-dom`

**CLI (Go)**:
- TUI: `github.com/charmbracelet/bubbletea`, `github.com/charmbracelet/lipgloss`
- Input: `github.com/charmbracelet/bubbles/textinput`

## Configuration

**API Environment** (`apps/api/.env`):
- `OPENAI_API_KEY`: Required for LLM integration
- `GHOST_MODEL_NAME`: Model selection (default: `gpt-3.5-turbo`)
- `DATABASE_URL`: PostgreSQL connection string (set in docker-compose)

Copy `.env.example` to `.env` and add your OpenAI API key.

**Web Environment**:
- `NEXT_PUBLIC_API_URL`: API endpoint (defaults to `http://localhost:8000`)

## Development Notes

### Current State

- **Frontend IS connected to backend**: Polling every 2 seconds, drag-and-drop syncs with API
- **LangGraph Planner**: Uses real OpenAI LLM calls with fallback simulation on errors
- **Worker node**: Still simulated with `time.sleep()` - **no real task execution yet**
- **Database**: Uses `create_all()` on startup (no migration system like Alembic)
- **Polling-based UI**: Ready for WebSocket/SSE upgrade (see TODO.md)

### Architectural Patterns

- **Async-first**: SQLAlchemy 2.0 async with asyncpg driver throughout
- **Background processing**: Missions execute in FastAPI `BackgroundTasks`
- **State machine**: LangGraph provides linear workflow (planner → worker → reporter)
- **Optimistic UI updates**: Frontend allows drag-and-drop, syncs to backend afterward

### Known Limitations (from TODO.md)

- No authentication/authorization on API endpoints
- Secrets hardcoded in `docker-compose.yml` (should use `.env`)
- TypeScript strict mode disabled (`"strict": false` in `tsconfig.json`)
- Test timeout issue: API tests pass but `make test` times out (tests currently skipped)
- No migration system (uses `create_all()`)
- Polling instead of WebSocket (inefficient for real-time updates)

### Code Style

- **Japanese comments**: Present throughout, particularly in API logic explaining Ghost-Squad concepts
- **Python**: Black formatter (line length 88), Isort for imports
- **TypeScript**: ESLint with Next.js rules

### Important Files for Common Tasks

**Adding new API endpoint**: `apps/api/main.py`, `apps/api/services.py`, `apps/api/schemas.py`

**Modifying agent logic**: `apps/api/agents/graph.py`, `apps/api/agents/state.py`

**Database schema changes**: `apps/api/models.py` (then run `make db-reset`)

**Frontend UI changes**: `apps/web/app/page.tsx`, `apps/web/components/LivingKanban.tsx`

**Testing**: `apps/api/tests/test_endpoints.py`, `apps/web/__tests__/Home.test.tsx`
