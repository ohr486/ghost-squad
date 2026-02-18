# GitHub Copilot Instructions for Ghost Squad

This file provides guidance for GitHub Copilot when working with the Ghost Squad codebase.

## Project Overview

Ghost Squad is an AI-driven task management platform that converts natural language inquiries into structured user stories. The platform uses AI agents to understand user requests and automatically generate actionable tasks.

**Core Functionality:**
- Natural language inquiry processing (Japanese/English)
- AI-powered story generation from inquiries
- Email (IMAP) import with AI analysis
- Task management with approval workflows
- Plugin architecture for data sources and AI providers

## Tech Stack

**Backend:**
- Python 3.11+ with FastAPI 0.104.1
- SQLAlchemy 2.0.23 ORM + Alembic 1.12.1 migrations
- PostgreSQL 15 Alpine
- OpenAI API 1.3.7 for AI features

**Frontend:**
- React 18.2.0 with TypeScript 4.9.5
- Modern component-based architecture

**Infrastructure:**
- Docker Compose for containerization
- Makefile for development automation

## Development Methodology: Kiro Spec-Driven Development

This project follows **Kiro-style Spec-Driven Development** on AI-DLC (AI Development Life Cycle).

### Workflow Phases:
1. **Requirements** → 2. **Design** → 3. **Tasks** → 4. **Implementation**

### Key Commands:
```bash
/kiro:spec-status {feature}      # Check spec progress
/kiro:spec-requirements {feature} # Generate requirements
/kiro:spec-design {feature}      # Create design
/kiro:spec-tasks {feature}       # Generate tasks
/kiro:spec-impl {feature}        # Execute implementation
```

### Important Rules:
- Always check `.kiro/steering/` for project-wide guidelines
- All spec documents (requirements.md, design.md, tasks.md) are written in **Japanese**
- Follow 3-phase approval workflow
- Use Test-Driven Development (TDD)

## Project Structure

```
ghost-squad/
├── api/                    # Python FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── models/            # Data models
│   │   ├── database/      # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── enums/         # Status/priority enums
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   │   ├── *_repository.py      # Data access layer
│   │   ├── *_validator.py       # Validation logic
│   │   ├── *_workflow_service.py # Workflow management
│   │   └── importer/      # Plugin-based importers
│   ├── alembic/           # DB migrations
│   └── tests/             # Backend tests
├── web/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── package.json
├── .kiro/                 # Kiro specifications
│   ├── steering/         # Project guidelines
│   └── specs/            # Feature specs
├── docs/                  # Documentation
└── docker-compose.yml     # Container orchestration
```

## Code Standards

### Python (Backend)

**Formatting:**
- `black` with 88 character line length
- `isort --profile black` for imports
- Import order: standard library → third-party → local (absolute) → relative

**Linting:**
- `flake8` for style checking
- `mypy --strict` for type checking
- `bandit` for security

**Naming Conventions:**
- Files/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

**Testing:**
- Test coverage: 80%+ for new features
- Use pytest for testing
- Follow TDD approach

### TypeScript (Frontend)

**Formatting:**
- `prettier` for code formatting
- `ESLint --fix` for linting
- TypeScript strict mode enabled

**Naming Conventions:**
- Components: `PascalCase.tsx`
- Other files: `camelCase.ts`
- Types/Interfaces: `PascalCase`

**Import Order:**
1. React imports
2. Third-party libraries
3. Local imports
4. Type-only imports

**Testing:**
- Test coverage: 50%+ minimum, 80%+ for new features

## Domain Model

### Inquiry (問い合わせ)
- Represents user inquiries in natural language
- Status: RECEIVED, PROCESSING, NEEDS_CLARIFICATION, TASK_WORKING, COMPLETED, FAILED
- Key fields: user_id, content, language (default: "ja"), timestamp, status

### Story (ストーリー)
- Generated from inquiries using AI
- Status: PENDING_REVIEW, APPROVED, EXPORTED, REJECTED
- Priority: LOW, MEDIUM, HIGH, URGENT
- Category: DEVELOPMENT, TESTING, DOCUMENTATION, RESEARCH, MAINTENANCE, CUSTOM
- Key fields: inquiry_id, title, description, category, priority, estimated_effort

### Importer
- Plugin-based system for importing data (e.g., email)
- Dual plugin architecture: data source + AI provider
- Supports OpenAI and Anthropic for AI analysis

## Development Commands

