-- 001_initial_schema.sql
-- 存放位置: backend/supabase/migrations/001_initial_schema.sql
-- 描述: Read-Tube 核心数据库架构定义

-- 1. 视频主表 (存储去重后的处理结果)
CREATE TABLE IF NOT EXISTS public.videos (
    id TEXT PRIMARY KEY, -- YouTube ID 或文件精简哈希
    title TEXT NOT NULL,
    thumbnail TEXT,
    media_path TEXT, -- 存储在后端本地或对象存储的相对路径
    report_data JSONB, -- 存储段落信息及 AI 分析结果
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    view_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0
);

-- 2. 用户提交记录表 (关联用户与视频，处理权限)
CREATE TABLE IF NOT EXISTS public.submissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    task_id TEXT, -- 后端任务 ID
    is_public BOOLEAN DEFAULT FALSE, -- 上传内容的共享状态
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. 评论与讨论表
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE, -- 支持回复
    likes_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. 行为分析与埋点表
CREATE TABLE IF NOT EXISTS public.analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT REFERENCES public.videos(id) ON DELETE SET NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- view, subtitle_click, play_pause etc.
    event_data JSONB, -- 存储具体时间戳或元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 启用权限控制 (RLS) - 暂时允许认证用户读取，后续可细化
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics ENABLE ROW LEVEL SECURITY;

-- 允许所有登录用户读取视频(为了去重查重)
CREATE POLICY "Allow authenticated reads on videos" ON public.videos FOR SELECT USING (auth.role() = 'authenticated');

-- 允许用户管理自己的提交记录
CREATE POLICY "Users can manage their own submissions" ON public.submissions
    FOR ALL USING (auth.uid() = user_id);

-- 允许用户读取公开视频的提交记录（用于共享查看）
CREATE POLICY "Allow access to public submissions" ON public.submissions
    FOR SELECT USING (is_public = TRUE);
