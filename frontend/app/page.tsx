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
  Sun,
  Heart
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
  is_liked?: boolean;
}

export default function MarketingPage() {
  const { t, language } = useTranslation();
  const { theme, toggleTheme } = useTheme();
  const [viewMode, setViewMode] = useState<"thumb" | "text-single" | "text-double">("text-double");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
  const [items, setItems] = useState<ExploreItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(80);
  const [trendingKeywords, setTrendingKeywords] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [density, setDensity] = useState<"detailed" | "compact">("detailed");
  const [user, setUser] = useState<any>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    // Read preference
    const saved = localStorage.getItem("rt-explore-view-mode");
    if (saved === "thumb" || saved === "text-single" || saved === "text-double") {
      setViewMode(saved as any);
    } else if (saved === "text") {
      // Migrate old setting
      setViewMode("text-single");
    }

    const savedDensity = localStorage.getItem("rt-explore-density");
    if (savedDensity === "detailed" || savedDensity === "compact") {
      setDensity(savedDensity as any);
    }

    const fetchUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
    };
    fetchUser();

    fetchTrending();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    fetchExplore(page, debouncedSearchQuery);
  }, [page, debouncedSearchQuery, limit, user?.id]);

  const fetchExplore = async (pageNum: number, query: string) => {
    setIsLoading(true);
    try {
      const apiBase = getApiBase();
      const url = new URL(`${apiBase}/explore`);
      url.searchParams.append("page", pageNum.toString());
      url.searchParams.append("limit", limit.toString());
      if (query) url.searchParams.append("q", query);
      if (user?.id) url.searchParams.append("user_id", user.id);

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

  const toggleDensity = (d: "detailed" | "compact") => {
    setDensity(d);
    localStorage.setItem("rt-explore-density", d);
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

  const handleLike = async (e: React.MouseEvent, videoId: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (!user) {
      window.location.href = "/login";
      return;
    }

    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/like`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId, user_id: user.id })
      });
      const data = await response.json();
      if (data.status === "success") {
        setItems(prev => prev.map(item =>
          item.id === videoId ? { ...item, is_liked: data.action === "liked" } : item
        ));
      }
    } catch (error) {
      console.error("Failed to toggle like:", error);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-foreground font-sans selection:bg-indigo-500/30">
      <main className="max-w-7xl mx-auto p-3 md:p-8 relative">
        {/* Background Glows */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
          <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
        </div>

        {/* Header: Logo & Global Settings (Sticky) */}
        <div className="sticky top-0 z-[60] bg-background backdrop-blur-xl border-b border-card-border -mx-3 px-3 md:-mx-8 md:px-8 h-14 md:h-16 flex items-center transition-all duration-300">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="flex items-center space-x-2 md:space-x-3 group shrink-0">
              <div className={cn(
                "p-1.5 border rounded-lg group-hover:border-indigo-500/50 transition-all duration-300 shadow-xl",
                theme === 'dark' ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"
              )}>
                <img src="/icon.png" alt="Read-Tube Logo" className="w-5 h-5" />
              </div>
              <span className={cn(
                "text-lg md:text-xl font-black tracking-tighter",
                theme === 'dark' ? "bg-gradient-to-r from-foreground to-slate-400 bg-clip-text text-transparent" : "text-indigo-600"
              )}>
                {t("marketing.title")}
              </span>
            </Link>

            <div className="flex items-center gap-1.5 md:gap-3">
              <LanguageSwitcher />
              <Link
                href="/pending"
                className="p-2 bg-card-bg/50 backdrop-blur-md border border-card-border rounded-xl text-slate-400 dark:text-slate-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:border-indigo-500/50 transition-all shadow-lg group"
                title="Queue / 待处理"
              >
                <Clock className="w-4 h-4 md:w-5 md:h-5 group-hover:animate-pulse" />
              </Link>
              <button
                onClick={toggleTheme}
                className="p-2 bg-card-bg/50 backdrop-blur-md border border-card-border rounded-xl text-slate-400 dark:text-slate-400 light:text-slate-600 hover:text-white dark:hover:text-white light:hover:text-slate-900 hover:border-indigo-500/50 transition-all shadow-lg"
                title={theme === 'dark' ? "Light Mode / 浅色模式" : "Dark Mode / 深色模式"}
              >
                {theme === 'dark' ? <Sun className="w-4 h-4 md:w-5 md:h-5" /> : <Moon className="w-4 h-4 md:w-5 md:h-5" />}
              </button>
              <Link
                href={user ? "/dashboard" : "/login"}
                className="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs md:text-sm transition-all shadow-lg shadow-indigo-500/20 active:scale-[0.98]"
              >
                <User className="w-3.5 h-3.5 md:w-4 md:h-4" />
                <span className="hidden sm:inline">{user ? "Profile" : t("login.title")}</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Hero Title (Non-sticky) */}
        <div className={cn(
          "relative z-10 overflow-hidden transition-all duration-500 ease-in-out",
          isScrolled ? "max-h-0 opacity-0 mb-0 mt-0" : "max-h-40 opacity-100 mb-6 mt-6"
        )}>
          <div className="flex flex-col">
            <h1 className={cn(
              "text-xl md:text-2xl lg:text-3xl font-black tracking-tight mb-1 leading-[1.1]",
              theme === 'dark' ? "bg-gradient-to-r from-foreground via-foreground to-slate-500 bg-clip-text text-transparent" : "text-indigo-900"
            )}>
              {t("marketing.heroTitle1")}{t("marketing.heroTitle2")}
            </h1>
            <p className={cn(
              "text-sm md:text-base font-medium leading-snug transition-colors duration-300",
              theme === 'dark' ? "text-slate-500" : "text-indigo-950/60"
            )}>
              {t("marketing.description")}
            </p>
          </div>
        </div>

        {/* Consolidate Toolbar (Sticky below hero) */}
        <div className="sticky top-14 md:top-16 z-50 bg-background backdrop-blur-lg border-y border-card-border -mx-3 px-3 md:-mx-8 md:px-8 py-2 md:py-3 transition-all duration-300">
          <div className="flex flex-wrap lg:flex-nowrap items-center gap-3 md:gap-4">
            {/* Search Bar: Desktop Order 1, 30% Width | Mobile Order 2 */}
            <div className="order-2 lg:order-1 flex-grow lg:flex-none lg:w-[30%] relative group">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                <Search className="w-3.5 h-3.5" />
              </div>
              <input
                type="text"
                placeholder={t("explore.searchPlaceholder")}
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full bg-card-bg/50 border border-card-border rounded-xl py-1.5 pl-9 pr-3 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/40 placeholder:text-slate-500 transition-all backdrop-blur-md"
              />
            </div>

            {/* Keywords: Desktop Order 2, Flexible | Mobile Order 1, Full Width */}
            <div className="order-1 lg:order-2 w-full lg:w-auto lg:flex-1 overflow-hidden relative group h-8">
              <div className="flex items-center whitespace-nowrap animate-scroll-slow hover:[animation-play-state:paused] h-full">
                {[...trendingKeywords, ...trendingKeywords].map((kw, idx) => (
                  <button
                    key={`${kw}-${idx}`}
                    onClick={() => handleKeywordClick(kw)}
                    className={cn(
                      "mx-1.5 px-3 py-1 rounded-full border text-[9px] font-bold transition-all duration-300",
                      searchQuery === kw
                        ? "bg-indigo-500 border-indigo-400 text-white shadow-lg shadow-indigo-500/20"
                        : "bg-card-bg/50 border-card-border text-slate-500 hover:border-indigo-500/50 hover:text-white"
                    )}
                  >
                    {kw}
                  </button>
                ))}
              </div>
              <div className="absolute top-0 left-0 h-full w-8 bg-gradient-to-r from-background to-transparent pointer-events-none z-10" />
              <div className="absolute top-0 right-0 h-full w-8 bg-gradient-to-l from-background to-transparent pointer-events-none z-10" />
            </div>

            {/* View & Pagination Switchers: Desktop Order 3 | Mobile Order 3 */}
            <div className="order-3 flex items-center gap-2">
              {/* View Switchers */}
              <div className="flex items-center bg-card-bg/30 border border-card-border p-0.5 rounded-lg gap-0.5 shrink-0">
                {(viewMode === "text-single" || viewMode === "text-double") && (
                  <div className="flex items-center bg-background/30 rounded-md p-0.5 border border-card-border/30 mr-0.5">
                    <button
                      onClick={() => toggleDensity("compact")}
                      className={cn(
                        "px-1.5 py-0.5 rounded text-[8px] font-black transition-all",
                        density === "compact" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                      )}
                    >
                      1L
                    </button>
                    <button
                      onClick={() => toggleDensity("detailed")}
                      className={cn(
                        "px-1.5 py-0.5 rounded text-[8px] font-black transition-all",
                        density === "detailed" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                      )}
                    >
                      3L
                    </button>
                  </div>
                )}

                <div className="flex items-center bg-background/30 rounded-md p-0.5 border border-card-border/30">
                  <button
                    onClick={() => toggleViewMode("text-double")}
                    className={cn(
                      "p-1 rounded transition-all",
                      viewMode === "text-double" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                    )}
                  >
                    <Columns2 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => toggleViewMode("text-single")}
                    className={cn(
                      "p-1 rounded transition-all",
                      viewMode === "text-single" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                    )}
                  >
                    <List className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => toggleViewMode("thumb")}
                    className={cn(
                      "p-1 rounded transition-all",
                      viewMode === "thumb" ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                    )}
                  >
                    <LayoutGrid className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Page Size Selector (20/40/80) */}
              <div className="flex items-center bg-card-bg/30 border border-card-border p-0.5 rounded-lg shrink-0">
                {[20, 40, 80].map((val) => (
                  <button
                    key={val}
                    onClick={() => {
                      setLimit(val);
                      setPage(1);
                    }}
                    className={cn(
                      "px-1.5 py-0.5 rounded text-[8px] font-black transition-all",
                      limit === val ? "bg-foreground text-background shadow-sm" : "text-slate-500 hover:text-indigo-400"
                    )}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10">
          {isLoading ? (
            <div className={cn(
              "gap-1.5",
              viewMode === "text-double" ? "grid grid-cols-1 lg:grid-cols-2" : "flex flex-col space-y-1"
            )}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="flex items-center gap-3 p-2 bg-card-bg border border-card-border rounded-lg animate-pulse">
                  <div className="hidden sm:block w-24 h-14 bg-slate-400/10 dark:bg-slate-800/50 rounded-md shrink-0" />
                  <div className="flex-grow space-y-2">
                    <div className="h-4 bg-slate-400/10 dark:bg-slate-800/50 rounded-md w-3/4" />
                    <div className="h-3 bg-slate-400/10 dark:bg-slate-800/50 rounded-md w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="py-20 text-center bg-card-bg border border-dashed border-card-border rounded-[2rem] flex flex-col items-center">
              <div className="w-16 h-16 bg-background border border-card-border rounded-2xl flex items-center justify-center mb-6 text-slate-500">
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
                  className={cn(
                    "group flex items-center bg-card-bg border border-card-border rounded-lg hover:bg-slate-100 dark:hover:bg-slate-900/40 hover:border-indigo-500/20 transition-all duration-300",
                    density === "compact" ? "py-0.5 px-2 gap-2" : "p-1.5 sm:p-2 gap-2 sm:gap-4"
                  )}
                >
                  {density === "compact" ? (
                    <>
                      <div className="shrink-0 w-9 h-5 rounded-[4px] bg-slate-900 overflow-hidden border border-card-border/30">
                        <img src={item.thumbnail} alt={item.title} className="w-full h-full object-cover" />
                      </div>
                      <div className="flex-grow min-w-0 flex items-center gap-3">
                        <h3 className="font-bold text-xs sm:text-sm text-foreground group-hover:text-indigo-400 transition-colors truncate flex-grow leading-none">
                          {item.title}
                        </h3>
                        <div className="shrink-0 flex items-center gap-3 text-[9px] font-black text-slate-500 pr-1">
                          <span className="hidden sm:flex items-center gap-1">
                            <Calendar className="w-2.5 h-2.5" />
                            {formatDate(item.date)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye className="w-2.5 h-2.5" />
                            {item.views.toLocaleString()}
                          </span>
                          <button
                            onClick={(e) => handleLike(e, item.id)}
                            className={cn(
                              "flex items-center gap-1 transition-colors",
                              item.is_liked ? "text-rose-500" : "hover:text-rose-400"
                            )}
                          >
                            <Heart className={cn("w-2.5 h-2.5", item.is_liked && "fill-current")} />
                          </button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Thumbnail - Now always visible */}
                      <div className="shrink-0 w-24 sm:w-28 h-auto">
                        <div className="aspect-video rounded-md overflow-hidden bg-slate-900 border border-card-border">
                          <img src={item.thumbnail} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                        </div>
                      </div>

                      <div className="flex-grow min-w-0 flex flex-col justify-center gap-0.5">
                        <h3 className="font-bold text-sm text-foreground group-hover:text-indigo-400 transition-colors line-clamp-2 leading-tight">
                          {item.title}
                        </h3>
                        <div className="flex items-center gap-3 text-[9px] sm:text-[10px] font-black text-slate-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-2.5 h-2.5" />
                            {formatDate(item.date)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye className="w-2.5 h-2.5" />
                            {item.views.toLocaleString()}
                          </span>
                          <button
                            onClick={(e) => handleLike(e, item.id)}
                            className={cn(
                              "flex items-center gap-1.5 transition-colors pl-1 border-l border-slate-800/30",
                              item.is_liked ? "text-rose-500" : "hover:text-rose-400"
                            )}
                          >
                            <Heart className={cn("w-3 h-3", item.is_liked && "fill-current")} />
                            {item.is_liked && <span className="text-[8px] uppercase">{language === 'zh' ? '已收录' : 'Saved'}</span>}
                          </button>
                        </div>
                      </div>

                      <div className="shrink-0 hidden sm:flex items-center pr-2">
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {items.map((item) => (
                <div key={item.id} className="group relative bg-card-bg border border-card-border rounded-2xl overflow-hidden hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                  <div className="aspect-video relative overflow-hidden bg-slate-900 border-b border-card-border/10">
                    <img src={item.thumbnail} alt={item.title} className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700" />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent dark:block hidden" />

                    <div className="absolute top-4 left-4 p-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10">
                      <Youtube className="w-4 h-4 text-red-500" />
                    </div>
                  </div>

                  <div className="p-4">
                    <h3 className="font-bold text-[18px] leading-tight line-clamp-2 mb-3 h-[48px] group-hover:text-indigo-400 transition-colors uppercase tracking-tight">
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
                        <button
                          onClick={(e) => handleLike(e, item.id)}
                          className={cn(
                            "flex items-center gap-1 transition-colors",
                            item.is_liked ? "text-rose-500" : "hover:text-rose-400"
                          )}
                        >
                          <Heart className={cn("w-3.5 h-3.5", item.is_liked && "fill-current")} />
                        </button>
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
