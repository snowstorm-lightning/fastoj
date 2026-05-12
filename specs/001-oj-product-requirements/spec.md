# Feature Specification: 面向面试者的 OJ 平台产品需求定义

**Feature Branch**: `001-oj-product-requirements`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "请基于宪法（Constitution），详细定义这个面向面试者的 OJ 平台的产品需求。必须包含以下核心场景：1. 核心页面规划：题目大厅支持按标签和难度筛选与分页；刷题工作台左右分屏，左侧题目描述+官方最优解(Markdown)，右侧Monaco Editor+终端输出。2. 评测生命周期：支持5种语言，状态流转Pending->Judging->AC/WA/TLE/MLE/CE。3. 测试用例管理：公开用例+隐藏用例"

## Clarifications

### Session 2026-03-16

- Q: Authentication & Authorization model → A: JWT-based auth with roles (user/admin)
- Q: Rate limiting for API/submissions → A: Token bucket via Redis: 10 sub/min per user
- Q: Observability (logging, metrics, tracing) → A: Structured JSON logging + basic metrics (requests, judge tasks, errors)
- Q: Out-of-scope boundaries → A: Single problem practice only (no contests, ranking, or problem editor)
- Q: Reliability & availability target → A: 99.5% uptime (11h downtime/month)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 浏览与筛选题目 (Priority: P1)

作为面试者，我希望能够浏览所有算法题目，并按标签和难度进行筛选，以便高效地找到适合我当前水平的练习题目。

**Why this priority**: 题目浏览与筛选是用户进入平台后的首要行为，是整个OJ平台的核心入口

**Independent Test**: 用户进入题目大厅后，可以看到题目列表，并能成功应用标签和难度筛选条件，系统返回符合条件的结果

**Acceptance Scenarios**:

1. **Given** 用户打开题目大厅页面，**When** 页面加载完成，**Then** 显示题目列表（默认按最新/难度排序），每页展示20道题目

2. **Given** 题目列表已加载，**When** 用户点击"数组"标签筛选条件，**Then** 页面更新仅显示带有"数组"标签的题目

3. **Given** 题目列表已加载，**When** 用户选择"困难"难度筛选，**Then** 页面更新仅显示难度为"困难"的题目

4. **Given** 用户同时选择"树"标签和"中等"难度，**Then** 页面仅显示同时满足两个条件的题目（AND逻辑）

5. **Given** 题目列表超过一页，**When** 用户点击分页控件或滚动到底部，**Then** 系统加载下一页题目，页面无刷新

6. **Given** 用户在筛选条件下没有任何题目，**Then** 显示友好提示"暂无符合条件的题目"

---

### User Story 2 - 查看题目详情 (Priority: P1)

作为面试者，我希望点击一道题目后能够进入详细的题目描述页面，了解题目的具体要求、输入输出格式和样例。

**Why this priority**: 题目详情是用户开始做题的前提，必须清晰展示题目所有关键信息

**Independent Test**: 用户从题目大厅点击任意题目后，成功进入题目详情页，能够阅读完整的题目描述

**Acceptance Scenarios**:

1. **Given** 用户在题目大厅，**When** 点击某道题目的标题或卡片，**Then** 跳转到该题目的刷题工作台页面

2. **Given** 用户进入刷题工作台，**When** 页面加载完成，**Then** 左侧面板显示完整的题目描述，包括：题目名称、难度标签、题目正文、输入输出格式、样例数据

---

### User Story 3 - 编写代码 (Priority: P1)

作为面试者，我希望在一个集成的代码编辑环境中编写算法代码，并能够实时看到代码编辑效果。

**Why this priority**: 代码编写是核心功能，编辑器的体验直接影响用户的使用效率和满意度

**Independent Test**: 用户进入刷题工作台后，能够选择编程语言并在右侧代码编辑区编写代码

**Acceptance Scenarios**:

1. **Given** 用户进入刷题工作台，**When** 页面加载完成，**Then** 右侧面板默认显示代码编辑器（已选择用户上次使用的语言或默认Python）

2. **Given** 代码编辑器已显示，**When** 用户从语言下拉菜单选择"Java"，**Then** 编辑器内容被清空或保留，用户可以开始用Java编写代码

3. **Given** 用户正在编写代码，**When** 输入代码内容，**Then** 编辑器支持语法高亮、自动补全、括号匹配等基础功能

4. **Given** 用户已完成代码编写，**When** 点击"运行代码"按钮，**Then** 系统使用公开测试用例执行代码，终端输出区域显示运行结果

5. **Given** 用户已完成代码编写，**When** 点击"提交代码"按钮，**Then** 系统使用公开+隐藏测试用例执行评测

---

### User Story 4 - 查看官方最优解 (Priority: P2)

作为面试者，我希望能够在做题过程中查看题目的官方最优解和详细讲解，以学习高效的解题思路。

**Why this priority**: 学习官方解法是面试者提升算法能力的重要途径，是平台教育价值的核心体现

**Independent Test**: 用户在刷题工作台能够查看到题目对应的官方最优解和详细讲解

**Acceptance Scenarios**:

