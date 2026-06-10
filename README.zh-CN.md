# FastOJ

[English](README.md) | 简体中文

在线体验：[fastoj.snowstormlightning.top](http://fastoj.snowstormlightning.top)

FastOJ 是一个面向面试训练的全栈 AI 辅助在线评测平台。它把类 LeetCode 的学习
体验和更接近生产系统的后端组合在一起：FastAPI、PostgreSQL、Redis Streams、
Docker 沙箱判题、React/Monaco 编程工作台、双语界面、管理后台出题流程，以及
严格隔离隐藏用例的 AI 反馈。

这个项目既可以直接作为本地可运行的刷题平台，也适合作为系统设计和 AI 产品工程
样例来研究：判题队列、沙箱执行、异步 Worker、AI Provider 路由、管理后台和
产品级前端交互都在同一个代码库里。

## 为什么有吸引力

- **真实判题链路。** 提交从 FastAPI 进入 Redis Streams，由带 parent/child
  监督的 Judge Worker 消费，最后进入受限 Docker 沙箱执行；生产环境不会用宿主机
  `subprocess` 跑不可信代码。
- **函数模式和 ACM 模式并重。** 学习者可以写带 starter frame 的函数题，也可以
  练传统 stdin/stdout；双模式草稿可以基于同一组逻辑 testcase 同步维护函数视图和
  ACM 视图。
- **AI 有用，但守住 OJ 边界。** 提示、失败解释、代码审查和对话只使用公开样例、
  判题结果、用户代码和安全聚合信息。隐藏用例输入、期望输出、实际输出不会给用户，
  也不会发送给模型服务商。
- **前端是完整产品界面。** React UI 包含题库搜索、卡片/列表布局、Monaco 编辑器、
  可调结果面板、输出 diff、判题时间线、AI Copilot、账号设置、共享讨论、React Flow
  训练图谱和完整管理后台。
- **管理后台覆盖真实内容运营。** 管理员可以生成原创草稿、导入外部题目材料、通过
  SSE 查看 Agent 执行路径、用沙箱校验官方解法、管理用户和权限、编辑完整用例集、
  重新校验草稿，并发布多语言官方题解。
- **AI Provider 可替换。** 后端使用 OpenAI-compatible profile，既能接 DeepSeek
  风格的托管 API，也能接本地 Qwen/llama.cpp `llama-server`。
- **具备部署形态。** 本地和生产都使用 Docker Compose；GitHub Actions 构建
  API/worker 镜像，推送到镜像仓库，服务器只拉镜像并重启服务。

## 技术栈一览

| 层级 | 技术 |
| --- | --- |
| 后端 API | Python 3.11+、FastAPI、Pydantic v2、SQLAlchemy 2.0、Alembic |
| 数据与队列 | PostgreSQL 14+、Redis Streams、Redis Pub/Sub |
| 判题运行时 | Python Docker SDK、Docker 沙箱容器、Worker watchdog、死信队列 |
| 前端 | React、TypeScript、Vite、Tailwind CSS、Monaco Editor、TanStack Query、Zustand、Zod |
| 富交互 UI | React Flow、Shiki、xterm、DOMPurify、marked、Pretext 文本测量 |
| AI 层 | OpenAI-compatible HTTP Provider、DeepSeek profiles、本地 Qwen/llama.cpp profile |
| 工具与 CI/CD | `uv`、`ruff`、`pytest`、`npm`、Vitest、Docker Compose、GitHub Actions、镜像仓库 |

## 产品体验

1. **双语和浅色/深色主题** - 顶部导航可以切换中文/英文和主题；登录用户的语言
   偏好保存到账户，访客使用浏览器语言和本地存储。题库、工作台、图谱、登录注册
   和管理后台都使用同一套主题系统。
2. **题库页** - 搜索、标签/难度筛选、卡片和传统 OJ 列表切换、推荐练习入口。
3. **编程工作台** - 阅读题面、在 Monaco 中写代码、编辑公开运行输入、对比官方
   期望输出和自己的输出、提交隐藏用例评测，并实时观察状态。错误答案会把判题反馈、
   diff、历史提交代码和 AI 后续分析放在同一个工作流里。
4. **AI Copilot** - 按当前界面语言请求渐进提示、失败解释、代码审查和上下文对话。
5. **训练图谱** - 使用 React Flow 浏览知识点节点，点击后回到题库并自动应用标签筛选。
6. **管理后台** - 在一个受保护工作区中管理题目、用例、用户、权限、AI 出题草稿、
   题目导入、Agent 运行路径、官方解法和草稿发布。

## 页面展示

页面支持浅色和深色两种主题，顶部导航即可切换；截图使用英文界面，产品右上角
可以切换中文，登录后语言偏好会保存到账户。

| 题库页 | 编程工作台 |
| --- | --- |
| ![FastOJ 题库页，包含筛选器、题目卡片、模式标签和通过率统计](docs/screenshots/library-en.png) | ![FastOJ 工作台，包含题面、Monaco 编辑器、可调整的代码和运行结果区域、可编辑运行输入、官方期望输出、输出差异和 AI Judge Copilot](docs/screenshots/workbench-en.png) |
| 可搜索的练习目录，支持浅色/深色主题、筛选、卡片/列表布局、模式标签和训练数据概览。 | 集中式刷题界面，把题面、starter frame、可调代码/结果区域、示例输入、官方期望输出、自己的输出、差异对比和 AI 判题助手放在同一视图中；错误代码运行后，助手会根据判题反馈给出定位和改进建议。 |

| 训练图谱 | 登录注册 |
| --- | --- |
| ![FastOJ 知识图谱，包含知识点卡片和进度统计](docs/screenshots/graph-en.png) | ![FastOJ 登录注册页，包含账号表单、确认密码、产品能力标签和认证弹窗](docs/screenshots/auth-en.png) |
| 基于 React Flow 的知识点地图，点击节点后回到题库并自动应用标签筛选。 | 独立登录/注册页，注册时确认密码，并用清晰弹窗反馈登录失败或注册成功。 |

| 管理后台 |
| --- |
| 管理员视图集中提供原创出题 Agent、导入题目草稿、执行路径查看、用户管理、题目与内容管理、正式用例管理和草稿审核。隐藏用例和导入原文只在管理员界面和管理员 API 中展示，不会进入普通用户题面、AI 解释或提交日志。 |

## 快速启动

Docker Compose 是最快的完整体验路径。

Linux/WSL 前置要求：

- Docker Engine 或开启 Linux containers 的 Docker Desktop。
- Python 3.11+ 和 `uv`，用于宿主机侧后端检查。
- Node.js `20.19+` 或 `22.12+`，以及 npm `10+`，用于前端构建。
- 在 WSL 中建议把仓库放在 Linux 文件系统中，例如 `~/projects`，不要放在
  `/mnt/c` 下，这样 bind mount 和依赖安装更快，也能保留 Linux 文件语义。

```bash
git clone https://github.com/snowstorm-lightning/fastoj.git
cd fastoj
cp .env.example .env
docker compose up --build
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

打开：

```text
http://127.0.0.1:8010
```

导入内置题库：

```bash
docker compose exec api uv run python -m backend.scripts.seed_data
```

从可信 shell 创建第一个管理员：

```bash
docker compose exec api uv run python -m backend.scripts.create_admin --username admin --email admin@example.com
```

管理员脚本会无回显地提示输入密码。无人值守的本地自动化场景可以在可信执行
环境里设置 `FASTOJ_ADMIN_PASSWORD`，不要把真实密码写进命令历史。

## 本地开发

如果你想直接跑后端和前端进程，可以使用下面的方式。请先确保 PostgreSQL 和
Redis 可用，或者保留 Compose 中的基础服务运行。
使用仓库内 Compose 文件时，宿主机工具通过 `5433` 端口访问 PostgreSQL；
从 `.env.example` 复制出的 `.env` 已经包含
`DATABASE_URL=postgresql://fastoj:fastoj_secret@localhost:5433/fastoj`。

直接在宿主机跑后端判题前，先构建一次 Docker judge runtime：

```bash
docker compose build judge-runtime
```

后端：

```bash
cp .env.example .env
docker compose up -d postgres redis
uv sync --extra dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm ci
npm run dev
```

直接在宿主机开发时 `.env.example` 使用 `DEBUG=true`，异步队列不可用时 API
可以 inline 判题，方便调试。Docker Compose 和生产环境使用 `JUDGE_ASYNC=true`
并关闭 `JUDGE_INLINE_FALLBACK`；Redis 或 Worker 不可用时会返回
`503 Judge service unavailable`，不会把提交判题负载转移到 API 进程。

Worker 默认会把每个队列判题任务放进独立 child process。Parent 负责 Redis
heartbeat、active-task 标记和 hard timeout；child 如果卡死，parent 会在
`JUDGE_TASK_HARD_TIMEOUT_SECONDS` 后终止它，并把原 stream message 重试或写入
dead-letter。

Vite 开发服务器默认可以调用同源 API。只有当前端和 API 分别跑在不同 origin
时，才需要设置 `VITE_API_BASE_URL`。

## AI 配置

AI 默认关闭，所以不配置模型服务或 API Key 也能使用核心 OJ 流程。

```bash
AI_PROVIDER=disabled
```

托管 OpenAI-compatible Provider 示例：

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your-provider-key
AI_MODEL=deepseek-v4-flash
```

页面内模型选择器使用的命名 profile：

```bash
AI_DEEPSEEK_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_API_KEY=your-provider-key
AI_DEEPSEEK_MODEL=deepseek-v4-flash

AI_DEEPSEEK_PRO_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_PRO_API_KEY=your-provider-key
AI_DEEPSEEK_PRO_MODEL=deepseek-v4-pro
AI_DEEPSEEK_PRO_TIMEOUT_SECONDS=120
AI_DEEPSEEK_PRO_MAX_OUTPUT_TOKENS=4000
AI_AUTHORING_REPAIR_ATTEMPTS=4

AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

直接调用 DeepSeek 官方 OpenAI-compatible API 时使用 `deepseek-v4-pro` 或
`deepseek-v4-flash`。

FastOJ 通过 `GET /api/v1/ai/profiles` 给前端模型选择器提供动态 profile
列表。后端启动后会用短超时在后台检查 profile 可用性，并缓存 60 秒；普通用户
只看到当前可用模型，管理员可以看到不可用模型和安全摘要原因。选择 `default`
时会自动按“默认配置、DeepSeek Pro、DeepSeek、本地 Qwen”的顺序路由到第一个
健康 profile。管理员出题 Agent 在 Pro 可用时默认选择 DeepSeek Pro，普通用户
AI 控件仍优先使用 `default`。真正调用 AI 时仍会再次兜底校验，因此模型临时
离线只会返回正常 503，不会影响 API 启动。

### 本地 Qwen 部署与启动

FastOJ 通过 llama.cpp 的 OpenAI-compatible `llama-server` 访问本地 Qwen。
当前测试过的 profile 使用官方
[Qwen/Qwen2.5-Coder-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)
模型、`Q4_K_M` 量化，以及本地模型 id
`qwen2.5-coder-7b-instruct-q4_k_m`。

FastOJ 仓库不内置模型文件或 `llama-server`。建议把它们放到仓库外，例如
Linux/WSL 下的 `$HOME/Models/qwen`，或 Windows 下的
`%USERPROFILE%\Models\qwen`，避免把大模型和运行二进制放进 git。

推荐的 Linux/WSL 本地目录结构：

```text
$HOME/Models/qwen/
  llama-server  # 使用全局安装的 llama.cpp 时可省略
  qwen2.5-coder-7b-instruct-q4_k_m.gguf
  start-qwen-llama-server.sh
```

推荐的 Windows 本地目录结构：

```text
%USERPROFILE%\Models\qwen\
  llama-server.exe  # 使用全局安装的 llama.cpp 时可省略
  qwen2.5-coder-7b-instruct-q4_k_m.gguf
  start-qwen-llama-server.ps1
  stop-qwen-llama-server.ps1
```

推荐的 Linux/WSL 安装方式：

```bash
mkdir -p "$HOME/Models/qwen"
python3 -m pip install -U huggingface_hub
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
  --include "qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --local-dir "$HOME/Models/qwen"
```

如果 `llama-server` 已全局安装，可以创建
`$HOME/Models/qwen/start-qwen-llama-server.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

root="$HOME/Models/qwen"
server="$root/llama-server"
if [ ! -x "$server" ]; then
  server="$(command -v llama-server)"
fi

exec "$server" \
  -m "$root/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --alias qwen2.5-coder-7b-instruct-q4_k_m \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -ngl 999
```

然后赋予执行权限：

```bash
chmod +x "$HOME/Models/qwen/start-qwen-llama-server.sh"
```

推荐的 Windows 安装方式：

1. 用 WinGet 安装 llama.cpp：

   ```powershell
   winget install llama.cpp
   llama-server --version
   ```

   如果提示找不到 `llama-server`，关闭并重新打开 PowerShell，让新的 `PATH`
   生效。

2. 创建模型目录：

   ```powershell
   New-Item -ItemType Directory -Force "$env:USERPROFILE\Models\qwen"
   ```

3. 安装 Hugging Face 下载工具：

   ```powershell
   py -m pip install -U huggingface_hub
   ```

4. 下载 Q4_K_M GGUF 文件：

   ```powershell
   huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF `
     --include "qwen2.5-coder-7b-instruct-q4_k_m.gguf" `
     --local-dir "$env:USERPROFILE\Models\qwen"
   ```

5. 如果用 WinGet 安装 llama.cpp，下面的启动脚本可以通过 `PATH` 找到它。
   如需查看实际解析到的路径，运行：

   ```powershell
   Get-Command llama-server
   ```

手动安装二进制的方式：

1. 打开 [llama.cpp releases 页面](https://github.com/ggml-org/llama.cpp/releases)。
2. 下载和机器匹配的最新 Windows asset：
   - CPU-only 或不确定 GPU 时，选 `Windows x64 (CPU)`。
   - NVIDIA GPU offload 选 `Windows x64 (CUDA 12/13)`，并下载同一版本匹配的
     `CUDA DLLs`。
   - Vulkan 可用的 GPU 可以选 `Windows x64 (Vulkan)`。
3. 把 zip 解压到 `%USERPROFILE%\Models\qwen`。
4. 确认 `%USERPROFILE%\Models\qwen\llama-server.exe` 存在。
5. 从 Qwen Hugging Face 模型页下载
   `qwen2.5-coder-7b-instruct-q4_k_m.gguf` 到同一目录。更推荐使用上面的
   `huggingface-cli download`，因为大文件下载失败后更容易续传。

源码构建方式，适合没有匹配二进制的机器：

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build
cmake --build build -j --target llama-server llama-cli
```

然后把构建出的 `llama-server` 复制到 Linux/WSL 的 `$HOME/Models/qwen`，或
Windows 的 `%USERPROFILE%\Models\qwen`，也可以让启动脚本指向构建输出路径。

`%USERPROFILE%\Models\qwen\start-qwen-llama-server.ps1` 示例：

```powershell
$root = "$env:USERPROFILE\Models\qwen"
$server = Join-Path $root "llama-server.exe"
if (-not (Test-Path $server)) {
  $server = (Get-Command llama-server -ErrorAction Stop).Source
}

& $server `
  -m "$root\qwen2.5-coder-7b-instruct-q4_k_m.gguf" `
  --alias qwen2.5-coder-7b-instruct-q4_k_m `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192 `
  -ngl 999
```

如果机器没有可用 GPU，可以移除或调低 `-ngl`。服务保持监听
`127.0.0.1:8080`；OpenAI-compatible API 地址是
`http://127.0.0.1:8080/v1`。

如果换用其他 GGUF 文件，需要保持 `--alias`、`AI_MODEL` 和
`AI_QWEN_MODEL` 一致。

快速替代方式：如果 `llama-server` 已经安装，且不需要固定本地 GGUF 文件路径，
也可以让 llama.cpp 直接从 Hugging Face 下载并启动：

```bash
llama-server \
  -hf Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M \
  --alias qwen2.5-coder-7b-instruct-q4_k_m \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -ngl 999
```

PowerShell 等价命令：

```powershell
llama-server `
  -hf Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M `
  --alias qwen2.5-coder-7b-instruct-q4_k_m `
  --host 127.0.0.1 `
  --port 8080 `
  -c 8192 `
  -ngl 999
```

启动 FastOJ 前先检查本地模型服务：

```bash
curl --noproxy '*' http://127.0.0.1:8080/v1/models
```

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8080/v1/models
```

更完整的 API 检查：

```bash
curl --noproxy '*' http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder-7b-instruct-q4_k_m",
    "messages": [{"role": "user", "content": "Say OK only."}],
    "max_tokens": 8
  }'
```

PowerShell：

```powershell
$body = @{
  model = "qwen2.5-coder-7b-instruct-q4_k_m"
  messages = @(@{ role = "user"; content = "Say OK only." })
  max_tokens = 8
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8080/v1/chat/completions `
  -ContentType "application/json" `
  -Body $body
```

Linux/WSL 日常启动需要两个 shell，因为 `llama-server` 会保持前台运行：

```bash
# Shell 1
"$HOME/Models/qwen/start-qwen-llama-server.sh"
```

```bash
# Shell 2
curl --noproxy '*' http://127.0.0.1:8080/v1/models
docker compose up
```

PowerShell 日常启动同样需要两个 shell：

```powershell
# Shell 1
& "$env:USERPROFILE\Models\qwen\start-qwen-llama-server.ps1"
```

```powershell
# Shell 2
Invoke-RestMethod http://127.0.0.1:8080/v1/models
docker compose up
```

如果希望 FastOJ 容器后台运行，先在 Shell 1 启动模型服务，再在 Shell 2 执行：

```bash
docker compose up -d
```

如果 FastOJ 通过 Docker Compose 运行，容器需要用 `host.docker.internal`
访问宿主机上的 Qwen 服务，因此 `.env` 中应配置下面的容器侧 URL。Compose
文件已经把 `host.docker.internal` 映射到 Docker 的 `host-gateway`，可兼容原生
Linux，同时也兼容 Docker Desktop 和 WSL。

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://host.docker.internal:8080/v1
AI_API_KEY=sk-no-key-required
AI_MODEL=qwen2.5-coder-7b-instruct-q4_k_m

AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

修改 `.env` 后重启 API：

```bash
docker compose up --build -d api
```

如果后端直接跑在宿主机上，而不是 Docker 容器里，则 `AI_BASE_URL` 和
`AI_QWEN_BASE_URL` 使用 `http://127.0.0.1:8080/v1`。

前台运行的 `docker compose up` 可以用 `Ctrl+C` 停止。本地 Qwen 服务可以这样
停止：

```bash
pkill -f "llama-server.*qwen2.5-coder-7b-instruct-q4_k_m" || true
```

PowerShell：

```powershell
& "$env:USERPROFILE\Models\qwen\stop-qwen-llama-server.ps1"
```

参考：[Qwen GGUF quickstart](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF)、
[llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases) 和
[llama-server 文档](https://www.mintlify.com/ggml-org/llama.cpp/inference/server)。

真实密钥放在 `.env` 或部署环境变量中。仓库已经忽略 `.env` 和 `.env.*`；
`.env.example` 只保留安全占位值。

## CI/CD 部署

FastOJ 已包含 GitHub Actions：

- `.github/workflows/ci.yml`：在包含代码或配置变更的 PR 和 `master` 推送时运行
  后端 lint/test、前端 build/test；纯文档变更（`*.md`、`docs/**`、`specs/**`）
  会被忽略。
- `.github/workflows/deploy.yml`：在 GitHub Actions 里构建 API 和 worker
  镜像，推送到配置的镜像仓库；judge 运行时镜像只在需要时用稳定 tag 构建。随后用
  `ubuntu` 用户 SSH 到服务器，只拉取 API/worker 镜像并重启容器。纯文档
  `master` 推送不会触发部署。

本机和服务器都使用 `.env` 作为运行时环境文件名。本机从 `.env.example` 复制出
`.env`；服务器从 `.env.prod.example` 复制到 `/opt/projects/fastoj/.env` 并填写真实密钥。
常规“本机 + 一台服务器”流程不需要单独维护 `.env.dev`。

完整步骤见 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)。

## 安全模型

- 隐藏用例输入、期望输出、实际输出不会进入 AI prompt。
- 隐藏用例内容只通过管理员专用的用例管理和草稿审核界面展示。
- 普通用户只能解释和审查自己的提交；管理员访问全部提交也由服务端角色检查
  保护。
- 公开注册只能创建普通 `user`；管理员账号需要从可信 shell 启动，或由已有管
  理员管理。
- 当前忘记密码流程为管理员协助重置：用户联系管理员设置临时密码；密码变更会提升
  用户 token 版本，旧 access/refresh token 会被拒绝。
- 生产判题只使用 Docker 沙箱；`FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true`
  只允许本地开发使用。
- 生产提交必须走 Redis Streams Worker。inline judge fallback 只允许
  `DEBUG=true` 或显式设置 `JUDGE_INLINE_FALLBACK=true` 的本地调试场景。
- Judge Worker 会用 parent/child 模式监督单个判题任务，防止 Docker API 或
  数据库调用卡住时 parent 也失去调度能力；真正的不可信代码隔离仍由 Docker
  sandbox 提供。
- 在 Docker Compose 中，API 服务也会挂载 Docker socket，这样管理员专用的
  出题 Agent 可以在发布前或手动编辑后用沙箱校验官方草稿解法；多语言草稿
  会按每种官方解法语言分别校验。双模式草稿可以基于同一逻辑 testcase metadata
  同时校验 ACM stdin/stdout 与函数 JSON 视图。
- 沙箱容器默认禁用网络，带内存限制、pid 限制、capability drop、
  `no-new-privileges`、非 root 用户、输出截断、超时终止；正常 executor 路径会
  清理容器。如果 worker parent hard-kill 卡住的 judge child，child 可能来不及
  执行 Docker 清理逻辑，生产运维仍应监控和清理残留的 `fastoj_judge_*` 容器。

## 内置题库

种子数据已经扩展到可以支撑持续刷题：

- **Hot 100 面试题：** 覆盖 100 道 canonical Hot 100 题，链表、二叉树、设计题和
  多答案题都使用 FastOJ 自写题面与确定性用例。
- **经典函数题：** Two Sum、Add Two Numbers、Longest Substring Without
  Repeating Characters、Valid Parentheses、Alien Dictionary、Two-Car Parking Lot
  带 starter frame；现在所有 seed 题都有可展示、可执行的 Python 官方题解。
- **LeetCode 风格节点题：** Hot 100 链表和二叉树函数模式在 Python、C++、
  Java、JavaScript、TypeScript、Go、C 中暴露 `head`、`root`、`p`、`q`
  等节点对象。底层 testcase 输入输出仍保存为 JSON 数组；判题 wrapper 负责把
  数组构造成节点，并把返回节点序列化回公开示例格式。
- **确定性增强用例：** seed 导入时每题至少包含两个公开用例，并按题型扩展隐藏
  覆盖：普通数组/字符串/DP/图/树/链表题至少 30 个隐藏用例，设计类和 AI/ML 题至少
  20 个，高输出组合题至少 15 个。
- **本地化解释：** seed 题目详情会返回中英文公开示例解释，Python 官方题解也会按
  页面语言显示真实解法说明，不再显示生成式占位模板。
- **AI/ML 算法题：** Logistic Regression Sigmoid、KNN Majority Vote、
  KMeans One Iteration、Scaled Dot-Product Attention、Softmax Cross
  Entropy、Attention Mask Apply。

函数模式支持 Python、C++、Java、JavaScript、TypeScript、Go，以及部分简单 C
wrapper。所有题目仍然可以使用 ACM 模式。公开题解 API 仍可按当前编辑器语言查询；
如果该语言没有官方题解，会回退返回 Python 官方题解，并保留真实的
`language: "python"`。Judge runtime 内置 Python `numpy==2.2.6` 和 CPU
`torch==2.7.1+cpu`，AI 算法题可以使用标准 Python、NumPy 或 PyTorch。

## 架构

```mermaid
flowchart LR
  Browser[React UI] --> API[FastAPI API]
  API --> DB[(PostgreSQL)]
  API --> Redis[(Redis Streams)]
  Redis --> Worker[Judge Worker]
  Worker --> Sandbox[Docker Sandbox]
  Worker --> Bus[Redis Pub/Sub]
  Bus --> API
  API --> Browser
  API --> AI[OpenAI-compatible AI Provider]
```

关键链路：

- **运行和提交：** API 持久化提交记录，把判题任务写入 Redis Streams，并快速返回
  状态；Worker 再在 Docker 沙箱中执行用户代码。
- **实时反馈：** Worker 事件通过 Redis 发布，再由 API 推送到浏览器；前端优先使用
  WebSocket 状态更新，必要时回退到轮询。
- **函数模式：** 服务层 wrapper 把 typed JSON 风格的函数输入转换成各语言可执行
  harness，并为 seed 链表/二叉树题提供节点对象适配；ACM 模式仍保留原始
  stdin/stdout 执行。
- **AI 辅助：** API 只用公开样例、判题结果、用户代码和安全摘要构造 prompt。隐藏
  用例内容留在管理员专用接口之后，不进入学习者侧 AI prompt。
- **管理端出题：** 草稿生成、题目导入、校验、修复尝试、官方题解和用例审核都经过
  服务端角色检查。

核心工程栈：

- 后端：Python 3.11+、FastAPI、SQLAlchemy 2.0、Pydantic v2、Alembic、
  PostgreSQL、Redis Streams。
- 判题：Docker 沙箱 Worker，支持异步队列、parent/child 任务 watchdog、
  active-task 标记、重试、死信队列和重复任务保护。
- 前端：React、TypeScript、Vite、Tailwind CSS、Monaco Editor、TanStack
  Query、Zustand、Zod、xterm、Shiki、React Flow、DOMPurify、marked、Pretext
  文本测量。
- 工具：`uv`、`ruff`、`pytest`、`npm`、Vitest、Docker Compose、GitHub Actions、
  镜像仓库。

## 项目结构

```text
backend/
  ai/           AI provider 配置、prompt、响应 schema
  api/          FastAPI 路由
  core/         设置、数据库、安全、日志
  models/       SQLAlchemy 模型
  schemas/      Pydantic API schema
  scripts/      seed、管理员、修复类工具
  services/     业务逻辑、判题、函数模式 wrapper
  worker/       Judge Worker
frontend/
  src/
    components/
    lib/
    stores/
    main.tsx
tests/          后端测试
docs/           部署、交接、验收和项目导览文档
specs/          产品和实现规划文档
```

## 质量门槛

较大的变更交付前运行：

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

如果改动涉及 judge、worker、WebSocket/SSE、沙箱或真实提交链路，还需要运行：

```bash
docker compose up --build -d api worker
```

完整手工验收清单位于
[`docs/ACCEPTANCE_HARNESS.md`](docs/ACCEPTANCE_HARNESS.md)。

## 已知限制

- Monaco 和 Shiki 目前直接进入前端 bundle，生产 chunk 偏大。
- C 函数模式暂时只覆盖较简单的种子签名；矩阵/字符串密集的 AI 题建议先用
  ACM 模式。
- MLE 分类依赖 Docker runtime 的退出状态。
- AI 质量取决于配置的 OpenAI-compatible 模型和提示词行为。
- 初始 Alembic migration 是当前 schema 的基线，接入已有生产数据库前需要单
  独验证。
