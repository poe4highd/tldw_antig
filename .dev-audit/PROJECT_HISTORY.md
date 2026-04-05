[2026-04-04] | [Eval] | Gemma 4 本地矫正评测 | gemma4:e2b CER 37%，不如 qwen3:8b（28%），gpt-4o-mini 最优（12%）；Ollama 升级至 0.20.2，补 zhconv 依赖 | log_20260404.md
[2026-03-30] | [Perf] | Supabase Egress 超量优化 | 进度轮询 2s→30s、历史改事件驱动、队列条件轮询、videos(*) 改精确字段，预计 egress 降 ~4.5GB/月 | log_20260330.md
[2026-03-22] | [Docs] | 创作者故事与产品介绍文章 | 在 dev_docs 新增周末/夜晚构建 Read-Tube 的英文文章，附产品截图占位与 ASCII 架构/流程图 | log_20260322.md
[2026-03-17] | [Bugfix] | 修复 /history Supabase 查询缺 status 字段 | videos join select 漏了 status 导致所有记录被跳过，history 一直走本地 fallback | DEV_LOG.md
[2026-03-17] | [UX] | 上传文件报告页自动切换 MP3 播放器 | useLocalAudio 根据 youtube_id 自动判断，删除手动切换按钮 | DEV_LOG.md
[2026-03-17] | [Bugfix] | /process 端点增加 URL 格式校验 | 前后端双重校验拒绝无效 URL 输入，防止无效任务入队浪费资源 | DEV_LOG.md
[2026-03-16] | [Bugfix] | 修复上传音频 channel 未定义崩溃 | process_task.py channel/channel_id/channel_avatar 初始化提到分支外，Worker 成功后清理残留 _error.json | DEV_LOG.md
[2026-03-09] | [Feature] | 加权语言检测覆盖韩/日/多语言 | detect_language_preference() 改为字符计数，transcriber.py 暴露 Whisper info.language，worker.py 加权合并，summarize_text() 增加韩/日/通用 prompt | DEV_LOG.md
[2026-03-06] | [Feature] | AI 摘要语言随视频原语言自动适配 | processor.py summarize_text() 按 detect_language_preference() 结果选用英/繁/简三套 prompt | DEV_LOG.md
[2026-03-06] | [Feature] | SEO 英文市场战略 + 结果页 SSR 动态 Metadata | result/[id] 拆分 Server/Client Component，generateMetadata 动态生成 title/OG，新增 sitemap.ts、robots.txt，layout.tsx 英文化 | DEV_LOG.md
[2026-03-07] | [Bugfix] | 修复 UC 频道 ID 被误判为 cookies 失败 | channel_tracker.py 改正 UC... 频道的 videos URL 拼接并收敛误导性日志，验证后成功新入队 VP09PAKYUq4 | DEV_LOG.md
[2026-03-07] | [验证] | 手动触发 Tracker 测试 youtube_cookies.txt | 手动运行 channel_tracker.py 证实 Tracker 可正常执行整轮检查，但当前 cookies 文件仍会先失败再降级回退 | DEV_LOG.md
[2026-03-07] | [Bugfix] | 保留自动追踪任务的来源字段与 queued 元数据 | process_task.py 完成态保存结果时改为合并既有 report_data，避免 source=tracker 等元字段被覆盖为 null | DEV_LOG.md
[2026-03-07] | [审计] | 再次审核频道追踪功能健康度 | 核实 5 个追踪频道、小时级触发、最新自动发现任务 Kys6HuRNwxo 成功闭环；发现 cookies 每轮回退和 report_data.source 被完成态覆盖的可观测性缺口 | DEV_LOG.md
[2026-03-07] | [Bugfix] | 修复频道追踪器在 systemd 下找不到 yt-dlp | 诊断确认视频处理链正常但 Tracker 每小时触发均因硬编码 yt-dlp 命令失效；channel_tracker.py 改为优先解析 venv/bin/yt-dlp 并验证修复 | DEV_LOG.md
[2026-03-03] | [Bugfix] | 修复上传视频文件无法播放 | 后端删除原视频后file_path未更新导致media_path指向已删文件404，前端添加扩展名fallback兼容旧数据 | log_20260303.md
[2026-03-01] | [UX/Bugfix] | 活动任务列表限高滚动+缩略图本地优先修复 | 任务列表加max-h滚动，process_task.py缩略图本地JPG优先，前端img添加onError fallback | DEV_LOG.md
[2026-03-01] | [i18n] | 进度状态文本多语言支持 | 后端status改为英文key，前端通过statusMap+t()翻译，en/zh各新增8条翻译 | DEV_LOG.md
[2026-03-01] | [Bugfix] | 修复yt-dlp下载失败：过期Cookies回退+ffmpeg路径 | downloader.py添加3层重试策略处理过期cookies和429限流，process_task.py补全systemd环境ffmpeg PATH | DEV_LOG.md
[2026-03-01] | [Bugfix] | 修复Scheduler使用错误Python解释器导致所有任务失败 | scheduler.py硬编码python3指向anaconda缺少supabase包，改用sys.executable；修复/history端点同类竞态 | DEV_LOG.md
[2026-02-28] | [Bugfix] | 修复GET /result竞态条件和错误诊断链断裂 | 修复Supabase processing+本地failed的竞态透传bug，Scheduler和process_task早期退出补写_error.json | DEV_LOG.md
[2026-02-27] | [Bugfix] | 修复提交任务立刻显示错误和100%进度 | 清理重新提交时的旧文件污染，重构GET /result状态路由，failed进度归零 | DEV_LOG.md
[2026-02-27] | [Feature] | 最终处理特定视频(OOwS_HHOWfs)并修复GPU转录降级 | 清理进程彻底完成该视频处理，并删除 transcriber.py 对 torch 的隐式探测依赖，强制启用 CUDA float16 | DEV_LOG.md
[2026-02-27] | [Bugfix] | 修复后台处理任务与云端状态不同步 | 修复 scheduler.py 运行子进程崩溃时不更新云端状态的核心bug，统一早期退出错误上报机制 | DEV_LOG.md
[2026-02-27] | [UX/UI] | 视频报告页面空间密度优化 | 全面缩减桌面端报告页面的容器内外边距、移除硬编码高度与紧凑字体，大幅提升单屏信息展示密度 | DEV_LOG.md
[2026-02-27] | [Bugfix] | 修复前端进度条假死问题 | 修改后端API /result与/history 使得未完成任务回退读取本地真实进度，并执行长视频全链路通过 | DEV_LOG.md
[2026-02-26] | [故障排查] | 修复僵尸任务与Supabase网络 | 诊断Tailscale DNS劫持导致Supabase无法连接，关闭Tailscale恢复并手动清理失败记录 | log_20260226.md
[2026-02-26] | 维护 | 重新处理最近 5 个错误任务 | 挑选最近的 5 个 _error.json 重新执行以排查错误 | PROJECT_HISTORY.md
[2026-02-26] | [Bugfix] | 修复 Worker 错误 traceback 被覆盖 | process_task.py 外层 except 不再覆盖 worker 写好的 traceback，增加 stderr 兜底 | DEV_LOG.md
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
