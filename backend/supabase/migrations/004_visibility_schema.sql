-- 004_visibility_schema.sql
-- 存放位置: backend/supabase/migrations/004_visibility_schema.sql
-- 描述: 视频与频道可见性管理功能

-- 1. 频道设置表（管理频道级别的显示和追踪配置）
CREATE TABLE IF NOT EXISTS public.channel_settings (
    channel_id TEXT PRIMARY KEY,             -- YouTube 频道 ID（如 @handle 或 UCxxxx）
    channel_name TEXT,                       -- 频道名称（便于管理页面显示）
    hidden_from_home BOOLEAN DEFAULT FALSE,  -- 是否在主页隐藏该频道所有视频
    track_new_videos BOOLEAN DEFAULT TRUE,   -- 是否自动追踪新视频
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 为 videos 表添加单个视频的隐藏字段
ALTER TABLE public.videos ADD COLUMN IF NOT EXISTS hidden_from_home BOOLEAN DEFAULT FALSE;

-- 3. 添加索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_videos_hidden ON public.videos(hidden_from_home) WHERE hidden_from_home = TRUE;
CREATE INDEX IF NOT EXISTS idx_channel_settings_hidden ON public.channel_settings(hidden_from_home) WHERE hidden_from_home = TRUE;

-- 4. 启用 RLS
ALTER TABLE public.channel_settings ENABLE ROW LEVEL SECURITY;

-- 5. 策略定义（允许所有人读取，仅管理员可写 - 暂时简化为允许所有操作）
CREATE POLICY "Allow all on channel_settings" ON public.channel_settings FOR ALL USING (true);

-- 6. 初始化数据：隐藏 @mingjinglive 频道
INSERT INTO public.channel_settings (channel_id, channel_name, hidden_from_home, track_new_videos)
VALUES ('@mingjinglive', '明镜live', TRUE, FALSE)
ON CONFLICT (channel_id) DO UPDATE SET 
    hidden_from_home = TRUE,
    track_new_videos = FALSE,
    updated_at = NOW();

-- 7. 隐藏视频 0_zgry0AGqU
UPDATE public.videos SET hidden_from_home = TRUE WHERE id = '0_zgry0AGqU';
