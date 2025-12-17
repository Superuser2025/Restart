"""
Enable Live Mode - Quick Script
Switches application from DEMO to LIVE mode programmatically
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.demo_mode_manager import demo_mode_manager, is_demo_mode, set_demo_mode


def enable_live_mode():
    """Enable live mode"""

    print("=" * 60)
    print("AppleTrader Pro - Enable Live Mode")
    print("=" * 60)
    print()

    # Check current mode
    current_mode = "DEMO" if is_demo_mode() else "LIVE"
    print(f"Current Mode: {current_mode}")

    if is_demo_mode():
        print()
        print("Switching to LIVE mode...")
        set_demo_mode(False)

        print()
        print("✓ LIVE MODE ENABLED")
        print()
        print("All widgets will now use REAL MT5 data:")
        print("  - Real account balance & P/L")
        print("  - Real market prices")
        print("  - Real pattern detections")
        print("  - Real opportunities")
        print()
        print("⚠️ IMPORTANT: Make sure MT5 Expert Advisor is running!")
        print()
    else:
        print()
        print("✓ Already in LIVE mode")
        print()

    print("=" * 60)


if __name__ == "__main__":
    enable_live_mode()
