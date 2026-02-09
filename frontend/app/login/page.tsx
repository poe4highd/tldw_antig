"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, ArrowRight, Chrome, ShieldCheck, Clock, LayoutGrid, Sparkles, FileUp } from "lucide-react";
import { supabase } from "@/utils/supabase";
import { getSiteUrl } from "@/utils/api";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

import { useTranslation } from "@/contexts/LanguageContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTheme } from "@/contexts/ThemeContext";

export default function LoginPage() {
    const { t, language } = useTranslation();
    const { theme } = useTheme();
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
    const router = useRouter();

    useEffect(() => {
        const checkSession = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                router.replace("/dashboard");
            }
        };
        checkSession();
    }, [router]);

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
                message: t("login.magicLinkSent")
            });
        } catch (error: any) {
            console.error("Error sending magic link:", error.message);
            setStatus({
                type: 'error',
                message: t("login.sendFailed") + error.message
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-transparent text-foreground font-sans selection:bg-indigo-500/30 flex flex-col items-center justify-center p-6 relative overflow-hidden transition-colors duration-300">
            {/* Background Glows */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
            </div>

            {/* Language Switcher & Theme Toggle */}
            <div className="absolute top-8 right-8 z-30 flex items-center gap-3">
                <LanguageSwitcher />
            </div>

            {/* Top Logo (Navigator back to Home) */}
            <Link href="/" className="absolute top-12 left-1/2 -translate-x-1/2 flex items-center space-x-3 group z-20">
                <div className="p-2 bg-card-bg border border-card-border rounded-xl group-hover:border-indigo-500/50 transition-all duration-300 shadow-xl">
                    <img src="/icon.png" alt="Read-Tube Logo" className="w-8 h-8" />
                </div>
                <span className={cn(
                    "text-2xl font-black tracking-tighter",
                    theme === 'dark' ? "bg-gradient-to-r from-foreground to-slate-400 bg-clip-text text-transparent" : "text-indigo-600"
                )}>
                    Read-Tube
                </span>
            </Link>

            <div className="relative z-10 w-full max-w-4xl grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                {/* Left side: Feature List */}
                <div className="hidden lg:flex flex-col space-y-8">
                    <div className="space-y-2">
                        <h2 className="text-4xl font-black tracking-tight leading-tight">
                            {language === 'zh' ? "探索 Read-Tube 完整体验" : "Experience the Full Power"}
                        </h2>
                        <p className="text-slate-500 text-lg">
                            {language === 'zh' ? "登录后解锁更多专为深度学习者设计的功能" : "Unlock premium features designed for deep learners"}
                        </p>
                    </div>

                    <div className="grid grid-cols-1 gap-6">
                        {[
                            {
                                icon: <FileUp className="w-6 h-6 text-indigo-400" />,
                                title: t("login.featureSubmitTitle"),
                                desc: t("login.featureSubmitDesc")
                            },
                            {
                                icon: <LayoutGrid className="w-6 h-6 text-blue-400" />,
                                title: t("login.featurePersonalTitle"),
                                desc: t("login.featurePersonalDesc")
                            },
                            {
                                icon: <Clock className="w-6 h-6 text-indigo-400" />,
                                title: language === 'zh' ? "云端历史" : "Cloud History",
                                desc: language === 'zh' ? "永久保存您的所有音视频转录与阅读记录，随时随地回溯。" : "Save all transcriptions and reading history permanently."
                            },
                            {
                                icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
                                title: language === 'zh' ? "跨端同步" : "Multi-device Sync",
                                desc: language === 'zh' ? "在网页、手机和平板上同步进度，学习不间断。" : "Keep your progress synced across all your devices."
                            }
                        ].map((feat, i) => (
                            <div key={i} className="flex gap-4 group cursor-default">
                                <div className="shrink-0 w-12 h-12 bg-card-bg border border-card-border rounded-2xl flex items-center justify-center group-hover:border-indigo-500/50 group-hover:bg-slate-100 dark:group-hover:bg-slate-800 transition-all shadow-lg">
                                    {feat.icon}
                                </div>
                                <div className="space-y-1">
                                    <h3 className="font-bold text-foreground group-hover:text-indigo-400 transition-colors">{feat.title}</h3>
                                    <p className="text-slate-500 text-sm leading-relaxed">{feat.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Card */}
                <div className="bg-card-bg backdrop-blur-2xl border border-card-border rounded-[2.5rem] p-10 shadow-2xl shadow-black/5 flex flex-col group relative">
                    <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent" />

                    <div className="text-center mb-10">
                        <h2 className="text-3xl font-bold tracking-tight mb-2 text-foreground">{t("login.title")}</h2>
                        <p className="text-slate-500 text-sm">{t("login.subtitle")}</p>
                    </div>

                    <div className="space-y-4">
                        {/* Google Login */}
                        <button
                            onClick={handleGoogleLogin}
                            className="w-full flex items-center justify-center space-x-3 py-4 bg-foreground text-background rounded-2xl font-bold text-sm hover:opacity-90 transition-all active:scale-[0.98] shadow-lg shadow-black/5"
                        >
                            <Chrome className="w-5 h-5" />
                            <span>{t("login.googleTitle")}</span>
                        </button>

                        <div className="relative py-4 flex items-center">
                            <div className="flex-grow border-t border-card-border"></div>
                            <span className="flex-shrink mx-4 text-slate-500 text-xs font-bold uppercase tracking-widest">{t("login.or")}</span>
                            <div className="flex-grow border-t border-card-border"></div>
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
                                    className="w-full bg-background/50 border border-card-border rounded-2xl py-4 pl-14 pr-5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/50 transition-all placeholder:text-slate-600 text-foreground"
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
                                className="w-full py-4 bg-card-bg border border-card-border hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed text-foreground rounded-2xl font-bold text-sm transition-all active:scale-[0.98] flex items-center justify-center space-x-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                                        <span>{t("login.sending")}</span>
                                    </>
                                ) : (
                                    <span>{t("login.sendMagicLink")}</span>
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Guest Entry */}
                    <div className="mt-10 pt-8 border-t border-card-border text-center">
                        <button
                            onClick={handleGuestEntry}
                            className="inline-flex items-center space-x-2 text-indigo-500 hover:text-indigo-400 font-bold text-sm group transition-colors"
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
