[2026-01-18] | [Refactor/Brand] | 品牌升级：仪表盘更名为“见地” | 将全站 Dashboard 文案统一替换为“见地 (Insights)”，提升应用文化调性 | archive/log_20260118_19.md
[2026-01-18] | [Refactor/UI] | 重构左侧栏布局 | 实现视频+操作栏固定吸顶，字幕区域独立滚动，彻底解决长字幕阅读遮挡视频的问题 | archive/log_20260118_18.md
[2026-01-18] | [Fix/Sync] | 修复页面刷新后字幕不同步 | 将 Player 实例改为 useRef 存储，解决初始化时闭包导致的轮询失效问题 | archive/log_20260118_17.md
[2026-01-18] | [Feat/UX] | 优化字幕阅读体验 | 实现视频播放器 Sticky 吸顶，字幕居中自动滚动，支持手动滚动暂停与一键回正 | archive/log_20260118_16.md
[2026-01-18] | [Refactor/Lib] | 重构播放器组件 | 废弃 iframe postMessage 方案，引入 react-youtube 库以彻底解决字幕同步不稳定的回归问题 | archive/log_20260118_15.md
[2026-01-18] | [Fix/Visual] | 修复字幕同步失效 | 指定 YouTube Iframe origin 参数，恢复 postMessage 通信，解决字幕不高亮/不滚动问题 | archive/log_20260118_14.md
[2026-01-18] | [Fix/Infra] | 重建 Cloudflare 隧道与环境自检 | 修复凭证丢失导致的 530/CORS 错误，重建本地管理型隧道并在 dev.sh 增加状态检测 | archive/log_20260118_13.md
[2026-01-18] | [Fix/Nav] | 修复导航重定向死循环 | 修正营销页状态监听逻辑以支持 noredirect 参数，并统一各页面 Logo 链接，确保护航回营销页不被强制跳回 | archive/log_20260118_12.md
[2026-01-18] | [Fix/Tool] | 修复 dev.sh 日志着色 | 改用 printf 定义逃逸字符，修复 macOS 下日志前缀颜色失效及原始代码外露的问题 | archive/log_20260118_11.md
[2026-01-18] | [Docs] | 补充开发指南端口检查特性 | 在 docs/development_guide.md 中补充 dev.sh 的自动化端口冲突处理说明 | archive/log_20260118_10.md
[2026-01-18] | [Tool] | 增强 dev.sh 端口检查 | 为启动脚本增加自动端口冲突检测与清理功能，解决“端口已占用”导致启动失败的问题 | archive/log_20260118_9.md
[2026-01-18] | [Docs] | 编写开发启动与日志监控指南 | 创建 docs/development_guide.md 并更新 README，详细说明 ./dev.sh 与分步启动及日志排查方法 | archive/log_20260118_8.md
[2026-01-18] | [Fix/API] | 修复报告页 404 错误 | 移除 main.py 中的冗余代码并验证 /view 和 /comments 接口注册，确保前后端数据同步 | archive/log_20260118_7.md
[2026-01-18] | [Optimization/UI] | 导航集成与重定向优化 | Dashboard 侧边栏集成历史与营销页入口，优化重定向逻辑并紧凑化历史页布局 | archive/log_20260118_6.md
[2026-01-18] | [Fix/DevOps] | 恢复公网连通性与 CORS | 手动重启 Cloudflare 隧道并修复后端重载导致的 530 错误与跨域拦截 | archive/log_20260118_5.md
[2026-01-18] | [Fix/UI] | 修复任务启动报错 | 优化前端 API 识别逻辑并增加详细错误提示，解决移动端提交任务时的通用失败提示 | archive/log_20260118_4.md
[2026-01-18] | [Tool] | 一键开发启动脚本 | 增加 dev.sh 脚本，支持前后端同步启动、日志合并显示及进程统一管理 | archive/log_20260118_3.md
[2026-01-18] | [Feature] | 项目历史展示功能 | 实现 .antigravity/PROJECT_HISTORY.md 的后端解析、前端独立页面及首页集成链接 | archive/log_20260118_2.md
[2026-01-18] | [Fix/Perf] | LSP 修复与存储优化 | 延迟导入 yt-dlp 修复崩溃；实现 3 天周期大文件自动清理及原视频自动删除 | archive/log_20260118.md
[2026-01-17] | [Feature] | 多语言音轨支持 | 增加多音轨识别与本地音频回退同步功能 | archive/log_20260117_3.md
[2026-01-17] | [Feature] | 用户专属任务历史 | 实现基于 user_id 的任务隔离与 submissions 表关联记录 | archive/log_20260117_2.md
[2026-01-17] | [Feature] | Supabase 数据库升级 | 完成本地 JSON 数据到云端迁移，实现 Google OAuth 认证 | archive/log_20260117_1.md
[2026-01-16] | [Feature] | 仪表盘、登录页与全站重构 | 实现 Landing Page、用户 Dashboard 及运营看板 | archive/log_20260116_1.md
[2026-01-16] | [Style] | 品牌视觉精修 | 正式定名 Read-Tube，完成多轮图标迭代与透明度修复 | archive/log_20260116_2.md
[2026-01-18] | FEATURE | 报告页真实数据与UI优化 | 实现阅读数、点赞、讨论区真实数据，按钮移动至视频下方，恢复无抖动字幕高亮 | walkthrough.md
