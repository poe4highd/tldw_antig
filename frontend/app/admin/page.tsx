"use client";

import React from "react";
import Link from "next/link";
import {
    BarChart3,
    TrendingUp,
    Users,
    Activity,
    ArrowLeft,
    Calendar,
    Filter,
    ChevronRight,
    MousePointer2,
    Lock,
    Key,
    Loader2,
    Brain,
    Moon,
    Sun
} from "lucide-react";
import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export default function AdminInsightPage() {
    const { t, language } = useTranslation();
    const { theme, toggleTheme } = useTheme();
    // Mock Heatmap Data
    const [heatmapRows, setHeatmapRows] = React.useState<{ id: number; label: string; cells: number[] }[]>([]);
    const [adminKey, setAdminKey] = React.useState<string | null>(null);
    const [isAuthorized, setIsAuthorized] = React.useState<boolean>(false);
    const [verifying, setVerifying] = React.useState(true);
    const [stats, setStats] = React.useState<any>(null);
    const [loadingStats, setLoadingStats] = React.useState(false);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const fetchStats = async (key: string) => {
        setLoadingStats(true);
        try {
            const res = await fetch(`${API_BASE}/admin/stats`, {
                headers: { "X-Admin-Key": key }
            });
            if (res.ok) {
                const data = await res.json();
                setStats(data);

                // Transform Heatmap Data
                if (data.heatmap) {
                    const categories = Array.from(new Set(data.heatmap.map((h: any) => h.category || "未分类")));
                    const rows = categories.map((cat: any, i) => {
                        const cells = Array.from({ length: 24 }, (_, hour) => {
                            const match = data.heatmap.find((h: any) => (h.category || "未分类") === cat && h.hour_of_day === hour);
                            return match ? match.intensity : 0;
                        });
                        // 归一化强度到 0-100 用于显示
                        const maxIntensity = Math.max(...cells, 1);
                        return {
                            id: i,
                            label: cat.length > 10 ? cat.substring(0, 8) + '...' : cat,
                            cells: cells.map(c => (c / maxIntensity) * 100)
                        };
                    });
                    setHeatmapRows(rows);
                }
            }
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
        setLoadingStats(false);
    };

    React.useEffect(() => {
        const storedKey = localStorage.getItem("tldw_admin_key");
        if (storedKey) {
            setAdminKey(storedKey);
            verifyKey(storedKey);
        } else {
            setVerifying(false);
        }
    }, []);

    const verifyKey = async (key: string) => {
        setVerifying(true);
        try {
            // 通过调用 visibility 接口来验证密钥是否正确
            const res = await fetch(`${API_BASE}/admin/visibility`, {
                headers: { "X-Admin-Key": key }
            });
            if (res.ok) {
                setIsAuthorized(true);
                localStorage.setItem("tldw_admin_key", key);
                fetchStats(key);
            } else {
                setIsAuthorized(false);
            }
        } catch (err) {
            console.error("Auth failed:", err);
            setIsAuthorized(false);
        }
        setVerifying(false);
    };

    const handleSaveKey = (newKey: string) => {
        setAdminKey(newKey);
        verifyKey(newKey);
    };

    if (verifying) {
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
                    <div className="w-16 h-16 bg-indigo-500/10 text-indigo-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-black mb-2">{t("admin.subtitle")}</h2>
                    <p className="text-slate-500 mb-8 text-[10px] font-black uppercase tracking-widest">{t("admin.secretNote")}</p>

                    <div className="space-y-4 text-left">
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

                    <Link href="/dashboard" className="inline-block mt-8 text-[10px] font-black text-slate-500 hover:text-indigo-400 uppercase tracking-widest transition-colors">
                        {t("common.back")}
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-transparent text-foreground p-4 md:p-8 font-sans selection:bg-indigo-500/30">
            {/* Background Glows (consistent with homepage) */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
                <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
            </div>

            {/* Header */}
            <header className="sticky top-0 z-[60] bg-background/80 backdrop-blur-xl border-b border-card-border -mx-4 px-4 md:-mx-8 md:px-8 h-14 md:h-16 flex items-center justify-between gap-4 mb-6 md:mb-8 transition-all duration-300">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-2 bg-card-bg/50 border border-card-border rounded-xl text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all group" title={t("common.back")}>
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    </Link>
                    <div>
                        <h1 className="text-lg md:text-xl font-black tracking-tighter leading-none">{t("admin.title")}</h1>
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 hidden sm:block">Internal Cockpit</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <LanguageSwitcher />
                    <button
                        onClick={toggleTheme}
                        className="p-2 bg-card-bg/50 border border-card-border rounded-xl text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all shadow-sm"
                        title={theme === 'dark' ? "Light Mode" : "Dark Mode"}
                    >
                        {theme === 'dark' ? <Sun className="w-4 h-4 md:w-5 md:h-5" /> : <Moon className="w-4 h-4 md:w-5 md:h-5" />}
                    </button>

                    <div className="h-6 w-px bg-card-border mx-1 hidden sm:block" />

                    <button
                        onClick={() => adminKey && fetchStats(adminKey)}
                        disabled={loadingStats}
                        className="px-3 py-1.5 bg-card-bg border border-card-border rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors disabled:opacity-50"
                    >
                        {loadingStats ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Activity className="w-3.5 h-3.5 text-indigo-400" />}
                        <span className="hidden md:inline">{t("admin.refresh")}</span>
                    </button>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4 mb-8">
                {[
                    { label: t("admin.totalVideos"), value: stats?.stats?.video_count || "0", trend: "+12.5%", icon: Activity, color: "text-blue-400" },
                    { label: t("admin.activeUsers"), value: stats?.stats?.dau || "0", trend: "+3.2%", icon: Users, color: "text-indigo-400" },
                    { label: t("admin.totalInteractions"), value: stats?.stats?.total_clicks || "0", trend: "+24.8%", icon: MousePointer2, color: "text-emerald-400" },
                    { label: t("admin.llmTotalCost"), value: stats?.stats?.total_llm_cost || "$0.00", trend: "+8.4%", icon: Brain, color: "text-rose-400" },
                    { label: t("admin.retention"), value: stats?.stats?.retention || "84%", trend: "+5.1%", icon: TrendingUp, color: "text-amber-400" },
                ].map((stat, i) => (
                    <div key={i} className="bg-card-bg border border-card-border rounded-2xl p-4 hover:border-indigo-500/30 transition-all group relative overflow-hidden backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-3">
                            <div className={`p-2 rounded-xl bg-background border border-card-border ${stat.color} group-hover:scale-110 transition-transform`}>
                                <stat.icon className="w-4 h-4" />
                            </div>
                            <span className="text-[8px] font-black text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded-md">{stat.trend}</span>
                        </div>
                        <p className="text-slate-500 text-[9px] font-black uppercase tracking-widest mb-0.5">{stat.label}</p>
                        <h3 className="text-xl font-black">{stat.value}</h3>
                    </div>
                ))}
            </div>

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Heatmap Section */}
                <div className="lg:col-span-2 bg-card-bg border border-card-border rounded-3xl p-6 overflow-hidden relative backdrop-blur-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-black uppercase tracking-tight">{t("admin.heatmapTitle")}</h3>
                        <div className="flex items-center space-x-1.5">
                            {[0.1, 0.4, 0.7, 1].map((op, idx) => (
                                <div key={idx} className="w-2.5 h-2.5 rounded-[2px]" style={{ backgroundColor: `rgba(99, 102, 241, ${op})` }}></div>
                            ))}
                            <span className="text-[9px] text-slate-500 font-black ml-1 uppercase tracking-tighter">{t("admin.heatmapLegend")}</span>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {heatmapRows.map(row => (
                            <div key={row.id} className="flex items-center space-x-3">
                                <span className="w-16 text-[9px] font-black text-slate-500 truncate uppercase tracking-tighter">{row.label}</span>
                                <div className="flex-grow grid grid-cols-24 h-4 gap-0.5">
                                    {row.cells.map((cell, idx) => (
                                        <div
                                            key={idx}
                                            className="rounded-[1px] transition-all hover:scale-110 cursor-help"
                                            style={{
                                                backgroundColor: `rgba(99, 102, 241, ${cell / 100})`,
                                                opacity: cell < 10 ? 0.05 : 1
                                            }}
                                            title={`${Math.round(cell)}%`}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-between items-center mt-4 pl-20 pr-1">
                        {["00:00", "06:00", "12:00", "18:00", "24:00"].map((time, i) => (
                            <span key={i} className="text-[8px] font-black text-slate-600 tracking-tighter">{time}</span>
                        ))}
                    </div>
                </div>

                {/* Sidebar Mini List */}
                <div className="bg-card-bg border border-card-border rounded-3xl p-6 backdrop-blur-sm">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-base font-black uppercase tracking-tight">{t("admin.topVideos")}</h3>
                        <BarChart3 className="w-4 h-4 text-indigo-400" />
                    </div>

                    <div className="space-y-4">
                        {(stats?.top_videos || []).map((video: any, i: number) => (
                            <Link
                                key={video.id}
                                href={`/result/${video.id}`}
                                className="flex items-center space-x-3 group cursor-pointer"
                            >
                                <div className="w-7 h-7 rounded-lg bg-background border border-card-border flex items-center justify-center text-[10px] font-black text-slate-500 group-hover:text-indigo-400 group-hover:border-indigo-500/30 transition-all">
                                    #{i + 1}
                                </div>
                                <div className="flex-grow overflow-hidden">
                                    <p className="text-xs font-bold truncate group-hover:text-indigo-400 transition-colors uppercase tracking-tight">{video.title}</p>
                                    <p className="text-[9px] text-slate-500 font-black tracking-widest">{(video.interaction_count || 0).toLocaleString()} {t("admin.interactions")}</p>
                                </div>
                                <ChevronRight className="w-3.5 h-3.5 text-slate-700 group-hover:text-indigo-400 transition-all" />
                            </Link>
                        ))}
                        {(!stats?.top_videos || stats.top_videos.length === 0) && (
                            <div className="text-center py-6 text-slate-600 text-[10px] font-black uppercase tracking-widest">
                                {t("admin.noTopData")}
                            </div>
                        )}
                    </div>

                    <Link href="/admin/visibility" className="block w-full mt-6 py-3 border border-dashed border-card-border hover:border-indigo-500/50 hover:bg-indigo-500/5 rounded-xl transition-all text-[10px] font-black text-slate-500 hover:text-indigo-400 text-center uppercase tracking-widest">
                        {t("admin.manageContent")}
                    </Link>
                </div>
            </div>

            {/* LLM Usage Tracking Table */}
            <div className="bg-card-bg border border-card-border rounded-3xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            <Brain className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-base font-black uppercase tracking-tight">{t("admin.llmTracking")}</h3>
                            <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest">{t("admin.llmTrackingDesc")}</p>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-[9px] font-black text-slate-500 uppercase tracking-widest">
                                <th className="px-4 py-2">{t("admin.thTitle")}</th>
                                <th className="px-4 py-2 text-center">{t("admin.thModel")}</th>
                                <th className="px-4 py-2 text-center">{t("admin.thPrompt")}</th>
                                <th className="px-4 py-2 text-center">{t("admin.thCompletion")}</th>
                                <th className="px-4 py-2 text-right">{t("admin.thCost")}</th>
                                <th className="px-4 py-2 text-right">{t("admin.thDate")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(stats?.llm_usage_history || []).map((record: any) => (
                                <tr key={record.id} className="group hover:bg-slate-500/5 transition-colors">
                                    <td className="px-4 py-3 bg-background/50 rounded-l-xl border-y border-l border-card-border group-hover:border-indigo-500/30 transition-all">
                                        <p className="text-xs font-bold truncate max-w-sm">{record.title}</p>
                                    </td>
                                    <td className="px-4 py-3 bg-background/50 border-y border-card-border group-hover:border-indigo-500/30 text-center transition-all">
                                        <div className="flex flex-col items-center gap-0.5">
                                            <span className="px-1.5 py-0.5 bg-indigo-500/10 text-indigo-400 rounded text-[9px] font-black uppercase tracking-wider border border-indigo-500/10">
                                                {record.model.replace(" (est.)", "")}
                                            </span>
                                            {record.is_estimated && (
                                                <span className="text-[7px] font-black text-amber-500/70 uppercase tracking-tighter">
                                                    {t("admin.estLabel")}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 bg-background/50 border-y border-card-border group-hover:border-indigo-500/30 text-center text-[10px] font-bold text-slate-500 transition-all">
                                        {record.prompt_tokens.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 bg-background/50 border-y border-card-border group-hover:border-indigo-500/30 text-center text-[10px] font-bold text-slate-500 transition-all">
                                        {record.completion_tokens.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 bg-background/50 border-y border-card-border group-hover:border-indigo-500/30 text-right text-[10px] font-black text-rose-400 transition-all">
                                        ${record.cost.toFixed(4)}
                                    </td>
                                    <td className="px-4 py-3 bg-background/50 rounded-r-xl border-y border-r border-card-border group-hover:border-indigo-500/30 text-right text-[9px] font-black text-slate-600 transition-all">
                                        {new Date(record.created_at).toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US')}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {(!stats?.llm_usage_history || stats.llm_usage_history.length === 0) && (
                        <div className="text-center py-12 bg-background/30 rounded-2xl border border-card-border border-dashed mt-2">
                            <p className="text-slate-600 text-[10px] font-black uppercase tracking-widest">{t("admin.noLlmData")}</p>
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}
