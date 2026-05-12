# Tasks: Fix WSL移植 Issues and Cleanup

**Feature**: Fix WSL移植 Issues and Cleanup
**Branch**: `003-fix`
**Generated**: 2026-03-16

## Overview

This is a cleanup/migration task to fix issues when copying a project from WSL Ubuntu to Windows. The tasks are organized by user story to enable independent testing.

## User Stories Summary

| Story | Priority | Goal | Independent Test |
|-------|----------|------|-----------------|
| US1 | P1 | Fix Path and Line Ending Issues | Run uv sync and verify imports |
| US2 | P2 | Remove Unnecessary Files | Project still functions after cleanup |
| US3 | P3 | Verify Project Structure | pytest runs without errors |

## Phase 1: Remove Unnecessary Files (US2)

**Goal**: Remove Linux-specific cache directories that are not usable on Windows

**Independent Test**: After cleanup, verify project still functions

### Tasks

- [x] T001 Remove .venv directory in project root (not usable on Windows)
- [x] T002 [P] Remove all __pycache__ directories recursively
- [x] T003 Remove .ruff_cache directory
- [x] T004 Remove .pytest_cache directory

## Phase 2: Fix Path and Line Ending Issues (US1)

**Goal**: Fix Unix-specific paths and verify line endings work on Windows

**Independent Test**: Run `uv sync` and verify Python can import modules

### Tasks

- [x] T005 Check .env file for Windows-compatible paths
- [x] T006 Check pyproject.toml for any Unix-specific paths
- [x] T007 Check docker-compose.yml for any Unix-specific paths
- [x] T008 Verify line endings in source files (should work as-is on Windows)

## Phase 3: Verify Project Works (US3)

**Goal**: Verify the project can run successfully on Windows

**Independent Test**: Run pytest and verify API can start

### Tasks

- [x] T009 Run `uv sync` to install dependencies
- [x] T010 Run `ruff check .` to verify no path issues
- [x] T011 Run `pytest` to verify tests work
- [x] T012 Verify API can start (uvicorn backend.main:app --reload)

## Dependencies

```
T001 ─┬─> T002 ─┬─> T003 ─┬─> T004 ─┬─> Phase 1 Complete
      │         │         │         │
      └─────────┴─────────┴─────────┘
                  │
                  v
Phase 2 (T005-T008): Can run in parallel with Phase 1 or after
Phase 3 (T009-T012): Must run AFTER Phases 1 and 2 complete
```

## Parallel Opportunities

- T001-T004: Can run in parallel (different directories)
- T005-T007: Can run in parallel (different config files)
- T008: Independent of T005-T007
- T009-T011: Can run in parallel after Phase 1+2 complete

## Implementation Strategy

### MVP Scope (US2 - Remove Unnecessary Files)
- T001-T004: Remove cache directories
- This is the minimum needed to clean up the project

### Incremental Delivery
1. First: Remove cache directories (T001-T004)
2. Second: Check configs for path issues (T005-T008)
3. Third: Verify everything works (T009-T012)

## Success Criteria Validation

| Criteria | Validation Task |
|----------|-----------------|
| SC-001: uv sync works | T009 |
| SC-002: Cache directories removed | T001-T004 |
| SC-003: No import errors | T010, T011 |
| SC-004: API can start | T012 |

---

**Total Tasks**: 12
**Parallelizable Tasks**: 9
**User Stories Covered**: 3
