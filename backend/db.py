import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("[SUPABASE] Warning: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment variables.")
    supabase: Client = None
else:
    print(f"[SUPABASE] Initializing client for {url}")
    supabase: Client = create_client(url, key)
    if supabase:
        print("[SUPABASE] Client successfully created")

def get_db():
    return supabase
