"""
AppleTrader Pro - Equity Curve & Drawdown Analyzer (IMPROVEMENT #9)
Real-time performance tracking with drawdown alerts
Prevents blowups and emotional trading
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import deque


class TradeRecord:
    """Individual trade record"""

    def __init__(self, trade_id: int, symbol: str, direction: str,
                 entry_price: float, exit_price: float, lots: float,
                 entry_time: datetime, exit_time: datetime,
                 profit: float, pips: float):
        self.trade_id = trade_id
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.lots = lots
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.profit = profit
        self.pips = pips
        self.is_win = profit > 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'lots': self.lots,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'profit': self.profit,
            'pips': self.pips,
            'is_win': self.is_win
        }


class EquityCurveAnalyzer:
    """
    Equity Curve & Drawdown Analysis Engine

    Tracks real-time trading performance:
    - Live equity curve visualization
    - Drawdown calculation and alerts
    - Daily/weekly loss limits
    - Psychological state indicators
    - Win rate and profit factor

    Expected Impact: -50% emotional trading, prevents blowups
    """

    def __init__(self, starting_balance: float = 10000,
                 daily_loss_limit_pct: float = 2.0,
                 weekly_loss_limit_pct: float = 5.0):
        """
        Initialize analyzer

        Args:
            starting_balance: Starting account balance
            daily_loss_limit_pct: Daily loss limit (%)
            weekly_loss_limit_pct: Weekly loss limit (%)
        """
        self.starting_balance = starting_balance
        self.current_balance = starting_balance
        self.current_equity = starting_balance  # Balance + floating P/L

        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.weekly_loss_limit_pct = weekly_loss_limit_pct

        # Trade history
        self.trades = []  # List of TradeRecord objects
        self.trade_counter = 0

        # Equity curve data points
        self.equity_curve = [(datetime.now(), starting_balance)]

        # Drawdown tracking
        self.peak_balance = starting_balance
        self.current_drawdown_pct = 0
        self.max_drawdown_pct = 0
        self.max_drawdown_date = None

        # Daily/weekly tracking
        self.daily_start_balance = starting_balance
        self.daily_start_date = datetime.now().date()

        self.weekly_start_balance = starting_balance
        self.weekly_start_date = self._get_week_start()

        # Statistics
        self.stats = self._calculate_stats()

        # Alerts
        self.active_alerts = []

    def add_trade(self, symbol: str, direction: str, entry_price: float,
                  exit_price: float, lots: float, entry_time: datetime,
                  exit_time: datetime, profit: float, pips: float):
        """
        Add a completed trade

        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            exit_price: Exit price
            lots: Position size in lots
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            profit: Profit in account currency
            pips: Profit in pips
        """
        self.trade_counter += 1

        trade = TradeRecord(
            self.trade_counter, symbol, direction,
            entry_price, exit_price, lots,
            entry_time, exit_time, profit, pips
        )

        self.trades.append(trade)

        # Update balance
        self.current_balance += profit

        # Update equity curve
        self.equity_curve.append((exit_time, self.current_balance))

        # Update drawdown
        self._update_drawdown()

        # Check loss limits
        self._check_loss_limits()

        # Check psychological state
        self._check_psychological_state()

        # Recalculate stats
        self.stats = self._calculate_stats()

    def update_floating_pl(self, floating_pl: float):
        """
        Update current equity with floating P/L from open positions

        Args:
            floating_pl: Total floating profit/loss
        """
        self.current_equity = self.current_balance + floating_pl

        # Update drawdown with equity
        if self.current_equity > self.peak_balance:
            self.peak_balance = self.current_equity

        if self.peak_balance > 0:
            self.current_drawdown_pct = ((self.peak_balance - self.current_equity) /
                                        self.peak_balance) * 100
        else:
            self.current_drawdown_pct = 0

    def _update_drawdown(self):
        """Update drawdown calculations"""
        # Update peak
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        # Calculate current drawdown
        if self.peak_balance > 0:
            self.current_drawdown_pct = ((self.peak_balance - self.current_balance) /
                                        self.peak_balance) * 100
        else:
            self.current_drawdown_pct = 0

        # Update max drawdown
        if self.current_drawdown_pct > self.max_drawdown_pct:
            self.max_drawdown_pct = self.current_drawdown_pct
            self.max_drawdown_date = datetime.now()

    def _check_loss_limits(self):
        """Check daily and weekly loss limits"""
        self.active_alerts = []

        today = datetime.now().date()

        # Reset daily counter if new day
        if today != self.daily_start_date:
            self.daily_start_balance = self.current_balance
            self.daily_start_date = today

        # Calculate daily loss
        daily_loss = self.current_balance - self.daily_start_balance
        daily_loss_pct = (daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0

        # Daily limit check
        if daily_loss_pct <= -self.daily_loss_limit_pct:
            self.active_alerts.append({
                'type': 'CRITICAL',
                'message': f'🛑 DAILY LOSS LIMIT REACHED: {daily_loss_pct:.1f}% '
                          f'(limit: {self.daily_loss_limit_pct}%)',
                'recommendation': 'STOP TRADING FOR TODAY'
            })
        elif daily_loss_pct <= -(self.daily_loss_limit_pct * 0.75):
            self.active_alerts.append({
                'type': 'WARNING',
                'message': f'⚠️ APPROACHING DAILY LIMIT: {daily_loss_pct:.1f}% '
                          f'(limit: {self.daily_loss_limit_pct}%)',
                'recommendation': 'Be very selective with next trades'
            })

        # Weekly limit check
        week_start = self._get_week_start()
        if week_start != self.weekly_start_date:
            self.weekly_start_balance = self.current_balance
            self.weekly_start_date = week_start

        weekly_loss = self.current_balance - self.weekly_start_balance
        weekly_loss_pct = (weekly_loss / self.weekly_start_balance) * 100 if self.weekly_start_balance > 0 else 0

        if weekly_loss_pct <= -self.weekly_loss_limit_pct:
            self.active_alerts.append({
                'type': 'CRITICAL',
                'message': f'🛑 WEEKLY LOSS LIMIT REACHED: {weekly_loss_pct:.1f}% '
                          f'(limit: {self.weekly_loss_limit_pct}%)',
                'recommendation': 'STOP TRADING FOR THIS WEEK'
            })

    def _check_psychological_state(self):
        """Check for psychological warning signs"""
        if len(self.trades) < 3:
            return

        recent_trades = self.trades[-10:] if len(self.trades) >= 10 else self.trades

        # Check for losing streak
        recent_losses = [t for t in recent_trades[-3:] if not t.is_win]
        if len(recent_losses) == 3:
            self.active_alerts.append({
                'type': 'PSYCHOLOGICAL',
                'message': '😤 3 LOSSES IN A ROW',
                'recommendation': 'Take a break. Review strategy. Avoid revenge trading.'
            })

        # Check for rapid trading (3+ trades in 2 hours)
        if len(self.trades) >= 3:
            recent_3 = self.trades[-3:]
            time_span = (recent_3[-1].exit_time - recent_3[0].entry_time).total_seconds() / 3600

            if time_span <= 2:
                self.active_alerts.append({
                    'type': 'PSYCHOLOGICAL',
                    'message': '⚡ RAPID TRADING DETECTED',
                    'recommendation': 'Slow down. 3 trades in 2 hours suggests emotional trading.'
                })

        # Check for large single loss (> 50% of daily limit)
        if self.trades:
            last_trade = self.trades[-1]
            loss_pct = (last_trade.profit / self.daily_start_balance) * 100

            if loss_pct < -(self.daily_loss_limit_pct * 0.5):
                self.active_alerts.append({
                    'type': 'WARNING',
                    'message': f'📉 LARGE LOSS: {loss_pct:.1f}%',
                    'recommendation': 'Review what went wrong. Take a 30min break.'
                })

    def _calculate_stats(self) -> Dict:
        """Calculate trading statistics"""
        if not self.trades:
            return self._empty_stats()

        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.is_win]
        losing_trades = [t for t in self.trades if not t.is_win]

        wins = len(winning_trades)
        losses = len(losing_trades)

        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        # Profit calculations
        total_profit = sum(t.profit for t in self.trades)
        gross_profit = sum(t.profit for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.profit for t in losing_trades)) if losing_trades else 0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Average trades
        avg_win = gross_profit / wins if wins > 0 else 0
        avg_loss = gross_loss / losses if losses > 0 else 0

        # R-multiple (simplified)
        r_multiple = avg_win / avg_loss if avg_loss > 0 else 0

        # Return %
        return_pct = ((self.current_balance - self.starting_balance) /
                     self.starting_balance) * 100

        # Best/worst trades
        best_trade = max(self.trades, key=lambda t: t.profit) if self.trades else None
        worst_trade = min(self.trades, key=lambda t: t.profit) if self.trades else None

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'r_multiple': r_multiple,
            'return_pct': return_pct,
            'best_trade': best_trade.profit if best_trade else 0,
            'worst_trade': worst_trade.profit if worst_trade else 0,
            'current_balance': self.current_balance,
            'starting_balance': self.starting_balance
        }

    def _empty_stats(self) -> Dict:
        """Return empty stats structure"""
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'total_profit': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'r_multiple': 0,
            'return_pct': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'current_balance': self.current_balance,
            'starting_balance': self.starting_balance
        }

    def get_equity_curve_data(self, days: int = 30) -> pd.DataFrame:
        """
        Get equity curve data for charting

        Args:
            days: Number of days to include

        Returns:
            DataFrame with timestamp and balance columns
        """
        if not self.equity_curve:
            return pd.DataFrame(columns=['timestamp', 'balance'])

        cutoff = datetime.now() - timedelta(days=days)
        filtered = [(ts, bal) for ts, bal in self.equity_curve if ts >= cutoff]

        df = pd.DataFrame(filtered, columns=['timestamp', 'balance'])
        return df

    def get_drawdown_analysis(self) -> Dict:
        """Get detailed drawdown analysis"""
        daily_loss = self.current_balance - self.daily_start_balance
        daily_loss_pct = (daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0

        weekly_loss = self.current_balance - self.weekly_start_balance
        weekly_loss_pct = (weekly_loss / self.weekly_start_balance) * 100 if self.weekly_start_balance > 0 else 0

        return {
            'current_drawdown_pct': self.current_drawdown_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'max_drawdown_date': self.max_drawdown_date,
            'peak_balance': self.peak_balance,
            'daily_loss': daily_loss,
            'daily_loss_pct': daily_loss_pct,
            'daily_limit_pct': self.daily_loss_limit_pct,
            'daily_remaining_pct': self.daily_loss_limit_pct + daily_loss_pct,
            'weekly_loss': weekly_loss,
            'weekly_loss_pct': weekly_loss_pct,
            'weekly_limit_pct': self.weekly_loss_limit_pct,
            'weekly_remaining_pct': self.weekly_loss_limit_pct + weekly_loss_pct
        }

    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        lines = []
        lines.append(f"Balance: ${self.current_balance:.2f} ({self.stats['return_pct']:+.1f}%)")
        lines.append(f"Equity: ${self.current_equity:.2f}")
        lines.append(f"")
        lines.append(f"Current DD: {self.current_drawdown_pct:.1f}%")
        lines.append(f"Max DD: {self.max_drawdown_pct:.1f}%")

        dd_analysis = self.get_drawdown_analysis()
        lines.append(f"")
        lines.append(f"Daily: {dd_analysis['daily_loss_pct']:.1f}% "
                    f"(Limit: {self.daily_loss_limit_pct}%)")
        lines.append(f"Weekly: {dd_analysis['weekly_loss_pct']:.1f}% "
                    f"(Limit: {self.weekly_loss_limit_pct}%)")

        if self.stats['total_trades'] > 0:
            lines.append(f"")
            lines.append(f"Win Rate: {self.stats['win_rate']:.1f}% "
                        f"({self.stats['wins']}/{self.stats['total_trades']})")
            lines.append(f"Profit Factor: {self.stats['profit_factor']:.2f}")

        return '\n'.join(lines)

    def _get_week_start(self) -> datetime.date:
        """Get start of current week (Monday)"""
        today = datetime.now().date()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        return week_start

    def reset_account(self, new_balance: float):
        """Reset account (for testing or new account)"""
        self.starting_balance = new_balance
        self.current_balance = new_balance
        self.current_equity = new_balance
        self.trades = []
        self.equity_curve = [(datetime.now(), new_balance)]
        self.peak_balance = new_balance
        self.current_drawdown_pct = 0
        self.max_drawdown_pct = 0
        self.stats = self._empty_stats()
        self.active_alerts = []


# Global instance
equity_curve_analyzer = EquityCurveAnalyzer()
