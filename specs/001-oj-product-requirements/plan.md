# Implementation Plan: 面向面试者的 OJ 平台

**Branch**: `001-oj-product-requirements` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: 面向面试者的 OJ 平台产品需求 - 题目浏览、代码编辑、多语言评测、实时状态流转

## Summary

构建一个面向面试者的在线评测（OJ）平台，支持题目浏览与筛选、代码编写与评测、多语言支持和实时评测状态流转。系统采用 FastAPI 后端 + PostgreSQL + Redis + 自研 Docker 沙箱架构，满足宪法规定的所有技术原则。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, Redis, Python Docker SDK
**Storage**: PostgreSQL (primary), Redis (cache + queue)
**Testing**: pytest
**Target Platform**: Linux server (Docker)
**Project Type**: web-service (FastAPI backend)
**Performance Goals**:
- 题目大厅页面加载 < 3秒
- 筛选响应 < 1秒
- 代码编辑器加载 < 2秒
- 95% 评测任务在 30 秒内完成
- 支持 1000+ 并发用户
**Constraints**:
- 99.5% 可用性（月均 11 小时 downtime）
- 5 种语言支持：Python, C/C++, Java, TypeScript/JavaScript, Golang
- 评测状态：Pending -> Judging -> AC/WA/TLE/MLE/CE
**Scale/Scope**: 单项目，无前端（仅后端 API）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| PostgreSQL-First Storage | ✅ PASS | 所有业务数据存储在 PostgreSQL |
| Redis + Message Queue | ✅ PASS | Redis 用于缓存和判题任务队列 |
| Custom Sandbox (Docker SDK) | ✅ PASS | 使用 Python Docker SDK 自研沙箱 |
| Modular Route Architecture | ✅ PASS | 路由按 domain 分为 problems/submissions/users 等 |
| Judge Worker Decoupling | ✅ PASS | Worker 完全解耦，通过 Redis 队列通信 |
| Docker-Compose Deployment | ✅ PASS | 所有服务通过 docker-compose 部署 |

**结论**: 完全符合宪法规定的所有技术原则。

## Project Structure

### Documentation (this feature)

```text
specs/001-oj-product-requirements/
├── plan.md              # This file
├── research.md          # (已存在如有需要)
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
└── tasks.md             # Phase 2 输出
```

### Source Code (repository root)

```text
backend/
├── main.py                 # FastAPI 应用入口
├── api/                    # 路由模块（按 domain 分离）
│   ├── __init__.py
│   ├── auth/               # 认证相关
│   ├── problems/           # 题目相关
│   ├── submissions/        # 提交相关
│   ├── users/              # 用户相关
│   ├── websocket/          # WebSocket 实时通信
│   └── middleware/         # 中间件
├── models/                 # SQLAlchemy 模型
│   ├── __init__.py
│   ├── problem.py
│   ├── testcase.py
│   ├── solution.py
│   ├── submission.py
│   └── user.py
├── schemas/                # Pydantic schemas
│   ├── __init__.py
│   ├── problem.py
│   ├── submission.py
│   └── user.py
├── services/               # 业务逻辑
│   ├── __init__.py
│   ├── problem_service.py
│   ├── submission_service.py
│   ├── judge_service.py
│   ├── queue_service.py
│   └── user_service.py
├── worker/                 # 判题 Worker（解耦部署）
│   ├── __init__.py
│   ├── judge_worker.py
│   └── tasks/
│       ├── __init__.py
│       ├── consumer.py
│       └── judge_task.py
├── sandbox/                # Docker 沙箱
│   ├── __init__.py
│   ├── executor.py
│   ├── security.py
│   └── languages/
│       ├── __init__.py
│       ├── python.py
│       ├── cpp.py
│       ├── java.py
│       ├── javascript.py
│       └── golang.py
├── core/                   # 核心配置
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── languages.py
│   └── validators.py
├── scripts/                # 脚本
│   └── seed_data.py
└── tests/                  # 测试
    ├── __init__.py
    ├── api/
    ├── services/
    └── sandbox/
```

