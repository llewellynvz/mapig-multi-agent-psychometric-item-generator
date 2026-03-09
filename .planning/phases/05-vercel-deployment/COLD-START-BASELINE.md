# Cold Start Performance Baseline

**Date:** 2026-03-09
**Phase:** 05-vercel-deployment
**Requirement:** DEP-08 (Cold start optimization <5s)
**Status:** DEFERRED TO v2

## Decision Summary

Per 05-CONTEXT.md user decision: Accept longer cold starts for v1 deployment.

**Rationale:**
- Typical Python serverless cold starts: 3-8 seconds
- Warm function performance is more critical (majority of user requests hit warm functions)
- Optimization techniques (lazy imports, dependency pruning, warming strategies) add complexity
- Focus v1 on core functionality and deployment stability
- DEP-08 optimization deferred to v2 phase

## Baseline Measurements

**Methodology:**
Cold start measurements taken in Vercel production environment after initial deployment.

**Measurement approach:**
1. Trigger function cold start (wait 5+ minutes for function idle)
2. Make request to /healthz endpoint
3. Measure time from request initiation to first byte received
4. Repeat 5 times for statistical accuracy
5. Record Vercel function logs for internal initialization time

**Expected baseline (pre-deployment):**
- Cold start: 3-8 seconds (typical Python 3.12 serverless)
- Warm request: <500ms

**Actual baseline (to be measured post-deployment):**

| Attempt | Cold Start Time | Notes |
|---------|----------------|-------|
| 1       | TBD            | Initial cold start after deployment |
| 2       | TBD            | After 5 min idle |
| 3       | TBD            | After 10 min idle |
| 4       | TBD            | After 15 min idle |
| 5       | TBD            | After 20 min idle |

**Average cold start:** TBD seconds

**Warm request baseline:**

| Request | Response Time | Notes |
|---------|--------------|-------|
| 1       | TBD          | Immediate after cold start |
| 2       | TBD          | Sequential request |
| 3       | TBD          | Sequential request |

**Average warm response:** TBD milliseconds

## v2 Optimization Strategies

When DEP-08 becomes priority in v2, consider these approaches:

1. **Lazy imports:** Defer heavy imports (LangGraph, LLM clients) until first use
2. **Dependency pruning:** Remove unused dependencies to reduce bundle size
3. **Code splitting:** Move rarely-used features to separate functions
4. **Warming strategy:** Periodic ping to keep function warm during business hours
5. **Cold start monitoring:** Track cold start frequency and user impact
6. **Vercel Fluid Compute:** Leverage platform optimizations for faster cold starts

## Acceptance Criteria for v2

When revisiting DEP-08 in v2:
- [ ] Cold start consistently <5s (95th percentile)
- [ ] Optimization doesn't degrade warm function performance
- [ ] Monitoring shows reduced user-visible cold start impact
- [ ] Cost/benefit analysis justifies optimization complexity

## References

- User decision: .planning/phases/05-vercel-deployment/05-CONTEXT.md (lines 39-44)
- Research findings: .planning/phases/05-vercel-deployment/05-RESEARCH.md (Cold start section)
- Vercel documentation: https://vercel.com/docs/functions/limitations (Performance section)

---

*Created: 2026-03-09*
*Requirement: DEP-08*
*Status: Deferred to v2 per user decision*
