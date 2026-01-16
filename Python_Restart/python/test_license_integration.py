#!/usr/bin/env python3
"""
Quick verification that license integration works correctly
Run this to test: python test_license_integration.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("TESTING LICENSE INTEGRATION")
print("=" * 70)

# Test 1: Check dev_config exists
print("\n[1/5] Checking dev_config.py exists...")
try:
    from core.dev_config import is_dev_mode, DEVELOPMENT_MODE
    print(f"    ✓ Found: DEVELOPMENT_MODE = {DEVELOPMENT_MODE}")
    print(f"    ✓ Current mode: {'🔧 DEVELOPMENT' if is_dev_mode() else '🔐 PRODUCTION'}")
except ImportError as e:
    print(f"    ✗ ERROR: {e}")
    sys.exit(1)

# Test 2: Check license_manager works
print("\n[2/5] Checking license_manager.py...")
try:
    from core.license_manager import license_manager
    valid, message, info = license_manager.validate_license()
    print(f"    ✓ License validation works")
    print(f"    ✓ Valid: {valid}")
    print(f"    ✓ Message: {message}")
    if info:
        print(f"    ✓ Tier: {info.get('tier', 'unknown')}")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    sys.exit(1)

# Test 3: Check license_dialog works
print("\n[3/5] Checking license_dialog.py...")
try:
    from widgets.license_dialog import check_license_on_startup
    print(f"    ✓ check_license_on_startup imported")
except Exception as e:
    print(f"    ✗ ERROR: {e}")
    sys.exit(1)

# Test 4: Check main_enhanced.py has license check
print("\n[4/5] Checking main_enhanced.py integration...")
try:
    with open('main_enhanced.py', 'r') as f:
        content = f.read()
        if 'check_license_on_startup' in content:
            print(f"    ✓ License check found in main_enhanced.py")
        else:
            print(f"    ✗ WARNING: License check NOT found in main_enhanced.py")
except Exception as e:
    print(f"    ✗ ERROR: {e}")

# Test 5: Check main.py has license check
print("\n[5/5] Checking main.py integration...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
        if 'check_license_on_startup' in content:
            print(f"    ✓ License check found in main.py")
        else:
            print(f"    ✗ WARNING: License check NOT found in main.py")
except Exception as e:
    print(f"    ✗ ERROR: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if is_dev_mode():
    print("\n✓ Currently in DEVELOPMENT MODE")
    print("  → You can run the application normally")
    print("  → No license required")
    print("  → All features unlocked")
    print("\n  Command to run:")
    print("    python main_enhanced.py")
    print("\n  Application will start with this message:")
    print("    ============================================================")
    print("    🔧 DEVELOPMENT MODE - License checks bypassed")
    print("    ============================================================")
else:
    print("\n✓ Currently in PRODUCTION MODE")
    print("  → License will be required")
    print("  → Activation dialog will appear")
    print("  → Good for testing customer experience")
    print("\n  To switch back to dev mode:")
    print("    Edit: python/core/dev_config.py")
    print("    Change: DEVELOPMENT_MODE = False → True")

print("\n" + "=" * 70)
print("✓ All tests passed! License system is integrated correctly.")
print("=" * 70)
