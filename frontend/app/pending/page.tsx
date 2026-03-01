"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
    Clock,
    RefreshCcw,
    CheckCircle2,
    AlertCircle,
    ChevronLeft,
    Youtube,
    Search,
    Loader2,
    Sun,
    Moon
} from "lucide-react";
import { getApiBase } from "@/utils/api";
import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { twMerge } from "tailwind-merge";
import { clsx, type ClassValue } from "clsx";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface PendingItem {
    id: string;
    title: string;
    status: "queued" | "processing" | "completed" | "failed";
    progress: number;
    mtime: any;
    thumbnail?: string;
    duration?: number;
}

export default function PendingPage() {
    const { t } = useTranslation();
    const { theme, toggleTheme } = useTheme();
    const [tasks, setTasks] = useState<PendingItem[]>([]);
    const [recentRecords, setRecentRecords] = useState<PendingItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchTasks = async () => {
        try {
            const apiBase = getApiBase();
            const response = await fetch(`${apiBase}/history`);
            const data = await response.json();

            setTasks(data.active_tasks || []);
            setRecentRecords(data.recent_tasks || []);
        } catch (error) {
            console.error("Failed to fetch pending tasks:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
        const timer = setInterval(fetchTasks, 5000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-indigo-500/30">
            <main className="max-w-4xl mx-auto p-6 md:p-12">
                <div className="flex items-center justify-between mb-12">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 bg-card-bg border border-card-border rounded-xl text-slate-400 hover:text-foreground transition-all shadow-lg"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-black tracking-tight mb-1">
                                {t("pending.title")} <span className="text-indigo-500">{t("pending.queueLabel")}</span>
                            </h1>
                            <p className="text-slate-500 dark:text-slate-500 light:text-slate-600 text-sm font-medium">
                                {t("pending.subtitle")}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <LanguageSwitcher />
                        <button
                            onClick={toggleTheme}
                            className="p-3 bg-card-bg border border-card-border rounded-xl text-slate-400 hover:text-foreground transition-all shadow-lg"
                            title={theme === 'dark' ? "Light Mode" : "Dark Mode"}
                        >
                            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <button
                            onClick={fetchTasks}
                            className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 hover:bg-indigo-500/20 transition-all shadow-lg"
                        >
                            <RefreshCcw className={cn("w-5 h-5", isLoading && "animate-spin")} />
                        </button>
                    </div>
                </div>

                {tasks.length === 0 && !isLoading ? (
                    <div className="py-20 text-center bg-card-bg/20 border border-dashed border-card-border rounded-[2rem] flex flex-col items-center">
                        <div className="w-16 h-16 bg-card-bg border border-card-border rounded-2xl flex items-center justify-center mb-6 text-slate-500">
                            <Clock className="w-8 h-8" />
                        </div>
                        <p className="text-slate-500 dark:text-slate-400 font-bold text-lg">{t("pending.empty")}</p>
                        <Link href="/" className="mt-4 text-indigo-400 hover:underline font-bold text-sm">
                            {t("pending.goSubmit")}
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                        {tasks.map((task) => (
                            <div
                                key={task.id}
                                className="group relative bg-card-bg border border-card-border rounded-2xl p-4 transition-all hover:border-indigo-500/30"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 shrink-0 bg-background rounded-xl flex items-center justify-center overflow-hidden border border-card-border/50">
                                        {task.id.startsWith('up_') ? (
                                            <Search className="w-6 h-6 text-slate-500" />
                                        ) : (
                                            <img
                                                src={`https://i.ytimg.com/vi/${task.id}/default.jpg`}
                                                alt="thumb"
                                                className="w-full h-full object-cover opacity-50"
                                                onError={(e) => {
                                                    (e.target as any).src = "";
                                                    (e.target as any).className = "hidden";
                                                }}
                                            />
                                        )}
                                    </div>

                                    <div className="flex-grow min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-bold text-sm text-foreground truncate">
                                                {task.id}
                                            </h3>
                                            <span className={cn(
                                                "px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider",
                                                task.status === 'processing' ? "bg-indigo-500/20 text-indigo-400" :
                                                    task.status === 'queued' ? "bg-slate-800 text-slate-500" :
                                                        task.status === 'completed' ? "bg-emerald-500/20 text-emerald-400" :
                                                            "bg-red-500/20 text-red-400"
                                            )}>
                                                {task.status === 'processing' ? t("pending.statusProcessing") :
                                                    task.status === 'queued' ? t("pending.statusQueued") :
                                                        task.status === 'completed' ? t("pending.statusCompleted") :
                                                            t("pending.statusFailed")}
                                            </span>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="w-full h-1.5 bg-background border border-card-border rounded-full overflow-hidden">
                                            <div
                                                className={cn(
                                                    "h-full transition-all duration-500 ease-out",
                                                    task.status === 'processing' ? "bg-indigo-500 animate-pulse" : "bg-slate-400 dark:bg-slate-600"
                                                )}
                                                style={{ width: `${task.progress}%` }}
                                            />
                                        </div>
                                    </div>

                                    <div className="shrink-0 flex items-center gap-3">
                                        {task.status === 'processing' && <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />}
                                        {task.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                                        {task.status === 'failed' && <AlertCircle className="w-4 h-4 text-red-500" />}

                                        {task.status === 'completed' && (
                                            <Link
                                                href={`/result/${task.id}`}
                                                className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 underline"
                                            >
                                                {t("pending.viewReport")}
                                            </Link>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Recent History Section */}
                <div className="mt-16 mb-8">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-card-bg border border-card-border rounded-xl text-indigo-400 shadow-lg">
                            <Clock className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold leading-none">
                                {t("pending.recentTitle")}
                            </h2>
                            <p className="text-slate-500 dark:text-slate-500 light:text-slate-600 text-xs mt-1">
                                {t("pending.recentSubtitle")}
                            </p>
                        </div>
                    </div>

                    <div className="bg-card-bg border border-card-border rounded-3xl p-2 space-y-1 shadow-inner">
                        {recentRecords.length === 0 ? (
                            <div className="py-8 text-center text-slate-600 text-sm italic">
                                {t("pending.noRecent")}
                            </div>
                        ) : (
                            recentRecords.map((item) => (
                                <div
                                    key={`${item.id}-${item.mtime}`}
                                    className="flex items-center justify-between p-3 hover:bg-slate-100 dark:hover:bg-slate-800/30 rounded-2xl transition-all group"
                                >
                                    <div className="flex items-center gap-4 min-w-0">
                                        <div className="w-8 h-8 rounded-lg bg-background border border-card-border/50 flex items-center justify-center shrink-0 text-slate-500 group-hover:text-indigo-400 transition-colors">
                                            {item.id.includes('up_') ? <Search size={14} /> : <Youtube size={14} />}
                                        </div>
                                        <div className="min-w-0">
                                            <h4 className="text-sm font-bold text-foreground truncate pr-4">
                                                {item.title || item.id}
                                            </h4>
                                            <div className="flex items-center gap-3 mt-0.5">
                                                <span className={cn(
                                                    "text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded",
                                                    item.status === 'completed' ? "bg-emerald-500/10 text-emerald-500/80" :
                                                        item.status === 'failed' ? "bg-red-500/10 text-red-500/80" :
                                                            "bg-slate-800 text-slate-500"
                                                )}>
                                                    {item.status === 'completed' ? t("pending.statusCompleted") :
                                                        item.status === 'failed' ? t("pending.statusFailed") :
                                                            item.status}
                                                </span>
                                                <span className="text-slate-500 dark:text-slate-600 text-[10px] font-medium flex items-center gap-1">
                                                    <Clock size={10} />
                                                    {new Date(item.mtime).toLocaleString(undefined, {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4 shrink-0">
                                        {item.duration ? (
                                            <div className="text-[10px] font-bold text-slate-500 tabular-nums">
                                                {Math.floor(item.duration / 60)}:{(item.duration % 60).toString().padStart(2, '0')}
                                                <span className="ml-0.5 opacity-50 font-medium">{t("pending.seconds")}</span>
                                            </div>
                                        ) : null}

                                        {item.status === 'completed' && (
                                            <Link
                                                href={`/result/${item.id}`}
                                                className="w-8 h-8 flex items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 opacity-0 group-hover:opacity-100 transition-all hover:bg-indigo-500 hover:text-white"
                                            >
                                                <ChevronLeft className="w-4 h-4 rotate-180" />
                                            </Link>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="mt-12 p-6 bg-indigo-500/5 rounded-[2rem] border border-indigo-500/10">
                    <h4 className="text-indigo-500 dark:text-indigo-400 text-xs font-black uppercase tracking-widest mb-2 flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5" />
                        {t("pending.noteTitle")}
                    </h4>
                    <ul className="text-slate-500 dark:text-slate-500 light:text-slate-600 text-xs space-y-2 font-medium">
                        <li>• {t("pending.note1")}</li>
                        <li>• {t("pending.note2")}</li>
                        <li>• {t("pending.note3")}</li>
                    </ul>
                </div>
            </main>
        </div>
    );
}

const Sparkles = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
);