1. **Given** 用户在刷题工作台，**When** 页面加载完成，**Then** 题目描述区域显示"官方最优解"折叠面板（默认收起）

2. **Given** 官方最优解面板已存在，**When** 用户点击展开面板，**Then** 显示该题目的最优解代码和详细讲解（支持Markdown渲染，包含代码块、公式、步骤说明）

3. **Given** 官方最优解已展开，**When** 用户选择不同的编程语言，**Then** 最优解代码区域显示对应语言版本的实现

---

### User Story 5 - 查看评测结果 (Priority: P1)

作为面试者，我希望提交代码后能够实时看到评测进度和最终结果，以便了解自己的代码是否正确。

**Why this priority**: 评测结果是用户最关心的信息，必须清晰、及时地展示给用户

**Independent Test**: 用户提交代码后，能够在界面上看到评测状态的实时变化和最终结果

**Acceptance Scenarios**:

1. **Given** 用户点击"提交"按钮，**When** 评测任务已提交，**Then** 界面显示状态"Pending（等待中）"

2. **Given** 评测任务已被判题服务器接收，**When** 判题开始，**Then** 界面状态更新为"Judging（判题中）"，显示进度百分比或已完成的测试用例数

3. **Given** 判题完成且全部通过，**Then** 状态显示为"Accepted (AC)"，显示绿色标识

4. **Given** 判题完成且存在错误，**Then** 显示具体错误类型：
   - "Wrong Answer (WA)" - 答案错误
   - "Time Limit Exceeded (TLE)" - 超时
   - "Memory Limit Exceeded (MLE)" - 内存超限
   - "Compile Error (CE)" - 编译错误

5. **Given** 评测结果为非AC，**When** 用户查看详情，**Then** 显示具体哪个测试用例失败、输入内容、预期输出和实际输出

---

### User Story 6 - 多语言支持 (Priority: P1)

作为面试者，我希望能够使用我熟悉的编程语言来解决算法题目，平台需要支持我常用的语言。

**Why this priority**: 支持多种语言是OJ平台的基本要求，必须覆盖主流面试语言

**Independent Test**: 用户可以选择任意支持的语言编写代码并成功提交评测

**Acceptance Scenarios**:

1. **Given** 用户进入代码编辑区，**When** 打开语言选择下拉框，**Then** 显示支持的5种语言：Python, C/C++, Java, TypeScript/JavaScript, Golang

2. **Given** 用户选择"Python"并提交代码，**Then** 后端使用Python编译器/解释器执行评测

3. **Given** 用户选择"C/C++"并提交代码，**Then** 后端使用gcc/g++编译器编译后执行评测

4. **Given** 用户选择"Java"并提交代码，**Then** 后端使用javac编译后使用java执行评测

5. **Given** 用户选择"TypeScript/JavaScript"并提交代码，**Then** 后端使用Node.js执行评测

6. **Given** 用户选择"Golang"并提交代码，**Then** 后端使用go run执行评测

---

### User Story 7 - 实时评测状态流转 (Priority: P1)

作为面试者，我希望提交代码后能够实时看到评测状态的流转，从等待到判题再到出结果的全过程。

**Why this priority**: 实时反馈评测状态是良好用户体验的基础，让用户知道系统正在工作

**Independent Test**: 用户提交代码后，界面能够实时反映评测的每个状态变化

**Acceptance Scenarios**:

1. **Given** 用户提交代码，**When** 请求发送成功，**Then** 状态立即变为"Pending"，前端建立WebSocket连接或轮询获取状态

2. **Given** 状态为Pending，**When** 后端判题服务器开始处理，**Then** 状态通过实时推送更新为"Judging"

3. **Given** 状态为Judging，**When** 判题完成，**Then** 状态更新为最终结果（AC/WA/TLE/MLE/CE）

4. **Given** 评测过程中，**When** 用户刷新页面或重新进入，**Then** 能够从后端获取当前评测的最新状态

---

### User Story 8 - 公开测试用例 (Priority: P1)

作为面试者，我希望能够在调试阶段看到公开的测试用例及其运行结果，帮助我验证代码逻辑是否正确。

**Why this priority**: 公开用例是用户调试代码的主要依据，是提升用户体验的重要功能

**Independent Test**: 用户点击"运行代码"后，能够看到公开用例的执行结果

**Acceptance Scenarios**:

1. **Given** 用户编写完代码并点击"运行"，**Then** 系统使用该题目的所有公开测试用例执行代码

2. **Given** 代码执行公开用例，**When** 所有用例通过，**Then** 终端显示"运行通过"和每个用例的执行时间

3. **Given** 代码执行公开用例，**When** 某个用例失败，**Then** 终端显示失败用例的输入、预期输出、实际输出

4. **Given** 用户在代码编辑区，**When** 查看题目描述区域的测试用例部分，**Then** 显示所有公开测试用例（输入+输出）

---

### User Story 9 - 隐藏测试用例 (Priority: P1)

作为面试者，我希望隐藏的测试用例只在最终评测时使用，以确保评测的公平性和有效性。

**Why this priority**: 隐藏用例是防止作弊和确保题目有效性的关键机制

