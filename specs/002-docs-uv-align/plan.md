# Implementation Plan: Windows 系统移植分析

**Branch**: `002-docs-uv-align` | **Date**: 2026-03-16 | **Spec**: [link](../002-docs-uv-align/spec.md)
**Input**: 将 FastOJ 项目从 Linux 移植到 Windows 系统（使用 Linux 容器 + Docker Desktop）

## Summary

分析 FastOJ 项目从 Linux 迁移到 Windows 开发环境所需修改的代码。项目使用 Python/FastAPI + PostgreSQL + Redis + Docker 技术栈。由于采用 Docker Desktop for Windows 运行 Linux 容器，核心代码无需大幅修改，仅需调整部分配置和脚本。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Pydantic, Redis, Python Docker SDK
**Storage**: PostgreSQL 14+, Redis
**Testing**: pytest
**Target Platform**: Windows (使用 Linux 容器)
**Project Type**: Web Service (Online Judge System)
**Development Environment**: Claude Code (Windows) + Docker Desktop (Linux 容器)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| PostgreSQL-First Storage | ✅ PASS | PostgreSQL 可在 Windows 运行 |
| Redis + Message Queue | ✅ PASS | Redis 可在 Windows 运行 |
| Custom Sandbox | ✅ PASS | Docker 配置无需大改（使用 Linux 容器） |
| Docker-Compose Deployment | ✅ PASS | Docker Desktop 支持 docker-compose |

## 兼容性分析结果

### 需要关注的区域

| 类别 | 状态 | 说明 |
|------|------|------|
| Python 代码 | ✅ 兼容 | 标准库已跨平台 |
| SQLAlchemy/Redis | ✅ 兼容 | 纯 Python，无平台依赖 |
| Docker 容器 | ✅ 兼容 | Linux 容器在 Docker Desktop 中运行正常 |
| Shell 脚本 | ⚠️ 需修改 | `.specify/scripts/bash/` 下的脚本使用 bash 语法 |

### 必须修改的文件

#### 1. Docker 配置

| 文件 | 修改内容 |
|------|---------|
| `docker-compose.yml` | 健康检查命令需兼容 Linux 容器（已兼容） |
| `docker-compose.yml` | 移除 Windows 不存在的路径挂载说明 |

#### 2. Shell 脚本 (Windows 无法直接运行)

| 文件 | 问题 | 解决方案 |
|------|------|---------|
| `.specify/scripts/bash/*.sh` | bash 脚本无法在 Windows CMD/PowerShell 运行 | 创建 PowerShell 等效脚本 或 在 WSL 中运行 |

#### 3. Python 代码 (无需修改)

| 文件 | 状态 |
|------|------|
| `backend/sandbox/executor.py` | ✅ 使用 `os.path.join` 跨平台兼容 |
| `backend/core/database.py` | ✅ 纯 Python，无平台依赖 |
| `backend/services/queue_service.py` | ✅ 纯 Python，无平台依赖 |
| `backend/sandbox/security.py` | ✅ Docker 配置在容器内执行，无影响 |

### Windows 开发环境准备

#### 必需软件

1. **Docker Desktop for Windows**
   - 需启用 WSL2 后端
   - 建议分配 4GB+ 内存

2. **Python 3.11+**
   - 建议使用 `uv` 安装（已支持 Windows）

3. **PostgreSQL 14+**
   - 可选择:
     - Docker 容器运行（推荐）
     - Windows 本地安装

4. **Redis**
   - 可选择:
     - Docker 容器运行（推荐）
     - Windows 本地安装（使用 WSL 或 Memurai/Redis Windows 端口）

### 推荐的 Windows 开发工作流

```powershell
# 1. 启动 Docker Desktop

# 2. 使用 uv 安装依赖
uv sync

# 3. 启动 PostgreSQL 和 Redis (Docker)
docker run -d --name fastoj-postgres -e POSTGRES_DB=fastoj -e POSTGRES_USER=fastoj -e POSTGRES_PASSWORD=fastoj_secret -p 5432:5432 postgres:14
docker run -d --name fastoj-redis -p 6379:6379 redis:7-alpine

# 4. 运行测试
pytest

# 5. 启动开发服务器
uvicorn backend.main:app --reload
```

## Project Structure

```text
fastoj/
├── backend/
│   ├── api/           # FastAPI routes
│   ├── core/          # 配置
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # 业务逻辑
│   ├── worker/        # Judge worker
│   └── sandbox/       # Docker sandbox
├── tests/
├── docker-compose.yml        # Docker 部署配置
├── Dockerfile.api            # API 容器
├── Dockerfile.worker         # Worker 容器
└── pyproject.toml           # 项目配置
```

## 实际需要修改的内容

### 1. 创建 Windows 开发环境脚本

新建 `scripts/dev-start.ps1` (PowerShell):

```powershell
# Windows 开发环境启动脚本
# 位置: scripts/dev-start.ps1
```

### 2. 更新文档

- `README.md`: 添加 Windows 开发环境说明
- `CLAUDE.md`: 添加 Windows 开发注意事项

### 3. Shell 脚本兼容

`.specify/scripts/bash/` 下的脚本需要:
- 在 Windows 上通过 WSL 或 Git Bash 运行
- 或创建 PowerShell 等效版本

## Complexity Tracking

| 改动项 | 优先级 | 预估工作量 |
|--------|--------|-----------|
| 创建 Windows 启动脚本 | 中 | 1h |
| 更新 README.md | 低 | 0.5h |
| 更新 CLAUDE.md | 低 | 0.5h |

## 结论

由于采用 **Docker Desktop for Windows + Linux 容器** 方案，FastOJ 项目代码本身无需重大修改。主要工作:

1. **代码层面**: 无需修改（Python 代码已是跨平台）
2. **配置层面**: Docker 配置在容器内运行，无影响
3. **脚本层面**: Shell 脚本需通过 WSL/Git Bash 运行
4. **文档层面**: 添加 Windows 开发环境说明

**建议**: 直接将代码复制到 Windows 系统，安装 Docker Desktop + Python (uv) + PostgreSQL/Redis (Docker) 即可开始开发。

## 下一步

1. 在 Windows 系统上安装 Docker Desktop 并启用 WSL2
2. 复制项目代码到 Windows
3. 运行 `uv sync` 安装依赖
4. 通过 Docker 启动 PostgreSQL 和 Redis
5. 运行测试验证环境
