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
    Menu
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { supabase } from "@/utils/supabase";
import { getApiBase } from "@/utils/api";
import { Sidebar } from "@/components/Sidebar";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Mock Data
// ... (omitted if possible, but replace_file_content needs contiguous block)
// I'll replace from the imports down to the return statement start.

// Mock Data
const MOCK_VIDEOS = [
    {
        id: "_1C1mRhUYwo",
        title: "Stop learning investment if you are an ordinary person? The most ridiculous advice.",
        thumbnail: "https://i.ytimg.com/vi/_1C1mRhUYwo/sddefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 1250,
        date: "2024-01-16"
    },
    {
        id: "0wwqxQchN64",
        title: "Empress Xuan in 'Love Like the Galaxy' - Why is she so tragic? #LoveLikeTheGalaxy",
        thumbnail: "https://i.ytimg.com/vi_webp/0wwqxQchN64/maxresdefault.webp",
        source: "youtube",
        isPublic: true,
        views: 450,
        date: "2024-01-15"
    },
    {
        id: "MnjNgtPr3v0",
        title: "2026 Tesla Model Y Performance - Actually still the best?",
        thumbnail: "https://i.ytimg.com/vi/MnjNgtPr3v0/maxresdefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 890,
        date: "2024-01-14"
    },
    {
        id: "yDc0_8emz7M",
        title: "Agent Skills: From Usage to Theory, Explained.",
        thumbnail: "https://i.ytimg.com/vi/yDc0_8emz7M/maxresdefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 3100,
        date: "2024-01-13"
    },
    {
        id: "ZzPoWrlzE1w",
        title: "Claude Skills: The Automated Superpower Underrated by 90% | 3-Week Review",
        thumbnail: "https://i.ytimg.com/vi/ZzPoWrlzE1w/maxresdefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 2400,
        date: "2024-01-12"
    },
    {
        id: "upload-mock-1",
        title: "Internal Meeting: 2024 Q4 Product Roadmap Discussion.mp3",
        thumbnail: "https://images.unsplash.com/photo-1589903303904-a0422599fa86?auto=format&fit=crop&q=80&w=800",
        source: "upload",
        isPublic: false,
        views: 0,
        date: "2024-01-11"
    }
];

import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";

export default function DashboardPage() {
    const { t, language } = useTranslation();
    const { theme } = useTheme();
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
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
        const savedViewMode = localStorage.getItem("rt-view-mode");
        if (savedViewMode === "grid" || savedViewMode === "list") {
            setViewMode(savedViewMode);
        }
    }, []);

    // 2. Save preference to localStorage when changed
    useEffect(() => {
        localStorage.setItem("rt-view-mode", viewMode);
    }, [viewMode]);

    useEffect(() => {
        const fetchUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.push("/login");
                return;
            }
            setUser(session.user);
            fetchHistory();
        };

        const fetchHistory = async () => {
            setIsLoading(true);
            try {
                // Determine API Base
                const apiBase = getApiBase();

                const { data: { session } } = await supabase.auth.getSession();
                const user_id = session?.user?.id;
                const response = await fetch(`${apiBase}/history${user_id ? `?user_id=${user_id}` : ''}`);
                const data = await response.json();

                if (data.history) {
                    // Map backend data to frontend structure
                    const formattedVideos = data.history.map((item: any) => ({
                        id: item.id,
                        title: item.title,
                        thumbnail: item.thumbnail,
                        source: item.id.length === 11 ? "youtube" : "upload",
                        isPublic: true, // For now, assume public until privacy logic is in
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
                setIsLoading(false);
            }
        };

        fetchUser();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!session) {
                router.push("/login");
            } else {
                setUser(session.user);
                fetchHistory();
            }
        });

        return () => subscription.unsubscribe();
    }, [router, language]);

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/");
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
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12 relative z-10">
                    <div>
                        <h1 className={cn(
                            "text-3xl md:text-4xl font-black tracking-tight mb-2",
                            theme === 'dark' ? "bg-gradient-to-r from-foreground to-slate-400 bg-clip-text text-transparent" : "text-indigo-900"
                        )}>
                            {t("nav.bookshelf")}
                        </h1>
                        <p className="text-slate-500 text-sm font-medium">{t("dashboard.subtitle")}</p>
                    </div>
                    <Link href="/tasks" className="flex items-center justify-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold text-sm transition-all shadow-xl shadow-indigo-500/20 active:scale-95">
                        <Plus className="w-5 h-5" />
                        <span>{t("dashboard.newTask")}</span>
                    </Link>
                </header>

                {/* Filters & View Toggle (Sticky) */}
                <div className="sticky top-0 z-40 bg-background/50 backdrop-blur-lg border-y border-card-border -mx-4 px-4 md:-mx-10 md:px-10 py-3 mb-8 transition-all duration-300">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="relative w-full md:max-w-md group">
                            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                                <Search className="w-4 h-4" />
                            </div>
                            <input
                                type="text"
                                placeholder={t("dashboard.searchPlaceholder")}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-card-bg/30 border border-card-border rounded-xl py-2 pl-12 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/40 placeholder:text-slate-500 transition-all backdrop-blur-md text-foreground"
                            />
                        </div>

                        <div className="flex items-center gap-2">
                            <div className="flex items-center bg-card-bg/30 border border-card-border p-0.5 rounded-lg backdrop-blur-md">
                                <button
                                    onClick={() => setViewMode("grid")}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        viewMode === "grid" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                    )}
                                >
                                    <LayoutGrid className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setViewMode("list")}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        viewMode === "list" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                                    )}
                                >
                                    <List className="w-4 h-4" />
                                </button>
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
                    ) : viewMode === "grid" ? (
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

                                    <div className="p-6">
                                        <h3 className="font-bold text-sm line-clamp-2 mb-4 h-10 group-hover:text-indigo-400 transition-colors text-foreground">{video.title}</h3>
                                        <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                                            <span>{video.date}</span>
                                            <span className="flex items-center space-x-1">
                                                <ArrowRight className="w-3 h-3" />
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
                        <div className="space-y-4">
                            {videos.filter(v => v.title.toLowerCase().includes(searchQuery.toLowerCase())).map((video) => (
                                <Link
                                    key={video.id}
                                    href={`/result/${video.id}`}
                                    className="flex items-center justify-between p-5 bg-card-bg border border-card-border rounded-2xl hover:border-indigo-500/50 hover:bg-slate-100 dark:hover:bg-slate-900/60 transition-all group"
                                >
                                    <div className="flex items-center space-x-6 overflow-hidden">
                                        <span className="p-2 bg-background border border-card-border rounded-lg group-hover:text-indigo-400 transition-colors">
                                            {video.source === "youtube" ? <Youtube className="w-4 h-4" /> : <FileUp className="w-4 h-4" />}
                                        </span>
                                        <span className="font-bold text-sm truncate text-foreground">{video.title}</span>
                                    </div>
                                    <div className="flex items-center space-x-8 flex-shrink-0 ml-4">
                                        <div className="hidden sm:flex items-center space-x-4">
                                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{video.date}</span>
                                            {video.isPublic ? <Share2 className="w-4 h-4 text-emerald-500/50" /> : <Lock className="w-4 h-4 text-slate-600" />}
                                        </div>
                                        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
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
