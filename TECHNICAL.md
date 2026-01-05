# TECHNICAL.md

Technical documentation for developers working on ClearTrail. For project context and user requirements, see CLAUDE.md.

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Celery, Redis
- **Frontend:** Next.js 14, React 18, TypeScript, TailwindCSS, TanStack Query
- **Database:** PostgreSQL 16 with Alembic migrations
- **AI:** OpenAI API (GPT-4o) for narrative generation

---

## Development Commands

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Run server
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info -Q sync,ai

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Tests
pytest                          # All tests
pytest tests/test_api -v        # Specific directory
pytest -k "test_name" -v        # Single test by name
pytest --cov=app                # With coverage

# Linting
ruff check .
ruff format .
mypy .
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Development server (:3000)
npm run build    # Production build
npm run lint
npm test         # Vitest
```

### Docker (Full Stack)

```bash
docker-compose up -d            # Start all services
docker-compose logs -f backend  # View logs
docker-compose down -v          # Stop and reset
```

---

## Architecture

### Core Data Flow

```
OAuth → Sync → Normalize → Map to Controls → Approve → Export
```

1. User connects integrations via OAuth (tokens encrypted with Fernet)
2. Celery tasks sync artifacts from source systems
3. Artifacts normalized with provenance (source, object ID, URL, hash)
4. AI or manual mapping to SOC 2/ISO 27001 controls
5. Human approval creates immutable ApprovalRecord
6. Export to Google Drive with manifest

### Backend Structure (`backend/app/`)

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Pydantic Settings
├── database.py          # SQLAlchemy async setup
├── api/                 # REST endpoint routers
│   ├── auth.py          # Authentication
│   ├── integrations.py  # OAuth flows, sync triggers
│   ├── artifacts.py     # Evidence CRUD & approval
│   ├── controls.py      # SOC 2/ISO 27001 controls
│   ├── packets.py       # Evidence packet management
│   ├── exports.py       # Export to Google Drive
│   └── deps.py          # Dependency injection
├── models/              # SQLAlchemy ORM models
│   ├── base.py          # TimestampMixin, UUIDMixin
│   ├── user.py          # User with org membership
│   ├── organization.py  # Multi-tenant organization
│   ├── artifact.py      # EvidenceArtifact, ControlMapping, ApprovalRecord
│   ├── control.py       # Control definitions
│   ├── integration.py   # OAuth token storage (encrypted)
│   └── packet.py        # EvidencePacket wrapper
├── schemas/             # Pydantic request/response
├── services/            # Business logic
│   ├── evidence_service.py    # Artifact CRUD + hashing
│   ├── approval_service.py    # Approval workflows
│   ├── mapping_service.py     # Control mapping
│   ├── gap_service.py         # Gap detection
│   ├── narrative_service.py   # AI narrative generation
│   └── export_service.py      # Drive export
├── connectors/          # Source system integrations
│   ├── base.py          # BaseConnector interface
│   ├── registry.py      # Connector factory
│   ├── github/          # GitHub API
│   ├── jira/            # Jira API
│   └── google_drive/    # Google Drive API
└── workers/             # Celery async tasks
    ├── celery_app.py    # Celery setup
    ├── sync_tasks.py    # Connector sync
    └── narrative_tasks.py  # AI narrative
```

### Key Models

- **EvidenceArtifact** - Core model with content_hash (SHA-256), approval_status, period coverage
- **ControlMapping** - Links artifacts to controls with confidence score and source (auto/manual)
- **ApprovalRecord** - Immutable audit trail with signature hash
- **Integration** - OAuth tokens (encrypted) per organization

### Multi-Tenancy

All data is organization-scoped via `org_id` foreign keys.

### Connector Pattern

New integrations extend `BaseConnector` from `connectors/base.py` and register via `connectors/registry.py`.

---

## API Routes

| Route | Module | Purpose |
|-------|--------|---------|
| `/api/auth/*` | auth.py | Login, register, token refresh |
| `/api/integrations/*` | integrations.py | OAuth flow, connection test, sync |
| `/api/artifacts/*` | artifacts.py | List, get, approve artifacts |
| `/api/controls/*` | controls.py | List controls, gap detection |
| `/api/packets/*` | packets.py | Create packets, generate narrative |
| `/api/exports/*` | exports.py | Export to Google Drive |
| `/api/health` | main.py | Health check |

Swagger UI: `http://localhost:8000/api/docs`

---

## Database

- **Type:** PostgreSQL with async SQLAlchemy 2.0
- **Driver:** asyncpg
- **Migrations:** Alembic
- **Connection Pool:** 5 size, 10 max overflow

### Mixins

- `TimestampMixin` - created_at, updated_at (UTC, indexed)
- `UUIDMixin` - UUID primary key

---

## Configuration

Copy `.env.example` to `.env` and configure:

```
APP_ENV=development|staging|production
DEBUG=true|false
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:port/0
SECRET_KEY=<jwt-signing-key>
ENCRYPTION_KEY=<fernet-key>
GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
JIRA_CLIENT_ID, JIRA_CLIENT_SECRET
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
OPENAI_API_KEY
```

---

## Celery Queues

- `sync` - Connector sync tasks
- `ai` - Narrative generation tasks

---

## Design Decisions

### Why these technologies?

- **FastAPI + async SQLAlchemy:** High concurrency for sync operations
- **Celery + Redis:** Background processing for long-running syncs and AI calls
- **PostgreSQL:** Reliable, supports UUID natively, good JSON support
- **Next.js 14:** Server components, good DX, production-ready
- **TanStack Query:** Handles caching, refetching, loading states

### Security

- OAuth tokens encrypted at rest with Fernet
- JWT for session management
- Approval records are immutable (append-only)
- Content hashes (SHA-256) for artifact integrity
