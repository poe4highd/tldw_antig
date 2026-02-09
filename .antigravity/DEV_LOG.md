# 开发日志 (2026-02-08)

## 任务：修复结果页 URL 误识别导致的转录失败问题

### 1. 需求 (Requirement)
- **背景**: 视频 `NRDWBQWiYeg` 处理速度极快但没有字幕，状态显示为 `failed`。
- **错误信息**: `ERROR: Unsupported URL: https://read-tube.com/result/NRDWBQWiYeg`
- **根本原因**: `main.py` 中的正则表达式过于宽泛，误将本站结果页 URL 中的路径部分识别为 YouTube ID。随后 `process_task.py` 优先使用了该无效 URL 尝试下载，导致失败。

### 2. 实施 (Implementation)
- **Regex 优化**: 改进 `main.py` 中的 URL 识别逻辑，明确限定仅对 YouTube 相关域名进行 11 位 ID 提取。
- **URL 降级逻辑**: 改进 `process_task.py`，若识别到 11 位 ID 但提供的 URL 为本站结果页，则自动降级为标准的 YouTube Watch URL 进行处理。
- **验证脚本**: 新增 `backend/tests/test_url_logic.py` 用于自动化回归测试。

### 3. 回顾 (Review)
- **结果**: URL 误匹配问题已彻底解决。测试证明系统现能正确识别本站 URL 为“非 YouTube”链接，并在处理阶段成功触发降级逻辑转向 YouTube。
- **改动文件**: `backend/main.py`, `backend/process_task.py`, `backend/tests/test_url_logic.py`。
- **已知问题**: 实测过程中触发了 YouTube 的 429 (Too Many Requests) 频率限制，目前建议稍后重试或在生产环境配置代理/Cookie 池。

### 4. 经验 (Lessons)
- **正则防御**: 对 ID 提取不宜过于激进，应配合域名上下文。
- **增强容错**: 处理层应具备从 Task ID 重新构造标准资源路径的能力。

---


## 任务：修复首页滚动遮挡问题

### 1. 需求
- 主页视频容器向上滚动时，应该在搜索条下面就被遮挡，而不应该出现在搜索条上面又出现的情况。

### 2. 实施
- **前端 (`page.tsx`)**:
  - **消除残余边距**: 将 Hero Title 的 `mt-6` 修改为动态控制 (`isScrolled ? "mt-0" : "mt-6"`)，防止主标题隐藏后留下 24px 的空隙。
  - **像素级对齐**: 为 Global Header 设置固定高度 (`h-14 md:h-16`)，并将 Toolbar 的吸顶偏移量 (`top`) 硬编码为与之完全相等，消除任何由于动态高度计算导致的缝隙。
  - **层级加固**: 维持 Header (`z-60`) > Toolbar (`z-50`) > 视频内容的堆叠顺序。

### 3. 回顾
- **结果**: 视频卡片现在在滚动过程中会被工具栏完美遮挡，完全消除了由于标题边距残留导致的“二阶段漏出”现象。
- **改动文件**: `frontend/app/page.tsx`, `.antigravity/DEV_LOG.md`, `.antigravity/PROJECT_HISTORY.md`。

---


## 任务：全链路视频隐私控制实现

### 1. 需求
- 用户在提交视频（URL/文件）时可选择公开或私密。
- 私密视频对其他用户不可见，不出现在发现广场，仅在拥有者的书架中展示。
- RLS 层面需要针对高并发场景进行性能优化。
- 保证历史存量视频的可见性与所有权归属。

### 2. 实施
- **数据库**：
  - `005_privacy_schema.sql`：在 `videos` 注入 `is_public` 与 `user_id` 冗余字段。
  - **性能优化**：通过冗余字段实现的 RLS 策略 `is_public = TRUE OR user_id = auth.uid()` 大幅优于 `EXISTS` 子查询逻辑。
  - **数据一致性**：通过子查询回填了现有视频的 `user_id` 至其首位提交者。
- **后端 (FastAPI)**：
  - 更新 `main.py` 及 `process_task.py`：捕获 `is_public` 参数并透传给后台处理进程，确保最终录入 Supabase 的结果保留隐私偏好。
  - `get_explore` 增加显式隐私过滤。
  - `get_bookshelf` 增加 `is_public` 字段返回以支撑 UI 显状态。
- **前端 (Next.js)**：
  - `Tasks` 页面新增 Switch 切换按钮。
  - Dashboard 视频卡片增加隐私状态图标（Lock/Share）。
  - 更新中英文多语言包。

