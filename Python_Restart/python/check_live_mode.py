"""
Live Mode Verification - Check if widgets are using real MT5 data
Run this while the main application is running
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.demo_mode_manager import demo_mode_manager, is_demo_mode
from core.mt5_connector import mt5_connector
from core.data_manager import data_manager


def check_live_mode_status():
    """Check if application is truly using live MT5 data"""

    print("=" * 70)
    print("Live Mode Verification - Data Source Check")
    print("=" * 70)
    print()

    # Check 1: Demo Mode Flag
    print("1. Demo Mode Flag:")
    if is_demo_mode():
        print("   ✗ demo_mode = True (Application is in DEMO mode)")
        print("   → Widgets are using FAKE generated data")
        print()
        print("   FIX: In the application, go to Settings → Enable Live Mode")
        print()
        return False
    else:
        print("   ✓ demo_mode = False (Application is in LIVE mode)")
        print()

    # Check 2: MT5 Connector Status
    print("2. MT5 Connector:")
    is_connected = mt5_connector.is_connection_active()

    if is_connected:
        print("   ✓ MT5 Connector: CONNECTED")
        print()
    else:
        print("   ✗ MT5 Connector: DISCONNECTED")
        print("   → No live data can flow even if mode is LIVE")
        print()
        return False

    # Check 3: Last MT5 Data
    print("3. MT5 Data Content:")
    if mt5_connector.last_data:
        print("   ✓ Data received from MT5")

        # Show key fields
        symbol = mt5_connector.last_data.get('symbol', 'N/A')
        bid = mt5_connector.last_data.get('bid', 0)
        ask = mt5_connector.last_data.get('ask', 0)

        print(f"   Symbol: {symbol}")
        print(f"   Bid: {bid}")
        print(f"   Ask: {ask}")
        print()

        # Get more symbols if available
        print("   Available Data Keys (first 15):")
        keys = list(mt5_connector.last_data.keys())[:15]
        for key in keys:
            print(f"     - {key}")
        print()
    else:
        print("   ✗ No data in MT5 connector")
        print()

    # Check 4: Data Manager Status
    print("4. Data Manager:")
    if data_manager.last_update:
        from datetime import datetime
        age = (datetime.now() - data_manager.last_update).total_seconds()
        print(f"   ✓ Last Update: {data_manager.last_update}")
        print(f"   ✓ Age: {age:.1f} seconds")

        if age < 10:
            print("   ✓ Data is VERY FRESH (< 10s)")
        elif age < 30:
            print("   ✓ Data is FRESH (< 30s)")
        else:
            print(f"   ⚠️ Data is OLD ({age:.0f}s)")
        print()

        # Show account data
        account = data_manager.get_account_summary()
        print("   Account Data:")
        print(f"     Balance: ${account.get('balance', 0):.2f}")
        print(f"     Equity: ${account.get('equity', 0):.2f}")
        print(f"     Profit: ${account.get('profit', 0):.2f}")
        print()
    else:
        print("   ⚠️ Data Manager not yet updated")
        print()

    # Check 5: Compare with Demo Mode Manager
    print("5. Widget Data Source:")
    print("   When widgets call is_demo_mode():")
    print(f"   → Returns: {is_demo_mode()}")
    print()

    if is_demo_mode():
        print("   ✗ Widgets will use: demo_mode_manager.generate_demo_*()")
        print("   → Fake/generated data")
    else:
        print("   ✓ Widgets will use: mt5_connector.get_*()")
        print("   → Real MT5 data")
    print()

    print("=" * 70)

    if not is_demo_mode() and is_connected:
        print("✓ LIVE MODE IS ACTIVE")
        print()
        print("Your widgets ARE using real MT5 data!")
        print()
        print("Verification Tips:")
        print("1. Compare prices in widgets with MT5 terminal (should match)")
        print("2. Check account balance in dashboard cards (should match MT5)")
        print("3. Look for REAL symbols (not just EURUSD/GBPUSD)")
        print("4. Opportunity cards should show actual market patterns")
        print("5. Status bar should show GREEN and say 'LIVE'")
        print()
        return True
    else:
        print("✗ LIVE MODE NOT FULLY ACTIVE")
        print()
        if is_demo_mode():
            print("Issue: Application still in DEMO mode")
            print("Fix: Settings → Enable Live Mode in GUI")
        if not is_connected:
            print("Issue: MT5 not connected")
            print("Fix: Ensure MT5 EA is running")
        print()
        return False


if __name__ == "__main__":
    success = check_live_mode_status()
    sys.exit(0 if success else 1)
