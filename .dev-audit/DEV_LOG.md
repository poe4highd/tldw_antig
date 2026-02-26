# 开发日志 (2026-02-25) - 最近任务：摘要时间轴条

## 1. 需求 (Requirement)
- **背景**: 从截图产品 UI 借鉴，在结果页视频播放器下方添加彩色时间轴条，直观展示 7 条 AI 摘要对应的视频时段。
- **目标**: 7 段彩色条，宽度正比时长，当前播放段高亮，点击跳转，悬停 tooltip，色盲友好配色。

## 2. 计划 (Plan)
- 添加 `videoDuration` state，分别从 YouTube `onPlayerReady` 和 audio `onLoadedMetadata` 获取时长
- 解析 `result.summary` 字符串，提取每行 startTime
- end_time[i] = start_time[i+1] - 1，最后项用 videoDuration
- 用 Okabe-Ito 7色（色盲友好）渲染色段
- 插入位置：视频播放器 `</div>` 与 Middle Section 之间

## 3. 回顾 (Review)
- 修改文件：`frontend/app/result/[id]/page.tsx`，共 4 处改动
- 新增 state：`videoDuration`
- 更新：`onPlayerReady` 调用 `getDuration()`，新增 `handleAudioLoadedMetadata`，`<audio>` 标签加 `onLoadedMetadata`
- 新增：Summary Timeline Bar 内联组件（IIFE 写法），无需新建文件
- 条件渲染：`result.summary && videoDuration > 0`，无摘要或时长未就绪时不渲染

## 4. 经验 (Lessons)
- YouTube player `getDuration()` 在 `onReady` 时已可调用，不需要额外等待
- IIFE 内联写法避免新建组件文件，适合一次性逻辑
- `Math.max(..., 1)` 防止宽度为 0 的边缘情况（第一条摘要时间戳为 0 时）

---

# 开发日志 (2026-02-25) - 任务：移除本地缩略图依赖，改用频道头像与 YouTube CDN

## 1. 需求 (Requirement)
- **背景**: 首页大量视频缩略图显示为黑色方块，原因是 `backend/downloads/` 本地文件丢失。
- **根本问题**: 设计错误——不该把缩略图保存到本地，应直接用公共 URL。
- **目标**: 文本模式展示频道头像（来源标识），缩略图模式用 YouTube CDN 封面图，彻底消除本地文件依赖。

## 2. 计划 (Plan)
- 添加 `getYoutubeThumbnail(videoId)` 辅助函数，生成 `img.youtube.com/vi/{id}/hqdefault.jpg`
- **thumb 模式**：`item.thumbnail`（本地文件）→ YouTube CDN URL
- **detailed 文本模式**：视频缩略图矩形 → 40px 圆形频道头像（带频道色彩环）
- **compact 文本模式**：微型矩形缩略图 → 24px 圆形频道头像（带频道色彩环）

## 3. 回顾 (Review)
- 修改文件：`frontend/app/page.tsx`，共 3 处替换 + 1 个新函数
- thumb 模式：直接读 YouTube 公共 CDN，无需本地文件，永不丢失
- 文本模式：频道头像复用 `getChannelColor` 生成的彩色环，与 thumb 模式底部设计统一
- 降级策略：非 YouTube 视频（11 位 ID 以外）自动降级到 `ui-avatars.com` 生成头像

## 4. 经验 (Lessons)
- **不要缓存公共资源**：YouTube 封面图有稳定的公共 CDN，直接引用比本地存储更简单、更可靠
- **UI 语义优先**：文本模式下显示"频道头像"（来源标识）比显示"视频缩略图"（内容预览）语义更准确

---

# 开发日志 (2026-02-23) - 任务：修改频道默认追踪行为

## 1. 需求 (Requirement)
- **背景**: 当前新视频提交时，如果是新频道，系统会默认开启对此频道的追踪，导致自动抓取过多无关视频。
- **目标**: 将新频道的默认追踪状态设为 `false`。新频道被发现后，必须由管理员在后台手动开启追踪。

## 2. 计划 (Plan)
- **数据库**: 修改 `004_visibility_schema.sql` 迁移文件中的默认值，将 `track_new_videos` 的 `DEFAULT TRUE` 改为 `DEFAULT FALSE`。
- **后端追踪器**: 修改 `backend/scripts/channel_tracker.py`，逻辑从“排除型追踪”（追踪所有未禁用的）改为“包含型追踪”（仅追踪明确启用的）。
- **前端管理页**: 修改 `frontend/app/admin/visibility/page.tsx`，将未配置频道的默认显示状态改为不追踪。

## 3. 回顾 (Review)
- **数据库**: 成功修改了 `track_new_videos` 的默认值为 `false`。
- **后端**: 重构了 `channel_tracker.py`，逻辑由“黑名单过滤”改为“白名单包含”，极大提高了追踪的准确性和可控性。
- **前端**: 同步更新了管理界面的默认渲染逻辑，消除了前后端状态不一致的情况。

## 4. 经验 (Lessons)
- **包含 vs 排除**: 在处理自动化追踪逻辑时，基于安全和资源成本考虑，采用“显式开启”的包含型逻辑通常比“默认全开”的排除型逻辑更健壮，且更容易扩展。
