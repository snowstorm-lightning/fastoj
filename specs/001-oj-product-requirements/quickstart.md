# Quickstart Guide: FastOJ 开发环境搭建

**Created**: 2026-03-16
**Feature**: 面向面试者的 OJ 平台

## 1. 环境要求

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose
- Node.js 18+ (前端开发)

---

## 2. 本地开发环境

### 2.1 克隆项目

```bash
git clone https://github.com/your-repo/fastoj.git
cd fastoj
```

### 2.2 启动基础服务 (PostgreSQL + Redis)

```bash
# 使用 docker-compose 启动基础服务
docker-compose -f docker-compose.base.yml up -d
```

`docker-compose.base.yml` 内容:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: fastoj
      POSTGRES_USER: fastoj
      POSTGRES_PASSWORD: fastoj_secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2.3 配置环境变量

```bash
# 复制环境配置示例
cp .env.example .env

# 编辑 .env 文件
DATABASE_URL=postgresql://fastoj:fastoj_secret@localhost:5432/fastoj
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

### 2.4 安装后端依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2.5 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 或创建表（开发环境）
python -c "from backend.models import Base; from backend.core.database import engine; Base.metadata.create_all(engine)"
```

### 2.6 启动后端服务

```bash
# 启动 FastAPI 开发服务器
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 启动判题 Worker (新终端)
python -m backend.worker.judge_worker
```

### 2.7 启动前端开发服务器

```bash
cd frontend
npm install
npm run dev
```

---

## 3. Docker Compose 完整部署

### 3.1 生产环境部署

```bash
# 启动所有服务
docker-compose up -d
```

`docker-compose.yml` 结构:
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://fastoj:fastoj_secret@postgres:5432/fastoj
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://fastoj:fastoj_secret@postgres:5432/fastoj
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    # ...

  redis:
    image: redis:7-alpine
    # ...
```

### 3.2 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f worker

# API 健康检查
curl http://localhost:8000/api/v1/health
```

---

## 4. 判题 Worker 配置

### 4.1 判题容器镜像构建

```bash
cd backend/sandbox
docker build -t fastoj-judge:latest -f Dockerfile.judge .
```

`Dockerfile.judge` 示例:
```dockerfile
FROM python:3.11-slim

# 安装编译工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-jdk \
    nodejs \
    npm \
    golang \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -s /bin/bash judge
USER judge

WORKDIR /home/judge

CMD ["/bin/bash"]
```

### 4.2 Worker 配置

```python
# backend/core/config.py
class Settings(BaseSettings):
    # 判题配置
    JUDGE_CONTAINER_IMAGE = "fastoj-judge:latest"
    JUDGE_TIMEOUT = 30  # 最大判题时间（秒）
    JUDGE_MAX_RETRIES = 3

    # 资源限制
    DEFAULT_TIME_LIMIT = 1000  # ms
    DEFAULT_MEMORY_LIMIT = 256  # MB
```

---

## 5. 测试

### 5.1 单元测试

```bash
# 运行后端单元测试
pytest backend/tests/unit -v

# 运行前端测试
cd frontend && npm test
```

### 5.2 集成测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest backend/tests/integration -v
```

### 5.3 判题测试

```bash
# 测试沙箱隔离
python -m pytest backend/tests/unit/test_sandbox.py -v

# 测试判题流程
python -m pytest backend/tests/integration/test_judge.py -v
```

---

## 6. 常见问题

### Q: Worker 无法连接到 Redis
A: 检查 `REDIS_URL` 环境变量配置，确保 Redis 服务正常运行

### Q: 判题超时
A: 检查沙箱容器镜像是否正确构建，增加 `JUDGE_TIMEOUT` 配置

### Q: 数据库连接失败
A: 确保 PostgreSQL 服务运行中，检查 `DATABASE_URL` 配置格式

### Q: 前端无法连接 API
A: 检查 API 服务端口是否正确暴露，CORS 配置是否正确
