# Data Model: FastOJ 核心数据模型

**Created**: 2026-03-16
**Feature**: 面向面试者的 OJ 平台

## 1. 实体关系图

```
┌──────────────┐       ┌──────────────┐
│    Users     │       │   Problems   │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ username     │       │ title        │
│ email        │       │ description  │
│ password_hash│       │ difficulty   │
│ created_at   │       │ time_limit   │
│ updated_at   │       │ memory_limit │
└──────────────┘       │ created_at   │
        │              └──────┬─────────┘
        │                     │
        │              ┌──────┴─────────┐
        │              │                │
┌───────┴───────┐    ┌▼──────────────┐ ┌───────────────┐
│  Submissions  │    │  TestCases    │ │   Solutions   │
├───────────────┤    ├───────────────┤ ├───────────────┤
│ id (PK)       │    │ id (PK)       │ │ id (PK)       │
│ user_id (FK)  │───▶│ problem_id(FK) │◀│ problem_id(FK) │
│ problem_id(FK)│    │ input         │ │ language      │
│ code          │    │ output        │ │ code          │
│ language      │    │ is_hidden     │ │ explanation   │
│ status        │    │ is_sample     │ │ created_at    │
│ result        │    │ score         │ └───────────────┘
│ error_message │    └───────────────┘
│ execute_time  │
│ memory_used   │
│ created_at    │
└───────────────┘
```

---

## 2. 数据库表定义

### 2.1 Users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 用户唯一标识 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希密码 |
| avatar_url | VARCHAR(500) | NULLABLE | 头像 URL |
| role | ENUM('user', 'admin') | DEFAULT 'user' | 用户角色 |
| is_active | BOOLEAN | DEFAULT TRUE | 账户状态 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `idx_users_email` ON users(email)
- `idx_users_username` ON users(username)

---

### 2.2 Problems 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 题目唯一标识 |
| title | VARCHAR(200) | NOT NULL | 题目标题 |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL 友好标识 |
| description | TEXT | NOT NULL | 题目描述 (Markdown) |
| difficulty | ENUM('easy', 'medium', 'hard') | NOT NULL | 难度等级 |
| time_limit | INTEGER | NOT NULL, DEFAULT 1000 | 时间限制 (ms) |
| memory_limit | INTEGER | NOT NULL, DEFAULT 256 | 内存限制 (MB) |
| total_submissions | INTEGER | DEFAULT 0 | 总提交数 |
| accepted_submissions | INTEGER | DEFAULT 0 | 通过数 |
| tags | ARRAY(VARCHAR(50)) | NOT NULL | 标签数组 |
| hint | TEXT | NULLABLE | 提示 (Markdown) |
| source | VARCHAR(200) | NULLABLE | 题目来源 |
| is_public | BOOLEAN | DEFAULT TRUE | 是否公开 |
| created_by | UUID | FK -> users(id) | 创建者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `idx_problems_difficulty` ON problems(difficulty)
- `idx_problems_tags` ON problems USING GIN(tags) (GIN 索引)
- `idx_problems_slug` ON problems(slug)

---

### 2.3 TestCases 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 测试用例唯一标识 |
| problem_id | UUID | FK -> problems(id), NOT NULL | 所属题目 |
| input | TEXT | NOT NULL | 输入数据 |
| output | TEXT | NOT NULL | 输出数据 |
| is_hidden | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否隐藏 |
| is_sample | BOOLEAN | NOT NULL DEFAULT FALSE | 是否为样例 |
| score | INTEGER | NOT NULL DEFAULT 10 | 分值 |
| order | INTEGER | NOT NULL DEFAULT 0 | 排序顺序 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `idx_testcases_problem` ON testcases(problem_id)

**说明**:
- 公开用例: `is_hidden = FALSE`，用户可在题目描述中看到
- 隐藏用例: `is_hidden = TRUE`，仅用于最终评测
- 样例: `is_sample = TRUE`，显示在题目描述中

---

