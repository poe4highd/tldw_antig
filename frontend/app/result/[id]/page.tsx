"use client";

import React, { useState, useRef, useEffect, use } from "react";
import Link from "next/link";
import YouTube, { YouTubeProps } from 'react-youtube';

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
    Play,
    ArrowDownToLine // New icon for sync button
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
    usage?: {
        total_cost: number;
    };
    raw_subtitles?: any[];
    mtime?: string | number;
    thumbnail?: string;
    media_path?: string;
}

export default function EnhancedResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [result, setResult] = useState<Result | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copyStatus, setCopyStatus] = useState(false);
    const [likeCount, setLikeCount] = useState(128);
    const [isLiked, setIsLiked] = useState(false);
    // const iframeRef = useRef<HTMLIFrameElement>(null); // Removed in favor of react-youtube
    const playerRef = useRef<any>(null); // YouTube Player instance ref
    const [isPlayerReady, setIsPlayerReady] = useState(false); // Track readiness for UI/polling
    const audioRef = useRef<HTMLAudioElement>(null);
    const [useLocalAudio, setUseLocalAudio] = useState(false);

    const [currentTime, setCurrentTime] = useState(0);
    const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false); // New state for scroll control
    const subtitleContainerRef = useRef<HTMLDivElement>(null); // Ref for custom scrolling
    const isProgrammaticScroll = useRef(false); // Flag to distinguish auto-scroll from user scroll

    const [viewCount, setViewCount] = useState(0);
    const [comments, setComments] = useState<any[]>([]);
    const [newComment, setNewComment] = useState("");
    // const [origin, setOrigin] = useState(""); // react-youtube handles origin

    // useEffect(() => {
    //     setOrigin(window.location.origin);
    // }, []);

    useEffect(() => {
        const fetchResult = async () => {
            try {
                const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

                // Fetch basic result
                const response = await fetch(`${apiBase}/result/${id}`);
                if (!response.ok) throw new Error("无法获取报告内容");
                const data = await response.json();

                if (data.status === "completed") {
                    setResult(data);
                    setViewCount(data.view_count || 0);
                    setLikeCount(data.interaction_count || 0);

                    // Trigger view increment
                    fetch(`${apiBase}/result/${id}/view`, { method: 'POST' });

                    // Fetch comments
                    const commRes = await fetch(`${apiBase}/result/${id}/comments`);
                    if (commRes.ok) {
                        const commData = await commRes.json();
                        setComments(commData);
                    }
                } else if (data.status === "failed") {
                    setError(data.detail || "处理失败");
                } else {
                    setError("该报告正在生成中，请稍后再试。");
                }
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchResult();
    }, [id]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (!useLocalAudio && isPlayerReady && playerRef.current) {
            interval = setInterval(() => {
                // Ensure player is ready and has the function
                if (playerRef.current && typeof playerRef.current.getCurrentTime === 'function') {
                    const time = playerRef.current.getCurrentTime();
                    // getCurrentTime returns a number, safeguard against undefined
                    if (typeof time === 'number') {
                        setCurrentTime(time);
                    }
                }
            }, 200); // Poll every 200ms for smoother updates
        }
        return () => clearInterval(interval);
    }, [useLocalAudio, isPlayerReady]);

    const handleLocalTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
        }
    };

    const seekTo = (seconds: number) => {
        if (useLocalAudio && audioRef.current) {
            audioRef.current.currentTime = seconds;
            audioRef.current.play();
        } else if (playerRef.current && typeof playerRef.current.seekTo === 'function') {
            playerRef.current.seekTo(seconds, true);
            playerRef.current.playVideo();
        }
    };

    const onPlayerReady: YouTubeProps['onReady'] = (event) => {
        playerRef.current = event.target;
        setIsPlayerReady(true);
    };

    const scrollToActive = (force = false) => {
        if (!result?.paragraphs || !subtitleContainerRef.current) return;

        let activeId = "";
        for (let pIdx = 0; pIdx < result.paragraphs.length; pIdx++) {
            const p = result.paragraphs[pIdx];
            for (let sIdx = 0; sIdx < p.sentences.length; sIdx++) {
                const s = p.sentences[sIdx];
                const nextS = p.sentences[sIdx + 1] || result.paragraphs[pIdx + 1]?.sentences?.[0];
                if (currentTime >= s.start && (nextS ? currentTime < nextS.start : true)) {
                    activeId = `sentence-${pIdx}-${sIdx}`;
                    break;
                }
            }
            if (activeId) break;
        }

        if (activeId) {
            const container = subtitleContainerRef.current;
            const el = document.getElementById(activeId);
            if (el) {
                const containerRect = container.getBoundingClientRect();
                const elRect = el.getBoundingClientRect();
                const offset = elRect.top - containerRect.top;
                const targetScroll = container.scrollTop + offset - (container.clientHeight / 2) + (el.clientHeight / 2);

                if (force || Math.abs(container.scrollTop - targetScroll) > 10) {
                    isProgrammaticScroll.current = true;
                    container.scrollTo({
                        top: targetScroll,
                        behavior: 'smooth'
                    });
                    // Reset flag after smooth scroll duration
                    setTimeout(() => {
                        isProgrammaticScroll.current = false;
                    }, 500);
                }
            }
        }
    };

    // Handle manual scroll to show sync button
    const handleManualScroll = () => {
        if (!isProgrammaticScroll.current && !isAutoScrollPaused) {
            setIsAutoScrollPaused(true);
        }
    };

    // Auto-scroll logic
    useEffect(() => {
        if (!isAutoScrollPaused) {
            scrollToActive(false);
        }
    }, [currentTime, isAutoScrollPaused, result]);

    const resumeAutoScroll = () => {
        setIsAutoScrollPaused(false);
        // Force immediate scroll back
        setTimeout(() => scrollToActive(true), 0);
    };

    const copyFullText = () => {
        if (!result?.paragraphs) return;
        const fullText = result.paragraphs
            .map(p => p.sentences.map(s => s.text).join(""))
            .join("\n\n");
        navigator.clipboard.writeText(fullText);
        setCopyStatus(true);
        setTimeout(() => setCopyStatus(false), 2000);
    };

    const downloadSRT = () => {
        if (!result?.raw_subtitles) return;
        const formatTime = (sec: number) => {
            const h = Math.floor(sec / 3600).toString().padStart(2, '0');
            const m = Math.floor((sec % 3600) / 60).toString().padStart(2, '0');
            const s = Math.floor(sec % 60).toString().padStart(2, '0');
            const ms = Math.floor((sec % 1) * 1000).toString().padStart(3, '0');
            return `${h}:${m}:${s},${ms}`;
        };
        const srtContent = result.raw_subtitles.map((sub, i) =>
            `${i + 1}\n${formatTime(sub.start)} --> ${formatTime(sub.end)}\n${sub.text}`
        ).join("\n\n");
        const blob = new Blob([srtContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${result.title || "subtitle"}.srt`;
        a.click();
    };

    const handleToggleLike = async () => {
        setIsLiked(!isLiked);
        setLikeCount(l => isLiked ? l - 1 : l + 1);
        try {
            const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
            await fetch(`${apiBase}/result/${id}/like`, { method: 'POST' });
        } catch (err) { }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error || !result) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
                <h1 className="text-2xl font-bold text-slate-200 mb-4">糟糕！出错了</h1>
                <p className="text-slate-400 mb-8">{error || "找不到该报告"}</p>
                <Link href="/dashboard" className="px-6 py-2 bg-indigo-500 rounded-xl font-bold">返回见地</Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 font-sans">
            {/* Top Navigation Bar */}
            <nav className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-900 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-6">
                    <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-xl transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <Link href="/?noredirect=1" className="flex items-center space-x-3 cursor-pointer group">
                        <div className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg group-hover:border-indigo-500/50 transition-colors">
                            <img src="/icon.png" alt="Logo" className="w-4 h-4" />
                        </div>
                        <span className="text-sm font-bold truncate max-w-[200px] md:max-w-md">{result.title}</span>
                    </Link>
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
                <div className="lg:col-span-8 lg:sticky lg:top-20 lg:h-[calc(100vh-7rem)] flex flex-col gap-6">
                    {/* Fixed Header Group: Video, Actions, Info */}
                    <div className="flex-shrink-0 space-y-6 sticky top-[72px] lg:static z-50 bg-slate-950 lg:bg-slate-950 py-2 lg:py-0 -mx-6 px-6 lg:mx-0 lg:px-0 transition-all lg:rounded-none shadow-xl lg:shadow-none border-b border-white/5 lg:border-none">
                        {/* Video Player Section */}
                        <div className="relative aspect-video bg-black rounded-[2.5rem] overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 group transition-all duration-300">
                            <div className="relative aspect-video group">
                                {useLocalAudio ? (
                                    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900 group">
                                        <img
                                            src={result.thumbnail?.startsWith('http') ? result.thumbnail : `${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}/media/${result.thumbnail}`}
                                            alt="Thumbnail"
                                            className="absolute inset-0 w-full h-full object-cover opacity-20 blur-sm"
                                        />
                                        <div className="relative z-10 p-8 flex flex-col items-center text-center">
                                            <div className="w-20 h-20 bg-indigo-500 rounded-full flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/50">
                                                <Play className="w-8 h-8 text-white fill-current" />
                                            </div>
                                            <h4 className="text-xl font-bold mb-2">正在播放本地音频</h4>
                                            <p className="text-sm text-slate-400 max-w-xs">已切换至转录音频，确保语音与字幕严格同步。</p>
                                        </div>
                                        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-md px-10">
                                            <audio
                                                ref={audioRef}
                                                src={`${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}/media/${result.media_path}`}
                                                controls
                                                onTimeUpdate={handleLocalTimeUpdate}
                                                className="w-full h-10 accent-indigo-500"
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <YouTube
                                        videoId={result.youtube_id}
                                        className="w-full h-full"
                                        iframeClassName="w-full h-full"
                                        onReady={onPlayerReady}
                                        opts={{
                                            height: '100%',
                                            width: '100%',
                                            playerVars: {
                                                autoplay: 0,
                                                hl: 'zh-CN',
                                                // origin will be handled automatically, but explicitly disabling modestbranding etc can be nice
                                            },
                                        }}
                                    />
                                )}
                                <button
                                    onClick={() => setUseLocalAudio(!useLocalAudio)}
                                    className="absolute top-6 right-6 z-20 px-4 py-2 bg-black/60 backdrop-blur-md border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-500 transition-all shadow-xl"
                                >
                                    {useLocalAudio ? "返回 YouTube 视频" : "切换为同步音频"}
                                </button>

                            </div>
                        </div>

                        {/* Action Bar Below Video */}
                        <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-2xl backdrop-blur-sm">
                            <div className="flex items-center space-x-2">
                                <button
                                    onClick={copyFullText}
                                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs font-bold text-slate-200 hover:bg-indigo-500 hover:border-indigo-500 transition-all flex items-center space-x-2 group"
                                >
                                    {copyStatus ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400 group-hover:text-white" />}
                                    <span>{copyStatus ? "已复制" : "复制全文"}</span>
                                </button>
                                <button
                                    onClick={downloadSRT}
                                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs font-bold text-slate-200 hover:bg-indigo-500 hover:border-indigo-500 transition-all flex items-center space-x-2 group"
                                >
                                    <Download className="w-4 h-4 text-slate-400 group-hover:text-white" />
                                    <span>SRT</span>
                                </button>
                                <button
                                    onClick={() => {
                                        if (!result?.paragraphs) return;
                                        const text = result.paragraphs.map(p => p.sentences.map(s => s.text).join("")).join("\n\n");
                                        const blob = new Blob([text], { type: "text/plain" });
                                        const url = URL.createObjectURL(blob);
                                        const a = document.createElement("a");
                                        a.href = url;
                                        a.download = `${result.title}.txt`;
                                        a.click();
                                    }}
                                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs font-bold text-slate-200 hover:bg-indigo-500 hover:border-indigo-500 transition-all flex items-center space-x-2 group"
                                >
                                    <Download className="w-4 h-4 text-slate-400 group-hover:text-white" />
                                    <span>TXT</span>
                                </button>
                            </div>
                            <div>
                                <button
                                    onClick={handleToggleLike}
                                    className={cn(
                                        "px-5 py-2 border rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shadow-sm",
                                        isLiked ? "bg-indigo-500 border-indigo-500 text-white" : "bg-slate-800 border-slate-700 text-slate-200 hover:bg-indigo-500 hover:border-indigo-500"
                                    )}
                                >
                                    <ThumbsUp className={cn("w-4 h-4", isLiked && "fill-current")} />
                                    <span>{likeCount}</span>
                                </button>
                            </div>
                        </div>

                        {/* Video Info */}
                        <div className="px-4">
                            <h2 className="text-2xl font-black mb-2 tracking-tight">{result.title}</h2>
                            <div className="flex items-center space-x-4 text-xs font-bold text-slate-500 uppercase tracking-widest">
                                <span>{viewCount.toLocaleString()} 次阅读</span>
                                <span>自动生成于 {(() => {
                                    const date = result.mtime ? new Date(result.mtime) : new Date();
                                    return date.toLocaleDateString('zh-CN', {
                                        year: 'numeric', month: '2-digit', day: '2-digit'
                                    }).replace(/\//g, '-');
                                })()}</span>
                            </div>
                        </div>
                    </div> {/* End of Header Group */}

                    {/* Transcription Content - Scrollable Area */}
                    <div
                        ref={subtitleContainerRef}
                        onWheel={handleManualScroll}
                        onTouchMove={handleManualScroll}
                        className="bg-slate-900/30 border border-slate-800/50 rounded-[2.5rem] p-8 relative flex-1 min-h-0 lg:overflow-y-auto no-scrollbar scroll-smooth"
                    >
                        <div className="absolute top-8 right-8 text-[120px] font-black text-white/[0.02] pointer-events-none select-none italic">
                            TLDW
                        </div>

                        <div className="space-y-12 relative z-10">
                            {(() => {
                                const allSentences = result.paragraphs?.flatMap(p => p.sentences) || [];
                                return result.paragraphs?.map((p: Paragraph, pIdx: number) => (
                                    <p key={pIdx} className="text-lg leading-[1.8] text-slate-400">
                                        {p.sentences.map((s: Sentence, sIdx: number) => {
                                            const flatIdx = allSentences.indexOf(s);
                                            const nextS = allSentences[flatIdx + 1];
                                            const isCurrent = currentTime >= s.start && (nextS ? currentTime < nextS.start : true);

                                            return (
                                                <span
                                                    key={sIdx}
                                                    id={`sentence-${pIdx}-${sIdx}`}
                                                    className={cn(
                                                        "cursor-pointer rounded px-1 transition-all duration-300 inline",
                                                        isCurrent ? "text-indigo-400 bg-indigo-500/10" : "hover:text-white hover:bg-white/5"
                                                    )}
                                                    style={{ fontSize: 'inherit', fontWeight: 'inherit' }} // Force stable font size
                                                    onClick={() => seekTo(s.start)}
                                                >
                                                    {s.text}
                                                </span>
                                            );
                                        })}
                                    </p>
                                ))
                            })()}

                            <div className="pt-8 border-t border-slate-800 flex items-center justify-between">
                                <p className="text-xs font-bold text-slate-600 uppercase tracking-widest leading-relaxed">
                                    生成消耗: ${result.usage?.total_cost || "0.01"} <br />
                                    AI 模型: Claude 3.5 Sonnet
                                </p>
                            </div>
                        </div>
                    </div>
                    {/* Resume Follow Button */}
                    {isAutoScrollPaused && (
                        <div className="fixed bottom-10 right-10 z-50 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <button
                                onClick={resumeAutoScroll}
                                className="flex items-center space-x-2 px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-lg shadow-indigo-500/30 transition-all transform hover:scale-105 active:scale-95 font-bold"
                            >
                                <ArrowDownToLine className="w-5 h-5" />
                                <span>同步播放进度</span>
                            </button>
                        </div>
                    )}
                </div>

                {/* Right Column: Discussion & Analytics Side Panel */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Discussion Section */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] flex flex-col h-[600px]">
                        <div className="p-8 border-b border-slate-800 flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <MessageSquare className="w-5 h-5 text-indigo-400" />
                                <h3 className="font-bold">讨论区 ({comments.length})</h3>
                            </div>
                            <MoreVertical className="w-5 h-5 text-slate-600 cursor-pointer" />
                        </div>

                        <div className="flex-grow overflow-y-auto p-8 space-y-8 no-scrollbar">
                            {comments.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
                                    <MessageSquare className="w-8 h-8 opacity-20" />
                                    <p className="text-sm">暂无评论，快来抢沙发吧</p>
                                </div>
                            ) : comments.map((comment, idx) => (
                                <div key={comment.id || idx} className="flex gap-4">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-slate-800 flex items-center justify-center font-bold text-xs ring-2 ring-white/5 overflow-hidden">
                                        {comment.profiles?.avatar_url ? (
                                            <img src={comment.profiles.avatar_url} className="w-full h-full object-cover" />
                                        ) : (
                                            (comment.profiles?.username?.[0] || comment.user_id?.[0] || "?").toUpperCase()
                                        )}
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-bold text-slate-200">{comment.profiles?.username || "热心网友"}</span>
                                            <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">
                                                {new Date(comment.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-400 leading-relaxed">{comment.content}</p>
                                        <div className="flex items-center gap-4 pt-1">
                                            <button className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 hover:text-indigo-400 transition-colors">
                                                <ThumbsUp className="w-3 h-3" /> {comment.likes_count || 0}
                                            </button>
                                            <button className="text-[10px] font-bold text-slate-500 hover:text-white transition-colors">回复</button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
                            <form onSubmit={async (e) => {
                                e.preventDefault();
                                if (!newComment.trim()) return;
                                try {
                                    const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
                                    const res = await fetch(`${apiBase}/result/${id}/comments`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ video_id: id, content: newComment })
                                    });
                                    if (res.ok) {
                                        const data = await res.json();
                                        setComments([data.comment, ...comments]);
                                        setNewComment("");
                                    }
                                } catch (err) { }
                            }} className="relative">
                                <input
                                    type="text"
                                    value={newComment}
                                    onChange={(e) => setNewComment(e.target.value)}
                                    placeholder="发表你的深度见解..."
                                    className="w-full bg-slate-950 border border-slate-800 rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-700 transition-all font-medium"
                                />
                                <button type="submit" className="absolute right-2 top-2 p-1.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors">
                                    <Send className="w-4 h-4" />
                                </button>
                            </form>
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
