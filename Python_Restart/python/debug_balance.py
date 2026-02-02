"""
Balance Diagnostic Tool
Checks the actual balance values being read and displayed
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.data_manager import data_manager
from core.demo_mode_manager import demo_mode_manager, is_demo_mode
from core.mt5_connector import mt5_connector
import time

print("=" * 80)
print("BALANCE DIAGNOSTIC TOOL")
print("=" * 80)

# Check demo mode status
print(f"\n1. Demo Mode Status: {'DEMO' if is_demo_mode() else 'LIVE'}")
print(f"   Demo Mode Flag: {demo_mode_manager._demo_mode}")

# Check MT5 connector status
print(f"\n2. MT5 Connector Status:")
print(f"   Connected: {mt5_connector.is_connected}")
print(f"   Data Directory: {mt5_connector.data_dir}")
print(f"   Market Data File: {mt5_connector.market_data_file}")
if mt5_connector.market_data_file:
    exists = mt5_connector.market_data_file.exists()
    print(f"   File Exists: {exists}")
    if exists:
        print(f"   Last Modified: {mt5_connector.market_data_file.stat().st_mtime}")

# Check data_manager account data
print(f"\n3. Data Manager Account Data:")
print(f"   Balance: ${data_manager.account.get('balance', 0):,.2f}")
print(f"   Equity: ${data_manager.account.get('equity', 0):,.2f}")
print(f"   Profit: ${data_manager.account.get('profit', 0):,.2f}")
print(f"   Daily P&L: ${data_manager.account.get('daily_pnl', 0):,.2f}")
print(f"   Last Update: {data_manager.last_update}")

# Check MT5 connector cached data
print(f"\n4. MT5 Connector Cached Data:")
if mt5_connector.last_data:
    account_keys = [k for k in mt5_connector.last_data.keys()
                    if 'account' in k.lower() or 'balance' in k.lower()
                    or 'equity' in k.lower() or 'pnl' in k.lower()]
    for key in account_keys:
        value = mt5_connector.last_data.get(key)
        print(f"   {key}: {value}")
else:
    print("   No cached data available")

# Check raw data
print(f"\n5. Last Raw Data from EA:")
if data_manager.last_raw_data:
    account_keys = [k for k in data_manager.last_raw_data.keys()
                    if 'account' in k.lower() or 'balance' in k.lower()
                    or 'equity' in k.lower() or 'pnl' in k.lower()]
    for key in account_keys:
        value = data_manager.last_raw_data.get(key)
        print(f"   {key}: {value}")
else:
    print("   No raw data stored")

# Try to read the JSON file directly
print(f"\n6. Reading JSON File Directly:")
if mt5_connector.market_data_file and mt5_connector.market_data_file.exists():
    try:
        import json
        with open(mt5_connector.market_data_file, 'r') as f:
            data = json.load(f)

        print(f"   account_balance: {data.get('account_balance', 'NOT FOUND')}")
        print(f"   account_equity: {data.get('account_equity', 'NOT FOUND')}")
        print(f"   total_pnl: {data.get('total_pnl', 'NOT FOUND')}")
        print(f"   today_pnl: {data.get('today_pnl', 'NOT FOUND')}")
    except Exception as e:
        print(f"   Error reading file: {e}")
else:
    print("   File not accessible")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)

if is_demo_mode():
    print("⚠️  ISSUE: Demo mode is ACTIVE - showing fake generated data")
    print("   SOLUTION: Switch to LIVE mode in the application")
elif not mt5_connector.is_connected:
    print("⚠️  ISSUE: MT5 connector is NOT connected")
    print("   SOLUTION: Ensure EA is running and exporting data")
elif data_manager.account.get('balance', 0) == 0:
    print("⚠️  ISSUE: Balance is 0 - no data received yet")
    print("   SOLUTION: Wait for EA to export data, or check file permissions")
else:
    balance = data_manager.account.get('balance', 0)
    equity = data_manager.account.get('equity', 0)
    print(f"✓ Data looks valid:")
    print(f"  Python shows: Balance=${balance:,.2f}, Equity=${equity:,.2f}")
    print(f"  Check if this matches MT5 terminal values")
    if abs(balance - equity) > 1:
        diff = equity - balance
        print(f"  Difference: ${diff:,.2f} (likely floating P&L from open positions)")

print("=" * 80)
