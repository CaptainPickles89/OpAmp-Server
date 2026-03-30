---
phase: 09-dynamic-resource-attribute-columns
plan: 01
subsystem: backend
tags: [sqlite, persistence, opamp, resource-attributes, handler]
dependency_graph:
  requires: ["09-00"]
  provides: ["agent_resource_attrs table", "upsert_resource_attrs", "get_resource_attrs_for_agents", "get_all_resource_attr_keys", "handler extraction"]
  affects: ["opamp_server/persistence.py", "opamp_server/handler.py", "opamp_server/api/collectors.py", "opamp_server/main.py"]
tech_stack:
  added: []
  patterns: ["fire-and-forget asyncio.ensure_future", "SQLite ON CONFLICT upsert", "composite primary key", "FK-ordered DELETE chain"]
key_files:
  created: []
  modified:
    - opamp_server/persistence.py
    - opamp_server/handler.py
    - opamp_server/api/collectors.py
    - opamp_server/main.py
    - tests/test_handler.py
decisions:
  - "Store resource attributes in dedicated agent_resource_attrs table with (instance_uid, key) composite PK, not in description_json column"
  - "Use ON CONFLICT upsert so repeated agent pings update values rather than duplicating rows"
  - "Fire-and-forget upsert_resource_attrs using asyncio.ensure_future consistent with existing health/config persistence pattern"
  - "attrs/keys endpoint placed before {collector_id} wildcard route to prevent hex-parse of 'attrs'"
  - "app.state.db_path reads from _cfg_module.settings (module attribute) to survive per-test config reloads"
metrics:
  duration: "~45 minutes"
  completed: "2026-03-30T15:38:26Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 5
requirements: [COLS-01]
---

# Phase 09 Plan 01: Schema + Persistence + Handler Extraction Summary

SQLite schema for agent_resource_attrs table, three persistence functions (upsert, batch-fetch, keys), handler extraction of non_identifying_attributes from AgentDescription, and collectors API extended with resource_attributes per collector and a distinct-keys endpoint.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Schema migration and persistence functions | bb77feb | opamp_server/persistence.py |
| 2 | Handler extraction + API + test fixes | 8fe79a5 | opamp_server/handler.py, opamp_server/api/collectors.py, opamp_server/main.py, tests/test_handler.py |

## Decisions Made

1. Resource attributes stored in a dedicated `agent_resource_attrs(instance_uid, key, value, updated_at)` table with composite PK — not merged into `description_json`. Enables efficient `SELECT DISTINCT key` queries without JSON parsing.

2. `ON CONFLICT(instance_uid, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at` — same upsert pattern used in the agents table, ensures idempotent repeated pings.

3. `DELETE FROM agent_resource_attrs` inserted between `config_pushes` delete and `agents` delete in `purge_agent()` to satisfy the FK dependency ordering documented in the existing purge chain comment.

4. `GET /api/v1/collectors/attrs/keys` endpoint registered BEFORE the `{collector_id}` wildcard route to prevent FastAPI from trying to hex-parse `"attrs"` as a collector UID.

5. `app.state.db_path` set via `_cfg_module.settings` (module attribute reference) instead of the import-time `settings` binding, so post-reload config changes in tests are reflected correctly.

## Deviations from Plan

### Auto-fixed Issues (Rule 1 - Bugs in Wave 0 Test Stubs)

**1. [Rule 1 - Bug] Fixed bare hex string as SQL params in test_handler.py**
- **Found during:** Task 2 verification
- **Issue:** Wave 0 stubs passed `(b"\xaa" * 16).hex()` (a 32-char string) as SQL binding params instead of `((b"\xaa" * 16).hex(),)` (a single-element tuple). aiosqlite iterated the string, producing 32 bindings for one `?` placeholder.
- **Fix:** Wrapped hex strings in tuples in both test methods.
- **Files modified:** tests/test_handler.py
- **Commit:** 8fe79a5

**2. [Rule 1 - Bug] Fixed missing asyncio.wait drain for fire-and-forget timing**
- **Found during:** Task 2 verification
- **Issue:** Test read the DB immediately after the HTTP response without waiting for the `asyncio.ensure_future(upsert_resource_attrs(...))` task to complete. aiosqlite writes via a thread pool; `asyncio.sleep(N)` is not reliable because the preceding test's zombie threads compete for the event loop.
- **Fix:** Added `asyncio.wait(pending, timeout=1.0)` targeted at tasks whose coroutine name contains `upsert_resource_attrs`. This holds the event loop open until the specific task finishes.
- **Files modified:** tests/test_handler.py
- **Commit:** 8fe79a5

**3. [Rule 1 - Bug] Fixed stale settings reference in app.state.db_path**
- **Found during:** Task 2 verification (root cause analysis of timing failure)
- **Issue:** `main.py` used `from opamp_server.config import settings` which binds at import time. After `reload(cfg_module)` in each test fixture, the module-level `settings` object is replaced, but `main.py`'s local `settings` reference stays pointing to the old object. `app.state.db_path` was therefore set to the PREVIOUS test's DB path, so the test queried the wrong file.
- **Fix:** Added `import opamp_server.config as _cfg_module` and changed `app.state.db_path = _cfg_module.settings.db_path` to read via the module reference, which always reflects the current post-reload settings.
- **Files modified:** opamp_server/main.py
- **Commit:** 8fe79a5

### Auto-added Missing Functionality (Rule 2)

**4. [Rule 2 - Missing functionality] Added resource_attributes to collectors list API**
- **Found during:** Full suite run after Task 2
- **Issue:** Wave 0 stub `test_list_collectors_includes_resource_attributes` expected `resource_attributes` dict in the `GET /api/v1/collectors` response, but `CollectorSummary` and `list_collectors()` didn't include it.
- **Fix:** Added `resource_attributes: dict[str, str] = {}` to `CollectorSummary`, batch-fetched via `get_resource_attrs_for_agents()` alongside the existing health batch-fetch, and included in each result dict.
- **Files modified:** opamp_server/api/collectors.py
- **Commit:** 8fe79a5

**5. [Rule 2 - Missing functionality] Added GET /api/v1/collectors/attrs/keys endpoint**
- **Found during:** Full suite run after Task 2
- **Issue:** Wave 0 stubs `test_attrs_keys_returns_distinct_keys`, `test_attrs_keys_empty_when_no_attrs`, and `test_attrs_keys_route_not_consumed_by_collector_id` expected this endpoint to exist.
- **Fix:** Added `GET /collectors/attrs/keys` endpoint calling `persistence.get_all_resource_attr_keys()`, registered before the `{collector_id}` wildcard route.
- **Files modified:** opamp_server/api/collectors.py
- **Commit:** 8fe79a5

## Verification Results

All 98 tests pass:

```
pytest tests/test_persistence.py::TestResourceAttrs -x -v   → 5 passed
pytest tests/test_handler.py::TestResourceAttrExtraction -x -v  → 2 passed
pytest tests/ -x                                             → 98 passed
```

The previously pre-existing failure `test_failed_triggers_rollback` also resolved as a side effect of the main.py settings fix.

## Known Stubs

None — all functions are fully implemented with real SQLite I/O.

## Self-Check: PASSED

Files exist:
- opamp_server/persistence.py: FOUND
- opamp_server/handler.py: FOUND
- opamp_server/api/collectors.py: FOUND
- opamp_server/main.py: FOUND

Commits exist:
- bb77feb: FOUND (feat(09-01): add agent_resource_attrs schema)
- 8fe79a5: FOUND (feat(09-01): add handler resource attr extraction)
