# FastOJ - 面向面试者的在线评测平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109-green?style=flat-square&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-14+-blue?style=flat-square&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7+-red?style=flat-square&logo=redis" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker" alt="Docker">
</p>

## 项目简介

FastOJ 是一个面向面试者的在线评测（OJ）平台，旨在帮助开发者通过刷题提升算法能力，为技术面试做准备。

### 核心特性

- **题目大厅** - 支持按难度、标签筛选，分页浏览
- **刷题工作台** - 左右分屏布局，题目描述与代码编辑一体化
- **多语言支持** - Python、C/C++、Java、JavaScript、Go
- **实时评测** - WebSocket 实时推送 Pending → Judging → AC/WA/TLE/MLE/CE
- **公开/隐藏用例** - 运行仅用公开用例，提交使用全部用例

## 技术架构

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | PostgreSQL 14+ |
| 缓存/队列 | Redis 7+ |
| ORM | SQLAlchemy 2.0 |
| 认证 | JWT |
| 判题沙箱 | Docker |
| 部署 | Docker Compose |

### 架构图

```
┌─────────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐
│  前端提交   │────▶│ FastAPI │────▶│  Redis   │────▶│  Worker │────▶│ 沙箱   │
│  代码请求   │     │   API   │     │  Queue   │     │  判题   │     │ 执行   │
└─────────────┘     └─────────┘     └──────────┘     └─────────┘     └─────────┘
      │                                    │                                    │
      │                                    ▼                                    │
      │                             ┌──────────┐                                │
      │                             │ 更新状态 │◀───────────────────────────────┘
      │                             │ DB: Pending->Judging                     │
      │                             └──────────┘                                │
      │                                    │                                    │
      ▼                                    ▼                                    ▼
┌─────────────┐                     ┌──────────┐                         ┌─────────┐
│ WebSocket   │◀────────────────────│ 更新状态 │                          │ 返回结果│
│ 实时推送    │                     │ DB: Judging->AC/WA...            │ 存储DB  │
└─────────────┘                     └──────────┘                          └─────────┘
```

## 快速开始

### 环境要求

- Python 3.11+
- uv (Python 包管理工具)
- Docker & Docker Compose
- PostgreSQL 14+ (Docker 提供)
- Redis 7+ (Docker 提供)

### 本地开发

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/fastoj.git
cd fastoj
```

#### 2. 启动基础服务

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis
```

#### 3. 安装 Python 依赖

```bash
# 使用 uv 安装依赖
uv sync
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

#### 5. 初始化数据库

```bash
uv run python -c "from backend.core.database import engine, Base; Base.metadata.create_all(engine)"
```

#### 6. 导入示例数据

```bash
uv run python scripts/seed_data.py
```

#### 7. 启动服务

```bash
# 启动 API 服务
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 启动判题 Worker (新终端)
uv run python -m backend.worker.judge_worker
```

#### 8. 访问服务

- API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f worker
```

## API 文档

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新 Token |

### 题目接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/problems | 获取题目列表 (支持分页/筛选) |
| GET | /api/v1/problems/{id} | 获取题目详情 |
| GET | /api/v1/problems/{id}/solutions | 获取官方解法 |

### 提交接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/submissions | 提交代码 (完整评测) |
| POST | /api/v1/submissions/run | 运行代码 (仅公开用例) |
| GET | /api/v1/submissions | 获取用户提交列表 |
| GET | /api/v1/submissions/{id} | 获取提交详情 |

### WebSocket

| 路径 | 描述 |
|------|------|
| /api/v1/ws/judge/{submission_id} | 实时判题状态推送 |

### 请求示例

#### 获取题目列表

```bash
curl -X GET "http://localhost:8000/api/v1/problems?page=1&page_size=20&difficulty=easy"
```

#### 提交代码

```bash
curl -X POST "http://localhost:8000/api/v1/submissions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "uuid-here",
    "code": "print(\"hello\")",
    "language": "python"
  }'
```

## 项目结构

```
fastoj/
├── backend/
│   ├── api/                    # API 路由
│   │   ├── auth/               # 认证接口
│   │   ├── problems/            # 题目接口
│   │   ├── submissions/         # 提交接口
│   │   ├── websocket/           # WebSocket
│   │   └── middleware/          # 中间件
│   ├── core/                    # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── security.py          # JWT 认证
│   │   └── languages.py         # 语言配置
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # 业务逻辑
│   │   ├── problem_service.py
│   │   ├── submission_service.py
│   │   ├── queue_service.py
│   │   └── judge_service.py
│   ├── worker/                  # 判题 Worker
│   │   ├── judge_worker.py
│   │   └── tasks/
│   ├── sandbox/                 # Docker 沙箱
│   │   ├── executor.py
│   │   ├── security.py
│   │   └── languages/
│   └── scripts/
│       └── seed_data.py         # 示例数据
├── frontend/                    # 前端 (待实现)
├── docker-compose.yml           # 容器编排
├── Dockerfile.api               # API 容器
├── Dockerfile.worker            # Worker 容器
├── pyproject.toml               # 项目配置
└── README.md                    # 本文件
```

## 判题流程

### 支持的语言

| 语言 | 编译命令 | 执行命令 |
|------|----------|----------|
| Python | 无 | `python3 {file}` |
| C | `gcc -o {out} {file} -O2 -std=c11` | `{out}` |
| C++ | `g++ -o {out} {file} -O2 -std=c++17` | `{out}` |
| Java | `javac {file}` | `java -cp . {class}` |
| JavaScript | 无 | `node {file}` |
| Go | 无 | `go run {file}` |

### 状态流转

```
Pending → Judging → Finished
                         ↓
                   AC / WA / TLE / MLE / CE / RE / SE
```

- **AC** - Accepted (通过)
- **WA** - Wrong Answer (答案错误)
- **TLE** - Time Limit Exceeded (超时)
- **MLE** - Memory Limit Exceeded (内存超限)
- **CE** - Compile Error (编译错误)
- **RE** - Runtime Error (运行时错误)
- **SE** - System Error (系统错误)

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

## 待实现功能

- [ ] 前端界面 (React/Vue)
- [ ] 完整 Docker 沙箱执行
- [ ] 单元测试/集成测试
- [ ] 用户个人信息管理
- [ ] 题目管理后台
- [ ] 排行榜功能

## 许可证

MIT License

---

<p align="center">Made with ❤️ for developers</p>
