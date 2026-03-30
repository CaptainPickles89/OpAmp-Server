---
phase: 09-dynamic-resource-attribute-columns
plan: "00"
subsystem: testing
tags: [tdd, red-phase, resource-attributes, persistence, frontend]
dependency_graph:
  requires: []
  provides:
    - "Failing test stubs for all Phase 9 features (RED)"
    - "MSW mock handlers with resource_attributes and attrs/keys"
  affects:
    - tests/test_persistence.py
    - tests/test_collectors_api.py
    - tests/test_handler.py
    - ui/src/hooks/__tests__/useColumnPrefs.test.ts
    - ui/src/components/__tests__/ColumnPicker.test.tsx
    - ui/src/mocks/handlers.ts
tech_stack:
  added: []
  patterns:
    - "pytest async class-based test stubs"
    - "Vitest renderHook for hook testing"
    - "MSW route ordering (specific before dynamic)"
key_files:
  created:
    - ui/src/hooks/__tests__/useColumnPrefs.test.ts
    - ui/src/components/__tests__/ColumnPicker.test.tsx
  modified:
    - tests/test_persistence.py
    - tests/test_collectors_api.py
    - tests/test_handler.py
    - ui/src/mocks/handlers.ts
decisions:
  - "Used anyvalue_pb2.KeyValue (not opamp_pb2) for handler test proto construction - confirmed via runtime inspection"
  - "handler test uses app.state.db_path to access DB directly - will require production implementation to set this attribute"
  - "MSW attrs/keys handler inserted BEFORE :id wildcard route to prevent route conflict"
metrics:
  duration: "~15 minutes"
  completed: "2026-03-30T14:55:30Z"
  tasks_completed: 2
  files_modified: 6
---

# Phase 9 Plan 00: TDD Wave 0 — RED Phase Stubs Summary

One-liner: 12 backend test stubs and 10 frontend test stubs written for dynamic resource attribute columns, all failing RED with AttributeError or module-not-found.

## What Was Built

### Task 1: Backend failing test stubs

**tests/test_persistence.py** — `TestResourceAttrs` class (5 stubs):
- `test_upsert_resource_attrs_inserts_rows` (COLS-01)
- `test_upsert_resource_attrs_updates_existing_key` (COLS-01)
- `test_get_all_resource_attr_keys_returns_distinct_keys` (COLS-03)
- `test_get_all_resource_attr_keys_empty_db` (COLS-03)
- `test_get_resource_attrs_for_agents_batch` (COLS-02)

**tests/test_collectors_api.py** — 5 standalone test functions:
- `test_list_collectors_includes_resource_attributes` (COLS-02)
- `test_list_collectors_resource_attributes_empty_when_none` (COLS-02)
- `test_attrs_keys_returns_distinct_keys` (COLS-03)
- `test_attrs_keys_empty_when_no_attrs` (COLS-03)
- `test_attrs_keys_route_not_consumed_by_collector_id` (COLS-03)

**tests/test_handler.py** — `TestResourceAttrExtraction` class (2 stubs):
- `test_handler_extracts_resource_attrs_from_agent_description` (COLS-01)
- `test_handler_ignores_empty_agent_description` (COLS-01)

### Task 2: Frontend failing test stubs + MSW mock updates

**ui/src/mocks/handlers.ts** — updated:
- Added `resource_attributes` field to both mockCollectors entries
- Added `/api/v1/collectors/attrs/keys` GET handler BEFORE the `:id` wildcard

**ui/src/hooks/__tests__/useColumnPrefs.test.ts** — new file (5 stubs):
- seeds with `["host.name"]` when localStorage empty
- toggleKey adds/removes keys
- persists to localStorage on toggle
- reads persisted state on mount

**ui/src/components/__tests__/ColumnPicker.test.tsx** — new file (5 stubs):
- renders trigger button with "Columns" label
- opens popover showing attribute keys
- checked state reflects enabledKeys
- calls onToggle on checkbox change
- closes on outside click

## Verification Results (RED)

All tests fail as expected:

| Test | Failure type |
|------|-------------|
| `TestResourceAttrs` (all 5) | `AttributeError: module 'opamp_server.persistence' has no attribute 'upsert_resource_attrs'` |
| `test_list_collectors_includes_resource_attributes` | `AttributeError: module 'opamp_server.persistence' has no attribute 'upsert_resource_attrs'` |
| `test_attrs_keys_*` (3 tests) | `AttributeError` (endpoint not implemented) |
| `TestResourceAttrExtraction` (2) | `AttributeError: 'State' object has no attribute 'db_path'` |
| `useColumnPrefs.test.ts` (5) | `Failed to resolve import "@/hooks/useColumnPrefs"` |
| `ColumnPicker.test.tsx` (5) | `Failed to resolve import "@/components/ColumnPicker"` |

## Deviations from Plan

None - plan executed exactly as written.

The proto import note in the plan was accurate: `anyvalue_pb2.KeyValue` is the correct type (confirmed via runtime inspection), but the `opamp_pb2` import is used for `AgentToServer` which contains the `agent_description` field — both imports work together.

## Commits

- `5269998` — `test(09-00): add RED stubs for resource attribute backend tests`
- `7094296` — `test(09-00): add RED stubs for frontend column prefs and picker tests`

## Self-Check: PASSED

- `tests/test_persistence.py` — FOUND, contains `TestResourceAttrs`
- `tests/test_collectors_api.py` — FOUND, contains `test_attrs_keys_returns_distinct_keys`
- `tests/test_handler.py` — FOUND, contains `TestResourceAttrExtraction`
- `ui/src/hooks/__tests__/useColumnPrefs.test.ts` — FOUND
- `ui/src/components/__tests__/ColumnPicker.test.tsx` — FOUND
- `ui/src/mocks/handlers.ts` — FOUND, contains `collectors/attrs/keys`
- Commits `5269998` and `7094296` — VERIFIED
