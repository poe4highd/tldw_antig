-- 005_privacy_schema.sql
-- 描述: 添加视频隐私控制和 RLS 性能优化

-- 1. 为 videos 表添加 is_public 和 user_id (冗余用于 RLS)
ALTER TABLE public.videos ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;
ALTER TABLE public.videos ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- 2. 尝试从 submissions 表同步已有的 user_id (回填历史数据)
-- 如果一个视频有多个提交者，取最早的一个作为“主所属人”，或者保持为 NULL（此时由 is_public 决定）
UPDATE public.videos v
SET user_id = (
    SELECT s.user_id 
    FROM public.submissions s 
    WHERE s.video_id = v.id 
    ORDER BY s.created_at ASC 
    LIMIT 1
)
WHERE v.user_id IS NULL;

-- 3. 创建索引优化性能
CREATE INDEX IF NOT EXISTS idx_videos_is_public_created ON public.videos(is_public, created_at DESC) WHERE is_public = TRUE;
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON public.videos(user_id) WHERE user_id IS NOT NULL;

-- 4. 更新 RLS 策略
-- 首先删除旧的过于宽松的策略 (如果有)
DROP POLICY IF EXISTS "Allow authenticated reads on videos" ON public.videos;
DROP POLICY IF EXISTS "Videos visibility" ON public.videos;

-- 创建新的高性能隐私策略
CREATE POLICY "Videos visibility" ON public.videos
    FOR SELECT USING (
        is_public = TRUE OR 
        user_id = auth.uid()
    );

-- 5. 更新 submissions 表的 RLS (确保一致性)
-- 之前的策略是 is_public = TRUE，现在应该保持一致
DROP POLICY IF EXISTS "Allow access to public submissions" ON public.submissions;
CREATE POLICY "Allow access to public submissions" ON public.submissions
    FOR SELECT USING (is_public = TRUE);
