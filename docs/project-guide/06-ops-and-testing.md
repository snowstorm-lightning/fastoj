# 06. 运行、测试、部署与排障

这篇文档回答“我怎么把项目跑起来、怎么验证它没坏、线上怎么部署、常见问题怎么定位”。详细命令以根目录 [README.zh-CN.md](../../README.zh-CN.md) 和 [docs/DEPLOYMENT.md](../DEPLOYMENT.md) 为准，这里强调理解和排障思路。

## 本地运行方式

推荐完整体验使用 Docker Compose：

```bash
cp .env.example .env
docker compose up --build
```

服务拓扑来自 [docker-compose.yml:1](../../docker-compose.yml#L1)。API 默认通过 Compose 设置 `JUDGE_ASYNC=true`，并连接 Compose 内的 PostgreSQL 和 Redis，看 [docker-compose.yml:46](../../docker-compose.yml#L46)。

如果只做后端开发，也可以只启动基础服务，再在宿主机跑 FastAPI：

```bash
docker compose up -d postgres redis
uv sync --extra dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

前端本地开发：

```bash
cd frontend
npm ci
npm run dev
```

## 配置来源

配置类在 [backend/core/config.py:5](../../backend/core/config.py#L5)。它从 `.env` 读取：

- `DATABASE_URL`
- `REDIS_URL`
- JWT secret 和过期时间
- Judge Docker 配置
- Redis Stream 配置
- Worker child-process watchdog 配置：`JUDGE_CHILD_PROCESS_ENABLED`、`JUDGE_TASK_HARD_TIMEOUT_SECONDS`、`JUDGE_CHILD_TERMINATE_GRACE_SECONDS`、`JUDGE_ACTIVE_TASK_TTL_SECONDS`
- AI provider 配置

不要把真实 `.env`、API key、JWT 或生产数据库密码写进文档、日志或截图。

## 数据库迁移

Alembic 配置在 `backend/alembic.ini` 和 `backend/alembic/`。本地开发常用：

```bash
uv run alembic -c backend/alembic.ini upgrade head
```

Docker API 启动也有迁移/初始化相关脚本。已有数据库如果没有 `alembic_version`，项目提供了 `backend/scripts/migrate_or_stamp.py` 做安全 stamp。

## 测试矩阵

按照仓库约定，较大变更交付前要跑：

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

如果改了 Docker、Worker、WebSocket、沙箱或真实提交流程，还要跑：

```bash
docker compose up --build -d api worker
docker compose ps
```

验收手册在 [docs/ACCEPTANCE_HARNESS.md](../ACCEPTANCE_HARNESS.md)。

## 测试覆盖怎么理解

后端 tests 重点覆盖：

- 队列语义：`tests/test_queue_streams.py`
- 提交服务生产拒绝、开发 fallback 和权限：`tests/test_submission_service.py`
- Worker 消费任务：`tests/test_judge_consumer.py`
- Worker parent/child watchdog：`tests/test_judge_worker.py`
- Docker 沙箱：`tests/test_sandbox_executor.py`
- Function mode 包装：`tests/test_function_mode.py`
- AI hidden-test safety：`tests/test_ai_service.py`
- WebSocket 鉴权：`tests/test_websocket_auth.py`

前端 tests 重点覆盖：

- API 错误格式化。
- schemas。
- i18n：locale registry、`lang` 映射、本地化搜索和 fallback helper。
- problemModes。
- AI panel 和 run result panel。
- TrainingGraph。

## 部署流程

生产部署文档在 [docs/DEPLOYMENT.md](../DEPLOYMENT.md)。当前思路：

1. GitHub Actions 跑 CI。
2. 构建 API、Worker、Judge 镜像。
3. 推送到 GHCR。
4. SSH 到 Tencent Cloud 服务器。
5. 上传生产 Compose 文件。
6. pull 镜像并重启容器。
7. 用 Nginx 或 Caddy 做 HTTPS 反向代理。

生产环境仍使用 `.env` 作为运行时配置文件，但真实 `.env` 不提交。

## 常见排障

### 提交一直 pending

优先检查：

- `docker compose ps` 看 worker 是否 running。
- Redis 是否 healthy。
- Worker 是否能连接 Docker socket。
- Worker heartbeat 是否存在。相关代码在 [backend/services/queue_service.py:44](../../backend/services/queue_service.py#L44)。
- Worker active task marker 是否长期不变。可以用 `docker compose exec redis sh -lc 'for key in $(redis-cli --scan --pattern "judge:worker:active-task:*"); do echo "$key"; redis-cli GET "$key"; done'` 查看，里面有 `submission_id`、`message_id`、`last_progress_at` 和 `deadline_at`。
- 生产环境如果没有 heartbeat 会返回 `503 Judge service unavailable`；只有 `DEBUG=true` 或 `JUDGE_INLINE_FALLBACK=true` 才允许 inline fallback。相关代码在 [backend/services/submission_service.py:136](../../backend/services/submission_service.py#L136)。

### 提交一直 judging

优先区分是 child 卡住还是 parent/worker 崩了：

- Child 卡住：parent 仍有 heartbeat，active task marker 会显示当前 submission。超过 `JUDGE_TASK_HARD_TIMEOUT_SECONDS` 后 parent 会 terminate/kill child，按 submission/message 标签清理残留 Docker judge 容器，并把任务 retry 或 dead-letter。
- Parent 崩溃：heartbeat 会消失，原 stream message 留在 pending；其他 worker 的 `claim_pending` 会在 owner heartbeat 失效后接管。
- Compose 层：worker 服务配置了 `restart: unless-stopped`；进程崩溃会由 Docker 重启。healthcheck 只验证配置可 import 且 Redis 可 ping，不执行判题，也不会替代业务层 watchdog。
- 残留容器：正常 Docker executor 路径会在 `finally` 里删除容器；如果 parent hard-kill child，child 可能来不及执行 `finally`。当前 parent 会清理当前 task 标签匹配的 `fastoj_judge_*` 容器，生产上仍建议监控残留容器数量。

### WebSocket 没有实时进度

先看最终结果是否能通过轮询出现。如果最终结果正常，说明判题链路没坏，问题可能在 WebSocket 或 Redis pub/sub relay。

检查：

- API startup 是否创建 relay task：[backend/main.py:116](../../backend/main.py#L116)
- relay 是否订阅状态 channel：[backend/api/websocket/status_relay.py:13](../../backend/api/websocket/status_relay.py#L13)
- 前端是否调用 `makeJudgeSocket`：[frontend/src/lib/api.ts:564](../../frontend/src/lib/api.ts#L564)

### Docker judge 不可用

检查：

- `judge-runtime` 镜像是否构建成功。
- API/Worker 容器是否挂载 `/var/run/docker.sock`。
- `JUDGE_CONTAINER_IMAGE` 是否等于当前 judge image。
- `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION` 是否保持关闭。生产不要依赖 host subprocess。

Docker 执行入口在 [backend/sandbox/executor.py:92](../../backend/sandbox/executor.py#L92)。

### AI 模型不可用

核心 OJ 不依赖 AI。AI profile 不可用时，普通用户模型列表会过滤不可用 profile，AI 调用返回正常 503，不影响题库和判题。

检查：

- `/api/v1/ai/profiles`
- AI provider 配置是否存在。
- 本地 Qwen 服务是否监听在容器可访问的地址。

### 前端 build 很大

当前首屏主入口已经做过组件级 code splitting：Monaco editor、Shiki 代码高亮、React Flow 图谱、xterm 判题时间线、AI 面板、运行结果、认证/设置页都会按需加载。`cd frontend && npm run build` 时如果仍看到 Vite 大 chunk 警告，先看具体 chunk 名：

- `index-*.js`：主入口。当前应约 499.81 kB；如果明显变大，说明又有重依赖被同步 import。
- `editor.api2-*.js`：Monaco editor lazy chunk，只有工作台编辑器加载时需要。
- `cpp-*.js`：Shiki C++ grammar lazy chunk，只有题解代码块按 C++ 高亮时需要。

不要直接调高 `chunkSizeWarningLimit` 来掩盖新的主入口膨胀；只有确认超限 chunk 都是已懒加载资产时，警告才是可接受的。

## 代码导航

- 配置类：[backend/core/config.py:5](../../backend/core/config.py#L5)
- Compose 拓扑：[docker-compose.yml:1](../../docker-compose.yml#L1)
- API health：[backend/main.py:104](../../backend/main.py#L104)
- API startup tasks：[backend/main.py:110](../../backend/main.py#L110)
- Queue heartbeat：[backend/services/queue_service.py:44](../../backend/services/queue_service.py#L44)
- Inline fallback：[backend/services/submission_service.py:136](../../backend/services/submission_service.py#L136)
- Docker sandbox：[backend/sandbox/executor.py:92](../../backend/sandbox/executor.py#L92)
- 部署文档：[docs/DEPLOYMENT.md](../DEPLOYMENT.md)
- 验收手册：[docs/ACCEPTANCE_HARNESS.md](../ACCEPTANCE_HARNESS.md)

## 面试讲法

运维和测试可以这样讲：

For confidence, I split verification into unit-level backend tests, frontend component/schema tests, build checks, and Docker-level smoke tests. The most critical path is the real judge workflow, because it crosses API, Redis, Worker, Docker, database writes, WebSocket events, and frontend rendering. I also documented a manual acceptance harness for browser scenarios and hidden-test safety checks.
