# OpAmp Server

## What This Is

A full-featured OpAMP (Open Agent Management Protocol) server and management UI for OpenTelemetry Contrib Collectors. It provides a Python/FastAPI backend that implements the CNCF OpAMP specification, a REST API for querying connected collectors, and a React UI for viewing collector health, inspecting and updating configs, and onboarding new collectors. The entire stack — server, UI, and an example collector — ships as Docker/Podman containers.

## Core Value

Operators can see which collectors are connected, understand their health, and safely push config changes — all from a browser.

## Requirements

### Validated

- ✓ HTTP POST `/v1/opamp` endpoint accepting binary protobuf `AgentToServer` messages — existing
- ✓ Protobuf message decoding/encoding via generated `opamp_pb2` / `anyvalue_pb2` stubs — existing
- ✓ Docker container for the OpAmp server — existing
- ✓ Docker container for example OTel Contrib Collector pre-configured to connect to the server — existing

### Active

**Server — Protocol:**
- [ ] Agent registry: track connected collectors by `instance_uid` with session state and `sequence_num` validation
- [ ] Capability negotiation: parse incoming `capabilities` bitmask and respond with server capabilities
- [ ] Health report handling: receive, parse, and store `ComponentHealth` from each agent
- [ ] Effective config storage: receive and persist the current config reported by each agent
- [ ] Remote config push: push a new config to a collector via `ServerToAgent.remote_config`
- [ ] Config push rollback: detect failure via `RemoteConfigStatus` and revert to previous config
- [ ] Proper `ServerToAgent` error responses using protobuf `ServerErrorResponse` (not JSON)
- [ ] Server `instance_uid`: generate a proper UUID v7 at startup (not hardcoded `b"server-1234"`)

**Server — API:**
- [ ] `GET /api/v1/collectors` — JSON list of all connected collectors with health and metadata
- [ ] `GET /api/v1/collectors/{id}` — JSON detail for a single collector (health, config, history)
- [ ] `POST /api/v1/collectors/{id}/config` — push a new config to a collector

**Server — Infrastructure:**
- [ ] SQLite persistence: agent state and config history survive server restarts
- [ ] Structured JSON logging (replace raw protobuf log lines)
- [ ] Request size limiting (prevent memory exhaustion from oversized payloads)
- [ ] Rate limiting middleware
- [ ] Pin all Python dependencies with a lockfile; remove `pylance` from `requirements.txt`
- [ ] Protobuf codegen tooling: `Makefile` target or `generate.sh` to regenerate `*_pb2.py` from `.proto`
- [ ] Configurable bind address via environment variable (default `0.0.0.0` for container, `127.0.0.1` for dev)

**UI:**
- [ ] Collector list view: all connected collectors with health status indicators and last-seen time
- [ ] Collector detail view: health breakdown, current effective config, config history
- [ ] Config editor: view current config, edit and push to collector, see push status
- [ ] Config failure handling: display error message and confirm rollback to previous config
- [ ] "Getting Started" page: onboarding guide with a base collector config example that can be applied to connect a new collector
- [ ] React frontend using Roboto font (provided in repo root); ui-ux-pro skill used for all UI phases
- [ ] UI built with a note to invoke `/ui-ux-pro-max` skill during UI phase planning

**Orchestration:**
- [ ] Docker Compose file bringing up server + UI + example collector as a unified stack
- [ ] Collector Dockerfile pinned to a specific OTel Contrib version (not `latest`)

### Out of Scope

- Authentication / authorization — deferred to a later milestone; v1 is an internal/dev tool
- WebSocket OpAMP transport — HTTP polling only for v1; spec-defined but adds complexity
- Package management via OpAMP (`PackagesAvailable` / `PackageStatuses`) — advanced feature for later
- Multi-user / RBAC — single-operator tool for v1
- External database (PostgreSQL, etc.) — SQLite covers the scale and avoids operational overhead
- TLS termination on the server directly — leave to reverse proxy or later milestone

## Context

**Existing skeleton:** The repo contains a 36-line `server.py` (FastAPI, Python 3.11) that decodes `AgentToServer` protobuf messages and returns a minimal stub `ServerToAgent` response. It is stateless, has no agent registry, and has zero test coverage. The protobuf generated stubs (`opamp_pb2.py`, `anyvalue_pb2.py`) are present and functional.

**Companion collector:** `collector/` contains an OTel Contrib Collector Dockerfile and `config.yaml` pre-configured to connect to the server via HTTP polling every 5 seconds. It reports `effective_config`, `health`, and `available_components`. The collector `instance_uid` is currently non-deterministic (auto-generated).

**Protocol:** OpAMP is the CNCF standard for remotely managing OpenTelemetry Collectors. The server communicates via binary Protobuf over HTTP POST. The spec requires tracking `sequence_num` per agent, proper UUID v7 `instance_uid`, capability bitmask negotiation, and typed `ServerErrorResponse` on failure.

**Scale target:** 100+ concurrent collectors. SQLite with WAL mode and connection pooling is adequate for this range.

**UI fonts:** Roboto font files are in the repo root and must be used across all UI components.

## Constraints

- **Tech Stack**: Python 3.11 / FastAPI server — existing foundation, do not migrate
- **Tech Stack**: React for the UI — user requirement
- **Tech Stack**: SQLite for persistence — no external database dependency for v1
- **Protocol**: CNCF OpAMP specification compliance — all agent interactions must conform
- **Containers**: Docker and Podman compatible — use `compose.yaml` (not `docker-compose.yml`) for broader compatibility
- **Font**: Roboto font from repo root for all UI typography
- **Planning files**: `.planning/`, `.claude/`, and GSD-related files must be in `.gitignore`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite for persistence | No external DB dependency; WAL mode handles 100+ concurrent readers; avoids operational overhead for v1 | — Pending |
| HTTP polling only (no WebSocket) | Simpler to implement; existing collector config uses HTTP; WebSocket adds connection management complexity | — Pending |
| React for UI | User requirement; widely supported ecosystem; good fit for real-time-updating state displays | — Pending |
| No auth for v1 | Internal/dev tool scope; reduces initial complexity; can be added as a later milestone | — Pending |
| Config rollback on push failure | OpAMP spec-aligned; prevents collectors from ending up in a broken config state | — Pending |
| Use ui-ux-pro skill for all UI phases | Ensures consistent, high-quality visual design; Roboto font alignment | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-27 after initialization*
