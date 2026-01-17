-- 001_initial_schema.sql
-- 存放位置: backend/supabase/migrations/001_initial_schema.sql
-- 描述: Read-Tube 核心数据库架构定义

-- 1. 用户资料表 (关联 Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. 视频主表 (存储去重后的处理结果)
CREATE TABLE IF NOT EXISTS public.videos (
    id TEXT PRIMARY KEY, -- YouTube ID 或文件精简哈希
    title TEXT NOT NULL,
    thumbnail TEXT,
    media_path TEXT, -- 存储在后端本地或对象存储的相对路径
    report_data JSONB, -- 存储段落信息及 AI 分析结果
    category TEXT, -- 用于热力图分类
    status TEXT DEFAULT 'queued', -- queued, processing, completed, failed
    usage JSONB, -- 存储成本和 Token 详情
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    view_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0
);

-- 3. 用户提交记录表 (关联用户与视频，处理权限)
CREATE TABLE IF NOT EXISTS public.submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    task_id TEXT, -- 后端任务 ID
    is_public BOOLEAN DEFAULT FALSE, -- 上传内容的共享状态
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. 评论与讨论表
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE, -- 支持回复
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. 行为分析与埋点表 (原 analytics)
CREATE TABLE IF NOT EXISTS public.interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT REFERENCES public.videos(id) ON DELETE SET NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- view, subtitle_click, play_pause etc.
    event_data JSONB, -- 存储具体时间戳或元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. 热力图管理视图
CREATE OR REPLACE VIEW public.admin_heatmap_data AS
SELECT 
    v.category,
    EXTRACT(HOUR FROM i.created_at) as hour_of_day,
    COUNT(*) as intensity
FROM public.interactions i
JOIN public.videos v ON i.video_id = v.id
WHERE i.event_type = 'subtitle_click'
GROUP BY v.category, hour_of_day;

-- 启用权限控制 (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interactions ENABLE ROW LEVEL SECURITY;

-- 策略定义
CREATE POLICY "公开资料所有人可见" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "用户可更新自己的资料" ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Allow authenticated reads on videos" ON public.videos FOR SELECT USING (true);

CREATE POLICY "Users can manage their own submissions" ON public.submissions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Allow access to public submissions" ON public.submissions
    FOR SELECT USING (is_public = TRUE);
