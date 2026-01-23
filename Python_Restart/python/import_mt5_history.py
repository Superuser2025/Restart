#!/usr/bin/env python3
"""
Import MT5 Trade History - CLI Tool

Quick script to import historical trades from MetaTrader 5 into
the statistical learning system.

Usage:
    python import_mt5_history.py              # Import last 90 days
    python import_mt5_history.py --days 180   # Import last 180 days
    python import_mt5_history.py --csv trades.csv  # Import from CSV

Author: AppleTrader Pro
Date: 2026-01-23
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.mt5_history_importer import mt5_history_importer
from core.statistical_analysis_manager import StatisticalAnalysisManager


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import MT5 trade history into statistical system')

    parser.add_argument('--days', type=int, default=90,
                        help='Number of days back to import (default: 90)')

    parser.add_argument('--csv', type=str,
                        help='Import from CSV file instead of MT5')

    parser.add_argument('--report', action='store_true',
                        help='Show import history report')

    args = parser.parse_args()

    print("=" * 60)
    print("  MT5 TRADE HISTORY IMPORTER")
    print("  Statistical Learning System Seed Data")
    print("=" * 60)
    print()

    # Show report if requested
    if args.report:
        print(mt5_history_importer.generate_import_report())
        return

    # Import from CSV
    if args.csv:
        print(f"Importing from CSV: {args.csv}")
        print()

        result = mt5_history_importer.import_from_csv(args.csv)

        if result['success']:
            print(f"✓ Successfully imported {result['imported']} trades!")
            print()
            print("Pattern Breakdown:")
            for pattern, count in sorted(result['pattern_breakdown'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {pattern}: {count} trades")
        else:
            print(f"✗ Import failed: {result.get('error', 'Unknown error')}")

        return

    # Import from MT5
    print(f"Importing trades from last {args.days} days...")
    print("This will:")
    print("  1. Connect to MetaTrader 5")
    print("  2. Fetch closed trades")
    print("  3. Analyze patterns (heuristic)")
    print("  4. Seed statistical models")
    print()
    print("Starting import...")
    print()

    result = mt5_history_importer.import_history(days_back=args.days)

    if result['success']:
        print()
        print("=" * 60)
        print("✓ IMPORT SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"Total Deals: {result.get('total_deals', 0)}")
        print(f"Complete Positions: {result.get('total_positions', 0)}")
        print(f"Imported to Stats: {result.get('imported', 0)}")
        print()
        print("Pattern Breakdown:")
        for pattern, count in sorted(result.get('pattern_breakdown', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"  - {pattern}: {count} trades")
        print()
        print("Your Bayesian learner now has REAL historical data!")
        print()

        # Show current statistics
        stats_manager = StatisticalAnalysisManager.get_instance()
        print("Current Statistical System Status:")
        for tf in ['M15', 'H1', 'H4', 'D1']:
            tf_data = stats_manager.get_timeframe_data(tf)
            total_trades = sum(p.get('trade_count', 0) for p in tf_data['patterns'].values())
            if total_trades > 0:
                print(f"  {tf}: {total_trades} trades across {len(tf_data['patterns'])} patterns")

    else:
        print()
        print("=" * 60)
        print("✗ IMPORT FAILED")
        print("=" * 60)
        print()
        print(f"Error: {result.get('error', 'Unknown error')}")
        print()

        if 'MT5 not available' in result.get('error', ''):
            print("TROUBLESHOOTING:")
            print("  1. Is MetaTrader 5 installed?")
            print("  2. Is MT5 running?")
            print("  3. Is MetaTrader5 Python package installed?")
            print("     Install: pip install MetaTrader5")
        elif 'No deals' in result.get('message', ''):
            print("TROUBLESHOOTING:")
            print("  1. Do you have closed trades in the selected period?")
            print("  2. Try increasing --days parameter")
            print("  3. Check MT5 account history tab")


if __name__ == '__main__':
    main()
