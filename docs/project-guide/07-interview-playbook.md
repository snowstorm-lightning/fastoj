# 07. Google 20 分钟项目通话速查

这篇是为 20 分钟电话准备的。目标不是把所有技术细节讲完，而是让对方快速感到：你真的做过这个项目，知道架构、取舍、安全边界、测试和后续改进。

## 20 分钟建议节奏

| 时间 | 你要做什么 |
| --- | --- |
| 0-2 分钟 | 60 秒项目介绍，再补一句你负责/实现的核心部分。 |
| 2-6 分钟 | 讲整体架构：React、FastAPI、PostgreSQL、Redis Streams、Worker、Docker judge、AI provider。 |
| 6-11 分钟 | 深讲判题链路：Run/Submit、SubmissionService、QueueService、Worker、Sandbox、WebSocket。 |
| 11-15 分钟 | 深讲一个亮点：隐藏用例隔离或 Function mode 包装。 |
| 15-18 分钟 | 讲测试、部署和可靠性。 |
| 18-20 分钟 | 讲你会怎么继续改进，并反问对方下一步流程或关注点。 |

## 60 秒英文项目介绍

FastOJ is an AI-assisted online judge for interview practice. It provides a LeetCode-like workflow with a React and TypeScript frontend, a FastAPI backend, PostgreSQL persistence, Redis Streams for asynchronous judging, and Docker-based sandbox execution for untrusted user code. The core flow is that a user submits code from the workbench, the API creates a submission, pushes a judge task to Redis, a worker consumes it, runs the code in a restricted Docker container, stores testcase results, and streams progress back through WebSocket with polling as a fallback. I also added AI features for hints, explanations, code review, and problem authoring, with a strong safety boundary: hidden testcase inputs, expected outputs, and actual outputs are never sent to users or AI providers.

## 中文版本

FastOJ 是一个面向面试训练的 AI 辅助在线评测平台。前端用 React 和 TypeScript，后端用 FastAPI，数据存在 PostgreSQL，判题任务通过 Redis Streams 异步分发，Worker 用 Docker 沙箱执行不可信用户代码。用户在工作台提交代码后，API 创建提交记录并入队，Worker 消费任务、运行测试用例、写入结果，再通过 Redis Pub/Sub 和 WebSocket 把进度推回前端，同时前端保留 polling fallback。AI 部分支持提示、解释、代码审查和管理员出题，但隐藏用例内容不会进入 UI、日志或 AI prompt。

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
- Admin-only problem authoring workflow

## 最可能被问的问题和回答要点

### 1. Why did you use Redis Streams for judging?

I needed more than fire-and-forget queueing. Redis Streams gives message ids, consumer groups, ack, pending messages, and a path for reclaiming or dead-lettering failed work. That fits judge workers because tasks can be slow, workers can crash, and multiple workers should be able to consume from the same stream safely.

