-- 002_keyword_schema.sql
-- 存放位置: backend/supabase/migrations/002_keyword_schema.sql
-- 描述: 关键词多对多模型及频率统计接口

-- 1. 关键词主表
CREATE TABLE IF NOT EXISTS public.keywords (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. 视频与关键词关联表 (多对多)
CREATE TABLE IF NOT EXISTS public.video_keywords (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES public.keywords(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(video_id, keyword_id)
);

-- 3. 索引优化
CREATE INDEX IF NOT EXISTS idx_video_keywords_video_id ON public.video_keywords(video_id);
CREATE INDEX IF NOT EXISTS idx_video_keywords_keyword_id ON public.video_keywords(keyword_id);
CREATE INDEX IF NOT EXISTS idx_keywords_count ON public.keywords(count DESC);

-- 启用权限控制 (RLS)
ALTER TABLE public.keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.video_keywords ENABLE ROW LEVEL SECURITY;

-- 策略定义
CREATE POLICY "Keywords are public readable" ON public.keywords FOR SELECT USING (true);
CREATE POLICY "Video keywords are public readable" ON public.video_keywords FOR SELECT USING (true);
