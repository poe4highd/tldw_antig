"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  LayoutGrid,
  List,
  Search,
  Youtube,
  ArrowRight,
  Menu,
  Eye,
  Calendar,
  User,
  Clock,
  Sparkles,
  Settings,
  TrendingUp,
  Columns2,
  Moon,
  Sun
} from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTheme } from "@/contexts/ThemeContext";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { supabase } from "@/utils/supabase";
import { getApiBase } from "@/utils/api";
import { useTranslation } from "@/contexts/LanguageContext";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ExploreItem {
  id: string;
  title: string;
  thumbnail: string;
  channel?: string;
  channel_id?: string;
  channel_avatar?: string;
  summary?: string;
  keywords?: string[];
  date: string;
  views: number;
}

export default function MarketingPage() {
  const { t, language } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const [viewMode, setViewMode] = useState<"thumb" | "text-single" | "text-double">("text-double");
  const [searchQuery, setSearchQuery] = useState("");
  const [items, setItems] = useState<ExploreItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(80);
  const [trendingKeywords, setTrendingKeywords] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Read preference
    const saved = localStorage.getItem("rt-explore-view-mode");
    if (saved === "thumb" || saved === "text-single" || saved === "text-double") {
      setViewMode(saved as any);
    } else if (saved === "text") {
      // Migrate old setting
      setViewMode("text-single");
    }

    const fetchUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
    };
    fetchUser();

    fetchTrending();
  }, []);

  useEffect(() => {
    fetchExplore(page, searchQuery);
  }, [page, searchQuery, limit]);

  const fetchExplore = async (pageNum: number, query: string) => {
    setIsLoading(true);
    try {
      const apiBase = getApiBase();
      const url = new URL(`${apiBase}/explore`);
      url.searchParams.append("page", pageNum.toString());
      url.searchParams.append("limit", limit.toString());
      if (query) url.searchParams.append("q", query);

      const response = await fetch(url.toString());
      const data = await response.json();
      if (data.items) {
        setItems(data.items);
        setTotal(data.total || data.items.length);
      }
    } catch (error) {
      console.error("Failed to fetch explore:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTrending = async () => {
    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/trending-keywords`);
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setTrendingKeywords(data);
      } else {
        // Fallback
        setTrendingKeywords(["AI", "Finance", "Productivity", "Tech", "Education", "Crypto"]);
      }
    } catch (error) {
      console.error("Failed to fetch trending:", error);
      setTrendingKeywords(["AI", "Finance", "Productivity", "Tech", "Education", "Crypto"]);
    }
  };

  const toggleViewMode = (mode: "thumb" | "text-single" | "text-double") => {
    setViewMode(mode);
    localStorage.setItem("rt-explore-view-mode", mode);
  };

  const totalPages = Math.ceil(total / limit);

  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    setPage(1);
  };

  const handleKeywordClick = (kw: string) => {
    const newVal = searchQuery === kw ? "" : kw;
    setSearchQuery(newVal);
    setPage(1);
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr;
    }
  };

  const getAvatarUrl = (channelName: string) => {
    if (!channelName) return null;
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(channelName)}&background=random&color=fff&size=64&bold=true`;
  };

  const getChannelColor = (channelId: string | undefined, channelName: string | undefined): string => {
    const seed = channelId || channelName || "default";
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = seed.charCodeAt(i) + ((hash << 5) - hash);
    }
    const h = Math.abs(hash) % 360;
    return `hsl(${h}, 70%, 60%)`;
  };

  return (
    <div className="min-h-screen bg-transparent text-foreground font-sans selection:bg-indigo-500/30">
      <main className="max-w-7xl mx-auto p-4 md:p-8 relative">
        {/* Background Glows */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
          <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
        </div>

        {/* Desktop & Mobile Top Header (Settings/Lang) */}
        <div className="absolute top-4 right-4 md:top-8 md:right-8 z-20 flex items-center gap-3">
          <LanguageSwitcher />
          <Link
            href="/pending"
            className="p-2.5 bg-slate-900/60 dark:bg-slate-900/60 light:bg-slate-100/80 backdrop-blur-md border border-slate-800 dark:border-slate-800 light:border-slate-200 rounded-xl text-slate-400 dark:text-slate-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:border-indigo-500/50 transition-all shadow-lg group"
            title="Queue / 待处理"
          >
            <Clock className="w-5 h-5 group-hover:animate-pulse" />
          </Link>
          <button
            onClick={toggleTheme}
            className="p-2.5 bg-slate-900/60 dark:bg-slate-900/60 light:bg-slate-100/80 backdrop-blur-md border border-slate-800 dark:border-slate-800 light:border-slate-200 rounded-xl text-slate-400 dark:text-slate-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:border-indigo-500/50 transition-all shadow-lg"
            title={theme === 'dark' ? "Light Mode / 浅色模式" : "Dark Mode / 深色模式"}
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <Link
            href="/settings"
            className="p-2.5 bg-slate-900/60 dark:bg-slate-900/60 light:bg-slate-100/80 backdrop-blur-md border border-slate-800 dark:border-slate-800 light:border-slate-200 rounded-xl text-slate-400 dark:text-slate-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:border-indigo-500/50 transition-all shadow-lg"
            title={t("common.settings")}
          >
            <Settings className="w-5 h-5" />
          </Link>
        </div>



        {/* Compact Hero Section */}
        <div className="relative z-10 mb-6">
          <div className="flex items-center gap-4 mb-2 flex-wrap">
            <Link href="/" className="flex items-center space-x-3 group animate-in fade-in slide-in-from-left-4 duration-700">
              <div className="p-1.5 bg-slate-900 dark:bg-slate-900 light:bg-slate-100 border border-slate-800 dark:border-slate-800 light:border-slate-200 rounded-lg group-hover:border-indigo-500/50 transition-all duration-300 shadow-xl">
                <img src="/icon.png" alt="Read-Tube Logo" className="w-5 h-5" />
              </div>
              <span className="text-xl font-black tracking-tighter bg-gradient-to-r from-foreground to-slate-400 bg-clip-text text-transparent">
                {t("marketing.title")}
              </span>
            </Link>
            <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />
            <div className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[9px] font-bold tracking-widest uppercase">
              <Sparkles className="w-2.5 h-2.5 mr-1" />
              {t("marketing.tagline")}
            </div>

            {/* Integrated Search Bar */}
            <div className="relative flex-grow max-w-md group ml-4">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-slate-600 group-focus-within:text-indigo-400 transition-colors">
                <Search className="w-3.5 h-3.5" />
              </div>
              <input
                type="text"
                placeholder={t("explore.searchPlaceholder")}
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full bg-card-bg border border-card-border rounded-full py-1.5 pl-9 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/40 placeholder:text-slate-500 transition-all backdrop-blur-sm"
              />
            </div>
          </div>
          <div className="flex items-end justify-between gap-4">
            <div className="flex-grow">
              <h1 className="text-xl md:text-2xl lg:text-3xl font-black tracking-tight mb-1 bg-gradient-to-r from-foreground via-foreground to-slate-500 bg-clip-text text-transparent leading-[0.8]">
                {t("marketing.heroTitle1")}{t("marketing.heroTitle2")}
              </h1>
              <p className="text-slate-500 dark:text-slate-500 light:text-slate-600 text-sm md:text-base font-medium leading-snug hidden sm:block">
                {t("marketing.description")}
              </p>
            </div>

            {/* Compact View Switcher */}
            <div className="flex items-center bg-card-bg border border-card-border p-1 rounded-xl shadow-inner mb-2">
              <button
                onClick={() => toggleViewMode("text-double")}
                className={cn(
                  "p-2 rounded-lg transition-all duration-300",
                  viewMode === "text-double" ? "bg-foreground text-background shadow-lg" : "text-slate-500 dark:text-slate-600 light:text-slate-400 hover:text-indigo-400"
                )}
                title={t("explore.modeText") + " (2)"}
              >
                <Columns2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => toggleViewMode("text-single")}
                className={cn(
                  "p-2 rounded-lg transition-all duration-300",
                  viewMode === "text-single" ? "bg-foreground text-background shadow-lg" : "text-slate-500 dark:text-slate-600 light:text-slate-400 hover:text-indigo-400"
                )}
                title={t("explore.modeText") + " (1)"}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => toggleViewMode("thumb")}
                className={cn(
                  "p-2 rounded-lg transition-all duration-300",
                  viewMode === "thumb" ? "bg-foreground text-background shadow-lg" : "text-slate-500 dark:text-slate-600 light:text-slate-400 hover:text-indigo-400"
                )}
                title={t("explore.modeThumb")}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>


        {/* Auto-Scrolling Keywords */}
        <div className="relative z-10 mb-8 overflow-hidden group border-y border-card-border py-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center whitespace-nowrap animate-scroll-slow hover:[animation-play-state:paused] cursor-pointer">
              {/* Duplicate array for seamless loop */}
              {[...trendingKeywords, ...trendingKeywords].map((kw, idx) => (
                <button
                  key={`${kw}-${idx}`}
                  onClick={() => handleKeywordClick(kw)}
                  className={cn(
                    "mx-2 px-4 py-1.5 rounded-full border text-[10px] font-bold transition-all duration-300",
                    searchQuery === kw
                      ? "bg-indigo-500 border-indigo-400 text-white shadow-lg shadow-indigo-500/20"
                      : "bg-card-bg border-card-border text-slate-500 dark:text-slate-400 light:text-slate-600 hover:border-indigo-500/50 hover:text-indigo-400"
                  )}
                >
                  {kw}
                </button>
              ))}
            </div>
          </div>
          {/* Gradients to mask edges */}
          <div className="absolute top-0 left-0 h-full w-20 bg-gradient-to-r from-background to-transparent pointer-events-none z-10" />
          <div className="absolute top-0 right-0 h-full w-20 bg-gradient-to-l from-background to-transparent pointer-events-none z-10" />
        </div>

        {/* Content */}
        <div className="relative z-10">
          {isLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-12 bg-slate-900/40 rounded-xl animate-pulse border border-slate-800/50" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="py-20 text-center bg-slate-900/20 border border-dashed border-slate-800 rounded-[2rem] flex flex-col items-center">
              <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center mb-6 text-slate-700">
                <Search className="w-8 h-8" />
              </div>
              <p className="text-slate-400 font-bold text-lg">{t("explore.empty")}</p>
            </div>
          ) : viewMode === "text-single" || viewMode === "text-double" ? (
            <div className={cn(
              "gap-1.5",
              viewMode === "text-double" ? "grid grid-cols-1 lg:grid-cols-2" : "flex flex-col space-y-1"
            )}>
              {items.map((item) => (
                <Link
                  key={item.id}
                  href={`/result/${item.id}`}
                  className="group flex items-start sm:items-center gap-2 sm:gap-3 p-1.5 sm:p-2.5 bg-card-bg border border-card-border rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900/40 hover:border-indigo-500/20 transition-all duration-300"
                >
                  {/* Thumbnail for Mobile/List */}
                  <div className="shrink-0 w-24 sm:w-auto h-auto sm:h-auto">
                    <div className="aspect-video sm:hidden rounded-md overflow-hidden bg-slate-900 border border-slate-800/50 mb-0">
                      <img src={item.thumbnail} alt={item.title} className="w-full h-full object-cover" />
                    </div>
                    <div
                      className="hidden sm:flex w-6 h-6 rounded-full items-center justify-center p-[1px] shadow-sm group-hover:scale-105 transition-transform"
                      style={{ backgroundColor: getChannelColor(item.channel_id, item.channel) }}
                    >
                      <div className="w-full h-full rounded-full overflow-hidden border border-slate-950 bg-slate-800">
                        {item.channel_avatar ? (
                          <img src={item.channel_avatar} alt={item.channel} className="w-full h-full object-cover" />
                        ) : (
                          <img src={getAvatarUrl(item.channel || "YT")!} alt={item.channel} className="w-full h-full object-cover" />
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex-grow min-w-0 flex flex-col justify-center h-full">
                    <h3 className="font-bold text-sm sm:text-base text-foreground group-hover:text-indigo-400 transition-colors line-clamp-2 sm:truncate leading-tight mb-1 sm:mb-0">
                      {item.title}
                    </h3>
                    <div className="flex sm:hidden items-center gap-3 text-[10px] font-black text-slate-600">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5" />
                        {formatDate(item.date)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-2.5 h-2.5" />
                        {item.views.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="shrink-0 hidden sm:flex items-center gap-4 pr-1">
                    <div className="flex items-center gap-1 text-[9px] font-black text-slate-500 group-hover:text-slate-400">
                      <Eye className="w-2.5 h-2.5" />
                      {item.views.toLocaleString()}
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-800 group-hover:text-indigo-400 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {items.map((item) => (
                <div key={item.id} className="group relative bg-slate-900/30 border border-slate-800/50 rounded-2xl overflow-hidden hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                  <div className="aspect-video relative overflow-hidden">
                    <img src={item.thumbnail} alt={item.title} className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700" />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />

                    <div className="absolute top-4 left-4 p-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10">
                      <Youtube className="w-4 h-4 text-red-500" />
                    </div>
                  </div>

                  <div className="p-4">
                    <h3 className="font-bold text-lg leading-[0.85] line-clamp-2 mb-3 h-10 group-hover:text-indigo-400 transition-colors uppercase tracking-tight">
                      {item.title}
                    </h3>

                    <div className="flex items-center justify-between pt-3 border-t border-slate-800/50">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-7 h-7 rounded-full flex items-center justify-center p-[1.5px]"
                          style={{ backgroundColor: getChannelColor(item.channel_id, item.channel) }}
                        >
                          <div className="w-full h-full rounded-full overflow-hidden border border-slate-950 bg-slate-800">
                            <img src={item.channel_avatar || getAvatarUrl(item.channel || "YT")!} className="w-full h-full object-cover" />
                          </div>
                        </div>
                        <span className="text-[10px] font-bold text-slate-400 truncate max-w-[80px]">
                          {item.channel || "Creator"}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] font-bold text-slate-600">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {item.views}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Link href={`/result/${item.id}`} className="absolute inset-0 z-10" aria-label="View report" />
                </div>
              ))}
            </div>
          )}

          {/* Pagination Controls - Always show the row to provide the limit selector */}
          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-8 py-6 border-y border-slate-900/30">
            {totalPages > 1 && (
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1 || isLoading}
                  className="px-4 py-2 bg-card-bg border border-card-border rounded-xl text-xs font-bold text-slate-500 dark:text-slate-400 light:text-slate-600 hover:text-indigo-500 hover:border-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {language === 'zh' ? '上一页' : 'Previous'}
                </button>
                <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest min-w-[100px] text-center">
                  {language === 'zh' ? `第 ${page} / ${totalPages} 页` : `Page ${page} of ${totalPages}`}
                </div>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages || isLoading}
                  className="px-4 py-2 bg-card-bg border border-card-border rounded-xl text-xs font-bold text-slate-500 dark:text-slate-400 light:text-slate-600 hover:text-indigo-500 hover:border-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {language === 'zh' ? '下一页' : 'Next'}
                </button>
              </div>
            )}

            {/* Limit Selector - Always visible */}
            <div className="flex items-center gap-3 bg-card-bg border border-card-border p-1 rounded-xl shadow-lg">
              <span className="text-[9px] font-black text-slate-500 px-2 uppercase tracking-tighter">
                {language === 'zh' ? '每页显示' : 'Limit'}
              </span>
              <div className="flex items-center bg-background rounded-lg p-0.5 border border-card-border">
                {[20, 40, 80].map((l) => (
                  <button
                    key={l}
                    onClick={() => {
                      setLimit(l);
                      setPage(1);
                    }}
                    className={cn(
                      "px-3 py-1 rounded-md text-[10px] font-bold transition-all",
                      limit === l ? "bg-foreground text-background shadow-md scale-105" : "text-slate-500 hover:text-indigo-400"
                    )}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer Link */}
        <footer className="relative z-10 mt-12 py-6 border-t border-slate-900/50 text-center">
          <div className="flex items-center justify-center space-x-6 text-[10px] font-bold text-slate-500 dark:text-slate-600 light:text-slate-400">
            <Link href="/project-history" className="hover:text-indigo-400 transition-colors uppercase tracking-widest">{t("nav.projectHistory")}</Link>
            <a href="#" className="hover:text-indigo-400 transition-colors uppercase tracking-widest">{t("nav.terms")}</a>
            <a href="#" className="hover:text-indigo-400 transition-colors uppercase tracking-widest">{t("nav.privacy")}</a>
          </div>
        </footer>
      </main >
    </div >
  );
}
