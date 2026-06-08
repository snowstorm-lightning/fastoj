# 07. 项目讲解速查

这篇用于帮助读者用一条清晰主线讲 FastOJ。目标不是把所有技术细节一次性讲完，而是先建立项目轮廓，再按需要深入架构、判题、安全边界、测试和后续改进。

## 建议讲解顺序

| 阶段 | 讲解重点 |
| --- | --- |
| 开场 | 用一段话说明 FastOJ 是什么、解决什么问题、核心链路是什么。 |
| 架构 | 讲整体拓扑：React、FastAPI、PostgreSQL、Redis Streams、Worker、Docker judge、AI provider。 |
| 核心链路 | 深讲判题：Run/Submit、SubmissionService、QueueService、Worker、Sandbox、WebSocket。 |
| 设计亮点 | 选择一个重点展开：隐藏用例隔离、Function mode 包装、队列可靠性或 Docker sandbox。 |
| 工程质量 | 讲测试、部署、生产/开发环境边界和可观测性。 |
| 后续方向 | 说明还可以如何继续增强，例如 e2e、队列仪表盘、多 Worker 压测和更强 sandbox。 |

## 60 秒英文项目介绍

FastOJ is an AI-assisted online judge for algorithm practice. It provides a LeetCode-like workflow with a React and TypeScript frontend, a FastAPI backend, PostgreSQL persistence, Redis Streams for asynchronous judging, and Docker-based sandbox execution for untrusted user code. The core flow is that a user submits code from the workbench, the API creates a submission, pushes a judge task to Redis, a worker consumes it, runs the code in a restricted Docker container, stores testcase results, and streams progress back through WebSocket with polling as a fallback. The workbench separates fixed learning material from personalized assistance: the left detail dock holds examples, official hints, solutions, judge history, submission trail, and discussion, while the right AI copilot focuses on result explanation, code review, dynamic hints, and follow-up chat. The safety boundary is explicit: hidden testcase inputs, expected outputs, actual outputs, and imported raw source material are not exposed to normal users or learner-side AI prompts.

## 中文版本

FastOJ 是一个面向面试训练的 AI 辅助在线评测平台。前端用 React 和 TypeScript，后端用 FastAPI，数据存在 PostgreSQL，判题任务通过 Redis Streams 异步分发，Worker 用 Docker 沙箱执行不可信用户代码。用户在工作台提交代码后，API 创建提交记录并入队，Worker 消费任务、运行测试用例、写入结果，再通过 Redis Pub/Sub 和 WebSocket 把进度推回前端，同时前端保留 polling fallback。工作台把固定学习材料和个性化辅助分开：左侧详情区放公开用例、官方提示、题解、判题记录、提交轨迹和讨论，右侧 AI 判题助手负责解释结果、审查代码、动态提示和追问。隐藏用例内容和导入原文不会进入普通用户 UI、日志或学习者侧 AI prompt。

## 架构关键词

- FastAPI service layer
- PostgreSQL with SQLAlchemy models
- Redis Streams consumer group
- Judge worker
- Docker sandbox execution
- WebSocket-first status updates
- Polling fallback
- Function mode harness generation
- Hidden testcase isolation
- OpenAI-compatible AI provider profiles
- Admin-only problem authoring and import workflow

## 常见技术问题和回答要点

### 1. Why did you use Redis Streams for judging?

The judge queue needs more than fire-and-forget delivery. Redis Streams gives message ids, consumer groups, ack, pending messages, and a path for reclaiming or dead-lettering failed work. That fits judge workers because tasks can be slow, workers can crash, and multiple workers should be able to consume from the same stream safely.

