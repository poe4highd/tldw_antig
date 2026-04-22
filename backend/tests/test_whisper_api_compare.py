"""
Whisper 三方性能对比：本地 CUDA / 本地 CPU / 远程 MLX API
用法: cd backend && venv/bin/python tests/test_whisper_api_compare.py

测试设计：
- 本地两种模式在同一进程内先 warm-up（5s短音频），再对长音频正式计时
- 只记录推理耗时，不含模型加载
- 远程 MLX 服务常驻，直接计时
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_SHORT = os.path.join(BASE_DIR, "tests", "sample.mp3")
AUDIO_LONG  = os.path.join(BASE_DIR, "downloads", "rTsZ-2ldBIw.mp3")
DURATION    = 544   # 秒

API_BASE      = "http://192.168.1.176:47913/v1"
REMOTE_MODEL  = "mlx-community/whisper-large-v3-mlx"


def fmt(t):
    return f"{t:.1f}s" if t else "失败"

def rtf(t):
    return f"{DURATION/t:.1f}x" if t else "—"

def preview(text, n=100):
    return repr(text[:n]) if text else "—"


def run_local_cuda():
    from faster_whisper import WhisperModel
    print("\n[CUDA] 加载模型 large-v3-turbo float16 ...")
    t_load = time.time()
    m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    print(f"[CUDA] 加载耗时 {time.time()-t_load:.1f}s，开始 warm-up ...")
    list(m.transcribe(AUDIO_SHORT, beam_size=5)[0])

    print(f"[CUDA] 正式推理 {DURATION}s 音频 ...")
    t0 = time.time()
    segs, info = m.transcribe(AUDIO_LONG, beam_size=5)
    text = " ".join(s.text for s in segs)
    elapsed = time.time() - t0
    print(f"[CUDA] 完成，语言={info.language}，耗时={elapsed:.1f}s")
    return text, elapsed


def run_local_cpu():
    from faster_whisper import WhisperModel
    print("\n[CPU]  加载模型 large-v3-turbo int8 ...")
    t_load = time.time()
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    print(f"[CPU]  加载耗时 {time.time()-t_load:.1f}s，开始 warm-up ...")
    list(m.transcribe(AUDIO_SHORT, beam_size=5)[0])

    print(f"[CPU]  正式推理 {DURATION}s 音频（预计数十分钟）...")
    t0 = time.time()
    segs, info = m.transcribe(AUDIO_LONG, beam_size=5)
    text = " ".join(s.text for s in segs)
    elapsed = time.time() - t0
    print(f"[CPU]  完成，语言={info.language}，耗时={elapsed:.1f}s")
    return text, elapsed


def run_remote():
    from openai import OpenAI
    client = OpenAI(api_key="none", base_url=API_BASE)
    print(f"\n[MLX]  上传音频至 {API_BASE} ...")
    t0 = time.time()
    with open(AUDIO_LONG, "rb") as f:
        result = client.audio.transcriptions.create(
            model=REMOTE_MODEL,
            file=f,
            response_format="verbose_json",
        )
    elapsed = time.time() - t0
    text = result.text if hasattr(result, "text") else str(result)
    print(f"[MLX]  完成，耗时={elapsed:.1f}s")
    return text, elapsed


def main():
    print("=" * 65)
    print(f"  Whisper 三方性能对比  |  音频: {DURATION}s (~9min)  |  11MB")
    print("=" * 65)

    results = {}

    try:
        results["CUDA"] = run_local_cuda()
    except Exception as e:
        print(f"[CUDA] 失败: {e}")
        results["CUDA"] = (None, None)

    results["CPU"] = (None, None)  # 跳过，预计耗时 1-2 小时

    try:
        results["MLX"] = run_remote()
    except Exception as e:
        print(f"[MLX]  失败: {e}")
        results["MLX"] = (None, None)

    print("\n" + "=" * 65)
    print(f"  {'方案':<18} {'耗时':>8}  {'实时倍率':>10}  {'转录预览'}")
    print("=" * 65)
    for name, (text, t) in results.items():
        label = {
            "CUDA": "本地 CUDA float16",
            "CPU":  "本地 CPU  int8  ",
            "MLX":  "远程 MLX (Mac)  ",
        }[name]
        print(f"  {label}  {fmt(t):>8}  {rtf(t):>10}  {preview(text, 60)}")
    print("=" * 65)

    # 如果 CUDA 和 MLX 都成功，计算速度比
    cuda_t = results["CUDA"][1]
    mlx_t  = results["MLX"][1]
    if cuda_t and mlx_t:
        if cuda_t < mlx_t:
            print(f"\n  → 本地 CUDA 比远程 MLX 快 {mlx_t/cuda_t:.1f}x")
        else:
            print(f"\n  → 远程 MLX 比本地 CUDA 快 {cuda_t/mlx_t:.1f}x")


if __name__ == "__main__":
    main()