### 3. 回顾
- **结果**：视频隐私控制系统上线。经测试，私密视频完全从公共 Explore 流中排除，且书架性能未受冗余字段影响。

---


## 任务：视频与频道可见性管理

### 1. 需求
- 隐藏视频 `0_zgry0AGqU` 及其频道（@mingjinglive）的所有视频在主页
- 增加开发者管理页面，控制视频/频道在主页的显示/隐藏
- 控制哪些频道需要定期追踪新视频

### 2. 实施
- **数据库**：`004_visibility_schema.sql` 新增 `channel_settings` 表和 `videos.hidden_from_home` 字段
- **后端**：
  - `get_explore` API 过滤隐藏视频和隐藏频道
  - `channel_tracker.py` 跳过 `track_new_videos=FALSE` 的频道
  - 新增 `/admin/visibility` 管理 API，由 `x-admin-key` 保护
- **前端**：
  - 新增 `/admin/visibility` 频道与视频管理页面
  - 管理页面整合密钥验证流，支持 `localStorage` 持久化存储
  - /admin 主页增加密钥锁定保护

### 3. 回顾
- **结果**：视频可见性控制与管理员认证系统完整上线。用户已验证 `/admin/visibility` 功能可用，且所有变更已提交并推送。
- **改动文件**：`backend/main.py`, `backend/scripts/channel_tracker.py`, `frontend/app/admin/visibility/page.tsx`, `frontend/app/admin/page.tsx`。

### 4. 经验
- **轻量级鉴权**：在小型单用户/内部项目中，利用环境变量 `ADMIN_SECRET_KEY` 配合自定义 HTTP Header (`X-Admin-Key`) 是一种极简且优雅的鉴权方案，避免了复杂的 RBAC 角色系统。
- **DB 限制**：Python Supabase 库无法执行 DDL，必须通过 SQL 脚本进行迁移。
- **UX 优化**：在管理页面使用 `localStorage` 存储密钥，避免了刷新页面重复输入的烦恼。

---


## 任务：同步任务页 UI 与优化书架加载性能

### 3. 回顾 (Review)
- **改动内容**：
    - **任务页 (`tasks/page.tsx`)**：
        - 引入 `useTheme` 和 `LanguageSwitcher`。
        - 补全顶部 Logo、语言/主题切换、用户个人资料入口。
        - 将硬编码颜色类名（如 `bg-slate-950`）迁移至主题感知的 `bg-background`。
        - 重构 Header 为标准粘性布局。
    - **书架性能极致优化**：
        - **后端 (`main.py`)**：在数据库查询级引入 `.order().limit()`，避免全量合并，大幅降低 IO 与 CPU 开销。
        - **前端 (`dashboard/page.tsx`)**：视频标题字号增加 70%（网格 22px / 列表 20px），并优化标题容器高度以适配双行显示。
- **测试结果**：即使在数据量较大的情况下，书架加载也近乎瞬时完成；标题视觉效果更醒目，阅读体验显著提升。

---


## 任务：书架页控制按钮与首页对齐

### 3. 回顾 (Review)
- **改动内容**：
    - **前端 (`dashboard/page.tsx`)**：
        - 统一 `viewMode` 状态为 `thumb/text-single/text-double`。
        - 引入 `density` 状态（1L/3L）并实现对应的渲染模板。
        - 引入 `limit` (分页大小) 控制，并与后端 API 连通。
        - 重新布局工具栏，使用首页同款的紧凑型粘性设计。
    - **后端 (`main.py`)**：
        - 更新 `/bookshelf` 接口，支持点选 `limit` 参数。
        - 接口返回数据中增加 `summary` 和 `keywords` 字段，以支持详细列表模式。
- **测试结果**：书架页功能现已与首页完全一致，能够自由切换视图、密度和分页大小，摘要正常显示。

---


## 任务：主页视频消失热修复 (Hotfix)

### 3. 回顾 (Review)
- **原因分析**：在为 `get_explore` API 增加 `user_id` 参数以支持透传点赞状态时，函数签名定义遗漏了该参数，导致后端抛出 `NameError`。由于该函数有异常捕获，导致错误被隐藏并返回了空列表。
- **改动内容**：
    - **后端 (`main.py`)**：修复 `get_explore` 函数签名，补全 `user_id` 参数。
    - **环境同步**：清理了后台残留的 Python 进程并重新启动后端服务。
