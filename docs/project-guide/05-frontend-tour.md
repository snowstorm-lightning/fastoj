# 05. 前端导览

FastOJ 前端是 React + TypeScript + Vite。它不是多页面路由应用，而是在一个 App 里维护当前 view，并根据 view 渲染题库、工作台、图谱、认证、设置和管理后台。

## 前端结构总览

![前端状态和数据流](assets/frontend-flow.svg)

主入口在 [frontend/src/main.tsx:5590](../../frontend/src/main.tsx#L5590)，React root 在文件末尾创建。

## App 级状态

`App` 维护这些关键状态：

- `view`：当前页面，可能是 `library`、`workbench`、`graph`、`auth`、`settings`、`admin`。
- `selectedId`：当前题目 id。
- `locale`：当前界面语言，来自 `SUPPORTED_LOCALES`。
- `theme`：浅色或深色。
- `authenticated` 和 `currentUser`：登录状态和用户资料。

看 [frontend/src/main.tsx:5590](../../frontend/src/main.tsx#L5590)。`document.documentElement.lang` 由 `htmlLangForLocale` 设置，语言偏好会写 localStorage，并且登录后同步到账户。

## 国际化扩展点

长期扩展语言时，先改 [frontend/src/lib/i18n.ts:4](../../frontend/src/lib/i18n.ts#L4) 的 `LOCALE_META` 和文案表，而不是在组件里新增二分判断。关键规则：

- `SUPPORTED_LOCALES` 驱动设置页语言按钮和 starter 模板去重。
- `htmlLangForLocale` 驱动页面 `lang` 属性。
- `nextLocale` 驱动顶部快速切换按钮。
- `localeText` 和 `localeValue` 给 UI 文案和列表数据提供默认 locale 回退。
- 后端请求校验使用 [backend/core/locales.py:30](../../backend/core/locales.py#L30) 的 `validate_locale`，数据库旧值读取使用 `normalize_locale` 兜底。

## API client

API client 统一在 [frontend/src/lib/api.ts:438](../../frontend/src/lib/api.ts#L438)。它负责：

- 拼接 `API_BASE`。
- 附带 JWT。
- 解析 FastAPI 错误并做安全格式化。
- 用 Zod schema 校验重要响应。
- 提供问题、提交、AI、管理后台等方法。

提交入口和管理员导入入口都在这个 client 中；导入题目调用 [adminCreateProblemImport](../../frontend/src/lib/api.ts#L553)，WebSocket 创建在 [makeJudgeSocket](../../frontend/src/lib/api.ts#L818)。讨论区点赞/取消点赞只返回 `{ liked, like_count }` 这样的轻量结果，前端会把它合并回已有评论树，而不是把响应当作完整评论重新解析。

## 题库页

题库页入口：[frontend/src/main.tsx:577](../../frontend/src/main.tsx#L577)。

它做的事情：

- 调用 `api.problems` 获取题目。
- 支持关键词、难度、标签筛选。
- 支持卡片布局和传统 OJ 列表布局。
- 支持从训练图谱带 tag 回到题库。
- 用 `matchesLocalizedProblem` 支持中英文搜索。

本地化搜索入口：[frontend/src/lib/i18n.ts:580](../../frontend/src/lib/i18n.ts#L580)。

## 工作台是前端最重要的组件

`Workspace` 入口在 [frontend/src/main.tsx:1388](../../frontend/src/main.tsx#L1388)。它承担了刷题体验的核心状态：

- 当前代码。
- 当前语言。
- 当前 judge mode。
- AI 模型 profile。
- 左右面板宽度和打开状态。
- 当前提交和判题事件。
- public run cases。
- AI explain/review/hint/chat 状态。
- 当前题目和提交轨迹 query。

工作台顶部题目头部可以折叠。展开时展示练习台、题名、难度、标签、限制和最近结果；折叠后保留返回、题名、状态和展开按钮，把更多垂直空间留给代码区和运行结果。这个偏好写入 `fastoj.workbenchHeaderCollapsed`，和左右面板宽度、打开状态一样属于本地工作台布局偏好。

左侧详情 dock 是学习材料区，不只是样例列表。它包含公开用例、官方提示、题解、判题时间线、提交轨迹和讨论。这里的“官方提示”是题目固定内容，接近 LeetCode 的 hint；它不依赖当前代码，也不调用 AI。

工作台的基本数据流：

上图下半部分就是工作台的数据流：用户动作进入 `judge(runOnly)`，再经 `api.submit` 到后端；提交创建后，`connectStatus` 同时连接 WebSocket 和 polling fallback，最终更新 JudgeTimeline、RunResultPanel 和 AI panel。

提交动作在 [frontend/src/main.tsx:1632](../../frontend/src/main.tsx#L1632)，状态连接在 [frontend/src/main.tsx:1673](../../frontend/src/main.tsx#L1673)。

## WebSocket-first + polling fallback

前端不会只依赖 WebSocket。`connectStatus` 会同时：

1. 打开 WebSocket 接收 `pending`、`progress`、`result`。
2. 启动 interval polling 获取提交详情。
3. 如果 WebSocket 先收到 result，就停止 polling。
4. 如果 WebSocket 漏掉 result，polling 看到 `finished` 后补一个终态事件。

这让实时体验和最终一致性都更稳。

## RunResultPanel

`RunResultPanel` 展示公开运行输入、官方期望输出、用户实际输出和 diff。它只处理公开 run 的输入输出，不展示隐藏用例内容。自定义用例的删除控件在用例 tab 右上角，hover 或键盘聚焦时出现；重置使用回退箭头图标而不是文字 `R`。组件文件在 [frontend/src/components/RunResultPanel.tsx](../../frontend/src/components/RunResultPanel.tsx)，并通过 lazy component 按需加载。

## AI Copilot Panel

AI 面板组件在 [frontend/src/components/AICopilotPanel.tsx:39](../../frontend/src/components/AICopilotPanel.tsx#L39)，由 `Workspace` 右侧栏渲染。它依赖当前 `submission`，并通过这些函数调用后端：

- explain：[frontend/src/main.tsx:1727](../../frontend/src/main.tsx#L1727)
- review：[frontend/src/main.tsx:1752](../../frontend/src/main.tsx#L1752)
- hint：[frontend/src/main.tsx:1770](../../frontend/src/main.tsx#L1770)
- chat：[frontend/src/main.tsx:1788](../../frontend/src/main.tsx#L1788)

工作台会在新题目、新提交、语言变化时清理旧 AI 状态，避免旧提交的解释出现在新提交上。AI 面板里的“解释”和“审查”是提交结果相关操作：“解释”优先说明最近一次 verdict、错误原因和下一步；“审查”更像代码 review，关注算法、边界和复杂度风险。“轻提示 / 方向提示 / 重提示”收在 `AI 提示` 折叠区里，它们是基于当前题目、语言和代码动态生成的个性化提示，不等同于左侧题目详情里的固定官方提示。

## Function/ACM starter

前端负责给用户展示 starter code：

- 支持语言列表：[frontend/src/stores/useAppStore.ts:5](../../frontend/src/stores/useAppStore.ts#L5)
- 判断题目支持模式：[frontend/src/lib/problemModes.ts:706](../../frontend/src/lib/problemModes.ts#L706)
- 生成 starter：[frontend/src/lib/problemModes.ts:748](../../frontend/src/lib/problemModes.ts#L748)

前端只是改善用户体验，真正的 Function mode 判题仍由后端包装和 Docker 沙箱执行。

工作台工具栏还提供代码补全开关。它写入 `fastoj.completionEnabled`，并即时更新 Monaco quick suggestions、trigger-character suggestions、parameter hints 和 word-based suggestions；代码模板重置也使用同一套图标风格。

## AdminPage

管理后台入口在 [frontend/src/main.tsx:3514](../../frontend/src/main.tsx#L3514)。它覆盖：

- 用户与权限管理：账号列表、状态、角色、内容管理员权限和管理员重置密码。密码重置输入有显示/隐藏按钮，错误或成功反馈只显示在密码重置区域，避免全页提示挡住主要内容。
- 题目基础信息管理。
- 用例管理。
- 官方解法管理。
- AI 原创出题 Agent 草稿、校验、发布。
- 导入题目 Agent：来源链接、原始材料 textarea、适配要求、模式/语言/模型选择和导入为草稿。
- 导入草稿来源摘要：导入 chip、来源、原始材料长度、导入说明和管理员可折叠原文预览。

注意：前端是否显示 admin 页面不是安全边界。后端管理接口使用 `require_admin` 做服务端角色检查。

## 打包与懒加载

前端仍然是单入口状态驱动的 SPA，但重组件不会全部同步进入首屏 bundle。lazy component 声明在 [frontend/src/main.tsx:141](../../frontend/src/main.tsx#L141) 附近：

- `CodeEditor`：进入工作台编辑区时加载，Monaco 使用 ESM editor API、显式 `editor.worker` 和 FastOJ 支持语言贡献。
- `CodeBlock`：题解代码出现时加载，Shiki 使用 `shiki/core`，按实际语言动态加载 grammar 和 `github-dark` theme。
- `TrainingGraph`、`JudgeTimeline`、`AICopilotPanel`、`RunResultPanel`、`SubmissionTrail`、`AuthPage`、`SettingsPage`：按 view 或 tab 渲染时加载。

生产 build 的具体 chunk 大小会随功能变动。当前仍会看到 Vite 大 chunk 警告，主要来自 lazy-loaded Monaco editor API、Shiki 语言包和部分训练图谱资源；判断首屏体验时应结合懒加载边界，而不是只看单个 chunk 的警告。

## 代码导航

- React App：[frontend/src/main.tsx:5590](../../frontend/src/main.tsx#L5590)
- lazy component 声明：[frontend/src/main.tsx:141](../../frontend/src/main.tsx#L141)
- 题库页：[frontend/src/main.tsx:577](../../frontend/src/main.tsx#L577)
- 工作台：[frontend/src/main.tsx:1388](../../frontend/src/main.tsx#L1388)
- 提交动作：[frontend/src/main.tsx:1632](../../frontend/src/main.tsx#L1632)
- 状态连接：[frontend/src/main.tsx:1673](../../frontend/src/main.tsx#L1673)
- AI 面板：[frontend/src/components/AICopilotPanel.tsx:39](../../frontend/src/components/AICopilotPanel.tsx#L39)
- AdminPage：[frontend/src/main.tsx:3514](../../frontend/src/main.tsx#L3514)
- API client：[frontend/src/lib/api.ts:438](../../frontend/src/lib/api.ts#L438)
- WebSocket 创建：[frontend/src/lib/api.ts:818](../../frontend/src/lib/api.ts#L818)
- starter 生成：[frontend/src/lib/problemModes.ts:748](../../frontend/src/lib/problemModes.ts#L748)
- locale registry：[frontend/src/lib/i18n.ts:4](../../frontend/src/lib/i18n.ts#L4)
- locale fallback helpers：[frontend/src/lib/i18n.ts:52](../../frontend/src/lib/i18n.ts#L52)

## 讲解口径

讲前端时不要只说 “React”。更好的说法是：

The frontend is organized around the learner workflow. The workbench owns the active problem, language, judge mode, code draft, run cases, submission state, WebSocket events, polling fallback, and AI panel state. Static learning material lives in the statement/detail dock, while personalized AI help lives in the copilot panel. TanStack Query handles server data like problems, solutions, profiles, and submission history, while local UI preferences such as theme, panel sizes, collapsible header state, drafts, and locale are stored locally or synced to the user profile.
