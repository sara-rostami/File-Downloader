#!/usr/bin/env python3
"""
پاک‌سازی فایل‌های منقضی‌شده در downloads/
بر اساس فایل downloads/downloads_meta.json
"""

import os
import json
import subprocess
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = "downloads"
META_FILE = os.path.join(OUTPUT_DIR, "downloads_meta.json")

def run_cmd(cmd):
    subprocess.run(cmd, check=True, shell=True)

def is_expired(entry):
    """بررسی expired بودن یک رکورد"""
    download_time = datetime.fromisoformat(entry["download_time"])
    retention_days = entry["retention_days"]
    expiration_time = download_time + timedelta(days=retention_days)
    now = datetime.now(timezone.utc)
    # مقایسه آگاه از منطقه زمانی
    if download_time.tzinfo is None:
        # فرض UTC اگر tz نبود
        download_time = download_time.replace(tzinfo=timezone.utc)
        expiration_time = download_time + timedelta(days=retention_days)
    return now > expiration_time

def main():
    if not os.path.exists(META_FILE):
        print("No metadata file found. Nothing to clean.")
        return

    with open(META_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    updated_metadata = []
    removed_files = []

    for entry in metadata:
        if is_expired(entry):
            file_path = os.path.join(OUTPUT_DIR, entry["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
                removed_files.append(entry["filename"])
                print(f"Removed expired file: {entry['filename']}")
        else:
            updated_metadata.append(entry)

    if removed_files:
        # ذخیره متادیتای به‌روز شده
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_metadata, f, indent=2, ensure_ascii=False)

        # git commit
        run_cmd("git config user.name 'github-actions[bot]'")
        run_cmd("git config user.email 'github-actions[bot]@users.noreply.github.com'")
        run_cmd("git add -A")
        diff = subprocess.run("git diff --cached --quiet", shell=True)
        if diff.returncode != 0:
            commit_msg = f"Auto-cleanup expired files: {', '.join(removed_files)}"
            run_cmd(f'git commit -m "{commit_msg}"')
            run_cmd("git push")
        else:
            print("No changes after cleanup.")
    else:
        print("No expired files found.")

if __name__ == "__main__":
    main()
