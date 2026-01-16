"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

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

export default function Home() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState("local");
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [apiBase, setApiBase] = useState("");
  const [isDev, setIsDev] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    // 优先使用环境变量，否则根据当前协议动态推导
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const defaultPort = ":8000";

    let base = process.env.NEXT_PUBLIC_API_BASE;
    if (!base) {
      if (hostname === "localhost" || hostname === "127.0.0.1" || hostname.startsWith("192.168.")) {
        base = `http://${hostname}${defaultPort}`;
      } else {
        // 在外网/隧道环境下，如果当前是 HTTPS，API 也必须是 HTTPS
        // 且外网环境下通常不直接跟 :8000 (除非是自定义端口隧道)
        const isTunnel = hostname.includes("trycloudflare.com") || hostname.includes("vercel.app");
        base = `${protocol}//${hostname}${isTunnel ? "" : defaultPort}`;
      }
    }

    setApiBase(base);
    fetchHistory(base);

    // 检查是否为开发者模式
    const params = new URLSearchParams(window.location.search);
    if (params.get("role") === "dev") {
      setIsDev(true);
    }

    // 每 15 秒刷新一次历史和任务状态
    const interval = setInterval(() => fetchHistory(base), 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (eta !== null && eta > 0) {
      const timer = setTimeout(() => setEta(eta - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [eta]);

  const fetchHistory = async (base: string) => {
    try {
      const resp = await fetch(`${base}/history`);
      const data = await resp.json();
      setHistory(data.items || []);
      setSummary(data.summary || null);
      setActiveTasks(data.active_tasks || []);
    } catch (e) {
      console.error("Failed to fetch history");
    }
  };

  const startProcess = async () => {
    if (!url) return;
    setStatus("正在初始化任务...");
    setProgress(0);
    setEta(null);
    try {
      const resp = await fetch(`${apiBase}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, mode }),
      });
      const data = await resp.json();
      pollStatus(data.task_id);
    } catch (e) {
      setStatus("Error starting process");
    }
  };

  const onFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setStatus("正在上传音频文件...");
    setProgress(0);
    setEta(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", mode);

    try {
      const resp = await fetch(`${apiBase}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      pollStatus(data.task_id);
    } catch (err) {
      setStatus("上传失败");
    }
  };

  const pollStatus = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`${apiBase}/result/${taskId}`);
        const data = await resp.json();
        setProgress(data.progress || 0);
        if (data.eta !== undefined) setEta(data.eta);

        if (data.status === "completed") {
          clearInterval(interval);
          router.push(`/${isDev ? 'dev-result' : 'result'}/${taskId}${isDev ? '?role=dev' : ''}`);
        } else if (data.status === "failed") {
          setStatus("Failed: " + (data.detail || "Unknown error"));
          clearInterval(interval);
        } else {
          setStatus(data.status || "Processing...");
        }
      } catch (e) {
        setStatus("Connection lost...");
      }
    }, 2000);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-50 font-sans pb-20">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <header className="text-center mb-16 flex flex-col items-center">
          <div className="flex items-center justify-center mb-4">
            <img src="/icon.png" alt="Read-Tube Logo" className="w-16 h-16 mr-4" />
            <h1 className="text-5xl font-black bg-gradient-to-r from-indigo-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent tracking-tight">
              Read-Tube
            </h1>
          </div>
          <p className="text-slate-400 text-lg">YouTube / Audio / Video Quick Reader</p>
        </header>

        {/* Stats Dashboard */}
        {summary && isDev && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm">
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2">已处理实体</p>
              <p className="text-4xl font-black text-white">{summary.video_count}</p>
            </div>
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm">
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2">累计处理时长</p>
              <p className="text-4xl font-black text-white">
                {Math.floor(summary.total_duration / 60)}<span className="text-lg text-slate-500 font-medium">m</span>
              </p>
            </div>
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2 text-right">累计消耗估算</p>
              <p className="text-4xl font-black text-emerald-400 text-right">
                <span className="text-2xl">$</span>{summary.total_cost.toFixed(3)}
              </p>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 p-8 rounded-[2.5rem] shadow-2xl mb-20 max-w-4xl mx-auto ring-1 ring-white/5">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                placeholder="Paste YouTube link here..."
                className="flex-1 bg-slate-950 border border-slate-700/50 rounded-2xl px-6 py-5 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-lg"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              <div className="flex gap-3">
                <select
                  className="bg-slate-950 border border-slate-700/50 rounded-2xl px-5 py-5 appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-slate-300 font-medium cursor-pointer"
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="cloud">云端 (API)</option>
                  <option value="local">本地 (FREE)</option>
                </select>
                <button
                  onClick={startProcess}
                  className="bg-blue-600 hover:bg-blue-500 transition-all px-10 py-5 rounded-2xl font-black text-white shadow-xl shadow-blue-900/20 active:scale-[0.98] whitespace-nowrap"
                >
                  开始阅读
                </button>
              </div>
            </div>

            <div className="flex items-center gap-4 px-2">
              <div className="h-px flex-1 bg-slate-800"></div>
              <span className="text-xs text-slate-600 font-bold uppercase tracking-widest">或者</span>
              <div className="h-px flex-1 bg-slate-800"></div>
            </div>

            <div className="flex justify-center">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-3 px-8 py-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-2xl text-slate-300 transition-all group"
              >
                <svg className="w-5 h-5 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <span className="font-bold">上传视频或音频文件 (MP4/MOV/MP3/M4A)</span>
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
            <div className="mt-10 space-y-4 animate-in fade-in slide-in-from-top-2 duration-700">
              <div className="flex justify-between items-end">
                <div className="space-y-1">
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-[0.2em]">Current Task</p>
                  <p className="text-blue-400 font-bold text-lg animate-pulse">{status}</p>
                </div>
                <div className="text-right">
                  <p className="text-4xl font-black text-slate-700 font-mono leading-none">{progress}%</p>
                </div>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-4 overflow-hidden border border-slate-800 p-1">
                <div
                  className="bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 h-full transition-all duration-1000 ease-out shadow-[0_0_20px_rgba(37,99,235,0.3)] rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Active Tasks (Dev Only) */}
        {isDev && activeTasks.length > 0 && (
          <div className="mb-12 space-y-4">
            <h2 className="text-xl font-black uppercase tracking-widest text-blue-400 flex items-center gap-2">
              正在后台处理
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeTasks.map((task) => (
                <div key={task.id} className="bg-slate-900/60 border border-blue-500/20 p-5 rounded-3xl backdrop-blur-md relative overflow-hidden group">
                  <div className="flex justify-between items-start mb-3">
                    <div className="space-y-1">
                      <p className="text-[10px] text-slate-500 font-mono">TASK ID: {task.id}</p>
                      <p className="text-sm font-bold text-blue-300 group-hover:text-blue-200 transition-colors tracking-tight uppercase">{task.status}</p>
                    </div>
                    <p className="text-2xl font-black text-blue-500/50 group-hover:text-blue-500 transition-colors">{task.progress}%</p>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
                    <div
                      className="bg-blue-500 h-full transition-all duration-1000 ease-out"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* History Section */}
        <div className="space-y-10">
          <div className="flex items-center gap-6">
            <h2 className="text-3xl font-black tracking-tight">阅读历史</h2>
            <div className="h-px flex-1 bg-gradient-to-r from-slate-800 to-transparent"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {history.map((item) => (
              <div
                key={item.id}
                onClick={() => router.push(`/${isDev ? 'dev-result' : 'result'}/${item.id}${isDev ? '?role=dev' : ''}`)}
                className="group bg-slate-900/40 border border-slate-800/50 rounded-[2rem] overflow-hidden cursor-pointer hover:border-blue-500/30 transition-all hover:-translate-y-2 shadow-xl ring-1 ring-white/5"
              >
                <div className="aspect-video relative overflow-hidden">
                  {item.thumbnail?.startsWith("#") ? (
                    <div className="w-full h-full flex items-center justify-center" style={{ backgroundColor: item.thumbnail }}>
                      <svg className="w-12 h-12 text-white/50" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 3v11.13a3.345 3.345 0 102 3.29V5.47l8-1.6v6.26a3.345 3.345 0 102 3.29V3z" />
                      </svg>
                    </div>
                  ) : (
                    <img
                      src={item.thumbnail?.startsWith("http") ? item.thumbnail : (item.thumbnail ? `${apiBase}/media/${item.thumbnail}` : "https://images.unsplash.com/photo-1611162617474-5b21e879e113")}
                      alt={item.title}
                      className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700"
                    />
                  )}
                  {isDev && item.total_cost !== undefined && (
                    <div className="absolute top-4 right-4 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-[10px] font-black text-emerald-400 font-mono shadow-xl">
                      ${item.total_cost.toFixed(3)}
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-60"></div>
                </div>
                <div className="p-7">
                  <h3 className="font-bold text-lg line-clamp-2 text-slate-100 group-hover:text-blue-400 transition-colors leading-snug">
                    {item.title}
                  </h3>
                  <div className="mt-4 flex items-center justify-between">
                    <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center group-hover:bg-blue-600 transition-colors">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <footer className="max-w-6xl mx-auto px-6 py-12 border-t border-slate-900 mt-20 flex justify-between items-center text-slate-600 text-xs font-mono">
        <span>© 2026 Read-Tube</span>
        <a href={isDev ? "/" : "/?role=dev"} className="hover:text-blue-500 transition-colors">
          {isDev ? "退出开发者模式" : "进入开发者模式"}
        </a>
      </footer>
    </main>
  );
}
