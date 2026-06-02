# 01. 项目整体架构

FastOJ 是一个面向面试训练的 AI 辅助在线评测平台。它不是只在浏览器里跑代码的演示项目，而是包含题库、用户、提交、判题队列、Docker 沙箱、实时状态、AI 辅助解释、管理后台和部署流程的一套完整 OJ 系统。

## 一句话讲清楚

FastOJ uses a FastAPI backend, PostgreSQL persistence, Redis Streams based judge queue, Docker sandboxed code execution, and a React/Vite frontend to provide a LeetCode-like practice workflow with AI assistance that does not expose hidden tests.

中文表达：

FastOJ 用 FastAPI 提供 API，PostgreSQL 保存题目和提交，Redis Streams 解耦异步判题，Worker 通过 Docker 沙箱执行用户代码，React 前端提供题库和工作台，AI 只基于公开样例和聚合判题结果做解释。

## 运行时组件

![FastOJ 总体运行架构](assets/architecture.svg)

## 后端分层

后端目录不是随意堆代码，而是按职责分层：

- `backend/api/`：HTTP 和 WebSocket 路由，只做鉴权、参数接收、状态码和响应模型。
- `backend/services/`：业务逻辑，比如提交、题目、队列、Function mode 包装、出题 Agent。
- `backend/worker/`：异步判题进程，消费 Redis Streams 任务。
- `backend/sandbox/`：Docker 沙箱和语言运行命令。
- `backend/models/`：SQLAlchemy 表模型。
- `backend/schemas/`：Pydantic 请求/响应结构。
- `backend/ai/`：AI provider、prompt、响应 schema 和安全上下文构造。
- `backend/core/`：配置、数据库、安全、语言枚举等基础设施。

FastAPI 应用入口在 [backend/main.py:37](../../backend/main.py#L37)。路由统一挂载在 `/api/v1` 下，WebSocket 单独挂载在 `/ws/judge/{submission_id}`。看 [backend/main.py:91](../../backend/main.py#L91) 可以快速知道后端暴露了哪些模块。

## 前端分层

前端是 Vite + React + TypeScript，主入口集中在 [frontend/src/main.tsx:3633](../../frontend/src/main.tsx#L3633)。当前项目选择单入口文件组织主要视图：

- 题库页：搜索、筛选、卡片/列表布局。
- 工作台：题面、代码编辑器、公开运行输入、结果面板、判题时间线、AI Copilot。
- 训练图谱：React Flow 知识点图。
- 认证和设置页：登录注册、语言/主题/资料。
- 管理后台：用户、题目、用例、官方解法、AI 出题草稿。

公共 API client 在 [frontend/src/lib/api.ts:325](../../frontend/src/lib/api.ts#L325)，题目模式和 starter code 在 [frontend/src/lib/problemModes.ts:680](../../frontend/src/lib/problemModes.ts#L680)，前端 locale registry、本地化文案和搜索在 [frontend/src/lib/i18n.ts:4](../../frontend/src/lib/i18n.ts#L4)。后端也有对应的 locale registry 和请求校验，见 [backend/core/locales.py:5](../../backend/core/locales.py#L5)。

## Docker Compose 拓扑

本地完整环境由 `docker-compose.yml` 管理：

- `postgres`：PostgreSQL 14，保存持久业务数据。
- `redis`：Redis 7，保存 judge stream、dead-letter stream、pub/sub 状态消息。
- `api`：FastAPI + 静态前端 dist，连接 DB、Redis、Docker socket。
- `worker`：消费 Redis judge stream，执行判题。
- `judge-runtime`：构建 `fastoj-judge:latest` 镜像，提供多语言运行环境。

Compose 里 API 设置 `JUDGE_ASYNC=true`，表示提交优先进入 Redis 异步队列。对应代码配置在 [backend/core/config.py:33](../../backend/core/config.py#L33)，Compose 环境变量在 [docker-compose.yml:46](../../docker-compose.yml#L46)。

## 请求如何进入系统

常规 HTTP 请求流程：

- React UI 发起 `GET /api/v1/problems`。
- FastAPI route 接收请求并创建 service。
- Service layer 通过 SQLAlchemy 查询 PostgreSQL。
- Service 把 ORM 数据转换成 Pydantic 响应数据。
- FastAPI 返回 JSON 给前端，前端由 TanStack Query 缓存和渲染。

提交请求会更复杂，因为它还会经过 Redis、Worker、Docker 和 WebSocket。这个核心链路在 [02-judge-pipeline.md](02-judge-pipeline.md) 单独讲。

## 关键设计取舍

1. **异步判题**：判题可能慢，不能阻塞 API 进程。Redis Streams 提供 consumer group、ack、pending reclaim 和 dead-letter 的基础能力。
2. **Docker 沙箱**：用户代码不可信。生产路径使用 Docker SDK 创建受限容器，禁网、限制内存、限制进程数、丢弃 capabilities。
3. **双模式题目**：Function mode 更像 LeetCode，ACM mode 更像传统 OJ。后端统一把它们转成可执行的 stdin/stdout 程序再判题。
4. **WebSocket-first + polling fallback**：实时体验用 WebSocket；如果事件丢失，前端轮询提交详情补齐最终状态。
5. **AI 安全上下文**：AI 只看到公开样例、用户代码、公开用例结果和隐藏失败的摘要，不看到隐藏输入、期望输出、实际输出。
6. **Locale registry**：前端不再用 `locale === "zh"` 这类二分判断扩展语言，而是从 `LOCALE_META`、`SUPPORTED_LOCALES`、`localeText`、`localeValue` 和后端 `validate_locale` 集中派生行为。

## 代码导航

- FastAPI app 初始化：[backend/main.py:37](../../backend/main.py#L37)
- 路由挂载：[backend/main.py:91](../../backend/main.py#L91)
- 启动 Redis 状态 relay：[backend/main.py:110](../../backend/main.py#L110)
- 配置入口：[backend/core/config.py:5](../../backend/core/config.py#L5)
- Compose 服务定义：[docker-compose.yml:1](../../docker-compose.yml#L1)
- 前端 App 入口：[frontend/src/main.tsx:3633](../../frontend/src/main.tsx#L3633)
- 前端 API client：[frontend/src/lib/api.ts:325](../../frontend/src/lib/api.ts#L325)
- 前端 locale registry：[frontend/src/lib/i18n.ts:4](../../frontend/src/lib/i18n.ts#L4)
- 后端 locale registry：[backend/core/locales.py:5](../../backend/core/locales.py#L5)

## 面试讲法

当别人问“架构是什么”时，不要只列技术栈。建议按这个顺序回答：

1. 用户在 React 工作台写代码并点击 Run 或 Submit。
2. FastAPI 鉴权后创建 Submission 记录。
3. 如果异步判题可用，API 把任务写入 Redis Streams。
4. Worker 使用 consumer group 取任务，通过 Docker SDK 创建沙箱容器运行代码。
5. 判题结果写回 PostgreSQL，同时通过 Redis Pub/Sub 发进度。
6. API relay 把状态推到 WebSocket；前端也保留 polling fallback。
7. AI 功能只读取安全过滤后的提交上下文。
