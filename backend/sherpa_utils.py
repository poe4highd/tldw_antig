import os
import wave
import numpy as np
import subprocess

def load_audio_for_sherpa(file_path: str, sample_rate: int = 16000) -> np.ndarray:
    """
    Load an audio file and convert it to the format required by sherpa-onnx:
    16kHz, Mono, Float32 normalized to [-1, 1].
    Uses ffmpeg for robust format support.
    """
    # Use ffmpeg to convert/resample to a temporary wav file
    temp_wav = f"{file_path}.temp.wav"
    try:
        cmd = [
            "ffmpeg", "-i", file_path,
            "-ar", str(sample_rate),
            "-ac", "1",
            "-f", "wav",
            "-y", temp_wav
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with wave.open(temp_wav, "rb") as f:
            num_frames = f.getnframes()
            data = f.readframes(num_frames)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            return samples
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

def format_sherpa_result(result_text: str):
    """
    Normalize sherpa-onnx result text if needed.
    (Currently SenseVoice ONNX output is quite clean)
    """
    # SenseVoice sometimes includes language tags like <|zh|>, we might want to strip them if they appear in text
    # but usually they are metadata. Let's keep it simple for now.
    return result_text.strip()
