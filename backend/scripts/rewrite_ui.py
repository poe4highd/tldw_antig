import re
import os

page_path = os.path.join(os.path.dirname(__file__), "../../frontend/app/result/[id]/page.tsx")

with open(page_path, "r", encoding="utf-8") as f:
    content = f.read()

nav_end_idx = content.find("</nav>")
main_start_idx = content.find("<main", nav_end_idx)
main_end_idx = content.find("</main>", main_start_idx) + 7

original_main = content[main_start_idx:main_end_idx]

# Extract smaller pieces from the original main block to reuse
def extract_section(regex_pattern, fallback=""):
    match = re.search(regex_pattern, original_main, re.DOTALL)
    if match:
        return match.group(1)
    return fallback

video_player_inner = extract_section(r'<div className="relative aspect-video group">(.*?)</div>\s*</div>\s*\{/\* Action Bar')
action_bar_inner = extract_section(r'\{/\* Action Bar Below Video \*/\}\s*<div[^>]*>(.*?)</div>\s*\{/\* Video Info \*/\}')
summary_content = extract_section(r'\{/\* Transcription Content - Scrollable Area \*/\}\s*<div[^>]*>(.*?)</div>\s*\{/\* Resume Follow Button \*/\}')
# Resume follow button isn't extracted properly because it's outside the scrollable div. We can reconstruct it.
discussion_inner = extract_section(r'\{/\* Discussion Section \*/\}\s*<div[^>]*>(.*?)</div>\s*\{/\* User Interest Heatmap')

new_main = f"""            <main className="max-w-[1440px] mx-auto px-6 py-6 flex flex-col gap-6 h-[calc(100vh-5rem)] overflow-y-auto no-scrollbar">
                {{/* Top Section: Video (1/3) */}}
                <div className="w-full flex-shrink-0 h-[33vh] min-h-[250px] relative bg-black rounded-2xl md:rounded-[2.5rem] overflow-hidden shadow-2xl border border-card-border/10 ring-1 ring-card-border/5 group transition-all duration-300">
                    <div className="relative w-full h-full group">
{video_player_inner}
                    </div>
                </div>

                {{/* Middle Section: Title & Stats (1/6) */}}
                <div className="w-full flex-shrink-0 h-[16vh] min-h-[140px] flex flex-col justify-center gap-3">
                    <h2 className="text-xl md:text-2xl font-black tracking-tight line-clamp-2 leading-tight px-1">{{result.title}}</h2>
                    <div className="flex flex-wrap items-center gap-4 text-[9px] md:text-xs font-black text-slate-600 uppercase tracking-widest px-1">
                        <span>{{viewCount.toLocaleString()}} {{t("result.views")}}</span>
                        <span>{{t("result.date")}}: {{( () => {{
                            const date = result.mtime ? new Date(result.mtime) : new Date();
                            return date.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {{
                                year: 'numeric', month: '2-digit', day: '2-digit'
                            }}).replace(r"\\/"g, '.');
                        }})()}}</span>
                        
                        {{/* Heatmap as 1 line tall after date */}}
                        <div className="flex items-center gap-2 flex-1 max-w-[250px] ml-4 bg-card-bg/50 px-3 py-1.5 rounded-full border border-card-border/50 shadow-inner">
                            <span className="shrink-0 text-[8px] md:text-[10px] text-indigo-500">{{t("result.keyInterest")}}:</span>
                            <div className="flex-1 h-1.5 bg-background border border-card-border rounded-full overflow-hidden flex">
                                <div className="h-full bg-indigo-500" style={{{{ width: '45%' }}}}></div>
                                <div className="h-full bg-indigo-600 opacity-50" style={{{{ width: '20%' }}}}></div>
                                <div className="h-full bg-indigo-400" style={{{{ width: '35%' }}}}></div>
                            </div>
                        </div>
                    </div>

                    {{/* Action Bar Below Title */}}
                    <div className="flex flex-wrap items-center justify-between gap-4 py-2 px-4 bg-card-bg/50 border border-card-border rounded-2xl md:rounded-full backdrop-blur-sm">
{action_bar_inner}
                    </div>
                </div>

                {{/* Bottom Section: Transcript & Summary (1/2) */}}
                <div className="relative w-full flex-shrink-0 h-[50vh] min-h-[400px]">
                    <div
                        ref={{subtitleContainerRef}}
                        onScroll={{handleManualScroll}}
                        data-testid="subtitle-container"
                        className="w-full h-full bg-card-bg/30 border border-card-border rounded-[2.5rem] p-6 md:p-8 overflow-y-auto no-scrollbar scroll-smooth shadow-inner relative"
                    >
{summary_content}
                    </div>
                    {{/* Resume Follow Button */}}
                    {{isAutoScrollPaused && (
                        <div className="absolute bottom-6 right-8 md:right-12 z-[60] animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <button
                                onClick={{resumeAutoScroll}}
                                className="flex items-center space-x-2 px-5 md:px-6 py-2.5 md:py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-2xl shadow-indigo-500/50 transition-all transform hover:scale-105 active:scale-95 font-black text-xs md:text-sm"
                            >
                                <ArrowDownToLine className="w-4 h-4 md:w-5 h-5" />
                                <span>{{t("result.syncProgress")}}</span>
                            </button>
                        </div>
                    )}}
                </div>

                {{/* Discussion Panel Moved to Bottom */}}
                <div className="w-full mt-4 flex-shrink-0 pb-12">
                    <div className="bg-card-bg/40 border border-card-border rounded-[2.5rem] flex flex-col h-[500px] shadow-sm">
{discussion_inner}
                    </div>
                </div>
            </main>"""

full_content = content[:main_start_idx] + new_main + content[main_end_idx:]

with open(page_path, "w", encoding="utf-8") as f:
    f.write(full_content)

print("page.tsx updated successfully.")
