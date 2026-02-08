-- 003_likes_schema.sql
-- 存放位置: backend/supabase/migrations/003_likes_schema.sql
-- 描述: 用户对视频的点赞记录，作为“我的书架”的核心数据源之一

CREATE TABLE IF NOT EXISTS public.user_likes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id TEXT REFERENCES public.videos(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, video_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_user_likes_user_id ON public.user_likes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_likes_video_id ON public.user_likes(video_id);

-- 启用 RLS
ALTER TABLE public.user_likes ENABLE ROW LEVEL SECURITY;

-- 策略：用户只能管理自己的点赞
CREATE POLICY "Users can manage their own likes" ON public.user_likes
    FOR ALL USING (auth.uid() = user_id);

-- 同步更新 videos 表的互动数 (可选触发器，暂由 API 处理)
