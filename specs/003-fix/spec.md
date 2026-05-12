# Feature Specification: Fix WSL移植 Issues and Cleanup

**Feature Branch**: `003-fix`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "当前项目是刚从wsl里的ubuntu直接复制过来的，修复移植问题，去除无用的文件"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Path and Line Ending Issues (Priority: P1)

Project copied from WSL Ubuntu may have path separators and line ending issues on Windows.

**Why this priority**: The project may not run at all without fixing these fundamental issues.

**Independent Test**: Can be tested by running `uv sync` and verifying Python can import modules correctly.

**Acceptance Scenarios**:

1. **Given** a project copied from WSL Ubuntu, **When** checking for Unix-style paths in configuration files, **Then** all paths should use Windows-compatible formats or environment variables
2. **Given** text files with Unix line endings (LF), **When** examining source files, **Then** line endings should be either preserved (works on Windows) or converted to Windows-style (CRLF) as appropriate for the project

---

### User Story 2 - Remove Unnecessary Files (Priority: P2)

Remove cache directories and Linux-specific artifacts that are not needed on Windows.

**Why this priority**: Cleanup reduces confusion and potential issues from stale cache files.

**Independent Test**: Can be verified by checking that project still functions after cleanup.

**Acceptance Scenarios**:

1. **Given** the project root, **When** listing directories, **Then** `.venv` directory should be removed (needs recreation on Windows)
2. **Given** the project directories, **When** searching for cache directories, **Then** all `__pycache__` directories should be removed
3. **Given** the project, **When** checking for cache folders, **Then** `.ruff_cache` and `.pytest_cache` should be removed
4. **Given** the project root, **When** examining hidden files, **Then** any Unix-specific dotfiles (like `.bashrc`, `.profile`, `.ssh`) should be identified if present

---

### User Story 3 - Verify Project Structure (Priority: P3)

Verify that all essential project files are present and properly configured after transplant.

**Why this priority**: Ensures the project is in a working state after migration.

**Independent Test**: Can be verified by running project tests or starting the application.

**Acceptance Scenarios**:

1. **Given** the project, **When** running `uv sync`, **Then** dependencies should install without errors
2. **Given** the project, **When** running linting with ruff, **Then** there should be no errors related to file paths
3. **Given** the project, **When** running pytest, **Then** tests should execute without import errors

---

### Edge Cases

- What happens if critical configuration files reference Unix-specific paths?
- How to handle files that may have been symlinks in WSL (need to recreate as real files)?
- Should `.env` file be preserved or reset with new values?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove `.venv` directory (Linux virtual environment is not usable on Windows)
- **FR-002**: System MUST remove all `__pycache__` directories recursively
- **FR-003**: System MUST remove `.ruff_cache` and `.pytest_cache` directories
- **FR-004**: System MUST identify and report any Unix-specific paths in configuration files
- **FR-005**: System MUST verify project dependencies can be reinstalled with `uv sync`
- **FR-006**: System MUST ensure `.env` file exists and is properly configured for Windows environment
- **FR-007**: System MUST check and fix any line ending issues in source files if causing problems

### Key Entities

- **Project Root**: The main directory containing all project files
- **Cache Directories**: `.venv`, `__pycache__`, `.ruff_cache`, `.pytest_cache`
- **Configuration Files**: `.env`, `pyproject.toml`, `docker-compose.yml`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Project can successfully run `uv sync` without errors
- **SC-002**: All cache directories (.venv, __pycache__, .ruff_cache, .pytest_cache) are removed
- **SC-003**: No import errors when running Python from the project root
- **SC-004**: Project can be started (API server can launch) without path-related errors

## Assumptions

- The user wants to keep the project code and configuration but needs it to work on Windows
- The `.env` file contains local development settings that should be preserved (or reset if problematic)
- Cache files are safe to delete and will be regenerated on Windows
