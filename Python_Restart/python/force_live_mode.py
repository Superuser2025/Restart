"""
Force Enable Live Mode - Guaranteed Switch
This script will FORCE the application into live mode
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.demo_mode_manager import demo_mode_manager


def force_enable_live_mode():
    """Force enable live mode with verification"""

    print("=" * 60)
    print("FORCE ENABLE LIVE MODE")
    print("=" * 60)
    print()

    # Check current state
    print("Current state:")
    print(f"  demo_mode_manager._demo_mode = {demo_mode_manager._demo_mode}")
    print()

    # Force set to False (False = Live Mode)
    print("Forcing live mode...")
    demo_mode_manager._demo_mode = False

    # Verify
    print()
    print("After forcing:")
    print(f"  demo_mode_manager._demo_mode = {demo_mode_manager._demo_mode}")
    print(f"  is_demo_mode() = {demo_mode_manager.is_demo()}")
    print(f"  is_live_mode() = {demo_mode_manager.is_live()}")
    print()

    if demo_mode_manager._demo_mode == False:
        print("✓ SUCCESS - Live mode is now ENABLED")
        print()
        print("IMPORTANT: You must RESTART the application for this to take effect!")
        print()
        print("Steps:")
        print("1. Close the current application (if running)")
        print("2. Run: py main_enhanced.py")
        print("3. Application will start in LIVE mode")
        print()
    else:
        print("✗ FAILED - Could not enable live mode")
        print()

    print("=" * 60)


if __name__ == "__main__":
    force_enable_live_mode()
