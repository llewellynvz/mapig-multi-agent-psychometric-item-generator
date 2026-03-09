---
status: testing
phase: 01-llm-as-judge-validation-gate
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md
started: 2026-03-08T19:30:00Z
updated: 2026-03-08T19:30:00Z
---

## Current Test

number: 1
name: Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: [pending]

### 2. Validation Gate Workflow
expected: Generate items using the API (e.g., 5 items for a construct). Items are automatically validated using Claude Opus with 4-dimension scoring. If any items score below 7.0 weighted threshold, they are automatically regenerated (max 3 attempts). The final API response includes validation_result for each item with weighted scores and accept/reject status.
result: [pending]

### 3. Validation Score Display in Results UI
expected: After generating items, Results UI displays validation information for each item: weighted score (0-10), accept/reject badge (green for accepted, red for rejected), and attempt number if item was regenerated (e.g., "Attempt 2"). Clicking "Show reasoning" expands to reveal 4 dimension scores (correspondence, distinctiveness, clarity, specificity) with detailed reasoning text for each dimension.
result: [pending]

### 4. Real-time Validation Progress
expected: During item generation workflow, SSE stream displays status messages: "Validating item quality..." when validation starts. If items fail validation, warning message shows count (e.g., "2 items below quality threshold, regenerating..."). If regeneration occurs, "Regenerating low-scoring items..." message appears before retry.
result: [pending]

### 5. Validation Metadata in Audit Section
expected: Results UI audit section displays validation summary statistics showing total validation attempts across all items and count of items that failed validation (e.g., "Validation attempts: 2" and "Validation failures: 1" or similar display format).
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0

## Gaps

[none yet]
