"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutGrid,
    FileUp,
    Settings,
    History,
    LogOut,
    X
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SidebarProps {
    user: {
        id: string;
        email?: string;
        user_metadata?: {
            full_name?: string;
            avatar_url?: string;
        };
    } | null;
    onSignOut: () => void;
    isOpen: boolean;
    onClose: () => void;
}

export function Sidebar({ user, onSignOut, isOpen, onClose }: SidebarProps) {
    const pathname = usePathname();

    const menuItems = [
        { name: "我的书架", icon: LayoutGrid, href: "/dashboard" },
        { name: "任务处理中心", icon: FileUp, href: "/tasks" },
    ];

    const systemItems = [
        { name: "项目更新历史", icon: History, href: "/project-history" },
        { name: "偏好设置", icon: Settings, href: "/settings" },
    ];

    return (
        <>
            {/* Overlay for mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
                    onClick={onClose}
                />
            )}

            <aside
                className={cn(
                    "fixed top-0 left-0 z-50 w-64 h-screen bg-slate-950 border-r border-slate-900 flex flex-col transition-transform duration-300 ease-in-out md:translate-x-0 md:static",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="p-8 flex flex-col h-full overflow-y-auto">
                    <div className="flex items-center justify-between mb-12">
                        <Link href="/?noredirect=1" className="flex items-center space-x-3 group">
                            <div className="p-2 bg-slate-900 border border-slate-800 rounded-xl group-hover:border-indigo-500/50 transition-all duration-300">
                                <img src="/icon.png" alt="Read-Tube Logo" className="w-6 h-6" />
                            </div>
                            <span className="text-xl font-black tracking-tighter bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                                Read-Tube
                            </span>
                        </Link>
                        <button
                            onClick={onClose}
                            className="p-2 text-slate-500 hover:text-white md:hidden"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <nav className="space-y-8 flex-1">
                        <div>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 px-4">主菜单</p>
                            <div className="space-y-1">
                                {menuItems.map((item) => {
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            onClick={onClose}
                                            className={cn(
                                                "w-full flex items-center space-x-3 px-4 py-3 rounded-xl font-medium text-sm transition-all",
                                                isActive
                                                    ? "bg-indigo-500/10 text-indigo-400 font-bold"
                                                    : "text-slate-400 hover:bg-slate-900 hover:text-white"
                                            )}
                                        >
                                            <item.icon className="w-5 h-5 flex-shrink-0" />
                                            <span>{item.name}</span>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        <div>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 px-4">系统与支持</p>
                            <div className="space-y-1">
                                {systemItems.map((item) => {
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            onClick={onClose}
                                            className={cn(
                                                "w-full flex items-center space-x-3 px-4 py-3 rounded-xl font-medium text-sm transition-all",
                                                isActive
                                                    ? "bg-indigo-500/10 text-indigo-400 font-bold"
                                                    : "text-slate-400 hover:bg-slate-900 hover:text-white"
                                            )}
                                        >
                                            <item.icon className="w-5 h-5 flex-shrink-0" />
                                            <span>{item.name}</span>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    </nav>

                    <div className="mt-auto pt-6 border-t border-slate-900">
                        <div className="flex items-center space-x-3 mb-6 px-2">
                            {user?.user_metadata?.avatar_url ? (
                                <img
                                    src={user.user_metadata.avatar_url}
                                    alt="Avatar"
                                    className="w-10 h-10 rounded-full border-2 border-white/10 shadow-lg shadow-indigo-500/20"
                                />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center font-bold border-2 border-white/10 shadow-lg shadow-indigo-500/20">
                                    {user?.email?.[0].toUpperCase() || "U"}
                                </div>
                            )}
                            <div className="overflow-hidden">
                                <p className="text-sm font-bold truncate">{user?.user_metadata?.full_name || user?.email?.split('@')[0] || "已登录"}</p>
                                <p className="text-[10px] text-slate-500 truncate">{user?.email || "..."}</p>
                            </div>
                        </div>
                        <button
                            onClick={() => {
                                onSignOut();
                                onClose();
                            }}
                            className="w-full flex items-center justify-center space-x-2 py-3 border border-slate-800 hover:border-red-500/50 hover:bg-red-500/5 text-slate-400 hover:text-red-400 rounded-xl text-xs font-bold transition-all"
                        >
                            <LogOut className="w-4 h-4" />
                            <span>退出登录</span>
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
