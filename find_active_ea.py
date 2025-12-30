#!/usr/bin/env python3
"""
Find Active EA - Identifies which EA version is currently running in MT5
Searches MT5 directories and log files to determine the active EA
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import platform
import re

def find_mt5_directories():
    """Find all possible MT5 installation directories"""
    possible_paths = []

    if platform.system() == "Windows":
        # Windows MT5 paths
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            possible_paths.append(Path(appdata) / "MetaTrader 5")

        possible_paths.extend([
            Path("C:/Program Files/MetaTrader 5"),
            Path("C:/Program Files (x86)/MetaTrader 5"),
        ])
    else:
        # Linux/Wine paths
        home = Path.home()
        possible_paths.extend([
            home / ".wine" / "drive_c" / "Program Files" / "MetaTrader 5",
            home / ".wine" / "drive_c" / "Program Files (x86)" / "MetaTrader 5",
            home / ".wine" / "drive_c" / "users" / os.environ.get('USER', 'user') / "AppData" / "Roaming" / "MetaTrader 5",
        ])

    # Find existing paths
    existing = [p for p in possible_paths if p.exists()]
    return existing

def find_compiled_eas(mt5_path):
    """Find all compiled EA files (.ex5) and their modification times"""
    experts_dir = mt5_path / "MQL5" / "Experts"

    if not experts_dir.exists():
        return []

    ea_files = []
    for ex5_file in experts_dir.rglob("*.ex5"):
        mtime = ex5_file.stat().st_mtime
        age_minutes = (datetime.now().timestamp() - mtime) / 60

        ea_files.append({
            'path': ex5_file,
            'name': ex5_file.name,
            'modified': datetime.fromtimestamp(mtime),
            'age_minutes': age_minutes,
            'size': ex5_file.stat().st_size
        })

    # Sort by modification time (most recent first)
    ea_files.sort(key=lambda x: x['modified'], reverse=True)
    return ea_files

def find_source_eas(mt5_path):
    """Find all source EA files (.mq5)"""
    experts_dir = mt5_path / "MQL5" / "Experts"

    if not experts_dir.exists():
        return []

    source_files = []
    for mq5_file in experts_dir.rglob("*.mq5"):
        mtime = mq5_file.stat().st_mtime

        source_files.append({
            'path': mq5_file,
            'name': mq5_file.name,
            'modified': datetime.fromtimestamp(mtime),
            'size': mq5_file.stat().st_size
        })

    source_files.sort(key=lambda x: x['modified'], reverse=True)
    return source_files

def read_mt5_logs(mt5_path):
    """Read MT5 log files to find EA initialization messages"""
    logs_dir = mt5_path / "MQL5" / "Logs"

    if not logs_dir.exists():
        return []

    today = datetime.now().strftime("%Y%m%d")
    log_files = list(logs_dir.glob(f"*{today}*.log"))

    if not log_files:
        # Try yesterday and recent files
        log_files = sorted(logs_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]

    ea_mentions = []

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-16-le', errors='ignore') as f:
                for line in f:
                    # Look for EA names
                    if 'InstitutionalTradingRobot' in line or 'AppleTrader' in line:
                        ea_mentions.append({
                            'log_file': log_file.name,
                            'line': line.strip()
                        })
        except Exception as e:
            print(f"Could not read log file {log_file}: {e}")

    return ea_mentions

def analyze_data_exports(mt5_path):
    """Check for recent data exports from EA"""
    files_dir = mt5_path / "MQL5" / "Files"

    if not files_dir.exists():
        return []

    exports = []

    # Look for JSON files
    for json_file in files_dir.rglob("*.json"):
        mtime = json_file.stat().st_mtime
        age_seconds = datetime.now().timestamp() - mtime

        exports.append({
            'path': json_file,
            'name': json_file.name,
            'age_seconds': age_seconds,
            'age_display': f"{age_seconds:.0f}s" if age_seconds < 60 else f"{age_seconds/60:.1f}min",
            'fresh': age_seconds < 60
        })

    exports.sort(key=lambda x: x['age_seconds'])
    return exports

def main():
    print("="*70)
    print("EA DETECTOR - Finding Your Active EA")
    print("="*70)
    print()

    # Find MT5 installations
    print("[1/5] Searching for MT5 installations...")
    mt5_dirs = find_mt5_directories()

    if not mt5_dirs:
        print("❌ No MT5 installation found!")
        print("\nMT5 might be installed in a custom location.")
        print("Please check manually using the guide in IDENTIFY_YOUR_EA.md")
        return

    print(f"✓ Found {len(mt5_dirs)} MT5 installation(s):")
    for mt5_dir in mt5_dirs:
        print(f"  → {mt5_dir}")
    print()

    # Use the first (or most likely) MT5 directory
    mt5_path = mt5_dirs[0]
    print(f"[2/5] Analyzing: {mt5_path}")
    print()

    # Find compiled EAs
    print("[3/5] Checking compiled EA files (.ex5)...")
    compiled_eas = find_compiled_eas(mt5_path)

    if compiled_eas:
        print(f"✓ Found {len(compiled_eas)} compiled EA(s):")
        for ea in compiled_eas[:5]:  # Show top 5
            age_display = f"{ea['age_minutes']:.0f} min ago" if ea['age_minutes'] < 60 else f"{ea['age_minutes']/60:.1f} hours ago"
            freshness = "🔥 ACTIVE" if ea['age_minutes'] < 10 else "⏰ RECENT" if ea['age_minutes'] < 1440 else "💤 OLD"

            print(f"  {freshness} {ea['name']}")
            print(f"     Last compiled: {ea['modified'].strftime('%Y-%m-%d %H:%M:%S')} ({age_display})")
            print(f"     Size: {ea['size']/1024:.1f} KB")
            print()
    else:
        print("❌ No compiled EA files found")
    print()

    # Check data exports
    print("[4/5] Checking for recent data exports...")
    exports = analyze_data_exports(mt5_path)

    if exports:
        print(f"✓ Found {len(exports)} exported file(s):")
        for exp in exports[:5]:
            freshness = "🔥 FRESH" if exp['fresh'] else "⏰ OLD"
            print(f"  {freshness} {exp['name']} (updated {exp['age_display']} ago)")
        print()

        if any(exp['fresh'] for exp in exports):
            print("✅ EA IS ACTIVELY RUNNING - Data is being exported!")
        else:
            print("⚠️  EA may not be running - No recent exports")
    else:
        print("❌ No exported data files found - EA may not be exporting")
    print()

    # Check logs
    print("[5/5] Checking MT5 logs for EA activity...")
    log_mentions = read_mt5_logs(mt5_path)

    if log_mentions:
        print(f"✓ Found {len(log_mentions)} EA mention(s) in logs:")
        for mention in log_mentions[-10:]:  # Show last 10
            print(f"  → {mention['line'][:100]}")
        print()
    else:
        print("⚠️  No EA mentions found in recent logs")
    print()

    # Final determination
    print("="*70)
    print("DETERMINATION")
    print("="*70)

    if compiled_eas:
        most_recent = compiled_eas[0]

        if most_recent['age_minutes'] < 10:
            print(f"✅ ACTIVE EA DETECTED: {most_recent['name']}")
            print(f"   Last compiled: {most_recent['modified']}")

            # Try to identify version
            if 'Institutional' in most_recent['name']:
                size_kb = most_recent['size'] / 1024
                if size_kb > 70:
                    print("   Likely version: MLALGO (81KB source)")
                else:
                    print("   Likely version: Advisor_Restart (55KB source)")
            elif 'AppleTrader' in most_recent['name']:
                print("   EA Type: AppleTrader")

        elif most_recent['age_minutes'] < 1440:  # 24 hours
            print(f"⚠️  POSSIBLY ACTIVE: {most_recent['name']}")
            print(f"   Last compiled: {most_recent['modified']}")
            print("   (Not compiled recently - may not be current)")
        else:
            print(f"❌ NO RECENT EA ACTIVITY")
            print("   Last EA compiled over 24 hours ago")
    else:
        print("❌ NO EA DETECTED")
        print("   No compiled EA files found in MT5 directory")

    print()
    print("="*70)
    print("NEXT STEPS")
    print("="*70)
    print()
    print("1. Open MT5 and check if an EA is attached to your chart")
    print("2. Right-click chart → Expert Advisors → Properties")
    print("3. Check the 'Inputs' tab - send me the first 5 settings")
    print()
    print("OR send me a screenshot of your MT5 window!")
    print()

if __name__ == "__main__":
    main()
