# OpAmp Server

## What This Is

A full-featured OpAMP (Open Agent Management Protocol) server and management UI for OpenTelemetry Contrib Collectors. It provides a Python/FastAPI backend that implements the CNCF OpAMP specification, a REST API for querying connected collectors, and a React UI for viewing collector health, inspecting and updating configs, and onboarding new collectors. The entire stack — server, UI, and an example collector — ships as Docker/Podman containers and starts with a single `docker compose up`.

## Core Value

Operators can see which collectors are connected, understand their health, and safely push config changes — all from a browser.

## Requirements

### Validated

- ✓ HTTP POST `/v1/opamp` endpoint accepting binary protobuf `AgentToServer` messages — v1.0
- ✓ Protobuf message decoding/encoding via generated `opamp_pb2` / `anyvalue_pb2` stubs — v1.0
- ✓ Docker container for the OpAmp server — v1.0
- ✓ Docker container for example OTel Contrib Collector pre-configured to connect to the server — v1.0
- ✓ Agent registry: track connected collectors by `instance_uid` with `sequence_num` tracking — v1.0 (Phase 1)
- ✓ Capability negotiation: capabilities=0x05 (AcceptsStatus | AcceptsEffectiveConfig) on every response — v1.0 (Phase 1)
- ✓ Health report handling: store_health_snapshot with rolling retention — v1.0 (Phase 1)
- ✓ Effective config storage: store_effective_config with rolling retention — v1.0 (Phase 1)
- ✓ Proper binary ServerErrorResponse on all error paths — v1.0 (Phase 1)
- ✓ Server instance_uid: UUID v7 via uuid6 — v1.0 (Phase 1)
- ✓ SQLite persistence with WAL mode: aiosqlite, init_db, startup hydration — v1.0 (Phase 1)
- ✓ Structured JSON logging via structlog — v1.0 (Phase 1)
- ✓ Request size limiting via MaxBodySizeMiddleware — v1.0 (Phase 1)
- ✓ Rate limiting via slowapi with binary error response — v1.0 (Phase 1)
- ✓ Pinned deps, pylance removed, requirements.in source of truth — v1.0 (Phase 1)
- ✓ make proto regeneration via Makefile + grpc_tools.protoc — v1.0 (Phase 1)
- ✓ Configurable bind address via OPAMP_HOST env var — v1.0 (Phase 1)
- ✓ Pinned collector Dockerfile (0.119.0) — v1.0 (Phase 1)
- ✓ Sequence gap detection: detect_sequence_gap + ReportFullState flag — v1.0 (Phase 1)
- ✓ PROTO-00 skeleton defects documented and fixed — v1.0 (Phase 1)
- ✓ Remote config push: push a new config to a collector via `ServerToAgent.remote_config` — v1.0 (Phase 2)
- ✓ Config push rollback: detect failure via `RemoteConfigStatus` and revert to previous config — v1.0 (Phase 2)
- ✓ Push state machine: IDLE/PUSH_PENDING/APPLYING/APPLIED/FAILED transitions — v1.0 (Phase 2)
- ✓ Double-push rejection: 409 Conflict when push already in progress — v1.0 (Phase 2)
- ✓ POST /api/v1/collectors/{id}/config REST endpoint — v1.0 (Phase 2)
- ✓ config_pushes SQLite table with rollback query support — v1.0 (Phase 2)
- ✓ Rollback anti-loop guard: prevents infinite rollback cycles — v1.0 (Phase 2)
- ✓ Push state hydration on server restart (APPLYING coerced to PUSH_PENDING) — v1.0 (Phase 2)
- ✓ GET /api/v1/collectors — JSON list of all collectors with health_status, capabilities — v1.0 (Phase 3)
- ✓ GET /api/v1/collectors/{id} — full detail with health_history, effective_config, push_status — v1.0 (Phase 3)
- ✓ Persistence functions for batch health and config queries — v1.0 (Phase 3)
- ✓ Collector list view at /collectors with 5s auto-polling, UID search, health filter — v1.0 (Phase 4)
- ✓ Collector detail page at /collectors/:id with health history and CodeMirror YAML editor — v1.0 (Phase 4)
- ✓ Config push flow: edit YAML, POST to API, watch PUSH_PENDING/APPLYING/APPLIED/FAILED — v1.0 (Phase 4)
- ✓ Push failure callout with explicit rollback confirmation — v1.0 (Phase 4)
- ✓ Getting Started page with CopyButton, base config YAML, dynamic server endpoint URL — v1.0 (Phase 4)
- ✓ Self-hosted Roboto variable font via @font-face (no Google CDN) — v1.0 (Phase 4)
- ✓ Vite 8 + React 19 + TypeScript scaffold with Tailwind v4, shadcn/ui — v1.0 (Phase 4)
- ✓ Multi-stage Dockerfile (node:20-alpine + nginx:1.27-alpine) with SPA fallback and /api/ proxy — v1.0 (Phase 4)
- ✓ Docker Compose file (`compose.yaml`) bringing up server + UI + example collector as unified stack — v1.0 (Phase 5)
- ✓ CapabilityChip/CapabilityChipList: decode OpAMP bitmask into named chips ("Remote Config", "Health") with hex fallback for unknown bits — v1.1 (Phase 6)
- ✓ Config editor pre-seed: seededRef guard seeds CodeMirror with effective_config on first data arrival, poll-safe — v1.1 (Phase 6)
- ✓ Getting Started BASE_CONFIG_YAML enriched with host.name, service.instance.id, deployment.environment, host.ip — v1.1 (Phase 6)
- ✓ compose.yaml collector service pinned to otel/opentelemetry-collector-contrib:0.119.0 — v1.1 (Phase 6)
- ✓ Status landing page at `/`: OTel hero gradient, live "X of Y agents healthy" count (5s poll), Status nav item — v1.1 (Phase 7)
- ✓ GET /api/v1/stats endpoint: total and healthy agent counts — v1.1 (Phase 7)
- ✓ Stale collector TTL purge: background asyncio task, OPAMP_COLLECTOR_TTL_HOURS env var (default 24), push-state guard — v1.1 (Phase 8)
- ✓ registry.remove() and persistence.purge_agent() with ordered child-table deletes — v1.1 (Phase 8)
- ✓ Dynamic resource attribute columns: agent_description parsed and stored per collector in agent_resource_attrs table — v1.1 (Phase 9)
- ✓ GET /api/v1/collectors returns resource_attributes dict per collector (additive, backward-compatible) — v1.1 (Phase 9)
- ✓ GET /api/v1/collectors/attrs/keys returns union of all discovered attribute keys — v1.1 (Phase 9)
- ✓ Column picker with localStorage persistence; host.name visible by default; new keys auto-appear on next poll — v1.1 (Phase 9)

