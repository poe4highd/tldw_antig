import sherpa_onnx
import time
import os
import wave
import numpy as np
from sherpa_utils import load_audio_for_sherpa

def transcribe_sensevoice_vad(file_path: str):
    """
    Transcribe long audio using SenseVoice + VAD (Silero) for efficiency.
    """
    # 1. Setup VAD
    # We need to download silero_vad if not present
    vad_dir = "backend/models/silero_vad"
    vad_model_path = os.path.join(vad_dir, "silero_vad.onnx")
    
    if not os.path.exists(vad_model_path):
        print("--- Downloading Silero VAD model... ---")
        os.makedirs(vad_dir, exist_ok=True)
        # Use a more reliable download link or huggingface-cli
        os.system(f"huggingface-cli download csukuangfj/silero-vad-onnx silero_vad.onnx --local-dir {vad_dir}")

    vad_config = sherpa_onnx.SileroVadModelConfig(
        model=vad_model_path,
        min_silence_duration=0.5,
        min_speech_duration=0.25,
        threshold=0.5,
        window_size=512,
    )
    
    # 2. Setup Recognizer
    model_dir = "backend/models/sensevoice-onnx"
    model_path = os.path.join(model_dir, "model.int8.onnx")
    tokens_path = os.path.join(model_dir, "tokens.txt")
    
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=model_path,
        tokens=tokens_path,
        num_threads=os.cpu_count(),
        use_itn=True,
        debug=False
    )
    
    # 3. Process Audio
    print(f"--- [Sherpa-VAD] Processing {file_path} ---")
    samples = load_audio_for_sherpa(file_path)
    sample_rate = 16000
    
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=30)
    
    results = []
    chunk_size = int(0.1 * sample_rate) # 100ms
    
    start_time = time.time()
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i : i + chunk_size]
        vad.accept_waveform(chunk)
        
        while not vad.is_empty():
            segment = vad.front
            # Transcribe segment
            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, segment.samples)
            recognizer.decode_stream(stream)
            
            start_s = segment.start / sample_rate
            duration_s = len(segment.samples) / sample_rate
            
            results.append({
                "start": start_s,
                "end": start_s + duration_s,
                "text": stream.result.text.strip(),
                "words": []
            })
            vad.pop()
            print(f"[{start_s:.1f}s - {start_s + duration_s:.1f}s] {stream.result.text}")
            
    print(f"--- VAD Transcription finished in {time.time() - start_time:.2f}s ---")
    return results

if __name__ == "__main__":
    # Test on the long file if possible or a sample
    # results = transcribe_sensevoice_vad("backend/downloads/QVBpiuph3rM.m4a")
    # print(results)
    pass
