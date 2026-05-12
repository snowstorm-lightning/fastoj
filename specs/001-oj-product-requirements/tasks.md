# Tasks: 面向面试者的 OJ 平台

**Input**: Design documents from `/specs/001-oj-product-requirements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec - tests will be optional for verification

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project directory structure per implementation plan in backend/ (no frontend - backend API only)
- [X] T002 [P] Initialize Python project with FastAPI dependencies in pyproject.toml [project] section (uv-based)
- [X] T003 [P] Configure docker-compose.yml with PostgreSQL, Redis, API, Worker services
- [X] T004 [P] Setup Dockerfile.api and Dockerfile.worker containers
- [X] T005 Configure ruff and pytest in pyproject.toml for backend

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Setup database schema and migrations framework in backend/alembic/
- [X] T007 [P] Implement core configuration in backend/core/config.py
- [X] T008 [P] Setup database connection in backend/core/database.py
- [X] T009 Create SQLAlchemy base models in backend/models/__init__.py
- [X] T010 Setup API routing structure in backend/api/
- [X] T011 Configure JWT authentication in backend/core/security.py
- [X] T012 [P] Create user authentication endpoints in backend/api/auth/
- [X] T013 Implement error handling middleware in backend/api/middleware/
- [X] T014 Setup Redis connection and queue service in backend/services/queue_service.py
- [X] T015 Configure CORS and logging in backend/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - 题目浏览与详情 (Priority: P1) 🎯 MVP

**Goal**: 用户可以浏览题目列表、按标签和难度筛选、查看题目详情

**Independent Test**: 用户打开题目大厅页面，能够看到题目列表，并能成功应用标签和难度筛选条件

### Implementation for User Stories 1 & 2

- [X] T016 [P] [US1] Create Problem model in backend/models/problem.py
- [X] T017 [P] [US1] Create TestCase model in backend/models/testcase.py
- [X] T018 [P] [US1] Create Solution model in backend/models/solution.py
- [X] T019 [P] [US1] Create Problem Pydantic schemas in backend/schemas/problem.py
- [X] T020 [US1] Implement ProblemService in backend/services/problem_service.py
- [X] T021 [US1] Implement GET /problems endpoint in backend/api/problems/__init__.py
- [X] T022 [US1] Implement GET /problems/{problem_id} endpoint in backend/api/problems/__init__.py
- [X] T023 [US1] Implement GET /problems/{problem_id}/solutions endpoint in backend/api/problems/solutions.py
- [X] T024 [US1] Add pagination and filtering logic in backend/services/problem_service.py

**Checkpoint**: User Stories 1 & 2 should be fully functional

---

## Phase 4: User Story 3 - 代码编写 (Priority: P1)

**Goal**: 用户可以在刷题工作台编写代码

**Independent Test**: 用户进入刷题工作台后，能够选择编程语言并在右侧代码编辑区编写代码

### Implementation for User Story 3

- [X] T025 [P] [US3] Create Submission model in backend/models/submission.py
- [X] T026 [P] [US3] Create Submission Pydantic schemas in backend/schemas/submission.py
- [X] T027 [US3] Implement SubmissionService in backend/services/submission_service.py
- [X] T028 [US3] Implement POST /submissions endpoint in backend/api/submissions/__init__.py
- [X] T029 [US3] Implement GET /submissions/{submission_id} endpoint in backend/api/submissions/__init__.py
- [X] T030 [US3] Implement GET /submissions (user submissions list) endpoint in backend/api/submissions/__init__.py

**Checkpoint**: User Story 3 should be functional

---

## Phase 5: User Story 6 - 多语言支持 (Priority: P1)

**Goal**: 支持 Python, C/C++, Java, TypeScript/JavaScript, Golang 五种语言

**Independent Test**: 用户可以选择任意支持的语言编写代码并成功提交评测

### Implementation for User Story 6

- [X] T031 [P] [US6] Create language enum in backend/core/languages.py
- [X] T032 [P] [US6] Create language validators in backend/core/validators.py
- [X] T033 [US6] Implement language configuration for each supported language in backend/sandbox/languages/
- [X] T034 [US6] Add language selection to submission endpoint validation

**Checkpoint**: Language selection should work end-to-end

---

## Phase 6: User Story 5 & 7 - 评测结果与状态流转 (Priority: P1)

**Goal**: 实时展示 Pending -> Judging -> AC/WA/TLE/MLE/CE 状态流转

**Independent Test**: 用户提交代码后，能够在界面上看到评测状态的实时变化和最终结果

### Implementation for User Stories 5 & 7

- [X] T035 [P] [US5] Implement WebSocket manager in backend/api/websocket/manager.py
- [X] T036 [P] [US5] Create WebSocket endpoint in backend/api/websocket/judge.py
- [X] T037 [P] [US5] Add submission status update logic in backend/services/submission_service.py
- [X] T038 [US5] Implement status notification via WebSocket in backend/api/websocket/judge.py
- [X] T039 [US5] Add result filtering (hide hidden testcase details) in backend/api/submissions/__init__.py

**Checkpoint**: Real-time status updates should work

---

## Phase 7: User Story 8 & 9 - 公开与隐藏测试用例 (Priority: P1)

**Goal**: 运行代码仅使用公开用例，提交代码使用公开+隐藏用例

**Independent Test**: 用户点击"运行代码"后，能够看到公开用例的执行结果；点击"提交"后系统使用全部用例评测

### Implementation for User Stories 8 & 9

- [X] T040 [P] [US8] Add testcase visibility filtering in backend/services/problem_service.py
- [X] T041 [P] [US8] Create TestCaseResult model in backend/models/testcase_result.py
- [X] T042 [US8] Implement "运行代码" endpoint in backend/api/submissions/run.py (uses public only)
- [X] T043 [US8] Update POST /submissions to use public + hidden testcases

**Checkpoint**: Test case visibility should be correctly enforced

---

## Phase 8: User Story 4 - 官方最优解 (Priority: P2)

**Goal**: 用户可以查看题目的官方最优解和详细讲解

**Independent Test**: 用户在刷题工作台能够查看到题目对应的官方最优解和详细讲解

### Implementation for User Story 4

- [X] T044 [US4] Implement solution retrieval in backend/api/problems/solutions.py
- [X] T045 [US4] Add language-based solution filtering in backend/services/solution_service.py

**Checkpoint**: Official solutions should be accessible

---

## Phase 9: 判题 Worker 与沙箱 (Priority: P1)

**Goal**: 实现独立的判题 Worker 和 Docker 沙箱执行环境

**Independent Test**: Worker 能够接收判题任务，执行代码并返回结果

### Implementation for Judge Worker

- [X] T046 [P] Create JudgeWorker main loop in backend/worker/judge_worker.py
- [X] T047 [P] Create task queue consumer in backend/worker/tasks/consumer.py
- [X] T048 [P] Create Docker sandbox executor in backend/sandbox/executor.py
- [X] T049 [P] Implement sandbox security configuration in backend/sandbox/security.py
- [X] T050 [P] Create language-specific runners in backend/sandbox/languages/
- [X] T051 [US6] Implement Python execution in backend/sandbox/languages/python.py
- [X] T052 [US6] Implement C/C++ execution in backend/sandbox/languages/cpp.py
- [X] T053 [US6] Implement Java execution in backend/sandbox/languages/java.py
- [X] T054 [US6] Implement JavaScript execution in backend/sandbox/languages/javascript.py
- [X] T055 [US6] Implement Golang execution in backend/sandbox/languages/golang.py
- [X] T056 [US5] Implement JudgeService in backend/services/judge_service.py
- [X] T057 [US5] Add result processing and storage in backend/worker/tasks/judge_task.py

**Checkpoint**: Judge worker should be able to execute code and return results

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T058 [P] Add database indexes for performance in backend/models/
- [X] T059 [P] Implement Redis token bucket rate limiting (10 submissions/min per user) in backend/api/middleware/rate_limit.py
- [X] T060 Add logging for all judge operations in backend/
- [X] T061 [P] Update docker-compose.yml with health checks
- [X] T062 Run quickstart.md validation
- [X] T063 Create sample data seeding script in backend/scripts/seed_data.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Stories 1 & 2 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 3 (P1)**: Depends on Foundational + Models (T016-T019) - Can run in parallel with other P1 stories
- **User Story 6 (P1)**: Depends on Foundational - Should complete before Judge Worker tasks
- **User Stories 5 & 7 (P1)**: Depends on Foundational + Submission model - Requires Worker/Sandbox
- **User Stories 8 & 9 (P1)**: Depends on Foundational - Requires Worker/Sandbox
- **User Story 4 (P2)**: Can start after Foundational - Depends on Problem model

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1-3 can start in parallel
- Models within Phase 3 marked [P] can run in parallel
- Language implementations in Phase 9 marked [P] can run in parallel

---

## Parallel Example: Phase 3 (User Stories 1 & 2)

```bash
# Launch all models for User Stories 1 & 2 together:
Task: "Create Problem model in backend/models/problem.py"
Task: "Create TestCase model in backend/models/testcase.py"
Task: "Create Solution model in backend/models/solution.py"