### 2.4 Submissions 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 提交唯一标识 |
| user_id | UUID | FK -> users(id), NOT NULL | 提交用户 |
| problem_id | UUID | FK -> problems(id), NOT NULL | 所属题目 |
| code | TEXT | NOT NULL | 提交代码 |
| language | VARCHAR(20) | NOT NULL | 编程语言 |
| status | ENUM('pending', 'judging', 'finished') | NOT NULL | 评测状态 |
| result | ENUM('ac', 'wa', 'tle', 'mle', 'ce', 're', 'se', NULL) | NULLABLE | 评测结果 |
| error_message | TEXT | NULLABLE | 错误信息 |
| execute_time | INTEGER | NULLABLE | 执行时间 (ms) |
| memory_used | INTEGER | NULLABLE | 内存使用 (KB) |
| score | INTEGER | NOT NULL DEFAULT 0 | 得分 |
| ip_address | VARCHAR(45) | NULLABLE | 提交 IP |
| judge_version | VARCHAR(20) | NOT NULL | 判题版本 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| finished_at | TIMESTAMP | NULLABLE | 完成时间 |

**索引**:
- `idx_submissions_user` ON submissions(user_id)
- `idx_submissions_problem` ON submissions(problem_id)
- `idx_submissions_status` ON submissions(status)
- `idx_submissions_created` ON submissions(created_at DESC)

**评测状态流转**:
```
pending -> judging -> finished
              ↓
           (result: ac/wa/tle/mle/ce/re/se)
```

---

### 2.5 Solutions 表 (官方解法)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 解法唯一标识 |
| problem_id | UUID | FK -> problems(id), NOT NULL | 所属题目 |
| language | VARCHAR(20) | NOT NULL | 编程语言 |
| code | TEXT | NOT NULL | 解法代码 |
| explanation | TEXT | NOT NULL | 详细讲解 (Markdown) |
| time_complexity | VARCHAR(50) | NULLABLE | 时间复杂度 |
| space_complexity | VARCHAR(50) | NULLABLE | 空间复杂度 |
| is_official | BOOLEAN | NOT NULL DEFAULT TRUE | 是否官方 |
| created_by | UUID | FK -> users(id) | 创建者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `idx_solutions_problem` ON solutions(problem_id, language) UNIQUE

---

### 2.6 Tags 表 (可选，用于标签管理)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 标签唯一标识 |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 标签名称 |
| slug | VARCHAR(50) | UNIQUE, NOT NULL | 标签别名 |
| color | VARCHAR(7) | NOT NULL | 颜色代码 |
| description | TEXT | NULLABLE | 描述 |
| problem_count | INTEGER | DEFAULT 0 | 使用次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

---

## 3. 验证规则

### Problem 验证

- title: 1-200 字符，非空
- slug: 1-200 字符，小写字母、数字、连字符
- description: 最小 10 字符
- time_limit: 100-10000 ms
- memory_limit: 64-1024 MB
- tags: 最多 5 个，每个 1-50 字符

### Submission 验证

- code: 最大 65536 字符 (64KB)
- language: 必须是支持的 5 种语言之一
- user_id + problem_id 组合必须有对应权限

### TestCase 验证

- input/output: 最大 10240 字符 (10KB)
- 每个 problem 至少 1 个公开用例
- 每个 problem 至少 3 个隐藏用例

---

## 4. 状态枚举定义

### Difficulty

```python
class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
```

### SubmissionStatus

```python
class SubmissionStatus(str, Enum):
    PENDING = "pending"      # 等待中
    JUDGING = "judging"      # 判题中
    FINISHED = "finished"    # 已完成
```

### SubmissionResult

```python
class SubmissionResult(str, Enum):
    AC = "ac"       # Accepted - 通过
    WA = "wa"       # Wrong Answer - 答案错误
    TLE = "tle"     # Time Limit Exceeded - 超时
    MLE = "mle"     # Memory Limit Exceeded - 内存超限
    CE = "ce"       # Compile Error - 编译错误
    RE = "re"       # Runtime Error - 运行时错误
    SE = "se"       # System Error - 系统错误
```

### Language

```python
class Language(str, Enum):
    PYTHON = "python"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GOLANG = "golang"
```
