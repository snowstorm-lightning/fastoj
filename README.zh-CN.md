# FastOJ

## 本轮补充

- AI explain/review 已兼容 provider 返回 `null` 文本字段；本地 Qwen 服务不可达时返回 HTTP 503 和明确提示，不再显示泛化的内部服务器错误。
- 新增 AI 对话接口，只使用题目、代码、判题状态和公开用例结果，不发送隐藏用例内容。
- 题库卡片现在会同时显示支持的函数模式和 ACM 模式；有效的括号已补充函数模式模板和后端 wrapper。

[English](README.md) | 简体中文

FastOJ 是一个面向面试训练的 AI 可解释 OJ 平台。它保留传统 OJ 的严格评测，同时把判题解释、代码审查、渐进提示、判题时间线、知识图谱和提交轨迹做成核心体验。

AI 解释只基于真实提交结果和公开用例信息。隐藏用例的输入、期望输出、实际输出不会返回给普通用户，也不会发送给 AI 服务商。

## 架构

- 后端：FastAPI、SQLAlchemy 2.0、PostgreSQL、Alembic、JWT 认证。
- 队列：Redis Streams，包含 consumer group、ack、重试、死信队列和 pending reclaim。
- 评测：Docker 沙箱 Worker。生产环境不回退到宿主机 `subprocess`。
- 实时状态：Worker 通过 Redis pub/sub 发布判题状态，API 通过 WebSocket 转发给前端。
- 前端：Vite、React、TypeScript、Tailwind CSS、Monaco Editor、TanStack Query、Zustand、Zod、xterm、Shiki、@xyflow/react、@chenglou/pretext。
- AI：OpenAI-compatible Chat Completions Provider，默认关闭。

## 启动

后端：

```bash
uv sync --extra dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

Docker：

```bash
docker compose up --build
```

## 前端体验

- 题库页：支持关键词、标签、难度筛选、分页、训练摘要、AI 练习数量、函数模式数量和推荐入口。
- 认证页：登录/注册是独立页面，不嵌入全局 Header。
- 工作台：三栏布局，题面和结果侧栏支持折叠、拖拽调整宽度，中间是 Monaco 编辑器。
- 模式切换：支持函数模式和 ACM 模式。函数模式展示对应语言的函数框架；ACM 模式由用户代码处理标准输入输出。
- 语言切换：UI chrome、判题状态、hover 说明、模式标签、题目展示和 AI 请求语言都跟随中文/英文切换。
- 详情区：公开用例、官方题解、判题过程、提交记录和本地讨论区通过 Tab 切换。
- 知识图谱：使用 @xyflow/react 渲染知识点节点，点击节点回到题库并应用标签筛选。
- 静态图形化讲解：部分题目展示预生成步骤图，不为基础概念解释消耗 AI token。
- 账户设置：登录用户可以修改显示名、用户名、邮箱、头像 URL、紧凑模式和密码。
- 管理后台：只有管理员角色可以进入。后台支持管理用户角色/启用状态、题目难度/公开状态，并显示测试用例和题解数量；隐藏用例只显示数量，不暴露内容。

## AI 配置

AI 默认关闭：

```bash
AI_PROVIDER=disabled
```

DeepSeek API 示例：

```bash
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-v4-flash
```

页面内选择 `DeepSeek` 时使用命名 profile：

```bash
AI_DEEPSEEK_BASE_URL=https://api.deepseek.com
AI_DEEPSEEK_API_KEY=your-deepseek-api-key
AI_DEEPSEEK_MODEL=deepseek-v4-flash
```

页面内选择 `Qwen local` 时使用本地 OpenAI-compatible 服务：

```bash
AI_QWEN_BASE_URL=http://host.docker.internal:8080/v1
AI_QWEN_API_KEY=sk-no-key-required
AI_QWEN_MODEL=qwen2.5-coder-3b-instruct
```

如果本地 Qwen 服务没有启动，或端口配置不对，AI 操作会返回 HTTP 503，并显示明确的 provider unreachable 提示，不再显示泛化的内部服务器错误。

真实密钥放在仓库根目录 `.env` 或部署环境变量中。`.env` 和 `.env.*` 已被 git 忽略；`.env.example` 只保留变量名和占位值。

## 安全规则

- 隐藏用例的输入、期望输出、实际输出不会进入 AI prompt。
- 用户只能解释/审查自己的提交；管理员可以访问全部提交。
- AI 被要求不能直接泄露完整 AC 解法。
- 生产环境只使用 Docker 沙箱；`FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION=true` 仅允许本地开发使用。

## 练习模式和题目

种子数据可以应用到新数据库或已有数据库：

```bash
uv run python -m backend.scripts.seed_data
```

种子题包含传统面试题、面试清单题和 AI 算法题：

- 传统/函数题：Two Sum、Add Two Numbers、Longest Substring Without Repeating Characters。
- 面试清单 ACM 题：Valid Parentheses、Maximum Subarray、Group Anagrams、Merge Intervals、Climbing Stairs、Container With Most Water。
- AI 算法题：Logistic Regression Sigmoid、KNN Majority Vote、KMeans One Iteration、Scaled Dot-Product Attention、Softmax Cross Entropy、Attention Mask Apply。

函数模式支持 Python、C++、Java、JavaScript、TypeScript、Go，以及部分简单 C 签名。所有题目仍可使用 ACM 模式。

Docker judge runtime 内置 Python `numpy==2.2.6` 和 CPU `torch==2.7.1+cpu`，AI 算法提交可以使用标准 Python、NumPy 或 PyTorch。

## 测试命令

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run build
cd frontend && npm test
```

本次最新验证：

- `uv run ruff check .`：通过。
- `uv run pytest`：72 passed，3 个 datetime deprecation warnings。
- `cd frontend && npm run build`：通过，仍有 Monaco/Shiki chunk-size warning。
- `cd frontend && npm test`：6 个测试文件、8 个测试通过；jsdom 仍打印预期的 canvas `getContext` warning。
- `docker compose up --build -d api worker`：通过，API 和 Worker 均 healthy。
- Docker 真实公开运行 Two Sum C++ 函数模式：`result=ac`。本轮修复了编译型语言 stdin 被错误管道到编译器、以及沙箱工作目录不可写的问题。

## 已知限制

- Monaco 和 Shiki 目前直接打进前端包，初始 bundle 偏大。
- C 函数模式暂时只覆盖简单种子签名；矩阵/字符串类 AI 题建议先用 ACM 模式。
- MLE 分类依赖 Docker runtime 的退出状态。
- `qwen-local` profile 已接线，但需要本机先启动 OpenAI-compatible Qwen 服务。
