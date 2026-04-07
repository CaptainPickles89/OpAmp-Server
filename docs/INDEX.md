# OpAMP Server Documentation Index

Quick reference guide to all documentation for the OpAMP Server project.

## Core Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](../README.md) | Project overview and quick start | Everyone |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup, testing, code standards | Developers |
| [RUNBOOK.md](RUNBOOK.md) | Deployment, operations, troubleshooting | DevOps / SRE |

## Frontend Documentation

| Document | Purpose |
|----------|---------|
| [ui/README.md](../ui/README.md) | React UI build/dev/Docker setup |

## Project Planning

Project milestones, roadmaps, and phase documentation are in `.planning/`:

- `.planning/PROJECT.md` — Project charter and requirements
- `.planning/STATE.md` — Current project status and phase tracking
- `.planning/ROADMAP.md` — v1.0, v1.1, v1.2+ milestones
- `.planning/RETROSPECTIVE.md` — Post-mortem from v1.0 and v1.1 delivery

## Quick Links

### Getting Started
1. Clone repository: `git clone <url>`
2. Follow [Quick start](../README.md#quick-start) in README
3. Review [Development setup](CONTRIBUTING.md#development-setup) in CONTRIBUTING

### Making Changes
1. Understand [Architecture](CONTRIBUTING.md#architecture-overview) in CONTRIBUTING
2. Follow [Code style](CONTRIBUTING.md#code-style)
3. Write tests (see [Testing](CONTRIBUTING.md#testing))
4. Use [Commit message convention](CONTRIBUTING.md#commit-message-convention)

### Deploying to Production
1. Review [Deployment](RUNBOOK.md#deployment) in RUNBOOK
2. Configure environment via [Environment Configuration](RUNBOOK.md#environment-configuration)
3. Set up [Health Checks](RUNBOOK.md#health-checks)
4. Establish [Monitoring](RUNBOOK.md#monitoring)

### Troubleshooting
See [Troubleshooting](RUNBOOK.md#troubleshooting) section in RUNBOOK for:
- Collectors not connecting
- API service issues
- Database problems
- Performance issues

## API Reference

See [REST API Reference](CONTRIBUTING.md#rest-api-reference) in CONTRIBUTING for all endpoints and response formats.

## Environment Variables

See [Environment Variables](CONTRIBUTING.md#environment-variables) in CONTRIBUTING for all configuration options.

## Architecture

### Layers

```
┌─────────────────────────────────────────┐
│         React UI (Vite)                 │
│    http://localhost:8080                │
└────────────┬────────────────────────────┘
             │ /api, /v1 proxies
             │
┌────────────▼────────────────────────────┐
│       FastAPI Server (Port 8000)        │
│  ├── REST API (/api/v1/...)             │
│  ├── OpAMP Protocol (/v1/opamp)         │
│  └── Health Check (/api/v1/collectors)  │
└────────────┬────────────────────────────┘
             │ Reads/writes
             │
┌────────────▼────────────────────────────┐
│      SQLite Registry                    │
│  ├── agents (collectors)                │
│  ├── health_snapshots                   │
│  ├── effective_configs                  │
│  ├── config_pushes (state machine)      │
│  └── agent_resource_attrs               │
└─────────────────────────────────────────┘

Collectors (OTel Contrib) ──OpAMP──> /v1/opamp
```

### Key Design Patterns

- **OpAMP Protocol** — Binary over HTTP/1.1, request/response model
- **Config Push State Machine** — Pending → Applying → Applied/Failed → Rollback
- **SQLite Persistence** — Agent registry, health history, config versions
- **REST API** — Fleet management, detail views, config operations
- **React UI** — Real-time dashboard, config editor, getting started guide

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115
- **Server**: Uvicorn 0.34
- **Database**: SQLite with aiosqlite
- **Protocol**: gRPC protobuf (OpAMP spec)
- **Logging**: structlog 25.1
- **Testing**: pytest 8.3, pytest-asyncio 0.24

### Frontend
- **Framework**: React 19
- **Build**: Vite 8.0, TypeScript 5.9
- **Routing**: React Router 7.13
- **State**: TanStack React Query 5.95
- **UI**: shadcn/ui + Tailwind CSS 4.0
- **Validation**: Zod 4.3
- **Themes**: next-themes 0.4
- **Editor**: CodeMirror 6 + uiw
- **Testing**: Vitest 4.1, React Testing Library 16.3
- **Mocking**: MSW 2.12

### Infrastructure
- **Docker**: Compose (api, ui, collector services)
- **Base Images**: Python 3.11-slim, node:20-slim
- **Networking**: Internal Docker network + port mapping
- **Persistence**: Named volume (`opamp-data`)

## Support & Community

- **Issues/PRs**: GitHub repository
- **Discussions**: GitHub Discussions
- **Status Page**: Available at http://localhost:8080/api/v1/stats (after deployment)

---

**Documentation Last Updated:** 2026-04-07  
**OpAMP Server Version:** v1.1 (Operator UX)

For detailed version history, see `.planning/ROADMAP.md`.
