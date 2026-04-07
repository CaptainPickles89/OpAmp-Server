# Contributing to OpAMP Server

Welcome! This guide covers the development setup, build process, testing, and code standards for the OpAMP Server project.

## Project Overview

OpAMP Server is a spec-compliant CNCF OpAMP server with:
- **Backend**: FastAPI (Python 3.11) with SQLite persistence
- **Frontend**: React 19 + TypeScript with Vite
- **Protocol**: Binary OpAMP over HTTP/1.1 + JSON REST API
- **Infrastructure**: Docker Compose (FastAPI + nginx SPA + example collector)

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+ (npm)
- Docker & Docker Compose (for full stack testing)

### Backend Setup

```bash
# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### Frontend Setup

```bash
cd ui
npm install
```

### Environment Variables

The server reads configuration from environment variables with the `OPAMP_` prefix:

<!-- AUTO-GENERATED: Environment variables from opamp_server/config.py -->

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPAMP_HOST` | string | `0.0.0.0` | Server listen address |
| `OPAMP_PORT` | int | `8000` | Server listen port |
| `OPAMP_DB_PATH` | string | `./data/registry.db` | SQLite database path |
| `OPAMP_MAX_BODY_SIZE` | int | `1048576` (1 MB) | Maximum request body size in bytes |
| `OPAMP_RATE_LIMIT` | string | `100/minute` | Rate limiting (slowapi format) |
| `OPAMP_HEALTH_SNAPSHOT_RETENTION` | int | `1000` | Max health history records per collector |
| `OPAMP_EFFECTIVE_CONFIG_RETENTION` | int | `10` | Max effective config versions per collector |
| `OPAMP_COLLECTOR_TTL_HOURS` | int | `24` | Stale collector retention before purge |
| `OPAMP_PURGE_INTERVAL_HOURS` | int | `1` | How often to run stale collector cleanup |
| `OPAMP_LOG_LEVEL` | string | `INFO` | Python logging level (DEBUG/INFO/WARNING/ERROR) |

<!-- END AUTO-GENERATED -->

## Scripts & Commands

### Backend

<!-- AUTO-GENERATED: Scripts from Makefile and pytest -->

```bash
# Protocol buffer generation
make proto                 # Regenerate opamp_pb2.py and anyvalue_pb2.py from .proto files

# Testing
make test                  # Run pytest with coverage report (term-missing)
pytest tests/              # Run tests without coverage
pytest tests/ -v           # Verbose output

# Code quality
make lint                  # Run ruff check and format validation
ruff check opamp_server/   # Check only (no changes)
ruff format opamp_server/  # Auto-format code
```

**Development server:**
```bash
python server.py           # Runs uvicorn on 0.0.0.0:8000
```

### Frontend

```bash
npm run dev                # Vite dev server at http://localhost:5173 (proxies /api, /v1 to :8000)
npm run build              # Production build (TypeScript + Vite) → dist/
npm run type-check         # TypeScript type checking (no emit)
npm run test               # Vitest watch mode
npm run test -- --run      # Single test run (CI)
npm run test:coverage      # Coverage report
npm run lint               # ESLint check
npm run preview            # Preview production build locally
```

### Full Stack (Docker Compose)

```bash
# From repo root
docker compose up --build  # Build and start api, ui, and collector

# Individual services
docker compose up api      # Backend only
docker compose up ui       # UI only (proxies to api service)
docker compose up collector # Example collector only

# Clean up
docker compose down        # Stop all services (preserves data volume)
docker compose down -v     # Stop and remove data volume
```

<!-- END AUTO-GENERATED -->

## Testing

### Backend

The backend uses **pytest** with async support and coverage tracking.

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/test_collectors_api.py -v

# Run with verbose output and show print statements
pytest tests/ -v -s

# Specific test
pytest tests/test_collectors_api.py::test_list_collectors -v
```

**Coverage Target:** 80%+ (configured in `pyproject.toml`)

Test organization:
- `tests/test_*.py` — Unit and integration tests
- Tests use `pytest.mark.asyncio` for async test functions
- HTTP client testing uses `httpx.AsyncClient` with TestClient pattern

### Frontend

The frontend uses **Vitest** for unit tests and **React Testing Library** for component tests.

```bash
# Watch mode (recommended for development)
npm run test

# Single run (CI mode)
npm run test -- --run

# Coverage report
npm run test:coverage

# Specific test file
npm run test src/components/CollectorList.test.tsx

# UI dashboard (optional)
npm run test -- --ui
```

**Test markers:**
- `*.test.ts(x)` — Unit and component tests
- `*.spec.ts(x)` — Integration and behavioral tests

## Code Style

### Python

**Standards:**
- PEP 8 compliance
- Type annotations required on all function signatures
- Line length: 100 characters (configured in `pyproject.toml`)

**Formatting:**
- **ruff** for linting and auto-formatting
- Run `make lint` before committing

**Example:**
```python
from typing import Optional
import structlog

log = structlog.get_logger(__name__)

async def fetch_collector(
    collector_id: str,
    include_history: bool = True,
) -> Optional[dict]:
    """Fetch a collector by ID.
    
    Args:
        collector_id: Unique collector identifier
        include_history: Include health snapshot history
        
    Returns:
        Collector dict or None if not found
    """
    # Implementation...
```

### TypeScript/React

**Standards:**
- TypeScript strict mode (no `any`)
- ESLint with React hooks rules
- Functional components + hooks (no class components)
- Immutable data patterns

**Example:**
```typescript
import { FC, useEffect, useState } from "react";

