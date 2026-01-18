import os
import time

# 配置
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
MAX_AGE_DAYS = 3
TARGET_EXTENSIONS = [".mp3", ".m4a", ".mp4", ".webm", ".mov", ".avi"]
EXCLUDE_EXTENSIONS = [".jpg", ".png", ".json"] # 绝对保留缩略图和状态文件

def cleanup():
    if not os.path.exists(DOWNLOADS_DIR):
        print(f"Directory {DOWNLOADS_DIR} does not exist.")
        return

    now = time.time()
    count = 0
    freed_space = 0

    print(f"--- Starting cleanup in {DOWNLOADS_DIR} (Files older than {MAX_AGE_DAYS} days) ---")

    for filename in os.listdir(DOWNLOADS_DIR):
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        
        # 检查是否是文件
        if not os.path.isfile(file_path):
            continue

        # 获取文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        
        # 如果在排除列表中，跳过
        if ext in EXCLUDE_EXTENSIONS:
            continue
            
        # 如果在目标列表中，或者是其他大文件类型
        if ext in TARGET_EXTENSIONS or os.path.getsize(file_path) > 10 * 1024 * 1024: # 超过 10MB 的也视为潜在清理对象
            mtime = os.path.getmtime(file_path)
            age_days = (now - mtime) / (24 * 3600)
            
            if age_days > MAX_AGE_DAYS:
                size = os.path.getsize(file_path)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {filename} ({size / 1024 / 1024:.2f} MB, {age_days:.1f} days old)")
                    count += 1
                    freed_space += size
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")

    print(f"--- Cleanup completed. Removed {count} files, freed {freed_space / 1024 / 1024:.2f} MB ---")

if __name__ == "__main__":
    cleanup()
