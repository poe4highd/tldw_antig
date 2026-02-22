# 开发日志 (2026-02-16) - 任务：修复 API 回归错误与调度器阻塞

## 1. 需求 (Requirement)
- **背景**: 用户反馈新任务卡在 0%，且发现首页视频列表消失。
- **目标**: 修复代码中的 NameError，清理重复的后台进程，恢复处理流程。

## 2. 实施 (Implementation)
- **修复逻辑**: 
    - `backend/main.py`: 修复 `get_explore` 调用 `get_history` 时的参数缺失，并加固了异常捕获。
- **运维清理**:
    - 杀死了 2 个冗余的 `scheduler.py` 进程。
    - 重启了 `uvicorn` 和 `scheduler`，验证 API 响应恢复正常。

## 3. 回顾 (Review)
- **结果**: `/explore` API 恢复正常，任务系统回归就绪状态。
- **改动文件**: `backend/main.py`

## 4. 经验 (Lessons)
- **多实例防范**: 在单机环境下，必须严格通过脚本（如 `dev.sh`）或 PID 文件确保调度器等单例程序的唯一性，否则易引发数据库竞态。

# 开发日志 (2026-02-16) - 任务：修复书架页面视频缺失问题

## 1. 需求 (Requirement)
- **背景**: 用户发现手动提交的视频在处理完成后会出现在任务列表,但不会出现在书架页面。
- **目标**: 确保所有由用户提交并处理完成的视频都能正确出现在其书架中。

## 2. 实施 (Implementation)
- **根因分析**: `submissions` 表缺失 `task_id` 唯一约束,导致后端 `upsert` 操作因 SQL 错误而失败。
- **后端修复**: 
    - `backend/main.py` & `backend/process_task.py`: 将 `upsert` 改为更健壮的 `insert` + `try-update` 模式。
- **数据修复**:
    - `backend/scripts/fix_missing_submissions.py`: 扫描并补全了用户缺失的 3 条 `submissions` 记录。

## 3. 回顾 (Review)
- **结果**: 目标用户的书架已通过数据库验证恢复正常。系统逻辑现在具备故障自愈能力（即使缺失约束也能工作）。
- **改动文件**: 
    - `backend/main.py`
    - `backend/process_task.py`
    - `backend/scripts/fix_missing_submissions.py` (New)

## 4. 经验 (Lessons)
- **约束依赖**: 在不确定外部库或数据库 schema 严格程度时,应避免依赖特定字段的 `upsert` 行为,转而使用显式的 `insert` 捕获异常后再 `update` 的模式更安全。

# 开发日志 (2026-02-15) - 任务：优化视频处理提交流


## 1. 需求 (Requirement)
- **背景**: 用户提交视频处理后，系统会立即自动跳转到可能尚未完全准备好（如无字幕）的报告页面，导致用户困惑。
- **目标**: 实现“提交 -> 处理进度 (100%) -> 处理完成提示 -> 用户手动点击跳转”的受控流程。

## 2. 计划 (Plan)
- **前端重构**:
    - `frontend/app/tasks/page.tsx`: 
        - 移除 `pollStatus` 中的自动 `router.push`。
        - 增加 `isFinished` 状态，用于控制进度条完成后的 UI 切换。
        - 在进度条下方或替代位置增加“查看报告”按钮。
    - `frontend/translations/`: 
        - 补充 `tasks.statusCompleted` 和 `tasks.viewReport` 词条。

# 开发日志 (2026-02-15) - 任务：管理页 UI 精细化、双语支持与主题适配

## 1. 需求 (Requirement)
- **背景**: 管理页布局较为拥挤，且缺乏与主页一致的主题切换和多语言选择功能。
- **目标**: 实现黑白主题（与首页一致）、集成语言切换器、优化布局紧凑度（Compact UI）。

