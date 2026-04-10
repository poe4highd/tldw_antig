import os
import json
import sys
import time
import subprocess
from dotenv import load_dotenv

# 优先使用项目 venv Python
VENV_PYTHON = os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python")
PYTHON = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

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

def run_correction(provider, model_name, prompt_mode="v1", suffix=""):
    label = f"{model_name}{suffix}"
    print(f"\n>>> Running correction: {provider} ({label}) [prompt={prompt_mode}]...")
    os.environ["LLM_PROVIDER"] = provider
    if provider == "ollama":
        os.environ["OLLAMA_MODEL"] = model_name

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        raw_subtitles = json.load(f)

    t0 = time.perf_counter()
    paragraphs, usage = split_into_paragraphs(
        raw_subtitles, title=TITLE, description=DESCRIPTION, prompt_mode=prompt_mode
    )
    elapsed = time.perf_counter() - t0
    print(f">>> 耗时: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    result = {
        "paragraphs": paragraphs,
        "usage": usage,
        "title": TITLE,
        "provider": provider,
        "model": label,
        "prompt_mode": prompt_mode,
    }

    safe_label = label.replace(":", "_")
    output_path = os.path.join(backend_dir, "results", f"eval_{safe_label}_{VIDEO_ID}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Results saved to {output_path}")
    return output_path

def evaluate_cer(pred_path):
    print(f"\n>>> Evaluating CER for {pred_path}...")
    compare_script = os.path.join(backend_dir, "scripts", "compare_subs.py")
    cmd = [
        PYTHON, compare_script,
        "--gt", GT_PATH,
        "--pred", pred_path,
        "--outdir", VALIDATION_DIR
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")

def evaluate_raw_baseline():
    """直接评测 raw Whisper 输出的 CER，不经过任何 LLM 矫正。"""
    print(f"\n>>> Evaluating raw Whisper baseline (no LLM correction)...")
    compare_script = os.path.join(backend_dir, "scripts", "compare_subs.py")
    cmd = [
        PYTHON, compare_script,
        "--gt", GT_PATH,
        "--pred", CACHE_PATH,
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

    results_dir = os.path.join(backend_dir, "results")

    # 0. raw Whisper baseline（无矫正），用于衡量 LLM 矫正的实际增益
    evaluate_raw_baseline()

    # 已有结果的模型直接复用，不重跑
    cached_models = [
        ("ollama", "qwen3:8b"),
        ("ollama", "gemma4:e2b"),
        ("openai", "gpt-4o-mini"),
    ]
    all_results = []
    for provider, model_name in cached_models:
        path = os.path.join(results_dir, f"eval_{model_name.replace(':', '_')}_{VIDEO_ID}.json")
        if os.path.exists(path):
            print(f">>> Skipping {model_name} (cached: {path})")
            all_results.append(path)
        else:
            print(f">>> No cache for {model_name}, running correction...")
            all_results.append(run_correction(provider, model_name))

    # gemma4:e4b V1（复用已有缓存）
    e4b_v1_path = os.path.join(results_dir, f"eval_gemma4_e4b_{VIDEO_ID}.json")
    if os.path.exists(e4b_v1_path):
        print(f">>> Skipping gemma4:e4b v1 (cached: {e4b_v1_path})")
        all_results.append(e4b_v1_path)
    else:
        all_results.append(run_correction("ollama", "gemma4:e4b", prompt_mode="v1"))

    # gemma4:e4b V2（句子保留模式）
    e4b_v2_path = os.path.join(results_dir, f"eval_gemma4_e4b-v2_{VIDEO_ID}.json")
    if os.path.exists(e4b_v2_path):
        print(f">>> Skipping gemma4:e4b v2 (cached: {e4b_v2_path})")
        all_results.append(e4b_v2_path)
    else:
        all_results.append(run_correction("ollama", "gemma4:e4b", prompt_mode="v2", suffix="-v2"))

    # gemma4:26b — OOM on MacStudio, skipped

    # 评估所有模型 CER
    for path in all_results:
        evaluate_cer(path)

    print("\n评估完成。请检查 backend/validation 目录下的报告。")

if __name__ == "__main__":
    main()
