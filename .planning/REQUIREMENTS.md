# Requirements: OpAMP Server v1.1

**Defined:** 2026-03-30
**Core Value:** Operators can see which collectors are connected, understand their health, and safely push config changes — all from a browser.

## v1.1 Requirements

### UI — Frontend Quick Wins

- [x] **UI-01**: User sees the config editor pre-populated with the collector's current `effective_config` when opening the detail page
- [x] **UI-02**: Config editor does not overwrite in-progress edits when background polls refresh `effective_config`
- [x] **UI-03**: Collector list table shows capability chips (e.g. "Remote Config", "Health") instead of a raw bitmask integer
- [x] **UI-04**: Collector detail page shows the same capability chips as the list view
- [x] **UI-05**: Unknown capability bits render as a hex fallback chip (e.g. "0x8000") rather than being silently dropped
- [x] **UI-06**: Getting Started example config includes `host.name`, `service.instance.id`, `deployment.environment`, `host.ip` in the resource attributes block
- [x] **UI-07**: `compose.yaml` collector service uses a pinned image tag (`otel/opentelemetry-collector-contrib:0.119.0`) not `latest`

### STATUS — Landing Page

- [x] **STATUS-01**: A "Status" page exists at the `/` route with an OTel logo hero section and gradient background
- [x] **STATUS-02**: Status page shows a one-to-two sentence description of what the UI does
- [x] **STATUS-03**: Status page shows a live "X of Y agents healthy" count that updates every 5 seconds
- [x] **STATUS-04**: "Status" nav item appears in the app navigation

### TTL — Stale Collector Purge

- [ ] **TTL-01**: Server auto-purges collectors from DB and in-memory registry when `last_seen` exceeds the TTL threshold
- [ ] **TTL-02**: TTL is configurable via `OPAMP_COLLECTOR_TTL_HOURS` env var, default 24
- [ ] **TTL-03**: Purge sweep runs as a background task launched at startup, recurring on a schedule
- [ ] **TTL-04**: A structured log entry is written for each purged collector
- [ ] **TTL-05**: Collectors with an active config push (`PUSH_PENDING` or `APPLYING`) are not purged

### COLS — Dynamic Resource Attribute Columns

- [ ] **COLS-01**: Server parses `agent_description` from incoming OpAMP messages and stores resource attribute key/value pairs per collector
- [ ] **COLS-02**: `GET /api/v1/collectors` returns a `resource_attributes` dict per collector (additive — does not break existing clients)
- [ ] **COLS-03**: An endpoint returns the union of all distinct resource attribute keys seen across all connected collectors
- [ ] **COLS-04**: Collector list table shows `host.name` as a visible column by default
- [ ] **COLS-05**: A column picker lets the operator toggle any discovered resource attribute key on/off as a table column
- [ ] **COLS-06**: Column picker selection persists across page reloads via `localStorage`
- [ ] **COLS-07**: When a new collector reports a new resource attribute key, that key appears in the column picker on the next poll cycle

## Future Requirements

### Operator Enhancements

- **OPS-01**: "Expiring soon" indicator on collectors approaching TTL threshold
- **OPS-02**: Filter collector list by resource attribute value
- **OPS-03**: Column reorder via drag-and-drop
- **OPS-04**: Config diff view comparing pushed config vs current effective config

## Out of Scope

| Feature | Reason |
|---------|--------|
| Manual purge trigger REST endpoint | TTL purge is automated hygiene; no operator action needed |
| Per-agent TTL override | One global TTL is sufficient; per-agent TTL adds UI and data model complexity |
| Server-side column preference storage | No auth identity exists; localStorage is the correct approach |
| Filter by capability chip | Separate feature; not requested for this milestone |
| Animated hero / OTel logo animation | Distraction in an operator context |
| Config diff view on editor | Defer to a later milestone |
| WebSocket OpAMP transport | HTTP polling sufficient; spec-defined but adds connection management complexity |
| Authentication / authorization | Deferred; v1.x is an internal/dev tool |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 6 | Complete |
| UI-02 | Phase 6 | Complete |
| UI-03 | Phase 6 | Complete |
| UI-04 | Phase 6 | Complete |
| UI-05 | Phase 6 | Complete |
| UI-06 | Phase 6 | Complete |
| UI-07 | Phase 6 | Complete |
| STATUS-01 | Phase 7 | Complete |
| STATUS-02 | Phase 7 | Complete |
| STATUS-03 | Phase 7 | Complete |
| STATUS-04 | Phase 7 | Complete |
| TTL-01 | Phase 8 | Pending |
| TTL-02 | Phase 8 | Pending |
| TTL-03 | Phase 8 | Pending |
| TTL-04 | Phase 8 | Pending |
| TTL-05 | Phase 8 | Pending |
| COLS-01 | Phase 9 | Pending |
| COLS-02 | Phase 9 | Pending |
| COLS-03 | Phase 9 | Pending |
| COLS-04 | Phase 9 | Pending |
| COLS-05 | Phase 9 | Pending |
| COLS-06 | Phase 9 | Pending |
| COLS-07 | Phase 9 | Pending |

**Coverage:**
- v1.1 requirements: 23 total
- Mapped to phases: 23 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 — traceability mapped after roadmap creation*