## 2. 实施 (Implementation)
- **前端**:
    - `app/admin/page.tsx`: 集成 `useTheme` 和 `useTranslation`，重构 Header 包含语言切换和主题切换。
    - `app/admin/visibility/page.tsx`: 全面翻新 UI，对齐新版 Admin 设计风格，支持自动追踪、可见性开关的双语提示。
    - `translations/en.json` & `zh.json`: 补充 `admin.visibility` 相关词条。
    - 统一使用 `bg-card-bg`, `border-card-border` 等 CSS 变量确保主题感知。

## 3. 回顾 (Review)
- **结果**: 管理后台现在具备了与前台一致的视觉体验，信息密度更高，且方便多语言用户操作。
- **改动文件**: 
    - `frontend/app/admin/page.tsx`
    - `frontend/app/admin/visibility/page.tsx`
    - `frontend/translations/en.json`
    - `frontend/translations/zh.json`

## 4. 经验 (Lessons)
- **UI 连贯性**: 对于管理端此类信息密集型页面，使用更窄的边距和更小的字号（如 `text-[10px]`）配以 `font-black` 可以在保持可读性的同时大幅提升专业感。

# 开发日志 (2026-02-15) - 任务：优化 dev.sh 防止后端挂起

## 1. 需求 (Requirement)
- **背景**: 发现由于 `uvicorn --reload` 产生的残留子进程占用端口，导致后端服务静默崩溃，主页列表消失。
- **目标**: 在 `dev.sh` 启动早期增加强力的进程清理逻辑。

## 2. 实施 (Implementation)
- **脚本优化**:
    - `dev.sh`: 
        - 增加了 `cleanup_stale_processes` 函数，通过进程名强制清理 `uvicorn`、`scheduler` 和 `process_task` 残留。
        - 增强了 `check_and_kill_port` 函数，使其能够同时清理多个关联 PID。

## 3. 回顾 (Review)
- **结果**: 解决了后端因端口占用无法启动的问题，确保了开发环境的自愈能力。
- **改动文件**: `dev.sh`

## 4. 经验 (Lessons)
- **多进程残留**: 在涉及 `multiprocessing` 的 Python Web 应用中，传统的单 PID 端口清理可能不完全，使用 `xargs` 和进程名正则扫描是更稳妥的做法。

# 开发日志 (2026-02-15) - 任务：修复频道名称显示为 ID 的问题

## 1. 需求 (Requirement)
- **背景**: 管理员发现“可见性管理”页面中，部分频道名称显示为 YouTube ID（如 `UCo2gxyermsLBSCxFHvJs0Zg`）。
- **目标**: 统一后端字段名，修复元数据提取逻辑，并补全存量数据的真实频道名称。

## 2. 实施 (Implementation)
- **后端代码**:
    - `backend/scripts/channel_tracker.py`: 将 `report_data` 中的 `channel_name` 统一为 `channel`。
    - `backend/main.py`: 
        - `/admin/visibility` 接口增加对 `channel` 和 `channel_name` 的兼容性读取。
        - 去除 `background_process` 中将 ID 作为名称落后的逻辑。
    - `backend/process_task.py`: 同步更新元数据处理逻辑。
- **数据迁移**:
    - `backend/scripts/fix_channel_names.py`: 扫描并补全了 13 条视频记录的真实频道名称。

## 3. 回顾 (Review)
- **结果**: 管理页面现在能正确显示频道中文名称。
- **改动文件**: 
    - `backend/scripts/channel_tracker.py`
    - `backend/main.py`
    - `backend/process_task.py`
    - `backend/scripts/fix_channel_names.py` (New)

## 4. 经验 (Lessons)
- **字段一致性**: 在快速迭代中,不同组件(如手动提交 vs 自动追踪)使用的 JSON 键名必须严格统一,否则会导致 UX 层面的显示异常。

# 开发日志 (2026-02-15) - 任务:管理页增加 LLM 用量追踪面板

## 1. 需求 (Requirement)
- **背景**: 管理员需要监控 LLM 的使用情况，包括模型、Token 消耗及预估费用。
- **目标**: 在 Admin 页面增加实时用量统计与历史记录面板。

