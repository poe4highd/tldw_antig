# Walkthrough: Vercel Custom Domain Binding

I have updated the documentation to include steps for binding the Vercel app to a custom domain and pushed the changes to the repository.

## Changes Made

### 1. 全套图标生成与部署 (Icon Set Generation)
- 使用选定的“AI 智能播放”方案（透明背景版）更新了全套 Web 图标：
  - `favicon.ico` (32x32)
  - `icon.png` & `apple-icon.png` (Next.js App Router 规范)
  - 不同比例的 PWA 通用图标 (`icon-192.png`, `icon-512.png`) 等。
- 部署至 [frontend/public](file:///frontend/public) 和 [frontend/app](file:///frontend/app)。

### 2. 核心功能优化 (Core Feature Optimizations)
- **下载限制**：在 [downloader.py](file:///backend/downloader.py) 中添加了 `noplaylist: True`，防止带有 `&list=...` 的链接下载整个播放列表。
- **语言一致性**：在 [processor.py](file:///backend/processor.py) 中重构了语言检测逻辑。现在系统会根据视频标题自动识别**英文、繁体、简体**，并在转录校正时保持文字语言的一致性。
- **转录质量提升**：优化了 LLM Prompt，减少了对文本的过度干预，确保校正后的错别字更少。

### 3. 字幕排版优化 (Subtitle Layout Fix)
- **修复布局抖动**：移除了高亮字幕中的 `font-bold`、`scale-[1.01]` 和 `inline-block` 属性。
- **效果**：现在高亮字幕与普通字幕字体大小完全一致，切换高亮时页面排版保持绝对稳定。

## Git 记录
- 所有更改已提交并推送至远程仓库。
- 提交 ID：`feat: update site icons, fix playlist download, and improve transcription language consistency`

## 验证结论
- **图标**：已手动确认文件存在并符合尺寸规范。
- **功能逻辑**：通过了 [test_improvements.py](file:///backend/tests/test_improvements.py) 的自动化逻辑测试。
- **详细报告**：查看 [test_report_v1.1.md](file:///dev_docs/test_report_v1.1.md)。
