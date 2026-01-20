import os
import sys
import gc

# Force single thread for everything
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

print("--- Starting stress test for MLX + Torch ---")

import torch
print(f"Torch loaded, MPS available: {torch.backends.mps.is_available()}")
if torch.backends.mps.is_available():
    # Force some MPS activity
    x = torch.randn(100, 100).to("mps")
    y = x @ x
    print("Torch MPS op successful")
    torch.mps.empty_cache()

import mlx_whisper
import mlx.core as mx
print(f"MLX loaded, version: {mx.__version__}")

# Simulate model loading
hf_repo = "mlx-community/whisper-large-v3-turbo"
print(f"Attempting to transcribe a tiny silent audio or just load the model...")

# Instead of full transcribe which needs a file, let's just use the load part if possible
# Or just try to run it on any small file
if os.path.exists("downloads"):
    files = [f for f in os.listdir("downloads") if f.endswith((".m4a", ".mp3", ".wav"))]
    if files:
        target = os.path.join("downloads", files[0])
        print(f"Transcribing {target}...")
        try:
            res = mlx_whisper.transcribe(target, path_or_hf_repo=hf_repo)
            print("Transcribe successful!")
        except Exception as e:
            print(f"Transcribe failed: {e}")
    else:
        print("No audio file found in downloads to test transcription.")
else:
    print("downloads dir not found.")

print("Test finished.")
