"use client";

import React, { useState, useRef, useEffect, use } from "react";
import Link from "next/link";
import YouTube, { YouTubeProps } from 'react-youtube';
import { getApiBase } from "@/utils/api";
import { useTranslation } from "@/contexts/LanguageContext";

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
    ArrowDownToLine,
    Sun,
    Moon,
    Heart
} from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { supabase } from "@/utils/supabase";

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
    summary?: string;
    keywords?: string[];
}

export default function EnhancedResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { t, language } = useTranslation();
    const { theme, toggleTheme } = useTheme();
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
    const [videoDuration, setVideoDuration] = useState(0);
    const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false); // New state for scroll control
    const subtitleContainerRef = useRef<HTMLDivElement>(null); // Ref for custom scrolling
    const isProgrammaticScroll = useRef(false); // Flag to distinguish auto-scroll from user scroll

    const [viewCount, setViewCount] = useState(0);
    const [comments, setComments] = useState<any[]>([]);
    const [newComment, setNewComment] = useState("");
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const fetchUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            setUser(session?.user || null);
        };
        fetchUser();
    }, []);

    useEffect(() => {
        const fetchResult = async () => {
            try {
                const apiBase = getApiBase();
                const { data: { session } } = await supabase.auth.getSession();
                const user_id = session?.user?.id;

                // Fetch basic result
                const response = await fetch(`${apiBase}/result/${id}${user_id ? `?user_id=${user_id}` : ''}`);
                if (!response.ok) throw new Error(t("result.fetchError"));
                const data = await response.json();

                if (data.status === "completed") {
                    setResult(data);
                    setViewCount(data.view_count || 0);
                    setLikeCount(data.interaction_count || 0);
                    setIsLiked(data.is_liked || false);

                    // Trigger view increment
                    fetch(`${apiBase}/result/${id}/view`, { method: 'POST' });

                    // Fetch comments
                    const commRes = await fetch(`${apiBase}/result/${id}/comments`);
                    if (commRes.ok) {
                        const commData = await commRes.json();
                        setComments(commData);
                    }
                } else if (data.status === "failed") {
                    setError(data.detail || t("result.processFailed"));
                } else {
                    setError(t("result.generating"));
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

    const handleAudioLoadedMetadata = () => {
        if (audioRef.current && audioRef.current.duration > 0) {
            setVideoDuration(audioRef.current.duration);
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
        const dur = event.target.getDuration();
        if (dur > 0) setVideoDuration(dur);
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
        if (!user) {
            window.location.href = "/login";
            return;
        }

        const newStatus = !isLiked;
        setIsLiked(newStatus);
        setLikeCount(l => newStatus ? l + 1 : l - 1);

        try {
            const apiBase = getApiBase();
            const response = await fetch(`${apiBase}/like`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_id: id, user_id: user.id })
            });
            const data = await response.json();
            if (data.status !== "success") {
                // Rollback if failed
                setIsLiked(!newStatus);
                setLikeCount(l => !newStatus ? l + 1 : l - 1);
            }
        } catch (err) {
            // Rollback if error
            setIsLiked(!newStatus);
            setLikeCount(l => !newStatus ? l + 1 : l - 1);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error || !result) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
                <h1 className="text-2xl font-bold mb-4">{t("result.errorTitle")}</h1>
                <p className="text-slate-500 dark:text-slate-400 mb-8">{error || t("result.notFound")}</p>
                <Link href="/" className="px-6 py-2 bg-indigo-500 rounded-xl font-bold text-white">{t("result.backButton")}</Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground font-sans">
            {/* Top Navigation Bar */}
            <nav className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-card-border px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-6">
                    <Link href="/" className="p-2 hover:bg-card-bg rounded-xl transition-colors">
                        <ArrowLeft className="w-5 h-5 text-slate-400 hover:text-foreground" />
                    </Link>
                    <Link href="/?noredirect=1" className="flex items-center space-x-3 cursor-pointer group">
                        <div className="p-1.5 bg-card-bg border border-card-border rounded-lg group-hover:border-indigo-500/50 transition-colors">
                            <img src="/icon.png" alt="Logo" className="w-4 h-4" />
                        </div>
                        <span className="text-sm font-bold truncate max-w-[200px] md:max-w-md">{result.title}</span>
                    </Link>
                </div>

                <div className="flex items-center space-x-3">
                    <LanguageSwitcher />
                    <button
                        onClick={toggleTheme}
                        className="p-2 bg-card-bg border border-card-border rounded-xl text-slate-400 hover:text-foreground transition-all shadow-lg hidden sm:block"
                        title={theme === 'dark' ? "Light Mode" : "Dark Mode"}
                    >
                        {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </button>
                    <button className="flex items-center space-x-2 px-4 py-2 bg-card-bg border border-card-border hover:border-indigo-500/50 rounded-xl text-xs font-bold transition-all text-slate-400 hover:text-foreground">
                        <Share2 className="w-4 h-4" />
                        <span className="hidden sm:inline">{t("result.shareReport")}</span>
                    </button>
                    <button className="p-2 bg-indigo-500 text-white rounded-full hover:scale-105 transition-all shadow-lg shadow-indigo-500/20 active:scale-95 md:hidden">
                        <Download className="w-5 h-5" />
                    </button>
                </div>
            </nav>

            <main className="max-w-[1440px] mx-auto px-6 py-6 flex flex-col gap-6 h-[calc(100vh-5rem)] overflow-y-auto no-scrollbar">

                {/* Top Section: Video (1/3) */}
                <div className="w-full flex-shrink-0 h-[33vh] min-h-[250px] relative bg-black rounded-2xl md:rounded-[2.5rem] overflow-hidden shadow-2xl border border-card-border/10 ring-1 ring-card-border/5 group transition-all duration-300">
                    <div className="relative w-full h-full group">
                        {useLocalAudio ? (
                            <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900 group">
                                <img
                                    src={result.thumbnail?.startsWith('http') ? result.thumbnail : `${getApiBase()}/media/${result.thumbnail}`}
                                    alt="Thumbnail"
                                    className="absolute inset-0 w-full h-full object-cover opacity-20 blur-sm"
                                />
                                <div className="relative z-10 p-8 flex flex-col items-center text-center">
                                    <div className="w-20 h-20 bg-indigo-500 rounded-full flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/50">
                                        <Play className="w-8 h-8 text-white fill-current" />
                                    </div>
                                    <h4 className="text-xl font-bold mb-2">{t("result.localAudioTitle")}</h4>
                                    <p className="text-sm text-slate-400 max-w-xs">{t("result.localAudioDesc")}</p>
                                </div>
                                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-md px-10">
                                    <audio
                                        ref={audioRef}
                                        src={`${getApiBase()}/media/${result.media_path}`}
                                        controls
                                        onTimeUpdate={handleLocalTimeUpdate}
                                        onLoadedMetadata={handleAudioLoadedMetadata}
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
                                        origin: typeof window !== 'undefined' ? window.location.origin : '',
                                        modestbranding: 1,
                                        rel: 0,
                                    },
                                }}
                            />
                        )}
                        <button
                            onClick={() => setUseLocalAudio(!useLocalAudio)}
                            className="absolute top-4 md:top-6 right-4 md:right-6 z-20 px-3 md:px-4 py-1.5 md:py-2 bg-black/60 backdrop-blur-md border border-white/10 rounded-xl text-[9px] md:text-[10px] font-black uppercase tracking-widest text-white hover:bg-indigo-500 transition-all shadow-xl"
                        >
                            {useLocalAudio ? (
                                <span className="flex items-center gap-2"><Play className="w-3 h-3" /> YouTube</span>
                            ) : (
                                <span className="flex items-center gap-2"><ArrowDownToLine className="w-3 h-3" /> {t("result.syncAudio")}</span>
                            )}
                        </button>

                    </div>
                </div>

                {/* Summary Timeline Bar */}
                {result.summary && videoDuration > 0 && (() => {
                    const COLORS = ['#E69F00','#56B4E9','#009E73','#F0E442','#0072B2','#D55E00','#CC79A7'];
                    const items = result.summary.split('\n').filter(Boolean).map(line => {
                        const m = line.match(/\[(\d{2}):(\d{2})(?::(\d{2}))?\]$/);
                        let startTime = 0;
                        if (m) {
                            const h = m[3] ? parseInt(m[1]) : 0;
                            const min = m[3] ? parseInt(m[2]) : parseInt(m[1]);
                            const s = m[3] ? parseInt(m[3]) : parseInt(m[2]);
                            startTime = h * 3600 + min * 60 + s;
                        }
                        const text = line.replace(/^\d+\.\s*/, '').replace(/\[\d{2}:\d{2}(?::\d{2})?\]$/, '').trim();
                        return { text, startTime };
                    });
                    const segments = items.map((item, i) => {
                        const end = i < items.length - 1 ? items[i + 1].startTime - 1 : videoDuration;
                        const width = Math.max(((end - item.startTime) / videoDuration) * 100, 1);
                        return { ...item, end, width, color: COLORS[i % COLORS.length] };
                    });
                    let activeIdx = -1;
                    for (let i = segments.length - 1; i >= 0; i--) {
                        if (currentTime >= segments[i].startTime) { activeIdx = i; break; }
                    }
                    return (
                        <div className="w-full flex-shrink-0 flex gap-0.5 h-[7px] rounded-full overflow-hidden">
                            {segments.map((seg, i) => (
                                <div
                                    key={i}
                                    title={seg.text}
                                    onClick={() => seekTo(seg.startTime)}
                                    style={{
                                        width: `${seg.width}%`,
                                        backgroundColor: seg.color,
                                        opacity: activeIdx === i ? 1 : 0.35,
                                        transition: 'opacity 0.3s'
                                    }}
                                    className="cursor-pointer hover:opacity-80"
                                />
                            ))}
                        </div>
                    );
                })()}

                {/* Middle Section: Title & Stats (1/6) */}
                <div className="w-full flex-shrink-0 min-h-[140px] flex flex-col justify-center gap-3">
                    <h2 className="text-xl md:text-2xl font-black tracking-tight line-clamp-2 leading-tight px-1">{result.title}</h2>

                    {/* Stats & Actions Row */}
                    <div className="flex flex-wrap items-center justify-between gap-4 w-full">
                        {/* Left side: Stats & Heatmap */}
                        <div className="flex flex-wrap items-center gap-4 text-[9px] md:text-xs font-black text-slate-600 uppercase tracking-widest px-1">
                            <span>{viewCount.toLocaleString()} {t("result.views")}</span>
                            <span>{t("result.date")}: {(() => {
                                const date = result.mtime ? new Date(result.mtime) : new Date();
                                return date.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
                                    year: 'numeric', month: '2-digit', day: '2-digit'
                                }).replace(/\//g, '.');
                            })()}</span>

                            {/* Heatmap as 1 line tall after date */}
                            <div className="flex items-center gap-2 flex-1 max-w-[250px] ml-1 md:ml-4 bg-card-bg/50 px-3 py-1.5 rounded-full border border-card-border/50 shadow-inner">
                                <span className="shrink-0 text-[8px] md:text-[10px] text-indigo-500">{t("result.keyInterest")}:</span>
                                <div className="flex-1 h-1.5 bg-background border border-card-border rounded-full overflow-hidden flex">
                                    <div className="h-full bg-indigo-500" style={{ width: '45%' }}></div>
                                    <div className="h-full bg-indigo-600 opacity-50" style={{ width: '20%' }}></div>
                                    <div className="h-full bg-indigo-400" style={{ width: '35%' }}></div>
                                </div>
                            </div>
                        </div>

                        {/* Right side: Action Bar */}
                        <div className="flex items-center gap-3 py-1.5 px-3 bg-card-bg/50 border border-card-border rounded-2xl md:rounded-full backdrop-blur-sm">
                            <div className="flex items-center space-x-1.5 md:space-x-2">
                                <button
                                    onClick={copyFullText}
                                    className="px-3 md:px-4 py-1.5 bg-background border border-card-border rounded-xl text-[10px] md:text-xs font-black text-foreground hover:bg-indigo-500 hover:border-indigo-500 hover:text-white transition-all flex items-center space-x-1.5 md:space-x-2 group"
                                >
                                    {copyStatus ? <Check className="w-3.5 h-3.5 md:w-4 h-4 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 md:w-4 h-4 text-slate-400 group-hover:text-white" />}
                                    <span>{copyStatus ? t("result.copied") : t("result.copyFullText")}</span>
                                </button>
                                <button
                                    onClick={downloadSRT}
                                    className="px-3 md:px-4 py-1.5 bg-background border border-card-border rounded-xl text-[10px] md:text-xs font-black text-foreground hover:bg-indigo-500 hover:border-indigo-500 hover:text-white transition-all flex items-center space-x-1.5 md:space-x-2 group"
                                >
                                    <Download className="w-3.5 h-3.5 md:w-4 h-4 text-slate-400 group-hover:text-white" />
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
                                    className="px-3 md:px-4 py-1.5 bg-background border border-card-border rounded-xl text-[10px] md:text-xs font-black text-foreground hover:bg-indigo-500 hover:border-indigo-500 hover:text-white transition-all flex items-center space-x-1.5 md:space-x-2 group hidden sm:flex"
                                >
                                    <Download className="w-3.5 h-3.5 md:w-4 h-4 text-slate-400 group-hover:text-white" />
                                    <span>TXT</span>
                                </button>
                            </div>
                            <div className="h-4 w-px bg-card-border hidden md:block"></div>
                            <div>
                                <button
                                    onClick={handleToggleLike}
                                    className={cn(
                                        "px-3 md:px-4 py-1.5 border rounded-xl text-[10px] md:text-xs font-black transition-all flex items-center space-x-1.5 md:space-x-2 shadow-sm",
                                        isLiked ? "bg-rose-500 border-rose-500 text-white" : "bg-background border-card-border text-foreground hover:bg-rose-500 hover:border-rose-500 hover:text-white"
                                    )}
                                >
                                    <Heart className={cn("w-3.5 h-3.5 md:w-4 h-4", isLiked && "fill-current")} />
                                    <span>{likeCount}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Section: Transcript & Summary (1/2) */}
                <div className="relative w-full flex-shrink-0 h-[50vh] min-h-[400px]">
                    <div
                        ref={subtitleContainerRef}
                        onScroll={handleManualScroll}
                        data-testid="subtitle-container"
                        className="w-full h-full bg-card-bg/30 border border-card-border rounded-[2.5rem] p-6 md:p-8 overflow-y-auto no-scrollbar scroll-smooth shadow-inner relative"
                    >
                        <div className="absolute top-8 right-8 text-[80px] md:text-[120px] font-black text-foreground/[0.02] pointer-events-none select-none italic">
                            TLDW
                        </div>

                        <div className="space-y-8 md:space-y-12 relative z-10">
                            {/* AI Summary Section */}
                            {result.summary && (
                                <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-3xl p-6 md:p-8 mb-8 md:mb-12 shadow-sm">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="p-2 bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/20">
                                            <Send className="w-4 h-4 text-white transform -rotate-45" />
                                        </div>
                                        <h3 className="text-lg font-black text-indigo-500 dark:text-indigo-400 uppercase tracking-wider">{t("result.aiSummary")}</h3>
                                    </div>
                                    <div className="text-foreground/90 text-sm md:text-base leading-relaxed mb-6 font-medium whitespace-pre-wrap">
                                        {result.summary.split(/(\[\d{2}:\d{2}(?::\d{2})?\])/g).map((part, index) => {
                                            const timeMatch = part.match(/^\[(\d{2}):(\d{2})(?::(\d{2}))?\]$/);
                                            if (timeMatch) {
                                                const h = timeMatch[3] ? parseInt(timeMatch[1], 10) : 0;
                                                const m = timeMatch[3] ? parseInt(timeMatch[2], 10) : parseInt(timeMatch[1], 10);
                                                const s = timeMatch[3] ? parseInt(timeMatch[3], 10) : parseInt(timeMatch[2], 10);
                                                const totalSeconds = (h * 3600) + (m * 60) + s;
                                                return (
                                                    <span
                                                        key={index}
                                                        onClick={() => seekTo(totalSeconds)}
                                                        className="cursor-pointer text-indigo-500 font-bold hover:underline transition-colors px-1"
                                                    >
                                                        {part}
                                                    </span>
                                                );
                                            }
                                            return <span key={index}>{part}</span>;
                                        })}
                                    </div>
                                    {result.keywords && result.keywords.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            {result.keywords.map((tag, i) => (
                                                <span key={i} className="px-3 py-1 bg-background border border-card-border rounded-full text-[10px] font-black text-slate-500 uppercase tracking-widest hover:border-indigo-500/50 hover:text-indigo-500 transition-colors shadow-sm">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

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
                                                        isCurrent ? "text-indigo-500 dark:text-indigo-400 bg-indigo-500/10" : "hover:text-foreground hover:bg-foreground/5"
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

                            <div className="pt-8 border-t border-card-border flex items-center justify-between">
                                <p className="text-xs font-bold text-slate-600 uppercase tracking-widest leading-relaxed">
                                    {t("result.usageCost")}: ${result.usage?.total_cost || "0.01"} <br />
                                    {t("result.aiModel")}: Claude 3.5 Sonnet
                                </p>
                            </div>
                        </div>
                    </div>
                    {/* Resume Follow Button */}
                    {isAutoScrollPaused && (
                        <div className="fixed bottom-6 md:bottom-10 right-6 md:right-10 z-[60] animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <button
                                onClick={resumeAutoScroll}
                                className="flex items-center space-x-2 px-5 md:px-6 py-2.5 md:py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-2xl shadow-indigo-500/50 transition-all transform hover:scale-105 active:scale-95 font-black text-xs md:text-sm"
                            >
                                <ArrowDownToLine className="w-4 h-4 md:w-5 h-5" />
                                <span>{t("result.syncProgress")}</span>
                            </button>
                        </div>
                    )}
                </div>

                {/* Discussion Panel Moved to Bottom */}
                <div className="w-full mt-4 flex-shrink-0 pb-12">
                    {/* Discussion Section */}
                    <div className="bg-card-bg/40 border border-card-border rounded-[2.5rem] flex flex-col h-[600px] shadow-sm">
                        <div className="p-8 border-b border-card-border flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <MessageSquare className="w-5 h-5 text-indigo-500" />
                                <h3 className="font-bold">{t("result.discussion")} ({comments.length})</h3>
                            </div>
                            <MoreVertical className="w-5 h-5 text-slate-400 cursor-pointer" />
                        </div>

                        <div className="flex-grow overflow-y-auto p-8 space-y-8 no-scrollbar">
                            {comments.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
                                    <MessageSquare className="w-8 h-8 opacity-20" />
                                    <p className="text-sm">{t("result.noComments")}</p>
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
                                            <span className="text-sm font-bold text-foreground">{comment.profiles?.username || t("result.anonymousUser")}</span>
                                            <span className="text-[10px] text-slate-500 dark:text-slate-600 font-bold uppercase tracking-widest">
                                                {new Date(comment.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{comment.content}</p>
                                        <div className="flex items-center gap-4 pt-1">
                                            <button className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 hover:text-indigo-400 transition-colors">
                                                <ThumbsUp className="w-3 h-3" /> {comment.likes_count || 0}
                                            </button>
                                            <button className="text-[10px] font-bold text-slate-500 hover:text-white transition-colors">{t("result.reply")}</button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="p-6 border-t border-card-border bg-card-bg/50">
                            <form onSubmit={async (e) => {
                                e.preventDefault();
                                if (!newComment.trim()) return;
                                try {
                                    const apiBase = getApiBase();
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
                                    placeholder={t("result.commentPlaceholder")}
                                    className="w-full bg-background border border-card-border rounded-2xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-500 transition-all font-medium"
                                />
                                <button type="submit" className="absolute right-2 top-2 p-1.5 bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition-colors">
                                    <Send className="w-4 h-4" />
                                </button>
                            </form>
                        </div>
                    </div>

                </div>
            </main >
        </div >
    );
}
