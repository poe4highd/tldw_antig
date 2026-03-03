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

def get_db(force_new=False):
    """获取 Supabase 客户端。force_new=True 时强制重建连接（用于长时间运行进程的连接恢复）。"""
    global supabase
    if force_new and url and key:
        print("[SUPABASE] Rebuilding client connection...")
        supabase = create_client(url, key)
    return supabase
