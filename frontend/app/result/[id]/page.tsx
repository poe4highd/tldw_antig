"use client";

import { useState, useRef, useEffect, use } from "react";
import Link from "next/link";

interface Paragraph {
    start: number;
    text: string;
}

interface Result {
    title: string;
    media_path?: string;
    media_url?: string;
    paragraphs?: Paragraph[];
    subtitles?: Paragraph[];
}

export default function ResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [result, setResult] = useState<Result | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const videoRef = useRef<HTMLVideoElement>(null);
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
        if (videoRef.current) {
            videoRef.current.currentTime = time;
            videoRef.current.play();
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
                    <div className="lg:col-span-7 space-y-6">
                        <h1 className="text-3xl font-bold leading-tight">{result.title}</h1>
                        <div className="aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-slate-800 sticky top-8">
                            <video
                                ref={videoRef}
                                src={`${apiBase}/media/${result.media_path || result.media_url}`}
                                controls
                                className="w-full h-full"
                                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                            />
                        </div>
                    </div>

                    {/* Right: Reader Section */}
                    <div className="lg:col-span-5 h-[calc(100vh-8rem)] flex flex-col pt-12 lg:pt-0">
                        <div className="bg-slate-900/50 rounded-3xl border border-slate-800 p-8 flex-1 overflow-y-auto custom-scrollbar backdrop-blur-sm">
                            <div className="prose prose-invert max-w-none space-y-8">
                                {(() => {
                                    const paragraphs = Array.isArray(result.paragraphs)
                                        ? result.paragraphs
                                        : Array.isArray(result.subtitles)
                                            ? result.subtitles
                                            : [];

                                    return paragraphs.map((p, i) => {
                                        const nextStart = paragraphs[i + 1]?.start || 999999;
                                        const isActive = currentTime >= p.start && currentTime < nextStart;

                                        return (
                                            <div
                                                key={i}
                                                onClick={() => seek(p.start)}
                                                className={`group cursor-pointer transition-all duration-300 p-4 rounded-xl -mx-4 ${isActive
                                                    ? "bg-blue-600/10 border-l-4 border-blue-500 shadow-lg shadow-blue-500/5"
                                                    : "hover:bg-slate-800/50 border-l-4 border-transparent"
                                                    }`}
                                            >
                                                <div className="flex items-center gap-3 mb-2 opacity-40 group-hover:opacity-100 transition">
                                                    <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded">
                                                        {new Date(p.start * 1000).toISOString().substr(14, 5)}
                                                    </span>
                                                    <div className="h-px flex-1 bg-slate-700"></div>
                                                </div>
                                                <p className={`text-lg leading-relaxed transition-colors ${isActive ? "text-blue-50" : "text-slate-300 group-hover:text-slate-100"
                                                    }`}>
                                                    {p.text}
                                                </p>
                                            </div>
                                        );
                                    });
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
