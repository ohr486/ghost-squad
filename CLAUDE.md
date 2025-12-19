# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ghost-Squad is a multi-agent AI system inspired by Ghost in the Shell, featuring a "Living Kanban" concept. The system consists of three main applications:

- **API (Backend)**: FastAPI server with LangGraph-based agent orchestration
- **Web (Frontend)**: Next.js 14 application with TypeScript and Tailwind CSS
- **CLI**: Command-line interface (placeholder directory)

The architecture uses LangGraph to create a "ghost brain" that processes missions through coordinated agent nodes (planner → worker → reporter).

## Development Commands

### Docker Compose (Recommended)
```bash
# Start all services (API, Web, PostgreSQL, Redis)
docker-compose up

# Start specific service
docker-compose up api
docker-compose up web

# Stop all services
docker-compose down
```

### API (FastAPI Backend)
```bash
cd apps/api

# Run development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Dependencies**: PostgreSQL (port 5432) and Redis (port 6379) must be running.

### Web (Next.js Frontend)
```bash
cd apps/web

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The web app will be available at http://localhost:3000.

## Architecture

### Agent System (LangGraph)

The core intelligence lives in `apps/api/agents/`:

- **state.py**: Defines `AgentState` - the shared memory structure passed between all nodes. Contains mission metadata, task input, planning steps, execution logs, status, and cost tracking.

- **graph.py**: Implements the LangGraph workflow with three sequential nodes:
  - `node_planner`: Receives mission instructions and creates an execution plan
  - `node_worker`: Executes the plan (currently simulated with random agent names like "tachikoma-01")
  - `node_reporter`: Finalizes and reports mission completion

  The graph is compiled into `ghost_brain` which is invoked by the API.

### API Structure

**main.py** is the FastAPI entry point:
- `POST /mission/start`: Accepts a mission instruction, initializes `AgentState`, invokes `ghost_brain`, and returns the final state with logs and status.
- `GET /`: Health check endpoint.

The API uses Pydantic models (`MissionRequest`, `MissionResponse`) for request/response validation.

### Frontend Structure

Minimal Next.js 14 App Router setup in `apps/web/app/`:
- **page.tsx**: Landing page with "GHOST-SQUAD" branding and system status indicator
- **layout.tsx**: Root layout with basic HTML structure

Uses Tailwind CSS for styling. No API integration implemented yet.

### Infrastructure

**docker-compose.yml** orchestrates four services:
- **api**: Python FastAPI backend (port 8000)
- **web**: Next.js frontend (port 3000)
- **db**: PostgreSQL 15 (port 5432) - "shared ghost-memory"
- **redis**: Redis (port 6379) - task queue and state cache

Environment variables are configured per service. Database credentials: `ghost/squad_password`, database name: `ghost_memory`.

## Key Dependencies

**API (Python)**:
- fastapi, uvicorn: Web framework and ASGI server
- sqlalchemy, asyncpg: Database ORM and PostgreSQL driver
- redis: Cache and queue management
- langchain, langgraph: Agent orchestration framework
- openai: LLM integration

**Web (TypeScript/React)**:
- next 14.1.0: React framework with App Router
- framer-motion: Animation library
- lucide-react: Icon library
- tailwindcss: Utility-first CSS

## Development Notes

- The LangGraph implementation currently simulates LLM calls with `time.sleep()` for demonstration purposes. Real LLM integration (OpenAI) is included in dependencies but not yet implemented.

- Agent State flows through the graph nodes, with each node returning partial state updates that get merged automatically by LangGraph.

- Japanese comments are present throughout the codebase, particularly in API logic explaining the Ghost-Squad concept and mission flow.

- The frontend does not yet connect to the backend API. The `NEXT_PUBLIC_API_URL` environment variable is configured but unused.

- TypeScript strict mode is disabled in the web app (`"strict": false` in tsconfig.json).
