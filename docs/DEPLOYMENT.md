# FastOJ CI/CD 部署流程

目标：本机和服务器尽量使用同一套 Docker Compose 拓扑。GitHub Actions
负责 build 镜像，服务器只负责 pull 镜像和重启容器。

## 环境文件

运行时只使用 `.env` 这个文件名。

- 本机：在仓库根目录把 `.env.example` 复制成 `.env`。
- 服务器：把 `.env.prod.example` 复制到 `/opt/projects/fastoj/.env`，再填真实生产值。
- 不要提交 `.env`；仓库已经忽略 `.env` 和 `.env.*`。
- 常规“本机 + 一台服务器”流程不需要 `.env.dev`。只有你需要在同一台机器上频繁切换多套本地环境时，才考虑额外的 `.env.dev`。

## 本机运行

```bash
cp .env.example .env
docker compose up --build
```

打开：

```text
http://127.0.0.1:8010
```

导入题库并创建第一个管理员：

```bash
docker compose exec api uv run python -m backend.scripts.seed_data
docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

如果你要在宿主机直接跑后端，只保留 PostgreSQL 和 Redis 在 Compose 里运行：

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

## GitHub Actions

仓库现在有两个 workflow：

- `.github/workflows/ci.yml`：包含代码或配置变更的 PR 和 `master` 推送时运行后端 lint/test、前端 build/test；纯文档变更（`*.md`、`docs/**`、`specs/**`）会被忽略。
- `.github/workflows/deploy.yml`：包含代码或配置变更的 `master` 推送，或手动运行 workflow 时，构建 `api`、`worker` 业务镜像并推送到配置的镜像仓库；`judge` 运行时镜像使用稳定 tag，只在镜像不存在、`Dockerfile.judge` 变更或手动要求时构建。随后 workflow 会 SSH 到服务器，上传生产 Compose 文件，只拉取业务镜像并重启服务。纯文档 `master` 推送不会触发部署。

需要在 GitHub 仓库 Settings -> Secrets and variables -> Actions 里配置：

```text
DEPLOY_HOST              # 服务器公网 IP 或域名
DEPLOY_SSH_PRIVATE_KEY   # 可以以 ubuntu 用户登录服务器的私钥
REGISTRY_USERNAME        # 镜像仓库登录用户名
REGISTRY_PASSWORD        # 镜像仓库登录密码或访问凭据
```

可选 secrets：

```text
DEPLOY_PORT              # SSH 端口，默认 22
```

可选 repository variable：

```text
DEPLOY_PATH              # 默认 /opt/projects/fastoj
CONTAINER_REGISTRY       # 默认 ccr.ccs.tencentyun.com
REGISTRY_NAMESPACE       # 镜像仓库命名空间；默认使用小写 GitHub owner
FASTOJ_JUDGE_IMAGE_TAG    # 默认 py311-node24-torch271
```

镜像仓库命名空间建议显式配置。默认值只适合 GitHub owner
刚好等于镜像仓库 namespace 的情况。`FASTOJ_JUDGE_IMAGE_TAG` 是稳定运行时 tag，只有
Python/Node/JDK/Go/NumPy/PyTorch 等判题运行环境变化时才需要调整或在手动运行
workflow 时勾选 `build_judge`。

## 服务器准备

SSH 到服务器：

```bash
ssh ubuntu@YOUR_SERVER_IP
```

安装 Docker Engine 和 Docker Compose plugin，然后创建部署目录：

```bash
sudo mkdir -p /opt/projects/fastoj
sudo chown ubuntu:ubuntu /opt/projects/fastoj
cd /opt/projects/fastoj
```

在服务器上创建 `/opt/projects/fastoj/.env`，可以参考 `.env.prod.example`。至少要改：

```text
FASTOJ_IMAGE_REGISTRY=ccr.ccs.tencentyun.com
FASTOJ_IMAGE_OWNER=你的镜像仓库命名空间，必须小写
FASTOJ_IMAGE_TAG=latest
FASTOJ_JUDGE_IMAGE_TAG=py311-node24-torch271
POSTGRES_PASSWORD=足够长的随机数据库密码
SECRET_KEY=足够长的随机应用密钥
CORS_ORIGINS=["https://你的域名"]
JUDGE_INLINE_FALLBACK=false
```

生产环境应保持 `FASTOJ_DEBUG=false` 和 `JUDGE_INLINE_FALLBACK=false`。Redis 或
Judge Worker 不可用时提交接口会返回 `503 Judge service unavailable`，而不是在
API 容器内执行用户提交。

Worker 默认开启 parent/child 判题监督：

```text
JUDGE_CHILD_PROCESS_ENABLED=true
JUDGE_TASK_HARD_TIMEOUT_SECONDS=120
JUDGE_CHILD_TERMINATE_GRACE_SECONDS=3
JUDGE_ACTIVE_TASK_TTL_SECONDS=180
```

`JUDGE_TASK_HARD_TIMEOUT_SECONDS` 是整次 submission 的 parent 级兜底时间，不是
单个 testcase 的 time limit。题目用例很多或单题时间限制较高时，应在生产 `.env`
中调大这个值，并让 `JUDGE_ACTIVE_TASK_TTL_SECONDS` 大于 hard timeout 或至少覆盖
最长的无进度阶段。Worker 服务在 Compose 中使用 `restart: unless-stopped`，
healthcheck 只验证应用配置可 import 且 Redis 可 ping，不会执行判题。

在服务器生成随机密钥：

```bash
openssl rand -hex 32
```

第一次部署可以推送到 `master`，或者在 GitHub Actions 页面手动运行
`Build and Deploy`。如果镜像仓库中还没有稳定 judge 镜像，workflow 会自动构建；如果你
只是想强制重建 judge 运行时，可以手动运行 workflow 并勾选 `build_judge`。
workflow 会上传生产 Compose 文件并启动容器。

首次部署完成后，初始化应用数据：

```bash
cd /opt/projects/fastoj
docker compose exec api uv run python -m backend.scripts.seed_data
docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

## 网络和 HTTPS

推荐生产结构：

- `.env` 里保持 `FASTOJ_BIND=127.0.0.1`、`FASTOJ_PORT=8010`。
- 在服务器上用 Nginx 或 Caddy 做 HTTPS 反向代理。
- 服务器防火墙或安全组只开放 `80`、`443` 和 SSH 端口。

Caddy 示例：

```text
fastoj.example.com {
  reverse_proxy 127.0.0.1:8010
}
```

如果暂时不用反向代理，把 `FASTOJ_BIND=0.0.0.0`，保留 `FASTOJ_PORT=8010`，并在
服务器防火墙或安全组开放 `8010`。这适合临时验证，不建议作为正式公网部署。

## 日常运维

查看状态：

```bash
cd /opt/projects/fastoj
docker compose ps
docker compose logs --tail=100 api worker
```

如果提交长时间停在 judging，可以检查 worker 的 active task marker：

```bash
docker compose exec redis sh -lc 'for key in $(redis-cli --scan --pattern "judge:worker:active-task:*"); do echo "$key"; redis-cli GET "$key"; done'
```

marker 的 JSON 里有 `submission_id`、`message_id`、`last_progress_at` 和
`deadline_at`。如果 worker parent 终止或 kill 了 judge child，child 内部的 Docker
executor `finally` 可能来不及清理容器；生产排障时也要检查是否有残留
`fastoj_judge_*` 容器。如果 worker parent 崩溃，heartbeat 会过期，pending message
会由其他 worker 的 reclaim 流程接管。

手动按当前 `.env` 镜像标签重启：

```bash
cd /opt/projects/fastoj
docker compose pull api worker
docker compose up -d --remove-orphans api worker
```

只有判题运行时发生变化时，才需要拉取并重启 `judge-runtime`：

```bash
cd /opt/projects/fastoj
docker compose pull judge-runtime
docker compose up -d judge-runtime api worker
```

备份 PostgreSQL：

```bash
cd /opt/projects/fastoj
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > fastoj-backup.sql
```
