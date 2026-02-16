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
    Key,
    Moon,
    Sun,
    Server
} from "lucide-react";
import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

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
    const { t, language } = useTranslation();
    const { theme, toggleTheme } = useTheme();
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
            <main className="min-h-screen bg-transparent text-foreground flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            </main>
        );
    }

    if (!isAuthorized) {
        return (
            <main className="min-h-screen bg-transparent text-foreground flex items-center justify-center p-6">
                <div className="bg-card-bg border border-card-border p-8 rounded-3xl w-full max-w-sm text-center shadow-2xl backdrop-blur-md">
                    <div className="w-16 h-16 bg-rose-500/10 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-black mb-2">{t("admin.subtitle")}</h2>
                    <p className="text-slate-500 mb-8 text-[10px] font-black uppercase tracking-widest">{t("admin.secretNote")}</p>

                    <div className="space-y-4">
                        <div className="relative">
                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="password"
                                placeholder={t("admin.placeholder")}
                                className="w-full pl-10 pr-4 py-3 bg-card-bg border border-card-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono"
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
                            className="w-full py-3 bg-indigo-500 text-white rounded-xl text-sm font-bold hover:bg-indigo-600 transition-all active:scale-[0.98] shadow-lg shadow-indigo-500/20"
                        >
                            {t("admin.enter")}
                        </button>
                    </div>

                    <Link href="/" className="inline-block mt-8 text-[10px] font-black text-slate-500 hover:text-indigo-400 uppercase tracking-widest transition-colors">
                        {t("common.back")}
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-transparent text-foreground p-4 md:p-8 font-sans selection:bg-indigo-500/30">
            {/* Glows */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
                <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
            </div>

            <header className="sticky top-0 z-[60] bg-background/80 backdrop-blur-xl border-b border-card-border -mx-4 px-4 md:-mx-8 md:px-8 h-14 md:h-16 flex items-center justify-between gap-4 mb-6 md:mb-8 transition-all duration-300">
                <div className="flex items-center gap-4">
                    <Link href="/admin" className="p-2 bg-card-bg/50 border border-card-border rounded-xl text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all group" title={t("admin.visibility.backToAdmin")}>
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    </Link>
                    <div>
                        <h1 className="text-lg md:text-xl font-black tracking-tighter leading-none">{t("admin.visibility.title")}</h1>
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 hidden sm:block">{t("admin.visibility.subtitle")}</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <LanguageSwitcher />
                    <button
                        onClick={toggleTheme}
                        className="p-2 bg-card-bg/50 border border-card-border rounded-xl text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all shadow-sm"
                    >
                        {theme === 'dark' ? <Sun className="w-4 h-4 md:w-5 md:h-5" /> : <Moon className="w-4 h-4 md:w-5 md:h-5" />}
                    </button>

                    <div className="h-6 w-px bg-card-border mx-1 hidden sm:block" />

                    <button
                        onClick={fetchData}
                        className="p-2 bg-card-bg border border-card-border rounded-xl text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all shadow-sm"
                        title={t("admin.refresh")}
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
                {/* 频道管理 */}
                <section className="bg-card-bg border border-card-border rounded-3xl p-6 backdrop-blur-sm">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                <Tv className="w-5 h-5" />
                            </div>
                            <h2 className="text-base font-black uppercase tracking-tight">{t("admin.visibility.channels")}</h2>
                            <span className="text-[9px] font-black text-slate-500 bg-slate-500/10 px-2 py-0.5 rounded-full uppercase">
                                {allChannels.length}
                            </span>
                        </div>
                    </div>

                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder={t("admin.visibility.searchChannels")}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-background border border-card-border rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                        {filteredChannels.map(channel => (
                            <div
                                key={channel.channel_id}
                                className="flex items-center justify-between p-2.5 bg-background/30 rounded-xl border border-card-border/50 hover:border-indigo-500/30 transition-all"
                            >
                                <div className="flex-1 min-w-0 mr-3">
                                    <p className="text-xs font-bold truncate uppercase tracking-tight">{channel.channel_name || channel.channel_id}</p>
                                </div>
                                <div className="flex items-center space-x-1.5">
                                    {/* 主页显示开关 */}
                                    <button
                                        onClick={() => updateChannel(channel.channel_id, { hidden_from_home: !channel.hidden_from_home })}
                                        disabled={saving === channel.channel_id}
                                        className={cn(
                                            "p-1.5 rounded-lg transition-all",
                                            channel.hidden_from_home
                                                ? "bg-rose-500/10 text-rose-500 hover:bg-rose-500/20"
                                                : "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"
                                        )}
                                        title={channel.hidden_from_home ? t("admin.visibility.hiddenFromHome") : t("admin.visibility.showOnHome")}
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
                                        className={cn(
                                            "p-1.5 rounded-lg transition-all",
                                            channel.track_new_videos
                                                ? "bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20"
                                                : "bg-slate-500/10 text-slate-500 hover:bg-slate-500/20"
                                        )}
                                        title={channel.track_new_videos ? t("admin.visibility.trackNew") : t("admin.visibility.noTrackNew")}
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
                            <div className="text-center py-12 rounded-2xl border border-card-border border-dashed col-span-2">
                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{t("admin.visibility.noChannels")}</p>
                            </div>
                        )}
                    </div>
                </section>

                {/* 视频管理 */}
                <section className="bg-card-bg border border-card-border rounded-3xl p-6 backdrop-blur-sm">
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <Video className="w-5 h-5" />
                        </div>
                        <h2 className="text-base font-black uppercase tracking-tight">{t("admin.visibility.videos")}</h2>
                        <span className="text-[9px] font-black text-slate-500 bg-slate-500/10 px-2 py-0.5 rounded-full uppercase">
                            {allVideos.length}
                        </span>
                    </div>

                    <div className="relative mb-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder={t("admin.visibility.searchVideos")}
                            value={videoSearchQuery}
                            onChange={(e) => setVideoSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-background border border-card-border rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                        {allVideos
                            .filter(v =>
                                v.title?.toLowerCase().includes(videoSearchQuery.toLowerCase()) ||
                                v.channel?.toLowerCase().includes(videoSearchQuery.toLowerCase()) ||
                                v.id.includes(videoSearchQuery)
                            )
                            .map(video => (
                                <div
                                    key={video.id}
                                    className={cn(
                                        "flex items-center space-x-3 p-2 rounded-xl border transition-all",
                                        video.hidden_from_home
                                            ? "bg-rose-500/5 border-rose-500/20"
                                            : "bg-background/30 border-card-border/50 hover:border-indigo-500/30"
                                    )}
                                >
                                    {video.thumbnail && (
                                        <div className="w-12 h-7 rounded-[4px] overflow-hidden border border-card-border/50 flex-shrink-0">
                                            <img
                                                src={video.thumbnail}
                                                alt={video.title}
                                                className="w-full h-full object-cover"
                                            />
                                        </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[10px] font-bold truncate uppercase tracking-tight">{video.title}</p>
                                    </div>
                                    <button
                                        onClick={() => updateVideo(video.id, !video.hidden_from_home)}
                                        disabled={saving === video.id}
                                        className={cn(
                                            "p-1.5 rounded-lg transition-all flex-shrink-0",
                                            video.hidden_from_home
                                                ? "bg-rose-500/10 text-rose-500 hover:bg-rose-500/20"
                                                : "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"
                                        )}
                                        title={video.hidden_from_home ? t("admin.visibility.hiddenFromHome") : t("admin.visibility.showOnHome")}
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
                            <div className="text-center py-12 rounded-2xl border border-card-border border-dashed col-span-2">
                                <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{t("admin.visibility.noVideos")}</p>
                            </div>
                        )}
                    </div>
                </section>
            </div>

            {/* 图例说明 */}
            <footer className="mt-8 p-6 bg-card-bg border border-card-border rounded-3xl backdrop-blur-sm">
                <p className="text-[10px] font-black text-slate-500 mb-3 uppercase tracking-widest">{t("admin.visibility.legend")}</p>
                <div className="flex flex-wrap gap-6 text-[10px] font-black uppercase tracking-tight">
                    <div className="flex items-center space-x-2">
                        <div className="p-1 px-2 rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/10">
                            <Eye className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-slate-500">{t("admin.visibility.legendHome")}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="p-1 px-2 rounded-md bg-rose-500/10 text-rose-500 border border-rose-500/10">
                            <EyeOff className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-slate-500">{t("admin.visibility.legendHidden")}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="p-1 px-2 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/10">
                            <Radio className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-slate-500">{t("admin.visibility.legendTrack")}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="p-1 px-2 rounded-md bg-slate-500/10 text-slate-500 border border-slate-500/10">
                            <CircleSlash className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-slate-500">{t("admin.visibility.legendNoTrack")}</span>
                    </div>
                </div>
            </footer>
        </main>
    );
}
