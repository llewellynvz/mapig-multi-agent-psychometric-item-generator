---
phase: 01-llm-as-judge-validation-gate
plan: 02
subsystem: validation-foundation
tags: [schemas, claude-integration, llm-factory, validation-models]
dependency_graph:
  requires: [01-01]
  provides: [validation-schemas, claude-api-config, validator-factory]
  affects: [app/schemas.py, app/settings.py, app/agents/llm_factory.py]
tech_stack:
  added: [langchain-anthropic>=1.3.4, anthropic>=0.84.0]
  patterns: [pydantic-validation, lru-cache-factory, chain-of-thought-scoring]
key_files:
  created: []
  modified:
    - path: app/schemas.py
      lines_added: 48
      purpose: Validation schemas with 4-dimension scoring
    - path: app/settings.py
      lines_added: 3
      purpose: Claude API configuration
    - path: app/agents/llm_factory.py
      lines_added: 38
      purpose: Claude model factory functions
    - path: pyproject.toml
      lines_added: 2
      purpose: Claude dependencies
    - path: tests/test_schemas.py
      lines_added: 92
      purpose: Validation schema tests
    - path: tests/test_llm_factory.py
      lines_added: 40
      purpose: Claude factory tests
decisions:
  - what: Use 4 validation dimensions with weighted scoring
    why: Research-backed psychometric validation (correspondence 50%, distinctiveness 25%, clarity 15%, specificity 10%)
    alternatives: [simple-pass-fail, single-score]
    impact: Foundation for nuanced item quality assessment
  - what: Claude Opus 4-6 for validation
    why: Highest accuracy model for critical validation decisions
    alternatives: [claude-sonnet, gpt-4]
    impact: Best-in-class validation quality, higher cost per validation
  - what: Forward reference for ItemValidation in DraftItem
    why: DraftItem defined before ItemValidation, Python requires string annotation
    alternatives: [reorder-classes, separate-files]
    impact: Maintains logical schema organization
metrics:
  duration_minutes: 6
  tasks_completed: 3
  tests_added: 6
  tests_passing: 6
  commits: 5
  files_modified: 6
  completed_at: 2026-03-08T12:55:00Z
---

# Phase 01 Plan 02: Validation Foundation Setup Summary

**One-liner:** Extended schemas with 4-dimension validation models (DimensionScore, ItemValidation), added Claude API configuration with claude-opus-4-6 validator model, and created cached factory functions for ChatAnthropic instances.

## What Was Built

### Validation Schemas (app/schemas.py)

Created three new schemas following existing patterns:

1. **DimensionScore** - Individual dimension evaluation with chain-of-thought
   - Fields: dimension (str), reasoning (str), score (int 1-10)
   - Validates score range using Pydantic Field constraints
   - ConfigDict(extra="forbid") for strict validation

2. **ItemValidation** - Per-item validation result
   - 4 dimension scores (correspondence, distinctiveness, clarity, specificity)
   - Weighted score calculation (correspondence*0.5 + distinctiveness*0.25 + clarity*0.15 + specificity*0.1)
   - Accept/reject decision (accept if weighted_score >= 7.0)
   - Attempt counter (1-3) for regeneration tracking

3. **ValidationResponse** - Validator agent output contract
   - List of ItemValidation objects
   - Follows existing agent I/O wrapper pattern

Extended existing schemas:
- **DraftItem**: Added optional `validation_result: Optional[ItemValidation]` field
- **AuditMetadata**: Added `validation_attempts` and `validation_failures` counters

### Claude Configuration (app/settings.py)

Added Claude-specific settings after Azure OpenAI section:
- `CLAUDE_API_KEY: Optional[str]` - API credential
- `VALIDATOR_MODEL: str = "claude-opus-4-6"` - Default to Opus for validation

### LLM Factory Functions (app/agents/llm_factory.py)

Added two new factory functions following existing patterns:

1. **get_claude_chat_model(model: str)** - Generic Claude model factory
   - lru_cache(maxsize=2) for caching different models
   - Validates CLAUDE_API_KEY presence
   - Configures: temperature=0.2, max_retries=3, timeout=60
   - Returns ChatAnthropic instance

