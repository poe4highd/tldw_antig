import os
import sys

# Simulation of what might be happening
print("--- Reproducing potential OMP conflict ---")

import torch
print(f"Torch loaded: {torch.__version__}")

import mlx_whisper
print("MLX-Whisper loaded")

# This might be where it crashes if we don't have enough memory or if OMP conflicts
try:
    import mlx.core as mx
    print(f"MLX version: {mx.__version__}")
except:
    print("MLX core not found")

print("Done")
