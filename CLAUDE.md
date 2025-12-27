# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Ghost Squad - AI-Driven Task Management Platform

Ghost SquadはAIエージェントを活用した包括的なタスク管理プラットフォームで、自然言語での問い合わせを構造化されたユーザーストーリーに変換します。

## Project Type: Kiro Spec-Driven Development

このプロジェクトは **Kiro-style Spec Driven Development on AI-DLC (AI Development Life Cycle)** を採用しています。

### Kiro Workflow - Quick Reference

**Specification Phase**
```bash
/kiro:spec-init "description"        # Initialize new spec
/kiro:spec-requirements {feature}    # Generate requirements
/kiro:spec-design {feature} [-y]     # Create technical design
/kiro:spec-tasks {feature} [-y]      # Generate implementation tasks
```

**Implementation Phase**
```bash
/kiro:spec-impl {feature} [tasks]    # Execute tasks using TDD
```

**Validation & Status**
```bash
/kiro:validate-gap {feature}         # Analyze implementation gap
/kiro:validate-design {feature}      # Design quality review
/kiro:validate-impl {feature}        # Validate implementation
/kiro:spec-status {feature}          # Check specification status
```

**📖 詳細**: [Spec-Driven Development Guide](docs/SDD.md)

### Important Rules

- **3-phase approval workflow**: Requirements → Design → Tasks → Implementation
- **Think in English, write in Japanese**: All Markdown content in spec files MUST be in Japanese
- **Human review required** at each phase (use `-y` only for fast-tracking)
- **Check `.kiro/steering/`** for project-wide guidelines before starting work

### Kiro Paths
- **Steering**: `.kiro/steering/` - Project-wide rules (product.md, tech.md, structure.md)
- **Specs**: `.kiro/specs/` - Feature specifications (each has spec.json, requirements.md, design.md, tasks.md)

## Architecture Overview

**Tech Stack**
- Backend: Python 3.11+ with FastAPI 0.104.1 + SQLAlchemy 2.0.23 + Alembic 1.12.1
- Frontend: React 18.2.0 + TypeScript 4.9.5 (planned)
- Database: PostgreSQL 15 Alpine
- AI Integration: OpenAI API 1.3.7 (GPT-4 recommended)
- Infrastructure: Docker + Docker Compose

**Project Structure**
```
ghost-squad/
├── api/                   # Python FastAPI backend (to be created)
├── web/                   # React TypeScript frontend (to be created)
├── .kiro/                # Kiro specification files
│   ├── steering/         # Project-wide guidelines
│   └── specs/           # Feature specifications
├── docs/                # Documentation
│   ├── API.md           # API specification
│   ├── DATABASE.md      # Database management guide
│   └── SDD.md           # Spec-Driven Development guide
├── docker-compose.yml   # Container orchestration
├── Makefile            # Development automation
└── README.md           # Project overview
```

**Note**: `api/` and `web/` directories don't exist yet - they will be created during `/kiro:spec-impl` phase.

## Development Commands - Quick Reference

### Essential Commands
```bash
# Setup & Control
make setup          # Initial environment setup
make dev           # Start development servers
make stop          # Stop all services
make status        # Check service health

# Testing & Quality
make test          # Run all tests
make lint          # Run all linting
make format        # Format all code

# Database
make db-migrate    # Run migrations
make db-seed       # Seed test data
make db-status     # Check migration status

# Logs
make logs          # All service logs
make logs-backend  # Backend logs only
```

**📖 詳細**: [開発コマンドリファレンス](docs/COMMAND.md) - 全コマンドの詳細説明、使用例、ワークフロー

## Service Endpoints (when running)

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (OpenAPI/Swagger)
- **Database**: localhost:5432 (PostgreSQL)

## Environment Variables

Required `.env` configuration:
```bash
DATABASE_URL=postgresql://gs_user:gs_password@db:5432/gs_db
OPENAI_API_KEY=your_openai_api_key         # Required for AI features
SECRET_KEY=your_jwt_secret                  # Change in production
ENVIRONMENT=development
DEBUG=true
```

## Domain Model - Quick Reference

**Inquiry** (問い合わせ) - `inquiry` spec: tasks-generated phase
- Status: RECEIVED, PROCESSING, NEEDS_CLARIFICATION, TASK_WORKING, COMPLETED, FAILED
- Key fields: user_id, content, language (default: "ja"), timestamp, status

