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

interface RawSubtitle {
    start: number;
    end: number;
    text: string;
}

interface Result {
    title: string;
    url: string;
    youtube_id?: string;
    media_path?: string;
    thumbnail?: string;
    paragraphs?: Paragraph[];
    subtitles?: any[];
    raw_subtitles?: RawSubtitle[];
}

export default function ResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [result, setResult] = useState<Result | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const iframeRef = useRef<HTMLIFrameElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [apiBase, setApiBase] = useState("");
    const [copyStatus, setCopyStatus] = useState("复制全文");

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
        if (!result || !result.youtube_id) return;

        const handleMessage = (event: MessageEvent) => {
            if (event.origin !== "https://www.youtube.com") return;
            try {
                const data = JSON.parse(event.data);
                if (data.event === "infoDelivery" && data.info && data.info.currentTime !== undefined) {
                    setCurrentTime(data.info.currentTime);
                }
            } catch (e) { }
        };

        window.addEventListener("message", handleMessage);
        const interval = setInterval(() => {
            if (iframeRef.current?.contentWindow) {
                iframeRef.current.contentWindow.postMessage(JSON.stringify({ event: "listening" }), "*");
            }
        }, 500);

        return () => {
            window.removeEventListener("message", handleMessage);
            clearInterval(interval);
        };
    }, [result]);

    useEffect(() => {
        if (!result || result.youtube_id) return;
        const media = videoRef.current || audioRef.current;
        if (!media) return;

        const onTimeUpdate = () => setCurrentTime(media.currentTime);
        media.addEventListener("timeupdate", onTimeUpdate);
        return () => media.removeEventListener("timeupdate", onTimeUpdate);
    }, [result]);

    const seek = (time: number) => {
        if (result?.youtube_id && iframeRef.current) {
            iframeRef.current.contentWindow?.postMessage(
                JSON.stringify({ event: "command", func: "seekTo", args: [time, true] }), "*"
            );
            iframeRef.current.contentWindow?.postMessage(
                JSON.stringify({ event: "command", func: "playVideo" }), "*"
            );
        } else {
            const media = videoRef.current || audioRef.current;
            if (media) {
                media.currentTime = time;
                media.play();
            }
        }
    };

    const formatTimestamp = (seconds: number, separator: string = ".") => {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}${separator}${ms.toString().padStart(3, '0')}`;
    };

    const generateSRT = (subs: RawSubtitle[]) => {
        return subs.map((s, i) =>
            `${i + 1}\n${formatTimestamp(s.start, ',')} --> ${formatTimestamp(s.end, ',')}\n${s.text}\n`
        ).join("\n");
    };

    const generateVTT = (subs: RawSubtitle[]) => {
        return "WEBVTT\n\n" + subs.map(s =>
            `${formatTimestamp(s.start)} --> ${formatTimestamp(s.end)}\n${s.text}\n`
        ).join("\n");
    };

    const downloadFile = (content: string, filename: string) => {
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    const getAllText = () => {
        if (!result?.paragraphs) return "";
        return result.paragraphs.map(p =>
            p.sentences.map(s => s.text).join(" ")
        ).join("\n\n");
    };

    const copyToClipboard = async () => {
        const textToCopy = getAllText();

        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(textToCopy);
            } else {
                // Fallback for non-secure contexts (e.g., HTTP IP address)
                const textArea = document.createElement("textarea");
                textArea.value = textToCopy;
                textArea.style.position = "absolute";
                textArea.style.left = "-9999px";
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
            }
            setCopyStatus("已复制！");
        } catch (err) {
            console.error("Copy failed", err);
            setCopyStatus("复制失败");
        }
        setTimeout(() => setCopyStatus("复制全文"), 2000);
    };

    if (!result) return (
        <div className="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    const isSentenceActive = (start: number, nextStart?: number) => {
        if (nextStart === undefined) return currentTime >= start;
        return currentTime >= start && currentTime < nextStart;
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-50 font-sans">
            <div className="flex flex-col lg:flex-row min-h-screen relative">

                <div className="w-full lg:w-[450px] xl:w-[500px] sticky top-0 lg:fixed lg:left-0 lg:top-0 lg:bottom-0 bg-slate-900 lg:border-r border-b lg:border-b-0 border-slate-800 p-4 lg:p-6 flex flex-col z-40 shadow-xl lg:shadow-none">
                    <Link href="/" className="inline-flex items-center text-slate-400 hover:text-blue-400 mb-3 lg:mb-6 transition group w-fit text-xs lg:text-sm">
                        <div className="bg-slate-800 p-1 lg:p-1.5 rounded-md mr-2 lg:mr-3 group-hover:bg-blue-600/20 transition-colors">
                            <svg className="w-3 h-3 lg:w-3.5 lg:h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </div>
                        返回列表
                    </Link>

                    <h1 className="hidden lg:block text-xl font-bold leading-tight text-slate-100 mb-6 px-1">
                        {result.title}
                    </h1>

                    <div className="aspect-video bg-black rounded-lg lg:rounded-xl overflow-hidden shadow-2xl border border-white/5 ring-1 ring-white/5 mb-2 lg:mb-8 relative">
                        {result.youtube_id ? (
                            <iframe
                                ref={iframeRef}
                                src={`https://www.youtube.com/embed/${result.youtube_id}?enablejsapi=1&autoplay=1`}
                                className="w-full h-full"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />
                        ) : (
                            result.media_path?.match(/\.(mp4|mov|webm|mkv)$/i) ? (
                                <video
                                    ref={videoRef}
                                    src={`${apiBase}/media/${result.media_path}`}
                                    poster={result.thumbnail && !result.thumbnail.startsWith('#') && !result.thumbnail.startsWith('http') ? `${apiBase}/media/${result.thumbnail}` : (result.thumbnail?.startsWith('http') ? result.thumbnail : undefined)}
                                    controls
                                    autoPlay
                                    className="w-full h-full"
                                />
                            ) : (
                                <div className="w-full h-full flex flex-col">
                                    <div className="flex-1 flex items-center justify-center" style={{ backgroundColor: result.thumbnail?.startsWith('#') ? result.thumbnail : '#1e293b' }}>
                                        {result.thumbnail && !result.thumbnail.startsWith('#') && (
                                            <img
                                                src={result.thumbnail.startsWith('http') ? result.thumbnail : `${apiBase}/media/${result.thumbnail}`}
                                                alt="thumbnail"
                                                className="absolute inset-0 w-full h-full object-cover opacity-30"
                                            />
                                        )}
                                        <svg className="w-20 h-20 text-white/20 relative z-10" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 3v11.13a3.345 3.345 0 102 3.29V5.47l8-1.6v6.26a3.345 3.345 0 102 3.29V3z" />
                                        </svg>
                                    </div>
                                    <div className="p-4 bg-slate-900">
                                        <audio
                                            ref={audioRef}
                                            src={`${apiBase}/media/${result.media_path}`}
                                            controls
                                            autoPlay
                                            className="w-full h-8"
                                        />
                                    </div>
                                </div>
                            )
                        )}
                    </div>

                    <h1 className="lg:hidden block text-sm font-bold leading-tight text-slate-100 truncate mb-1">
                        {result.title}
                    </h1>

                    {/* Action Buttons (Desktop Sidebar) */}
                    <div className="hidden lg:grid grid-cols-2 gap-2 mt-4">
                        <button onClick={copyToClipboard} className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 p-3 rounded-xl text-[11px] font-bold transition-colors">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                            {copyStatus}
                        </button>
                        <button onClick={() => downloadFile(getAllText(), `${result.title}.txt`)} className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 p-3 rounded-xl text-[11px] font-bold transition-colors">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                            下载正文
                        </button>
                        <button onClick={() => result.raw_subtitles && downloadFile(generateSRT(result.raw_subtitles), `${result.title}.srt`)} className="flex items-center justify-center gap-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 p-3 rounded-xl text-[10px] font-bold text-blue-400 transition-colors">
                            SRT 导出
                        </button>
                        <button onClick={() => result.raw_subtitles && downloadFile(generateVTT(result.raw_subtitles), `${result.title}.vtt`)} className="flex items-center justify-center gap-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 p-3 rounded-xl text-[10px] font-bold text-blue-400 transition-colors">
                            VTT 导出
                        </button>
                    </div>

                    <div className="hidden lg:block p-4 bg-slate-950/20 rounded-xl border border-slate-800/50 mt-4">
                        <p className="text-[11px] text-slate-500 leading-relaxed italic">
                            💡 高亮显示为当前播放内容。点击文字可快速跳转。
                        </p>
                    </div>

                    <div className="pt-4 mt-auto border-t border-slate-800/50 lg:flex hidden justify-between items-center text-[10px] text-slate-600 font-mono">
                        <span>AUDIO QUICK READER v2.5</span>
                        <span className="text-blue-500/50 px-2 py-0.5 border border-blue-500/20 rounded">USER</span>
                    </div>
                </div>

                <div className="lg:ml-[450px] xl:ml-[500px] flex-1 min-h-screen bg-slate-950">
                    <div className="max-w-3xl mx-auto p-6 lg:p-20">
                        {/* Mobile Action Buttons */}
                        <div className="lg:hidden flex gap-2 mb-8 overflow-x-auto pb-2 no-scrollbar">
                            <button onClick={copyToClipboard} className="shrink-0 flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-full text-xs font-bold whitespace-nowrap">
                                {copyStatus}
                            </button>
                            <button onClick={() => downloadFile(getAllText(), `${result.title}.txt`)} className="shrink-0 flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-full text-xs font-bold whitespace-nowrap">
                                下载正文
                            </button>
                            <button onClick={() => result.raw_subtitles && downloadFile(generateSRT(result.raw_subtitles), `${result.title}.srt`)} className="shrink-0 flex items-center gap-2 bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-full text-xs font-bold whitespace-nowrap">
                                SRT
                            </button>
                        </div>

                        <div className="prose prose-invert max-w-none">
                            {(() => {
                                const rawPara = result.paragraphs || [];
                                const displayParagraphs = rawPara;
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
                                                    className={`cursor-pointer rounded transition-all duration-300 text-[14.5px] lg:text-[15.5px] leading-[1.65] px-0.5 ${active
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
        </main>
    );
}
