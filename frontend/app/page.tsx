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
  Sparkles,
  Settings,
  Columns2
} from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
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
  date: string;
  views: number;
}

export default function MarketingPage() {
  const { t, language } = useTranslation();
  const [viewMode, setViewMode] = useState<"thumb" | "text-single" | "text-double">("text-double");
  const [searchQuery, setSearchQuery] = useState("");
  const [items, setItems] = useState<ExploreItem[]>([]);
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

    fetchExplore();
    fetchTrending();
  }, []);

  const fetchExplore = async () => {
    setIsLoading(true);
    try {
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/explore`);
      const data = await response.json();
      if (data.items) {
        setItems(data.items);
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

  const filteredItems = items.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (item.channel && item.channel.toLowerCase().includes(searchQuery.toLowerCase()))
  );

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
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      <main className="max-w-7xl mx-auto p-4 md:p-8 bg-slate-950 relative">
        {/* Background Glows */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[120px] rounded-full" />
          <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-600/5 blur-[120px] rounded-full" />
        </div>

        {/* Desktop & Mobile Top Header (Settings/Lang) */}
        <div className="absolute top-4 right-4 md:top-8 md:right-8 z-20 flex items-center gap-3">
          <LanguageSwitcher />
          <Link
            href="/settings"
            className="p-2.5 bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl text-slate-400 hover:text-white hover:border-indigo-500/50 transition-all shadow-lg"
            title={t("common.settings")}
          >
            <Settings className="w-5 h-5" />
          </Link>
        </div>



        {/* Compact Hero Section */}
        <div className="relative z-10 mb-12">
          <div className="flex items-center gap-4 mb-4">
            <Link href="/" className="flex items-center space-x-3 group animate-in fade-in slide-in-from-left-4 duration-700">
              <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-all duration-300 shadow-xl">
                <img src="/icon.png" alt="Read-Tube Logo" className="w-7 h-7" />
              </div>
              <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                {t("marketing.title")}
              </span>
            </Link>
            <div className="h-6 w-px bg-slate-800 mx-1" />
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold tracking-widest uppercase">
              <Sparkles className="w-3 h-3 mr-1.5" />
              {t("marketing.tagline")}
            </div>
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl lg:text-7xl font-black tracking-tight mb-6 bg-gradient-to-r from-white via-white to-slate-500 bg-clip-text text-transparent leading-tight">
              {t("marketing.heroTitle1")}{t("marketing.heroTitle2")}
            </h1>
            <p className="text-slate-500 text-base md:text-xl font-medium leading-relaxed">
              {t("marketing.description")}
            </p>
          </div>
        </div>

        {/* Toolbar */}
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
          <div className="relative w-full md:max-w-2xl group">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-indigo-400 transition-colors">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              placeholder={t("explore.searchPlaceholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/40 border border-slate-800/60 rounded-[1.5rem] py-4 pl-12 pr-4 text-base focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500/50 placeholder:text-slate-600 transition-all shadow-2xl backdrop-blur-sm"
            />
            {/* Quick Keywords */}
            <div className="flex flex-wrap items-center gap-2 mt-4 px-2">
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mr-2">{t("explore.trending") || "Trending"}:</span>
              {trendingKeywords.map((kw) => (
                <button
                  key={kw}
                  onClick={() => setSearchQuery(kw)}
                  className="px-3 py-1 rounded-full bg-slate-900/40 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800 text-[10px] font-bold text-slate-400 hover:text-indigo-400 transition-all"
                >
                  #{kw}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center bg-slate-900/50 border border-slate-800 p-1 rounded-xl shadow-inner">
            <button
              onClick={() => toggleViewMode("text-double")}
              className={cn(
                "flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all duration-300",
                viewMode === "text-double"
                  ? "bg-white text-slate-950 shadow-xl scale-[1.02]"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              <Columns2 className="w-3 h-3" />
              <span className="hidden sm:inline">{t("explore.modeText")} (2)</span>
              <span className="sm:hidden">2</span>
            </button>
            <button
              onClick={() => toggleViewMode("text-single")}
              className={cn(
                "flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all duration-300",
                viewMode === "text-single"
                  ? "bg-white text-slate-950 shadow-xl scale-[1.02]"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              <List className="w-3 h-3" />
              <span className="hidden sm:inline">{t("explore.modeText")} (1)</span>
              <span className="sm:hidden">1</span>
            </button>
            <button
              onClick={() => toggleViewMode("thumb")}
              className={cn(
                "flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all duration-300",
                viewMode === "thumb"
                  ? "bg-white text-slate-950 shadow-xl scale-[1.02]"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              <LayoutGrid className="w-3 h-3" />
              <span className="hidden sm:inline">{t("explore.modeThumb")}</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10">
          {isLoading ? (
            <div className="grid grid-cols-1 gap-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-12 bg-slate-900/40 rounded-xl animate-pulse border border-slate-800/50" />
              ))}
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-20 text-center bg-slate-900/20 border border-dashed border-slate-800 rounded-[2rem] flex flex-col items-center">
              <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center mb-6 text-slate-700">
                <Search className="w-8 h-8" />
              </div>
              <p className="text-slate-400 font-bold text-lg">{t("explore.empty")}</p>
            </div>
          ) : viewMode === "text-single" || viewMode === "text-double" ? (
            <div className={cn(
              "gap-3",
              viewMode === "text-double" ? "grid grid-cols-1 lg:grid-cols-2" : "flex flex-col space-y-2"
            )}>
              {filteredItems.map((item) => (
                <Link
                  key={item.id}
                  href={`/result/${item.id}`}
                  className="group flex items-center gap-3 p-3 bg-slate-900/20 border border-slate-800/30 rounded-xl hover:bg-slate-900/60 hover:border-indigo-500/30 transition-all duration-300 hover:scale-[1.005]"
                >
                  <div className="shrink-0 relative">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center p-[2px] shadow-lg group-hover:scale-110 transition-transform"
                      style={{ backgroundColor: getChannelColor(item.channel_id, item.channel) }}
                    >
                      <div className="w-full h-full rounded-full overflow-hidden border border-slate-950 bg-slate-800 flex items-center justify-center">
                        {item.channel_avatar ? (
                          <img src={item.channel_avatar} alt={item.channel} className="w-full h-full object-cover" />
                        ) : item.channel ? (
                          <img src={getAvatarUrl(item.channel)!} alt={item.channel} className="w-full h-full object-cover" />
                        ) : (
                          <User className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                    </div>
                    <div className="absolute -bottom-1 -right-1 bg-red-600 rounded-full p-0.5 border border-slate-950">
                      <Youtube className="w-2 h-2 text-white" />
                    </div>
                  </div>

                  <div className="flex-grow min-w-0">
                    <h3 className="font-bold text-sm text-slate-100 group-hover:text-indigo-400 transition-colors line-clamp-1 mb-0.5">
                      {item.title}
                    </h3>
                    <div className="flex items-center gap-3 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-600" />
                        {item.channel || "YouTube Creator"}
                      </span>
                      <span className="w-1 h-1 rounded-full bg-slate-800" />
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(item.date)}
                      </span>
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center gap-6 pr-2">
                    <div className="hidden sm:flex flex-col items-end">
                      <div className="flex items-center gap-1 text-[10px] font-black text-slate-400">
                        <Eye className="w-3 h-3" />
                        {item.views.toLocaleString()}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-700 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredItems.map((item) => (
                <div key={item.id} className="group relative bg-slate-900/30 border border-slate-800/50 rounded-2xl overflow-hidden hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10">
                  <div className="aspect-video relative overflow-hidden">
                    <img src={item.thumbnail} alt={item.title} className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-700" />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />

                    <div className="absolute top-4 left-4 p-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10">
                      <Youtube className="w-4 h-4 text-red-500" />
                    </div>
                  </div>

                  <div className="p-4">
                    <h3 className="font-bold text-sm line-clamp-2 mb-3 h-10 group-hover:text-indigo-400 transition-colors uppercase tracking-tight">
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
        </div>

        {/* Footer Link */}
        <footer className="relative z-10 mt-12 py-6 border-t border-slate-900/50 text-center">
          <div className="flex items-center justify-center space-x-6 text-[10px] font-bold text-slate-600">
            <Link href="/project-history" className="hover:text-white transition-colors">{t("nav.projectHistory")}</Link>
            <a href="#" className="hover:text-white transition-colors uppercase tracking-widest">{t("nav.terms")}</a>
            <a href="#" className="hover:text-white transition-colors uppercase tracking-widest">{t("nav.privacy")}</a>
          </div>
        </footer>
      </main>
    </div>
  );
}
