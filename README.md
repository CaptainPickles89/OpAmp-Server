# OpAMP Server
<p>
    <img src="https://skills-icons.vercel.app/api/icons?i=docker,otel,fastapi,python,react" />
</p>

A spec-compliant [CNCF OpAMP](https://opentelemetry.io/docs/specs/opamp/) server and management UI for OpenTelemetry Contrib Collectors. Operators can see which collectors are connected, inspect their health, and safely push config changes — all from a browser.

## What's included

- **FastAPI server** — implements the OpAMP protocol over HTTP POST, with a persistent agent registry (SQLite), config push state machine, and JSON REST API
- **React UI** — fleet dashboard with health status, config editor, and getting started guide
- **Example collector** — OTel Contrib Collector pre-configured to connect to the server
- **Docker Compose** — single command to bring the whole stack up

## Quick start

**Prerequisites:** Docker (or Podman) with Compose support.

```bash
docker compose up --build
```

That's it. The first run builds all three images.

| Service | URL |
|---------|-----|
| Management UI | http://localhost:8080 |
| REST API | http://localhost:8080/api/v1/collectors |
| OpAMP endpoint | http://localhost:8080/v1/opamp |

The example collector starts automatically and connects to the server — you should see it appear in the UI within a few seconds.

## Usage

- **Fleet view** — open http://localhost:8080 to see all connected collectors with health status and last-seen timestamps (auto-refreshes every 5 seconds)
- **Collector detail** — click any collector to see its health breakdown and current effective config
- **Config push** — edit the config in the browser editor and click Push; the UI shows status moving from Pending through Applying to Applied (or Failed with auto-rollback)
- **Getting started** — the Getting Started page has a base collector config you can copy to onboard a new collector

## Data persistence

SQLite data is stored in a named Docker volume (`opamp-data`) and survives restarts:

```bash
docker compose down      # stops stack, data preserved
docker compose up        # collector reappears in registry with full history

docker compose down -v   # stops stack AND wipes the volume
```

## Development

```bash
# Backend (Python 3.11)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/

# Regenerate protobuf stubs
make proto

# Frontend (Node 20)
cd ui
npm install
npm run dev   # dev server at http://localhost:5173 (proxies /api to localhost:8000)
npm test
npm run build
```

## REST API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/collectors` | List all connected collectors |
| `GET` | `/api/v1/collectors/{id}` | Detail for a single collector (health, config, push status) |
| `GET` | `/api/v1/collectors/attrs/keys` | List all known resource attribute keys (for dynamic columns) |
| `GET` | `/api/v1/stats` | Fleet health summary: healthy and total collector counts |
| `POST` | `/api/v1/collectors/{id}/config` | Push a new YAML config to a collector |
| `POST` | `/v1/opamp` | OpAMP binary protobuf endpoint (used by collectors) |

## Note on port 80

The UI is mapped to `8080:80` for compatibility with rootless container runtimes (Podman, rootless Docker). If you are running Docker Desktop and prefer port 80, change `"8080:80"` to `"80:80"` in `compose.yaml`.

---

Built with [Claude Code](https://claude.ai/code).
