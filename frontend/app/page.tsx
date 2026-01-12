"use client";

import { useState, useRef, useEffect } from "react";

interface Subtitle {
  start: number;
  end: number;
  text: string;
}

interface Result {
  title: string;
  media_path: string;
  subtitles: Subtitle[];
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState("cloud");
  const [taskId, setTaskId] = useState<string | null>(null);

  // 动态获取 API 基础地址
  const apiBase = typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "";
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  const startProcess = async () => {
    setStatus("Starting...");
    setProgress(0);
    setResult(null);
    try {
      const resp = await fetch(`${apiBase}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, mode }),
      });
      const data = await resp.json();
      setTaskId(data.task_id);
    } catch (e) {
      setStatus("Error starting process");
    }
  };

  useEffect(() => {
    if (!taskId || result) return;

    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`${apiBase}/result/${taskId}`);
        const data = await resp.json();
        setProgress(data.progress || 0);
        if (data.status === "completed") {
          setResult(data);
          setStatus("Done!");
          clearInterval(interval);
        } else if (data.status === "failed") {
          setStatus("Failed: " + JSON.stringify(data.detail));
          clearInterval(interval);
        } else {
          setStatus(data.status || "Processing...");
        }
      } catch (e) {
        console.error(e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [taskId, result]);

  const seek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          YouTube Transcription Tool
        </h1>

        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="Enter YouTube URL"
              className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <select
              className="bg-slate-950 border border-slate-700 rounded-lg px-4 py-2"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
            >
              <option value="cloud">Cloud (OpenAI)</option>
              <option value="local">Local (Whisper)</option>
            </select>
            <button
              onClick={startProcess}
              className="bg-blue-600 hover:bg-blue-500 transition px-6 py-2 rounded-lg font-semibold"
            >
              Start
            </button>
          </div>
          {status && (
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-sm text-slate-400">
                <span>{status}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-blue-600 h-full transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-fade-in">
            <div className="space-y-4">
              <h2 className="text-2xl font-semibold">{result.title}</h2>
              <div className="aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
                <video
                  ref={videoRef}
                  src={`${apiBase}/media/${result.media_path}`}
                  controls
                  className="w-full h-full"
                  onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                />
              </div>
            </div>

            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 h-[600px] flex flex-col">
              <h3 className="text-xl font-semibold mb-4 border-b border-slate-800 pb-2">Subtitles</h3>
              <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                {result.subtitles.map((sub, i) => {
                  const isActive = currentTime >= sub.start && currentTime <= sub.end;
                  return (
                    <div
                      key={i}
                      onClick={() => seek(sub.start)}
                      className={`p-3 rounded-lg cursor-pointer transition ${isActive
                        ? "bg-blue-600/20 border border-blue-500/50 text-blue-100"
                        : "hover:bg-slate-800 text-slate-400"
                        }`}
                    >
                      <span className="text-xs font-mono opacity-50 block mb-1">
                        {new Date(sub.start * 1000).toISOString().substr(14, 5)}
                      </span>
                      <p>{sub.text}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
        }
      `}</style>
    </main>
  );
}
