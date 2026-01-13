"use client";

import { useState, useRef, useEffect, use } from "react";
import Link from "next/link";

interface Sentence {
    start: number;
    text: string;
}

interface Paragraph {
    sentences: Sentence[];
}

interface Usage {
    duration: number;
    whisper_cost: number;
    llm_tokens: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
    llm_cost: number;
    total_cost: number;
    currency: string;
}

interface Result {
    title: string;
    url: string;
    youtube_id?: string;
    paragraphs?: Paragraph[];
    subtitles?: any[];
    usage?: Usage;
}

export default function ResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [result, setResult] = useState<Result | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const [apiBase, setApiBase] = useState("");

    useEffect(() => {
        setApiBase(`http://${window.location.hostname}:8000`);
    }, []);

    useEffect(() => {
        if (!id || !apiBase) return;
        const fetchResult = async () => {
            try {
                const resp = await fetch(`${apiBase}/result/${id}`);
                const data = await resp.json();
                if (data.status === "completed") {
                    setResult(data);
                }
            } catch (e) {
                console.error(e);
            }
        };
        fetchResult();
    }, [id, apiBase]);

    // Handle high-frequency time updates from YouTube Player
    useEffect(() => {
        if (!result) return;

        const handleMessage = (event: MessageEvent) => {
            if (event.origin !== "https://www.youtube.com") return;
            try {
                const data = JSON.parse(event.data);
                if (data.event === "infoDelivery" && data.info && data.info.currentTime !== undefined) {
                    setCurrentTime(data.info.currentTime);
                }
            } catch (e) {
                // Ignore non-JSON messages
            }
        };

        window.addEventListener("message", handleMessage);

        const interval = setInterval(() => {
            if (iframeRef.current && iframeRef.current.contentWindow) {
                iframeRef.current.contentWindow.postMessage(
                    JSON.stringify({ event: "listening" }),
                    "*"
                );
            }
        }, 500);

        return () => {
            window.removeEventListener("message", handleMessage);
            clearInterval(interval);
        };
    }, [result]);

    const seek = (time: number) => {
        if (iframeRef.current) {
            iframeRef.current.contentWindow?.postMessage(
                JSON.stringify({ event: "command", func: "seekTo", args: [time, true] }),
                "*"
            );
            iframeRef.current.contentWindow?.postMessage(
                JSON.stringify({ event: "command", func: "playVideo" }),
                "*"
            );
        }
    };

    if (!result) return (
        <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    const isSentenceActive = (start: number, nextStart?: number) => {
        if (nextStart === undefined) {
            return currentTime >= start;
        }
        return currentTime >= start && currentTime < nextStart;
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-50 font-sans">
            <div className="flex flex-col lg:flex-row min-h-screen">
                
                {/* Fixed Side Sidebar (Left) */}
                <div className="lg:w-[450px] xl:w-[500px] lg:fixed lg:left-0 lg:top-0 lg:bottom-0 bg-slate-900 border-r border-slate-800 p-6 flex flex-col z-20">
                    <Link href="/?role=dev" className="inline-flex items-center text-slate-400 hover:text-blue-400 mb-6 transition group w-fit text-sm">
                        <div className="bg-slate-800 p-1.5 rounded-md mr-3 group-hover:bg-blue-600/20 transition-colors">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </div>
                        返回列表 (DEV)
                    </Link>

                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
                        <h1 className="text-xl font-bold leading-tight text-slate-100 mb-6">
                            {result.title}
                        </h1>
                        
                        <div className="aspect-video bg-black rounded-xl overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 mb-8">
                            <iframe
                                ref={iframeRef}
                                src={`https://www.youtube.com/embed/${result.youtube_id || result.url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/)?.[1] || ''}?enablejsapi=1&autoplay=1`}
                                className="w-full h-full"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        </div>

                        {/* Usage Card (DEV only) */}
                        {result.usage && (
                            <div className="bg-slate-950/50 p-5 rounded-2xl border border-slate-800/80 mb-6 space-y-4">
                                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                                    <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                                    处理消耗统计 (DEV)
                                </h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-800/30">
                                        <p className="text-[10px] text-slate-500 mb-1">音频时长</p>
                                        <p className="text-sm font-mono text-slate-200">
                                            {Math.floor(result.usage.duration / 60)}:{(result.usage.duration % 60).toFixed(0).padStart(2, '0')}
                                        </p>
                                    </div>
                                    <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-800/30">
                                        <p className="text-[10px] text-slate-500 mb-1">预估费用 (USD)</p>
                                        <p className="text-sm font-mono text-emerald-400 font-bold">${result.usage.total_cost.toFixed(4)}</p>
                                    </div>
                                </div>
                                <div className="pt-2">
                                    <div className="flex justify-between text-[11px] mb-1">
                                        <span className="text-slate-500">LLM Tokens (In/Out)</span>
                                        <span className="text-slate-400 font-mono">
                                            {result.usage.llm_tokens.prompt_tokens} / {result.usage.llm_tokens.completion_tokens}
                                        </span>
                                    </div>
                                    <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                                        <div 
                                            className="bg-blue-500 h-full" 
                                            style={{ width: `${Math.min(100, (result.usage.llm_tokens.total_tokens / 5000) * 100)}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="p-4 bg-slate-950/20 rounded-xl border border-slate-800/50">
                            <p className="text-[11px] text-slate-500 leading-relaxed italic">
                                💡 开发模式：您可以查看详尽的 API 消耗与 Token 分布。
                            </p>
                        </div>
                    </div>

                    <div className="pt-6 mt-6 border-t border-slate-800/50 flex justify-between items-center text-[10px] text-slate-600 font-mono">
                        <span>YT QUICK READER v2.1</span>
                        <span className="text-blue-500/50 px-2 py-0.5 border border-blue-500/20 rounded">DEV</span>
                    </div>
                </div>

                {/* Main Content Area (Scrollable Right) */}
                <div className="lg:ml-[450px] xl:ml-[500px] flex-1 min-h-screen bg-slate-950">
                    <div className="max-w-3xl mx-auto p-12 lg:p-20">
                        <div className="prose prose-invert max-w-none">
                            {(() => {
                                const rawPara = result.paragraphs || [];
                                const rawSub = result.subtitles || [];
                                
                                const displayParagraphs: Paragraph[] = rawPara.length > 0 
                                    ? rawPara 
                                    : rawSub.map((s: any) => ({
                                        sentences: [{ start: s.start, text: s.text }]
                                    }));

                                const allSentences: Sentence[] = [];
                                displayParagraphs.forEach(p => allSentences.push(...p.sentences));

                                return displayParagraphs.map((para, pIdx) => (
                                    <div key={pIdx} className="mb-10 text-justify">
                                        {para.sentences?.map((sentence, sIdx) => {
                                            const flatIdx = allSentences.indexOf(sentence);
                                            const nextS = allSentences[flatIdx + 1];
                                            const active = isSentenceActive(sentence.start, nextS?.start);

                                            return (
                                                <span
                                                    key={sIdx}
                                                    onClick={() => seek(sentence.start)}
                                                    className={`cursor-pointer rounded transition-all duration-300 text-[15.5px] leading-[1.65] px-0.5 decoration-blue-500/20 hover:underline decoration-1 underline-offset-[6px] ${
                                                        active 
                                                        ? "text-blue-400 font-bold bg-blue-400/10 scale-[1.02] inline-block shadow-[0_0_20px_rgba(96,165,250,0.1)]" 
                                                        : "text-slate-400 hover:text-blue-300"
                                                    }`}
                                                    title={`跳转到 ${Math.floor(sentence.start / 60)}:${(sentence.start % 60).toFixed(0).padStart(2, '0')}`}
                                                >
                                                    {sentence.text}{" "}
                                                </span>
                                            );
                                        })}
                                    </div>
                                ));
                            })()}
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar { width: 4px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
            `}</style>
        </main>
    );
}
