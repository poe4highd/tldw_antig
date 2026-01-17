"use client";

import React, { useState, useRef, useEffect, use } from "react";
import Link from "next/link";
import {
    ArrowLeft,
    Share2,
    MessageSquare,
    ThumbsUp,
    Download,
    Copy,
    Check,
    User,
    Send,
    MoreVertical,
    Play
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Types
interface Sentence {
    start: number;
    text: string;
}
interface Paragraph {
    sentences: Sentence[];
}
interface Result {
    title: string;
    youtube_id?: string;
    paragraphs?: Paragraph[];
}

export default function EnhancedResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [currentTime, setCurrentTime] = useState(0);
    const [copyStatus, setCopyStatus] = useState(false);
    const [likeCount, setLikeCount] = useState(128);
    const [isLiked, setIsLiked] = useState(false);

    // Mock Video Data (In real app, fetch from backend)
    const mockResult: Result = {
        title: "“普通人别学投资”，是我听过最荒谬的蠢话",
        youtube_id: "_1C1mRhUYwo",
        paragraphs: [
            {
                sentences: [
                    { start: 0, text: "大家好，我是老总。我前面一条视频，评论区里组织一种声音仿佛出现。普通人不要学习投资，越学越亏。" },
                    { start: 7.9, text: "订投指数就够了。每次看到这句话，我顿时就黑人问号脸了。你从来没意识到这句话背后的逻辑很荒谬吗？" }
                ]
            },
            {
                sentences: [
                    { start: 18.3, text: "我给你这话来做几个类比，大家听听看。普通人别学开车了，学会了终于出车祸。老老实实做地铁就行。" },
                    { start: 25.8, text: "普通人别学英语了，学来是满口的亲个类似。说好中文就行了。你会不会觉得说这些话的人很可笑？" }
                ]
            }
        ]
    };

    const copyFullText = () => {
        setCopyStatus(true);
        setTimeout(() => setCopyStatus(false), 2000);
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 font-sans">
            {/* Top Navigation Bar */}
            <nav className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-900 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-6">
                    <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-xl transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center space-x-3">
                        <div className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg">
                            <img src="/icon.png" alt="Logo" className="w-4 h-4" />
                        </div>
                        <span className="text-sm font-bold truncate max-w-[200px] md:max-w-md">{mockResult.title}</span>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    <button className="flex items-center space-x-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl text-xs font-bold transition-all text-slate-400 hover:text-white">
                        <Share2 className="w-4 h-4" />
                        <span className="hidden sm:inline">共享报告</span>
                    </button>
                    <button className="p-2 bg-indigo-500 text-white rounded-full hover:scale-105 transition-all shadow-lg shadow-indigo-500/20 active:scale-95 md:hidden">
                        <Download className="w-5 h-5" />
                    </button>
                </div>
            </nav>

            <main className="max-w-[1440px] mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Left Column: Video & Transcription */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Video Player Section */}
                    <div className="relative aspect-video bg-black rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 group">
                        <iframe
                            src={`https://www.youtube.com/embed/${mockResult.youtube_id}?enablejsapi=1&autoplay=0`}
                            className="w-full h-full"
                            allowFullScreen
                        />
                        {/* Custom Overlay (Optional logic could go here) */}
                    </div>

                    {/* Video Info & High-level Actions */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 px-4">
                        <div>
                            <h2 className="text-2xl font-black mb-2 tracking-tight">{mockResult.title}</h2>
                            <div className="flex items-center space-x-4 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <span>12,482 次阅读</span>
                                <span>上传于 2024-01-16</span>
                            </div>
                        </div>

                        <div className="flex items-center space-x-2">
                            <button
                                onClick={() => { setIsLiked(!isLiked); setLikeCount(l => isLiked ? l - 1 : l + 1); }}
                                className={cn(
                                    "flex items-center space-x-2 px-5 py-2.5 rounded-2xl font-bold text-sm border transition-all",
                                    isLiked ? "bg-indigo-500 border-indigo-500 text-white shadow-lg shadow-indigo-500/20" : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                                )}
                            >
                                <ThumbsUp className={cn("w-4 h-4", isLiked && "fill-current")} />
                                <span>{likeCount}</span>
                            </button>
                            <button onClick={copyFullText} className="flex items-center space-x-2 px-5 py-2.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl font-bold text-sm text-slate-400 hover:text-white transition-all">
                                {copyStatus ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                                <span>{copyStatus ? "已复制" : "复制全文"}</span>
                            </button>
                        </div>
                    </div>

                    {/* Transcription Content */}
                    <div className="bg-slate-900/30 border border-slate-800/50 rounded-[2.5rem] p-10 relative overflow-hidden">
                        <div className="absolute top-8 right-8 text-[120px] font-black text-white/[0.02] pointer-events-none select-none italic">
                            TLDW
                        </div>

                        <div className="space-y-12 relative z-10">
                            {mockResult.paragraphs?.map((p, pIdx) => (
                                <p key={pIdx} className="text-lg leading-[1.8] text-slate-300">
                                    {p.sentences.map((s, sIdx) => (
                                        <span
                                            key={sIdx}
                                            className="cursor-pointer hover:text-white hover:bg-white/5 rounded px-1 transition-all duration-300"
                                            onClick={() => setCurrentTime(s.start)}
                                        >
                                            {s.text}
                                        </span>
                                    ))}
                                </p>
                            ))}

                            <div className="pt-8 border-t border-slate-800 flex items-center justify-between">
                                <p className="text-xs font-bold text-slate-600 uppercase tracking-widest leading-relaxed">
                                    生成报告耗时: 4.2s <br />
                                    AI 模型: GPT-4o 增强版
                                </p>
                                <button className="flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 font-bold text-sm transition-colors">
                                    <span>下载原文字幕 (.srt)</span>
                                    <Download className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Discussion & Analytics Side Panel */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Discussion Section */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] flex flex-col h-[600px]">
                        <div className="p-8 border-b border-slate-800 flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <MessageSquare className="w-5 h-5 text-indigo-400" />
                                <h3 className="font-bold">讨论区 (32)</h3>
                            </div>
                            <MoreVertical className="w-5 h-5 text-slate-600 cursor-pointer" />
                        </div>

                        <div className="flex-grow overflow-y-auto p-8 space-y-8 no-scrollbar">
                            {/* Mock Comments */}
                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center font-bold text-xs ring-2 ring-white/5">A</div>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold">Alice_Wonder</span>
                                        <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">2小时前</span>
                                    </div>
                                    <p className="text-sm text-slate-400 leading-relaxed">这个视频里的开车类比真的绝了，很多所谓的“专家”就是喜欢把简单的东西复杂化来收割普通人。</p>
                                    <div className="flex items-center gap-4 pt-1">
                                        <button className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 hover:text-indigo-400 transition-colors">
                                            <ThumbsUp className="w-3 h-3" /> 12
                                        </button>
                                        <button className="text-[10px] font-bold text-slate-500 hover:text-white transition-colors">回复</button>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center font-bold text-xs ring-2 ring-white/5">K</div>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-bold">Ken_Growth</span>
                                        <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">5小时前</span>
                                    </div>
                                    <p className="text-sm text-slate-400 leading-relaxed">有没有人觉得 7:15 那段关于复利的解释有点过于理想化了？实际操作中的磨损很大性。</p>
                                    <div className="flex items-center gap-4 pt-1">
                                        <button className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 hover:text-indigo-400 transition-colors">
                                            <ThumbsUp className="w-3 h-3" /> 5
                                        </button>
                                        <button className="text-[10px] font-bold text-slate-500 hover:text-white transition-colors">回复</button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="发表你的深度见解..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-700 transition-all font-medium"
                                />
                                <button className="absolute right-2 top-2 p-1.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors">
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* User Interest Heatmap Placeholder */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-8">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold">关注热度统计</h3>
                            <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 text-[10px] font-bold rounded-full border border-indigo-500/20">实时</span>
                        </div>
                        <div className="space-y-4">
                            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden flex">
                                <div className="h-full bg-indigo-500" style={{ width: '45%' }}></div>
                                <div className="h-full bg-indigo-600 opacity-50" style={{ width: '20%' }}></div>
                                <div className="h-full bg-indigo-400" style={{ width: '35%' }}></div>
                            </div>
                            <div className="flex justify-between text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                                <span>00:00</span>
                                <span>重点关注区域</span>
                                <span>12:45</span>
                            </div>
                        </div>
                        <p className="mt-6 text-xs text-slate-500 leading-relaxed font-medium">
                            本视频的 **4:12 - 6:30** 区域互动量最高，建议重点阅读。
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
