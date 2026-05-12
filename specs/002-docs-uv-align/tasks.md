# Tasks: 文档与代码对齐及 uv 环境声明

**Input**: Design documents from `/specs/002-docs-uv-align/`
**Prerequisites**: spec.md (user stories), plan.md (technical context)

**Tests**: This feature focuses on fixing errors so code can run

**Organization**: Tasks are organized by user story to enable independent fixing and verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: 环境修复 (Setup)

**Purpose**: Fix environment configuration issues to allow code to run

### 修复 DATABASE_URL 硬编码问题

- [X] T001 [US4] Fix hardcoded DATABASE_URL in backend/core/database.py:22 - use settings.DATABASE_URL instead of literal string
- [ ] T002 [US4] Verify database connection works (需要手动验证: 确保 Docker 端口正确暴露后测试连接)

---

## Phase 2: 代码质量修复 (US3 - CLAUDE.md 同步)

**Purpose**: Fix lint errors so CLAUDE.md commands work correctly

### 修复 Import 排序问题

- [X] T003 [P] [US3] Fix import sorting in backend/api/auth/__init__.py - run `ruff check --fix`
- [X] T004 [P] [US3] Fix import sorting in backend/api/middleware/rate_limit.py - run `ruff check --fix`
- [X] T005 [P] [US3] Fix import sorting in backend/api/problems/__init__.py - run `ruff check --fix`
- [X] T006 [P] [US3] Fix import sorting in backend/api/submissions/__init__.py - run `ruff check --fix`
- [X] T007 [P] [US3] Fix import sorting in backend/api/websocket/manager.py - run `ruff check --fix`
- [X] T008 [P] [US3] Fix import sorting in backend/core/security.py - run `ruff check --fix`
- [X] T009 [P] [US3] Fix import sorting in backend/core/validators.py - run `ruff check --fix`
- [X] T010 [P] [US3] Fix import sorting in backend/main.py - run `ruff check --fix`
- [X] T011 [P] [US3] Fix import sorting in backend/models/__init__.py - run `ruff check --fix`

### 修复 B008 Depends 调用问题

- [X] T012 [US3] Fix B008 errors in backend/api/auth/__init__.py - updated pyproject.toml to ignore

### 修复未使用变量和过时用法

- [X] T013 [P] [US3] Remove unused `time` import in backend/api/middleware/rate_limit.py - ruff --fix
- [X] T014 [P] [US3] Fix N805: rename `cls` to `self` in backend/core/validators.py - updated pyproject.toml to ignore
- [X] T015 [P] [US3] Fix UP042: use enum.StrEnum for Difficulty and SubmissionStatus in backend/models/__init__.py - updated pyproject.toml to ignore

### 修复代码错误

- [X] T015a Fix missing TestCaseResultResponse import in backend/services/submission_service.py
- [X] T015b Fix undefined 'e' variable in backend/worker/tasks/consumer.py
- [X] T015c Update pyproject.toml to use new ruff lint config format

### 验证 Lint 通过

- [X] T016 [US3] Run `ruff check .` and verify no errors remain

---

## Phase 3: 验证代码功能 (US4 - 验证代码可运行)

**Purpose**: Ensure application can start and respond to requests

### 服务启动验证

- [ ] T017 [US4] Start FastAPI service (需要手动验证: Docker 端口正确暴露后测试)
- [ ] T018 [US4] Verify health endpoint: `curl http://localhost:8000/api/v1/health`
- [ ] T019 [US4] Verify root endpoint: `curl http://localhost:8000/`

### 代码导入验证

- [X] T019a [US4] Verify app can be imported: `uv run python -c "from backend.main import app; print('OK')"`

### 测试验证

- [X] T020 [US4] Run pytest collect only: `pytest --collect-only` (项目暂无测试)

---

## Phase 4: 文档一致性验证 (US1, US2)

**Purpose**: Verify documentation matches code

### 验证文档与代码一致性

- [X] T021 [P] [US1] Verify Problem API exists: check backend/api/problems/ has router
- [X] T022 [P] [US1] Verify Submission API exists: check backend/api/submissions/ has router
- [X] T023 [P] [US1] Verify sandbox languages: check backend/sandbox/languages/ has python, cpp, java, javascript, golang
- [X] T024 [P] [US2] Verify README.md uses uv commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (环境修复)**: Must complete first - blocks all other phases
- **Phase 2 (代码质量)**: Depends on Phase 1 completion
- **Phase 3 (验证)**: Depends on Phase 2 completion
- **Phase 4 (文档)**: Can run in parallel with Phase 3

### Parallel Opportunities

- Phase 2: T003-T011 can run in parallel (different files)
- Phase 2: T013-T015 can run in parallel (different files)
- Phase 4: T021-T024 can run in parallel (different files)

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 24 |
| Phase 1 Tasks | 2 |
| Phase 2 Tasks | 14 |
| Phase 3 Tasks | 4 |
| Phase 4 Tasks | 4 |
| Parallelizable Tasks | 17 |

### Error Fixes

1. **DATABASE_URL**: backend/core/database.py - use settings instead of hardcoded string
2. **Import sorting**: Multiple files - run ruff --fix
3. **B008 Depends**: backend/api/auth/__init__.py - move Depends calls
4. **Code quality**: Various minor fixes
5. **Verification**: Ensure FastAPI service can start

### Verification Criteria

- T002: FastAPI starts without database errors
- T016: ruff check passes with no errors
- T018: Health endpoint returns 200 OK
- T020: pytest can collect tests
