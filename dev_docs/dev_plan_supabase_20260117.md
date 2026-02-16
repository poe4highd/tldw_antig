# Supabase 数据库架构设计方案

本方案详细说明了 `tldw` 应用的数据库架构设计，旨在支持现有 UI 功能，包括转录结果展示、管理后端分析（热力图、热门视频）以及用户互动（评论、点赞）。

## 变更建议

建议在 Supabase 数据库中增加以下表结构及扩展现有表。

### 核心组件

#### [修改] [001_initial_schema.sql](file:///backend/supabase/migrations/001_initial_schema.sql)

我们将优化现有架构，以更好地匹配当前的数据结构。

- **`videos` 表**: 
    - 增加 `category` (text): 用于支持管理后台的热力图分类。
    - 增加 `status` (text): 追踪处理状态（'queued', 'processing', 'completed', 'failed'）。
    - 增加 `usage` (jsonb): 存储成本和 Token 详情（`duration`, `whisper_cost`, `llm_cost` 等）。
- **`profiles` 表 [新]**:
    - `id` (uuid, 引用 `auth.users`)
    - `username` (text): 用户名。
    - `avatar_url` (text): 头像地址。
    - `created_at` (timestamptz)
- **`interactions` 表 (即原 `analytics` 表)**:
    - 确保 `event_type` 包含 `subtitle_click`。
    - `event_data` 将存储 `{selected_time: number}` 用于生成热力图。

---

### 数据库架构定义 (SQL)

```sql
-- 用户资料表，用于显示用户数据
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 扩展视频表
ALTER TABLE public.videos 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'queued',
ADD COLUMN IF NOT EXISTS category TEXT,
ADD COLUMN IF NOT EXISTS usage JSONB;

-- 权限控制 (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "公开资料所有人可见" 
ON public.profiles FOR SELECT USING (true);

CREATE POLICY "用户可更新自己的资料" 
ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 专门为热力图设计的管理视图
CREATE OR REPLACE VIEW public.admin_heatmap_data AS
SELECT 
    v.category,
    EXTRACT(HOUR FROM a.created_at) as hour_of_day,
    COUNT(*) as intensity
FROM public.analytics a
JOIN public.videos v ON a.video_id = v.id
WHERE a.event_type = 'subtitle_click'
GROUP BY v.category, hour_of_day;
```

## 验证计划

### 自动化测试
- 运行 `backend/tests`（如果存在），确保数据序列化没有回退。
- 在本地 Postgres 或 Supabase 实例上运行 SQL 以通过语法校验。

### 手动验证
1. **架构检查**: 应用迁移后，在 Supabase Dashboard 中确认表结构。
2. **数据流验证**:
    - 处理一个视频，确认数据库中视频的 `status` 和 `usage` 已更新。
    - 发表评论，确认显示正确的用户信息。
    - 在 UI 中点击字幕，确认 `analytics` 表中生成了类型为 `subtitle_click` 的记录。
3. **管理后台**: 确认热力图能根据新的 `admin_heatmap_data` 视图正确聚合数据。
