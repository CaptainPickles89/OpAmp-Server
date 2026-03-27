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
- ✓ Agent registry: track connected collectors by `instance_uid` with `sequence_num` tracking — Validated in Phase 1 (REGST-01)
- ✓ Capability negotiation: capabilities=0x05 (AcceptsStatus | AcceptsEffectiveConfig) on every response — Validated in Phase 1 (PROTO-03)
- ✓ Health report handling: store_health_snapshot with rolling retention — Validated in Phase 1 (REGST-04)
- ✓ Effective config storage: store_effective_config with rolling retention — Validated in Phase 1 (REGST-05)
- ✓ Proper binary ServerErrorResponse on all error paths — Validated in Phase 1 (PROTO-04)
- ✓ Server instance_uid: UUID v7 via uuid6 — Validated in Phase 1 (PROTO-01)
- ✓ SQLite persistence with WAL mode: aiosqlite, init_db, startup hydration — Validated in Phase 1 (REGST-02, REGST-03)
- ✓ Structured JSON logging via structlog — Validated in Phase 1 (OPS-04)
- ✓ Request size limiting via MaxBodySizeMiddleware — Validated in Phase 1 (PROTO-05)
- ✓ Rate limiting via slowapi with binary error response — Validated in Phase 1 (PROTO-06)
- ✓ Pinned deps, pylance removed, requirements.in source of truth — Validated in Phase 1 (OPS-01)
- ✓ make proto regeneration via Makefile + grpc_tools.protoc — Validated in Phase 1 (OPS-02)
- ✓ Configurable bind address via OPAMP_HOST env var — Validated in Phase 1 (OPS-03)
- ✓ Pinned collector Dockerfile (0.119.0) — Validated in Phase 1 (OPS-06)
- ✓ Sequence gap detection: detect_sequence_gap + ReportFullState flag — Validated in Phase 1 (PROTO-02)
- ✓ PROTO-00 skeleton defects documented and fixed — Validated in Phase 1
- ✓ Remote config push: push a new config to a collector via `ServerToAgent.remote_config` — Validated in Phase 2 (CFGMG-01, CFGMG-02)
- ✓ Config push rollback: detect failure via `RemoteConfigStatus` and revert to previous config — Validated in Phase 2 (CFGMG-04)
- ✓ Push state machine: IDLE/PUSH_PENDING/APPLYING/APPLIED/FAILED transitions — Validated in Phase 2 (CFGMG-03)
- ✓ Double-push rejection: 409 Conflict when push already in progress — Validated in Phase 2 (CFGMG-05)
- ✓ POST /api/v1/collectors/{id}/config REST endpoint — Validated in Phase 2 (CFGMG-01)
- ✓ config_pushes SQLite table with rollback query support — Validated in Phase 2
- ✓ Rollback anti-loop guard: prevents infinite rollback cycles — Validated in Phase 2
- ✓ Push state hydration on server restart (APPLYING coerced to PUSH_PENDING) — Validated in Phase 2

### Active

**Server — API:**
- [ ] `GET /api/v1/collectors` — JSON list of all connected collectors with health and metadata
- [ ] `GET /api/v1/collectors/{id}` — JSON detail for a single collector (health, config, history)

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
*Last updated: 2026-03-27 after Phase 2 completion — Config Push and Rollback complete*
