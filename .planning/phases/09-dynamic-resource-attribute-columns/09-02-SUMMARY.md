---
phase: 09-dynamic-resource-attribute-columns
plan: 02
subsystem: api-layer
tags: [api, zod, typescript, resource-attributes, collectors]
dependency_graph:
  requires: ["09-01"]
  provides: ["resource_attributes in list endpoint", "attrs/keys endpoint", "ResourceAttrKeysSchema", "fetchResourceAttrKeys"]
  affects: ["09-03", "09-04"]
tech_stack:
  added: []
  patterns: ["Zod schema extension with .default()", "FastAPI route ordering (static before parametric)"]
key_files:
  created: []
  modified:
    - opamp_server/api/collectors.py
    - ui/src/api/types.ts
    - ui/src/api/client.ts
decisions:
  - "Task 1 was already fully implemented by Wave 1 executor (09-01 deviation). All three required changes were present and tested green — no duplication needed."
  - "Pre-existing test failures in ColumnPicker.test.tsx and useColumnPrefs.test.ts are out of scope stubs for Wave 3 (09-03/09-04); all 83 existing tests pass."
  - "test_config_push::test_failed_triggers_rollback failure is pre-existing and unrelated to this plan."
metrics:
  duration: "~15 minutes"
  completed: "2026-03-30T15:45:00Z"
  tasks_completed: 2
  files_modified: 2
requirements: [COLS-02, COLS-03]
---

# Phase 9 Plan 02: API Layer + Frontend Types Summary

**One-liner:** Extended collectors list API with resource_attributes per collector, added attrs/keys endpoint with correct route ordering, and wired Zod validation types plus fetchResourceAttrKeys client function.

## Tasks Completed

| # | Name | Status | Commit |
|---|------|--------|--------|
| 1 | API endpoints (list + attrs/keys) | Skipped — already done by 09-01 deviation | pre-existing |
| 2 | Frontend Zod types and API client function | Complete | 9ae8284 |

## What Was Built

### Task 1 (pre-existing — verified, not re-implemented)

`opamp_server/api/collectors.py` already contained all required changes from the Wave 1 executor deviation:

- `resource_attributes: dict[str, str] = {}` field on `CollectorSummary` Pydantic model
- `@router.get("/collectors/attrs/keys")` endpoint (`list_attr_keys`) placed before the `{collector_id}` parametric route — correct ordering per RESEARCH.md Pitfall 1
- `resource_attrs_map = await persistence.get_resource_attrs_for_agents(uid_hexes)` called in `list_collectors`, with result mapped into each collector dict

All 5 targeted backend tests passed green on first run.

### Task 2 (implemented in this plan)

**ui/src/api/types.ts:**
- `CollectorSummarySchema` extended with `resource_attributes: z.record(z.string(), z.string()).default({})` — backward-compatible via `.default({})`
- `ResourceAttrKeysSchema` added as `z.object({ keys: z.array(z.string()) })`
- `ResourceAttrKeys` TypeScript type exported via `z.infer<typeof ResourceAttrKeysSchema>`

**ui/src/api/client.ts:**
- `ResourceAttrKeysSchema` imported from `./types`
- `fetchResourceAttrKeys(): Promise<string[]>` function added — follows existing `fetchStats()` pattern: request, Zod parse, return typed value

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_collectors_api.py -k "resource_attributes or attrs_keys"` | 5/5 PASSED |
| `pytest tests/test_collectors_api.py -v` | 17/17 PASSED |
| `npx tsc --noEmit` | Clean (no errors) |
| `npx vitest run` | 83/83 tests passed (2 pre-existing stub failures for Wave 3 components) |

## Deviations from Plan

### Task 1 Skipped — Already Implemented

**Found during:** Pre-execution check of collectors.py as instructed in prompt

**Issue:** Wave 1 executor (09-01) implemented all three API changes as a deviation during their plan. The collectors.py file already had `resource_attributes` in the model, `attrs/keys` endpoint in correct position, and `get_resource_attrs_for_agents` call in `list_collectors`.

**Action:** Ran verification tests immediately. All 5 targeted tests passed. Proceeded directly to Task 2.

**Impact:** None — plan goal achieved. No re-implementation needed.

## Known Stubs

None. All data flows are wired end-to-end:
- Backend persistence functions exist (09-01)
- API endpoints return live data (09-01 deviation)
- Zod schemas validate the response shape (this plan)
- Client function fetches and validates (this plan)

Wave 3 (09-03/09-04) will consume `fetchResourceAttrKeys` and `CollectorSummary.resource_attributes` to build the column picker UI.

## Self-Check: PASSED
