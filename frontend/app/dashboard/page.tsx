"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
    LayoutGrid,
    List,
    Plus,
    Search,
    Settings,
    LogOut,
    Youtube,
    FileUp,
    Share2,
    Lock,
    ArrowRight
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Mock Data
const MOCK_VIDEOS = [
    {
        id: "_1C1mRhUYwo",
        title: "“普通人别学投资”，是我听过最荒谬的蠢话",
        thumbnail: "https://i.ytimg.com/vi/_1C1mRhUYwo/sddefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 1250,
        date: "2024-01-16"
    },
    {
        id: "0wwqxQchN64",
        title: "《星汉灿烂》宣皇后为什么这么让人意难平？#星汉灿烂 #赵露思 #吴磊",
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
        title: "Agent Skill 从使用到原理，一次讲清",
        thumbnail: "https://i.ytimg.com/vi/yDc0_8emz7M/maxresdefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 3100,
        date: "2024-01-13"
    },
    {
        id: "ZzPoWrlzE1w",
        title: "Claude Skills：被 90% 的人低估的自动化超能力 | 三周深度实测",
        thumbnail: "https://i.ytimg.com/vi/ZzPoWrlzE1w/maxresdefault.jpg",
        source: "youtube",
        isPublic: true,
        views: 2400,
        date: "2024-01-12"
    },
    {
        id: "upload-mock-1",
        title: "内部会议录音：2024 Q4 产品路线图讨论.mp3",
        thumbnail: "https://images.unsplash.com/photo-1589903303904-a0422599fa86?auto=format&fit=crop&q=80&w=800",
        source: "upload",
        isPublic: false,
        views: 0,
        date: "2024-01-11"
    }
];

