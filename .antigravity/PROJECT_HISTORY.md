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
