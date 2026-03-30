---
phase: 07-status-landing-page
plan: 02
subsystem: ui
tags: [react, tanstack-query, msw, vitest, tailwind, opamp]

# Dependency graph
requires:
  - phase: 07-01
    provides: useStats hook, Stats type, MSW stats handler, GET /api/v1/stats backend endpoint

provides:
  - StatusPage at route '/' with OTel hero section and live agent health stat card
  - AgentHealthStat component showing "X of Y agents healthy" with aria-live
  - Status nav link (first in nav bar, exact-match active detection)
  - Tests: StatusPage (5 tests), AppLayout (4 tests)

affects: [phase-08, phase-09, any phase touching AppLayout routing or nav]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Duplicate private SVG components inline rather than importing (OtelTelescopeIcon)
    - Use renderWithProviders helper for component tests needing QueryClient + MemoryRouter
    - Exact pathname match for nav active state on root routes

key-files:
  created:
    - ui/src/components/AgentHealthStat.tsx
    - ui/src/pages/StatusPage.tsx
    - ui/src/pages/__tests__/StatusPage.test.tsx
    - ui/src/components/__tests__/AppLayout.test.tsx
  modified:
    - ui/src/App.tsx
    - ui/src/components/AppLayout.tsx

key-decisions:
  - "OtelTelescopeIcon SVG duplicated inline in StatusPage — it is a private function in AppLayout and cannot be imported"
  - "Active nav detection changed from pathname.startsWith(to) to pathname === to — safe because no nav links have sub-routes needing parent highlight"
  - "Brand logo link in AppLayout updated from /collectors to / for consistency with new home page"

patterns-established:
  - "Exact pathname match (pathname === to) for nav active state detection in AppLayout"
  - "StatusPage follows CollectorListPage skeleton/error/empty state patterns for consistency"

requirements-completed: [STATUS-01, STATUS-02, STATUS-03, STATUS-04]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 07 Plan 02: Status Landing Page UI Summary

**StatusPage with OTel hero gradient, live AgentHealthStat card, and Status nav link wired to route '/' replacing the old Navigate redirect**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T12:56:57Z
- **Completed:** 2026-03-30T13:00:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- StatusPage renders at `/` with gradient hero (otel-blue-subtle to background), OTel icon, heading "OpAMP Server", and description text (STATUS-01, STATUS-02)
- AgentHealthStat displays live "X of Y agents healthy" count with aria-live polling every 5s (STATUS-03)
- Status nav link is the first entry in the pill nav, links to `/`, uses exact match for active state (STATUS-04)
- Navigate redirect from `/` to `/collectors` removed — `/` is a real page
- All 83 frontend tests pass (9 new tests added: 5 StatusPage + 4 AppLayout)

## Task Commits

Each task was committed atomically:

1. **Task 1: AgentHealthStat component and StatusPage with tests** - `e98c32e` (feat)
2. **Task 2: Routing and nav changes with AppLayout test** - `6b4f383` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `ui/src/components/AgentHealthStat.tsx` - Stat card showing "X of Y agents healthy" with aria-live polite
- `ui/src/pages/StatusPage.tsx` - Status landing page: hero section with gradient, OTel icon, heading, description, and live stat card
- `ui/src/pages/__tests__/StatusPage.test.tsx` - 5 tests covering STATUS-01, STATUS-02, STATUS-03
- `ui/src/components/__tests__/AppLayout.test.tsx` - 4 tests covering STATUS-04 nav link behaviour
- `ui/src/App.tsx` - Replaced Navigate redirect with StatusPage route at `/`; removed Navigate import
- `ui/src/components/AppLayout.tsx` - Added Status as first navLink, changed active detection to exact match, updated brand link to `/`

## Decisions Made

- OtelTelescopeIcon SVG is duplicated inline in StatusPage rather than imported — it is a private function in AppLayout and the plan explicitly requires this approach
- Active nav detection changed from `pathname.startsWith(to)` to `pathname === to` — no existing nav link has sub-routes that depend on parent highlighting, so exact match is safe and required for the `/` route to not permanently highlight Status on all pages
- Brand logo link updated from `/collectors` to `/` for consistency — without this change clicking the brand logo would bypass the Status nav highlight

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Updated brand link in AppLayout from /collectors to /**
- **Found during:** Task 2 (Routing and nav changes)
- **Issue:** Plan specified updating navLinks but the brand logo link still pointed to `/collectors`, which would send users to the Collectors page instead of the new home page
- **Fix:** Updated `<Link to="/collectors"` to `<Link to="/"` in the brand logo section of AppLayout
- **Files modified:** ui/src/components/AppLayout.tsx
- **Verification:** AppLayout tests pass; clicking brand link navigates to / in the test
- **Committed in:** 6b4f383 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Fix necessary for consistent UX — without it the brand logo would bypass the new home page. No scope creep.

## Issues Encountered

None — plan executed smoothly. All tests passed on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 07 complete: full-stack status landing page (backend stats endpoint in Plan 01, frontend UI in this plan)
- Phase 08 (Stale Collector TTL Purge) is backend-only and has no dependencies on this phase
- Phase 09 (Dynamic Resource Attribute Columns) depends on Phase 08 completing first

---
*Phase: 07-status-landing-page*
*Completed: 2026-03-30*