- **测试结果**：主页 `/explore` 接口现在能正确返回视频列表，功能恢复。

---


## 任务：书架功能增强与首页点赞系统

### 3. 回顾 (Review)
- **改动内容**：
    - **后端系统**：
        - 新增 `user_likes` 数据库表，追踪用户的点赞行为。
        - 实现了 `/like` API 接口，支持对视频进行点赞/取消点赞的原子切换。
        - 重构了 `/bookshelf` 接口，聚合用户处理过的视频 (Submissions) 与点赞过的视频 (Likes)，并支持按时间倒序。
        - 增强了 `/explore` 与 `/result/{id}` 接口，支持根据 `user_id` 返回 `is_liked` 状态。
    - **前端页面**：
        - **首页 (`page.tsx`)**：在视频卡片中集成了心形点赞按钮。支持三种视图模式（Thumb, Text-Single, Text-Double）下的实时交互。
        - **书架页 (`dashboard/page.tsx`)**：彻底重构布局，审美全面对齐首页（Sticky Toolbar, Mesh Blur Background）；接入新书架 API，显示个人收藏与处理历史。
        - **详情页 (`result/[id]/page.tsx`)**：将原 ThumbsUp 系统升级为全站统一的点赞系统，支持数据持久化到个人书架。
- **测试结果**：
    - 首页点赞能即时同步至书架页面。
    - 书架页面布局与首页完全一致，审美体验大幅提升。
    - 无登录用户点击点赞按钮能正确重定向至登录页。

### 4. 经验 (Lessons)
- **跨组件状态一致性**：通过在 API 层面返回 `is_liked` 字段，简化了前端多个页面（首页、书架、详情）的状态初始化逻辑，确保了数据的一致性。
- **审美对齐**：在重构 Dashboard 时，复用首页的 Sticky Toolbar 样式（同样的 Blur 强度和 Border Opacity）相比于单独设计能更快达成视觉上的系统感。

---


## 任务：登录页功能更新与 Dashboard 主题适配

### 3. 回顾 (Review)
- **改动内容**：
    - **登录页面 (`login/page.tsx`)**：更新了特色功能描述，增加了“提交新视频”和“个人书架”功能位；移除了硬编码背景，完美支持浅色模式。
    - **Dashboard (`dashboard/page.tsx`)**：重构了顶栏布局，将其改为吸顶式 (Sticky) 且带有毛玻璃背景的工具栏，视觉风格与首页保持一致；修复了主题适配问题。
    - **侧边栏 (`Sidebar.tsx`)**：移除硬编码颜色，支持跟随全站主题切换。
    - **多语言适配**：更新了 `zh.json` 和 `en.json` 中的相关翻译键。
- **测试结果**：
    - 主题切换在登录页、Dashboard、侧边栏均表现正常。
    - Dashboard 滚动时顶栏吸顶效果丝滑，布局更具现代感。

### 4. 经验 (Lessons)
- **主题一致性**：使用 CSS 变量 (如 `--background`, `--card-bg`) 替代硬编码颜色是实现流畅主题切换的基础。
- **布局抽象**：Dashboard 与首页共享相近的“工具栏”布局逻辑，虽然组件不同，但维持一致的视觉变量（如 Blur, Border opacity）能显著提升产品的专业感。

---


## 任务：粘性工具栏重构与桌面布局优化

### 3. 回顾 (Review)
- **改动内容**：
    - 完成了整合式粘性工具栏的开发。
    - **桌面端布局优化**：将搜索栏固定在工具栏左侧，占据 30% 宽度，进一步平衡了搜索与动态关键词的展示比例。关键词条紧随其后，利用剩余空间。
    - **移动端兼容**：通过 `order` 属性，确保移动端依然维持“关键词在前、搜索/切换在后”的两行紧凑布局。
    - **状态管理**：分页选项统一为 (20/40/80)，移除了多余的 50 选项。
- **测试结果**：
    - 桌面端：搜索栏居左，与关键词和按钮完美处于同一物理行。
    - 移动端：关键词行独立显示，搜索与按钮行层叠正确，粘性效果丝滑。

### 4. 经验 (Lessons)
- **布局灵活性**：利用 Tailwind 的 `order` 属性可以轻松实现同一 HTML 结构在不同断点下的“视觉换位”，避免了冗余的 DOM。
- **宽度分配**：对搜索栏进行百分比限宽（如 `lg:w-1/2`）在宽屏设计中能显著提升控制逻辑的可读性和操作性。
