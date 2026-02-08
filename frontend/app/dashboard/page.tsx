"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
    LayoutGrid,
    List,
    Plus,
    Search,
    Youtube,
    FileUp,
    Share2,
    Lock,
    ArrowRight,
    Menu,
    Heart,
    Eye,
    Calendar,
    Clock,
    Columns2
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { supabase } from "@/utils/supabase";
import { getApiBase } from "@/utils/api";
import { Sidebar } from "@/components/Sidebar";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Mock Data removed

import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";

export default function DashboardPage() {
    const { t, language } = useTranslation();
    const { theme } = useTheme();
    const [viewMode, setViewMode] = useState<"thumb" | "text-single" | "text-double">("thumb");
    const [density, setDensity] = useState<"detailed" | "compact">("detailed");
    const [limit, setLimit] = useState(20);
    const [searchQuery, setSearchQuery] = useState("");
    const [user, setUser] = useState<{
        id: string;
        email?: string;
        user_metadata?: {
            full_name?: string;
            avatar_url?: string;
        };
    } | null>(null);
    const [videos, setVideos] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const router = useRouter();

    // 1. Read preference from localStorage on init
    useEffect(() => {
        const savedViewMode = localStorage.getItem("rt-dashboard-view-mode") as any;
        if (["thumb", "text-single", "text-double"].includes(savedViewMode)) {
            setViewMode(savedViewMode);
        }
        const savedDensity = localStorage.getItem("rt-dashboard-density") as any;
        if (["detailed", "compact"].includes(savedDensity)) {
            setDensity(savedDensity);
        }
        const savedLimit = localStorage.getItem("rt-dashboard-limit");
        if (savedLimit) setLimit(parseInt(savedLimit));
    }, []);

    // 2. Save preference to localStorage when changed
    useEffect(() => {
        localStorage.setItem("rt-dashboard-view-mode", viewMode);
        localStorage.setItem("rt-dashboard-density", density);
        localStorage.setItem("rt-dashboard-limit", limit.toString());
    }, [viewMode, density, limit]);

    // 3. Parallel Session Check + Data Prefetch
    useEffect(() => {
        let isMounted = true;

        const initializeDashboard = async () => {
            // Start fetching session and prepare API call in parallel
            const sessionPromise = supabase.auth.getSession();

            const { data: { session } } = await sessionPromise;

            if (!isMounted) return;

            if (!session) {
                router.push("/login");
                return;
            }

            setUser(session.user);

            // Immediately start fetching data after user is confirmed
            const apiBase = getApiBase();
            const url = new URL(`${apiBase}/bookshelf`);
            url.searchParams.append("user_id", session.user.id);
            url.searchParams.append("limit", limit.toString());

            try {
                const response = await fetch(url.toString());
                const data = await response.json();

                if (!isMounted) return;

                if (data.history) {
                    const formattedVideos = data.history.map((item: any) => ({
                        id: item.id,
                        title: item.title,
                        thumbnail: item.thumbnail,
                        source: item.id.length === 11 ? "youtube" : "upload",
                        isPublic: true,
                        is_liked: item.is_liked || item.source === "like",
                        summary: item.summary,
                        keywords: item.keywords,
                        date: new Date(item.mtime).toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit'
                        }).replace(/\//g, '-')
                    }));
                    setVideos(formattedVideos);
                }
            } catch (error) {
                console.error("Failed to fetch bookshelf:", error);
            } finally {
                if (isMounted) setIsLoading(false);
            }
        };

        initializeDashboard();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!session) {
                router.push("/login");
            } else {
                setUser(session.user);
            }
        });

        return () => {
            isMounted = false;
            subscription.unsubscribe();
        };
    }, [router, limit, language]);

    // 4. Silent refresh for limit/language changes when already loaded
    const fetchHistory = async (silent = true) => {
        if (!user?.id) return;
        if (!silent) setIsLoading(true);

        try {
            const apiBase = getApiBase();
            const url = new URL(`${apiBase}/bookshelf`);
            url.searchParams.append("user_id", user.id);
            url.searchParams.append("limit", limit.toString());

            const response = await fetch(url.toString());
            const data = await response.json();

            if (data.history) {
                const formattedVideos = data.history.map((item: any) => ({
                    id: item.id,
                    title: item.title,
                    thumbnail: item.thumbnail,
                    source: item.id.length === 11 ? "youtube" : "upload",
                    isPublic: true,
                    is_liked: item.is_liked || item.source === "like",
                    summary: item.summary,
                    keywords: item.keywords,
                    date: new Date(item.mtime).toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit'
                    }).replace(/\//g, '-')
                }));
                setVideos(formattedVideos);
            }
        } catch (error) {
            console.error("Failed to fetch history:", error);
        } finally {
            if (!silent) setIsLoading(false);
        }
    };

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/");
    };

    const handleLike = async (e: React.MouseEvent, videoId: string) => {
        e.preventDefault();
        e.stopPropagation();

        if (!user) return;

        try {
            const apiBase = getApiBase();
            const response = await fetch(`${apiBase}/like`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_id: videoId, user_id: user.id })
            });
            const data = await response.json();
            if (data.status === "success") {
                setVideos(prev => prev.map(video =>
                    video.id === videoId ? { ...video, is_liked: data.action === "liked" } : video
                ));
            }
        } catch (error) {
            console.error("Failed to toggle like:", error);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex font-sans transition-colors duration-300">
            <Sidebar
                user={user}
                onSignOut={handleSignOut}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            {/* Main Content */}
            <main className="flex-grow min-w-0 p-4 md:p-10 bg-transparent relative">
                {/* Background Glows */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
                    <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
                </div>

                {/* Mobile Header */}
                <header className="flex items-center justify-between mb-8 md:hidden">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="p-2 -ml-2 text-slate-400 hover:text-foreground hover:bg-card-bg rounded-xl transition-all"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                    <div className="flex items-center space-x-2">
                        <img src="/icon.png" alt="Logo" className="w-6 h-6" />
                        <span className="font-black tracking-tighter">{t("marketing.title")}</span>
                    </div>
                    <div className="w-10"></div>
                </header>

                {/* Header Section */}
                <header className="relative z-10 mb-8">
                    <div className="flex flex-col">
                        <h1 className={cn(
                            "text-xl md:text-3xl font-black tracking-tight mb-1",
                            theme === 'dark' ? "bg-gradient-to-r from-foreground via-foreground to-slate-500 bg-clip-text text-transparent" : "text-indigo-900"
                        )}>
                            {language === 'zh' ? "我的书架" : "My Bookshelf"}
                        </h1>
                        <p className={cn(
                            "text-xs md:text-sm font-medium transition-colors duration-300",
                            theme === 'dark' ? "text-slate-500" : "text-indigo-950/60"
                        )}>
                            {language === 'zh' ? "欢迎回来，这是您的核心知识库。" : "Welcome back, this is your core knowledge base."}
                        </p>
                    </div>
                </header>

                {/* Toolbar (Sticky) */}
                <div className="sticky top-0 z-40 bg-background/50 backdrop-blur-lg border-y border-card-border -mx-4 px-4 md:-mx-10 md:px-10 py-2.5 mb-8 transition-all duration-300">
                    <div className="flex flex-wrap lg:flex-nowrap items-center gap-3 md:gap-4">
                        {/* Search Bar */}
                        <div className="flex-grow lg:w-[30%] relative group">
                            <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                                <Search className="w-3.5 h-3.5" />
                            </div>
                            <input
                                type="text"
                                placeholder={t("dashboard.searchPlaceholder")}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-card-bg/50 border border-card-border rounded-xl py-1.5 pl-10 pr-4 text-[11px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/40 placeholder:text-slate-500 transition-all backdrop-blur-md text-foreground"
                            />
                        </div>

                        {/* Middle spacer on desktop */}
                        <div className="hidden lg:block flex-1"></div>

                        {/* Controls */}
                        <div className="flex items-center gap-2">
                            {/* New Task Button */}
                            <Link href="/tasks" className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-[10px] transition-all shadow-lg shadow-indigo-500/10 active:scale-95">
                                <Plus className="w-3.5 h-3.5" />
                                <span>{t("dashboard.newTask")}</span>
                            </Link>

                            <div className="flex items-center bg-card-bg/30 border border-card-border p-0.5 rounded-lg backdrop-blur-md shrink-0 gap-0.5">
                                {(viewMode === "text-single" || viewMode === "text-double") && (
                                    <div className="flex items-center bg-background/30 rounded-md p-0.5 border border-card-border/30 mr-0.5">
                                        <button
                                            onClick={() => setDensity("compact")}
                                            className={cn(
                                                "px-1.5 py-0.5 rounded text-[8px] font-black transition-all",
                                                density === "compact" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                            )}
                                        >
                                            1L
                                        </button>
                                        <button
                                            onClick={() => setDensity("detailed")}
                                            className={cn(
                                                "px-1.5 py-0.5 rounded text-[8px] font-black transition-all",
                                                density === "detailed" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                            )}
                                        >
                                            3L
                                        </button>
                                    </div>
                                )}

                                <div className="flex items-center bg-background/30 rounded-md p-0.5 border border-card-border/30">
                                    <button
                                        onClick={() => setViewMode("text-double")}
                                        className={cn(
                                            "p-1.5 rounded-md transition-all",
                                            viewMode === "text-double" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                        )}
                                    >
                                        <Columns2 className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode("text-single")}
                                        className={cn(
                                            "p-1.5 rounded-md transition-all",
                                            viewMode === "text-single" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                        )}
                                    >
                                        <List className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode("thumb")}
                                        className={cn(
                                            "p-1.5 rounded-md transition-all",
                                            viewMode === "thumb" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                        )}
                                    >
                                        <LayoutGrid className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>

                            {/* Page Size Selector */}
                            <div className="flex items-center bg-card-bg/30 border border-card-border p-0.5 rounded-lg shrink-0">
                                {[20, 40, 80].map((val) => (
                                    <button
                                        key={val}
                                        onClick={() => setLimit(val)}
                                        className={cn(
                                            "px-1.5 py-1 rounded text-[8px] font-black transition-all",
                                            limit === val ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                        )}
                                    >
                                        {val}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="relative z-10">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center py-20 animate-pulse">
                            <div className="w-12 h-12 bg-card-bg rounded-full mb-4" />
                            <div className="h-4 w-48 bg-card-bg rounded" />
                        </div>
                    ) : videos.length === 0 ? (
                        <div className="text-center py-20 bg-card-bg border border-dashed border-card-border rounded-[2.5rem] flex flex-col items-center justify-center shadow-xl">
                            <div className="w-16 h-16 bg-background border border-card-border rounded-2xl flex items-center justify-center mb-4 text-slate-500 shadow-xl">
                                <Plus className="w-8 h-8" />
                            </div>
                            <p className="text-foreground font-bold text-lg mb-2">{t("dashboard.emptyTitle")}</p>
                            <p className="text-slate-500 text-sm mb-8 font-medium">{t("dashboard.emptyDesc")}</p>
                            <Link href="/tasks" className="flex items-center justify-center space-x-2 px-8 py-3.5 bg-indigo-600 text-white rounded-2xl font-black text-sm hover:scale-[1.05] transition-all shadow-xl shadow-indigo-500/20 active:scale-95 leading-none">
                                <Plus className="w-5 h-5" />
                                <span>{t("dashboard.addFirstTask")}</span>
                            </Link>
                        </div>
                    ) : viewMode === "thumb" ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                            {videos.filter(v => v.title.toLowerCase().includes(searchQuery.toLowerCase())).map((video) => (
                                <div key={video.id} className="group relative bg-card-bg border border-card-border rounded-3xl overflow-hidden hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                                    <div className="aspect-video relative overflow-hidden">
                                        <img src={video.thumbnail} alt={video.title} className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent dark:block hidden" />

                                        {/* Source Badge */}
                                        <div className="absolute top-4 left-4 p-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 group-hover:border-white/20 transition-colors">
                                            {video.source === "youtube" ? <Youtube className="w-4 h-4 text-red-500" /> : <FileUp className="w-4 h-4 text-blue-400" />}
                                        </div>

                                        {/* Privacy Badge */}
                                        <div className="absolute top-4 right-4 flex items-center space-x-2">
                                            {video.isPublic ? (
                                                <div className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded-full backdrop-blur-md flex items-center space-x-1">
                                                    <Share2 className="w-3 h-3" />
                                                    <span>{t("dashboard.public")}</span>
                                                </div>
                                            ) : (
                                                <div className="px-3 py-1 bg-slate-500/20 border border-white/5 text-slate-400 text-[10px] font-bold rounded-full backdrop-blur-md flex items-center space-x-1">
                                                    <Lock className="w-3 h-3" />
                                                    <span>{t("dashboard.private")}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="p-5">
                                        <h3 className="font-bold text-[18px] leading-tight line-clamp-2 mb-4 h-[48px] group-hover:text-indigo-400 transition-colors text-foreground">{video.title}</h3>
                                        <div className="flex items-center justify-between text-[10px] font-black text-slate-500 uppercase tracking-tight border-t border-card-border/50 pt-3">
                                            <div className="flex items-center gap-3">
                                                <span>{video.date}</span>
                                                <button
                                                    onClick={(e) => handleLike(e, video.id)}
                                                    className={cn(
                                                        "flex items-center gap-1 transition-colors",
                                                        video.is_liked ? "text-rose-500" : "hover:text-rose-400"
                                                    )}
                                                >
                                                    <Heart className={cn("w-3 h-3", video.is_liked && "fill-current")} />
                                                </button>
                                            </div>
                                            <span className="flex items-center space-x-1 group/btn hover:text-indigo-400 transition-colors">
                                                <ArrowRight className="w-3 h-3 group-hover/btn:translate-x-0.5 transition-transform" />
                                                <span>{t("dashboard.viewReport")}</span>
                                            </span>
                                        </div>
                                    </div>

                                    {/* Click Overlay */}
                                    <Link href={`/result/${video.id}`} className="absolute inset-0 z-10" aria-label="View report" />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className={cn(
                            "gap-1.5",
                            viewMode === "text-double" ? "grid grid-cols-1 lg:grid-cols-2" : "flex flex-col space-y-1"
                        )}>
                            {videos.filter(v => v.title.toLowerCase().includes(searchQuery.toLowerCase())).map((video) => (
                                <Link
                                    key={video.id}
                                    href={`/result/${video.id}`}
                                    className={cn(
                                        "flex items-center gap-2 p-2 bg-card-bg border border-card-border rounded-xl transition-all group",
                                        theme === 'dark' ? "hover:border-indigo-500/50 hover:bg-slate-900/60" : "hover:border-indigo-500/40 hover:bg-slate-50"
                                    )}
                                >
                                    {/* Thumbnail for detailed view */}
                                    {density === "detailed" && (
                                        <div className="hidden sm:block w-24 h-14 rounded-lg overflow-hidden shrink-0 border border-card-border/50 relative">
                                            <img src={video.thumbnail} alt="" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                                        </div>
                                    )}

                                    {/* Icon for compact view */}
                                    {density === "compact" && (
                                        <div className="hidden sm:flex w-10 h-10 bg-background border border-card-border rounded-lg items-center justify-center shrink-0 group-hover:text-indigo-400 transition-colors">
                                            {video.source === "youtube" ? <Youtube className="w-4 h-4" /> : <FileUp className="w-4 h-4" />}
                                        </div>
                                    )}

                                    <div className="flex-grow min-w-0 pr-2">
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <h3 className="font-bold text-sm truncate text-foreground group-hover:text-indigo-400 transition-colors leading-tight">{video.title}</h3>
                                            <div className="shrink-0 flex items-center gap-1">
                                                <button
                                                    onClick={(e) => handleLike(e, video.id)}
                                                    className={cn(
                                                        "flex items-center gap-1 transition-colors",
                                                        video.is_liked ? "text-rose-500" : "hover:text-rose-400"
                                                    )}
                                                >
                                                    <Heart className={cn("w-2.5 h-2.5", video.is_liked && "fill-current")} />
                                                </button>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3 text-[9px] font-black text-slate-500 uppercase tracking-widest leading-none">
                                            <span className="flex items-center gap-1">
                                                {video.source === "youtube" ? "Youtube" : "Upload"}
                                            </span>
                                            <span>{video.date}</span>
                                        </div>

                                        {density === "detailed" && video.summary && (
                                            <p className="text-[10px] text-slate-500 line-clamp-1 mt-1 font-medium italic opacity-80">{video.summary}</p>
                                        )}
                                    </div>

                                    <div className="shrink-0 flex items-center gap-3 pr-2">
                                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
