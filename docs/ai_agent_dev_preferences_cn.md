# AI Agent Dev Preferences (AI 协作偏好与规范)

本文档记录了本项目中与 AI Agent 协作时的习惯、目录结构以及推荐的开发流程。

## 1. 目录与命名偏好 (Directory & Naming)

| 目录 | 用途 | 命名规范 | 示例 |
| :--- | :--- | :--- | :--- |
| `dev_docs/` | 开发记录与任务追踪 (Task, Plan, Logs) | **简短 + 8位日期时间戳** | `task_auth_20260117.md` |
| `docs/` | 正式项目文档 (指南、手册、路线图) | 简练描述，无需时间戳 | `features_guide.md` |
| `README.md` | 项目总入口与文档索引 | N/A | N/A |

## 2. Agent 交互习惯

### 2.1 任务驱动流程
*   **任务拆解**：在开始复杂工作前，Agent 应优先更新 `task.md`。
*   **方案确认**：对于涉及重大逻辑变动的任务，Agent 应在 `dev_docs/` 下创建或更新 `implementation_plan.md` 并请求用户复核。

### 2.2 开发记录
*   **执行与验证**：在完成功能开发后，Agent 应通过 `walkthrough.md` 记录验证结果（包含录屏、截图或日志片段），并存档于 `dev_docs/`。

## 3. 技术实践偏好 (由历史经验总结)

*   **前后端分离**：前端 Vercel + 后端内网穿透（Cloudflare Tunnel）。
*   **环境隔离**：敏感信息仅存本地 `.env`。
## 4. 透明化开发 (Transparent Development)

### 4.1 开发日志页面 (`/dev-logs`)
*   **功能**：系统会自动将 `dev_docs/` 下的所有 Markdown 文档同步到前端 `/dev-logs` 路由，供所有人查看。
*   **目的**：通过公开开发计划、记录和思考，实现完全透明的协作。
*   **Agent 要求**：
    *   在每次重大更新后，确保 `dev_docs/` 下有相应的记录文件。
    *   记录文件应使用标准 Markdown 格式，以便在前端正确渲染。

---
*最近更新：2026-01-17*
