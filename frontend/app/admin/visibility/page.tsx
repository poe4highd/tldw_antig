"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
    ArrowLeft,
    Eye,
    EyeOff,
    Radio,
    CircleSlash,
    RefreshCw,
    Save,
    Search,
    Tv,
    Video,
    Loader2,
    Lock,
    Unlock,
    Key
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ChannelSetting {
    channel_id: string;
    channel_name: string | null;
    hidden_from_home: boolean;
    track_new_videos: boolean;
}

interface VideoItem {
    id: string;
    title: string;
    thumbnail: string | null;
    hidden_from_home: boolean;
    channel: string | null;
    channel_id: string | null;
}

export default function VisibilityPage() {
    const [channels, setChannels] = useState<ChannelSetting[]>([]);
    const [allVideos, setAllVideos] = useState<VideoItem[]>([]);
    const [knownChannels, setKnownChannels] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [videoSearchQuery, setVideoSearchQuery] = useState("");
    const [adminKey, setAdminKey] = useState<string>("");
    const [isAuthorized, setIsAuthorized] = useState<boolean>(true);

    useEffect(() => {
        const storedKey = localStorage.getItem("tldw_admin_key");
        if (storedKey) {
            setAdminKey(storedKey);
        }
    }, []);

    useEffect(() => {
        if (adminKey !== undefined) {
            fetchData();
        }
    }, [adminKey]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/admin/visibility`, {
                headers: { "X-Admin-Key": adminKey }
            });
            if (res.status === 403) {
                setIsAuthorized(false);
                setLoading(false);
                return;
            }
            if (res.ok) {
                setIsAuthorized(true);
                const data = await res.json();
                setChannels(data.channels || []);
                setAllVideos(data.all_videos || []);
                setKnownChannels(data.known_channels || {});
            }
        } catch (err) {
            console.error("Failed to fetch visibility settings:", err);
        }
        setLoading(false);
    };

    const handleSaveKey = (newKey: string) => {
        setAdminKey(newKey);
        localStorage.setItem("tldw_admin_key", newKey);
        fetchData();
    };

    const updateChannel = async (channelId: string, update: Partial<ChannelSetting>) => {
        setSaving(channelId);
        try {
            const existingChannel = channels.find(c => c.channel_id === channelId);
            const res = await fetch(`${API_BASE}/admin/visibility/channel`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Admin-Key": adminKey
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    channel_name: update.channel_name ?? existingChannel?.channel_name ?? knownChannels[channelId],
                    hidden_from_home: update.hidden_from_home ?? existingChannel?.hidden_from_home ?? false,
                    track_new_videos: update.track_new_videos ?? existingChannel?.track_new_videos ?? true
                })
            });
            if (res.ok) {
                await fetchData();
            }
        } catch (err) {
            console.error("Failed to update channel:", err);
        }
        setSaving(null);
    };

    const updateVideo = async (videoId: string, hidden: boolean) => {
        setSaving(videoId);
        try {
            const res = await fetch(`${API_BASE}/admin/visibility/video`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Admin-Key": adminKey
                },
                body: JSON.stringify({ video_id: videoId, hidden_from_home: hidden })
            });
            if (res.ok) {
                await fetchData();
            }
        } catch (err) {
            console.error("Failed to update video:", err);
        }
        setSaving(null);
    };

    // 合并已配置频道和已知频道
    const allChannels = React.useMemo(() => {
        const map = new Map<string, ChannelSetting & { isKnown?: boolean }>();

        // 先添加已配置的
        channels.forEach(c => map.set(c.channel_id, { ...c, isKnown: false }));

        // 添加已知但未配置的
        Object.entries(knownChannels).forEach(([id, name]) => {
            if (!map.has(id)) {
                map.set(id, {
                    channel_id: id,
                    channel_name: name,
                    hidden_from_home: false,
                    track_new_videos: true,
                    isKnown: true
                });
            }
        });

        return Array.from(map.values());
    }, [channels, knownChannels]);

    const filteredChannels = allChannels.filter(c =>
        c.channel_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (c.channel_name && c.channel_name.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    if (loading) {
        return (
            <main className="min-h-screen bg-background text-foreground flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </main>
        );
    }

    if (!isAuthorized) {
        return (
            <main className="min-h-screen bg-background text-foreground flex items-center justify-center p-6">
                <div className="bg-card border border-card-border p-8 rounded-2xl w-full max-w-md text-center shadow-xl backdrop-blur-sm">
                    <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">需要管理员权限</h2>
                    <p className="text-muted-foreground mb-8 text-sm">请输入管理员密钥以继续操作。如果您不清楚密钥，请联系系统管理员。</p>

                    <div className="space-y-4">
                        <div className="relative">
                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input
                                type="password"
                                placeholder="输入管理员密钥..."
                                className="w-full pl-10 pr-4 py-3 bg-background border border-card-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        handleSaveKey((e.target as HTMLInputElement).value);
                                    }
                                }}
                            />
                        </div>
                        <button
                            onClick={(e) => {
                                const input = e.currentTarget.previousElementSibling?.querySelector('input');
                                if (input) handleSaveKey(input.value);
                            }}
                            className="w-full py-3 bg-primary text-primary-foreground rounded-xl text-sm font-semibold hover:bg-primary/90 transition-all active:scale-[0.98]"
                        >
                            身份验证
                        </button>
                    </div>

                    <Link href="/" className="inline-block mt-6 text-sm text-muted-foreground hover:text-foreground transition-colors">
                        返回首页
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-background text-foreground p-6 md:p-10">
            <header className="mb-8">
                <Link href="/admin" className="inline-flex items-center space-x-2 text-primary hover:text-primary/80 text-sm font-medium mb-4 group transition-colors">
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>返回管理中心</span>
                </Link>
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold mb-1">可见性管理</h1>
                        <p className="text-muted-foreground text-sm">控制视频和频道在主页的显示状态</p>
                    </div>
                    <button
                        onClick={fetchData}
                        className="p-2 rounded-lg bg-card border border-card-border hover:bg-accent transition-colors"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* 频道管理 */}
                <section className="bg-card border border-card-border rounded-2xl p-6">
                    <div className="flex items-center space-x-3 mb-6">
                        <Tv className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold">频道管理</h2>
                        <span className="text-xs text-muted-foreground bg-accent px-2 py-0.5 rounded-full">
                            {allChannels.length} 个频道
                        </span>
                    </div>

                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="搜索频道..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-background border border-card-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[500px] overflow-y-auto pr-2">
                        {filteredChannels.map(channel => (
                            <div
                                key={channel.channel_id}
                                className="flex items-center justify-between p-2 bg-background/50 rounded-lg border border-transparent hover:border-card-border transition-colors"
                            >
                                <div className="flex-1 min-w-0 mr-2">
                                    <p className="text-sm font-medium truncate">{channel.channel_name || channel.channel_id}</p>
                                </div>
                                <div className="flex items-center space-x-1">
                                    {/* 主页显示开关 */}
                                    <button
                                        onClick={() => updateChannel(channel.channel_id, { hidden_from_home: !channel.hidden_from_home })}
                                        disabled={saving === channel.channel_id}
                                        className={`p-1.5 rounded-md transition-colors ${channel.hidden_from_home
                                            ? "bg-red-500/10 text-red-500 hover:bg-red-500/20"
                                            : "bg-green-500/10 text-green-500 hover:bg-green-500/20"
                                            }`}
                                        title={channel.hidden_from_home ? "主页已隐藏" : "主页显示中"}
                                    >
                                        {saving === channel.channel_id ? (
                                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        ) : channel.hidden_from_home ? (
                                            <EyeOff className="w-3.5 h-3.5" />
                                        ) : (
                                            <Eye className="w-3.5 h-3.5" />
                                        )}
                                    </button>

                                    {/* 追踪开关 */}
                                    <button
                                        onClick={() => updateChannel(channel.channel_id, { track_new_videos: !channel.track_new_videos })}
                                        disabled={saving === channel.channel_id}
                                        className={`p-1.5 rounded-md transition-colors ${channel.track_new_videos
                                            ? "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"
                                            : "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20"
                                            }`}
                                        title={channel.track_new_videos ? "自动追踪新视频" : "不追踪新视频"}
                                    >
                                        {channel.track_new_videos ? (
                                            <Radio className="w-3.5 h-3.5" />
                                        ) : (
                                            <CircleSlash className="w-3.5 h-3.5" />
                                        )}
                                    </button>
                                </div>
                            </div>
                        ))}
                        {filteredChannels.length === 0 && (
                            <p className="text-center text-muted-foreground py-8 col-span-2">没有找到频道</p>
                        )}
                    </div>
                </section>

                {/* 视频管理 */}
                <section className="bg-card border border-card-border rounded-2xl p-6">
                    <div className="flex items-center space-x-3 mb-6">
                        <Video className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold">视频管理</h2>
                        <span className="text-xs text-muted-foreground bg-accent px-2 py-0.5 rounded-full">
                            {allVideos.length} 个视频
                        </span>
                        <span className="text-xs text-red-500 bg-red-500/10 px-2 py-0.5 rounded-full">
                            {allVideos.filter(v => v.hidden_from_home).length} 隐藏
                        </span>
                    </div>

                    {/* 搜索 */}
                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="搜索视频..."
                            value={videoSearchQuery}
                            onChange={(e) => setVideoSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-background border border-card-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[500px] overflow-y-auto pr-2">
                        {allVideos
                            .filter(v =>
                                v.title?.toLowerCase().includes(videoSearchQuery.toLowerCase()) ||
                                v.channel?.toLowerCase().includes(videoSearchQuery.toLowerCase()) ||
                                v.id.includes(videoSearchQuery)
                            )
                            .map(video => (
                                <div
                                    key={video.id}
                                    className={`flex items-center space-x-2 p-2 rounded-lg border transition-colors ${video.hidden_from_home
                                        ? "bg-red-500/5 border-red-500/20"
                                        : "bg-background/50 border-transparent hover:border-card-border"
                                        }`}
                                >
                                    {video.thumbnail && (
                                        <img
                                            src={video.thumbnail}
                                            alt={video.title}
                                            className="w-12 h-7 object-cover rounded flex-shrink-0"
                                        />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs font-medium truncate">{video.title}</p>
                                    </div>
                                    <button
                                        onClick={() => updateVideo(video.id, !video.hidden_from_home)}
                                        disabled={saving === video.id}
                                        className={`p-1.5 rounded-md transition-colors flex-shrink-0 ${video.hidden_from_home
                                            ? "bg-red-500/10 text-red-500 hover:bg-red-500/20"
                                            : "bg-green-500/10 text-green-500 hover:bg-green-500/20"
                                            }`}
                                        title={video.hidden_from_home ? "已隐藏 - 点击恢复" : "显示中 - 点击隐藏"}
                                    >
                                        {saving === video.id ? (
                                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        ) : video.hidden_from_home ? (
                                            <EyeOff className="w-3.5 h-3.5" />
                                        ) : (
                                            <Eye className="w-3.5 h-3.5" />
                                        )}
                                    </button>
                                </div>
                            ))}
                        {allVideos.length === 0 && (
                            <p className="text-center text-muted-foreground py-8 col-span-2">没有视频</p>
                        )}
                    </div>
                </section>
            </div>

            {/* 图例说明 */}
            <footer className="mt-8 p-4 bg-card border border-card-border rounded-xl">
                <p className="text-sm text-muted-foreground mb-2">图标说明：</p>
                <div className="flex flex-wrap gap-4 text-xs">
                    <div className="flex items-center space-x-2">
                        <Eye className="w-4 h-4 text-green-500" />
                        <span>主页显示中</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <EyeOff className="w-4 h-4 text-red-500" />
                        <span>主页已隐藏</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <Radio className="w-4 h-4 text-blue-500" />
                        <span>自动追踪新视频</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <CircleSlash className="w-4 h-4 text-gray-500" />
                        <span>不追踪新视频</span>
                    </div>
                </div>
            </footer>
        </main>
    );
}
