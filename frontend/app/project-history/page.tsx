"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, History, FileText, Tag, Calendar, Menu } from "lucide-react";
import Link from "next/link";
import { Sidebar } from "@/components/Sidebar";
import { supabase } from "@/utils/supabase";
import { useRouter } from "next/navigation";
import { getApiBase } from "@/utils/api";

interface HistoryItem {
    date: string;
    category: string;
    task: string;
    description: string;
    log_file: string;
}

import { useTranslation } from "@/contexts/LanguageContext";

export default function ProjectHistoryPage() {
    const { t, language } = useTranslation();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const router = useRouter();

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/");
    };

    useEffect(() => {
        const fetchUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            setUser(session?.user || null);
        };
        fetchUser();

        const fetchHistoryItems = async () => {
            try {
                const apiBase = getApiBase();
                const res = await fetch(`${apiBase}/project-history`);
                const data = await res.json();
                if (Array.isArray(data)) {
                    setHistory(data);
                } else {
                    console.error("Project history data is not an array:", data);
                    setHistory([]);
                }
            } catch (err) {
                console.error("Failed to fetch project history:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistoryItems();
    }, []);

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
                            <span className="font-black tracking-tighter text-lg">{t("marketing.title")}</span>
                        </div>
                        <div className="w-10"></div>
                    </header>

                    <header className="mb-12 flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <Link href="/dashboard" className="p-3 bg-slate-900 border border-slate-800 rounded-2xl hover:border-indigo-500/50 transition-all group hidden md:block">
                                <ArrowLeft className="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
                            </Link>
                            <div>
                                <h1 className="text-3xl md:text-4xl font-black tracking-tight">{t("history.title")}</h1>
                                <p className="text-slate-400 font-medium whitespace-nowrap overflow-hidden text-ellipsis">{t("history.subtitle")} · .antigravity/PROJECT_HISTORY.md</p>
                            </div>
                        </div>
                    </header>

                    {loading ? (
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-32 bg-slate-900/40 border border-slate-800/50 animate-pulse rounded-3xl" />
                            ))}
                        </div>
                    ) : (
                        <div className="relative space-y-6">
                            {/* Timeline Line */}
                            <div className="absolute left-[26px] top-0 bottom-0 w-px bg-slate-800/50 hidden md:block" />

                            {history.map((item, idx) => (
                                <div key={idx} className="relative md:pl-16 group">
                                    {/* Timeline Dot */}
                                    <div className="absolute left-[22px] top-8 w-2 h-2 rounded-full bg-indigo-500 ring-8 ring-slate-950 hidden md:block group-hover:scale-125 transition-all duration-300" />

                                    <div className="bg-slate-900/40 border border-slate-800/50 backdrop-blur-md rounded-3xl p-6 md:p-8 shadow-xl hover:border-indigo-500/30 transition-all duration-300 group-hover:-translate-y-1">
                                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                                            <div className="flex flex-wrap items-center gap-3">
                                                <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase tracking-widest rounded-full border border-indigo-500/20">
                                                    {item.category}
                                                </span>
                                                <h2 className="text-lg md:text-xl font-bold text-slate-100 group-hover:text-indigo-400 transition-colors">
                                                    {item.task}
                                                </h2>
                                            </div>
                                            <div className="flex items-center gap-4 text-xs font-bold text-slate-500 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <Calendar className="w-4 h-4 text-slate-600" />
                                                    {item.date}
                                                </div>
                                            </div>
                                        </div>

                                        <p className="text-slate-400 leading-relaxed mb-6 font-medium">
                                            {item.description}
                                        </p>

                                        <div className="flex items-center justify-between border-t border-slate-800/50 pt-4 mt-auto">
                                            <div className="flex items-center gap-2 text-[10px] font-mono font-bold text-slate-600 uppercase tracking-tighter">
                                                <FileText className="w-3.5 h-3.5" />
                                                {item.log_file}
                                            </div>
                                            <div className="text-[10px] font-black text-slate-700 uppercase tracking-widest">
                                                # {t("history.recordNum")} {history.length - idx}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )
                    }
                </div>
            </main>
        </div>
    );
}
