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
    Loader2
} from "lucide-react";

export default function AdminInsightPage() {
    // Mock Heatmap Data
    const [heatmapRows, setHeatmapRows] = React.useState<{ id: number; label: string; cells: number[] }[]>([]);
    const [adminKey, setAdminKey] = React.useState<string | null>(null);
    const [isAuthorized, setIsAuthorized] = React.useState<boolean>(false);
    const [verifying, setVerifying] = React.useState(true);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    React.useEffect(() => {
        const storedKey = localStorage.getItem("tldw_admin_key");
        if (storedKey) {
            setAdminKey(storedKey);
            verifyKey(storedKey);
        } else {
            setVerifying(false);
        }

        const rows = Array.from({ length: 8 }, (_, i) => ({
            id: i,
            label: `视频领域 ${i + 1}`,
            cells: Array.from({ length: 24 }, () => Math.random() * 100)
        }));
        setHeatmapRows(rows);
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
            <main className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            </main>
        );
    }

    if (!isAuthorized) {
        return (
            <main className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center p-6">
                <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl w-full max-w-sm text-center shadow-2xl">
                    <div className="w-16 h-16 bg-indigo-500/10 text-indigo-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Lock className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-black mb-2">需要管理员权限</h2>
                    <p className="text-slate-400 mb-8 text-xs font-medium uppercase tracking-widest">请输入身份验证密钥</p>

                    <div className="space-y-4 text-left">
                        <div className="relative">
                            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                            <input
                                type="password"
                                placeholder="Admin Secret..."
                                className="w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono"
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
                            进入驾驶舱
                        </button>
                    </div>

                    <Link href="/dashboard" className="inline-block mt-8 text-xs font-bold text-slate-600 hover:text-indigo-400 uppercase tracking-widest transition-colors">
                        返回书架
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-slate-950 text-slate-50 p-10 font-sans">
            {/* ... rest of the component ... */}
            {/* Header */}
            <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12">
                <div>
                    <Link href="/dashboard" className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 text-xs font-bold uppercase tracking-widest mb-4 group transition-colors">
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        <span>返回书架</span>
                    </Link>
                    <h1 className="text-4xl font-black tracking-tight mb-2">管理数据驾驶舱</h1>
                    <p className="text-slate-500 text-sm font-medium">全站运营热度与用户行为深度透视 (Mock Presentation)</p>
                </div>

                <div className="flex items-center space-x-3">
                    <button className="px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs font-bold flex items-center space-x-2 hover:bg-slate-800 transition-colors">
                        <Calendar className="w-4 h-4 text-slate-500" />
                        <span>过去 30 天</span>
                    </button>
                    <button className="px-4 py-2 bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center space-x-2 hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/20">
                        <Filter className="w-4 h-4" />
                        <span>自定义筛选</span>
                    </button>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                {[
                    { label: "累计处理视频", value: "2,481", trend: "+12.5%", icon: Activity, color: "text-blue-400" },
                    { label: "活跃用户 (DAU)", value: "156", trend: "+3.2%", icon: Users, color: "text-indigo-400" },
                    { label: "字幕总点击量", value: "48.2k", trend: "+24.8%", icon: MousePointer2, color: "text-emerald-400" },
                    { label: "平均阅读留存", value: "84%", trend: "+5.1%", icon: TrendingUp, color: "text-amber-400" },
                ].map((stat, i) => (
                    <div key={i} className="bg-slate-900/30 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/30 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className={`p-3 rounded-2xl bg-slate-950 border border-slate-800 ${stat.color} group-hover:scale-110 transition-transform`}>
                                <stat.icon className="w-5 h-5" />
                            </div>
                            <span className="text-[10px] font-black text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-lg">{stat.trend}</span>
                        </div>
                        <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1">{stat.label}</p>
                        <h3 className="text-2xl font-black">{stat.value}</h3>
                    </div>
                ))}
            </div>

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Heatmap Section */}
                <div className="lg:col-span-2 bg-slate-900/30 border border-slate-800 rounded-[2.5rem] p-8 overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-xl font-bold">全站字幕互动关注度 (Heatmap)</h3>
                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 rounded bg-slate-800"></div>
                            <div className="w-3 h-3 rounded bg-indigo-900"></div>
                            <div className="w-3 h-3 rounded bg-indigo-500"></div>
                            <div className="w-3 h-3 rounded bg-indigo-300"></div>
                            <span className="text-[10px] text-slate-500 font-bold ml-2">热度增长 {'->'}</span>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {heatmapRows.map(row => (
                            <div key={row.id} className="flex items-center space-x-4">
                                <span className="w-20 text-[10px] font-bold text-slate-500 truncate">{row.label}</span>
                                <div className="flex-grow grid grid-cols-24 h-6 gap-1">
                                    {row.cells.map((cell, idx) => (
                                        <div
                                            key={idx}
                                            className="rounded-sm transition-all hover:scale-125 cursor-help"
                                            style={{
                                                backgroundColor: `rgba(99, 102, 241, ${cell / 100})`, // Indigo color with variable opacity
                                                opacity: cell < 20 ? 0.1 : 1
                                            }}
                                            title={`点击强度: ${Math.round(cell)}%`}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-between items-center mt-6 pl-24 pr-4">
                        {["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"].map((time, i) => (
                            <span key={i} className="text-[10px] font-bold text-slate-600">{time}</span>
                        ))}
                    </div>
                </div>

                {/* Sidebar Mini List */}
                <div className="bg-slate-900/30 border border-slate-800 rounded-[2.5rem] p-8">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-xl font-bold">爆款视频 Top 5</h3>
                        <BarChart3 className="w-5 h-5 text-indigo-400" />
                    </div>

                    <div className="space-y-6">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex items-center space-x-4 group cursor-pointer">
                                <div className="w-8 h-8 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center text-xs font-bold text-slate-400 group-hover:text-indigo-400 group-hover:border-indigo-500/30 transition-all">
                                    #{i}
                                </div>
                                <div className="flex-grow overflow-hidden">
                                    <p className="text-sm font-bold truncate group-hover:text-indigo-400 transition-colors">爆款视频标题案例 {i} 展示</p>
                                    <p className="text-[10px] text-slate-500 font-bold tracking-widest">{10 * (6 - i)}k 次互动</p>
                                </div>
                                <ChevronRight className="w-4 h-4 text-slate-700 group-hover:text-indigo-400 transition-all" />
                            </div>
                        ))}
                    </div>

                    <button className="w-full mt-10 py-4 border border-dashed border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 rounded-2xl transition-all text-xs font-bold text-slate-500 hover:text-indigo-400">
                        查看完整榜单
                    </button>
                </div>
            </div>
        </main>
    );
}
