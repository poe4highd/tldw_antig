"use client";

import React from "react";
import Link from "next/link";

export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      {/* Background Glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute -bottom-[10%] left-[20%] w-[50%] h-[50%] bg-emerald-600/5 blur-[120px] rounded-full" />
      </div>

      <nav className="relative z-10 max-w-7xl mx-auto px-6 py-8 flex items-center justify-between">
        <div className="flex items-center space-x-3 group">
          <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-colors duration-300">
            <img src="/icon.png" alt="Read-Tube Logo" className="w-8 h-8" />
          </div>
          <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Read-Tube
          </span>
        </div>
        <div className="flex items-center space-x-6">
          <Link href="/dev-home" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
            开发测试
          </Link>
          <button className="px-5 py-2.5 bg-white text-slate-950 rounded-full text-sm font-bold hover:bg-slate-200 transition-all active:scale-95 shadow-lg shadow-white/5">
            立即登录
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-20 pb-32 text-center">
        <div className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold tracking-widest uppercase mb-8 animate-fade-in">
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          AI 驱动的阅读革命
        </div>

        <h1 className="text-6xl md:text-8xl font-black tracking-tight mb-8 max-w-4xl mx-auto leading-[1.1]">
          将视频转化为
          <span className="block bg-gradient-to-r from-indigo-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent italic">
            深度阅读体验
          </span>
        </h1>

        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-12 leading-relaxed">
          Read-Tube 利用最先进的 AI 技术，为您提供 YouTube、视频及音频内容的极速转化。
          不仅仅是转录，更是深度的知识提炼与沉浸式阅读。
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl font-bold text-lg hover:shadow-[0_0_40px_rgba(79,70,229,0.4)] transition-all active:scale-95">
            开始免费阅读
          </button>
          <button className="w-full sm:w-auto px-8 py-4 bg-slate-900 border border-slate-800 text-white rounded-2xl font-bold text-lg hover:bg-slate-800/50 transition-all">
            了解功能详情
          </button>
        </div>

        {/* Floating Abstract Elements */}
        <div className="mt-24 relative max-w-5xl mx-auto aspect-[16/9] rounded-3xl border border-slate-800 bg-slate-900/50 backdrop-blur-md overflow-hidden shadow-2xl group">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-50" />
          <div className="flex h-full items-center justify-center">
            <div className="text-slate-600 font-mono text-sm group-hover:text-slate-500 transition-colors">
              [ 产品预览图占位符 ]
            </div>
          </div>
          {/* Glossy overlay */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-24 border-t border-slate-900">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 rounded-3xl bg-slate-900/40 border border-slate-800 hover:border-indigo-500/30 transition-all group">
            <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-4">视频转速读</h3>
            <p className="text-slate-400 leading-relaxed">
              将冗长的视频演讲自动整理为结构化的精美文档，让您用传统阅读的效率吸收动态影像信息。
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-slate-900/40 border border-slate-800 hover:border-blue-500/30 transition-all group">
            <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-4">AI 智能总结</h3>
            <p className="text-slate-400 leading-relaxed">
              基于最新的大语言模型，自动提炼视频中的核心观点、金句和思维导图，精准捕捉每一处精彩。
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-slate-900/40 border border-slate-800 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-4">全格式支持</h3>
            <p className="text-slate-400 leading-relaxed">
              无论是 YouTube 链接、PODCAST 音频还是本地录像文件，Read-Tube 都能为您提供一致的优质体验。
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 max-w-7xl mx-auto px-6 py-12 border-t border-slate-900 text-center text-slate-500 text-sm">
        <p>© 2026 Read-Tube. All rights reserved.</p>
        <div className="mt-4 flex items-center justify-center space-x-6">
          <Link href="/dev-home" className="hover:text-white transition-colors">开发者入口</Link>
          <a href="#" className="hover:text-white transition-colors">服务条款</a>
          <a href="#" className="hover:text-white transition-colors">隐私政策</a>
        </div>
      </footer>
    </main>
  );
}