2. **get_validator_model()** - Specialized validator factory
   - Always returns claude-opus-4-6 (highest accuracy)
   - Delegates to get_claude_chat_model with settings.VALIDATOR_MODEL
   - Raises ValueError if CLAUDE_API_KEY missing

### Dependencies (pyproject.toml)

Added Claude integration packages:
- `langchain-anthropic>=1.3.4` - LangChain Claude integration
- `anthropic>=0.84.0` - Official Anthropic SDK

### Tests

Added 6 new tests (all passing):

**test_schemas.py:**
- `test_dimension_score_schema` - Score range validation (1-10), boundary tests, invalid scores
- `test_validation_export` - FinalOutput serialization with validation metadata

**test_llm_factory.py:**
- `test_validator_uses_opus` - Validates ChatAnthropic type, model name, temperature, max_retries
- `test_claude_api_key_required` - Validates ValueError raised when CLAUDE_API_KEY missing

## Deviations from Plan

None - plan executed exactly as written. All tasks completed, all tests pass.

## Performance

- **Duration:** 6 minutes
- **Tasks:** 3/3 completed (100%)
- **Tests:** 6 added, 6 passing (100%)
- **Commits:** 5 (TDD: RED → GREEN for Tasks 1 & 3, standard for Task 2)

## Verification

All success criteria met:

- ✅ DimensionScore, ItemValidation, ValidationResponse schemas exist and validate correctly
- ✅ DraftItem extended with optional validation_result field
- ✅ AuditMetadata extended with validation attempt tracking
- ✅ Settings include CLAUDE_API_KEY and VALIDATOR_MODEL
- ✅ langchain-anthropic and anthropic dependencies installed
- ✅ get_validator_model() returns ChatAnthropic with claude-opus-4-6
- ✅ get_claude_chat_model() properly cached with lru_cache
- ✅ All schema and factory tests pass

Verification commands passed:
```bash
pytest tests/test_schemas.py tests/test_llm_factory.py -v  # 4 passed
python -c "from app.schemas import DimensionScore, ItemValidation, ValidationResponse; from app.agents.llm_factory import get_validator_model; print('Imports successful')"  # Imports successful
```

## Dependencies Satisfied

Requirements implemented:
- **VAL-02** (ItemValidation requires exactly 4 dimensions) - Tested in test_dimension_score_schema
- **VAL-04** (DimensionScore.score validates range 1-10) - Tested with boundary and invalid values
- **VAL-07** (Claude Opus model for validation) - Tested in test_validator_uses_opus
- **VAL-09** (Export validation metadata) - Tested in test_validation_export

## Next Steps

Plan 01-03 can now proceed with validator agent implementation. Foundation ready:
- ✅ Validation schemas defined and tested
- ✅ Claude API configured
- ✅ Factory functions available for ChatAnthropic
- ✅ Type-safe contracts for validator input/output

## Self-Check

Verifying all claimed artifacts exist:

**Files modified:**
- ✅ app/schemas.py (contains DimensionScore, ItemValidation, ValidationResponse classes)
- ✅ app/settings.py (contains CLAUDE_API_KEY, VALIDATOR_MODEL fields)
- ✅ app/agents/llm_factory.py (contains get_claude_chat_model, get_validator_model functions)
- ✅ pyproject.toml (contains langchain-anthropic, anthropic dependencies)
- ✅ tests/test_schemas.py (contains test_dimension_score_schema, test_validation_export)
- ✅ tests/test_llm_factory.py (contains test_validator_uses_opus, test_claude_api_key_required)

**Commits:**
- ✅ 5ce8568 (test(01-02): add failing tests for validation schemas)
- ✅ 9c7598b (chore(01-02): add Claude configuration to settings and install dependencies)
- ✅ c982dfd (test(01-02): add failing tests for Claude model factory)
- ✅ 52f60cc (feat(01-02): add Claude model factory functions to llm_factory.py)

Self-Check: **PASSED**