## Current State: v1.1 Shipped

v1.1 Operator UX shipped 2026-04-07. All 23 requirements delivered across 4 phases (Phases 6-9).

**What shipped:**
- Capability chips replacing raw OpAMP bitmask integers
- Config editor pre-seeded from effective_config on page load
- Status landing page at `/` with live healthy-agent count
- Stale collector TTL purge (background asyncio, configurable, push-state guard)
- Dynamic resource attribute columns with column picker and localStorage persistence

### Out of Scope

- Authentication / authorization — deferred to a later milestone; v1 is an internal/dev tool
- WebSocket OpAMP transport — HTTP polling only for v1; spec-defined but adds complexity
- Package management via OpAMP (`PackagesAvailable` / `PackageStatuses`) — advanced feature for later
- Multi-user / RBAC — single-operator tool for v1
- External database (PostgreSQL, etc.) — SQLite covers the scale and avoids operational overhead
- TLS termination on the server directly — leave to reverse proxy or later milestone

## Context

**Current state (v1.1):** Fully functional OpAMP server and management UI with enhanced operator UX. ~7,100 lines of code (py + ts + tsx). Stack: Python 3.11 / FastAPI / SQLite / aiosqlite / structlog / slowapi; React 19 / Vite 8 / TypeScript / Tailwind v4 / shadcn/ui / CodeMirror; nginx Docker image for UI serving. Full TDD — all phases started with failing stubs before implementation.

**Companion collector:** `collector/` contains an OTel Contrib Collector (0.119.0) Dockerfile and `config.yaml` (standalone) + `config.compose.yaml` (Compose-aware with DNS name `api:8000`) pre-configured to connect to the server via HTTP polling every 5 seconds.

**Protocol:** OpAMP is the CNCF standard for remotely managing OpenTelemetry Collectors. The server communicates via binary Protobuf over HTTP POST.

**Scale target:** 100+ concurrent collectors. SQLite with WAL mode and connection pooling is adequate for this range.

**Known tech debt:**
- One pre-existing test failure in `tests/test_config_push.py::test_failed_triggers_rollback` (confirmed pre-existing, unrelated to v1.1 changes; deferred)

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
| SQLite for persistence | No external DB dependency; WAL mode handles 100+ concurrent readers; avoids operational overhead for v1 | ✓ Good — no operational friction during development |
| HTTP polling only (no WebSocket) | Simpler to implement; existing collector config uses HTTP; WebSocket adds connection management complexity | ✓ Good — 5s polling is imperceptible to operators |
| React for UI | User requirement; widely supported ecosystem; good fit for real-time-updating state displays | ✓ Good — TanStack Query + polling pattern worked cleanly |
| No auth for v1 | Internal/dev tool scope; reduces initial complexity; can be added as a later milestone | ✓ Good — kept scope tight; v2 will add bearer token |
| Config rollback on push failure | OpAMP spec-aligned; prevents collectors from ending up in a broken config state | ✓ Good — anti-loop guard prevents infinite rollback cycles |
| Use ui-ux-pro skill for all UI phases | Ensures consistent, high-quality visual design; Roboto font alignment | ✓ Good — UI component quality and visual consistency were high |
| TDD for all phases (failing stubs first) | Catches regressions early; forces interface design before implementation | ✓ Good — all phases used wave-0 stubs pattern |
| capabilities=0x07 (AcceptsRemoteConfig added in Phase 2) | Phase 1 used 0x05; Phase 2 added AcceptsRemoteConfig capability bit correctly | ✓ Good — backward-compatible upgrade |
| seededRef guard for config editor pre-seed | One-shot useEffect guard prevents background poll from overwriting in-progress edits | ✓ Good — handleEditStart fallback retained for re-entry into edit mode |
| asyncio.Task stored in app.state.purge_task | Prevents GC of unawaited background tasks; app.state is canonical FastAPI per-app store | ✓ Good — getattr guard covers partial startup failures |
| Ordered child-table deletes for purge (no FK cascade) | SQLite FK cascade is OFF by default; explicit delete order prevents constraint violations | ✓ Good — agent_resource_attrs added to delete order in Phase 9 |
| attrs/keys route registered before /{id} route | FastAPI path matching is first-match; /attrs/keys would be shadowed by /{id} if registered second | ✓ Good — route ordering documented as critical pattern |
| Node.js 22+ globalThis.localStorage shim in setupTests | Built-in localStorage in Node 22 shadows jsdom's Storage, breaking vitest | ✓ Good — fixed by pointing globalThis.localStorage at window._localStorage |

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
*Last updated: 2026-04-07 — after v1.1 Operator UX milestone*
