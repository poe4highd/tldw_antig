import os
from openai import OpenAI
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

def transcribe_local(file_path: str):
    # Depending on GPU availability, model_size can be 'tiny', 'base', 'small', 'medium', 'large-v3'
    model_size = "base" # Using base for faster local testing if no powerful GPU
    model = WhisperModel(model_size, device="cpu", compute_type="int8") # Default to CPU for safety, change to cuda if available
    
    segments, info = model.transcribe(file_path, beam_size=5)
    
    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    return results

def transcribe_cloud(file_path: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="verbose_json"
        )
    
    results = []
    for segment in transcript.segments:
        results.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })
    return results

def transcribe_audio(file_path: str, mode: str = "cloud"):
    if mode == "local":
        return transcribe_local(file_path)
    else:
        return transcribe_cloud(file_path)
