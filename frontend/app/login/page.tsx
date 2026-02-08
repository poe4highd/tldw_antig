"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, ArrowRight, Chrome, ShieldCheck, Clock, LayoutGrid, Sparkles } from "lucide-react";
import { supabase } from "@/utils/supabase";
import { getSiteUrl } from "@/utils/api";

import { useTranslation } from "@/contexts/LanguageContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function LoginPage() {
    const { t, language } = useTranslation();
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleGuestEntry = () => {
        // Simulate entry to Dashboard
        window.location.href = "/dashboard?mode=guest";
    };

    const handleGoogleLogin = async () => {
        const siteUrl = getSiteUrl();
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${siteUrl}/dashboard`,
            },
        });

        if (error) {
            console.error("Error logging in with Google:", error.message);
            alert(t("login.loginFailed") + error.message);
        }
    };

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        const siteUrl = getSiteUrl();

        setLoading(true);
        setStatus(null);

        try {
            const { error } = await supabase.auth.signInWithOtp({
                email,
                options: {
                    emailRedirectTo: `${siteUrl}/dashboard`,
                },
            });

            if (error) throw error;

            setStatus({
                type: 'success',
                message: t("magicLinkSent")
            });
        } catch (error: any) {
            console.error("Error sending magic link:", error.message);
            setStatus({
                type: 'error',
                message: t("sendFailed") + error.message
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30 flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background Glows */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
            </div>

            {/* Language Switcher */}
            <div className="absolute top-8 right-8 z-30">
                <LanguageSwitcher />
            </div>

            {/* Top Logo (Navigator back to Home) */}
            <Link href="/" className="absolute top-12 left-1/2 -translate-x-1/2 flex items-center space-x-3 group z-20">
                <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-all duration-300">
                    <img src="/icon.png" alt="Read-Tube Logo" className="w-8 h-8" />
                </div>
                <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                    Read-Tube
                </span>
            </Link>

            <div className="relative z-10 w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                {/* Left side: Feature List */}
                <div className="hidden lg:flex flex-col space-y-8">
                    <div className="space-y-2">
                        <h2 className="text-4xl font-black tracking-tight text-white leading-tight">
                            {language === 'zh' ? "探索 Read-Tube 完整体验" : "Experience the Full Power"}
                        </h2>
                        <p className="text-slate-400 text-lg">
                            {language === 'zh' ? "登录后解锁更多专为深度学习者设计的功能" : "Unlock premium features designed for deep learners"}
                        </p>
                    </div>

                    <div className="grid grid-cols-1 gap-6">
                        {[
                            {
                                icon: <Clock className="w-6 h-6 text-indigo-400" />,
                                title: language === 'zh' ? "云端历史" : "Cloud History",
                                desc: language === 'zh' ? "永久保存您的所有音视频转录与阅读记录，随时随地回溯。" : "Save all transcriptions and reading history permanently."
                            },
                            {
                                icon: <LayoutGrid className="w-6 h-6 text-blue-400" />,
                                title: language === 'zh' ? "专属书架" : "Personal Library",
                                desc: language === 'zh' ? "构建个人音视频知识库，分类管理您的深度阅读内容。" : "Build your own video knowledge base and library."
                            },
                            {
                                icon: <Sparkles className="w-6 h-6 text-indigo-400" />,
                                title: language === 'zh' ? "优先处理" : "Priority Processing",
                                desc: language === 'zh' ? "注册用户享受更快的处理速度，极速转录，无需等待。" : "Registered users get faster transcription and analysis."
                            },
                            {
                                icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
                                title: language === 'zh' ? "跨端同步" : "Multi-device Sync",
                                desc: language === 'zh' ? "在网页、手机和平板上同步进度，学习不间断。" : "Keep your progress synced across all your devices."
                            }
                        ].map((feat, i) => (
                            <div key={i} className="flex gap-4 group cursor-default">
                                <div className="shrink-0 w-12 h-12 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-center group-hover:border-indigo-500/50 group-hover:bg-slate-800 transition-all">
                                    {feat.icon}
                                </div>
                                <div className="space-y-1">
                                    <h3 className="font-bold text-slate-100 group-hover:text-indigo-400 transition-colors">{feat.title}</h3>
                                    <p className="text-slate-500 text-sm leading-relaxed">{feat.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Card */}
                <div className="bg-slate-900/40 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-2xl shadow-black/50 overflow-hidden group relative">
                    <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent" />

                    <div className="text-center mb-10">
                        <h2 className="text-3xl font-bold tracking-tight mb-2">{t("login.title")}</h2>
                        <p className="text-slate-400 text-sm">{t("login.subtitle")}</p>
                    </div>

                    <div className="space-y-4">
                        {/* Google Login */}
                        <button
                            onClick={handleGoogleLogin}
                            className="w-full flex items-center justify-center space-x-3 py-4 bg-white text-slate-950 rounded-2xl font-bold text-sm hover:bg-slate-200 transition-all active:scale-[0.98] shadow-lg shadow-white/5"
                        >
                            <Chrome className="w-5 h-5" />
                            <span>{t("login.googleTitle")}</span>
                        </button>

                        <div className="relative py-4 flex items-center">
                            <div className="flex-grow border-t border-slate-800"></div>
                            <span className="flex-shrink mx-4 text-slate-500 text-xs font-bold uppercase tracking-widest">{t("login.or")}</span>
                            <div className="flex-grow border-t border-slate-800"></div>
                        </div>

                        {/* Email Login */}
                        <form onSubmit={handleEmailLogin} className="space-y-4">
                            <div className="relative group/input">
                                <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-slate-500 group-focus-within/input:text-indigo-400 transition-colors">
                                    <Mail className="w-5 h-5" />
                                </div>
                                <input
                                    type="email"
                                    placeholder={t("login.emailPlaceholder")}
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-slate-950/50 border border-slate-800 rounded-2xl py-4 pl-14 pr-5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/50 transition-all placeholder:text-slate-600"
                                />
                            </div>

                            {status && (
                                <div className={`text-sm px-4 py-3 rounded-xl border ${status.type === 'success'
                                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                    : 'bg-red-500/10 border-red-500/20 text-red-400'
                                    }`}>
                                    {status.message}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || !email}
                                className="w-full py-4 bg-slate-800 border border-slate-700 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-2xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center space-x-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                        <span>{t("login.sending")}</span>
                                    </>
                                ) : (
                                    <span>{t("login.sendMagicLink")}</span>
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Guest Entry */}
                    <div className="mt-10 pt-8 border-t border-slate-800/50 text-center">
                        <button
                            onClick={handleGuestEntry}
                            className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 font-bold text-sm group transition-colors"
                        >
                            <span>{t("login.guestEntry")}</span>
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Footer info */}
            <p className="mt-8 text-center text-slate-500 text-xs flex items-center justify-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500/50" />
                <span>{t("login.securityNote")}</span>
            </p>
        </main>
    );
}
