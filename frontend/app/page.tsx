"use client";

import { useState, useEffect } from "react";
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

export default function Home() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState("cloud");
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [apiBase, setApiBase] = useState("");
  const [isDev, setIsDev] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const base = `http://${window.location.hostname}:8000`;
    setApiBase(base);
    fetchHistory(base);

    // 检查是否为开发者模式
    const params = new URLSearchParams(window.location.search);
    if (params.get("role") === "dev") {
      setIsDev(true);
    }
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
    } catch (e) {
      console.error("Failed to fetch history");
    }
  };

  const startProcess = async () => {
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
      const taskId = data.task_id;
      pollStatus(taskId);
    } catch (e) {
      setStatus("Error starting process");
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
        <header className="text-center mb-16">
          <h1 className="text-5xl font-black mb-4 bg-gradient-to-r from-indigo-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Youtube Quick Reader
          </h1>
          <p className="text-slate-400 text-lg">YouTube 视频转录与沉浸式阅读器</p>
        </header>

        {/* Stats Dashboard */}
        {summary && isDev && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-in fade-in slide-in-from-top-4 duration-1000">
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm">
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2">已处理视频</p>
              <p className="text-4xl font-black text-white">{summary.video_count}</p>
            </div>
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm">
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2">累计处理时长</p>
              <p className="text-4xl font-black text-white">
                {Math.floor(summary.total_duration / 60)}<span className="text-lg text-slate-500 font-medium">m</span>
              </p>
            </div>
            <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full -mr-12 -mt-12 blur-2xl group-hover:bg-emerald-500/20 transition-all"></div>
              <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-2">累计消耗估算</p>
              <p className="text-4xl font-black text-emerald-400">
                <span className="text-2xl">$</span>{summary.total_cost.toFixed(3)}
              </p>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 p-8 rounded-[2.5rem] shadow-2xl mb-20 max-w-4xl mx-auto ring-1 ring-white/5">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="Paste YouTube video link here..."
              className="flex-1 bg-slate-950 border border-slate-700/50 rounded-2xl px-6 py-5 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-lg placeholder:text-slate-600"
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
              {eta !== null && eta > 0 && (
                <div className="flex justify-center items-center gap-4 text-xs font-mono">
                  <span className="text-slate-500">预计剩余时间:</span>
                  <span className="text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">{eta}s</span>
                </div>
              )}
            </div>
          )}
        </div>

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
                className="group bg-slate-900/40 border border-slate-800/50 rounded-[2rem] overflow-hidden cursor-pointer hover:border-blue-500/30 transition-all hover:-translate-y-2 shadow-xl hover:shadow-blue-900/10 ring-1 ring-white/5"
              >
                <div className="aspect-video relative overflow-hidden">
                  <img
                    src={item.thumbnail || "https://images.unsplash.com/photo-1611162617474-5b21e879e113"}
                    alt={item.title}
                    className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700"
                  />
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
        <span>© 2026 Youtube Quick Reader</span>
        <a href={isDev ? "/" : "/?role=dev"} className="hover:text-blue-500 transition-colors">
          {isDev ? "退出开发者模式" : "开发者模式"}
        </a>
      </footer>
    </main>
  );
}
