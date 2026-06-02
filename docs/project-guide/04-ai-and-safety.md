# 04. AI 接入与安全边界

FastOJ 的 AI 不是简单把数据库里的所有信息发给模型。它的核心设计是：AI 可以帮助解释、提示、审查和出题，但不能看到隐藏用例内容，也不能把完整答案直接交给用户。

## AI 能做什么

当前 AI 能力主要有两类：

1. 学习者侧：
   - 提交解释：为什么失败、可能原因、下一步建议。
   - 代码审查：复杂度、边界风险、I/O 格式问题。
   - 渐进提示：按 level 给提示。
   - 对话：围绕当前提交上下文继续问。
2. 管理员侧：
   - 生成题目草稿。
   - 生成多语言官方解法。
   - 校验草稿和用例。
   - 自动修复 validation failed 的草稿，但隐藏内容仍会被过滤。

AI API 路由在 [backend/api/ai.py:21](../../backend/api/ai.py#L21)，业务逻辑在 [backend/ai/service.py:25](../../backend/ai/service.py#L25)。

## Provider profile

FastOJ 使用 OpenAI-compatible provider 抽象，不把某一家模型服务写死在业务里。前端通过 `GET /api/v1/ai/profiles` 获取可用 profile，普通用户只看到可用模型，管理员可以看到不可用原因摘要。

入口：

- AI profiles API：[backend/api/ai.py:25](../../backend/api/ai.py#L25)
- 服务初始化选择 profile：[backend/ai/service.py:25](../../backend/ai/service.py#L25)
- AI 配置字段：[backend/core/config.py:50](../../backend/core/config.py#L50)
- AI 响应语言映射：[backend/core/locales.py:36](../../backend/core/locales.py#L36)

## 安全上下文：什么能给 AI，什么不能

![AI 安全上下文边界](assets/ai-safety.svg)

AIService 构造提交上下文时只遍历公开 testcase result。隐藏 result 只会影响 `hidden_failure_notice`，不会带输入输出内容。看 [backend/ai/service.py:112](../../backend/ai/service.py#L112) 和 [backend/ai/service.py:132](../../backend/ai/service.py#L132)。

用户代码和问题文本还会经过 secret redaction，入口在 [backend/ai/service.py:287](../../backend/ai/service.py#L287)。

## 提示和解释的约束

`AIService` 对不同能力设置了不同规则：

- explain/review 使用当前提交上下文。
- hint 使用题目上下文、语言和当前代码，但不使用隐藏用例。
- chat 明确加规则：只使用公开 testcase details、不暴露隐藏用例、不返回完整 AC 解法。

chat 的 rules 在 [backend/ai/service.py:61](../../backend/ai/service.py#L61)，hint 的 rules 在 [backend/ai/service.py:89](../../backend/ai/service.py#L89)。

即使模型返回字段不稳定，AIService 也会做 schema 兼容和兜底解析，例如 `_parse_explain`、`_parse_review`、`_parse_chat`，避免前端直接渲染不可控结构。

## 出题 Agent 流程

管理员出题 Agent 是一个“生成、校验、修复、入库”的闭环：

![管理员出题 Agent 流程](assets/agent-flow.svg)

关键代码：

- 最大修复次数：[backend/services/problem_authoring_agent.py:36](../../backend/services/problem_authoring_agent.py#L36)
- 草稿校验器：[backend/services/problem_authoring_agent.py:95](../../backend/services/problem_authoring_agent.py#L95)
- 创建草稿流程：[backend/services/problem_authoring_agent.py:353](../../backend/services/problem_authoring_agent.py#L353)
- 批准草稿发布正式题目：[backend/services/problem_authoring_agent.py:500](../../backend/services/problem_authoring_agent.py#L500)

## Agent 修复为什么安全

草稿校验失败后，Agent 可能把失败摘要发回模型要求修复。但它不会把上一版隐藏用例内容原样发回。`_validation_repair_context` 会：

- 收集隐藏用例中的较长敏感值。
- 对题面、解法、解释、validation notes 做替换。
- 只保留公开样例内容。
- 对隐藏用例只给数量和聚合 case summary。

入口：[backend/services/problem_authoring_agent.py:1201](../../backend/services/problem_authoring_agent.py#L1201)。

## 隐藏用例的三道防线

1. **判题写库时隐藏内容不写到结果表**：见 [backend/worker/tasks/judge_task.py:216](../../backend/worker/tasks/judge_task.py#L216)。
2. **普通提交详情过滤隐藏结果**：见 [backend/api/submissions/__init__.py:83](../../backend/api/submissions/__init__.py#L83)。
3. **AI 上下文只加入公开 result**：见 [backend/ai/service.py:112](../../backend/ai/service.py#L112)。

这三层分别保护数据库结果、API 响应和外部 AI provider。

## 常见追问

**如果模型返回完整答案怎么办？**

服务端响应 schema 中保留 `full_solution_revealed` 这类安全标记，并且解析时会强制置为 false。产品层也把 AI 定位成提示和解释，而不是直接生成完整答案给普通用户。

**如果隐藏用例失败，AI 怎么帮助用户？**

AI 不知道隐藏输入输出，只知道有隐藏用例失败。它可以基于题面、代码、公开用例和 verdict 提醒常见边界类别，比如空数组、重复值、极限大小、格式问题。

**管理员能看到隐藏用例，是否会泄露到 AI？**

管理员 API 可以管理隐藏用例，但出题 Agent 的修复上下文和普通 AI 解释上下文都做了隐藏内容省略或 redaction。管理员 UI 不是安全边界，服务端检查才是安全边界。

## 代码导航

- AI API：[backend/api/ai.py:21](../../backend/api/ai.py#L21)
- AIService：[backend/ai/service.py:25](../../backend/ai/service.py#L25)
- Locale registry：[backend/core/locales.py:5](../../backend/core/locales.py#L5)
- 提交安全上下文：[backend/ai/service.py:112](../../backend/ai/service.py#L112)
- 隐藏失败摘要：[backend/ai/service.py:132](../../backend/ai/service.py#L132)
- secret redaction：[backend/ai/service.py:287](../../backend/ai/service.py#L287)
- 出题 Agent：[backend/services/problem_authoring_agent.py:353](../../backend/services/problem_authoring_agent.py#L353)
- Agent 修复上下文：[backend/services/problem_authoring_agent.py:1201](../../backend/services/problem_authoring_agent.py#L1201)
- Admin Agent API：[backend/api/admin_agent.py:25](../../backend/api/admin_agent.py#L25)
