import os
import json
import sys
import subprocess
from dotenv import load_dotenv

# 确保在 backend 目录上下文
backend_dir = os.path.join(os.getcwd(), 'backend')
if not os.path.exists(backend_dir):
    backend_dir = os.getcwd()
sys.path.append(backend_dir)

load_dotenv(os.path.join(backend_dir, '.env'))

from processor import split_into_paragraphs

VIDEO_ID = "QVBpiuph3rM"
TITLE = "灵修与明白神的旨意"
DESCRIPTION = "本视频分享关于灵修的意义和如何明白神的旨意。"
GT_PATH = f"backend/tests/data/{VIDEO_ID}.zh-CN.srv1"
CACHE_PATH = f"backend/cache/{VIDEO_ID}_local_large-v3-turbo_raw.json"
VALIDATION_DIR = "backend/validation"

def run_correction(provider, model_name):
    print(f"\n>>> Running correction with {provider} ({model_name})...")
    # 临时覆盖环境变量
    os.environ["LLM_PROVIDER"] = provider
    if provider == "ollama":
        os.environ["OLLAMA_MODEL"] = model_name
    
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        raw_subtitles = json.load(f)
    
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=TITLE, description=DESCRIPTION)
    
    result = {
        "paragraphs": paragraphs,
        "usage": usage,
        "title": TITLE,
        "provider": provider,
        "model": model_name
    }
    
    output_path = os.path.join(backend_dir, "results", f"eval_{provider}_{VIDEO_ID}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_path}")
    return output_path

def evaluate_cer(pred_path):
    print(f"\n>>> Evaluating CER for {pred_path}...")
    compare_script = os.path.join(backend_dir, "scripts", "compare_subs.py")
    cmd = [
        "python3", compare_script,
        "--gt", GT_PATH,
        "--pred", pred_path,
        "--outdir", VALIDATION_DIR
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")

def main():
    global CACHE_PATH
    if not os.path.exists(CACHE_PATH):
        # 尝试备选缓存路径
        alt_cache = f"backend/cache/{VIDEO_ID}_local_large-v3_raw.json"
        if os.path.exists(alt_cache):
            CACHE_PATH = alt_cache
        else:
            print(f"Error: No cache found for {VIDEO_ID}")
            return

    # 1. 运行 Ollama
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    ollama_res = run_correction("ollama", ollama_model)
    
    # 2. 运行 OpenAI
    openai_res = run_correction("openai", "gpt-4o-mini")
    
    # 3. 评估两者
    evaluate_cer(ollama_res)
    evaluate_cer(openai_res)
    
    print("\n评估完成。请检查 backend/validation 目录下的报告。")

if __name__ == "__main__":
    main()
