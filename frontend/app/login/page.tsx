"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, ArrowRight, Chrome, ShieldCheck } from "lucide-react";
import { supabase } from "@/utils/supabase";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleGuestEntry = () => {
        // 模拟进入 Dashboard
        window.location.href = "/dashboard?mode=guest";
    };

    const handleGoogleLogin = async () => {
        const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin;
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${siteUrl}/dashboard`,
            },
        });

        if (error) {
            console.error("Error logging in with Google:", error.message);
            alert("登录失败: " + error.message);
        }
    };

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin;

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
                message: "神奇链接已发送！请检查您的收件箱。"
            });
        } catch (error: any) {
            console.error("Error sending magic link:", error.message);
            setStatus({
                type: 'error',
                message: "发送失败: " + error.message
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

            {/* Top Logo (Navigator back to Home) */}
            <Link href="/" className="absolute top-12 left-1/2 -translate-x-1/2 flex items-center space-x-3 group z-20">
                <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-all duration-300">
                    <img src="/icon.png" alt="Read-Tube Logo" className="w-8 h-8" />
                </div>
                <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                    Read-Tube
                </span>
            </Link>

            <div className="relative z-10 w-full max-w-md">
                {/* Main Card */}
                <div className="bg-slate-900/40 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-2xl shadow-black/50 overflow-hidden group">
                    <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent" />

                    <div className="text-center mb-10">
                        <h2 className="text-3xl font-bold tracking-tight mb-2">欢迎回来</h2>
                        <p className="text-slate-400 text-sm">选择您喜欢的方式解锁知识阅读革命</p>
                    </div>

                    <div className="space-y-4">
                        {/* Google Login */}
                        <button
                            onClick={handleGoogleLogin}
                            className="w-full flex items-center justify-center space-x-3 py-4 bg-white text-slate-950 rounded-2xl font-bold text-sm hover:bg-slate-200 transition-all active:scale-[0.98] shadow-lg shadow-white/5"
                        >
                            <Chrome className="w-5 h-5" />
                            <span>使用 Google 账号继续</span>
                        </button>

                        <div className="relative py-4 flex items-center">
                            <div className="flex-grow border-t border-slate-800"></div>
                            <span className="flex-shrink mx-4 text-slate-500 text-xs font-bold uppercase tracking-widest">或者</span>
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
                                    placeholder="电子邮箱地址"
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
                                        <span>正在发送...</span>
                                    </>
                                ) : (
                                    <span>发送神奇登录链接</span>
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
                            <span>以访客身份快速体验 (Guest Entry)</span>
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </div>

                {/* Footer info */}
                <p className="mt-8 text-center text-slate-500 text-xs flex items-center justify-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-500/50" />
                    <span>您的数据安全受高级加密保护</span>
                </p>
            </div>
        </main>
    );
}
