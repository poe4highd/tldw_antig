import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next"
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://read-tube.vercel.app'),
  title: {
    default: "Read-Tube – AI YouTube Transcript & Summary",
    template: "%s | Read-Tube",
  },
  description: "Instantly transcribe YouTube videos and audio files with AI. Read transcripts, get AI summaries, and explore content faster than watching.",
  keywords: ["youtube transcript", "AI video summary", "youtube to text", "video transcription", "AI summarizer", "youtube subtitle"],
  authors: [{ name: "Read-Tube" }],
  openGraph: {
    siteName: "Read-Tube",
    type: "website",
    locale: "en_US",
    title: "Read-Tube – AI YouTube Transcript & Summary",
    description: "Instantly transcribe YouTube videos and audio files with AI. Read transcripts, get AI summaries, and explore content faster than watching.",
    images: [{ url: "/og-default.png", width: 1200, height: 630, alt: "Read-Tube" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Read-Tube – AI YouTube Transcript & Summary",
    description: "Instantly transcribe YouTube videos and audio files with AI.",
    images: ["/og-default.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

import { LanguageProvider } from "@/contexts/LanguageContext";
import { ThemeProvider } from "@/contexts/ThemeContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider>
          <LanguageProvider>
            {children}
            <Analytics />
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
