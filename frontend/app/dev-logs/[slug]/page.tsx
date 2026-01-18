"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
    ArrowLeft,
    Calendar,
    Clock,
    BookOpen
} from "lucide-react";
import { getApiBase } from "@/utils/api";

export default function DevLogDetailPage() {
    const params = useParams();
    const slug = params.slug as string;
    const [content, setContent] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchContent = async () => {
            setIsLoading(true);
            try {
                const apiBase = getApiBase();

                const response = await fetch(`${apiBase}/dev-docs/${slug}`);
                if (!response.ok) throw new Error("无法读取文件内容");
                const data = await response.json();
                setContent(data.content);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        if (slug) fetchContent();
    }, [slug]);

    if (error) {
        return (
            <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center p-6">
                <div className="text-center space-y-4">
                    <p className="text-red-400 font-bold">{error}</p>
                    <Link href="/dev-logs" className="text-indigo-400 hover:text-indigo-300 font-bold underline">返回列表</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
            <div className="max-w-4xl mx-auto px-6 py-20">
                {/* Navigation */}
                <nav className="mb-12">
                    <Link
                        href="/dev-logs"
                        className="inline-flex items-center space-x-2 text-slate-500 hover:text-white transition-colors group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        <span className="text-sm font-bold uppercase tracking-widest">返回日志列表</span>
                    </Link>
                </nav>

                {/* Content Area */}
                {isLoading ? (
                    <div className="space-y-6">
                        <div className="h-16 bg-slate-900/50 rounded-2xl w-3/4 animate-pulse" />
                        <div className="space-y-3">
                            {[1, 2, 3, 4, 5, 6].map(i => (
                                <div key={i} className="h-4 bg-slate-900/30 rounded w-full animate-pulse" />
                            ))}
                        </div>
                    </div>
                ) : (
                    <article className="relative">
                        {/* Markdown Content */}
                        <div className="markdown-body">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {content}
                            </ReactMarkdown>
                        </div>
                    </article>
                )}

                {/* Custom Styles */}
                <style jsx global>{`
                    .markdown-body {
                        font-family: inherit;
                        color: #cbd5e1;
                        line-height: 1.8;
                    }
                    .markdown-body h1 {
                        font-size: 3rem;
                        font-weight: 900;
                        letter-spacing: -0.05em;
                        color: #f8fafc;
                        margin-bottom: 2rem;
                        border-bottom: 1px solid #1e293b;
                        padding-bottom: 1rem;
                    }
                    .markdown-body h2 {
                        font-size: 1.875rem;
                        font-weight: 800;
                        color: #f8fafc;
                        margin-top: 3rem;
                        margin-bottom: 1.5rem;
                        display: flex;
                        align-items: center;
                    }
                    .markdown-body h2::before {
                        content: '';
                        display: block;
                        width: 4px;
                        height: 24px;
                        background: #6366f1;
                        margin-right: 12px;
                        border-radius: 99px;
                    }
                    .markdown-body h3 {
                        font-size: 1.25rem;
                        font-weight: 700;
                        color: #f8fafc;
                        margin-top: 2rem;
                        margin-bottom: 1rem;
                    }
                    .markdown-body p {
                        margin-bottom: 1.5rem;
                    }
                    .markdown-body ul, .markdown-body ol {
                        margin-bottom: 1.5rem;
                        padding-left: 1.5rem;
                    }
                    .markdown-body li {
                        margin-bottom: 0.5rem;
                    }
                    .markdown-body code {
                        background: #1e293b;
                        padding: 0.2rem 0.4rem;
                        border-radius: 0.4rem;
                        font-size: 0.9em;
                        color: #818cf8;
                    }
                    .markdown-body pre {
                        background: #020617;
                        border: 1px solid #1e293b;
                        padding: 1.5rem;
                        border-radius: 1.5rem;
                        margin-bottom: 2rem;
                        overflow-x: auto;
                    }
                    .markdown-body pre code {
                        background: transparent;
                        padding: 0;
                        color: #94a3b8;
                    }
                    .markdown-body blockquote {
                        border-left: 4px solid #334155;
                        padding: 1rem 1.5rem;
                        background: #0f172a;
                        border-radius: 0 1rem 1rem 0;
                        margin-bottom: 2rem;
                        color: #94a3b8;
                        font-style: italic;
                    }
                    .markdown-body table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 2rem;
                        border-radius: 1rem;
                        overflow: hidden;
                        border: 1px solid #1e293b;
                    }
                    .markdown-body th {
                        background: #1e293b;
                        padding: 1rem;
                        text-align: left;
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                        color: #94a3b8;
                    }
                    .markdown-body td {
                        padding: 1rem;
                        border-top: 1px solid #1e293b;
                        font-size: 0.875rem;
                    }
                    .markdown-body hr {
                        border: 0;
                        border-top: 1px solid #1e293b;
                        margin: 4rem 0;
                    }
                    .markdown-body a {
                        color: #6366f1;
                        text-decoration: underline;
                        text-underline-offset: 4px;
                    }
                    .markdown-body a:hover {
                        color: #818cf8;
                    }
                `}</style>
            </div>
        </div>
    );
}
