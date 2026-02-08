from db import get_db
import json
import os

supabase = get_db()
if not supabase:
    print("Supabase not connected")
    exit(1)

res = supabase.table("videos").select("id, status, created_at").order("created_at", desc=True).limit(50).execute()
print(json.dumps(res.data, indent=2))

# Also check how many are queued/processing
queued = [v for v in res.data if v['status'] == 'queued']
proc = [v for v in res.data if v['status'] == 'processing']
comp = [v for v in res.data if v['status'] == 'completed']
fail = [v for v in res.data if v['status'] == 'failed']

print(f"Summary: Queued: {len(queued)}, Processing: {len(proc)}, Completed: {len(comp)}, Failed: {len(fail)}")
