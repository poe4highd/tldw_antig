"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import en from "../translations/en.json";
import zh from "../translations/zh.json";

type Language = "en" | "zh";
type Translations = typeof en;

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (path: string) => string;
}

const translations: Record<Language, Translations> = { en, zh };

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>("en");
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        const savedLanguage = localStorage.getItem("language") as Language;
        if (savedLanguage && (savedLanguage === "en" || savedLanguage === "zh")) {
            setLanguageState(savedLanguage);
        }
        setIsLoaded(true);
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem("language", lang);
    };

    const t = (path: string): string => {
        const keys = path.split(".");
        let current: any = translations[language];

        for (const key of keys) {
            if (current[key] === undefined) {
                // Fallback to English if key missing in current language
                let fallback: any = translations["en"];
                for (const subKey of keys) {
                    if (fallback[subKey] === undefined) return path;
                    fallback = fallback[subKey];
                }
                return typeof fallback === 'string' ? fallback : path;
            }
            current = current[key];
        }

        return typeof current === "string" ? current : path;
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            <div style={{ visibility: isLoaded ? "visible" : "hidden" }}>
                {children}
            </div>
        </LanguageContext.Provider>
    );
}

export function useTranslation() {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error("useTranslation must be used within a LanguageProvider");
    }
    return context;
}
