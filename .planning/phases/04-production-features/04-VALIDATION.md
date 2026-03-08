---
phase: 04
slug: production-features
status: ready
nyquist_compliant: true
wave_0_complete: pending
created: 2026-03-08
updated: 2026-03-08
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest + @testing-library/react |
| **Config file** | frontend/vitest.config.ts |
| **Quick run command** | `cd frontend && npm test -- --run` |
| **Full suite command** | `cd frontend && npm test -- --run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run`
- **After every plan wave:** Run `cd frontend && npm test -- --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-00 | 01 | 0 | (infrastructure) | scaffold | `cd frontend && npm test -- --run` | ❌ W0 | ⬜ pending |
| 04-01-01 | 01 | 1 | FEAT-01, FEAT-02, FEAT-03 | unit | `cd frontend && npm test -- export.test.ts --run` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | FEAT-04, FEAT-05, FEAT-06 | integration | `cd frontend && npm test -- GeneratedItemsTable.test.tsx --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/vitest.config.ts` — Vitest configuration with React/JSDOM setup
- [ ] `frontend/src/test/setup.ts` — Test setup file with jest-dom imports
- [ ] `frontend/package.json` — Add "test" script and install vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom
- [ ] `frontend/src/lib/__tests__/export.test.ts` — Scaffold for export function tests
- [ ] `frontend/src/components/__tests__/GeneratedItemsTable.test.tsx` — Scaffold for UI integration tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CSV opens correctly in Excel | FEAT-02 | Excel-specific rendering | Open exported CSV in Excel, verify UTF-8 chars display, no quote corruption |
| File download triggers browser save dialog | FEAT-01 | Browser-specific behavior | Click download, verify save dialog appears with correct filename |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags (uses `--run` flag)
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready for execution

---

## Revision History

**2026-03-08 - Initial creation**
- Created validation strategy for 3-plan structure (01, 02, 03)

**2026-03-08 - Revision (checker feedback)**
- Updated to reflect single-plan structure (04-01 only)
- Added Wave 0 task for test infrastructure setup
- Updated test file paths to match actual implementation (export.test.ts, GeneratedItemsTable.test.tsx)
- Changed nyquist_compliant to true (all tasks now have automated verify)
- Changed wave_0_complete to pending (will be set to true after Wave 0 executes)
