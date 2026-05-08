#!/usr/bin/env python3
"""
اسکریپت دانلود فایل و ذخیره در downloads/
ورودی: URL, retention_days, filename (اختیاری)
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
from urllib.request import urlopen, Request
import shutil

OUTPUT_DIR = "downloads"
META_FILE = os.path.join(OUTPUT_DIR, "downloads_meta.json")

def run_cmd(cmd):
    subprocess.run(cmd, check=True, shell=True)

def get_filename_from_url(url, default="downloaded_file"):
    """استخراج نام فایل از URL یا نام پیش‌فرض"""
    path = urlparse(url).path
    if path:
        name = unquote(path.split("/")[-1])
        if name:
            return name
    return default

def update_metadata(filename, url, retention_days):
    """افزودن رکورد به فایل متادیتا"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    metadata = []
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                metadata = []
    for entry in metadata:
        if entry["filename"] == filename:
            entry["download_time"] = datetime.now(timezone.utc).isoformat()
            entry["retention_days"] = retention_days
            break
    else:
        metadata.append({
            "filename": filename,
            "url": url,
            "download_time": datetime.now(timezone.utc).isoformat(),
            "retention_days": retention_days
        })
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def download_file(url, dest_path):
    """دانلود فایل با urllib (بدون وابستگی خارجی)"""
    req = Request(url, headers={"User-Agent": "GitHub-Action-Downloader"})
    with urlopen(req) as response, open(dest_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

def git_commit_and_push(message):
    """مراحل git add, commit, push"""
    run_cmd("git config user.name 'github-actions[bot]'")
    run_cmd("git config user.email 'github-actions[bot]@users.noreply.github.com'")
    run_cmd("git add -A")
    diff = subprocess.run("git diff --cached --quiet", shell=True)
    if diff.returncode != 0:
        run_cmd(f'git commit -m "{message}"')
        run_cmd("git push")
    else:
        print("No changes to commit.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python download.py <URL> <RETENTION_DAYS> [FILENAME]")
        sys.exit(1)

    url = sys.argv[1]
    retention_days = int(sys.argv[2])

    # اصلاح: فقط در صورتی filename را از argv[3] بگیر که موجود و خالی نباشد
    if len(sys.argv) > 3 and sys.argv[3].strip():
        filename = sys.argv[3].strip()
    else:
        filename = get_filename_from_url(url)

    dest_path = os.path.join(OUTPUT_DIR, filename)
    print(f"Downloading {url} -> {dest_path}")
    download_file(url, dest_path)

    update_metadata(filename, url, retention_days)
    git_commit_and_push(f"Download {filename} (expires in {retention_days} days)")

if __name__ == "__main__":
    main()
