import sherpa_onnx
import time
import os
import wave
import numpy as np

def test_sherpa_onnx():
    model_dir = "backend/models/sensevoice-onnx"
    # model_path = os.path.join(model_dir, "model.onnx")
    model_path = os.path.join(model_dir, "model.int8.onnx")
    tokens_path = os.path.join(model_dir, "tokens.txt")
    audio_path = "backend/tests/sample.mp3"

    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found.")
        return

    print(f"--- Testing sherpa-onnx SenseVoice with {model_path} ---")
    
    start_load = time.time()
    # OfflineSenseVoiceModelConfig
    recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=model_path,
        tokens=tokens_path,
        num_threads=os.cpu_count(),
        use_itn=True,
        debug=False
    )
    print(f"Model loaded in {time.time() - start_load:.2f}s")

    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        return

    # Convert mp3 to wav
    wav_path = "backend/temp_test.wav"
    os.system(f"ffmpeg -i {audio_path} -ar 16000 -ac 1 -y {wav_path} > /dev/null 2>&1")
    
    # Read wav file using standard wave module
    with wave.open(wav_path, "rb") as f:
        num_frames = f.getnframes()
        data = f.readframes(num_frames)
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        sample_rate = f.getframerate()

    start_gen = time.time()
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, samples)
    recognizer.decode_stream(stream)
    
    print(f"Inference completed in {time.time() - start_gen:.2f}s")
    print(f"Result: {stream.result.text}")
    
    os.remove(wav_path)

if __name__ == "__main__":
    test_sherpa_onnx()
