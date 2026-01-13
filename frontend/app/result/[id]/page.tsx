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

interface Result {
    title: string;
    url: string;
    youtube_id?: string;
    paragraphs?: Paragraph[];
    subtitles?: any[];
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

    return (
        <main className="min-h-screen bg-slate-950 text-slate-50 p-4 md:p-8 font-sans">
            <div className="max-w-7xl mx-auto">
                <Link href="/" className="inline-flex items-center text-slate-400 hover:text-blue-400 mb-6 transition">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                    Back to History
                </Link>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Left: Video Section */}
                    <div className="lg:col-span-12 space-y-6">
                        <h1 className="text-3xl font-bold leading-tight">{result.title}</h1>
                        <div className="aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-slate-800">
                            <iframe
                                ref={iframeRef}
                                src={`https://www.youtube.com/embed/${result.youtube_id || result.url.split('v=')[1] || result.url.split('/').pop()}?enablejsapi=1`}
                                className="w-full h-full"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        </div>
                    </div>

                    {/* Right: Reader Section */}
                    <div className="lg:col-span-5 h-[calc(100vh-8rem)] flex flex-col pt-12 lg:pt-0">
                        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8 flex-1 overflow-y-auto custom-scrollbar backdrop-blur-sm">
                            <div className="prose prose-invert max-w-none space-y-8">
                                {(() => {
                                    // 兼容性处理
                                    const rawPara = result.paragraphs || [];
                                    const rawSub = result.subtitles || [];

                                    // 如果是旧版平铺格式 (subtitles)，将其包装成单一句子的段落
                                    const displayParagraphs: Paragraph[] = rawPara.length > 0
                                        ? rawPara
                                        : rawSub.map((s: any) => ({
                                            sentences: [{ start: s.start, text: s.text }]
                                        }));

                                    return displayParagraphs.map((para, pIdx) => (
                                        <div key={pIdx} className="mb-10 text-justify group">
                                            {para.sentences?.map((sentence, sIdx) => {
                                                const nextS = para.sentences[sIdx + 1];
                                                // 粗略判断是否激活 (由于 iframe 无法回调时间，这里仅支持手动点击跳转)
                                                return (
                                                    <span
                                                        key={sIdx}
                                                        onClick={() => seek(sentence.start)}
                                                        className="inline-block cursor-pointer hover:text-blue-400 hover:bg-blue-400/10 rounded px-1 transition-all duration-200 text-lg leading-relaxed text-slate-300 decoration-blue-500/30 hover:underline decoration-2 underline-offset-4"
                                                        title={`跳转到 ${Math.floor(sentence.start / 60)}:${(sentence.start % 60).toFixed(0).padStart(2, '0')}`}
                                                    >
                                                        {sentence.text}
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
            </div>

            <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
      `}</style>
        </main>
    );
}
