import httpx
import time
import sys
import os

BASE_URL = "http://localhost:8000"

def poll_task(task_id):
    print(f"Polling status for task {task_id}...")
    while True:
        try:
            resp = httpx.get(f"{BASE_URL}/result/{task_id}", timeout=30.0)
            data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            print(f" - Status: {status} ({progress}%)")
            
            if status == "completed":
                print("Task completed successfully!")
                return True
            if status == "failed":
                print(f"Task failed: {data.get('detail')}")
                return False
        except Exception as e:
            print(f"Error polling: {e}")
            return False
        time.sleep(2)

def test_url_process():
    print("\n--- Testing URL Processing ---")
    urls = open("tests/test_urls.txt").readlines()
    if not urls:
        print("No URLs found in test_urls.txt")
        return
    
    test_url = urls[0].strip()
    print(f"Submitting URL: {test_url}")
    
    try:
        resp = httpx.post(f"{BASE_URL}/process", json={"url": test_url, "mode": "local"}, timeout=30.0)
        task_id = resp.json()["task_id"]
        return poll_task(task_id)
    except Exception as e:
        print(f"Error starting process: {e}")
        return False

def test_upload():
    print("\n--- Testing Audio Upload ---")
    file_path = "tests/sample.mp3"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return False
    
    print(f"Uploading file: {file_path}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
            resp = httpx.post(f"{BASE_URL}/upload", files=files, data={"mode": "local"}, timeout=30.0)
            task_id = resp.json()["task_id"]
            return poll_task(task_id)
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False

def test_history():
    print("\n--- Testing History API ---")
    try:
        resp = httpx.get(f"{BASE_URL}/history")
        data = resp.json()
        items = data.get("items", [])
        active = data.get("active_tasks", [])
        print(f"History items: {len(items)}")
        print(f"Active tasks: {len(active)}")
        return True
    except Exception as e:
        print(f"Error fetching history: {e}")
        return False

if __name__ == "__main__":
    success = True
    # Test History first to see baseline
    test_history()
    
    # Test Upload (faster usually)
    if not test_upload():
        success = False
    
    # Test URL (might take longer due to download)
    if not test_url_process():
        success = False
        
    if success:
        print("\nALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED.")
        sys.exit(1)
