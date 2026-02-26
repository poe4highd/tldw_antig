[2026-02-26] | [Bugfix] | 自动清理卡住的任务 | Scheduler 增加超时检测，processing>3h 或 queued>24h 自动标为 failed | DEV_LOG.md
[2026-02-25] | [UX/UI] | 摘要时间轴条 | 结果页视频播放器下方添加 7 段 Okabe-Ito 配色时间轴条，支持高亮、点击跳转、tooltip | DEV_LOG.md
[2026-02-25] | [UX/UI] | 移除本地缩略图依赖 | 文本模式改为频道头像，thumb 模式用 YouTube CDN 封面图，消除黑色方块问题 | DEV_LOG.md
[2026-02-23] | [Feature] | 修改频道默认追踪行为 | 将新频道默认设为不追踪，需手动开启 | walkthrough.md
[2026-02-22] | [UX/UI] | 报告页布局改版与摘要回填 | 采用全屏宽度的全新垂直流式排版，使用脚本重做了最近10条结果的摘要。 | DEV_LOG.md
[2026-02-22] | [Feature] | 细化摘要结果并带时间戳跳转 | 约束摘要为少于7项每项限3句，支持大模型生成具体时间戳，前端正则配合实现跳转 | DEV_LOG.md
[2026-02-21] | [UX/UI] | 调整首页登录按钮文本 | 将未登录状态的“欢迎回来”按钮改为“登录后提交视频”，明确向用户传达功能导向 | DEV_LOG.md
[2026-02-16] | [Bugfix] | 修复字幕缺失与 Explore API 错误 | 解决同步失败导致的字幕缺失，并修复 get_explore 接口的 NameError 引用 | walkthrough.md
[2026-02-16] | [Bugfix] | 修复 API 回归错误与调度卡死 | 修复 get_explore 的 NameError 引用，清理多余调度器进程并重启服务 | walkthrough.md
[2026-02-16] | [Bugfix] | 修复书架页面视频丢失问题 | 解决 submissions 表缺失唯一约束导致的关联失败，补全了用户缺失的视频关联记录 | walkthrough.md
[2026-02-15] | [DevOps] | 优化开发脚本防止后端挂起 | 增强 dev.sh 的进程清理逻辑，解决间歇性端口占用及服务挂起问题 | dev.sh

[2026-02-15] | [Bugfix] | 修复频道名称显示为 ID 的问题 | 统一后端 JSON 字段名并运行脚本补全 13 条存量数据的频道名称 | walkthrough.md
[2026-02-15] | [UX/UI] | 管理页 UI 精细化与主题适配 | 实现管理端全量黑白主题、双语切换及紧凑型布局优化 | walkthrough_admin_ui.md
[2026-02-15] | [Feature] | 管理页增加 LLM 用量追踪面板 | 实现 LLM 模型、Token 及费用的实时统计与历史追踪 | walkthrough_llm_tracking.md
[2026-02-15] | [Docs] | 清理文档绝对路径并增强 Cookie 指导 | 全局清理硬编码路径，增加手动获取 Cookie 的插件指导 | youtube_cookies_setup.md
[2026-02-15] | [Docs] | 编写频道追踪系统技术文档 | 详尽记录频道检查频率限制、顺序调度逻辑及设计安全考量 | channel_tracking_design.md
[2026-02-10] | [Bugfix] | 修复可见性管理缩略图 | 修复 API URL 补全逻辑并恢复 60 个丢失的本地缩略图文件 | walkthrough.md
[2026-02-09] | [feature] | 管理数据驾驶舱实时化 | 管理页接入真实 API，实现视频数/DAU/热力图实时展示 | walkthrough.md
[2026-02-09] | [Feature] | 实现失败任务自动重试 | 在频道追踪中增加失败视频重试逻辑，每视频上限 3 次 | DEV_LOG.md
[2026-02-09] | [Feature] | 频道追踪逻辑优化 | 增加 Cookie 支持并过滤会员/直播视频，解决主页停滞问题 | DEV_LOG.md
[2026-02-09] | [UX] | 优化已登录用户 Profile 访问 | 实现登录页自动重定向及 Header 链接动态调整 | walkthrough.md
[2026-02-08] | [Feature] | 集成 YouTube Cookie 鉴权 | 在 yt-dlp 调用链中增加 cookiefile 支持，解决 429/403 频率限制问题 | DEV_LOG.md
[2026-02-08] | [Bugfix] | 修复结果页 URL 误识别 | 修复由于正则匹配过宽导致的结果页 URL 无法转录问题 | DEV_LOG.md
[2026-02-08] | [Bugfix] | 修复首页滚动遮挡问题 | 消除粘性头部与工具栏之间的间隙，通过调整 z-index 和背景不透明度解决视频漏出问题。 | walkthrough.md
[2026-02-08] | [Feature] | 视频与频道可见性管理 | 实现基于 Admin Secret Key 的管理权限校验；支持隐藏特定视频/频道及配置自动追踪频率。 | walkthrough.md
[2026-02-08] | [Feature] | 全链路视频隐私控制 | 实施 RLS 性能优化与隐私过滤；前端支持提交时切换公开/私有并实时同步书架状态。 | walkthrough.md
[2026-02-08] | UI/Performance | 深度优化书架性能与字号增强 | 后端实现数据库级分页限流；书架视频标题字号增加 70% 并适配布局。 | tasks_sync_shelf_opt.md
[2026-02-08] | [Feature] | 点赞功能与书架重构 | 给首页/详情页添加点赞系统并持久化，重构书架页布局与 API 聚合收藏内容。 | walkthrough.md
[2026-02-08] | [UI/UX] | 登录/Dashboard 体验优化 | 更新登录页功能描述，Dashboard 工具栏吸顶并对齐首页风格，全站支持主题切换。 | walkthrough.md
[2026-02-08] | [UI/UX] | 整合粘性工具栏布局优化 | 置顶工具栏桌面端重构：搜索栏左置并占 30% 宽度，整合关键词与切换器。 | walkthrough.md
[2026-02-08] | [UI/UX] | 登录按钮与搜索框优化 | 在首页添加登录按钮，并由于移动端遮挡重构了搜索框布局，同时升级了登录页面的功能展示。 | walkthrough.md