代码锚点：[QueueService.push_task](../../backend/services/queue_service.py#L56)、[QueueService.pop_stream_task](../../backend/services/queue_service.py#L74)、[retry_or_dead_letter](../../backend/services/queue_service.py#L95)。

### 2. How do you execute untrusted user code safely?

Production execution is Docker-first. The executor creates a temporary container from the judge runtime image, copies source and input through the Docker archive API, disables networking, limits memory and process count, drops Linux capabilities, enables no-new-privileges, and runs as a non-root user. Unsafe host subprocess execution is disabled unless explicitly configured for local experiments.

代码锚点：[Docker sandbox](../../backend/sandbox/executor.py#L118)、[network disabled](../../backend/sandbox/executor.py#L146)、[cap drop](../../backend/sandbox/executor.py#L148)。

### 3. How do you prevent hidden test leakage?

There are multiple layers. The judge does not store hidden input, expected output, or actual output in testcase result rows. The submission API filters hidden results for normal users. The AI service builds context only from public testcase results and uses a hidden failure notice instead of hidden data. WebSocket progress for full submissions also avoids exposing hidden case details.

代码锚点：[JudgeTask hidden result write](../../backend/worker/tasks/judge_task.py#L216)、[submission API filter](../../backend/api/submissions/__init__.py#L83)、[AI context](../../backend/ai/service.py#L112)。

### 4. How does Function mode work?

Function mode is a transformation layer. The user writes a function, but before judging the backend wraps it in a generated stdin/stdout harness based on the problem signature. The harness parses JSON-line input, calls the function, formats the return value, and then the same Docker judge pipeline can execute it like a normal program.

代码锚点：[SubmissionService._prepare_judge_code](../../backend/services/submission_service.py#L110)、[wrap_function_submission](../../backend/services/function_mode.py#L2468)、[frontend starter generation](../../frontend/src/lib/problemModes.ts#L712)。

### 5. What happens if the worker is down?

The API checks for a live worker heartbeat before pushing an async judge task. In debug/development mode, inline fallback can be used for local troubleshooting. In production, inline fallback is disabled, so Redis or worker unavailability returns `503 Judge service unavailable` instead of moving judge load into the FastAPI process. Workers refresh heartbeat in the background while long judge tasks are running. Each task runs in a child process supervised by the worker parent; if the child hangs, the parent terminates it and retries or dead-letters the stream message. If the parent crashes, its heartbeat expires and pending reclaim can move the unacked message to another worker.

代码锚点：[worker heartbeat](../../backend/services/queue_service.py#L36)、[has_live_worker](../../backend/services/queue_service.py#L50)、[worker parent](../../backend/worker/judge_worker.py)、[dispatch policy](../../backend/services/submission_service.py#L137)。

### 6. How does the frontend get real-time status?

After a submission is created, the workbench opens a WebSocket for that submission and also starts polling the submission detail endpoint. WebSocket gives real-time progress; polling guarantees the final state still appears if the socket misses a result event.

代码锚点：[judge action](../../frontend/src/main.tsx#L1675)、[connectStatus](../../frontend/src/main.tsx#L1716)、[makeJudgeSocket](../../frontend/src/lib/api.ts#L564)。

### 7. How did you test it?

I used backend unit tests for queue semantics, submission fallback, worker behavior, sandbox execution, Function mode wrapping, AI safety, and auth. On the frontend, tests cover API error formatting, schemas, i18n, problem mode helpers, and major UI panels. For integration confidence, the project has Docker Compose smoke checks and a manual browser acceptance harness that specifically checks hidden-test safety.

参考：[tests](../../tests)、[acceptance harness](../ACCEPTANCE_HARNESS.md)。

## 可以主动强调的项目亮点

- **Real judge pipeline**：不是浏览器模拟，不是直接 host subprocess。
- **Reliability-aware queue**：Redis Streams、ack、retry、dead-letter、pending reclaim。
- **Security boundary**：隐藏用例不进入普通 API、WebSocket、AI prompt。
- **Mode abstraction**：Function mode 和 ACM mode 共用同一条判题管线。
- **AI with constraints**：AI 辅助解释和出题，但 prompt 上下文被明确限制。
- **Extensible i18n**：前端 locale registry 和后端 dynamic locale validator 支持长期扩展，不把语言逻辑写成 `zh/en` 二分。
- **Deployment-ready shape**：Docker Compose、本地/生产配置、GitHub Actions、部署文档。

## 如果被问到 tradeoff

### 为什么没有一开始就用 Kubernetes？

For this project size, Docker Compose is enough to make the full topology reproducible: API, worker, database, Redis, and judge runtime. The design still separates API and worker, so moving to Kubernetes later would mostly be an operational migration rather than a rewrite of the judge flow.

### 为什么前端很多逻辑集中在 `main.tsx`？

The current frontend prioritized product completeness and fast iteration. The state boundaries are already visible: API client, i18n, problem mode helpers, editor, run result panel, AI panel, graph, and store are separate. A future refactor would split view components into route-level modules without changing backend contracts.

### 如何扩展第三种语言？

I would add the locale metadata and fallback labels in the frontend registry, add backend locale metadata and validation in one place, then fill UI copy incrementally through `localeText`/`localeValue` fallback helpers. That avoids scattering binary language checks across components and keeps API validation tied to the supported locale list.

代码锚点：[frontend LOCALE_META](../../frontend/src/lib/i18n.ts#L4)、[backend locale validator](../../backend/core/locales.py#L30)、[App lang sync](../../frontend/src/main.tsx#L3647)。

### 为什么 AI 不直接生成最终答案？

The product goal is training, not answer dumping. AI is constrained to hints, explanation, review, and safe conversation. It should help the learner debug and reason while preserving the integrity of hidden tests and the learning experience.

## 你可以说的改进计划

1. Add automated Playwright e2e coverage for auth, library search, run/submit, WebSocket fallback, AI stale-state cleanup, and admin workflows.
2. Add queue observability: worker heartbeat dashboard, pending count, dead-letter count, average judge latency, and per-language failure rate.
3. Split the frontend workbench into smaller route-level modules and lazy-load Monaco/Shiki to reduce bundle size.
4. Improve sandbox isolation further with stronger seccomp profiles, per-run filesystem isolation, and stricter CPU accounting.
5. Add multi-worker load testing and explicit pending reclaim scheduling.

## 最后反问

可以用简短英文结尾：

I can go deeper into the judge queue, the Docker sandbox, or the AI safety design. Which part would be most useful for you to hear more about?

如果是 recruiter 电话，也可以问：

What areas will the next interview focus on: backend systems, frontend product work, distributed systems, or coding fundamentals?
