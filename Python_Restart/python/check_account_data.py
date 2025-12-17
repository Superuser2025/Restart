"""
Check what account data is being received from MT5
Run this while application is running in LIVE mode
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.data_manager import data_manager
from core.mt5_connector import mt5_connector


def check_account_data():
    """Check what account data MT5 is sending"""

    print("=" * 70)
    print("Account Data Diagnostic")
    print("=" * 70)
    print()

    # Check raw MT5 data
    print("1. Raw MT5 Data Keys:")
    if mt5_connector.last_data:
        keys = list(mt5_connector.last_data.keys())
        print(f"   Total keys: {len(keys)}")
        print(f"   Keys: {keys[:20]}...")  # First 20 keys
        print()

        # Check for account-related keys
        account_keys = [k for k in keys if 'account' in k.lower() or 'balance' in k.lower() or 'equity' in k.lower()]
        print(f"   Account-related keys: {account_keys}")
        print()

        # Show values
        for key in account_keys:
            print(f"   {key} = {mt5_connector.last_data.get(key)}")
        print()
    else:
        print("   ✗ No data from MT5")
        print()

    # Check data_manager account
    print("2. Data Manager Account Summary:")
    account = data_manager.get_account_summary()
    print(f"   Balance: ${account.get('balance', 0):,.2f}")
    print(f"   Equity: ${account.get('equity', 0):,.2f}")
    print(f"   Profit: ${account.get('profit', 0):,.2f}")
    print(f"   Daily P&L: ${account.get('daily_pnl', 0):,.2f}")
    print(f"   Margin: ${account.get('margin', 0):,.2f}")
    print(f"   Margin Free: ${account.get('margin_free', 0):,.2f}")
    print(f"   Currency: {account.get('currency', 'N/A')}")
    print()

    # Check if data is fresh
    print("3. Data Freshness:")
    if data_manager.last_update:
        from datetime import datetime
        age = (datetime.now() - data_manager.last_update).total_seconds()
        print(f"   Last Update: {data_manager.last_update}")
        print(f"   Age: {age:.1f} seconds")
    else:
        print("   ✗ No updates yet")
    print()

    # Diagnosis
    print("=" * 70)
    print("DIAGNOSIS:")
    print()

    if mt5_connector.last_data and len(mt5_connector.last_data) > 0:
        print("✓ MT5 Connector receiving data")

        if account.get('balance', 0) == 0:
            print("✗ Account balance is $0.00")
            print()
            print("PROBLEM: MT5 EA is NOT sending account information")
            print()
            print("Possible causes:")
            print("1. EA doesn't have account data access")
            print("2. EA is not exporting account fields to JSON")
            print("3. Field names don't match what data_manager expects")
            print()
            print("SOLUTION:")
            print("Check MT5 EA code - it should export:")
            print("  - account_balance")
            print("  - account_equity")
            print("  - total_pnl")
            print("  - today_pnl")
            print()
    else:
        print("✗ MT5 Connector not receiving any data")
        print("  Check MT5 EA is running")

    print("=" * 70)


if __name__ == "__main__":
    check_account_data()
