"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
    History,
    ChevronRight,
    Terminal,
    Calendar,
    ArrowLeft
} from "lucide-react";
import { getApiBase } from "@/utils/api";

export default function DevLogsPage() {
    const [logs, setLogs] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            setIsLoading(true);
            try {
                const apiBase = getApiBase();

                const response = await fetch(`${apiBase}/dev-docs`);
                const data = await response.json();
                setLogs(data);
            } catch (error) {
                console.error("Failed to fetch dev logs:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchLogs();
    }, []);

    const formatDate = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
            <div className="max-w-4xl mx-auto px-6 py-20">
                {/* Header */}
                <header className="mb-16">
                    <Link
                        href="/"
                        className="inline-flex items-center space-x-2 text-slate-500 hover:text-white transition-colors mb-8 group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        <span className="text-sm font-bold uppercase tracking-widest">返回首页</span>
                    </Link>

                    <div className="flex items-center space-x-4 mb-6">
                        <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl">
                            <Terminal className="w-8 h-8 text-indigo-400" />
                        </div>
                        <div>
                            <h1 className="text-5xl font-black tracking-tighter">开发日志</h1>
                            <p className="text-slate-500 font-medium text-lg mt-1">记录项目演进的每一个瞬间</p>
                        </div>
                    </div>
                </header>

                {/* List Area */}
                {isLoading ? (
                    <div className="space-y-4">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-24 bg-slate-900/50 border border-slate-900 rounded-3xl animate-pulse" />
                        ))}
                    </div>
                ) : logs.length === 0 ? (
                    <div className="text-center py-20 bg-slate-900/20 border border-dashed border-slate-800 rounded-3xl">
                        <p className="text-slate-500 font-medium">暂无公开日志记录</p>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {logs.map((log) => (
                            <Link
                                key={log.filename}
                                href={`/dev-logs/${log.filename}`}
                                className="block group p-8 bg-slate-900/30 border border-slate-800/50 rounded-3xl hover:border-indigo-500/50 hover:bg-slate-900/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/5"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="space-y-3">
                                        <div className="flex items-center space-x-3 text-slate-500 group-hover:text-indigo-400 transition-colors">
                                            <Calendar className="w-4 h-4" />
                                            <span className="text-xs font-bold uppercase tracking-widest leading-none">
                                                {formatDate(log.mtime)}
                                            </span>
                                        </div>
                                        <h2 className="text-2xl font-black tracking-tight group-hover:translate-x-1 transition-transform">
                                            {log.title}
                                        </h2>
                                    </div>
                                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl group-hover:border-indigo-500/50 group-hover:text-indigo-400 transition-all">
                                        <ChevronRight className="w-6 h-6" />
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}

                {/* Footer Info */}
                <footer className="mt-20 pt-10 border-t border-slate-900 text-center">
                    <p className="text-slate-600 text-sm font-medium">
                        本页面内容实时同步自项目 <code>dev_docs/</code> 目录
                    </p>
                </footer>
            </div>
        </div>
    );
}
