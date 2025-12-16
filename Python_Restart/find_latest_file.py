#!/usr/bin/env python3
import os
import time
from pathlib import Path

print("=" * 50)
print("   MQL5 Latest File Finder")
print("=" * 50)
print()

# Find all MQL5 files
mql_files = []
for ext in ['*.mq5', '*.mq4', '*.mqh']:
    mql_files.extend(Path('.').rglob(ext))

if not mql_files:
    print("❌ No MQL5 files found!")
else:
    # Sort by modification time (newest first)
    sorted_files = sorted(mql_files, key=lambda x: x.stat().st_mtime, reverse=True)

    print(f"📁 Found {len(sorted_files)} MQL5 file(s):\n")

    for i, file in enumerate(sorted_files[:20], 1):
        mtime = file.stat().st_mtime
        mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        print(f"{i}. {file}")
        print(f"   Last modified: {mod_time}")
        print()

    print("=" * 50)
    print("✅ File #1 at the TOP is your LATEST version")
    print("=" * 50)
