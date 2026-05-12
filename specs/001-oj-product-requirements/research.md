# Research Report: FastOJ 技术调研

**Created**: 2026-03-16
**Feature**: 面向面试者的 OJ 平台

## 1. 前端状态同步方案

### Decision: WebSocket

### Rationale

- 实时性更好，状态变化可立即推送
- 减少不必要的 HTTP 请求开销
- 适合判题这种可能持续数秒的操作
- WebSocket 连接断开后可自动重连
- 支持双向通信，不仅可接收状态更新，还可发送心跳

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| WebSocket | 实时双向通信，低延迟 | 需要维护连接状态 | **采用** |
| Long-polling | 实现简单 | 延迟高，资源浪费 | 不采用 |
| Server-Sent Events | 单向推送简单 | 不支持双向通信 | 备选 |

---

## 2. 消息队列方案

### Decision: Redis List + 自研队列

### Rationale

- Constitution 要求使用 Redis 作为消息队列
- Celery 增加了不必要的复杂度（Broker、Result Backend、Task序列化等）
- 简单任务分发不需要 Celery 的高级特性（任务链、任务路由等）
- 可以使用 Redis 的 LPUSH/BRPOP 实现可靠 FIFO 队列
- 更轻量，更容易调试和维护

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| Redis List | 轻量，符合 Constitution | 需要自己实现重试机制 | **采用** |
| Celery + Redis | 功能完善 | 重量级，过度设计 | 不采用 |
| RabbitMQ | 功能完善 | 额外依赖，不符合 Constitution | 不采用 |

---

## 3. 沙箱隔离方案

### Decision: 自研 Docker 容器（遵循 Constitution IV）

### Rationale

- Constitution IV 明确禁止使用 Judge0 等预构建方案
- Python Docker SDK 提供足够的控制能力
- 可自定义安全策略（网络隔离、进程限制、内存限制）
- 资源限制通过 Docker 参数实现

### 沙箱安全配置

```python
# 核心安全配置
run_config = {
    'network_disabled': True,           # 网络完全禁用
    'mem_limit': '256m',                # 内存限制 256MB
    'pids_limit': 50,                   # 进程数限制（防forkbomb）
    'cpu_period': 100000,               # CPU 调度周期
    'cpu_quota': 50000,                 # CPU 时间限制 (50%)
    'read_only': True,                  # 只读文件系统
    'tmpfs': ['/tmp'],                  # 临时目录在内存中
}
```

### Alternatives Considered

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 自研 Docker | 灵活可控，符合 Constitution | 需要自行实现资源限制 | **采用** |
| gVisor | 安全隔离好 | 额外依赖，不使用 Python SDK | 不采用 |
| Judge0 | 快速集成 | 违反 Constitution 禁止条款 | 禁止 |

---

## 4. 各语言执行环境

### 语言支持矩阵

| 语言 | 基础镜像 | 编译工具 | 运行时 | 内存限制建议 |
|------|----------|----------|--------|--------------|
| Python | python:3.11-slim | - | python3 | 256MB |
| C/C++ | gcc:12-slim | gcc/g++ 12 | - | 256MB |
| Java | openjdk:17-slim | javac 17 | java 17 | 512MB |
| JavaScript | node:18-slim | - | node 18 | 256MB |
| Go | golang:1.20-slim | - | go 1.20 | 256MB |

### Dockerfile 示例 (Python 判题容器)

```dockerfile
FROM python:3.11-slim

# 安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -s /bin/bash judge
USER judge

WORKDIR /home/judge

CMD ["/bin/bash"]
```

---

## 5. 数据库设计考量

### PostgreSQL 表设计要点

1. **Users 表**: 存储用户基本信息，密码使用 bcrypt 哈希
2. **Problems 表**: 存储题目信息，描述字段使用 TEXT 类型（支持 Markdown）
3. **TestCases 表**: 测试用例，is_hidden 字段区分公开/隐藏用例
4. **Submissions 表**: 提交记录，status 字段存储评测状态
5. **Solutions 表**: 官方解法，content 字段存储 Markdown 格式讲解

### 索引设计

- problems: idx_difficulty, idx_tags (GIN 索引)
- submissions: idx_user_id, idx_problem_id, idx_status
- testcases: idx_problem_id

---

## 6. API 设计原则

### RESTful API 设计

- `/api/v1/problems` - 题目列表（支持分页、筛选）
- `/api/v1/problems/{id}` - 题目详情
- `/api/v1/submissions` - 提交列表
- `/api/v1/submissions` (POST) - 创建提交
- `/api/v1/submissions/{id}` - 提交详情
- `/api/v1/ws/judge` - WebSocket 判题状态

### 认证方案

- JWT Token 认证
- Access Token + Refresh Token 机制
- Token 存储在 Redis 中实现登出即失效
