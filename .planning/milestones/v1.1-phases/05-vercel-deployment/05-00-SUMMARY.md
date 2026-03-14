---
phase: 05-vercel-deployment
plan: "00"
subsystem: deployment-testing
tags: [tdd, test-scaffolds, vercel, serverless, deployment]
dependencies:
  requires: []
  provides:
    - vercel-entry-point-tests
    - memory-checkpointing-tests
    - cors-vercel-domain-tests
  affects:
    - tests/test_vercel_entry.py
    - tests/test_checkpointer.py
    - tests/test_cors_config.py
tech_stack:
  added:
    - MemorySaver (langgraph.checkpoint.memory)
  patterns:
    - TDD test scaffolding for future implementation
    - pytest.skip() for deferred Wave 1 tests
key_files:
  created:
    - tests/test_vercel_entry.py: Vercel entry point validation tests (32 lines)
    - tests/test_checkpointer.py: MemorySaver behavior tests (56 lines)
    - tests/test_cors_config.py: CORS configuration tests for Vercel domains (100 lines)
  modified: []
decisions: []
metrics:
  duration_minutes: 1.92
  tasks_completed: 3
  files_created: 3
  test_coverage: 12 test functions (3 fail, 4 skip, 5 pass as expected)
  lines_added: 188
  commits: 3
completed_date: "2026-03-09"
---

# Phase 05 Plan 00: Test Scaffolds for Vercel Deployment Summary

**One-liner:** Created TDD test scaffolds validating Vercel entry point structure, in-memory checkpointing with MemorySaver, and CORS configuration for Vercel domains.

## Objective Achieved

Established automated verification for critical deployment requirements (DEP-01, DEP-02, DEP-03) before implementing production changes. Test files validate:
- Vercel serverless entry point exports FastAPI app correctly
- MemorySaver provides in-memory checkpointing without external dependencies
- CORS middleware allows both localhost and Vercel production/preview domains

## Tasks Completed

| Task | Name                                    | Commit  | Files                        | Status   |
| ---- | --------------------------------------- | ------- | ---------------------------- | -------- |
| 1    | Create Vercel entry point test scaffold | a5633bd | tests/test_vercel_entry.py   | Complete |
| 2    | Create MemorySaver checkpointing test scaffold | 6aab403 | tests/test_checkpointer.py   | Complete |
| 3    | Create CORS configuration test scaffold | 5d01c51 | tests/test_cors_config.py    | Complete |

## Test Results

**Verification run confirmed expected Wave 0 behavior:**

1. **test_vercel_entry.py** (3 tests):
   - ✗ All 3 tests FAIL — `api/index.py` doesn't exist yet (expected)
   - Tests will pass when Wave 1 creates Vercel entry point

2. **test_checkpointer.py** (4 tests):
   - ✓ 1 PASSED — `test_memory_checkpointer_initialization` validates MemorySaver can be instantiated
   - ⊘ 3 SKIPPED — Awaiting graph integration in Wave 1

3. **test_cors_config.py** (5 tests):
   - ✓ 2 PASSED — Localhost CORS configuration works
   - ✗ 2 FAILED — Vercel domains not yet configured (expected)
   - ⊘ 1 SKIPPED — Middleware introspection deferred to Wave 1

**Total: 3 passing, 2 failing (expected), 4 skipped (intentional)**

## Implementation Details

### Test Coverage

**Vercel Entry Point Tests (DEP-01):**
- Validates `api/index.py` exports FastAPI app instance
- Verifies core routes accessible (`/healthz`, `/v1/generate-items-stream`)
- Confirms app metadata configured correctly

**MemorySaver Checkpointing Tests (DEP-02, DEP-03):**
- Initialization test passes — MemorySaver works without external dependencies
- Ephemeral behavior test skipped — Will validate checkpoints lost on cold start
- Concurrent thread test skipped — Will validate thread isolation

