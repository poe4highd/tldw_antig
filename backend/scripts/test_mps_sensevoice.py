import torch
from funasr import AutoModel
import time
import os

model_name = "iic/SenseVoiceSmall"
audio_file = "backend/tests/sample.mp3"

if not os.path.exists(audio_file):
    print(f"Error: {audio_file} not found.")
    exit(1)

print(f"--- Testing SenseVoice with MPS on {audio_file} ---")
print(f"MPS Available: {torch.backends.mps.is_available()}")

try:
    start_load = time.time()
    model = AutoModel(
        model=model_name,
        trust_remote_code=True,
        device="mps" if torch.backends.mps.is_available() else "cpu",
        disable_update=True
    )
    print(f"Model loaded in {time.time() - start_load:.2f}s")

    start_gen = time.time()
    res = model.generate(
        input=audio_file,
        cache={},
        language="auto",
        use_itn=True
    )
    print(f"Inference completed in {time.time() - start_gen:.2f}s")
    print(f"Result: {res}")

except Exception as e:
    print(f"Error during test: {e}")
