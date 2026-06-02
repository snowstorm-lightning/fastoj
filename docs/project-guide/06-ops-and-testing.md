# 06. 运行、测试、部署与排障

这篇文档回答“我怎么把项目跑起来、怎么验证它没坏、线上怎么部署、常见问题怎么定位”。详细命令以根目录 [README.zh-CN.md](../../README.zh-CN.md) 和 [docs/DEPLOYMENT.md](../DEPLOYMENT.md) 为准，这里强调理解和排障思路。

## 本地运行方式

推荐完整体验使用 Docker Compose：

```bash
cp .env.example .env
docker compose up --build
```

服务拓扑来自 [docker-compose.yml:1](../../docker-compose.yml#L1)。API 默认通过 Compose 设置 `JUDGE_ASYNC=true`，并连接 Compose 内的 PostgreSQL 和 Redis，看 [docker-compose.yml:43](../../docker-compose.yml#L43)。

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
- Worker heartbeat 是否存在。相关代码在 [backend/services/queue_service.py:36](../../backend/services/queue_service.py#L36)。
- 生产环境如果没有 heartbeat 会返回 `503 Judge service unavailable`；只有 `DEBUG=true` 或 `JUDGE_INLINE_FALLBACK=true` 才允许 inline fallback。相关代码在 [backend/services/submission_service.py:132](../../backend/services/submission_service.py#L137)。

### WebSocket 没有实时进度

先看最终结果是否能通过轮询出现。如果最终结果正常，说明判题链路没坏，问题可能在 WebSocket 或 Redis pub/sub relay。

检查：

- API startup 是否创建 relay task：[backend/main.py:115](../../backend/main.py#L115)
- relay 是否订阅状态 channel：[backend/api/websocket/status_relay.py:13](../../backend/api/websocket/status_relay.py#L13)
- 前端是否调用 `makeJudgeSocket`：[frontend/src/lib/api.ts:564](../../frontend/src/lib/api.ts#L564)

### Docker judge 不可用

检查：

- `judge-runtime` 镜像是否构建成功。
- API/Worker 容器是否挂载 `/var/run/docker.sock`。
- `JUDGE_CONTAINER_IMAGE` 是否等于当前 judge image。
- `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION` 是否保持关闭。生产不要依赖 host subprocess。

Docker 执行入口在 [backend/sandbox/executor.py:118](../../backend/sandbox/executor.py#L118)。

### AI 模型不可用

核心 OJ 不依赖 AI。AI profile 不可用时，普通用户模型列表会过滤不可用 profile，AI 调用返回正常 503，不影响题库和判题。

检查：

- `/api/v1/ai/profiles`
- AI provider 配置是否存在。
- 本地 Qwen 服务是否监听在容器可访问的地址。

### 前端 build 很大

当前 Monaco 和 Shiki 直接进入前端 bundle，README 和 handoff 已记录 bundle size 偏大。后续可以用 lazy loading 和路由级拆分优化。

## 代码导航

- 配置类：[backend/core/config.py:5](../../backend/core/config.py#L5)
- Compose 拓扑：[docker-compose.yml:1](../../docker-compose.yml#L1)
- API health：[backend/main.py:104](../../backend/main.py#L104)
- API startup tasks：[backend/main.py:110](../../backend/main.py#L110)
- Queue heartbeat：[backend/services/queue_service.py:36](../../backend/services/queue_service.py#L36)
- Inline fallback：[backend/services/submission_service.py:138](../../backend/services/submission_service.py#L138)
- Docker sandbox：[backend/sandbox/executor.py:118](../../backend/sandbox/executor.py#L118)
- 部署文档：[docs/DEPLOYMENT.md](../DEPLOYMENT.md)
- 验收手册：[docs/ACCEPTANCE_HARNESS.md](../ACCEPTANCE_HARNESS.md)

## 面试讲法

运维和测试可以这样讲：

For confidence, I split verification into unit-level backend tests, frontend component/schema tests, build checks, and Docker-level smoke tests. The most critical path is the real judge workflow, because it crosses API, Redis, Worker, Docker, database writes, WebSocket events, and frontend rendering. I also documented a manual acceptance harness for browser scenarios and hidden-test safety checks.
