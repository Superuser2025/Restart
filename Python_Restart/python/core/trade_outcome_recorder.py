"""
Trade Outcome Recorder - Feedback Loop for Statistical Learning

Records actual trade outcomes and feeds them back to the statistical system
so the Bayesian learner can update probabilities based on REAL results.

This solves the critical gap: "How does your Bayesian system learn from actual trades?"

Author: AppleTrader Pro
Date: 2026-01-23
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from core.verbose_mode_manager import vprint
from core.statistical_analysis_manager import StatisticalAnalysisManager


class TradeOutcomeRecorder:
    """
    Records trade outcomes and updates statistical models

    Workflow:
    1. record_trade_open() - When trade is entered
    2. record_trade_close() - When trade exits (win/loss)
    3. Automatically updates:
       - Bayesian pattern learner (win/loss counts)
       - Expected Value calculator (actual P&L)
       - Confidence Interval analyzer (sample size)
    """

    _instance = None

    def __init__(self):
        """Initialize the trade outcome recorder"""
        # Storage path
        self.data_dir = Path(__file__).parent.parent / "data" / "trade_history"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Open trades (waiting for close)
        self.open_trades_file = self.data_dir / "open_trades.json"
        self.open_trades = self._load_open_trades()

        # Closed trades (historical record)
        self.closed_trades_file = self.data_dir / "closed_trades.json"
        self.closed_trades = self._load_closed_trades()

        # Get statistical analysis manager
        self.stats_manager = StatisticalAnalysisManager.get_instance()

        vprint("[TradeRecorder] Initialized - Tracking trade outcomes for statistical learning")

    @classmethod
    def get_instance(cls):
        """Singleton pattern - only one recorder instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_open_trades(self) -> Dict:
        """Load currently open trades"""
        if self.open_trades_file.exists():
            try:
                with open(self.open_trades_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                vprint(f"[TradeRecorder] Error loading open trades: {e}")
                return {}
        return {}

    def _save_open_trades(self):
        """Save open trades to disk"""
        try:
            with open(self.open_trades_file, 'w') as f:
                json.dump(self.open_trades, f, indent=2)
        except Exception as e:
            vprint(f"[TradeRecorder] Error saving open trades: {e}")

    def _load_closed_trades(self) -> List[Dict]:
        """Load historical closed trades"""
        if self.closed_trades_file.exists():
            try:
                with open(self.closed_trades_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                vprint(f"[TradeRecorder] Error loading closed trades: {e}")
                return []
        return []

    def _save_closed_trades(self):
        """Save closed trades to disk"""
        try:
            with open(self.closed_trades_file, 'w') as f:
                json.dump(self.closed_trades, f, indent=2)
        except Exception as e:
            vprint(f"[TradeRecorder] Error saving closed trades: {e}")

    def record_trade_open(self, trade_data: Dict) -> str:
        """
        Record a new trade being opened

        Args:
            trade_data: Dict containing:
                - symbol: str
                - direction: 'BUY' or 'SELL'
                - entry_price: float
                - stop_loss: float
                - take_profit: float
                - lot_size: float
                - timeframe: str (e.g., 'H1')
                - pattern: str (e.g., 'Bullish_Engulfing')
                - quality_score: int (0-100)
                - statistical_win_prob: float (optional)
                - statistical_ev: float (optional)

        Returns:
            trade_id: Unique identifier for this trade
        """
        # Generate unique trade ID
        trade_id = f"{trade_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create trade record
        trade_record = {
            'trade_id': trade_id,
            'symbol': trade_data.get('symbol', 'UNKNOWN'),
            'direction': trade_data.get('direction', 'BUY'),
            'entry_price': trade_data.get('entry_price', 0.0),
            'stop_loss': trade_data.get('stop_loss', 0.0),
            'take_profit': trade_data.get('take_profit', 0.0),
            'lot_size': trade_data.get('lot_size', 0.01),
            'timeframe': trade_data.get('timeframe', 'H1'),
            'pattern': trade_data.get('pattern', 'Unknown'),
            'quality_score': trade_data.get('quality_score', 50),
            'statistical_win_prob': trade_data.get('statistical_win_prob', 0.5),
            'statistical_ev': trade_data.get('statistical_ev', 0.0),
            'open_time': datetime.now().isoformat(),
            'status': 'OPEN'
        }

        # Store in open trades
        self.open_trades[trade_id] = trade_record
        self._save_open_trades()

        vprint(f"[TradeRecorder] ✓ Recorded OPEN trade: {trade_id} | {trade_data.get('symbol')} {trade_data.get('direction')} | Pattern: {trade_data.get('pattern')}")

        return trade_id

    def record_trade_close(self, trade_id: str, outcome_data: Dict):
        """
        Record a trade closing and update statistical models

        Args:
            trade_id: Unique trade identifier
            outcome_data: Dict containing:
                - close_price: float
                - close_time: str (ISO format) or None (will use now)
                - profit_pips: float
                - profit_amount: float
                - outcome: 'WIN' or 'LOSS'
        """
        # Get the open trade record
        if trade_id not in self.open_trades:
            vprint(f"[TradeRecorder] ✗ Trade {trade_id} not found in open trades")
            return

        trade = self.open_trades[trade_id]

        # Update with closing data
        trade['close_price'] = outcome_data.get('close_price', trade['entry_price'])
        trade['close_time'] = outcome_data.get('close_time', datetime.now().isoformat())
        trade['profit_pips'] = outcome_data.get('profit_pips', 0.0)
        trade['profit_amount'] = outcome_data.get('profit_amount', 0.0)
        trade['outcome'] = outcome_data.get('outcome', 'LOSS')
        trade['status'] = 'CLOSED'

        # Calculate R-multiple (profit in terms of risk units)
        risk_amount = abs(trade['entry_price'] - trade['stop_loss']) * trade['lot_size'] * 100000  # Approximate for forex
        if risk_amount > 0:
            trade['r_multiple'] = trade['profit_amount'] / risk_amount
        else:
            trade['r_multiple'] = 0.0

        # Move to closed trades
        self.closed_trades.append(trade)
        self._save_closed_trades()

        # Remove from open trades
        del self.open_trades[trade_id]
        self._save_open_trades()

        vprint(f"[TradeRecorder] ✓ Recorded CLOSE trade: {trade_id} | {trade['outcome']} | P&L: {trade['profit_amount']:+.2f} | R: {trade['r_multiple']:+.2f}")

        # UPDATE STATISTICAL MODELS (This is the critical feedback loop!)
        self._update_statistical_models(trade)

    def _update_statistical_models(self, trade: Dict):
        """
        Update statistical models with actual trade outcome

        This is where the LEARNING happens!
        """
        try:
            pattern = trade.get('pattern', 'Unknown')
            timeframe = trade.get('timeframe', 'H1')
            outcome = trade.get('outcome', 'LOSS')
            profit_amount = trade.get('profit_amount', 0.0)
            r_multiple = trade.get('r_multiple', 0.0)

            vprint(f"[TradeRecorder] Updating statistical models for {pattern} on {timeframe}...")

            # Get calculators for this timeframe
            bayesian_calc = self.stats_manager.get_calculator(timeframe, 'bayesian')
            ev_calc = self.stats_manager.get_calculator(timeframe, 'expected_value')

            # Update Bayesian learner with win/loss
            is_win = outcome == 'WIN'
            bayesian_calc.record_outcome(pattern, is_win)
            vprint(f"[TradeRecorder]   ✓ Updated Bayesian: {pattern} -> {'WIN' if is_win else 'LOSS'}")

            # Update EV calculator with actual P&L
            ev_calc.record_trade_outcome(pattern, {
                'profit': profit_amount,
                'r_multiple': r_multiple,
                'outcome': outcome
            })
            vprint(f"[TradeRecorder]   ✓ Updated EV: {pattern} -> R={r_multiple:+.2f}")

            # Get updated statistics
            updated_prob = bayesian_calc.get_pattern_probability(pattern)
            vprint(f"[TradeRecorder]   📊 New win probability for {pattern}: {updated_prob['posterior_mean']*100:.1f}%")

        except Exception as e:
            vprint(f"[TradeRecorder] Error updating statistical models: {e}")
            import traceback
            traceback.print_exc()

    def get_open_trades(self) -> Dict:
        """Get all currently open trades"""
        return self.open_trades.copy()

    def get_closed_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent closed trades"""
        return self.closed_trades[-limit:]

    def get_pattern_history(self, pattern: str, timeframe: str = None) -> List[Dict]:
        """
        Get historical trades for a specific pattern

        Args:
            pattern: Pattern name (e.g., 'Bullish_Engulfing')
            timeframe: Optional timeframe filter (e.g., 'H1')

        Returns:
            List of trades matching the pattern
        """
        matches = [
            trade for trade in self.closed_trades
            if trade.get('pattern') == pattern and
            (timeframe is None or trade.get('timeframe') == timeframe)
        ]
        return matches

    def get_statistics_summary(self, pattern: str = None, timeframe: str = None) -> Dict:
        """
        Get summary statistics for trades

        Args:
            pattern: Optional pattern filter
            timeframe: Optional timeframe filter

        Returns:
            Dict with win rate, avg profit, total trades, etc.
        """
        # Filter trades
        trades = self.closed_trades
        if pattern:
            trades = [t for t in trades if t.get('pattern') == pattern]
        if timeframe:
            trades = [t for t in trades if t.get('timeframe') == timeframe]

        if not trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'avg_r_multiple': 0.0,
                'total_profit': 0.0
            }

        wins = [t for t in trades if t.get('outcome') == 'WIN']
        losses = [t for t in trades if t.get('outcome') == 'LOSS']

        total_profit = sum(t.get('profit_amount', 0.0) for t in trades)
        avg_profit = total_profit / len(trades)

        r_multiples = [t.get('r_multiple', 0.0) for t in trades]
        avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0.0

        return {
            'total_trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(trades) if trades else 0.0,
            'avg_profit': avg_profit,
            'avg_r_multiple': avg_r,
            'total_profit': total_profit
        }


# Singleton instance
trade_outcome_recorder = TradeOutcomeRecorder.get_instance()
