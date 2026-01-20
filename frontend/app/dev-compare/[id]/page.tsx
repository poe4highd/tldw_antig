"use client";

import React, { useState, useRef, useEffect, use } from "react";
import Link from "next/link";
import YouTube, { YouTubeProps } from 'react-youtube';
import { getApiBase } from "@/utils/api";

import {
    ArrowLeft,
    Play,
    ArrowDownToLine,
    ShieldCheck,
    Lock,
    KeyRound,
    AlertCircle,
    Save,
    Download,
    CheckCircle2
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// Types
interface RawSubtitle {
    start: number;
    end: number;
    text: string;
}

interface CompareResult {
    title: string;
    youtube_id?: string;
    media_path?: string;
    thumbnail?: string;
    models: {
        [key: string]: RawSubtitle[];
    };
}

export default function DevComparePage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [result, setResult] = useState<CompareResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Auth State
    const [isAuthorized, setIsAuthorized] = useState(false);
    const [passwordInput, setPasswordInput] = useState("");
    const [authError, setAuthError] = useState(false);

    const playerRef = useRef<any>(null);
    const [isPlayerReady, setIsPlayerReady] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [useLocalAudio, setUseLocalAudio] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false);
    const subtitleContainerRef = useRef<HTMLDivElement>(null);
    const isProgrammaticScroll = useRef(false);

    // Editor State
    const [editedSubtitles, setEditedSubtitles] = useState<RawSubtitle[]>([]);
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const [showSaveToast, setShowSaveToast] = useState(false);

    // Check Local Storage on mount
    useEffect(() => {
        const storedPass = localStorage.getItem("dev_password");
        const devPass = process.env.NEXT_PUBLIC_DEV_PASSWORD || "speedup2026";
        if (storedPass === devPass) {
            setIsAuthorized(true);
        } else {
            setLoading(false); // Show login form
        }
    }, []);

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        const devPass = process.env.NEXT_PUBLIC_DEV_PASSWORD || "speedup2026";
        if (passwordInput === devPass) {
            localStorage.setItem("dev_password", passwordInput);
            setIsAuthorized(true);
            setAuthError(false);
        } else {
            setAuthError(true);
        }
    };

    // Fetch Data
    useEffect(() => {
        if (!isAuthorized) return;
        setLoading(true);

        const fetchCompareData = async () => {
            try {
                const apiBase = getApiBase();
                const response = await fetch(`${apiBase}/dev/compare/${id}`);
                if (!response.ok) throw new Error("无法获取对比数据");
                const data = await response.json();
                setResult(data);

                // Initialize Editor
                const saved = localStorage.getItem(`dev_edit_${id}`);
                if (saved) {
                    setEditedSubtitles(JSON.parse(saved));
                } else {
                    // Try to use turbo/large-v3-turbo as initial value
                    const turboKey = ["large-v3-turbo", "turbo", "medium"].find(k => data.models[k]);
                    const benchmarkKey = data.models["reference"] ? "reference" : (turboKey || Object.keys(data.models)[0]);

                    // We map the edited lines to the benchmark segments
                    const initial = data.models[benchmarkKey].map((s: any) => {
                        // Find overlapping turbo text
                        let initialText = "";
                        if (turboKey && data.models[turboKey]) {
                            initialText = data.models[turboKey]
                                .filter((c: any) => Math.min(s.end, c.end) > Math.max(s.start, c.start))
                                .map((o: any) => o.text).join(" ");
                        } else {
                            initialText = s.text;
                        }
                        return { ...s, text: initialText };
                    });
                    setEditedSubtitles(initial);
                }
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchCompareData();
    }, [id, isAuthorized]);

    const handleEditSubtitle = (index: number, newText: string) => {
        const updated = [...editedSubtitles];
        updated[index].text = newText;
        setEditedSubtitles(updated);
        setHasUnsavedChanges(true);
    };

    const saveToLocal = () => {
        localStorage.setItem(`dev_edit_${id}`, JSON.stringify(editedSubtitles));
        setHasUnsavedChanges(false);
        setShowSaveToast(true);
        setTimeout(() => setShowSaveToast(false), 2000);
    };

    const downloadSRT = () => {
        const srtContent = editedSubtitles.map((s, i) => {
            const formatTime = (sec: number) => {
                const date = new Date(0);
                date.setSeconds(sec);
                const ms = (sec % 1).toFixed(3).substring(2);
                return date.toISOString().substring(11, 19) + "," + ms;
            };
            return `${i + 1}\n${formatTime(s.start)} --> ${formatTime(s.end)}\n${s.text}\n`;
        }).join("\n");

        const blob = new Blob([srtContent], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `corrected_${id}.srt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Playback Sync
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (!useLocalAudio && isPlayerReady && playerRef.current) {
            interval = setInterval(() => {
                if (playerRef.current && typeof playerRef.current.getCurrentTime === 'function') {
                    const time = playerRef.current.getCurrentTime();
                    if (typeof time === 'number') {
                        setCurrentTime(time);
                    }
                }
            }, 200);
        }
        return () => clearInterval(interval);
    }, [useLocalAudio, isPlayerReady]);

    const handleLocalTimeUpdate = () => {
        if (audioRef.current) setCurrentTime(audioRef.current.currentTime);
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

    // Data Alignment Logic
    // Fixed Order as requested: L1 reference -> L2 turbo -> L3 sensevoice
    const getModelKey = (possibleKeys: string[]) => {
        if (!result) return null;
        return possibleKeys.find(k => result.models[k]) || null;
    };

    const benchmarkKey = result && result.models["reference"] ? "reference" : (getModelKey(["large-v3-turbo", "turbo"]) || (result ? Object.keys(result.models)[0] : ""));
    const benchmarkSubtitles = result && benchmarkKey ? result.models[benchmarkKey] : [];

    // L2: Turbo
    const model2Key = benchmarkKey === "reference" ? getModelKey(["large-v3-turbo", "turbo", "medium"]) : getModelKey(["sensevoice"]);

    // L3: SenseVoice
    const model3Key = benchmarkKey === "reference" ? (model2Key?.includes("turbo") || model2Key === "medium" ? getModelKey(["sensevoice"]) : getModelKey(["large-v3-turbo", "turbo"])) : Object.keys(result?.models || {}).find(k => k !== benchmarkKey && k !== model2Key);

    // Scrolling Sync
    const scrollToActive = (force = false) => {
        if (!result || !subtitleContainerRef.current) return;

        let activeIdx = -1;
        for (let i = 0; i < benchmarkSubtitles.length; i++) {
            const s = benchmarkSubtitles[i];
            const nextS = benchmarkSubtitles[i + 1];
            if (currentTime >= s.start && (nextS ? currentTime < nextS.start : true)) {
                activeIdx = i;
                break;
            }
        }

        if (activeIdx !== -1) {
            const container = subtitleContainerRef.current;
            const el = document.getElementById(`segment-${activeIdx}`);
            if (el) {
                const containerRect = container.getBoundingClientRect();
                const elRect = el.getBoundingClientRect();
                const offset = elRect.top - containerRect.top;
                const targetScroll = container.scrollTop + offset - (container.clientHeight / 2) + (el.clientHeight / 2);

                if (force || Math.abs(container.scrollTop - targetScroll) > 10) {
                    isProgrammaticScroll.current = true;
                    container.scrollTo({ top: targetScroll, behavior: 'smooth' });
                    setTimeout(() => { isProgrammaticScroll.current = false; }, 500);
                }
            }
        }
    };

    useEffect(() => {
        if (!isAutoScrollPaused) scrollToActive(false);
    }, [currentTime, isAutoScrollPaused, result]);

    // Render Auth Form
    if (!isAuthorized) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center font-sans">
                <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-[2.5rem] p-12 shadow-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-8 opacity-5">
                        <ShieldCheck className="w-32 h-32" />
                    </div>

                    <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-indigo-500/20">
                        <KeyRound className="w-8 h-8 text-indigo-400" />
                    </div>

                    <h1 className="text-2xl font-black mb-2 tracking-tight">开发者实验场</h1>
                    <p className="text-slate-500 text-sm mb-10 font-medium">请输入开发授权密码进入三路比较系统</p>

                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="relative">
                            <input
                                type="password"
                                value={passwordInput}
                                onChange={(e) => setPasswordInput(e.target.value)}
                                placeholder="ENTER PASSWORD"
                                className={cn(
                                    "w-full bg-slate-950 border rounded-2xl py-4 px-6 text-center text-sm font-black tracking-widest placeholder:text-slate-800 focus:outline-none transition-all",
                                    authError ? "border-red-500/50 ring-2 ring-red-500/10" : "border-slate-800 focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/5"
                                )}
                            />
                            {authError && (
                                <div className="absolute -bottom-6 left-0 right-0 flex items-center justify-center gap-1.5 text-red-500 text-[10px] font-black uppercase">
                                    <AlertCircle className="w-3 h-3" />
                                    <span>密码错误，请查阅环境变量</span>
                                </div>
                            )}
                        </div>
                        <button type="submit" className="w-full py-4 bg-indigo-500 hover:bg-indigo-600 rounded-2xl font-black text-sm tracking-widest shadow-xl shadow-indigo-500/20 active:scale-[0.98] transition-all">
                            UNLOCK SYSTEM
                        </button>
                    </form>

                    <div className="mt-12 pt-8 border-t border-slate-800 flex justify-center gap-6">
                        <div className="h-1 w-12 bg-slate-800 rounded-full" />
                        <div className="h-1 w-12 bg-slate-800 rounded-full" />
                        <div className="h-1 w-12 bg-slate-800 rounded-full" />
                    </div>
                </div>
            </div>
        );
    }

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
                <p className="text-slate-400 mb-8">{error || "找不到该报告数据"}</p>
                <Link href="/dashboard" className="px-6 py-2 bg-indigo-500 rounded-xl font-bold">返回主页</Link>
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
                    <div className="flex items-center space-x-3">
                        <ShieldCheck className="w-5 h-5 text-indigo-400" />
                        <span className="text-sm font-bold truncate max-w-[200px] md:max-w-md">
                            [三路对齐] {result.title}
                        </span>
                    </div>
                </div>
                <div className="flex items-center space-x-3">
                    {hasUnsavedChanges && (
                        <span className="text-[10px] font-black text-amber-500 bg-amber-500/10 px-2 py-1 rounded-full animate-pulse uppercase tracking-widest">
                            Unsaved Changes
                        </span>
                    )}
                    <button
                        onClick={saveToLocal}
                        className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-xl text-xs font-black transition-all"
                    >
                        <Save className="w-4 h-4" />
                        SAVE
                    </button>
                    <button
                        onClick={downloadSRT}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-xs font-black shadow-lg shadow-indigo-500/20 transition-all"
                    >
                        <Download className="w-4 h-4" />
                        EXPORT SRT
                    </button>
                </div>
            </nav>

            <main className="max-w-[1700px] mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-5rem)]">

                {/* Left Column: Video & Metadata */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                    <div className="aspect-video bg-black rounded-3xl overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 relative">
                        {useLocalAudio ? (
                            <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900 group">
                                <img
                                    src={result.thumbnail?.startsWith('http') ? result.thumbnail : `${getApiBase()}/media/${result.thumbnail}`}
                                    alt="Thumbnail"
                                    className="absolute inset-0 w-full h-full object-cover opacity-20 blur-sm"
                                />
                                <audio
                                    ref={audioRef}
                                    src={`${getApiBase()}/media/${result.media_path}`}
                                    controls
                                    onTimeUpdate={handleLocalTimeUpdate}
                                    className="relative z-10 w-[80%] h-10 accent-indigo-500"
                                />
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
                                    playerVars: { autoplay: 1, hl: 'zh-CN' },
                                }}
                            />
                        )}
                        <button
                            onClick={() => setUseLocalAudio(!useLocalAudio)}
                            className="absolute top-4 right-4 z-20 px-3 py-1.5 bg-black/60 backdrop-blur-md border border-white/10 rounded-xl text-[10px] font-black text-white hover:bg-indigo-500 transition-all"
                        >
                            {useLocalAudio ? "切换 YouTube" : "同步本地音频"}
                        </button>
                    </div>

                    <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 space-y-6 overflow-y-auto no-scrollbar">
                        <div>
                            <h3 className="text-indigo-400 text-[10px] font-black uppercase tracking-widest mb-3">当前对齐基准</h3>
                            <div className="flex items-center gap-3 bg-slate-950 p-4 rounded-2xl border border-indigo-500/20 shadow-inner">
                                <div className="w-2 h-2 rounded-full bg-indigo-500" />
                                <span className="font-mono text-sm font-bold">{benchmarkKey}</span>
                                {benchmarkKey === "reference" && <span className="text-[10px] bg-indigo-500 text-white px-1.5 py-0.5 rounded font-black">GROUND TRUTH</span>}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h3 className="text-slate-500 text-[10px] font-black uppercase tracking-widest">模型层级</h3>
                            <div className="space-y-2">
                                {[benchmarkKey, model2Key, model3Key].filter(Boolean).map((k, i) => (
                                    <div key={k} className="flex justify-between items-center text-xs p-3 bg-white/5 rounded-xl border border-white/5">
                                        <span className="font-mono text-slate-400">L{i + 1}: {k}</span>
                                        <div className={cn("w-1.5 h-1.5 rounded-full", i === 0 ? "bg-indigo-500" : i === 1 ? "bg-emerald-400" : "bg-orange-400")} />
                                    </div>
                                ))}
                            </div>
                        </div>

                        <p className="text-[11px] text-slate-500 leading-relaxed italic">
                            正在对齐：已自动识别 SRV1 文件作为地面真值。您可以编辑 L4 区域进行人工校对，修改将自动缓存并支持导出。
                        </p>
                    </div>
                </div>

                {/* Right Column: Comparison List */}
                <div className="lg:col-span-8 flex flex-col min-h-0 bg-slate-900/30 border border-slate-800 rounded-[2rem] overflow-hidden">
                    <div
                        ref={subtitleContainerRef}
                        onScroll={() => { if (!isProgrammaticScroll.current) setIsAutoScrollPaused(true); }}
                        className="flex-1 overflow-y-auto p-4 md:p-8 no-scrollbar scroll-smooth space-y-4"
                    >
                        {benchmarkSubtitles.map((s, idx) => {
                            const nextS = benchmarkSubtitles[idx + 1];
                            const isActive = currentTime >= s.start && (nextS ? currentTime < nextS.start : true);

                            // Find overlapping segments helper
                            const getOverlaps = (modelKey: string | null | undefined) => {
                                if (!modelKey || !result.models[modelKey]) return "";
                                return result.models[modelKey]
                                    .filter(c => Math.min(s.end, c.end) > Math.max(s.start, c.start))
                                    .map(o => o.text).join(" ");
                            };

                            const text2 = getOverlaps(model2Key);
                            const text3 = getOverlaps(model3Key);

                            return (
                                <div
                                    key={idx}
                                    id={`segment-${idx}`}
                                    onClick={() => seekTo(s.start)}
                                    className={cn(
                                        "group p-4 rounded-xl border transition-all duration-300 cursor-pointer",
                                        isActive ? "bg-indigo-500/10 border-indigo-500/30 ring-1 ring-indigo-500/20" : "bg-transparent border-transparent hover:bg-white/5"
                                    )}
                                >
                                    <div className="flex items-start gap-4">
                                        <button
                                            onClick={() => seekTo(s.start)}
                                            className="mt-1 flex-shrink-0 font-mono text-[10px] font-bold text-slate-600 group-hover:text-indigo-400 min-w-[50px] text-left"
                                        >
                                            {Math.floor(s.start / 60)}:{(s.start % 60).toFixed(1).padStart(4, '0')}
                                        </button>

                                        <div className="flex-1 min-w-0 space-y-3">
                                            {/* Line 1: Benchmark */}
                                            <div className={cn(
                                                "text-[15px] leading-relaxed font-bold transition-colors",
                                                isActive ? "text-indigo-100" : "text-white"
                                            )}>
                                                {s.text}
                                            </div>

                                            {/* Line 2: Second Model */}
                                            {model2Key && (
                                                <div className={cn(
                                                    "text-[13px] leading-relaxed flex gap-2 items-start opacity-90",
                                                    isActive ? "text-emerald-400" : "text-slate-400"
                                                )}>
                                                    <span className="text-[8px] uppercase tracking-tighter bg-white/5 px-1 rounded flex-shrink-0 mt-0.5 border border-white/5">{model2Key}</span>
                                                    <span>{text2 || <span className="italic opacity-30 text-[10px]">[EMPTY]</span>}</span>
                                                </div>
                                            )}

                                            {/* Line 3: Third Model */}
                                            {model3Key && (
                                                <div className={cn(
                                                    "text-[13px] leading-relaxed flex gap-2 items-start opacity-80",
                                                    isActive ? "text-orange-400" : "text-slate-500"
                                                )}>
                                                    <span className="text-[8px] uppercase tracking-tighter bg-white/5 px-1 rounded flex-shrink-0 mt-0.5 border border-white/5">{model3Key}</span>
                                                    <span>{text3 || <span className="italic opacity-30 text-[10px]">[EMPTY]</span>}</span>
                                                </div>
                                            )}
                                            {/* Line 4: Final Editor */}
                                            <div className="pt-2">
                                                <div className="flex items-center gap-2 mb-1.5">
                                                    <span className="text-[8px] font-black uppercase tracking-widest bg-indigo-500 text-white px-1.5 rounded-sm">L4: FINAL CONFIRM</span>
                                                </div>
                                                <textarea
                                                    value={editedSubtitles[idx]?.text || ""}
                                                    onChange={(e) => handleEditSubtitle(idx, e.target.value)}
                                                    rows={1}
                                                    className={cn(
                                                        "w-full bg-slate-950/50 border rounded-xl py-2 px-3 text-[14px] font-medium focus:outline-none transition-all resize-none overflow-hidden",
                                                        isActive ? "border-indigo-500/50 text-indigo-100" : "border-slate-800 text-slate-300 focus:border-indigo-500/30"
                                                    )}
                                                    onInput={(e) => {
                                                        const target = e.target as HTMLTextAreaElement;
                                                        target.style.height = 'auto';
                                                        target.style.height = target.scrollHeight + 'px';
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Resume Floating Button */}
                {isAutoScrollPaused && (
                    <button
                        onClick={() => { setIsAutoScrollPaused(false); setTimeout(() => scrollToActive(true), 0); }}
                        className="fixed bottom-10 right-10 z-[60] flex items-center space-x-3 px-8 py-4 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-2xl shadow-indigo-500/20 animate-in fade-in slide-in-from-bottom-4 transition-all active:scale-95"
                    >
                        <ArrowDownToLine className="w-5 h-5" />
                        <span className="font-black text-sm tracking-widest uppercase">Sync Timeline</span>
                    </button>
                )}
                {/* Save Toast */}
                {showSaveToast && (
                    <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 px-6 py-3 bg-emerald-500 text-white rounded-2xl shadow-2xl animate-in fade-in slide-in-from-bottom-5">
                        <CheckCircle2 className="w-5 h-5" />
                        <span className="font-black text-sm uppercase tracking-widest">Progress Saved</span>
                    </div>
                )}
            </main>
        </div>
    );
}
