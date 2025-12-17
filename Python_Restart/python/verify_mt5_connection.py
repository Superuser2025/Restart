"""
MT5 Connection Verification Script
Run this to verify MT5 EA is connected and sending data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.mt5_connector import mt5_connector
from core.data_manager import data_manager
from core.demo_mode_manager import demo_mode_manager, is_demo_mode
import time


def verify_mt5_connection():
    """Verify MT5 connection and data flow"""

    print("=" * 60)
    print("AppleTrader Pro - MT5 Connection Verification")
    print("=" * 60)
    print()

    # Check 1: MT5 Data Directory
    print("1. Checking MT5 Data Directory...")
    data_dir = mt5_connector.get_data_directory()

    if data_dir:
        print(f"   ✓ MT5 Data Directory: {data_dir}")

        market_data_file = data_dir / "market_data.json"
        if market_data_file.exists():
            print(f"   ✓ market_data.json exists")
            file_size = market_data_file.stat().st_size
            print(f"   ✓ File size: {file_size} bytes")

            # Check file age
            import datetime
            modified_time = datetime.datetime.fromtimestamp(market_data_file.stat().st_mtime)
            age_seconds = (datetime.datetime.now() - modified_time).total_seconds()
            print(f"   ✓ Last modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')} ({age_seconds:.0f}s ago)")

            if age_seconds < 60:
                print("   ✓ File is FRESH (MT5 EA is likely running)")
            else:
                print(f"   ⚠️ WARNING: File is {age_seconds:.0f}s old (MT5 EA may not be running)")
        else:
            print("   ✗ market_data.json NOT FOUND")
            print("   → MT5 EA is not running or not configured correctly")
    else:
        print("   ✗ MT5 Data Directory not found")
        print("   → Expected location: %APPDATA%\\MetaQuotes\\Terminal\\Common\\Files\\AppleTrader")
        return False

    print()

    # Check 2: MT5 Connection Status
    print("2. Checking MT5 Connection Status...")
    is_connected = mt5_connector.is_connection_active()

    if is_connected:
        print("   ✓ MT5 Connector: CONNECTED")
    else:
        print("   ✗ MT5 Connector: DISCONNECTED")
        print("   → Waiting 5 seconds for connection...")

        # Wait and retry
        time.sleep(5)
        mt5_connector.update_data()
        is_connected = mt5_connector.is_connection_active()

        if is_connected:
            print("   ✓ MT5 Connector: NOW CONNECTED")
        else:
            print("   ✗ MT5 Connector: STILL DISCONNECTED")
            print("   → Make sure MT5 Expert Advisor is running")
            return False

    print()

    # Check 3: Data Flow
    print("3. Checking Data Flow...")

    if mt5_connector.last_data:
        print("   ✓ Data received from MT5")
        print(f"   ✓ Data keys: {list(mt5_connector.last_data.keys())[:10]}...")

        # Show some sample data
        if 'symbol' in mt5_connector.last_data:
            print(f"   ✓ Symbol: {mt5_connector.last_data['symbol']}")
        if 'bid' in mt5_connector.last_data:
            print(f"   ✓ Bid: {mt5_connector.last_data['bid']}")
        if 'ask' in mt5_connector.last_data:
            print(f"   ✓ Ask: {mt5_connector.last_data['ask']}")
    else:
        print("   ✗ No data received from MT5")
        return False

    print()

    # Check 4: Demo Mode Status
    print("4. Checking Demo/Live Mode Status...")
    current_mode = "DEMO" if is_demo_mode() else "LIVE"
    print(f"   Current Mode: {current_mode}")

    if is_demo_mode():
        print("   ℹ️ Application is in DEMO mode (using fake data)")
        print("   → To enable LIVE mode, see instructions below")
    else:
        print("   ✓ Application is in LIVE mode (using real MT5 data)")

    print()

    # Check 5: Data Manager
    print("5. Checking Data Manager...")
    is_fresh = data_manager.is_data_fresh(max_age_seconds=30)

    if is_fresh:
        print("   ✓ Data Manager: Data is FRESH (< 30 seconds old)")
        print(f"   ✓ Last Update: {data_manager.last_update}")
    else:
        print("   ⚠️ Data Manager: Data is STALE (> 30 seconds old)")
        if data_manager.last_update:
            print(f"   Last Update: {data_manager.last_update}")

    print()
    print("=" * 60)

    if is_connected and is_fresh:
        print("✓ ALL CHECKS PASSED - MT5 Connection is ACTIVE")
        print()
        print("Next Steps:")
        print("1. Run the main application: python main.py")

        if is_demo_mode():
            print("2. Toggle to LIVE mode using menu: Settings → Enable Live Mode")
        else:
            print("2. Application is already in LIVE mode - widgets showing real data")

        print()
        return True
    else:
        print("✗ SOME CHECKS FAILED - See errors above")
        print()
        print("Troubleshooting:")
        print("1. Make sure MetaTrader 5 is running")
        print("2. Make sure Expert Advisor (EA) is loaded on a chart")
        print("3. Check EA is not paused (AutoTrading button should be ON)")
        print("4. Verify EA file location: MQL5\\Experts\\AppleTrader\\...")
        print()
        return False


if __name__ == "__main__":
    success = verify_mt5_connection()
    sys.exit(0 if success else 1)