**Structure Decision**: 采用宪法规定的模块化架构，backend/ 下按 domain (api/models/services/worker/sandbox/core) 组织代码。

## Complexity Tracking

> **无需追踪**: 本计划完全符合宪法，无违规项。

---

## Phase 0: Research

*本阶段主要基于 spec.md 中的用户故事和宪法要求，技术选型已明确，无需额外研究。*

### 已确认的技术决策

| 决策项 | 选型 | 理由 |
|--------|------|------|
| 后端框架 | FastAPI | 高性能、异步支持、自动 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 | Python 标准 ORM，支持异步 |
| 数据库 | PostgreSQL | 宪法要求 |
| 缓存/队列 | Redis | 宪法要求 |
| 沙箱 | Python Docker SDK | 宪法明确要求禁止使用 Judge0 |
| Worker 通信 | Redis Queue | 宪法要求完全解耦 |
| 认证 | JWT | spec.md 明确要求 |

### 需要澄清的问题

无 - spec.md 和宪法已提供足够的技术上下文。

---

## Phase 1: Design

### 1.1 数据模型设计

基于 spec.md 中的实体定义和宪法要求：

**Problem (题目)**
- id: UUID/Integer
- title: String
- description: Text (Markdown)
- difficulty: Enum (Easy/Medium/Hard)
- tags: List[String]
- time_limit: Integer (ms)
- memory_limit: Integer (MB)
- created_at: DateTime

**TestCase (测试用例)**
- id: UUID/Integer
- problem_id: FK
- input: Text
- output: Text
- is_hidden: Boolean
- order: Integer

**Submission (提交)**
- id: UUID/Integer
- user_id: FK
- problem_id: FK
- code: Text
- language: Enum (Python/CPP/Java/JS/Go)
- status: Enum (Pending/Judging)
- result: Enum (AC/WA/TLE/MLE/CE/None)
- created_at: DateTime

**OfficialSolution (官方解法)**
- id: UUID/Integer
- problem_id: FK
- language: Enum
- code: Text
- explanation: Text (Markdown)

**User (用户)**
- id: UUID/Integer
- username: String
- email: String
- hashed_password: String
- role: Enum (user/admin)
- created_at: DateTime

### 1.2 API 接口设计

**认证**
- POST /auth/register
- POST /auth/login
- GET /auth/me

**题目**
- GET /problems - 列表（支持分页、标签/难度筛选）
- GET /problems/{id} - 详情
- GET /problems/{id}/solutions - 官方解法

**提交**
- POST /submissions - 提交代码（完整评测）
- POST /submissions/run - 运行代码（仅公开用例）
- GET /submissions/{id} - 详情
- GET /submissions - 用户提交列表

**WebSocket**
- WS /ws/judge/{submission_id} - 实时评测状态

### 1.3 评测流程设计

1. 用户提交代码 -> POST /submissions
2. API 创建 Submission (status=Pending) -> 入队到 Redis
3. Worker 消费任务 -> 更新 status=Judging
4. Worker 调用 Sandbox 执行代码
5. 执行完成 -> 更新 result -> WebSocket 通知前端

### 1.4 沙箱安全设计

基于宪法要求：
- network_mode='none' - 完全隔离网络
- pids_limit - 限制进程数
- CPU 时间限制 - cgroups
- 内存限制 - cgroups
- 代码文件只读挂载

---

## Quickstart

```bash
# 开发环境
cd /home/lightning/projects/fastoj
uv sync

# 运行 API
uv run uvicorn backend.main:app --reload

# 运行 Worker（独立终端）
uv run python -m backend.worker.judge_worker

# Docker 部署
docker-compose up --build
```

---

## 实施检查清单

- [x] 确认 Constitution Check 全部通过
- [x] 确认技术选型符合宪法要求
- [x] 确认数据模型覆盖所有 spec 实体
- [x] 确认 API 覆盖所有用户故事
- [x] 确认 Worker 解耦设计
- [x] 确认沙箱安全要求
