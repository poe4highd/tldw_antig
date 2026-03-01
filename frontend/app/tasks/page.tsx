"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/utils/supabase";
import { Youtube, FileUp, ArrowRight, LayoutGrid, Clock, CheckCircle2, Menu, Sun, Moon, User, Share2, Lock } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { getApiBase } from "@/utils/api";
import { useTranslation } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { twMerge } from "tailwind-merge";
import { clsx, type ClassValue } from "clsx";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface HistoryItem {
    id: string;
    title: string;
    thumbnail: string;
    url: string;
    total_cost?: number;
}

interface Summary {
    total_duration: number;
    total_cost: number;
    video_count: number;
}

interface ActiveTask {
    id: string;
    status: string;
    progress: number;
}

export default function TasksPage() {
    const { t, language } = useTranslation();
    const { theme, toggleTheme } = useTheme();
    const [url, setUrl] = useState("");
    const [mode, setMode] = useState("local");
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [eta, setEta] = useState<number | null>(null);
    const [isPublic, setIsPublic] = useState(true);
    const [isFinished, setIsFinished] = useState(false);
    const [finishedTaskId, setFinishedTaskId] = useState<string | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
    const [summary, setSummary] = useState<Summary | null>(null);
    const [user, setUser] = useState<{
        id: string;
        email?: string;
        user_metadata?: {
            full_name?: string;
            avatar_url?: string;
        };
    } | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isBackendOnline, setIsBackendOnline] = useState(true);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();

    const fetchHistory = async () => {
        if (!user) return;
        try {
            const apiBase = getApiBase();
            const resp = await fetch(`${apiBase}/history?user_id=${user.id}`);
            const data = await resp.json();
            setHistory(data.items || []);
            setSummary(data.summary || null);
            setActiveTasks(data.active_tasks || []);
            setIsBackendOnline(true);
        } catch (e) {
            console.error("Failed to fetch history");
            setIsBackendOnline(false);
        }
    };

    const startProcess = async () => {
        if (!url) return;
        setStatus(t("tasks.statusInit"));
        setProgress(0);
        setEta(null);
        setIsFinished(false);
        setFinishedTaskId(null);
        try {
            const apiBase = getApiBase();
            const resp = await fetch(`${apiBase}/process`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, mode, user_id: user?.id, is_public: isPublic }),
            });

            if (!resp.ok) {
                const errorData = await resp.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${resp.status}`);
            }

            const data = await resp.json();
            pollStatus(data.task_id);
        } catch (e: unknown) {
            console.error("Start process failed:", e);
            const message = e instanceof Error ? e.message : t("tasks.statusNetworkError");
            setStatus(`${t("tasks.statusStartFailed")}: ${message}`);
        }
    };

    const onFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setStatus(t("tasks.statusUploading"));
        setProgress(0);
        setEta(null);
        setIsFinished(false);
        setFinishedTaskId(null);

        const formData = new FormData();
        formData.append("file", file);
        formData.append("mode", mode);
        if (user) formData.append("user_id", user.id);
        formData.append("is_public", isPublic.toString());

        try {
            const apiBase = getApiBase();
            const resp = await fetch(`${apiBase}/upload`, {
                method: "POST",
                body: formData,
            });
            const data = await resp.json();
            pollStatus(data.task_id);
        } catch (err) {
            setStatus(t("tasks.statusUploadFailed"));
        }
    };

    const pollStatus = (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const apiBase = getApiBase();
                const resp = await fetch(`${apiBase}/result/${taskId}`);
                const data = await resp.json();
                setProgress(data.progress || 0);
                if (data.eta !== undefined) setEta(data.eta);

                if (data.status === "completed") {
                    clearInterval(interval);
                    setProgress(100);
                    setStatus(t("tasks.statusCompleted"));
                    setIsFinished(true);
                    setFinishedTaskId(taskId);
                } else if (data.status === "failed") {
                    setProgress(0);
                    setStatus("Failed: " + (data.detail || "Unknown error"));
                    clearInterval(interval);
                } else {
                    const statusMap: Record<string, string> = {
                        scheduling_download: t("tasks.statusSchedulingDownload"),
                        downloading: t("tasks.statusDownloading"),
                        extracting_audio: t("tasks.statusExtractingAudio"),
                        loading_cache: t("tasks.statusLoadingCache"),
                        importing_subtitles: t("tasks.statusImportingSubtitles"),
                        transcribing_cloud: t("tasks.statusTranscribingCloud"),
                        transcribing_local: t("tasks.statusTranscribingLocal"),
                        llm_processing: t("tasks.statusLlmProcessing"),
                    };
                    const raw = data.status || "";
                    setStatus(statusMap[raw] || raw || t("tasks.statusProcessing"));
                }
            } catch (e) {
                setStatus(t("tasks.statusConnectionLost"));
            }
        }, 2000);
    };

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/");
    };

    useEffect(() => {
        const checkUser = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.push("/login?redirect=/tasks");
                return;
            }
            setUser(session.user);
            setIsLoading(false);
        };

        checkUser();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!session) {
                router.push("/login?redirect=/tasks");
            } else {
                setUser(session.user);
            }
        });

        return () => subscription.unsubscribe();
    }, [router]);

    useEffect(() => {
        if (!user?.id) return;

        fetchHistory();
        const interval = setInterval(() => fetchHistory(), 15000);
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.id]);

    useEffect(() => {
        if (eta !== null && eta > 0) {
            const timer = setTimeout(() => setEta(eta - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [eta]);

    if (isLoading) {
        return (
            <main className="min-h-screen bg-background flex items-center justify-center">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="w-12 h-12 bg-card-bg border border-card-border rounded-full mb-4"></div>
                    <p className="text-slate-500 font-medium">{t("tasks.verifyingIdentity")}</p>
                </div>
            </main>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground flex font-sans transition-colors duration-300">
            <Sidebar
                user={user}
                onSignOut={handleSignOut}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            <main className="flex-grow min-w-0 bg-transparent text-foreground font-sans pb-20 relative">
                {/* Background Glows */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
                    <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
                </div>
                {/* Header: Logo & Controls (Sticky) */}
                <div className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-card-border -mx-4 px-4 md:-mx-10 md:px-10 pb-2 pt-3 md:pt-4 mb-8">
                    <div className="flex items-center justify-between gap-4">
                        <Link href="/" className="flex items-center space-x-2 md:space-x-3 group shrink-0">
                            <div className={cn(
                                "p-1.5 border rounded-lg group-hover:border-indigo-500/50 transition-all duration-300 shadow-xl",
                                theme === 'dark' ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"
                            )}>
                                <img src="/icon.png" alt="Logo" className="w-5 h-5" />
                            </div>
                            <span className={cn(
                                "text-lg md:text-xl font-black tracking-tighter",
                                theme === 'dark' ? "bg-gradient-to-r from-foreground to-slate-400 bg-clip-text text-transparent" : "text-indigo-600"
                            )}>
                                {t("marketing.title")}
                            </span>
                        </Link>

                        <div className="flex items-center gap-1.5 md:gap-3">
                            <LanguageSwitcher />
                            <button
                                onClick={toggleTheme}
                                className="p-2 bg-card-bg/50 backdrop-blur-md border border-card-border rounded-xl text-slate-400 hover:text-foreground transition-all shadow-lg"
                            >
                                {theme === 'dark' ? <Sun className="w-4 h-4 md:w-5 md:h-5" /> : <Moon className="w-4 h-4 md:w-5 md:h-5" />}
                            </button>
                            <Link
                                href={user ? "/dashboard" : "/login"}
                                className="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs md:text-sm transition-all shadow-lg active:scale-[0.98]"
                            >
                                <User className="w-3.5 h-3.5 md:w-4 md:h-4" />
                                <span className="hidden sm:inline">{user ? "Profile" : t("login.title")}</span>
                            </Link>
                            <button
                                onClick={() => setIsSidebarOpen(true)}
                                className="p-2 md:hidden text-slate-400 hover:text-foreground"
                            >
                                <Menu className="w-6 h-6" />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="max-w-6xl mx-auto px-4 md:px-6">
                    <header className="mb-12 flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                        <div>
                            <h1 className={cn(
                                "text-3xl md:text-4xl font-black tracking-tight mb-1",
                                theme === 'dark' ? "bg-gradient-to-r from-foreground via-foreground to-slate-500 bg-clip-text text-transparent" : "text-indigo-900"
                            )}>
                                {t("tasks.title")}
                            </h1>
                            <p className="text-slate-500 font-medium">{t("tasks.subtitle")}</p>
                        </div>
                        <Link href="/dashboard" className="text-indigo-500 hover:text-indigo-400 transition-colors text-sm font-bold uppercase tracking-widest flex items-center gap-2 group">
                            {t("tasks.backToBookshelf")} <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </Link>
                    </header>

                    {!isBackendOnline && (
                        <div className="mb-8 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center gap-4 animate-in fade-in slide-in-from-top-2 duration-500">
                            <div className="w-10 h-10 bg-amber-500/20 rounded-xl flex items-center justify-center text-amber-500 shrink-0">
                                <Clock className="w-6 h-6" />
                            </div>
                            <p className="text-amber-200/80 font-bold text-sm">
                                {t("common.offlineNotice")}
                            </p>
                        </div>
                    )}

                    {/* Input Section */}
                    <div className="bg-card-bg/50 backdrop-blur-xl border border-card-border p-5 sm:p-8 rounded-3xl sm:rounded-[2.5rem] shadow-2xl mb-12 max-w-4xl mx-auto ring-1 ring-white/5 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-5 text-foreground">
                            <LayoutGrid className="w-40 h-40" />
                        </div>

                        <div className="relative z-10 space-y-8">
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] ml-2">{t("tasks.submitNew")}</label>
                                {/* URL input row */}
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                                        <Youtube className="w-5 h-5" />
                                    </div>
                                    <input
                                        type="text"
                                        placeholder={t("tasks.placeholder")}
                                        className="w-full bg-background border border-card-border rounded-2xl pl-14 pr-5 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all text-base placeholder:text-slate-500 text-foreground shadow-inner"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                    />
                                </div>
                                {/* Controls row: mode select + process button */}
                                <div className="flex flex-col sm:flex-row gap-3">
                                    <select
                                        className="bg-background border border-card-border rounded-2xl px-5 py-3.5 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-foreground font-bold cursor-pointer shadow-inner text-sm sm:w-auto"
                                        value={mode}
                                        onChange={(e) => setMode(e.target.value)}
                                    >
                                        <option value="cloud" disabled>
                                            {t("tasks.cloudInferenceDev")}
                                        </option>
                                        <option value="local">{t("tasks.modeLocal")}</option>
                                    </select>
                                    <button
                                        onClick={startProcess}
                                        disabled={!url || !isBackendOnline || (!!status && !status.includes("Failed"))}
                                        className="flex-1 sm:flex-none bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all px-8 py-3.5 rounded-2xl font-black text-white shadow-xl shadow-indigo-500/20 active:scale-[0.98] whitespace-nowrap text-sm"
                                    >
                                        {t("tasks.processNow")}
                                    </button>
                                </div>
                                <div className="flex items-center gap-3 px-0 sm:px-2">
                                    <button
                                        onClick={() => setIsPublic(true)}
                                        className={cn(
                                            "flex-1 flex items-center justify-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-xl sm:rounded-2xl border transition-all duration-300",
                                            isPublic
                                                ? "bg-emerald-500/10 border-emerald-500/50 text-emerald-400 shadow-lg shadow-emerald-500/5"
                                                : "bg-background/50 border-card-border text-slate-500 hover:border-card-border/80"
                                        )}
                                    >
                                        <Share2 className={cn("w-4 h-4 sm:w-5 sm:h-5 shrink-0", isPublic && "animate-pulse")} />
                                        <div className="text-left min-w-0">
                                            <p className="text-[11px] sm:text-xs font-black uppercase tracking-tight">{t("tasks.public")}</p>
                                            <p className="text-[9px] opacity-60 font-medium hidden sm:block">{t("tasks.publicDesc")}</p>
                                        </div>
                                    </button>
                                    <button
                                        onClick={() => setIsPublic(false)}
                                        className={cn(
                                            "flex-1 flex items-center justify-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-xl sm:rounded-2xl border transition-all duration-300",
                                            !isPublic
                                                ? "bg-amber-500/10 border-amber-500/50 text-amber-400 shadow-lg shadow-amber-500/5"
                                                : "bg-background/50 border-card-border text-slate-500 hover:border-card-border/80"
                                        )}
                                    >
                                        <Lock className="w-4 h-4 sm:w-5 sm:h-5 shrink-0" />
                                        <div className="text-left min-w-0">
                                            <p className="text-[11px] sm:text-xs font-black uppercase tracking-tight">{t("tasks.private")}</p>
                                            <p className="text-[9px] opacity-60 font-medium hidden sm:block">{t("tasks.privateDesc")}</p>
                                        </div>
                                    </button>
                                </div>
                            </div>

                            <div className="flex items-center gap-4 px-2">
                                <div className="h-px flex-1 bg-card-border/50"></div>
                                <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">{t("tasks.orUpload")}</span>
                                <div className="h-px flex-1 bg-card-border/50"></div>
                            </div>

                            <div className="flex justify-center">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex items-center gap-3 px-8 py-4 bg-card-bg/50 hover:bg-card-bg/80 border border-card-border rounded-2xl text-slate-500 transition-all group hover:text-foreground"
                                >
                                    <FileUp className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                    <span className="font-bold">{t("tasks.uploadButton")}</span>
                                </button>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    accept="audio/*,video/*"
                                    onChange={onFileUpload}
                                />
                            </div>
                        </div>

                        {status && (
                            <div className="mt-12 pt-10 border-t border-card-border/50 space-y-6 animate-in fade-in slide-in-from-top-4 duration-1000">
                                <div className="flex justify-between items-end">
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-ping"></div>
                                            <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em]">{t("tasks.processingHeader")}</p>
                                        </div>
                                        <p className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">{status}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-5xl font-black text-foreground font-mono leading-none tracking-tighter">{progress}%</p>
                                    </div>
                                </div>
                                <div className="w-full bg-background rounded-full h-5 overflow-hidden border border-card-border p-1.5 shadow-inner">
                                    <div
                                        className="bg-gradient-to-r from-indigo-600 via-blue-500 to-emerald-500 h-full transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(79,70,229,0.4)] rounded-full relative"
                                        style={{ width: `${progress}%` }}
                                    >
                                        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.1)_50%,transparent_75%)] bg-[length:40px_40px] animate-[slide_2s_linear_infinite]"></div>
                                    </div>
                                </div>
                                {eta !== null && !isFinished && (
                                    <p className="text-center text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                                        {t("tasks.eta")} <span className="text-slate-300 ml-1">{Math.floor(eta / 60)}{t("tasks.minutes")} {eta % 60}{t("tasks.seconds")}</span>
                                    </p>
                                )}
                                {isFinished && finishedTaskId && (
                                    <div className="flex justify-center pt-4 animate-in fade-in zoom-in duration-500">
                                        <Link
                                            href={`/result/${finishedTaskId}`}
                                            className="group flex items-center gap-3 px-12 py-5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl font-black text-lg transition-all shadow-xl shadow-emerald-500/20 active:scale-[0.98] ring-4 ring-emerald-500/20"
                                        >
                                            <span>{t("tasks.viewReport")}</span>
                                            <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                                        </Link>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                        {/* Active Tasks Side */}
                        <div className="lg:col-span-1 space-y-8">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-black tracking-tight flex items-center gap-2">
                                    <Clock className="w-5 h-5 text-indigo-400" />
                                    {t("tasks.activeTasks")}
                                </h2>
                                {activeTasks.length > 0 && <span className="px-2 py-1 bg-indigo-500/20 text-indigo-400 text-[10px] font-black rounded-lg">{activeTasks.length}</span>}
                            </div>

                            {activeTasks.length === 0 ? (
                                <div className="bg-card-bg/20 border border-dashed border-card-border rounded-3xl p-10 text-center">
                                    <CheckCircle2 className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                                    <p className="text-slate-500 text-sm font-bold">{t("tasks.noActiveTasks")}</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {activeTasks.map((task) => (
                                        <div key={task.id} className="bg-card-bg border border-card-border p-5 rounded-2xl backdrop-blur-md group hover:border-indigo-500/30 transition-all shadow-sm">
                                            <div className="flex justify-between items-start mb-3">
                                                <div className="overflow-hidden">
                                                    <p className="text-[9px] text-slate-500 font-mono truncate mb-1">#{task.id}</p>
                                                    <p className="text-xs font-black text-indigo-400 uppercase tracking-tighter truncate">{task.status}</p>
                                                </div>
                                                <p className="text-xl font-black text-foreground/40 group-hover:text-indigo-500 transition-colors uppercase tracking-tight">{task.progress}%</p>
                                            </div>
                                            <div className="w-full bg-background border border-card-border/50 rounded-full h-1 overflow-hidden">
                                                <div
                                                    className="bg-indigo-500 h-full transition-all duration-1000 shadow-[0_0_10px_rgba(79,70,229,0.3)]"
                                                    style={{ width: `${task.progress}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* History Side */}
                        <div className="lg:col-span-2 space-y-8">
                            <h2 className="text-xl font-black tracking-tight flex items-center gap-2">
                                <Clock className="w-5 h-5 text-emerald-400" />
                                {t("tasks.recentHistory")}
                            </h2>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {history.slice(0, 6).map((item) => (
                                    <div
                                        key={item.id}
                                        onClick={() => router.push(`/result/${item.id}`)}
                                        className="group bg-card-bg/50 border border-card-border rounded-3xl overflow-hidden cursor-pointer hover:border-indigo-500/30 transition-all hover:-translate-y-1 shadow-md hover:shadow-indigo-500/10"
                                    >
                                        <div className="aspect-video relative overflow-hidden">
                                            {item.thumbnail?.startsWith("#") ? (
                                                <div className="w-full h-full flex items-center justify-center bg-card-bg">
                                                    <Youtube className="w-8 h-8 text-slate-400/20" />
                                                </div>
                                            ) : (
                                                <img
                                                    src={item.thumbnail?.startsWith("http") ? item.thumbnail : (item.thumbnail ? `${getApiBase()}/media/${item.thumbnail}` : "https://images.unsplash.com/photo-1611162617474-5b21e879e113")}
                                                    alt={item.title}
                                                    className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700"
                                                />
                                            )}
                                            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent opacity-60"></div>
                                        </div>
                                        <div className="p-5">
                                            <h3 className="font-bold text-xs line-clamp-2 text-foreground group-hover:text-indigo-500 transition-colors leading-relaxed">
                                                {item.title}
                                            </h3>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {history.length > 6 && (
                                <Link href="/dashboard" className="block text-center py-4 bg-card-bg/30 border border-card-border rounded-2xl text-slate-500 text-xs font-black uppercase tracking-widest hover:bg-card-bg/50 transition-all hover:text-foreground">
                                    {t("tasks.viewAll")}
                                </Link>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
