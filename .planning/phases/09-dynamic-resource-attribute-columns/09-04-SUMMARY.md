---
phase: 09-dynamic-resource-attribute-columns
plan: "04"
subsystem: frontend
tags: [react, dynamic-columns, resource-attributes, column-picker]
dependency_graph:
  requires: ["09-03"]
  provides: ["CollectorListPage with dynamic resource attribute columns"]
  affects: ["ui/src/pages/CollectorListPage.tsx"]
tech_stack:
  added: []
  patterns: ["inline CSS grid for dynamic column count", "localStorage for column prefs"]
key_files:
  created: []
  modified:
    - ui/src/pages/CollectorListPage.tsx
    - ui/src/pages/__tests__/CollectorListPage.test.tsx
decisions:
  - "Used inline style gridTemplateColumns instead of dynamic Tailwind class to avoid purge issue"
  - "localStorage cleared in beforeEach to isolate column pref state between tests"
  - "em dash rendered via unicode u2014 in span with aria-label for accessibility"
metrics:
  duration: "~10 minutes"
  completed: "2026-03-30"
  tasks_completed: 1
  files_modified: 2
---

# Phase 9 Plan 04: CollectorListPage Integration Summary

Wire all Phase 9 hooks and components (useResourceAttrKeys, useColumnPrefs, ColumnPicker) into CollectorListPage, producing a fully dynamic resource attribute column table with inline CSS grid sizing and localStorage persistence.

## What Was Done

### Task 1: Wire hooks and ColumnPicker into CollectorListPage

Modified `CollectorListPage.tsx` to:

1. Import `useResourceAttrKeys`, `useColumnPrefs`, and `ColumnPicker`
2. Call both hooks inside the component body; compute `gridStyle` from `4 + enabledKeys.length`
3. Replace both `grid-cols-4` static classes with `style={gridStyle}` inline CSS on the header and each data row
4. Render `enabledKeys.map(key => <span>{key}</span>)` after the four fixed column headers
5. Render `enabledKeys.map(key => ...)` dynamic cells per row, using `collector.resource_attributes[key]` with em dash fallback (`\u2014`) wrapped in `aria-label="not available"` span
6. Place `<ColumnPicker allKeys={attrKeys ?? []} enabledKeys={enabledKeys} onToggle={toggleKey} />` in the header controls div, left of the refresh spinner

Added 4 integration tests to `CollectorListPage.test.tsx`:
- "renders host.name column header by default" — asserts text "host.name" present after data loads
- "renders resource attribute value from collector data" — asserts "web-01" visible (MSW returns it)
- "renders em dash when attribute is absent for a collector" — sets localStorage to enable `os.type`, second collector has no `os.type`, asserts `span[aria-label="not available"]` present
- "renders ColumnPicker button in the header" — asserts button with `aria-label="Configure visible columns"`

## Verification Results

- Frontend tests: 11/11 passed (7 pre-existing + 4 new)
- TypeScript: `tsc --noEmit` clean, no errors
- Python backend: 98/98 passed

## Deviations from Plan

### Auto-fix: Test wrapper pattern alignment

- **Found during:** Task 1 test authoring
- **Issue:** Plan instructed using `AllProviders` wrapper but the existing test file uses `renderWithProviders` helper consistently
- **Fix:** Used `renderWithProviders` to stay consistent with the existing test suite conventions
- **Files modified:** ui/src/pages/__tests__/CollectorListPage.test.tsx

### Auto-add: `beforeEach` localStorage.clear()

- **Found during:** Task 1 — em dash test required enabling `os.type` via localStorage
- **Issue:** Without isolation, localStorage from one test could bleed into the next
- **Fix:** Added `beforeEach(() => { localStorage.clear() })` and set `localStorage` explicitly in the em dash test
- **Files modified:** ui/src/pages/__tests__/CollectorListPage.test.tsx

## Known Stubs

None. All dynamic columns are fully wired end-to-end.

## Self-Check: PASSED

- FOUND: ui/src/pages/CollectorListPage.tsx
- FOUND: ui/src/pages/__tests__/CollectorListPage.test.tsx
- FOUND: commit d59548f
