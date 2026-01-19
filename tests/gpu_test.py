import sys
import os
import time

# Ensure backend dir is in path
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

# Now import
from transcriber import transcribe_audio

# Set working directory to backend so relative paths work
os.chdir(backend_dir)

test_file = "downloads/QVBpiuph3rM.m4a"
if not os.path.exists(test_file):
    print(f"Test file {test_file} not found. Searching for any m4a in downloads...")
    import glob
    files = glob.glob("downloads/*.m4a")
    if files:
        test_file = files[0]
    else:
        print("No m4a files found.")
        sys.exit(1)

print(f"--- Starting GPU/CPU test for: {test_file} ---")
start_time = time.time()
results = transcribe_audio(test_file, mode="local")
end_time = time.time()

print(f"--- Transcription took {end_time - start_time:.2f} seconds ---")
print(f"Result segments: {len(results)}")
if results:
    print(f"First segment snippet: {results[0]['text'][:50]}...")