## 2. 实施 (Implementation)
- **后端**:
    - `worker.py`: 在 `usage` 数据中记录实际使用的 LLM 模型名称。
    - `main.py`: 
        - 修复 `video_count` 统计为 0 的问题，改用后端列表计数。
        - 实现 `estimate_llm_usage` 算法：对缺失用量记录的旧视频，基于 `report_data` 中的文本字数（1:1.5 token 倍率）进行后期补全估算。
        - 修改 `/admin/stats` 统一聚合精确记录与估算成本。
- **前端**:
    - `app/admin/page.tsx`: 增加“LLM 总支出”概览卡片，新增用量追踪表格，并增加“估算数据”黄色标签。

## 3. 回顾 (Review)
- **结果**: 管理员现在可以直观地查看 LLM 的运营成本和单个视频的处理开销。UI 保持了深色极简风格。
- **改动文件**: 
    - `backend/worker.py`
    - `backend/main.py`
    - `frontend/app/admin/page.tsx`

## 4. 经验 (Lessons)
- **数据兼容性**: 在 API 层对旧数据（缺失模型字段）进行了默认值处理，确保了界面的稳定性。
- **图标一致性**: 使用 `Brain` 图标来统一 AI 相关功能的视觉语言。

# 开发日志 (2026-02-15) - 任务：清理绝对路径与增强 Cookie 指导

## 1. 需求 (Requirement)
- **背景**: 文档中存在本地绝对路径，且用户反馈需要更直观的手动获取 Cookie 指导。
- **目标**: 清理全局硬编码路径，并更新 `youtube_cookies_setup.md`。

## 2. 实施 (Implementation)
- **路径清理**: 扫描 `docs/` 和 `dev_docs/`，将 `/Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/` 替换为相对路径。
- **文档增强**: 在 `youtube_cookies_setup.md` 中增加了“推荐方法 B：使用浏览器插件手动导出”一节。

## 3. 回顾 (Review)
- **结果**: 文档现在可以在不同环境下正确引用文件，不再泄漏本地路径。用户获取 Cookie 的指导更加全面。
- **改动文件**: 
    - `docs/youtube_cookies_setup.md`
    - `dev_docs/dev_plan_supabase_20260117.md`
    - `dev_docs/implementation_plan_20260116.md`
    - `dev_docs/walkthrough_20260116.md`

## 4. 经验 (Lessons)
- **路径通用性**: 在编写技术文档或生成的实施计划时，应优先使用相对于项目根目录的路径，以确保文档在团队或不同机器间的可移植性。

# 开发日志 (2026-02-15)

## 任务：完善频道追踪系统文档与限额评估
### 1. 需求 (Requirement)
- **背景**: 用户询问频道自动更新状态及 5个/小时、50个/天限额的必要性。
- **目标**: 整理系统设计文档，并评估当前限额逻辑的合理性。

### 2. 实施 (Implementation)
- **`dev_docs/channel_tracking_design.md`**:
    - [NEW] 创建了详细的设计文档。
    - 记录了核心配置参数、运行机制、顺序调度逻辑。
- **`docs/youtube_cookies_setup.md`**:
    - 增加了手动导出 Cookie 的方法（推荐方法 B）。
    - 记录了 Cookie 的维护周期建议及失效重置逻辑。
- **评估结论**:
    - 限额在技术上并非强制（因为有顺序调度保障负载），但在业务上是必要的（防 YouTube IP 风控、控制 LLM 费用风险）。

### 3. 回顾 (Review)
- **结果**: 成功将分散的代码逻辑转化为书面文档，并完善了 Cookie 维护指南。确认了系统限额在防范异常增长和账单风险方面的价值。
- **改动文件**: `dev_docs/channel_tracking_design.md`, `docs/youtube_cookies_setup.md`。

### 4. 经验 (Lessons)
- **安全垫机制**: 即使底层算法具备天然弹性（如单线程/顺序执行），应用层仍应保留逻辑限额作为第二道防线，以应对第三方接口（如 YouTube API）的不可控风险。
