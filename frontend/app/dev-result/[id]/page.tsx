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
            <div className="flex flex-col lg:flex-row min-h-screen relative">

                {/* Fixed/Sticky Video Panel */}
                <div className="w-full lg:w-[450px] xl:w-[500px] sticky top-0 lg:fixed lg:left-0 lg:top-0 lg:bottom-0 bg-slate-900 lg:border-r border-b lg:border-b-0 border-slate-800 p-4 lg:p-6 flex flex-col z-40 shadow-xl lg:shadow-none">
                    <Link href="/?role=dev" className="inline-flex items-center text-slate-400 hover:text-blue-400 mb-3 lg:mb-6 transition group w-fit text-xs lg:text-sm">
                        <div className="bg-slate-800 p-1 lg:p-1.5 rounded-md mr-2 lg:mr-3 group-hover:bg-blue-600/20 transition-colors">
                            <svg className="w-3 h-3 lg:w-3.5 lg:h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </div>
                        返回列表 (DEV)
                    </Link>

                    {/* Desktop Only Title */}
                    <h1 className="hidden lg:block text-xl font-bold leading-tight text-slate-100 mb-6 px-1">
                        {result.title}
                    </h1>

                    {/* Shared Single Player Instance (Crucial to avoid double sound) */}
                    <div className="aspect-video bg-black rounded-lg lg:rounded-xl overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 mb-2 lg:mb-8">
                        <iframe
                            ref={iframeRef}
                            src={`https://www.youtube.com/embed/${result.youtube_id || result.url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/)?.[1] || ''}?enablejsapi=1&autoplay=1`}
                            className="w-full h-full"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                        />
                    </div>

                    {/* Mobile Only Title */}
                    <h1 className="lg:hidden block text-sm font-bold leading-tight text-slate-100 truncate mb-1">
                        {result.title}
                    </h1>

                    {/* Desktop Only Tip */}
                    <div className="hidden lg:block p-4 bg-slate-950/20 rounded-xl border border-slate-800/50 mt-4">
                        <p className="text-[11px] text-slate-500 leading-relaxed italic">
                            💡 高亮显示为当前播放内容。点击文字可快速跳转。
                        </p>
                    </div>

                    {/* Usage Card (Dev Only) */}
                    {result.usage && (
                        <div className="hidden lg:block mt-6 p-4 bg-blue-500/5 rounded-xl border border-blue-500/10 backdrop-blur-sm">
                            <h3 className="text-[10px] uppercase tracking-wider text-blue-400 font-bold mb-3 flex items-center">
                                <span className="w-1 h-1 bg-blue-400 rounded-full mr-2"></span>
                                处理消耗统计
                            </h3>
                            <div className="space-y-2.5">
                                <div className="flex justify-between text-[11px]">
                                    <span className="text-slate-500">音频时长</span>
                                    <span className="text-slate-300 font-mono">{(result.usage.duration / 60).toFixed(1)} min</span>
                                </div>
                                <div className="flex justify-between text-[11px]">
                                    <span className="text-slate-500">LLM Tokens</span>
                                    <span className="text-slate-300 font-mono">{result.usage.llm_tokens.total_tokens}</span>
                                </div>
                                <div className="flex justify-between text-[11px] pt-2 border-t border-blue-500/10">
                                    <span className="text-blue-400/80 font-medium">预估总成本</span>
                                    <span className="text-blue-400 font-bold font-mono">
                                        {result.usage.currency === "USD" ? "$" : ""}{result.usage.total_cost.toFixed(4)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="pt-4 mt-auto border-t border-slate-800/50 lg:flex hidden justify-between items-center text-[10px] text-slate-600 font-mono">
                        <span>YT QUICK READER v2.2</span>
                        <span className="text-blue-500/50 px-2 py-0.5 border border-blue-500/20 rounded">DEV</span>
                    </div>
                </div>

                {/* Main Content Area (Scrollable Right) */}
                <div className="lg:ml-[450px] xl:ml-[500px] flex-1 min-h-screen bg-slate-950">
                    <div className="max-w-3xl mx-auto p-6 lg:p-20">
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
                                    <div key={pIdx} className="mb-8 lg:mb-10 text-justify">
                                        {para.sentences?.map((sentence, sIdx) => {
                                            const flatIdx = allSentences.indexOf(sentence);
                                            const nextS = allSentences[flatIdx + 1];
                                            const active = isSentenceActive(sentence.start, nextS?.start);

                                            return (
                                                <span
                                                    key={sIdx}
                                                    onClick={() => seek(sentence.start)}
                                                    className={`cursor-pointer rounded transition-all duration-300 text-[14.5px] lg:text-[15.5px] leading-[1.65] px-0.5 decoration-blue-500/20 hover:underline decoration-1 underline-offset-[6px] ${active
                                                            ? "text-blue-400 font-bold bg-blue-400/10 scale-[1.01] inline-block shadow-[0_0_15px_rgba(96,165,250,0.08)]"
                                                            : "text-slate-400 hover:text-blue-300"
                                                        }`}
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
