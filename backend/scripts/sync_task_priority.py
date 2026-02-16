from db import get_db

supabase = get_db()

def sync():
    if not supabase:
        print("Supabase not connected")
        return

    # Fetch all queued videos
    res = supabase.table("videos").select("id, title, report_data").eq("status", "queued").execute()
    
    if not res.data:
        print("No queued videos found to sync.")
        return

    count_manual = 0
    count_tracker = 0
    
    for v in res.data:
        report_data = v.get("report_data") or {}
        if "source" in report_data:
            continue
            
        # Heuristic: If it has channel_id in report_data, it's likely from tracker
        if report_data.get("channel_id"):
            report_data["source"] = "tracker"
            count_tracker += 1
        else:
            # Otherwise assume manual (user submitted)
            report_data["source"] = "manual"
            count_manual += 1
            
        supabase.table("videos").update({"report_data": report_data}).eq("id", v["id"]).execute()

    print(f"Sync complete. Marked {count_manual} manual and {count_tracker} tracker tasks.")

if __name__ == "__main__":
    sync()
