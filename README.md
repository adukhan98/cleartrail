# Compliance Packet Agent

AI-assisted evidence compiler for SOC 2 and ISO 27001 compliance. Connects to GitHub, Jira, and Google Drive to collect audit artifacts, map them to controls, and export auditor-ready evidence packages.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Local Development

1. **Clone and configure:**

```bash
cd compliance
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

2. **Start all services:**

```bash
docker-compose up -d
```

3. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

### Running Without Docker

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL and Redis locally, then:
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Architecture

```
├── backend/                  # FastAPI + Python
│   ├── app/
│   │   ├── api/             # REST endpoints
│   │   ├── connectors/      # GitHub, Jira, Drive
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── workers/         # Celery tasks
│   └── alembic/             # DB migrations
│
├── frontend/                 # Next.js 14
│   └── src/
│       ├── app/             # App Router pages
│       ├── components/      # React components
│       └── lib/             # API client, utils
│
└── docker-compose.yml       # Local dev stack
```

## Key Features

- **Provenance-first evidence:** Every artifact stored with source system, object ID, capture timestamp, and content hash
- **Human approval gates:** No evidence marked "audit-ready" until a control owner approves
- **AI-generated narratives:** Complete draft narratives with source citations
- **Gap detection:** Automatic detection of missing evidence and period coverage gaps
- **Auditor-ready export:** One-click Drive folder export with evidence manifest

## Integrations

| Source | OAuth Flow | Artifacts |
|--------|------------|-----------|
| GitHub | GitHub App / OAuth | PRs, commits, code reviews |
| Jira | OAuth 2.0 (3LO) | Issues, transitions, comments |
| Google Drive | OAuth 2.0 | Documents, policies, meeting notes |

## MVP Scope: Change Management

The MVP focuses on the **Change Management** control pack (SOC 2 CC7.1-CC7.3), which naturally stitches:
- Jira tickets (change requests)
- GitHub PRs (code changes + reviews)
- Drive docs (policies, meeting notes)

## License

Proprietary - All rights reserved
