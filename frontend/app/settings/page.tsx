"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Shield, User, Monitor, Eye, Menu } from "lucide-react";
import { supabase } from "@/utils/supabase";
import { Sidebar } from "@/components/Sidebar";

export default function SettingsPage() {
    const [user, setUser] = useState<any>(null);
    const [viewMode, setViewMode] = useState<string>("grid");
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const router = useRouter();

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/");
    };

    useEffect(() => {
        const fetchUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.push("/login");
                return;
            }
            setUser(session.user);
        };
        fetchUser();

        // Load view mode preference
        const savedView = localStorage.getItem("rt-view-mode") || "grid";
        setViewMode(savedView);
    }, [router]);

    const handleSaveViewMode = (mode: string) => {
        setViewMode(mode);
        localStorage.setItem("rt-view-mode", mode);
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 flex font-sans">
            <Sidebar
                user={user}
                onSignOut={handleSignOut}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            <main className="flex-grow min-w-0 bg-slate-950 text-slate-50 font-sans pb-20 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-indigo-900/10 via-slate-950 to-slate-950">
                <div className="max-w-4xl mx-auto px-4 md:px-8 py-8 md:py-12">
                    {/* Mobile Header */}
                    <header className="flex items-center justify-between mb-8 md:hidden">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="p-2 -ml-2 text-slate-400 hover:text-white"
                        >
                            <Menu className="w-6 h-6" />
                        </button>
                        <div className="flex items-center space-x-2">
                            <img src="/icon.png" alt="Logo" className="w-6 h-6" />
                            <span className="font-black tracking-tighter text-lg">Read-Tube</span>
                        </div>
                        <div className="w-10"></div>
                    </header>

                    <header className="mb-12 flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <Link href="/dashboard" className="p-3 bg-slate-900 border border-slate-800 rounded-2xl hover:border-indigo-500/50 transition-all group hidden md:block">
                                <ArrowLeft className="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
                            </Link>
                            <div>
                                <h1 className="text-3xl md:text-4xl font-black tracking-tight">偏好设置</h1>
                                <p className="text-slate-400 font-medium">定制您的阅读与管理体验</p>
                            </div>
                        </div>
                        <button className="px-6 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black text-sm transition-all flex items-center justify-center space-x-2 shadow-xl shadow-indigo-900/20 active:scale-95">
                            <Save className="w-5 h-5" />
                            <span>保存所有更改</span>
                        </button>
                    </header>

                    <div className="space-y-12">
                        {/* Profile Section */}
                        <section>
                            <div className="flex items-center space-x-3 mb-6">
                                <User className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-lg font-bold">基本信息</h2>
                            </div>
                            <div className="bg-slate-900/40 border border-slate-800/50 backdrop-blur-md rounded-3xl p-8 space-y-6">
                                <div className="flex items-center space-x-6">
                                    <img
                                        src={user?.user_metadata?.avatar_url || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop"}
                                        className="w-20 h-20 rounded-2xl border-2 border-white/5 shadow-2xl"
                                        alt="Avatar"
                                    />
                                    <div>
                                        <h3 className="text-xl font-bold">{user?.user_metadata?.full_name || "用户"}</h3>
                                        <p className="text-slate-500 text-sm font-medium">{user?.email}</p>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Interface Preferences */}
                        <section>
                            <div className="flex items-center space-x-3 mb-6">
                                <Monitor className="w-5 h-5 text-blue-400" />
                                <h2 className="text-lg font-bold">界面偏好</h2>
                            </div>
                            <div className="bg-slate-900/40 border border-slate-800/50 backdrop-blur-md rounded-3xl p-8 space-y-8">
                                <div>
                                    <label className="block text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4">默认显示模式</label>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <button
                                            onClick={() => handleSaveViewMode("grid")}
                                            className={`p-6 rounded-2xl border transition-all text-left group ${viewMode === "grid" ? "bg-indigo-500/10 border-indigo-500/50 text-indigo-100 shadow-lg shadow-indigo-500/5" : "bg-slate-950/50 border-slate-800 text-slate-500 hover:border-slate-700"}`}
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="font-black">卡片网格</div>
                                                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${viewMode === "grid" ? "border-indigo-500" : "border-slate-800"}`}>
                                                    {viewMode === "grid" && <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />}
                                                </div>
                                            </div>
                                            <div className="text-xs font-medium opacity-60">瀑布流式平铺，适合快速扫视封面。</div>
                                        </button>
                                        <button
                                            onClick={() => handleSaveViewMode("list")}
                                            className={`p-6 rounded-2xl border transition-all text-left group ${viewMode === "list" ? "bg-indigo-500/10 border-indigo-500/50 text-indigo-100 shadow-lg shadow-indigo-500/5" : "bg-slate-950/50 border-slate-800 text-slate-500 hover:border-slate-700"}`}
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <div className="font-black">精简列表</div>
                                                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${viewMode === "list" ? "border-indigo-500" : "border-slate-800"}`}>
                                                    {viewMode === "list" && <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />}
                                                </div>
                                            </div>
                                            <div className="text-xs font-medium opacity-60">紧凑行显示，适合管理大量历史记录。</div>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Privacy & Safety */}
                        <section>
                            <div className="flex items-center space-x-3 mb-6">
                                <Shield className="w-5 h-5 text-emerald-400" />
                                <h2 className="text-lg font-bold">安全与隐私</h2>
                            </div>
                            <div className="bg-slate-900/40 border border-slate-800/50 backdrop-blur-md rounded-3xl p-8">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h4 className="font-bold">登录保护</h4>
                                        <p className="text-xs text-slate-500 mt-1 font-medium">您当前通过 Google OAuth 账号登录，受 Google 安全保护。</p>
                                    </div>
                                    <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-widest rounded-full border border-emerald-500/20">
                                        安全
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </main>
        </div>
    );
}
