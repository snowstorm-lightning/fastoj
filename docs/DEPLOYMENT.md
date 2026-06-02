# FastOJ CI/CD 部署流程

目标：本机和腾讯云服务器尽量使用同一套 Docker Compose 拓扑。GitHub Actions
负责 build 镜像，服务器只负责 pull 镜像和重启容器。

## 环境文件

运行时只使用 `.env` 这个文件名。

- 本机：在仓库根目录把 `.env.example` 复制成 `.env`。
- 腾讯云服务器：把 `.env.prod.example` 复制到 `/opt/projects/fastoj/.env`，再填真实生产值。
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

- `.github/workflows/ci.yml`：PR 和 `master` 推送时运行后端 lint/test、前端 build/test。
- `.github/workflows/deploy.yml`：构建 `api`、`worker`、`judge` 三个镜像，推送到 GitHub Container Registry，然后 SSH 到腾讯云服务器，上传生产 Compose 文件、拉取镜像并重启服务。

需要在 GitHub 仓库 Settings -> Secrets and variables -> Actions 里配置：

```text
TENCENT_HOST              # 腾讯云服务器公网 IP 或域名
TENCENT_SSH_PRIVATE_KEY   # 可以以 ubuntu 用户登录服务器的私钥
```

可选 secrets：

```text
TENCENT_PORT              # SSH 端口，默认 22
GHCR_READ_USER            # 拉取私有 GHCR 镜像用的用户名
GHCR_READ_TOKEN           # 拉取私有 GHCR 镜像用的 token，需要 read:packages 权限
```

可选 repository variable：

```text
TENCENT_DEPLOY_PATH       # 默认 /opt/projects/fastoj
```

如果 GHCR package 是公开的，或者服务器已经 `docker login ghcr.io`，可以不设置
`GHCR_READ_TOKEN`。如果 GHCR package 是私有的，需要创建一个有 `read:packages`
权限的 GitHub token，保存为 `GHCR_READ_TOKEN`。

## 腾讯云服务器准备

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
FASTOJ_IMAGE_OWNER=你的 GitHub 用户名或组织名，必须小写
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
`Build and Deploy`。workflow 会上传生产 Compose 文件并启动容器。

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
- 腾讯云安全组只开放 `80`、`443` 和 SSH 端口。

Caddy 示例：

```text
fastoj.example.com {
  reverse_proxy 127.0.0.1:8010
}
```

如果暂时不用反向代理，把 `FASTOJ_BIND=0.0.0.0`，保留 `FASTOJ_PORT=8010`，并在
腾讯云安全组开放 `8010`。这适合临时验证，不建议作为正式公网部署。

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
docker compose pull
docker compose up -d --remove-orphans
```

备份 PostgreSQL：

```bash
cd /opt/projects/fastoj
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > fastoj-backup.sql
```
