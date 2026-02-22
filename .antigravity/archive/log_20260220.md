# 开发日志 (2026-02-20) - 任务：调整登录按钮文本

## 1. 需求 (Requirement)
- **背景**: 用户希望将首页的“欢迎回来”按钮（未登录状态）改为“登录后提交视频”或更简洁的名称，以明确功能导向。
- **目标**: 修改中英文翻译文件，并更新首页 Header 逻辑。

## 2. 计划 (Plan)
- **翻译包**: 在 `zh.json` 和 `en.json` 中添加 `login.loginToSubmit`。
- **前端页面**: 修改 `frontend/app/page.tsx` 中的按钮显示逻辑。

## 3. 回顾 (Review)
- **结果**: 页面中的登录按钮现在针对未登录用户展示为“登录后提交视频” (中文) / "Sign in to submit" (英文)，更明确地指引了用户功能，并通过浏览器测试验证成功。
- **改动文件**: 
    - `frontend/translations/zh.json`
    - `frontend/translations/en.json`
    - `frontend/app/page.tsx`

## 4. 经验 (Lessons)
- **UI引导**: 明确的 UI 文案能有效降低新用户的认知门槛。在处理此类修改时，需确保全量更新各语言的翻译配置以保持体验一致。
