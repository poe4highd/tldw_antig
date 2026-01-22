"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/utils/supabase";
import { Youtube, FileUp, ArrowRight, LayoutGrid, Clock, CheckCircle2, Menu } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { getApiBase } from "@/utils/api";
import { useTranslation } from "@/contexts/LanguageContext";

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
    const { t } = useTranslation();
    const [url, setUrl] = useState("");
    const [mode, setMode] = useState("local");
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [eta, setEta] = useState<number | null>(null);
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
        try {
            const apiBase = getApiBase();
            const resp = await fetch(`${apiBase}/process`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, mode, user_id: user?.id }),
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

        const formData = new FormData();
        formData.append("file", file);
        formData.append("mode", mode);
        if (user) formData.append("user_id", user.id);

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
                    router.push(`/result/${taskId}`);
                } else if (data.status === "failed") {
                    setStatus("Failed: " + (data.detail || "Unknown error"));
                    clearInterval(interval);
                } else {
                    setStatus(data.status || t("tasks.statusProcessing"));
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
            <main className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="animate-pulse flex flex-col items-center">
                    <div className="w-12 h-12 bg-slate-800 rounded-full mb-4"></div>
                    <p className="text-slate-500 font-medium">{t("tasks.verifyingIdentity")}</p>
                </div>
            </main>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50 flex font-sans">
            <Sidebar
                user={user}
                onSignOut={handleSignOut}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            <main className="flex-grow min-w-0 bg-slate-950 text-slate-50 font-sans pb-20 bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-indigo-900/10 via-slate-950 to-slate-950">
                <div className="max-w-6xl mx-auto px-4 md:px-6 py-8 md:py-12">
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
                            <span className="font-black tracking-tighter">Read-Tube</span>
                        </div>
                        <div className="w-10"></div>
                    </header>

                    <header className="mb-12 md:mb-16 flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-4">
                            <Link href="/dashboard" className="p-3 bg-slate-900 border border-slate-800 rounded-2xl hover:border-indigo-500/50 transition-all group hidden md:block">
                                <img src="/icon.png" alt="Read-Tube Logo" className="w-8 h-8 group-hover:scale-110 transition-transform" />
                            </Link>
                            <div>
                                <h1 className="text-3xl md:text-4xl font-black tracking-tight">{t("tasks.title")}</h1>
                                <p className="text-slate-400 font-medium">{t("tasks.subtitle")}</p>
                            </div>
                        </div>
                        <Link href="/dashboard" className="text-slate-500 hover:text-white transition-colors text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                            {t("tasks.backToBookshelf")} <ArrowRight className="w-4 h-4" />
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
                    <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-8 rounded-[2.5rem] shadow-2xl mb-12 max-w-4xl mx-auto ring-1 ring-white/5 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-5">
                            <LayoutGrid className="w-40 h-40" />
                        </div>

                        <div className="relative z-10 space-y-8">
                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] ml-2">{t("tasks.submitNew")}</label>
                                <div className="flex flex-col md:flex-row gap-4">
                                    <div className="flex-1 relative group">
                                        <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none text-slate-500 group-focus-within:text-blue-400 transition-colors">
                                            <Youtube className="w-5 h-5" />
                                        </div>
                                        <input
                                            type="text"
                                            placeholder={t("tasks.placeholder")}
                                            className="w-full bg-slate-950 border border-slate-700/50 rounded-2xl pl-16 pr-6 py-5 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-lg placeholder:text-slate-700 shadow-inner"
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                        />
                                    </div>
                                    <div className="flex gap-3">
                                        <select
                                            className="bg-slate-950 border border-slate-700/50 rounded-2xl px-6 py-5 appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-slate-300 font-bold cursor-pointer shadow-inner"
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
                                            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all px-10 py-5 rounded-2xl font-black text-white shadow-xl shadow-blue-900/20 active:scale-[0.98] whitespace-nowrap"
                                        >
                                            {t("tasks.processNow")}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4 px-2">
                                <div className="h-px flex-1 bg-slate-800/50"></div>
                                <span className="text-[10px] text-slate-600 font-black uppercase tracking-widest">{t("tasks.orUpload")}</span>
                                <div className="h-px flex-1 bg-slate-800/50"></div>
                            </div>

                            <div className="flex justify-center">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex items-center gap-3 px-8 py-4 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700/50 rounded-2xl text-slate-400 transition-all group hover:text-white"
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
                            <div className="mt-12 pt-10 border-t border-slate-800/50 space-y-6 animate-in fade-in slide-in-from-top-4 duration-1000">
                                <div className="flex justify-between items-end">
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
                                            <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em]">{t("tasks.processingHeader")}</p>
                                        </div>
                                        <p className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">{status}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-5xl font-black text-white font-mono leading-none tracking-tighter">{progress}%</p>
                                    </div>
                                </div>
                                <div className="w-full bg-slate-950/80 rounded-full h-5 overflow-hidden border border-slate-800 p-1.5 shadow-inner">
                                    <div
                                        className="bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 h-full transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(37,99,235,0.4)] rounded-full relative"
                                        style={{ width: `${progress}%` }}
                                    >
                                        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.1)_50%,transparent_75%)] bg-[length:40px_40px] animate-[slide_2s_linear_infinite]"></div>
                                    </div>
                                </div>
                                {eta !== null && (
                                    <p className="text-center text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                                        {t("tasks.eta")} <span className="text-slate-300 ml-1">{Math.floor(eta / 60)}{t("tasks.minutes")} {eta % 60}{t("tasks.seconds")}</span>
                                    </p>
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
                                <div className="bg-slate-900/20 border border-slate-800/50 rounded-3xl p-10 text-center">
                                    <CheckCircle2 className="w-10 h-10 text-slate-700 mx-auto mb-4" />
                                    <p className="text-slate-500 text-sm font-bold">{t("tasks.noActiveTasks")}</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {activeTasks.map((task) => (
                                        <div key={task.id} className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl backdrop-blur-md group hover:border-indigo-500/30 transition-all">
                                            <div className="flex justify-between items-start mb-3">
                                                <div className="overflow-hidden">
                                                    <p className="text-[9px] text-slate-500 font-mono truncate mb-1">#{task.id}</p>
                                                    <p className="text-xs font-black text-indigo-300 uppercase tracking-tighter truncate">{task.status}</p>
                                                </div>
                                                <p className="text-xl font-black text-white/50 group-hover:text-indigo-400 transition-colors">{task.progress}%</p>
                                            </div>
                                            <div className="w-full bg-slate-950 rounded-full h-1 overflow-hidden">
                                                <div
                                                    className="bg-indigo-500 h-full transition-all duration-1000"
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
                                        className="group bg-slate-900/30 border border-slate-800/50 rounded-3xl overflow-hidden cursor-pointer hover:border-emerald-500/30 transition-all hover:-translate-y-1 shadow-xl"
                                    >
                                        <div className="aspect-video relative overflow-hidden">
                                            {item.thumbnail?.startsWith("#") ? (
                                                <div className="w-full h-full flex items-center justify-center bg-slate-800">
                                                    <Youtube className="w-8 h-8 text-white/20" />
                                                </div>
                                            ) : (
                                                <img
                                                    src={item.thumbnail?.startsWith("http") ? item.thumbnail : (item.thumbnail ? `${getApiBase()}/media/${item.thumbnail}` : "https://images.unsplash.com/photo-1611162617474-5b21e879e113")}
                                                    alt={item.title}
                                                    className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700"
                                                />
                                            )}
                                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-60"></div>
                                        </div>
                                        <div className="p-5">
                                            <h3 className="font-bold text-xs line-clamp-2 text-slate-200 group-hover:text-emerald-400 transition-colors leading-relaxed">
                                                {item.title}
                                            </h3>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {history.length > 6 && (
                                <Link href="/dashboard" className="block text-center py-4 bg-slate-900/20 border border-slate-800 rounded-2xl text-slate-500 text-xs font-black uppercase tracking-widest hover:bg-slate-900/40 transition-all hover:text-slate-300">
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
