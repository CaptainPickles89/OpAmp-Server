# OpAMP Server Features & Release Notes

## Current Version: v1.1 — Operator UX (Released 2026-04-07)

### What's New in v1.1

#### UI Improvements

**1. Redesigned Collector Detail Page**
- Full collector health breakdown with status indicators
- Visual capability display using capability chips (bitmask decode + hex notation)
- Improved navigation back to fleet view
- Real-time health status updates

**2. Dynamic Resource Attribute Columns**
- Collectors can now report custom resource attributes (e.g., pod name, region, version)
- UI dynamically discovers all attributes in use across fleet
- Column picker to customize visible attributes per session
- Column preferences persisted to browser localStorage
- Attributes displayed inline in collector list view

**3. Theme Support**
- Light and dark mode toggle
- System preference detection (respects OS theme)
- Theme preference persisted across sessions
- Tailwind CSS theme tokens

**4. Enhanced Config Editor**
- Fixed issue where effective config wasn't pre-populating
- Now loads current config from last known successful push
- Better error handling for arbitrary YAML keys
- CodeMirror integration with syntax highlighting

#### Backend Improvements

**1. Stale Collector TTL & Auto-Purge**
- Collectors not reporting for >24 hours are automatically purged
- Configurable TTL via `OPAMP_COLLECTOR_TTL_HOURS` (default: 24)
- Background task runs every `OPAMP_PURGE_INTERVAL_HOURS` (default: 1)
- Cascade delete removes all associated health snapshots, configs, and push state
- Graceful lifecycle management in FastAPI startup/shutdown hooks

**2. Resource Attribute Extraction**
- Handler extracts resource attributes from collector's agent description
- Persists attributes to `agent_resource_attrs` table for querying
- REST API endpoint `/api/v1/collectors/attrs/keys` lists all unique attribute keys
- Enables dynamic column discovery in UI

**3. Effective Config Signal**
- Improved effective config tracking and display
- Better separation between pending config (being pushed) and effective config (applied)
- UI now correctly reflects which config version is actually running

#### API Additions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/collectors/attrs/keys` | GET | List unique resource attribute keys across all collectors |
| `/api/v1/stats` | GET | Server health check and uptime |

### v1.0 Features (Foundation)

#### Protocol & Core
- Full OpAMP protocol implementation (spec-compliant)
- Binary protobuf serialization over HTTP/1.1
- Config push with rollback state machine
- Health snapshot reporting from collectors

#### REST API
- `GET /api/v1/collectors` — Fleet view with summary data
- `GET /api/v1/collectors/{id}` — Detailed collector info
- `POST /api/v1/collectors/{id}/config` — Push new config
- `POST /v1/opamp` — OpAMP protocol endpoint

#### Management UI
- **Fleet Dashboard** — List all collectors with health indicators
- **Collector Detail** — View individual collector health, config, and push status
- **Config Editor** — YAML editor with syntax highlighting
- **Getting Started** — Quick onboarding guide with base config template
- **Responsive Design** — Mobile-friendly Tailwind CSS

#### Data Persistence
- SQLite agent registry
- Health snapshot history (up to 1000 per collector by default)
- Effective config versions (up to 10 per collector by default)
- Config push state tracking
- Automatic TTL-based cleanup

#### Docker Compose Stack
- `api` service — FastAPI server
- `ui` service — nginx SPA + reverse proxy
- `collector` service — Example OTel Collector pre-configured
- Health checks and automatic restart
- Data volume persistence across restarts

---

## Known Limitations & Future Work

### Not Yet Implemented

- **Metrics Export** — Prometheus-compatible `/metrics` endpoint (planned for v1.2)
- **Multi-User Support** — No authentication/authorization (single-operator mode)
- **Audit Logging** — Config push history and change tracking (planned)
- **Collector Groups** — Tag-based collector organization (planned)
- **Advanced Filtering** — Search/filter collectors by attributes (planned)

### Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Performance Characteristics

- **API Response Time** — <100ms for typical fleet sizes (100-1000 collectors)
- **Database Size** — ~1-2KB per collector (depends on health snapshot retention)
- **Memory Usage** — ~100-200MB for 1000 collectors (in-memory registry)
- **Config Push Latency** — 1-5 seconds (depends on collector response time)

### Scaling Limits (Single Server)

- **Collectors** — Tested to ~5000 concurrent collectors
- **Health Snapshots** — Up to 1M per collector (configurable retention)
- **Concurrent Config Pushes** — Limited by FastAPI worker threads (default 4)

For larger deployments, consider:
- Load balancing across multiple OpAMP server instances
- Separate database server (PostgreSQL migration path planned for v2.0)
- External metrics collection (Prometheus, Honeycomb, etc.)

---

## Capability Bits Reference

Collectors report capabilities as a bitmask. UI decodes and displays them as labeled chips:

| Value | Hex | Capability |
|-------|-----|-----------|
| 1 | 0x1 | AcceptsRemoteConfig |
| 2 | 0x2 | ReportsEffectiveConfig |
| 4 | 0x4 | ReportsOwnMetrics |
| 8 | 0x8 | ReportsOwnTraces |
| 16 | 0x10 | ReportsOwnLogs |
| 32 | 0x20 | AcceptsPackages |
| 64 | 0x40 | ReportsRemoteConfig |
| 128 | 0x80 | (Reserved) |
| 256+ | 0x100+ | Custom/future capabilities |

Unknown bits are displayed in hex format (e.g., "0x400").

---

## Configuration Examples

### Enable Debug Logging
```bash
OPAMP_LOG_LEVEL=DEBUG docker compose up api
```

### Faster TTL Purge (for testing)
```bash
OPAMP_COLLECTOR_TTL_HOURS=1 OPAMP_PURGE_INTERVAL_HOURS=1 docker compose up
```

### Increase Config History Retention
```bash
OPAMP_EFFECTIVE_CONFIG_RETENTION=50 docker compose up
```

### Larger Request Size (for big configs)
```bash
OPAMP_MAX_BODY_SIZE=10485760 docker compose up  # 10 MB
```

---

## Migration Guide: v1.0 → v1.1

No breaking changes! Databases from v1.0 continue to work with v1.1.

**What's Backward Compatible:**
- All REST API endpoints (v1.0 endpoints unchanged)
- SQLite schema (new columns added, old columns preserved)
- Collector protocol (OpAMP spec compliance)
- Docker Compose configuration (updated `compose.yaml` is superset)

**UI Changes:**
- New detail page layout — no breaking changes
- Theme support — defaults to light mode if not set
- Column picker — localStorage key: `opamp_columns_visible`
- Effective config signal — automatic, no user action needed

**Database Schema Evolution:**
- New table: `agent_resource_attrs` (automatically created on startup)
- Existing tables: `agents`, `health_snapshots`, `effective_configs`, `config_pushes` unchanged
- Migration is automatic — v1.1 server handles schema initialization

---

## Support & Reporting

### Report a Bug
1. Check existing issues in GitHub
2. Reproduce on latest code
3. Include:
   - Docker version and OS
   - Reproduction steps
   - API/UI logs (redact sensitive info)
   - Database state if relevant

### Request a Feature
1. Check roadmap in `.planning/ROADMAP.md`
2. Describe use case and expected behavior
3. Include relevant real-world examples

---

**For detailed technical documentation, see:**
- [CONTRIBUTING.md](CONTRIBUTING.md) — Development setup
- [RUNBOOK.md](RUNBOOK.md) — Operations
- [README.md](../README.md) — Quick start
