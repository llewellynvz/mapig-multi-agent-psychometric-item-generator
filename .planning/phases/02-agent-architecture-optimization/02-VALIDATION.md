---
phase: 02
slug: agent-architecture-optimization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (installed in Phase 1) |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -k "agent" --tb=short` |
| **Full suite command** | `pytest tests/ --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k "agent" --tb=short`
- **After every plan wave:** Run `pytest tests/ --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | AGT-XX | unit | `pytest tests/test_agents.py -k "test_name"` | TBD | ⬜ pending |

*Planner will populate this table based on plan tasks*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_item_writer.py` — stubs for AGT-01 through AGT-04 (Item Writer principles)
- [ ] `tests/test_bias_reviewer.py` — stubs for AGT-07, AGT-08 (7 bias types, multi-pass)
- [ ] `tests/test_agents.py` — general agent validation stubs if needed

*Planner will identify specific Wave 0 gaps based on research*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reading level assessment | AGT-03 | Flesch-Kincaid not automated per user decision | Generate items, manually check reading level via online tool |
| Semantic diversity validation | AGT-02 | Qualitative assessment of item variety | Review generated item set for paraphrasing vs. true diversity |
| Intersectional bias detection | AGT-08 | Complex identity combinations require expert judgment | Expert review of bias reviewer output for intersectional cases |

*Planner may add more based on research findings*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
