"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface HistoryItem {
  id: string;
  title: string;
  thumbnail: string;
  url: string;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState("cloud");
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [apiBase, setApiBase] = useState("");
  const router = useRouter();

  useEffect(() => {
    const base = `http://${window.location.hostname}:8000`;
    setApiBase(base);
    fetchHistory(base);
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
      setHistory(data);
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

      // 开始轮询进度
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
          router.push(`/result/${taskId}`);
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
    <main className="min-h-screen bg-slate-950 text-slate-50 font-sans">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <header className="text-center mb-16">
          <h1 className="text-5xl font-black mb-4 bg-gradient-to-r from-indigo-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent">
            TL;DW Antigravity
          </h1>
          <p className="text-slate-400 text-lg">YouTube 视频转录与沉浸式阅读器</p>
        </header>

        {/* Input Section */}
        <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 p-8 rounded-3xl shadow-2xl mb-16 max-w-3xl mx-auto">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="粘贴 YouTube 视频链接..."
              className="flex-1 bg-slate-950 border border-slate-700 rounded-2xl px-5 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-lg"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <div className="flex gap-2">
              <select
                className="bg-slate-950 border border-slate-700 rounded-2xl px-4 py-4 appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
              >
                <option value="cloud">云端 (OpenAI)</option>
                <option value="local">本地 (Whisper)</option>
              </select>
              <button
                onClick={startProcess}
                className="bg-blue-600 hover:bg-blue-500 transition-all px-8 py-4 rounded-2xl font-bold shadow-lg shadow-blue-600/20 active:scale-95 whitespace-nowrap"
              >
                立即开始
              </button>
            </div>
          </div>

          {status && (
            <div className="mt-8 space-y-3 animate-in fade-in slide-in-from-top-2 duration-500">
              <div className="flex justify-between items-center text-sm">
                <span className="text-blue-400 font-medium animate-pulse">{status}</span>
                <div className="flex items-center gap-3">
                  {eta !== null && eta > 0 && (
                    <span className="text-slate-400 bg-slate-800/50 px-2 py-0.5 rounded-lg border border-slate-700/50">
                      估计剩余: <span className="text-indigo-400 font-mono">{eta}s</span>
                    </span>
                  )}
                  <span className="text-slate-500 font-mono bg-slate-800/50 px-2 py-0.5 rounded-lg border border-slate-700/50">
                    {progress}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800 p-0.5">
                <div
                  className="bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 h-full transition-all duration-700 ease-out shadow-[0_0_15px_rgba(37,99,235,0.4)] rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
              {eta !== null && eta > 0 && (
                <p className="text-xs text-slate-500 text-center animate-in fade-in duration-1000">
                  AI 正在努力处理中，请稍候... ☕️
                </p>
              )}
            </div>
          )}
        </div>

        {/* History Section */}
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">历史记录</h2>
            <div className="h-px flex-1 bg-slate-800"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {history.map((item) => (
              <div
                key={item.id}
                onClick={() => router.push(`/result/${item.id}`)}
                className="group bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden cursor-pointer hover:border-slate-600 transition-all hover:-translate-y-1 shadow-xl hover:shadow-2xl"
              >
                <div className="aspect-video relative overflow-hidden">
                  <img
                    src={item.thumbnail || "https://images.unsplash.com/photo-1611162617474-5b21e879e113"}
                    alt={item.title}
                    className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                    <span className="text-white font-semibold">点击阅读全文 →</span>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="font-bold text-lg line-clamp-2 text-slate-100 group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm text-slate-500 font-mono truncate">{new URL(item.url).hostname}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