# Launch all Pydantic schemas in parallel:
Task: "Create Problem Pydantic schemas in backend/schemas/problem.py"
Task: "Create Submission Pydantic schemas in backend/schemas/submission.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Stories 1 & 2
4. **STOP and VALIDATE**: Test User Story 1 & 2 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Stories 1 & 2 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 → Test independently → Deploy/Demo
4. Add User Story 6 + Judge Worker → Test independently → Deploy/Demo
5. Add User Stories 5, 7, 8, 9 → Test independently → Deploy/Demo
6. Add User Story 4 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Stories 1 & 2 (Problem browsing)
   - Developer B: User Story 3 (Code submission)
   - Developer C: User Story 6 + Judge Worker (Language support + execution)
3. Stories complete and integrate independently

---

## Summary

- **Total Task Count**: 63
- **User Story Breakdown**:
  - User Stories 1 & 2: 9 tasks
  - User Story 3: 6 tasks
  - User Story 4: 2 tasks
  - User Stories 5 & 7: 5 tasks
  - User Stories 8 & 9: 4 tasks
  - User Story 6: 4 tasks
  - Judge Worker: 12 tasks
  - Setup: 5 tasks
  - Foundational: 10 tasks
  - Polish: 6 tasks

- **Parallel Opportunities**: 20+ tasks can run in parallel
- **Independent Test Criteria**:
  - US1 & US2: User can browse problems with filtering
  - US3: User can submit code
  - US4: User can view official solutions
  - US5: User sees real-time judge status
  - US6: All 5 languages work
  - US8: Run uses public testcases only
  - US9: Submit uses all testcases

- **Suggested MVP Scope**: User Stories 1 & 2 (Phase 3) - Problem browsing and viewing
