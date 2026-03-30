---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Operator UX
status: executing
last_updated: "2026-03-30T12:54:33.715Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 5
  completed_plans: 4
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** Operators can see which collectors are connected, understand their health, and safely push config changes — all from a browser.
**Current focus:** Phase 07 — status-landing-page

## Current Position

```
Milestone: v1.1 Operator UX
Phase: 07 (status-landing-page) — EXECUTING
Plan: 2 of 2
Status: Ready to execute

[██████████] Phase 6: Frontend Quick Wins (3/3 plans complete) 100%
[          ] Phase 7: Status Landing Page
[          ] Phase 8: Stale Collector TTL Purge
[          ] Phase 9: Dynamic Resource Attribute Columns

Progress: 1/4 phases complete (all Phase 6 plans delivered)
```

Last session: 2026-03-30T12:54:33.711Z

## Performance Metrics

- v1.0: 5 phases, 20 plans, 34 tasks, 91 files, ~13,100 LOC
- v1.1: 4 phases planned, 23 requirements to deliver

## Accumulated Context

### v1.0 Shipped (2026-03-30)

- Full OpAMP server + React management UI + Docker Compose stack
- Protocol, config push/rollback, REST API, React UI, Compose integration
- All 38 v1.0 requirements delivered

### v1.1 Roadmap Decisions

- Phase 6 (Frontend Quick Wins) is zero-backend — all UI-only changes; safe to parallelize internally
- Phase 7 (Status Landing Page) requires new `GET /api/v1/stats` endpoint — full-stack but small scope
- Phase 8 (TTL Purge) is backend-only; must be implemented as a unit — all four failure modes interact
- Phase 9 (Dynamic Columns) depends on Phase 8 because purge must include `agent_resource_attrs` table once it exists

### Critical Implementation Notes (from research)

- Phase 8: SQLite FK cascade is OFF by default — use explicit ordered child-table deletes (`health_snapshots`, `effective_configs`, `config_pushes`, then `agents`). Phase 9 adds `agent_resource_attrs` to this delete order.
- Phase 8: `AgentRegistry` has no `remove()` method — must add before purge can evict in-memory state
- Phase 9: `handler.py` line 99 unconditionally sets `description=None`, discarding all resource attributes — this is the root cause fix that unlocks the entire feature
- Phase 9: `GET /api/v1/collectors/attrs/keys` must be registered BEFORE `GET /api/v1/collectors/{id}` in FastAPI route order
- Phase 6: Config editor `useEffect` must guard with a `seededRef = useRef(false)` — fire only on first data arrival to avoid overwriting in-progress edits
- Phase 6: Verify config pre-populate may already be working via `handleEditStart()` before writing new code

### Plan 06-01 Decisions (2026-03-30)

- CapabilityChip uses role=listitem per chip and role=list container for semantic accessibility
- Hex fallback format is 0x{HEX} with no zero-padding, matching OpAMP spec notation
- "None" chip uses hex variant (not named) for visual distinction from real capabilities
- Bitmask decode: iterate CAPABILITY_BITS lookup table, mask off matched bits, loop remaining bits for hex labels

### Plan 06-02 Decisions (2026-03-30)

- seededRef guards useEffect to fire only once on first non-empty effective_config arrival; prevents background poll from overwriting in-progress edits
- handleEditStart fallback retained: refreshes editedYaml to latest effective_config on each re-entry into edit mode
- ConfigEditor.tsx not modified — parent-level isEditMode ternary is the edit protection guard

### Todos

- [x] Run Phase 6 first — verify config pre-populate (UI-01) before writing code; may be a no-op

### Blockers

None
