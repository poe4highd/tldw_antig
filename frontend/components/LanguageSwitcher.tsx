"use client";

import React from "react";
import { useTranslation } from "@/contexts/LanguageContext";
import { Languages } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function LanguageSwitcher() {
    const { language, setLanguage } = useTranslation();

    const toggleLanguage = () => {
        setLanguage(language === "en" ? "zh" : "en");
    };

    return (
        <button
            onClick={toggleLanguage}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/50 dark:bg-slate-900/50 light:bg-slate-100/60 border border-slate-800 dark:border-slate-800 light:border-slate-200 hover:border-indigo-500/50 transition-all duration-300 group overflow-hidden"
        >
            <Languages className="w-4 h-4 text-slate-400 dark:text-slate-400 light:text-slate-500 group-hover:text-indigo-400 transition-colors" />
            <span className="text-xs font-bold text-slate-400 dark:text-slate-400 light:text-slate-500 group-hover:text-indigo-300 uppercase tracking-tighter w-4 text-center">
                <AnimatePresence mode="wait">
                    <motion.span
                        key={language}
                        initial={{ y: 10, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -10, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="block"
                    >
                        {language}
                    </motion.span>
                </AnimatePresence>
            </span>
        </button>
    );
}
