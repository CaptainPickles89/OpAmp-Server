---
phase: 09-dynamic-resource-attribute-columns
plan: "03"
subsystem: frontend-hooks-components
tags: [react, tanstack-query, localStorage, accessibility, vitest]
dependency_graph:
  requires: ["09-02"]
  provides: ["useResourceAttrKeys", "useColumnPrefs", "ColumnPicker"]
  affects: ["CollectorListPage"]
tech_stack:
  added: []
  patterns:
    - TanStack Query polling hook (same pattern as useStats)
    - localStorage-backed state with immutable functional updater
    - Controlled popover with outside-click and Escape handlers
key_files:
  created:
    - ui/src/hooks/useResourceAttrKeys.ts
    - ui/src/hooks/useColumnPrefs.ts
    - ui/src/components/ColumnPicker.tsx
  modified:
    - ui/src/setupTests.ts
    - ui/vitest.config.ts
decisions:
  - "Used _localStorage internal jsdom property to bypass Node.js 22+ built-in localStorage shadowing issue"
  - "Added jsdom url option in vitest.config.ts for proper origin context"
metrics:
  duration: "~15 minutes"
  completed: "2026-03-30"
  tasks_completed: 2
  files_created: 3
  files_modified: 2
---

# Phase 09 Plan 03: Frontend Hooks and ColumnPicker Component Summary

TanStack Query polling hook, localStorage-backed column preference state, and accessible checkbox popover component for dynamic resource attribute column selection.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | useResourceAttrKeys and useColumnPrefs hooks | 89d6ae3 | ui/src/hooks/useResourceAttrKeys.ts, ui/src/hooks/useColumnPrefs.ts, ui/src/setupTests.ts, ui/vitest.config.ts |
| 2 | ColumnPicker component | 85a0725 | ui/src/components/ColumnPicker.tsx |

## Verification

- All 93 tests pass across 15 test files
- TypeScript compiles with zero errors (`npx tsc --noEmit`)
- useColumnPrefs: 5/5 tests GREEN
- ColumnPicker: 5/5 tests GREEN

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Node.js 22+ built-in localStorage shadows jsdom Storage**

- **Found during:** Task 1, running useColumnPrefs tests
- **Issue:** Node.js 22+ added a built-in `localStorage` global. Vitest's `populateGlobal` skips jsdom properties that already exist in the Node global, so `localStorage` in tests pointed to the Node built-in (which lacks `clear()`, `getItem()`, etc.) instead of jsdom's Storage implementation.
- **Fix:** In `setupTests.ts`, detect if `window._localStorage` exists (jsdom internal) and reassign `globalThis.localStorage` to it. Also added `environmentOptions.jsdom.url: 'http://localhost'` in `vitest.config.ts` to ensure a non-opaque document origin.
- **Files modified:** `ui/src/setupTests.ts`, `ui/vitest.config.ts`
- **Commits:** 89d6ae3

## Known Stubs

None — all three modules have real implementations wired to their data sources (API client and localStorage).

## Self-Check: PASSED

All created files found on disk. Both task commits verified in git log.
