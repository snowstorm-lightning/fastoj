# API Contracts: FastOJ 后端接口定义

**Created**: 2026-03-16
**Feature**: 面向面试者的 OJ 平台

---

## 1. API 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **Content-Type**: `application/json`
- **响应格式**: 统一 JSON 响应

### 通用响应格式

```json
// 成功响应
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}

// 分页响应
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 2. 用户接口

### 2.1 用户注册

**POST** `/auth/register`

Request:
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string (min 8 chars)"
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "user@example.com",
    "created_at": "2026-03-16T10:00:00Z"
  },
  "message": "注册成功"
}
```

### 2.2 用户登录

**POST** `/auth/login`

Request:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

Response (200):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

## 3. 题目接口

### 3.1 获取题目列表

**GET** `/problems`

Query Parameters:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |
| difficulty | string | 否 | 难度筛选 (easy/medium/hard) |
| tags | string | 否 | 标签筛选，逗号分隔 |
| keyword | string | 否 | 关键词搜索 |
| sort | string | 否 | 排序字段 (created_at/ac_rate/difficulty) |
| order | string | 否 | 排序方向 (asc/desc) |

Response (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "两数之和",
      "slug": "two-sum",
      "difficulty": "easy",
      "tags": ["数组", "哈希表"],
      "total_submissions": 1000,
      "accepted_submissions": 800,
      "ac_rate": 0.8,
      "is_public": true,
      "created_at": "2026-03-16T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 500,
    "total_pages": 25
  }
}
```

### 3.2 获取题目详情

**GET** `/problems/{problem_id}`

Response (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "两数之和",
    "slug": "two-sum",
    "description": "## 题目描述\n\n给定一个整数数组 nums ...",
    "difficulty": "easy",
    "tags": ["数组", "哈希表"],
    "time_limit": 1000,
    "memory_limit": 256,
    "hint": "使用哈希表可以做到 O(n) 时间复杂度",
    "total_submissions": 1000,
    "accepted_submissions": 800,
    "ac_rate": 0.8,
    "sample_testcases": [
      {
        "input": "[2,7,11,15], 9",
        "output": "[0,1]"
      }
    ],
    "created_at": "2026-03-16T10:00:00Z"
  }
}
```

### 3.3 获取题目官方解法

**GET** `/problems/{problem_id}/solutions`

Query Parameters:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| language | string | 否 | 语言筛选 |

Response (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "language": "python",
      "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        ...",
      "explanation": "## 解题思路\n\n使用哈希表...",
      "time_complexity": "O(n)",
      "space_complexity": "O(n)"
    }
  ]
}
```

---

## 4. 提交接口

### 4.1 创建提交

**POST** `/submissions`

Request:
```json
{
  "problem_id": "uuid",
  "code": "class Solution:\n    def twoSum(self, nums, target):\n        ...",
  "language": "python"
}
```

Response (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "problem_id": "uuid",
    "user_id": "uuid",
    "code": "...",
    "language": "python",
    "status": "pending",
    "result": null,
    "created_at": "2026-03-16T10:00:00Z"
  },
  "message": "提交成功"
}
```

### 4.2 获取提交详情

**GET** `/submissions/{submission_id}`

Response (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "problem_id": "uuid",
    "user_id": "uuid",
    "code": "...",
    "language": "python",
    "status": "finished",
    "result": "ac",
    "execute_time": 45,
    "memory_used": 12345,
    "score": 100,
    "testcase_results": [
      {
        "testcase_id": "uuid",
        "status": "ac",
        "input": "...",
        "expected_output": "...",
        "actual_output": "...",
        "execute_time": 10,
        "memory_used": 1234,
        "is_hidden": false
      }
    ],
    "created_at": "2026-03-16T10:00:00Z",
    "finished_at": "2026-03-16T10:00:01Z"
  }
}
```

**注意**: `testcase_results` 中的隐藏用例详情不会返回给客户端

### 4.3 获取用户提交列表

**GET** `/submissions`

Query Parameters:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |
| problem_id | uuid | 否 | 题目筛选 |
| language | string | 否 | 语言筛选 |
| result | string | 否 | 结果筛选 |
| status | string | 否 | 状态筛选 |

Response (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "problem": {
        "id": "uuid",
        "title": "两数之和",
        "slug": "two-sum"
      },
      "language": "python",
      "status": "finished",
      "result": "ac",
      "score": 100,
      "execute_time": 45,
      "created_at": "2026-03-16T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 5. WebSocket 接口

### 5.1 判题状态推送

**WebSocket** `/ws/judge/{submission_id}`

连接 URL: `ws://localhost:8000/ws/judge/{submission_id}?token={jwt_token}`

消息格式 (Server -> Client):

```json
// 状态变更消息
{
  "type": "status_update",
  "data": {
    "submission_id": "uuid",
    "status": "judging",
    "progress": 50,
    "current_testcase": 5,
    "total_testcases": 10
  }
}

// 判题完成消息
{
  "type": "result",
  "data": {
    "submission_id": "uuid",
    "status": "finished",
    "result": "ac",
    "execute_time": 45,
    "memory_used": 12345,
    "score": 100
  }
}

// 错误消息
{
  "type": "error",
  "data": {
    "message": "判题服务异常",
    "code": "JUDGE_ERROR"
  }
}
```

---

## 6. 错误码定义

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| VALIDATION_ERROR | 422 | 参数验证失败 |
| RATE_LIMIT | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

### 详细错误码

| 错误码 | 说明 |
|--------|------|
| PROBLEM_NOT_FOUND | 题目不存在 |
| SUBMISSION_NOT_FOUND | 提交不存在 |
| LANGUAGE_NOT_SUPPORTED | 不支持的编程语言 |
| CODE_TOO_LONG | 代码超过长度限制 |
| JUDGE_TIMEOUT | 判题超时 |
| JUDGE_ERROR | 判题服务异常 |
| COMPILATION_ERROR | 编译错误 |

---

## 7. 认证说明

### 请求头

```
Authorization: Bearer <access_token>
```

### Token 刷新

**POST** `/auth/refresh`

Request:
```json
{
  "refresh_token": "string"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "expires_in": 3600
  }
}
```
