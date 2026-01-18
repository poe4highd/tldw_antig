"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, History, FileText, Tag, Calendar } from "lucide-react";

interface HistoryItem {
    date: string;
    category: string;
    task: string;
    description: string;
    log_file: string;
}

export default function ProjectHistoryPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/project-history`);
                const data = await res.json();
                setHistory(data);
            } catch (err) {
                console.error("Failed to fetch project history:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 pb-20">
            {/* Header */}
            <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-10">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors">
                            <ArrowLeft className="w-5 h-5 text-slate-500" />
                        </Link>
                        <div className="flex items-center gap-2">
                            <History className="w-6 h-6 text-blue-500" />
                            <h1 className="text-xl font-bold text-slate-900 dark:text-white">项目开发史记</h1>
                        </div>
                    </div>
                    <div className="text-sm text-slate-400 font-mono">
                        .antigravity/PROJECT_HISTORY.md
                    </div>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-6 pt-10">
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-32 bg-slate-200 dark:bg-slate-800 animate-pulse rounded-xl" />
                        ))}
                    </div>
                ) : (
                    <div className="relative space-y-8">
                        {/* Timeline Line */}
                        <div className="absolute left-8 top-0 bottom-0 w-px bg-slate-200 dark:bg-slate-800 hidden md:block" />

                        {history.map((item, idx) => (
                            <div key={idx} className="relative md:pl-16 group">
                                {/* Timeline Dot */}
                                <div className="absolute left-7.5 top-6 w-1.5 h-1.5 rounded-full bg-blue-500 ring-4 ring-white dark:ring-slate-900 hidden md:block group-hover:scale-125 transition-transform" />

                                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all">
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                                        <div className="flex items-center gap-3">
                                            <span className="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-full uppercase tracking-wider">
                                                {item.category}
                                            </span>
                                            <h2 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-blue-500 transition-colors">
                                                {item.task}
                                            </h2>
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-4 h-4" />
                                                {item.date}
                                            </div>
                                        </div>
                                    </div>

                                    <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6">
                                        {item.description}
                                    </p>

                                    <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-4 mt-auto">
                                        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                                            <FileText className="w-3.5 h-3.5" />
                                            {item.log_file}
                                        </div>
                                        <div className="text-xs text-slate-300 dark:text-slate-600 italic">
                                            # Audit Record {history.length - idx}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