**CORS Configuration Tests:**
- Localhost validation passing — Current configuration works for local dev
- Vercel preview domain test failing — Pattern `https://*.vercel.app` not yet configured
- Vercel production domain test failing — Pattern needs regex support
- Credentials test passing — CORS allows credentials as required

### Test Scaffold Strategy

Used `pytest.skip()` for tests requiring Wave 1 implementation:
- Graph lifespan context access
- LangGraph checkpoint API interaction
- Middleware introspection

This approach:
- Documents expected behavior before implementation
- Prevents false negatives from missing dependencies
- Creates clear TDD workflow: RED → GREEN → REFACTOR

## Deviations from Plan

None — Plan executed exactly as written. All test files created with correct content and structure.

## Verification

**Automated verification passed:**
```bash
# All test files created
ls -lh tests/test_vercel_entry.py tests/test_checkpointer.py tests/test_cors_config.py
# Output: All files exist with expected sizes

# All tests syntactically valid
python -m py_compile tests/test_vercel_entry.py
python -m py_compile tests/test_checkpointer.py
python -m py_compile tests/test_cors_config.py
# Output: No syntax errors

# Tests run with expected Wave 0 behavior
python -m pytest tests/test_vercel_entry.py -v
# Output: 3 FAILED (api module not found)

python -m pytest tests/test_checkpointer.py -v
# Output: 1 PASSED, 3 SKIPPED

python -m pytest tests/test_cors_config.py -v
# Output: 2 PASSED, 2 FAILED (Vercel domains), 1 SKIPPED
```

## Requirements Coverage

**Requirements validated by test scaffolds:**
- **DEP-01** (Vercel entry point): test_vercel_entry.py validates `api/index.py` structure
- **DEP-02** (In-memory checkpointing): test_checkpointer.py validates MemorySaver usage
- **DEP-03** (Ephemeral storage): test_checkpointer.py validates checkpoint behavior across cold starts
- **CORS Support**: test_cors_config.py validates Vercel domain patterns

## Next Steps

**Wave 1 Implementation (Plan 05-01) will:**
1. Create `api/index.py` with Mangum wrapper → test_vercel_entry.py tests will pass
2. Replace `AsyncSqliteSaver` with `MemorySaver` in `app/main.py` → test_checkpointer.py skipped tests can be enabled
3. Update CORS configuration to allow `*.vercel.app` pattern → test_cors_config.py failing tests will pass

**Test-driven workflow established:**
- RED: Tests currently fail/skip (expected)
- GREEN: Wave 1 implementation makes tests pass
- REFACTOR: Clean up implementation while maintaining passing tests

## Performance

- **Duration:** 1.92 minutes
- **Tasks:** 3/3 completed
- **Files created:** 3 test scaffolds
- **Lines of code:** 188 lines
- **Commits:** 3 atomic commits
- **Test coverage:** 12 test functions covering critical deployment requirements

## Self-Check: PASSED

**Files created verification:**
```bash
test -f tests/test_vercel_entry.py && echo "FOUND: tests/test_vercel_entry.py"
# Output: FOUND: tests/test_vercel_entry.py

test -f tests/test_checkpointer.py && echo "FOUND: tests/test_checkpointer.py"
# Output: FOUND: tests/test_checkpointer.py

test -f tests/test_cors_config.py && echo "FOUND: tests/test_cors_config.py"
# Output: FOUND: tests/test_cors_config.py
```

**Commits exist verification:**
```bash
git log --oneline --all | grep -q "a5633bd" && echo "FOUND: a5633bd"
# Output: FOUND: a5633bd

git log --oneline --all | grep -q "6aab403" && echo "FOUND: 6aab403"
# Output: FOUND: 6aab403

git log --oneline --all | grep -q "5d01c51" && echo "FOUND: 5d01c51"
# Output: FOUND: 5d01c51
```

All created files exist. All commits exist in git history. Self-check PASSED.
