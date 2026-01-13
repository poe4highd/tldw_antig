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
        <main className="min-h-screen bg-slate-950 text-slate-50 p-4 md:p-12 font-sans">
            <div className="max-w-4xl mx-auto">
                <Link href="/" className="inline-flex items-center text-slate-400 hover:text-blue-400 mb-8 transition group">
                    <div className="bg-slate-900 p-2 rounded-lg mr-3 group-hover:bg-blue-600/20 transition-colors">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                    </div>
                    返回历史记录
                </Link>

                <div className="space-y-12">
                    <div className="space-y-6">
                        <h1 className="text-4xl font-black leading-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                            {result.title}
                        </h1>
                        <div className="aspect-video bg-black rounded-3xl overflow-hidden shadow-2xl border border-slate-800 ring-1 ring-slate-700/50">
                            <iframe
                                ref={iframeRef}
                                src={`https://www.youtube.com/embed/${result.youtube_id || result.url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/)?.[1] || ''}?enablejsapi=1`}
                                className="w-full h-full"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        </div>
                    </div>

                    <div className="bg-slate-900/40 rounded-[2.5rem] border border-slate-800 p-10 md:p-16 backdrop-blur-xl ring-1 ring-white/5">
                        <div className="max-w-none text-slate-200">
                            {(() => {
                                const rawPara = result.paragraphs || [];
                                const rawSub = result.subtitles || [];

                                const displayParagraphs: Paragraph[] = rawPara.length > 0
                                    ? rawPara
                                    : rawSub.map((s: any) => ({
                                        sentences: [{ start: s.start, text: s.text }]
                                    }));

                                return displayParagraphs.map((para, pIdx) => (
                                    <p key={pIdx} className="mb-12 text-justify last:mb-0">
                                        {para.sentences?.map((sentence, sIdx) => (
                                            <span
                                                key={sIdx}
                                                onClick={() => seek(sentence.start)}
                                                className="cursor-pointer hover:text-blue-400 hover:bg-blue-400/5 rounded transition-all duration-200 text-xl leading-[1.8] text-slate-300 decoration-blue-500/20 hover:underline decoration-2 underline-offset-8 px-0.5"
                                                title={`跳转到 ${Math.floor(sentence.start / 60)}:${(sentence.start % 60).toFixed(0).padStart(2, '0')}`}
                                            >
                                                {sentence.text}{" "}
                                            </span>
                                        ))}
                                    </p>
                                ));
                            })()}
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
