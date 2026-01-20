[2026-01-20] | [REFACTOR] | 进程隔离方案终极修复段错误 | 创建独立 worker.py 执行转录任务,彻底解决 MLX/Torch Metal GPU 冲突 | .antigravity/DEV_LOG.md
[2026-01-20] | [FIX] | 后端段错误深度修复 (Part 2) | 实现 AI 库全量延迟加载与显存隔离，彻底解决 MLX 与 Torch 冲突 | .antigravity/DEV_LOG.md
[2026-01-20] | [FIX] | 修复 Cloudflare 隧道 530/CORS 错误 | 重启 mac-read-tube 隧道并优化 dev.sh 状态检测逻辑 | .antigravity/DEV_LOG.md
[2026-01-19] | [FIX] | 修复后端段错误 | 解决 MLX-Whisper 与多框架线程冲突导致的 Segmentation fault: 11 | log_20260119_fix_2.md
[2026-01-19 Part 14] | [FEAT/PERF] | 转录模型默认值升级 | 将系统默认模型统一改为 large-v3-turbo 并更新缓存隔离机制与代码推送 | .antigravity/DEV_LOG.md

[2026-01-19 Part 13] | [FEATURE] | 字幕比较工具二期 | 实现三路对齐（引入 SRV1 地面真值）与内置登录安全 UI | .antigravity/DEV_LOG.md
[2026-01-19 Part 12] | [FEATURE] | 开发者字幕比较工具 | 实现双模型字幕对齐比较页面，支持多模型转录结果的同步校对 | .antigravity/DEV_LOG.md
[2026-01-19 Part 11] | [CLEANUP] | 项目文档与验证文件深度整理 | 清理冗余验证报告，确立 docs 与 validation 目录分工，更新模型管理策略并推送代码 | walkthrough.md
[2026-01-19 Part 10] | [FIX/PERF] | SenseVoice 性能突破 | 集成 sherpa-onnx + VAD, 37分钟音频推理从 3h+ 缩短至 55s (提升约 200 倍)，资源占用降低 80% | .antigravity/DEV_LOG.md
[2026-01-19 Part 9] | [FAIL] | SenseVoice 性能验证 | 确认为不可用 (Aborted after 3h): Mac CPU 推理效率极低 (<0.2x RTF)，彻底放弃 FunASR 本地集成计划 | .antigravity/DEV_LOG.md
[2026-01-19 Part 8] | [PERF] | SenseVoice 性能调优 | 解除了 ncpu 单核限制并将 batch_size_s 从 1 提升至 60，CPU 利用率从 14% 提升至 200%+ | .antigravity/DEV_LOG.md
[2026-01-19 Part 7] | [SUPPORT] | SenseVoice 模型加载疑难排查 | 解释了 FunASR 模型首次运行时约 900MB 的下载行为，澄清了磁盘占用与内存占用的区别 | .antigravity/DEV_LOG.md
[2026-01-19 Part 6] | [VERIFICATION] | 字幕准确度多模型横向对标 | 引入 Whisper-Turbo/Medium 验证，Turbo 表现惊艳 (CER 11.27%)，确认 FunASR 系列在本地 Mac 环境的 OOM 限制 | walkthrough.md
[2026-01-19 Part 5] | [TOOL] | 评估系统精准化 | 集成 zhconv 实现全量简繁对齐与代词归一化，CER 指标显著净化 | .antigravity/DEV_LOG.md
[2026-01-19 Part 4] | [TOOL] | 评估系统完善 | 实现报告自动持久化，重命名 docs/subtitle_utils.md 并完善工具集文档 | .antigravity/DEV_LOG.md
[2026-01-19 Part 3] | [TOOL] | 评估系统优化 | 实现数字归一化与 Whisper 原始缓存解析支持，引入基础简繁对齐逻辑 | .antigravity/DEV_LOG.md
[2026-01-19 Part 2] | [TOOL] | 字幕对比评估系统 | 实现 compare_subs.py 脚本计算 CER 并统计错误词频，完善量化评估文档 | .antigravity/DEV_LOG.md
[2026-01-19 Part 1] | [TOOL] | YouTube 字幕下载脚本 | 开发独立的字幕下载 CLI 工具并完善文档 | log_20260119.md
[2026-01-18 Part 27] | [UX/Refactor] | 移除侧边栏不再使用的 YouTube 发现按钮 | 移除菜单项并简化侧边栏渲染逻辑，修复因移除 disabled 属性导致的 TS 类型推导错误 | walkthrough.md
[2026-01-18 Part 26] | [Docs/Audit] | 规范项目历史格式并同步审计规则 | 为历史记录补全 Part 编号，并将审计规范录入全局协作指南 docs/ai_agent_dev_preferences_cn.md | .antigravity/DEV_LOG.md
[2026-01-18 Part 25] | [Optimization/Infra] | GPU 加速实测与自适应引擎上线 | mlx-whisper 解析 1138 个片段仅耗时 47s，确认 GPU 加速生效且格式兼容 | archive/log_20260118_25.md
[2026-01-18 Part 24] | [Tool] | 重处理脚本支持参数控制 | 修改 batch_reprocess.py 支持命令行指定视频数量，默认值调优为 1 以支持快速验证 | archive/log_20260118_24.md
[2026-01-18 Part 24] | [Planning/Infra] | 多用户并发支持评估 | 完成 task_id 冲突、资源争用、文件 IO 竞争的深度诊断，并制定 UUID 与任务队列优化方案 | implementation_plan.md
[2026-01-18 Part 23] | [Optimization/LLM] | 强化标题关键词权重提示词 | 针对纠错失败案例，引入“标题权重优先”与“拼音模糊匹配”指令，强制修正与标题不一致的同音异义词 | archive/log_20260118_23.md
[2026-01-18 Part 22] | [UX/UI] | 手机布局优化 | 完成全站侧边栏组件化与移动端响应式适配，优化结果页粘性布局。 | walkthrough.md
[2026-01-18 Part 22] | [Fix/Infra] | 实现开发与生产环境彻底分离 | 创建 utils/api.ts 实现环境感知 URL，修复 Google Auth 登录后跳转生产域名的隔离问题 | walkthrough.md
[2026-01-18 Part 21] | [Feature/Auth] | 实现神奇登录链接 (Magic Link) | 通过 Supabase 实现无密码邮件登录，包含前端 handleEmailLogin 逻辑与 Loading/反馈 UI | walkthrough.md
[2026-01-18 Part 21] | [Fix/UX] | 修复同步按钮与移动端遮挡 | 补全滚动监听事件触发同步按钮显示，优化吸顶布局消除字幕“钻入”感 | walkthrough.md
[2026-01-18 Part 20] | [Fix/UX] | 优化字幕滚动逻辑 | 弃用 scrollIntoView 改为容器内 scrollTop 计算，彻底修复自动滚动导致页面抖动/视频移位的问题 | archive/log_20260118_20.md
[2026-01-18 Part 19] | [Refactor/Brand] | 品牌升级：仪表盘更名为“见地” | 将全站 Dashboard 文案统一替换为“见地 (Insights)”，提升应用文化调性 | archive/log_20260118_19.md
[2026-01-18 Part 18] | [Refactor/UI] | 重构左侧栏布局 | 实现视频+操作栏固定吸顶，字幕区域独立滚动，彻底解决长字幕阅读遮挡视频的问题 | archive/log_20260118_18.md
[2026-01-18 Part 17] | [Fix/Sync] | 修复页面刷新后字幕不同步 | 将 Player 实例改为 useRef 存储，解决初始化时闭包导致的轮询失效问题 | archive/log_20260118_17.md
[2026-01-18 Part 16] | [Feat/UX] | 优化字幕阅读体验 | 实现视频播放器 Sticky 吸顶，字幕居中自动滚动，支持手动滚动暂停与一键回正 | archive/log_20260118_16.md
[2026-01-18 Part 15] | [Refactor/Lib] | 重构播放器组件 | 废弃 iframe postMessage 方案，引入 react-youtube 库以彻底解决字幕同步不稳定的回归问题 | archive/log_20260118_15.md
[2026-01-18 Part 14] | [Fix/Visual] | 修复字幕同步失效 | 指定 YouTube Iframe origin 参数，恢复 postMessage 通信，解决字幕不高亮/不滚动问题 | archive/log_20260118_14.md
[2026-01-18 Part 13] | [Fix/Infra] | 重建 Cloudflare 隧道与环境自检 | 修复凭证丢失导致的 530/CORS 错误，重建本地管理型隧道并在 dev.sh 增加状态检测 | archive/log_20260118_13.md
[2026-01-18 Part 12] | [Fix/Nav] | 修复导航重定向死循环 | 修正营销页状态监听逻辑以支持 noredirect 参数，并统一各页面 Logo 链接，确保护航回营销页不被强制跳回 | archive/log_20260118_12.md
[2026-01-18 Part 11] | [Fix/Tool] | 修复 dev.sh 日志着色 | 改用 printf 定义逃逸字符，修复 macOS 下日志前缀颜色失效及原始代码外露的问题 | archive/log_20260118_11.md
[2026-01-18 Part 10] | [Docs] | 补充开发指南端口检查特性 | 在 docs/development_guide.md 中补充 dev.sh 的自动化端口冲突处理说明 | archive/log_20260118_10.md
[2026-01-18 Part 9] | [Tool] | 增强 dev.sh 端口检查 | 为启动脚本增加自动端口冲突检测与清理功能，解决“端口已占用”导致启动失败的问题 | archive/log_20260118_9.md
[2026-01-18 Part 8] | [Docs] | 编写开发启动与日志监控指南 | 创建 docs/development_guide.md 并更新 README，详细说明 ./dev.sh 与分步启动及日志排查方法 | archive/log_20260118_8.md
[2026-01-18 Part 7] | [Fix/API] | 修复报告页 404 错误 | 移除 main.py 中的冗余代码并验证 /view 和 /comments 接口注册，确保前后端数据同步 | archive/log_20260118_7.md
[2026-01-18 Part 6] | [Optimization/UI] | 导航集成与重定向优化 | Dashboard 侧边栏集成历史与营销页入口，优化重定向逻辑并紧凑化历史页布局 | archive/log_20260118_6.md
[2026-01-18 Part 5] | [Fix/DevOps] | 恢复公网连通性与 CORS | 手动重启 Cloudflare 隧道并修复后端重载导致的 530 错误与跨域拦截 | archive/log_20260118_5.md
[2026-01-18 Part 4] | [Fix/UI] | 修复任务启动报错 | 优化前端 API 识别逻辑并增加详细错误提示，解决移动端提交任务时的通用失败提示 | archive/log_20260118_4.md
[2026-01-18 Part 3] | [Tool] | 一键开发启动脚本 | 增加 dev.sh 脚本，支持前后端同步启动、日志合并显示及进程统一管理 | archive/log_20260118_3.md
[2026-01-18 Part 2] | [Feature] | 项目历史展示功能 | 实现 .antigravity/PROJECT_HISTORY.md 的后端解析、前端独立页面及首页集成链接 | archive/log_20260118_2.md
[2026-01-18 Part 1] | [Fix/Perf] | LSP 修复与存储优化 | 延迟导入 yt-dlp 修复崩溃；实现 3 天周期大文件自动清理及原视频自动删除 | archive/log_20260118.md
[2026-01-17 Part 3] | [Feature] | 多语言音轨支持 | 增加多音轨识别与本地音频回退同步功能 | archive/log_20260117_3.md
[2026-01-17 Part 2] | [Feature] | 用户专属任务历史 | 实现基于 user_id 的任务隔离与 submissions 表关联记录 | archive/log_20260117_2.md
[2026-01-17 Part 1] | [Feature] | Supabase 数据库升级 | 完成本地 JSON 数据到云端迁移，实现 Google OAuth 认证 | archive/log_20260117_1.md
[2026-01-16 Part 1] | [Feature] | 仪表盘、登录页与全站重构 | 实现 Landing Page、用户 Dashboard 及运营看板 | archive/log_20260116_1.md
[2026-01-16 Part 2] | [Style] | 品牌视觉精修 | 正式定名 Read-Tube，完成多轮图标迭代与透明度修复 | archive/log_20260116_2.md
[2026-01-18 Part 1] | FEATURE | 报告页真实数据与UI优化 | 实现阅读数、点赞、讨论区真实数据，按钮移动至视频下方，恢复无抖动字幕高亮 | walkthrough.md
