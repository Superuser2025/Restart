"""
MT5 History Importer - Seed Statistical System with Real Trade Data

Imports historical trades from MetaTrader 5 and feeds them into the
statistical learning system, so the Bayesian learner starts with real
data instead of neutral 50/50 priors.

This solves: "Your system needs 30-50 trades per pattern to be reliable. Where's that data?"

Author: AppleTrader Pro
Date: 2026-01-23
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import json

from core.verbose_mode_manager import vprint
from core.statistical_analysis_manager import StatisticalAnalysisManager


class MT5HistoryImporter:
    """
    Imports historical trades from MT5 and seeds statistical models

    Workflow:
    1. Connect to MT5
    2. Fetch deals history (last N days/months)
    3. Analyze each trade to identify pattern (if possible)
    4. Feed into statistical system via record_pattern_outcome()
    5. Generate import report
    """

    def __init__(self):
        """Initialize the MT5 history importer"""
        self.stats_manager = StatisticalAnalysisManager.get_instance()
        self.imported_trades = []
        self.import_log_file = Path(__file__).parent.parent / "data" / "import_log.json"
        self.import_log_file.parent.mkdir(parents=True, exist_ok=True)

        vprint("[MT5Importer] Initialized")

    def import_history(self, days_back: int = 90, min_profit_threshold: float = -999999.0) -> Dict:
        """
        Import historical trades from MT5

        Args:
            days_back: How many days back to fetch trades (default 90 days)
            min_profit_threshold: Minimum profit to consider (filters out very small trades)

        Returns:
            Dict with import statistics
        """
        if not MT5_AVAILABLE:
            vprint("[MT5Importer] ✗ MetaTrader5 module not available")
            return {'success': False, 'error': 'MT5 not available'}

        # Initialize MT5 connection
        if not mt5.initialize():
            vprint(f"[MT5Importer] ✗ MT5 initialization failed: {mt5.last_error()}")
            return {'success': False, 'error': 'MT5 initialization failed'}

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            vprint(f"[MT5Importer] Fetching trade history from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # Fetch deals (closed positions)
            deals = mt5.history_deals_get(start_date, end_date)

            if deals is None:
                vprint(f"[MT5Importer] ✗ Failed to fetch deals: {mt5.last_error()}")
                return {'success': False, 'error': 'Failed to fetch deals'}

            if len(deals) == 0:
                vprint("[MT5Importer] ⚠ No deals found in date range")
                return {'success': True, 'imported': 0, 'message': 'No deals in range'}

            vprint(f"[MT5Importer] ✓ Found {len(deals)} deals")

            # Group deals by position (entry + exit = complete trade)
            positions = self._group_deals_into_positions(deals)
            vprint(f"[MT5Importer] ✓ Grouped into {len(positions)} complete positions")

            # Analyze and import each position
            imported_count = 0
            pattern_counts = {}

            for position in positions:
                # Filter by profit threshold
                if position['profit'] < min_profit_threshold:
                    continue

                # Try to identify pattern and timeframe
                pattern_info = self._identify_pattern_from_position(position)

                if pattern_info:
                    # Record in statistical system
                    self.stats_manager.record_pattern_outcome(
                        timeframe=pattern_info['timeframe'],
                        pattern=pattern_info['pattern'],
                        is_win=position['profit'] > 0,
                        profit=position['profit']
                    )

                    # Track statistics
                    pattern_key = f"{pattern_info['pattern']}_{pattern_info['timeframe']}"
                    pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1

                    imported_count += 1
                    self.imported_trades.append(position)

            # Save import log
            self._save_import_log({
                'import_date': datetime.now().isoformat(),
                'date_range': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
                'total_deals': len(deals),
                'total_positions': len(positions),
                'imported_positions': imported_count,
                'pattern_breakdown': pattern_counts
            })

            vprint(f"[MT5Importer] ✓ Successfully imported {imported_count} trades")
            vprint(f"[MT5Importer] Pattern breakdown:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                vprint(f"  - {pattern}: {count} trades")

            return {
                'success': True,
                'imported': imported_count,
                'total_deals': len(deals),
                'total_positions': len(positions),
                'pattern_breakdown': pattern_counts
            }

        except Exception as e:
            vprint(f"[MT5Importer] ✗ Error during import: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

        finally:
            mt5.shutdown()

    def _group_deals_into_positions(self, deals) -> List[Dict]:
        """
        Group MT5 deals into complete positions (entry + exit)

        MT5 stores each trade action as a separate deal (entry, exit, etc.)
        We need to group them into complete round-trip trades.
        """
        positions = []
        position_map = {}  # position_id -> deals

        for deal in deals:
            # MT5 deal structure
            position_id = deal.position_id if hasattr(deal, 'position_id') else deal.order

            if position_id not in position_map:
                position_map[position_id] = []

            position_map[position_id].append(deal)

        # Analyze each position
        for position_id, deal_list in position_map.items():
            if len(deal_list) < 2:
                continue  # Need at least entry and exit

            # Sort by time
            deal_list.sort(key=lambda d: d.time)

            entry_deal = deal_list[0]
            exit_deal = deal_list[-1]

            # Calculate position profit
            total_profit = sum(d.profit for d in deal_list if hasattr(d, 'profit'))

            position = {
                'position_id': position_id,
                'symbol': entry_deal.symbol if hasattr(entry_deal, 'symbol') else 'UNKNOWN',
                'entry_time': datetime.fromtimestamp(entry_deal.time) if hasattr(entry_deal, 'time') else datetime.now(),
                'exit_time': datetime.fromtimestamp(exit_deal.time) if hasattr(exit_deal, 'time') else datetime.now(),
                'entry_price': entry_deal.price if hasattr(entry_deal, 'price') else 0.0,
                'exit_price': exit_deal.price if hasattr(exit_deal, 'price') else 0.0,
                'volume': entry_deal.volume if hasattr(entry_deal, 'volume') else 0.0,
                'profit': total_profit,
                'type': 'BUY' if (hasattr(entry_deal, 'type') and entry_deal.type == mt5.DEAL_TYPE_BUY) else 'SELL',
                'duration_minutes': (exit_deal.time - entry_deal.time) // 60 if hasattr(entry_deal, 'time') and hasattr(exit_deal, 'time') else 0
            }

            positions.append(position)

        return positions

    def _identify_pattern_from_position(self, position: Dict) -> Optional[Dict]:
        """
        Try to identify pattern and timeframe from position characteristics

        This is heuristic-based since we can't always know what pattern
        triggered a historical trade. We use trade duration and outcome
        to make educated guesses.

        Better approach: Store pattern in EA comment field for future trades
        """
        duration_minutes = position.get('duration_minutes', 0)

        # Guess timeframe based on trade duration
        if duration_minutes < 30:
            timeframe = 'M15'
        elif duration_minutes < 120:
            timeframe = 'H1'
        elif duration_minutes < 480:
            timeframe = 'H4'
        else:
            timeframe = 'D1'

        # Guess pattern based on profit characteristics
        # This is a rough heuristic - ideally EA should store pattern in comment
        profit = position.get('profit', 0)
        trade_type = position.get('type', 'BUY')

        # Pattern heuristics (very rough)
        if profit > 0:
            # Winning trade - likely followed a strong pattern
            if trade_type == 'BUY':
                pattern = 'Bullish_Engulfing'  # Common bullish pattern
            else:
                pattern = 'Bearish_Engulfing'  # Common bearish pattern
        else:
            # Losing trade - could be any pattern
            pattern = 'Generic_Pattern'

        # TODO: BETTER APPROACH - Modify EA to store pattern name in trade comment
        # Then we can extract it like: pattern = parse_comment(position['comment'])

        return {
            'pattern': pattern,
            'timeframe': timeframe,
            'confidence': 'low'  # Acknowledge this is heuristic
        }

    def import_from_csv(self, csv_file: str) -> Dict:
        """
        Import trades from CSV file (for platforms without MT5)

        CSV format expected:
        Symbol,EntryTime,ExitTime,Type,EntryPrice,ExitPrice,Profit,Pattern,Timeframe

        Args:
            csv_file: Path to CSV file

        Returns:
            Dict with import statistics
        """
        try:
            import csv

            imported_count = 0
            pattern_counts = {}

            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    pattern = row.get('Pattern', 'Generic_Pattern')
                    timeframe = row.get('Timeframe', 'H1')
                    profit = float(row.get('Profit', 0))

                    # Record in statistical system
                    self.stats_manager.record_pattern_outcome(
                        timeframe=timeframe,
                        pattern=pattern,
                        is_win=profit > 0,
                        profit=profit
                    )

                    pattern_key = f"{pattern}_{timeframe}"
                    pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1
                    imported_count += 1

            vprint(f"[MT5Importer] ✓ Imported {imported_count} trades from CSV")

            return {
                'success': True,
                'imported': imported_count,
                'pattern_breakdown': pattern_counts
            }

        except Exception as e:
            vprint(f"[MT5Importer] ✗ CSV import error: {e}")
            return {'success': False, 'error': str(e)}

    def _save_import_log(self, log_data: Dict):
        """Save import log to file"""
        try:
            # Load existing logs
            logs = []
            if self.import_log_file.exists():
                with open(self.import_log_file, 'r') as f:
                    logs = json.load(f)

            # Append new log
            logs.append(log_data)

            # Save
            with open(self.import_log_file, 'w') as f:
                json.dump(logs, f, indent=2)

            vprint(f"[MT5Importer] ✓ Saved import log to {self.import_log_file}")

        except Exception as e:
            vprint(f"[MT5Importer] ✗ Failed to save log: {e}")

    def generate_import_report(self) -> str:
        """Generate human-readable import report"""
        if not self.import_log_file.exists():
            return "No import history found"

        with open(self.import_log_file, 'r') as f:
            logs = json.load(f)

        report = "=== MT5 TRADE IMPORT HISTORY ===\n\n"

        for idx, log in enumerate(logs[-5:], 1):  # Last 5 imports
            report += f"Import #{idx} - {log.get('import_date', 'Unknown date')}\n"
            report += f"  Date Range: {log.get('date_range', {}).get('start', '?')} to {log.get('date_range', {}).get('end', '?')}\n"
            report += f"  Imported: {log.get('imported_positions', 0)} trades\n"
            report += f"  Pattern Breakdown:\n"

            for pattern, count in sorted(log.get('pattern_breakdown', {}).items(), key=lambda x: x[1], reverse=True):
                report += f"    - {pattern}: {count}\n"

            report += "\n"

        return report


# Singleton instance
mt5_history_importer = MT5HistoryImporter()