```bash
# Environment Setup
make setup          # Initial setup
make dev           # Start dev servers
make stop          # Stop services

# Testing & Quality
make test          # Run all tests
make lint          # Run linting
make format        # Format code

# Database
make db-migrate    # Run migrations
make db-seed       # Seed test data
make db-status     # Check migration status

# Logs
make logs          # All service logs
make logs-backend  # Backend only
```

## Service Endpoints (Development)

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (OpenAPI/Swagger)
- Database: localhost:5432 (PostgreSQL)

## Environment Variables

Required in `.env`:
```bash
DATABASE_URL=postgresql://gs_user:gs_password@db:5432/gs_db
OPENAI_API_KEY=your_openai_api_key     # Required for AI features
SECRET_KEY=your_jwt_secret              # Security
ENVIRONMENT=development
DEBUG=true
```

## Common Patterns

### API Route Structure
```python
# api/routers/{entity}.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/{entity}", tags=["{entity}"])

@router.post("/", response_model=Schema)
async def create_{entity}(data: CreateSchema, db: Session = Depends(get_db)):
    # Implementation
```

### Service Layer Pattern
```python
# api/services/{entity}_repository.py
class EntityRepository:
    def create(self, db: Session, data: CreateSchema) -> Model:
        # Data access logic
    
    def get_by_id(self, db: Session, id: int) -> Optional[Model]:
        # Retrieval logic
```

### React Component Pattern
```typescript
// web/src/components/EntityList.tsx
import React, { useState, useEffect } from 'react';
import { EntityService } from '../services/entity';
import { Entity } from '../types/entity';

export const EntityList: React.FC = () => {
    const [entities, setEntities] = useState<Entity[]>([]);
    // Component logic
};
```

## Testing Approach

### Backend Tests
```python
# api/tests/test_{entity}.py
import pytest
from fastapi.testclient import TestClient

def test_create_{entity}(client: TestClient):
    response = client.post("/api/{entity}/", json={...})
    assert response.status_code == 201
```

### Frontend Tests
```typescript
// web/src/components/__tests__/Entity.test.tsx
import { render, screen } from '@testing-library/react';
import { EntityList } from '../EntityList';

test('renders entity list', () => {
    render(<EntityList />);
    // Assertions
});
```

## Language Considerations

- **Primary Language:** Japanese (for spec documents and user-facing content)
- **Secondary Language:** English (for code, comments, technical terms)
- **API Messages:** Support both Japanese and English
- **Default Language:** Japanese ("ja") for new inquiries

## Important Notes

1. **Always check specifications:** Use `/kiro:spec-status` before starting work
2. **Follow TDD:** Write tests before implementing features
3. **Consult steering docs:** Review `.kiro/steering/` for project-wide guidelines
4. **Japanese specs:** All requirement, design, and task documents are in Japanese
5. **Minimal changes:** Make surgical, focused changes to existing code
6. **Plugin architecture:** When adding new importers or AI providers, follow the existing plugin pattern

## Documentation

Comprehensive documentation in `docs/`:
- `API.md` - RESTful API endpoints and schemas
- `DATABASE.md` - Database management and migrations
- `COMMAND.md` - Development commands and workflows
- `DEBUG.md` - Troubleshooting guide
- `SDD.md` - Spec-Driven Development guide

Also check:
- `CLAUDE.md` - Detailed AI assistant guidance
- `.kiro/steering/` - Project-wide guidelines
- `.kiro/specs/` - Feature specifications

## Common Pitfalls to Avoid

1. **Don't skip the approval workflow** - Each phase requires human review
2. **Don't mix languages** - Keep spec documents in Japanese, code in English
3. **Don't bypass validation** - Always validate input data properly
4. **Don't ignore test coverage** - Maintain 80%+ for new backend features
5. **Don't modify working code unnecessarily** - Make minimal, surgical changes
6. **Don't forget migrations** - Always create Alembic migrations for schema changes
7. **Don't commit secrets** - Use `.env` for sensitive data, never commit `.env` file

## Quick Start for New Features

1. Initialize spec: `/kiro:spec-init "feature description"`
2. Generate requirements: `/kiro:spec-requirements {feature}`
3. Create design: `/kiro:spec-design {feature}`
4. Generate tasks: `/kiro:spec-tasks {feature}`
5. Implement: `/kiro:spec-impl {feature}`
6. Write tests first (TDD)
7. Run tests: `make test`
8. Lint code: `make lint`
9. Format code: `make format`

## Current Project Status

- **inquiry spec**: ✅ Ready for implementation (tasks approved)
- **story spec**: 🚧 Initialized (awaiting requirements)
- **importer spec**: ✅ Implemented

Backend and frontend are actively developed. Check `.kiro/specs/` for current feature status.