代码锚点：[QueueService.push_task](../../backend/services/queue_service.py#L116)、[QueueService.pop_stream_task](../../backend/services/queue_service.py#L134)、[retry_or_dead_letter](../../backend/services/queue_service.py#L155)。

### 2. How do you execute untrusted user code safely?

Production execution is Docker-first. The executor creates a temporary container from the judge runtime image, copies source and input through the Docker archive API, disables networking, limits memory and process count, drops Linux capabilities, enables no-new-privileges, and runs as a non-root user. Unsafe host subprocess execution is disabled unless explicitly configured for local experiments.

代码锚点：[Docker sandbox](../../backend/sandbox/executor.py#L92)、[network disabled](../../backend/sandbox/executor.py#L186)、[cap drop](../../backend/sandbox/executor.py#L188)。

### 3. How do you prevent hidden test leakage?

There are multiple layers. The judge does not store hidden input, expected output, or actual output in testcase result rows. The submission API filters hidden results for normal users. The AI service builds context only from public testcase results and uses a hidden failure notice instead of hidden data. WebSocket progress for full submissions also avoids exposing hidden case details.

代码锚点：[JudgeTask hidden result write](../../backend/worker/tasks/judge_task.py#L219)、[submission API filter](../../backend/api/submissions/__init__.py#L85)、[AI context](../../backend/ai/service.py#L112)。

### 4. How does Function mode work?

Function mode is a transformation layer. The user writes a function, but before judging the backend wraps it in a generated stdin/stdout harness based on the problem signature. The harness parses JSON-line input, calls the function, formats the return value, and then the same Docker judge pipeline can execute it like a normal program.

代码锚点：[SubmissionService._prepare_judge_code](../../backend/services/submission_service.py#L126)、[wrap_function_submission](../../backend/services/function_mode.py#L2468)、[frontend starter generation](../../frontend/src/lib/problemModes.ts#L712)。

### 5. What happens if the worker is down?

The API checks for a live worker heartbeat before pushing an async judge task. In debug/development mode, inline fallback can be used for local troubleshooting. In production, inline fallback is disabled, so Redis or worker unavailability returns `503 Judge service unavailable` instead of moving judge load into the FastAPI process. Workers refresh heartbeat in the background while long judge tasks are running. Each task runs in a child process supervised by the worker parent; if the child hangs, the parent terminates it and retries or dead-letters the stream message. If the parent crashes, its heartbeat expires and pending reclaim can move the unacked message to another worker.

代码锚点：[worker heartbeat](../../backend/services/queue_service.py#L44)、[has_live_worker](../../backend/services/queue_service.py#L58)、[worker parent](../../backend/worker/judge_worker.py)、[dispatch policy](../../backend/services/submission_service.py#L136)。

### 6. How does the frontend get real-time status?

After a submission is created, the workbench opens a WebSocket for that submission and also starts polling the submission detail endpoint. WebSocket gives real-time progress; polling guarantees the final state still appears if the socket misses a result event.

代码锚点：[judge action](../../frontend/src/main.tsx#L1456)、[connectStatus](../../frontend/src/main.tsx#L1497)、[makeJudgeSocket](../../frontend/src/lib/api.ts#L564)。

### 7. How did you test it?

The project uses backend unit tests for queue semantics, submission fallback, worker behavior, sandbox execution, Function mode wrapping, AI safety, and auth. On the frontend, tests cover API error formatting, schemas, i18n, problem mode helpers, and major UI panels. For integration confidence, the project has Docker Compose smoke checks and a manual browser acceptance harness that specifically checks hidden-test safety.

参考：[tests](../../tests)、[acceptance harness](../ACCEPTANCE_HARNESS.md)。

### 8. How does the admin problem import workflow work?

Admins paste external problem material into a separate import tab, optionally with a source URL and adaptation notes. The backend creates a `problem_import` run, sends the raw material only to the import-specific prompt, asks the model to extract and rewrite the task into the existing `AuthoredProblemDraft` JSON schema, and then reuses the normal validation, repair, persistence, and approval flow. The raw material is stored as admin-only draft source metadata, not in published problem responses.

代码锚点：[import API](../../backend/api/admin_agent.py#L49)、[import request schema](../../backend/schemas/problem_authoring.py#L78)、[import service](../../backend/services/problem_authoring_agent.py#L373)、[import prompt](../../backend/ai/prompts/problem_authoring.py#L19)、[frontend import form](../../frontend/src/main.tsx#L2456)。

## 可强调的项目亮点

- **Real judge pipeline**：不是浏览器模拟，不是直接 host subprocess。
- **Reliability-aware queue**：Redis Streams、ack、retry、dead-letter、pending reclaim。
- **Security boundary**：隐藏用例不进入普通 API、WebSocket、AI prompt。
- **Mode abstraction**：Function mode 和 ACM mode 共用同一条判题管线。
- **Learner-friendly workbench**：可折叠题头、可调整左右面板、固定官方提示和动态 AI 提示分工明确，减少练习时的信息噪音。
- **AI with constraints**：AI 辅助解释、出题和导入，但 prompt 上下文和原始材料可见范围被明确限制。
- **Extensible i18n**：前端 locale registry 和后端 dynamic locale validator 支持长期扩展，不把语言逻辑写成 `zh/en` 二分。
- **Deployment-ready shape**：Docker Compose、本地/生产配置、GitHub Actions、部署文档。

## 常见取舍

### 为什么没有一开始就用 Kubernetes？

For this project size, Docker Compose is enough to make the full topology reproducible: API, worker, database, Redis, and judge runtime. The design still separates API and worker, so moving to Kubernetes later would mostly be an operational migration rather than a rewrite of the judge flow.

### 为什么前端很多逻辑集中在 `main.tsx`？

The current frontend prioritized product completeness and fast iteration. The state boundaries are already visible: API client, i18n, problem mode helpers, editor, run result panel, AI panel, graph, and store are separate. Heavy modules such as Monaco, Shiki, React Flow, xterm, auth/settings, and side panels are already lazy-loaded, so the current tradeoff is mainly that view orchestration still lives in one file. A future refactor would split view components into route-level modules without changing backend contracts.

### 如何扩展第三种语言？

The extension path is to add locale metadata and fallback labels in the frontend registry, add backend locale metadata and validation in one place, then fill UI copy incrementally through `localeText`/`localeValue` fallback helpers. That avoids scattering binary language checks across components and keeps API validation tied to the supported locale list.

代码锚点：[frontend LOCALE_META](../../frontend/src/lib/i18n.ts#L4)、[backend locale validator](../../backend/core/locales.py#L30)、[App lang sync](../../frontend/src/main.tsx#L3462)。

### 为什么 AI 不直接生成最终答案？

The product goal is training, not answer dumping. AI is constrained to hints, explanation, review, and safe conversation. It should help the learner debug and reason while preserving the integrity of hidden tests and the learning experience.

## 后续改进方向

1. Add automated Playwright e2e coverage for auth, library search, run/submit, WebSocket fallback, AI stale-state cleanup, and admin workflows.
2. Add queue observability: worker heartbeat dashboard, pending count, dead-letter count, average judge latency, and per-language failure rate.
3. Split the frontend workbench into smaller route-level modules; Monaco/Shiki are already lazy-loaded, but route-level modules would further reduce the main entry and make `main.tsx` easier to maintain.
4. Improve sandbox isolation further with stronger seccomp profiles, per-run filesystem isolation, and stricter CPU accounting.
5. Add multi-worker load testing and explicit pending reclaim scheduling.

## 可继续深入的方向

读者可以继续深入这些主题：

- Judge queue：Redis Streams、ack、retry、dead-letter、pending reclaim。
- Docker sandbox：容器限制、非 root、网络隔离、输出截断和后续 seccomp 加固。
- AI safety：隐藏用例隔离、prompt 输入边界、管理员出题/导入工作流。
- Frontend architecture：工作台状态、WebSocket + polling、重组件懒加载。