export default function DashboardPage() {
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [searchQuery, setSearchQuery] = useState("");

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 flex font-sans">
            {/* Sidebar */}
            <aside className="w-64 flex-shrink-0 border-r border-slate-900 bg-slate-950 flex flex-col z-20 sticky top-0 h-screen overflow-y-auto">
                <div className="p-8">
                    <Link href="/" className="flex items-center space-x-3 group mb-12">
                        <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-all duration-300">
                            <img src="/icon.png" alt="Read-Tube Logo" className="w-6 h-6" />
                        </div>
                        <span className="text-xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                            Read-Tube
                        </span>
                    </Link>

                    <nav className="space-y-6">
                        <div>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 px-4">主菜单</p>
                            <div className="space-y-1">
                                <button className="w-full flex items-center space-x-3 px-4 py-3 bg-indigo-500/10 text-indigo-400 rounded-xl font-bold text-sm">
                                    <LayoutGrid className="w-5 h-5" />
                                    <span>仪表盘</span>
                                </button>
                                <button className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-slate-900 text-slate-400 hover:text-white rounded-xl font-medium text-sm transition-all">
                                    <Youtube className="w-5 h-5" />
                                    <span>YouTube 发现</span>
                                </button>
                                <Link href="/dev-home" className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-slate-900 text-slate-400 hover:text-white rounded-xl font-medium text-sm transition-all">
                                    <FileUp className="w-5 h-5" />
                                    <span>处理机入口</span>
                                </Link>
                            </div>
                        </div>

                        <div>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 px-4">个人中心</p>
                            <div className="space-y-1">
                                <button className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-slate-900 text-slate-400 hover:text-white rounded-xl font-medium text-sm transition-all">
                                    <Settings className="w-5 h-5" />
                                    <span>偏好设置</span>
                                </button>
                            </div>
                        </div>
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-900">
                    <div className="flex items-center space-x-3 mb-6 px-2">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center font-bold border-2 border-white/10 shadow-lg shadow-indigo-500/20">
                            G
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-sm font-bold truncate">Guest User</p>
                            <p className="text-[10px] text-slate-500 truncate">演示模式</p>
                        </div>
                    </div>
                    <Link href="/" className="w-full flex items-center justify-center space-x-2 py-3 border border-slate-800 hover:border-red-500/50 hover:bg-red-500/5 text-slate-400 hover:text-red-400 rounded-xl text-xs font-bold transition-all">
                        <LogOut className="w-4 h-4" />
                        <span>退出登录</span>
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-grow min-w-0 p-10 bg-slate-950 relative">
                {/* Header Section */}
                <header className="flex items-center justify-between mb-12">
                    <div>
                        <h1 className="text-4xl font-black tracking-tight mb-2">仪表盘</h1>
                        <p className="text-slate-500 text-sm font-medium">欢迎回来，这是您最近的知识处理记录。</p>
                    </div>
                    <button className="flex items-center space-x-2 px-6 py-3 bg-white text-slate-950 rounded-2xl font-bold text-sm hover:scale-[1.05] transition-all shadow-xl shadow-white/5 active:scale-95">
                        <Plus className="w-5 h-5" />
                        <span>新建处理任务</span>
                    </button>
                </header>

                {/* Filters & View Toggle */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
                    <div className="relative w-full md:max-w-md group">
                        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                            <Search className="w-4 h-4" />
                        </div>
                        <input
                            type="text"
                            placeholder="搜索标题、类型或来源..."
                            className="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-600 transition-all"
                        />
                    </div>

                    <div className="flex items-center bg-slate-900/50 border border-slate-800 p-1 rounded-xl">
                        <button
                            onClick={() => setViewMode("grid")}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                viewMode === "grid" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setViewMode("list")}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                viewMode === "list" ? "bg-slate-800 text-white shadow-sm" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <List className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Content Area */}
                {viewMode === "grid" ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                        {MOCK_VIDEOS.map((video) => (
                            <div key={video.id} className="group relative bg-slate-900/30 border border-slate-800/50 rounded-3xl overflow-hidden hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                                <div className="aspect-video relative overflow-hidden">
                                    <img src={video.thumbnail} alt={video.title} className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700" />
                                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />

                                    {/* Source Badge */}
                                    <div className="absolute top-4 left-4 p-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 group-hover:border-white/20 transition-colors">
                                        {video.source === "youtube" ? <Youtube className="w-4 h-4 text-red-500" /> : <FileUp className="w-4 h-4 text-blue-400" />}
                                    </div>

                                    {/* Privacy Badge */}
                                    <div className="absolute top-4 right-4 flex items-center space-x-2">
                                        {video.isPublic ? (
                                            <div className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded-full backdrop-blur-md flex items-center space-x-1">
                                                <Share2 className="w-3 h-3" />
                                                <span>公开</span>
                                            </div>
                                        ) : (
                                            <div className="px-3 py-1 bg-slate-500/20 border border-white/5 text-slate-400 text-[10px] font-bold rounded-full backdrop-blur-md flex items-center space-x-1">
                                                <Lock className="w-3 h-3" />
                                                <span>私有</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="p-6">
                                    <h3 className="font-bold text-sm line-clamp-2 mb-4 h-10 group-hover:text-indigo-400 transition-colors">{video.title}</h3>
                                    <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                                        <span>{video.date}</span>
                                        <span className="flex items-center space-x-1">
                                            <ArrowRight className="w-3 h-3" />
                                            <span>查看报告</span>
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
                        {MOCK_VIDEOS.map((video) => (
                            <Link
                                key={video.id}
                                href={`/result/${video.id}`}
                                className="flex items-center justify-between p-5 bg-slate-900/40 border border-slate-800 rounded-2xl hover:border-indigo-500/50 hover:bg-slate-900/60 transition-all group"
                            >
                                <div className="flex items-center space-x-6 overflow-hidden">
                                    <span className="p-2 bg-slate-950 border border-slate-800 rounded-lg group-hover:text-indigo-400 transition-colors">
                                        {video.source === "youtube" ? <Youtube className="w-4 h-4" /> : <FileUp className="w-4 h-4" />}
                                    </span>
                                    <span className="font-bold text-sm truncate">{video.title}</span>
                                </div>
                                <div className="flex items-center space-x-8 flex-shrink-0 ml-4">
                                    <div className="hidden sm:flex items-center space-x-4">
                                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{video.date}</span>
                                        {video.isPublic ? <Share2 className="w-4 h-4 text-emerald-500/50" /> : <Lock className="w-4 h-4 text-slate-600" />}
                                    </div>
                                    <ArrowRight className="w-4 h-4 text-slate-700 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