interface CollectorProps {
  id: string;
  onSelect?: (id: string) => void;
}

const CollectorCard: FC<CollectorProps> = ({ id, onSelect }) => {
  const [data, setData] = useState<CollectorDetail | null>(null);

  useEffect(() => {
    fetchCollector(id).then(setData);
  }, [id]);

  return (
    <div onClick={() => onSelect?.(id)}>
      {data?.instance_uid}
    </div>
  );
};

export default CollectorCard;
```

## REST API Reference

<!-- AUTO-GENERATED: REST API endpoints from opamp_server/api -->

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/collectors` | List all registered collectors with summary data |
| `GET` | `/api/v1/collectors/{id}` | Full detail for a collector (health history, config, push status) |
| `GET` | `/api/v1/collectors/attrs/keys` | List all unique resource attribute keys across collectors |
| `POST` | `/api/v1/collectors/{id}/config` | Push a new YAML config to a collector |
| `POST` | `/v1/opamp` | OpAMP binary protobuf endpoint (used by collectors) |
| `GET` | `/api/v1/stats` | Server statistics (health check, uptime) |

**Response Format:**
All responses use a consistent envelope with `data` and `error` fields.

```json
{
  "data": { "instance_uid": "...", "health_status": "healthy" },
  "error": null
}
```

<!-- END AUTO-GENERATED -->

## Architecture Overview

### Backend Structure

```
opamp_server/
├── main.py              # FastAPI app creation, routes registration
├── server.py            # Uvicorn entry point
├── config.py            # Settings loaded from environment variables
├── protocol.py          # OpAMP protobuf serialization/deserialization
├── handler.py           # Core OpAMP message handling (state machine)
├── registry.py          # In-memory collector registry (active agents)
├── persistence.py       # SQLite database operations
├── config_manager.py    # Config push state machine and rollback
├── logging_config.py    # Structured logging setup (structlog)
└── api/
    ├── collectors.py    # Fleet management REST endpoints
    ├── config.py        # Config push POST endpoint
    └── stats.py         # Health check / stats endpoints
```

### Frontend Structure

```
ui/src/
├── App.tsx              # Main router and layout
├── pages/               # Page-level components
│   ├── CollectorListPage.tsx
│   ├── CollectorDetailPage.tsx
│   └── GettingStartedPage.tsx
├── components/          # Reusable UI components
│   ├── CollectorCard.tsx
│   ├── CapabilityChip.tsx
│   ├── ConfigEditor.tsx
│   └── ...
├── hooks/               # Custom React hooks
│   ├── useCollectors.ts
│   └── useColumnPrefs.ts
├── types/               # Zod schemas and TypeScript types
│   ├── api.ts          # API response types
│   └── domain.ts       # Domain models
└── lib/                 # Utilities
    └── api-client.ts   # HTTP client functions
```

## Database Schema

The database uses SQLite with the following tables:

- `agents` — Registered collectors (id, instance_uid, first_seen, last_seen)
- `health_snapshots` — Health history (agent_id, recorded_at, healthy, status, error)
- `effective_configs` — Current configs (agent_id, recorded_at, hash, config_json)
- `config_pushes` — Push state (agent_id, push_state, pending_hash)
- `agent_resource_attrs` — Resource attributes (agent_id, key, value)

See `opamp_server/persistence.py` for schema DDL.

## Common Tasks

### Adding a New REST Endpoint

1. Define request/response models in `opamp_server/api/your_module.py`
2. Implement route handler with type annotations
3. Register route in `opamp_server/main.py` (FastAPI `app.include_router()`)
4. Add tests in `tests/test_your_module.py`
5. Update API table in this document

### Modifying the Protocol

1. Update `.proto` files in `proto/`
2. Regenerate stubs: `make proto`
3. Update handler logic in `opamp_server/handler.py`
4. Update tests
5. Commit both `.proto` and generated `*_pb2.py` files

### Adding a UI Feature

1. Create component in `ui/src/components/`
2. Write tests in `ui/src/components/ComponentName.test.tsx`
3. Integrate into page component
4. Test with `npm run test` and `npm run type-check`
5. Verify styling with `npm run dev`

## Debugging

### Backend

**Enable debug logging:**
```bash
OPAMP_LOG_LEVEL=DEBUG python server.py
```

**Inspect database:**
```bash
sqlite3 ./data/registry.db
sqlite> .tables
sqlite> SELECT * FROM agents;
```

**Debug a test:**
```bash
pytest tests/test_collectors_api.py::test_name -v -s --pdb
```

### Frontend

**Browser DevTools:**
- React DevTools extension
- Network tab to inspect `/api/v1/collectors` responses
- Console for logging

**Vite HMR:**
Dev server automatically reloads on file changes (see `npm run dev`)

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

<optional body>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code restructuring (no behavior change)
- `docs:` Documentation updates
- `test:` Test additions or fixes
- `chore:` Build system, dependencies
- `perf:` Performance improvements

**Examples:**
```
feat: add collector health breakdown on detail page
fix: config editor not pre-populating effective config
docs: update environment variables table
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and run tests locally
3. Commit with conventional messages
4. Push: `git push -u origin feature/your-feature`
5. Open a PR with a clear description
6. Ensure CI passes (tests, linting)
7. Request review from maintainers

## Release Process

(Documented in RUNBOOK.md)

---

**Questions?** Check the planning docs in `.planning/` or open an issue.