**Story** (ストーリー) - `story` spec: init phase
- Status: PENDING_REVIEW, APPROVED, EXPORTED, REJECTED
- Priority: LOW, MEDIUM, HIGH, URGENT
- Category: DEVELOPMENT, TESTING, DOCUMENTATION, RESEARCH, MAINTENANCE, CUSTOM
- Key fields: inquiry_id, title, description, category, priority, estimated_effort

**📖 詳細**: [API Specification](docs/API.md) - Endpoints, schemas, error handling

## Code Standards - Quick Reference

**Python (Backend)**
- Format: `black` (88 chars) + `isort --profile black`
- Lint: `flake8` + `mypy --strict` + `bandit`
- Test coverage: 80%+ for new features
- Naming: `snake_case` files/functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants

**TypeScript (Frontend)**
- Format: `prettier` + `ESLint --fix`
- Type checking: TypeScript strict mode
- Test coverage: 50%+ minimum, 80%+ for new features
- Naming: `PascalCase.tsx` components, `camelCase.ts` others

**Import Order**
- Python: standard library → third-party → local (absolute) → relative
- TypeScript: React → third-party → local → type-only imports

## Documentation

Ghost Squadの詳細ドキュメントは `docs/` ディレクトリに整理されています：

### 📚 Core Documentation

- **[開発コマンドリファレンス](docs/COMMAND.md)** - All Makefile commands, usage examples, workflows
- **[トラブルシューティングガイド](docs/DEBUG.md)** - Problem diagnosis, debugging techniques, environment reset
- **[API Specification](docs/API.md)** - RESTful endpoints, request/response formats, error handling
- **[Database Management](docs/DATABASE.md)** - Setup, migrations, schema details, backup/restore
- **[Spec-Driven Development](docs/SDD.md)** - Kiro workflow, development rules, best practices

### 📖 Additional Resources

- **[README.md](README.md)** - Project overview, quick start, basic commands
- **`.kiro/steering/`** - Project-wide guidelines (product.md, tech.md, structure.md)
- **`.kiro/specs/`** - Feature specifications (requirements.md, design.md, tasks.md)

## Current Project Status

- **inquiry spec**: ✅ Requirements, design, and tasks approved - ready for implementation
- **story spec**: 🚧 Initialized - awaiting requirements generation
- **Implementation**: Backend (`api/`) and frontend (`web/`) directories to be created during `/kiro:spec-impl` phase

## Quick Tips for Claude Code

### Before Starting Work

1. **Check spec status**: `/kiro:spec-status` to understand current progress
2. **Read steering docs**: Always load `.kiro/steering/` for project context
3. **Review existing specs**: Check `.kiro/specs/` for related features

### During Development

1. **Follow Kiro workflow**: Don't skip phases (Requirements → Design → Tasks → Impl)
2. **Get approval**: Each phase needs human review (don't use `-y` unless fast-tracking)
3. **Write in Japanese**: All spec documents must be in Japanese (spec.json language field)
4. **Use TDD**: Write tests first, then implement

### Common Tasks

**Starting a new feature**:
```bash
/kiro:spec-init "feature description"
/kiro:spec-requirements {feature}
/kiro:spec-design {feature}
/kiro:spec-tasks {feature}
/kiro:spec-impl {feature}
```
See [SDD.md](docs/SDD.md) for detailed workflow examples.

**Development workflow**:
```bash
make dev           # Start servers
make test          # Run tests
make lint          # Check code quality
make format        # Format code
```
See [COMMAND.md](docs/COMMAND.md) for complete workflows and examples.

**Troubleshooting**:
- Quick diagnosis: `make status`, `make logs`, `make disk-usage`
- Detailed guide → [DEBUG.md](docs/DEBUG.md)
- Database issues → [DATABASE.md](docs/DATABASE.md)
- API errors → [API.md](docs/API.md)
- Kiro workflow → [SDD.md](docs/SDD.md)

## Language Notes

- **Primary language**: Japanese (default for all user-facing content and spec documents)
- **Secondary language**: English (technical terms, API, code comments)
- **日本語特有の考慮事項**: 全角・半角、敬語・丁寧語、業界用語統一

## Notes

- このプロジェクトはKiro spec-driven developmentを採用しています
- 実装開始前に必ず `/kiro:spec-status` で仕様を確認してください
- すべての仕様ドキュメント (requirements.md, design.md, tasks.md) は日本語で記述されています
- Follow the 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- 詳細情報は `docs/` ディレクトリの各ドキュメントを参照してください
