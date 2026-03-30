---
phase: 07-status-landing-page
plan: "01"
subsystem: stats-endpoint
tags: [backend, frontend, fastapi, tanstack-query, zod, msw]
dependency_graph:
  requires: []
  provides: [GET /api/v1/stats, useStats hook, StatsSchema, fetchStats, MSW /api/v1/stats mock]
  affects: [ui/src/api/types.ts, ui/src/api/client.ts, opamp_server/api/__init__.py]
tech_stack:
  added: []
  patterns: [TanStack Query polling, Zod schema validation, FastAPI APIRouter, MSW handler extension]
key_files:
  created:
    - opamp_server/api/stats.py
    - tests/test_stats.py
    - ui/src/hooks/useStats.ts
  modified:
    - opamp_server/api/__init__.py
    - ui/src/api/types.ts
    - ui/src/api/client.ts
    - ui/src/mocks/handlers.ts
decisions:
  - "_derive_health_status duplicated in stats.py rather than imported from collectors.py to avoid coupling between endpoint modules"
metrics:
  duration: "117s"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_changed: 7
---

# Phase 7 Plan 1: Stats Endpoint and Frontend Data Layer Summary

**One-liner:** GET /api/v1/stats endpoint counting healthy agents from health snapshots, wired to a 5s-polling useStats hook with Zod validation and MSW mock.

## Objective

Create the GET /api/v1/stats backend endpoint, its frontend data layer (Zod schema, API client function, TanStack Query hook), MSW mock handler, and backend tests.

## What Was Built

### Task 1: Backend stats endpoint with tests (TDD)

**Commit:** b93869f

- `opamp_server/api/stats.py` — FastAPI router with `GET /stats`, `StatsResponse` Pydantic model, and duplicated `_derive_health_status` function
- `opamp_server/api/__init__.py` — registered `stats_router` after existing routers
- `tests/test_stats.py` — 3 integration tests:
  - `test_stats_empty_registry` — empty registry returns `{"healthy_count": 0, "total_count": 0}`
  - `test_stats_one_healthy_agent` — one healthy agent returns `{"healthy_count": 1, "total_count": 1}`
  - `test_stats_agent_no_health_snapshot` — agent with no snapshot returns `{"healthy_count": 0, "total_count": 1}`

TDD flow: RED (404 on missing route) → GREEN (all 3 pass).

### Task 2: Frontend data layer (8d79717)

**Commit:** 8d79717

- `ui/src/api/types.ts` — added `StatsSchema` (z.object with healthy_count, total_count) and `Stats` type
- `ui/src/api/client.ts` — added `fetchStats()` calling `/api/v1/stats` with `StatsSchema.parse`; updated imports to include `Stats` and `StatsSchema`
- `ui/src/hooks/useStats.ts` — TanStack Query hook with `queryKey: ['stats']`, `refetchInterval: 5000`, `staleTime: 4000`
- `ui/src/mocks/handlers.ts` — added `http.get('/api/v1/stats', ...)` returning `{healthy_count: 1, total_count: 2}`

TypeScript compiles with no errors.

## Decisions Made

1. `_derive_health_status` is duplicated in `stats.py` rather than imported from `collectors.py` — this is a deliberate design choice to avoid coupling between endpoint modules. Both modules can evolve independently. The function is a 10-line pure helper.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data flows are wired. The MSW mock returns `{healthy_count: 1, total_count: 2}` which is intentional test data, not a stub in the production path.

## Verification Results

- `python -m pytest tests/test_stats.py -x -q` — 3 passed
- `cd ui && npx tsc --noEmit` — exits 0, no errors

## Self-Check: PASSED

Files confirmed present:
- opamp_server/api/stats.py — FOUND
- tests/test_stats.py — FOUND
- ui/src/hooks/useStats.ts — FOUND
- opamp_server/api/__init__.py — FOUND (modified)
- ui/src/api/types.ts — FOUND (modified)
- ui/src/api/client.ts — FOUND (modified)
- ui/src/mocks/handlers.ts — FOUND (modified)

Commits confirmed:
- b93869f — feat(07-01): add GET /api/v1/stats backend endpoint with tests
- 8d79717 — feat(07-01): add frontend data layer for stats endpoint
