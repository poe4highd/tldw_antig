"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Shield, User, Monitor, Eye } from "lucide-react";
import { supabase } from "@/utils/supabase";

export default function SettingsPage() {
    const [user, setUser] = useState<any>(null);
    const [viewMode, setViewMode] = useState<string>("grid");
    const router = useRouter();

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
        <div className="min-h-screen bg-slate-950 text-slate-50 font-sans">
            <nav className="border-b border-slate-900 px-8 py-6 flex items-center justify-between bg-slate-950/50 backdrop-blur-xl sticky top-0 z-10">
                <div className="flex items-center space-x-4">
                    <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-xl transition-all">
                        <ArrowLeft className="w-5 h-5 text-slate-400" />
                    </Link>
                    <h1 className="text-xl font-bold">个人偏好设置</h1>
                </div>
                <button className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-bold text-sm transition-all flex items-center space-x-2">
                    <Save className="w-4 h-4" />
                    <span>保存更改</span>
                </button>
            </nav>

            <main className="max-w-3xl mx-auto py-12 px-6 space-y-12">
                {/* Profile Section */}
                <section>
                    <div className="flex items-center space-x-3 mb-6">
                        <User className="w-5 h-5 text-indigo-400" />
                        <h2 className="text-lg font-bold">基本信息</h2>
                    </div>
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 space-y-6">
                        <div className="flex items-center space-x-6">
                            <img
                                src={user?.user_metadata?.avatar_url || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop"}
                                className="w-20 h-20 rounded-2xl border-2 border-white/5"
                                alt="Avatar"
                            />
                            <div>
                                <h3 className="text-xl font-bold">{user?.user_metadata?.full_name || "用户"}</h3>
                                <p className="text-slate-500 text-sm">{user?.email}</p>
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
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 space-y-8">
                        <div>
                            <label className="block text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">默认显示模式</label>
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={() => handleSaveViewMode("grid")}
                                    className={`p-6 rounded-2xl border transition-all text-left ${viewMode === "grid" ? "bg-indigo-500/10 border-indigo-500 text-indigo-400 shadow-lg shadow-indigo-500/10" : "bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700"}`}
                                >
                                    <div className="font-bold mb-1">卡片网格 (Grid)</div>
                                    <div className="text-xs opacity-60">瀑布流式平铺，适合快速扫视封面。</div>
                                </button>
                                <button
                                    onClick={() => handleSaveViewMode("list")}
                                    className={`p-6 rounded-2xl border transition-all text-left ${viewMode === "list" ? "bg-indigo-500/10 border-indigo-500 text-indigo-400 shadow-lg shadow-indigo-500/10" : "bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700"}`}
                                >
                                    <div className="font-bold mb-1">精简列表 (List)</div>
                                    <div className="text-xs opacity-60">紧凑行显示，适合管理大量历史记录。</div>
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
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="font-bold">登录保护</h4>
                                <p className="text-xs text-slate-500 mt-1">您当前通过 Google OAuth 账号登录，受 Google 安全保护。</p>
                            </div>
                            <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 text-[10px] font-bold rounded-full border border-emerald-500/20">
                                安全
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
