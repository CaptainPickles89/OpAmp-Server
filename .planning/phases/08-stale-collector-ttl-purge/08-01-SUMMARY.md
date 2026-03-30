---
phase: 08-stale-collector-ttl-purge
plan: 01
subsystem: backend
tags: [purge, ttl, registry, persistence, config]
dependency_graph:
  requires: []
  provides: [purge-sweep-logic, registry-remove, persistence-purge-agent, ttl-config]
  affects: [opamp_server/config.py, opamp_server/registry.py, opamp_server/persistence.py, opamp_server/purger.py]
tech_stack:
  added: [structlog (purge logging)]
  patterns: [_settings() accessor for test-safe config reload, sleep-first purge loop, frozenset push-state guard]
key_files:
  created:
    - opamp_server/purger.py
    - tests/test_purge.py
  modified:
    - opamp_server/config.py
    - opamp_server/registry.py
    - opamp_server/persistence.py
decisions:
  - Use _settings() accessor in purger.py (same pattern as persistence.py) so monkeypatch+reload in tests works correctly
  - Sleep-first pattern in start_purge_loop prevents purging agents on server restart
  - ACTIVE_PUSH_STATES as frozenset for O(1) membership checks
  - Ordered child-table deletes (health_snapshots, effective_configs, config_pushes, agents) because SQLite FK cascade is OFF
metrics:
  duration: 23m 32s
  completed: "2026-03-30"
  tasks: 2
  files: 5
---

# Phase 08 Plan 01: Core Purge Sweep Logic Summary

TTL-based stale collector purge: config fields, registry.remove, ordered persistence.purge_agent, and run_purge_sweep with push-state guard and structured logging.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write failing tests for all purge behaviors (RED) | 517a9c8 | tests/test_purge.py (+272 lines) |
| 2 | Implement config, registry.remove, persistence.purge_agent, and purger.run_purge_sweep (GREEN) | 17b5024 | config.py, registry.py, persistence.py, purger.py (+98 lines) |

## What Was Built

**opamp_server/config.py** — Added two new Settings fields:
- `collector_ttl_hours: int = 24` — overridable via `OPAMP_COLLECTOR_TTL_HOURS`
- `purge_interval_hours: int = 1` — overridable via `OPAMP_PURGE_INTERVAL_HOURS`

**opamp_server/registry.py** — Added `async def remove(uid: bytes) -> None` to `AgentRegistry`. Uses `self._lock` via `async with`, pops from `self._agents` with no-op on missing key.

**opamp_server/persistence.py** — Added `async def purge_agent(instance_uid: bytes) -> None`. Deletes in FK-safe order: `health_snapshots` → `effective_configs` → `config_pushes` → `agents`, all in a single connection + commit.

**opamp_server/purger.py** — New module with:
- `ACTIVE_PUSH_STATES = frozenset({"PUSH_PENDING", "APPLYING"})` — agents in active push are never purged
- `run_purge_sweep(registry)` — computes cutoff in nanoseconds, filters stale agents, calls `persistence.purge_agent` then `registry.remove`, logs `collector_purged` event, returns purged count
- `start_purge_loop(registry)` — background loop that sleeps first then calls sweep on interval

## Test Coverage

12 tests in `tests/test_purge.py`:
- `TestSettings`: default TTL (24h), default interval (1h), custom TTL via env
- `TestRegistryRemove`: remove deletes agent, remove on unknown is no-op
- `TestPurgeAgent`: purge_agent clears all child tables and agents row
- `TestRunPurgeSweep`: stale agent purged, fresh agent skipped, PUSH_PENDING skipped, APPLYING skipped, structured log entry with uid hex, 48h TTL config respected

All 12 tests pass. Full suite (83 tests) passes except one pre-existing `test_failed_triggers_rollback` failure that exists when `test_collectors_api.py` runs before it — confirmed pre-existing via baseline run without these changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _settings() accessor pattern in purger.py**
- **Found during:** Task 2, GREEN phase
- **Issue:** `from opamp_server.config import settings` binds the settings object at import time. When tests call `monkeypatch.setenv` + `reload(cfg_module)`, a new settings object is created but purger.py retained the old one, causing `test_ttl_config_respected` to fail (sweeper used old 24h TTL instead of patched 48h).
- **Fix:** Changed to `import opamp_server.config as _config` + `_settings()` accessor function, matching the pattern used in `persistence.py`.
- **Files modified:** opamp_server/purger.py
- **Commit:** 17b5024

## Known Stubs

None — all plan truths are implemented and tested.

## Self-Check: PASSED
