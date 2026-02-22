# 开发日志 (2026-02-22) - 任务：总结时间戳与格式优化

## 1. 需求 (Requirement)
- **背景**: 用户希望优化总结文本的输出。
- **目标**: 将总结的项数限制到不多于7项，每项最多3句话，并且强制大模型总结时附加对应内容视频的时间戳，且点击即可跳转。要求全过程使用中文。

## 2. 计划 (Plan)
- **后端模型层**: 更新 `processor.py` 里 summarize 的提示词，并给 `worker.py` 下放带时间戳的字幕拼合完整文本，让 LLM 根据时间标签输出 [MM:SS] 形式的时间。
- **前端页面**: 修改 `frontend/app/result/[id]/page.tsx` 使用正则 `/[(\d{2}:\d{2}(?::\d{2})?)]/g` 匹配后生成可跳转到 `seekTo(seconds)` 的组件。

## 3. 回顾 (Review)
- **结果**: 后端能够准确带时间戳发大模型做中文约束。前端将大模型生成的纯文字利用正则替换为高亮的、可点击的跳转链接。功能已验证全部通过。
- **改动文件**: 
    - `backend/worker.py`
    - `backend/processor.py`
    - `frontend/app/result/[id]/page.tsx`

## 4. 经验 (Lessons)
- **Prompt 引导**: 对于 LLM 的生成不可抱有“他一定全用纯文本一行”的假想。必须配合能够解析 Markdown 转行的（如 Tailwind 的 `whitespace-pre-wrap`）来进行渲染前端才能保障最终的文本段落是美观的。
