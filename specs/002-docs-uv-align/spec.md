# Feature Specification: 文档与代码对齐及 uv 环境声明

**Feature Branch**: `002-docs-uv-align`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "确定当前的需求文档和代码对齐，文档中应当声明使用的是uv环境。保证每一个功能部分都进行了验证，实现上也要讲究性能。最终要确保应用可以运行。"

## Clarifications

### Session 2026-03-16

- Q: 用户要求"讲究性能"，是否需要添加 uv 性能优势说明？ → A: 无需额外性能内容
- Q: 验证范围应该包括哪些文档？ → A: 这里说的是代码部分的功能进行测试验证
- Q: 应该如何验证代码功能？ → A: 两者都验证（启动服务验证 API + 运行测试用例）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 验证文档与代码一致性 (Priority: P1)

作为项目维护者，我希望验证需求文档与实际代码实现的一致性，以确保文档准确反映系统功能。

**Why this priority**: 文档与代码不一致会导致开发者和用户误解系统行为，是项目质量的基础保障

**Independent Test**: 通过对比文档描述和代码实现，验证所有核心功能点是否匹配

**Acceptance Scenarios**:

1. **Given** 需求文档描述了题目大厅功能，**When** 检查后端代码，**Then** 代码中存在对应的 API 路由和服务实现

2. **Given** 需求文档定义了5种编程语言支持，**When** 检查代码实现，**Then** 后端沙箱包含对应语言的执行器

3. **Given** 需求文档描述了测试用例分为公开和隐藏两类，**When** 检查数据模型，**Then** Submission 和 TestCase 模型包含相应字段

---

### User Story 2 - 更新环境配置文档 (Priority: P1)

作为项目维护者，我希望更新文档以使用 uv 作为包管理工具，以便开发者使用更高效的依赖管理方式。

**Why this priority**: 使用 uv 可以显著提升依赖安装速度，是改善开发者体验的重要举措

**Independent Test**: 开发者按照更新后的文档使用 uv 能够成功搭建开发环境并运行项目

**Acceptance Scenarios**:

1. **Given** 新开发者克隆项目，**When** 阅读 README.md 中的安装说明，**Then** 文档展示使用 uv 安装依赖的命令

2. **Given** 开发者在本地环境，**When** 按照文档执行 `uv sync`，**Then** 所有依赖成功安装且项目可正常运行

3. **Given** 开发者运行测试，**When** 按照文档执行 `pytest`，**Then** 测试成功执行

---

### User Story 3 - 同步 CLAUDE.md 与项目配置 (Priority: P2)

作为项目维护者，我希望 CLAUDE.md 中声明的技术栈和命令与实际项目配置一致，以便 AI 辅助开发时能使用正确的工具。

**Why this priority**: CLAUDE.md 是 AI 辅助开发的指导文件，其准确性直接影响开发效率

**Independent Test**: AI 工具能够根据 CLAUDE.md 中的命令成功执行项目操作

**Acceptance Scenarios**:

1. **Given** AI 工具读取 CLAUDE.md，**When** 查看 Commands 部分，**Then** 显示的命令与 pyproject.toml 中的配置一致

2. **Given** AI 工具执行代码检查，**When** 按照 CLAUDE.md 中的 `ruff check .` 执行，**Then** 命令成功运行

---

### User Story 4 - 验证代码功能可运行 (Priority: P1)

作为项目维护者，我希望运行测试用例并启动服务，以确保代码实现的功能正常工作。

**Why this priority**: 确保代码实际可用，是交付质量的基本保障

**Independent Test**: 通过运行 pytest 和启动 FastAPI 服务验证代码功能正常

**Acceptance Scenarios**:

1. **Given** 依赖已安装，**When** 执行 `pytest`，**Then** 核心测试用例通过

2. **Given** 依赖已安装，**When** 启动 FastAPI 服务，**Then** 服务成功启动并响应请求

3. **Given** 服务已启动，**When** 访问 API 文档页面，**Then** 显示可用的 API 端点

---

### Edge Cases

- 当 pyproject.toml 依赖发生变化时，README.md 和 CLAUDE.md 需要同步更新
- 当新增项目依赖或工具时，所有相关文档需要统一更新
- 当项目结构发生变化时，README.md 中的项目结构说明需要同步

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 需求文档 MUST 准确描述已实现的核心功能，包括题目大厅、刷题工作台、代码评测等
- **FR-002**: 代码实现 MUST 与需求文档中的功能描述保持一致
- **FR-003**: README.md MUST 使用 uv 作为推荐的依赖管理工具
- **FR-004**: CLAUDE.md 中的 Commands 部分 MUST 与实际可执行的命令一致
- **FR-005**: 项目结构说明 MUST 与实际目录结构匹配
- **FR-006**: 环境要求文档 MUST 包含 uv 工具的安装说明
- **FR-007**: pytest 测试用例 MUST 能够成功执行
- **FR-008**: FastAPI 服务 MUST 能够成功启动并响应请求

### Key Entities

- **README.md**: 项目主文档，包含技术栈、快速开始、API 说明
- **CLAUDE.md**: AI 开发辅助文件，包含技术栈和命令
- **pyproject.toml**: Python 项目配置文件，定义依赖和工具

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: README.md 中的依赖安装命令可成功执行，开发者能在 5 分钟内完成环境搭建
- **SC-002**: 需求文档中的所有核心功能在代码中都有对应实现
- **SC-003**: CLAUDE.md 中的命令执行成功率为 100%
- **SC-004**: 新开发者按照文档能够从零开始运行项目
- **SC-005**: pytest 测试执行成功，核心测试用例通过
- **SC-006**: FastAPI 服务启动成功，API 可访问
