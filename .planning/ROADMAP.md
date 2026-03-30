# Roadmap: OpAmp Server

## Milestones

- ✅ **v1.0 MVP** — Phases 1-5 (shipped 2026-03-30) — [archive](.planning/milestones/v1.0-ROADMAP.md)
- **v1.1 Operator UX** — Phases 6-9 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-5) — SHIPPED 2026-03-30</summary>

- [x] Phase 1: Protocol Foundation (5/5 plans) — completed 2026-03-27
- [x] Phase 2: Config Push and Rollback (5/5 plans) — completed 2026-03-27
- [x] Phase 3: REST API (3/3 plans) — completed 2026-03-27
- [x] Phase 4: React Management UI (5/5 plans) — completed 2026-03-27
- [x] Phase 5: Docker Compose Integration (2/2 plans) — completed 2026-03-27

</details>

### v1.1 Operator UX

- [x] **Phase 6: Frontend Quick Wins** — Config pre-populate, capability chips, enriched example config (completed 2026-03-30)
- [x] **Phase 7: Status Landing Page** — New route with live agent health counts and OTel hero (completed 2026-03-30)
- [ ] **Phase 8: Stale Collector TTL Purge** — Background auto-purge with push-state guard
- [x] **Phase 9: Dynamic Resource Attribute Columns** — Column picker with dynamic attribute discovery (completed 2026-03-30)

## Phase Details

### Phase 6: Frontend Quick Wins
**Goal**: Operators see human-readable collector metadata and a pre-seeded config editor without any backend changes
**Depends on**: Phase 5 (v1.0 complete stack)
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07
**Success Criteria** (what must be TRUE):
  1. Operator opens a collector detail page and the CodeMirror editor is already populated with the collector's current effective config — no manual copy-paste required
  2. Operator edits the config YAML and a background poll completes without wiping their in-progress changes
  3. Collector list and detail pages show named chips ("Remote Config", "Health") instead of a raw bitmask integer; an unrecognised bit renders as a hex fallback chip (e.g. "0x8000") rather than disappearing
  4. Getting Started page example config block includes `host.name`, `service.instance.id`, `deployment.environment`, and `host.ip` in the resource attributes section
  5. `compose.yaml` collector service references the pinned image tag `otel/opentelemetry-collector-contrib:0.119.0`, not `latest`
**Plans**: 3 plans
Plans:
- [x] 06-01-PLAN.md — Capability chips: new CapabilityChip/CapabilityChipList components + integration into list and detail pages
- [x] 06-02-PLAN.md — Config editor pre-seed: seededRef guard for first-load pre-population of editedYaml
- [x] 06-03-PLAN.md — String changes: enriched example config + pinned compose.yaml image tag
**UI hint**: yes

### Phase 7: Status Landing Page
**Goal**: Operators land on a purpose-built status page that immediately shows fleet health at a glance
**Depends on**: Phase 6
**Requirements**: STATUS-01, STATUS-02, STATUS-03, STATUS-04
**Success Criteria** (what must be TRUE):
  1. Navigating to `/` displays a page with an OTel logo hero section and a gradient background
  2. The status page shows a one-to-two sentence description of what the management UI does
  3. A live "X of Y agents healthy" count is visible on the status page and refreshes every 5 seconds without a full page reload
  4. A "Status" navigation item appears in the app nav bar and routes to this page
**Plans**: 2 plans
Plans:
- [x] 07-01-PLAN.md — Backend stats endpoint + frontend data layer (Zod schema, API client, useStats hook, MSW mock)
- [x] 07-02-PLAN.md — StatusPage UI (hero, stat card, routing, nav link) + frontend tests
**UI hint**: yes

### Phase 8: Stale Collector TTL Purge
**Goal**: Stale ghost collectors are automatically removed from the server so the operator's view reflects only live agents
**Depends on**: Phase 6
**Requirements**: TTL-01, TTL-02, TTL-03, TTL-04, TTL-05
**Success Criteria** (what must be TRUE):
  1. A collector that has not sent a message for longer than the configured TTL no longer appears in the collector list after the next purge sweep
  2. Setting `OPAMP_COLLECTOR_TTL_HOURS=48` changes the expiry window; omitting the variable defaults to 24 hours
  3. The purge sweep runs automatically in the background on server startup and continues on a recurring schedule without operator intervention
  4. Each purged collector produces a structured log entry containing its instance UID
  5. A collector with an active config push (`PUSH_PENDING` or `APPLYING` state) is not purged during the sweep, even if its `last_seen` timestamp has exceeded the TTL
**Plans**: 2 plans
Plans:
- [x] 08-01-PLAN.md — Core purge logic: settings, registry.remove, persistence.purge_agent, purger.run_purge_sweep + tests
- [x] 08-02-PLAN.md — Lifecycle wiring: background task launch on startup, cancellation on shutdown
**UI hint**: no

### Phase 9: Dynamic Resource Attribute Columns
**Goal**: Operators can see `host.name` and any other resource attributes reported by their collectors as togglable table columns that persist across sessions
**Depends on**: Phase 8
**Requirements**: COLS-01, COLS-02, COLS-03, COLS-04, COLS-05, COLS-06, COLS-07
**Success Criteria** (what must be TRUE):
  1. The collector list table shows a `host.name` column by default, populated from the resource attributes the collector reports in its `agent_description`
  2. A column picker control lets the operator toggle any discovered resource attribute key on or off as a table column; toggling is reflected immediately without a page reload
  3. Column picker selections survive a browser refresh — reopening the page restores the same column configuration the operator last set
  4. Connecting a new collector that reports a previously unseen resource attribute key (e.g. `deployment.environment`) causes that key to appear in the column picker on the next poll cycle without any server restart
  5. `GET /api/v1/collectors` returns a `resource_attributes` dict per collector alongside existing fields; existing API consumers are not broken
**Plans**: 5 plans
Plans:
- [x] 09-00-PLAN.md — Wave 0: failing test stubs (backend + frontend) for all COLS requirements
- [x] 09-01-PLAN.md — Wave 1: DB migration (agent_resource_attrs table), persistence functions, handler extraction
- [x] 09-02-PLAN.md — Wave 2: API endpoints (attrs/keys + extend list_collectors), Zod types, API client
- [x] 09-03-PLAN.md — Wave 3: useResourceAttrKeys hook, useColumnPrefs hook, ColumnPicker component
- [x] 09-04-PLAN.md — Wave 4: CollectorListPage integration (dynamic grid, resource attr cells, ColumnPicker wiring)
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Protocol Foundation | v1.0 | 5/5 | Complete | 2026-03-27 |
| 2. Config Push and Rollback | v1.0 | 5/5 | Complete | 2026-03-27 |
| 3. REST API | v1.0 | 3/3 | Complete | 2026-03-27 |
| 4. React Management UI | v1.0 | 5/5 | Complete | 2026-03-27 |
| 5. Docker Compose Integration | v1.0 | 2/2 | Complete | 2026-03-27 |
| 6. Frontend Quick Wins | v1.1 | 3/3 | Complete   | 2026-03-30 |
| 7. Status Landing Page | v1.1 | 2/2 | Complete   | 2026-03-30 |
| 8. Stale Collector TTL Purge | v1.1 | 1/2 | In Progress|  |
| 9. Dynamic Resource Attribute Columns | v1.1 | 5/5 | Complete   | 2026-03-30 |