**Independent Test**: 用户无法在界面上看到隐藏用例，但提交后系统会使用隐藏用例进行评测

**Acceptance Scenarios**:

1. **Given** 用户在刷题工作台，**When** 查看测试用例列表，**Then** 只能看到标记为"公开"的测试用例，隐藏用例不可见

2. **Given** 用户点击"运行代码"，**Then** 系统仅使用公开用例，不会使用隐藏用例

3. **Given** 用户点击"提交代码"，**Then** 系统使用公开用例+所有隐藏用例进行完整评测

4. **Given** 评测结果显示失败，**When** 用户查看详情，**Then** 仅显示公开用例的详细信息，隐藏用例详情不显示

---

### Edge Cases

- 当用户提交代码时网络中断，界面显示"提交失败，请重试"并保留用户已填写的内容
- 当判题服务器繁忙时，用户提交后状态保持Pending排队中，超时（5分钟）后提示"判题超时，请稍后重试"
- 当用户选择的语言编译器/解释器不可用时，返回"该语言暂不支持"错误
- 当用户代码存在安全风险（检测到恶意系统调用），判定为"系统错误"并记录日志
- 当测试用例数量为0时，题目不可提交，应提示管理员配置测试用例
- 用户切换题目时，未保存的代码提示是否保存（若有本地缓存则自动保存）
- 分页请求过程中用户快速切换页码，仅返回最新一次请求的结果

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 提供题目大厅页面，展示所有可用的算法题目列表
- **FR-002**: 系统 MUST 支持按题目标签（如数组、树、动态规划、哈希表等）进行筛选
- **FR-003**: 系统 MUST 支持按题目难度（简单、中等、困难）进行筛选
- **FR-004**: 系统 MUST 支持题目列表分页，每页默认20道题
- **FR-005**: 系统 MUST 提供刷题工作台页面，采用左右分屏布局
- **FR-006**: 刷题工作台左侧 MUST 显示题目描述、输入输出格式、样例数据
- **FR-007**: 刷题工作台右侧 MUST 集成代码编辑器，支持语法高亮
- **FR-008**: 刷题工作台 MUST 支持 Markdown 渲染，用于题目描述和官方解法
- **FR-009**: 系统 MUST 提供官方最优解功能，显示代码和详细讲解
- **FR-010**: 系统 MUST 支持 5 种编程语言：Python, C/C++, Java, TypeScript/JavaScript, Golang
- **FR-011**: 系统 MUST 在用户提交代码后展示实时评测状态：Pending -> Judging -> 最终结果
- **FR-012**: 系统 MUST 支持评测结果状态：Accepted (AC), Wrong Answer (WA), Time Limit Exceeded (TLE), Memory Limit Exceeded (MLE), Compile Error (CE)
- **FR-013**: 系统 MUST 将测试用例分为"公开用例"和"隐藏用例"两类管理
- **FR-014**: 系统 MUST 在用户点击"运行代码"时仅使用公开用例
- **FR-015**: 系统 MUST 在用户点击"提交代码"时使用公开用例+隐藏用例
- **FR-016**: 系统 MUST 在评测结果中隐藏测试用例的详细信息（防作弊）
- **FR-017**: 系统 MUST 提供终端输出面板，显示代码运行结果或错误信息

### Key Entities

- **题目 (Problem)**: 包含题目ID、标题、描述、难度、标签列表、时间限制、内存限制、创建时间等属性
- **测试用例 (TestCase)**: 包含用例ID、所属题目ID、输入数据、输出数据、是否为隐藏用例等属性
- **提交记录 (Submission)**: 包含提交ID、用户ID、题目ID、代码内容、编程语言、评测状态、评测结果、创建时间等属性
- **官方解法 (OfficialSolution)**: 包含解法ID、所属题目ID、编程语言、代码内容、讲解内容（Markdown格式）等属性

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户能够在 3 秒内完成题目大厅页面加载并显示第一页题目
- **SC-002**: 筛选和分页操作后，页面响应时间不超过 1 秒
- **SC-003**: 代码编辑器加载完成时间不超过 2 秒
- **SC-004**: 用户点击提交后，评测状态在 500ms 内从 Pending 变为 Judging
- **SC-005**: 单个测试用例执行时间（不含排队）不超过题目设定的时间限制的 1.5 倍
- **SC-006**: 95% 的评测任务在 30 秒内完成（简单题 5 秒，中等题 15 秒，困难题 30 秒）
- **SC-007**: 90% 的用户能够成功完成至少一次完整的"浏览-做题-提交"流程
- **SC-008**: 题目大厅支持 1000+ 道题目的存储和展示
- **SC-009**: 系统支持 1000+ 并发用户同时使用
- **SC-010**: 用户对官方解法的满意度评分达到 4 分以上（5分制）

---

## Assumptions

- 用户已注册并登录平台，能够访问题目大厅
- 题目数据已由管理员预先导入系统
- 每道题目至少包含 1 个公开测试用例和 3 个隐藏测试用例
- 判题服务器具备足够的计算资源处理并发评测请求
- 用户浏览器支持 Monaco Editor 的主流版本
- 网络环境稳定，能够支持 WebSocket 长连接或轮询
