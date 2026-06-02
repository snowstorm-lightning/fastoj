# 02. 判题链路深度讲解

判题链路是 FastOJ 最核心、最值得在项目讲解中展开的部分。你需要能从前端按钮一路讲到 Docker 容器执行，再讲回数据库和 WebSocket。

第一次读这篇时，先记住五个关键词：`Submission` 是一次判题请求，`TestCaseResult` 是每个用例的结果，Redis Stream message 是异步任务，worker heartbeat 表示是否有判题服务在线，active task marker 用来排障当前卡住的任务。

## 一次 Run 或 Submit 的完整时序

![Run / Submit 判题链路](assets/judge-pipeline.svg)

## Run 和 Submit 的区别

前端工作台里的两个按钮不是同一个语义：

- **Run**：调用 `/api/v1/submissions/run`，只使用公开样例或用户编辑的公开运行输入，不触碰隐藏用例。
- **Submit**：调用 `/api/v1/submissions`，使用正式用例集合。公开用例失败时会提前停止，隐藏用例结果只给聚合状态，不返回隐藏内容。

API 路由分别在 [backend/api/submissions/run.py:13](../../backend/api/submissions/run.py#L13) 和 [backend/api/submissions/__init__.py:21](../../backend/api/submissions/__init__.py#L21)。

## SubmissionService：业务入口

`SubmissionService` 做四件事：

1. 校验语言、题目是否存在、私有题目权限。
2. Function mode 时把用户函数包装成可执行程序。
3. 创建 `Submission` 数据库记录，初始状态为 `pending`。
4. 按环境策略决定进入 Redis 队列还是开发期 inline 判题。

关键代码：

- 创建正式提交：[backend/services/submission_service.py:33](../../backend/services/submission_service.py#L33)
- 创建公开运行：[backend/services/submission_service.py:80](../../backend/services/submission_service.py#L80)
- Function mode 包装：[backend/services/submission_service.py:126](../../backend/services/submission_service.py#L126)
- 队列或 inline 判题选择：[backend/services/submission_service.py:136](../../backend/services/submission_service.py#L136)

`SubmissionService` 里有一个重要生产边界：inline judge 只在 `DEBUG=true` 或显式 `JUDGE_INLINE_FALLBACK=true` 时允许。`DEBUG=false` 时必须走 Redis Worker；如果没有 live worker heartbeat、Redis 不可用，或入队失败，提交 API 返回 `503 Judge service unavailable`，不会让 FastAPI API 进程承担判题负载。判断和策略入口看 [backend/services/submission_service.py:136](../../backend/services/submission_service.py#L136)。

## QueueService：Redis Streams 核心

当前打开的文件 [backend/services/queue_service.py](../../backend/services/queue_service.py) 是异步判题的队列抽象。它不是一个简单 list queue，而是基于 Redis Streams：

![QueueService Redis Streams 设计](assets/queue-service.svg)

### 连接和命名

`QueueService.__init__` 从 settings 读取 stream、consumer group、dead-letter stream、status channel，并用 hostname 生成 consumer name。看 [backend/services/queue_service.py:16](../../backend/services/queue_service.py#L16)。

### Worker heartbeat

Heartbeat 用来判断是否有活着的判题 Worker：

- 写入 heartbeat：[backend/services/queue_service.py:44](../../backend/services/queue_service.py#L44)
- 扫描是否有活 Worker：[backend/services/queue_service.py:58](../../backend/services/queue_service.py#L58)

API 在生产策略下用 heartbeat 做提交前检查：没有 live worker 时直接拒绝提交。开发调试时可以通过 `DEBUG=true` 或 `JUDGE_INLINE_FALLBACK=true` 允许 inline fallback。Worker 进程用后台 heartbeat 线程持续续期，避免长时间判题时 heartbeat 过期造成误判。

### active task marker

Worker parent 在启动 judge child 前会写一个短 TTL 的 active task key，内容包括 consumer、message id、submission id、开始时间、最近进度时间、deadline 和 progress。Child 每次发布 testcase progress 时顺手刷新这个 marker；刷新失败只记 warning，不影响判题。这个 marker 不是抢占依据，也不是安全边界，主要用于排障“某个 worker 当前卡在哪个 submission”。

相关方法在 [QueueService](../../backend/services/queue_service.py)：`mark_task_active`、`touch_active_task`、`clear_task_active` 和 `get_active_task`。

### 入队

入队在 [backend/services/queue_service.py:116](../../backend/services/queue_service.py#L116)：

- `task_data.setdefault("attempt", 0)` 初始化重试次数。
- `ensure_group()` 确保 consumer group 存在。
- `xadd(queue_name, {"payload": json.dumps(task_data)})` 写入 stream。
- `publish_status` 和 `xadd` 已解耦：只要 `xadd` 成功，就不再因为状态发布失败而 inline 重复判题。

### 出队

出队在 [backend/services/queue_service.py:134](../../backend/services/queue_service.py#L134)：

- 使用 `xreadgroup`。
- group 是 `judge-workers`。
- consumer 是当前 Worker hostname。
- stream id 用 `>`，表示读取尚未投递给任何 consumer 的新消息。

### ack、retry 和 dead-letter

正常完成后调用 [ack_task](../../backend/services/queue_service.py#L151)。

异常时调用 [retry_or_dead_letter](../../backend/services/queue_service.py#L155)：

- 增加 `attempt`。
- 没超过最大重试次数时重新 `xadd` 回主 stream。
- 达到最大重试次数时写入 dead-letter stream。
- retry/dead-letter 使用 Redis Lua 脚本原子化处理：只有原消息 `XACK` 成功时才 `XADD` 新 retry/dead-letter 消息；如果原消息已经被 child 或其他恢复路径 ACK，parent 不再追加重复 retry，也不覆盖提交状态。

### pending reclaim

[claim_pending](../../backend/services/queue_service.py#L190) 用来把长时间 idle 的 pending 消息 claim 给当前 consumer，并把 claim 到的 payload 送回 Worker 处理。它会跳过仍有 heartbeat 的其他 consumer，避免抢正在长时间判题的活跃 Worker。

### 状态发布

[publish_status](../../backend/services/queue_service.py#L244) 统一发布提交状态。消息结构固定为：

```text
type: pending | judging | progress | result | error
submission_id: 当前提交
data: 状态详情
```

API 启动时的 relay 会订阅 `judge:status` 并广播给对应 WebSocket 连接，代码在 [backend/api/websocket/status_relay.py:13](../../backend/api/websocket/status_relay.py#L13)。

## Worker：消费和状态更新

Worker 进程分成 parent 和 judge child 两层：

- Parent 在 [backend/worker/judge_worker.py](../../backend/worker/judge_worker.py) 中负责 heartbeat、pending reclaim、从 Redis 取任务、写 active task marker、启动 child、等待 hard timeout、清理 marker，并在 hard-kill 后按 submission/message 标签清理可能残留的 Docker judge 容器。
- Child 每次只处理一个 task，入口重新创建 [JudgeTaskConsumer](../../backend/worker/tasks/consumer.py#L111)，执行 Docker 判题、写数据库、发布状态，并在成功或内部异常处理后 ACK / retry / dead-letter。

这种设计的目的不是替代 Docker sandbox，而是避免 parent 卡在 Docker API、`container.exec_run()`、数据库调用或其他阻塞 I/O 时，Redis heartbeat 仍然显示 worker 存活而任务长期留在 judging。

Parent 检测到 child 超过 `JUDGE_TASK_HARD_TIMEOUT_SECONDS` 时，会先 `terminate`，等待 `JUDGE_CHILD_TERMINATE_GRACE_SECONDS`，仍未退出则 `kill`，然后清理当前 task 标签匹配的残留 Docker 容器，并复用 consumer 的 `handle_task_failure` 做 retry/dead-letter 和状态发布。Child 崩溃或 spawn/start 失败但 parent 还活着时也走同一套失败处理。Parent 自己崩溃时 heartbeat 消失，原消息留在 Redis pending，后续由 `claim_pending` 接管。

`JudgeTaskConsumer.process_task` 的职责：

1. 读取任务中的 `submission_id`。
2. 从 DB 加载提交。
3. 如果提交已经完成并有结果，ack 掉重复任务。
4. 标记提交为 `judging`。
5. 调用 `JudgeTask.execute`。
6. 写入最终状态。
7. 发布 `result` 事件。
8. ack 原 stream message。
9. 如果 Worker 异常且还有重试次数，任务重新入队，submission 回到 `pending`；达到最终重试才写 `SE` 和 dead-letter。

重复任务保护有两层：如果 submission 已经 `finished` 且已有 testcase results，consumer 直接 ACK；如果 submission 还没 finished 但已有 testcase results，`JudgeTask` 会从已持久化结果汇总 verdict，不再重复写 result rows。数据库层还没有 `unique(submission_id, testcase_id)` 约束，后续如果引入 Alembic migration，可以把这个约束作为更强的幂等保护。

关键入口：[backend/worker/judge_worker.py](../../backend/worker/judge_worker.py)、[backend/worker/tasks/consumer.py](../../backend/worker/tasks/consumer.py)。

## JudgeTask：执行测试用例

[JudgeTask.execute](../../backend/worker/tasks/judge_task.py#L127) 做的是判题语义，不负责队列：

- 加载 Problem。
- 按 Run/Submit 选择公开用例、全部用例或用户自定义公开运行输入。
- 对每个 testcase 调 `SandboxExecutor.execute`。
- 比较实际输出和期望输出。
- 写 `TestCaseResult`。
- 发布 progress。
- 汇总最终 verdict。

隐藏用例保护发生在写结果时：隐藏用例的 `input`、`expected_output`、`actual_output` 都写成 `None`，看 [backend/worker/tasks/judge_task.py:219](../../backend/worker/tasks/judge_task.py#L219)。

## SandboxExecutor：Docker-first 执行

[SandboxExecutor.execute](../../backend/sandbox/executor.py#L92) 先判断语言是否支持，再优先走 Docker。Docker 执行入口是 [backend/sandbox/executor.py:149](../../backend/sandbox/executor.py#L149)。

关键安全参数：

- 禁用网络：[backend/sandbox/executor.py:186](../../backend/sandbox/executor.py#L186)
- 限制进程数：[backend/sandbox/executor.py:187](../../backend/sandbox/executor.py#L187)
- 丢弃 Linux capabilities：[backend/sandbox/executor.py:188](../../backend/sandbox/executor.py#L188)
- no-new-privileges：[backend/sandbox/executor.py:189](../../backend/sandbox/executor.py#L189)
- 非 root 用户运行：[backend/sandbox/executor.py:192](../../backend/sandbox/executor.py#L192)
- 输出截断：[backend/sandbox/executor.py:261](../../backend/sandbox/executor.py#L261)

生产约束是 Docker-first。只有显式打开 `FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION` 才可能走宿主机 subprocess fallback，默认关闭，配置见 [backend/core/config.py:53](../../backend/core/config.py#L53)。

## 前端如何接收结果

工作台提交入口是 [frontend/src/main.tsx:1456](../../frontend/src/main.tsx#L1456)。提交创建成功后调用 [connectStatus](../../frontend/src/main.tsx#L1497)：

- 优先创建 WebSocket：[frontend/src/lib/api.ts:564](../../frontend/src/lib/api.ts#L564)
- 同时启动轮询，每 1.6 秒拉取提交详情。
- WebSocket 收到 result 后停止轮询。
- 如果 WebSocket 丢事件，轮询看到 finished 会补一个 terminal event。

这个设计让用户体验实时，但最终状态不完全依赖 WebSocket。

## 常见追问

**为什么用 Redis Streams，不用 Redis list？**

Streams 有 consumer group、ack、pending、claim、message id 和 dead-letter 设计空间，更适合多个 Worker 并发消费和失败恢复。

**Worker 崩了怎么办？**

如果是 judge child 卡死或崩溃，parent 会在 hard timeout 后终止 child，并把任务 retry 或 dead-letter。如果 parent 整个进程崩了，未 ack 的消息会留在 pending 里，`claim_pending` 可以把 idle 太久、且 owner heartbeat 已失效的消息 claim 给当前 consumer。真正生产化还要加队列仪表盘、active task 页面和 dead-letter 告警。

**隐藏用例会不会通过 WebSocket 泄露？**

不会。JudgeTask 存储隐藏结果时不保存输入、期望和实际输出；WebSocket progress 对 full submit 的隐藏阶段也只发聚合进度，不发 case 内容。

## 代码导航

- Run API：[backend/api/submissions/run.py:13](../../backend/api/submissions/run.py#L13)
- Submit API：[backend/api/submissions/__init__.py:21](../../backend/api/submissions/__init__.py#L21)
- 提交服务：[backend/services/submission_service.py:33](../../backend/services/submission_service.py#L33)
- 队列服务：[backend/services/queue_service.py:15](../../backend/services/queue_service.py#L15)
- 入队：[backend/services/queue_service.py:116](../../backend/services/queue_service.py#L116)
- 出队：[backend/services/queue_service.py:134](../../backend/services/queue_service.py#L134)
- retry/dead-letter：[backend/services/queue_service.py:155](../../backend/services/queue_service.py#L155)
- Worker parent：[backend/worker/judge_worker.py](../../backend/worker/judge_worker.py)
- Worker 消费：[backend/worker/tasks/consumer.py:111](../../backend/worker/tasks/consumer.py#L111)
- 判题执行：[backend/worker/tasks/judge_task.py:127](../../backend/worker/tasks/judge_task.py#L127)
- Docker 沙箱：[backend/sandbox/executor.py:149](../../backend/sandbox/executor.py#L149)
- 前端提交：[frontend/src/main.tsx:1456](../../frontend/src/main.tsx#L1456)
