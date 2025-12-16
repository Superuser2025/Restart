"""
AppleTrader Pro - Automated Trade Journal with AI Insights (IMPROVEMENT #10)
Auto-generated trade entries with AI-powered pattern analysis
Zero manual work, continuous improvement through insights
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum


class TradeSetupType(Enum):
    """Trade setup classification"""
    BULLISH_OB = "Bullish OB"
    BEARISH_OB = "Bearish OB"
    FVG_LONG = "FVG Long"
    FVG_SHORT = "FVG Short"
    LIQUIDITY_SWEEP = "Liquidity Sweep"
    TREND_CONTINUATION = "Trend Continuation"
    REVERSAL = "Reversal"
    BREAKOUT = "Breakout"
    OTHER = "Other"


class TradeJournalEntry:
    """Individual trade journal entry"""

    def __init__(self, trade_id: int, symbol: str, setup_type: TradeSetupType,
                 direction: str, entry_price: float, exit_price: float,
                 stop_loss: float, take_profit: float, lots: float,
                 entry_time: datetime, exit_time: datetime,
                 profit: float, pips: float, r_multiple: float):
        self.trade_id = trade_id
        self.symbol = symbol
        self.setup_type = setup_type
        self.direction = direction
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.lots = lots
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.profit = profit
        self.pips = pips
        self.r_multiple = r_multiple
        self.is_win = profit > 0

        # Context (filled in during analysis)
        self.session = self._determine_session()
        self.day_of_week = entry_time.strftime("%A")
        self.confluence_count = 0
        self.quality_score = 0

        # Screenshots (paths)
        self.entry_screenshot = None
        self.exit_screenshot = None

    def _determine_session(self) -> str:
        """Determine trading session"""
        hour = self.entry_time.hour

        if 0 <= hour < 8:
            return "Asian"
        elif 8 <= hour < 16:
            return "London"
        elif 16 <= hour < 24:
            return "New York"
        else:
            return "Unknown"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'setup_type': self.setup_type.value,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'lots': self.lots,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'profit': self.profit,
            'pips': self.pips,
            'r_multiple': self.r_multiple,
            'is_win': self.is_win,
            'session': self.session,
            'day_of_week': self.day_of_week,
            'quality_score': self.quality_score
        }


class AutomatedTradeJournal:
    """
    Automated Trade Journal with AI Insights

    Features:
    - Auto-generated entries for every trade
    - Setup type classification
    - Performance analysis by setup/session/day
    - Pattern recognition (strengths/weaknesses)
    - AI-powered recommendations
    - Weekly/monthly summaries

    Expected Impact: Zero manual work, continuous improvement
    """

    def __init__(self):
        """Initialize journal"""
        self.entries = []  # List of TradeJournalEntry
        self.trade_counter = 0

        # Analysis cache
        self.analysis_cache = {}
        self.last_analysis = None

    def add_trade(self, symbol: str, setup_type: TradeSetupType,
                  direction: str, entry_price: float, exit_price: float,
                  stop_loss: float, take_profit: float, lots: float,
                  entry_time: datetime, exit_time: datetime,
                  profit: float, pips: float, r_multiple: float) -> TradeJournalEntry:
        """
        Add a trade to the journal

        Args:
            ... (trade parameters)

        Returns:
            TradeJournalEntry object
        """
        self.trade_counter += 1

        entry = TradeJournalEntry(
            self.trade_counter, symbol, setup_type, direction,
            entry_price, exit_price, stop_loss, take_profit, lots,
            entry_time, exit_time, profit, pips, r_multiple
        )

        self.entries.append(entry)

        # Invalidate cache
        self.analysis_cache = {}

        return entry

    def analyze_performance(self) -> Dict:
        """
        Comprehensive performance analysis

        Returns:
            Analysis dict with insights
        """
        if not self.entries:
            return self._empty_analysis()

        analysis = {
            'total_trades': len(self.entries),
            'wins': sum(1 for e in self.entries if e.is_win),
            'losses': sum(1 for e in self.entries if not e.is_win),
            'win_rate': 0,
            'total_profit': sum(e.profit for e in self.entries),
            'avg_r': np.mean([e.r_multiple for e in self.entries]),
            'best_trade': max(self.entries, key=lambda x: x.profit).to_dict(),
            'worst_trade': min(self.entries, key=lambda x: x.profit).to_dict(),

            # By setup type
            'by_setup': self._analyze_by_setup(),

            # By session
            'by_session': self._analyze_by_session(),

            # By day of week
            'by_day': self._analyze_by_day(),

            # Strengths and weaknesses
            'strengths': self._identify_strengths(),
            'weaknesses': self._identify_weaknesses(),

            # AI insights
            'ai_insights': self._generate_ai_insights(),

            # Recommendations
            'recommendations': self._generate_recommendations()
        }

        # Calculate win rate
        if analysis['total_trades'] > 0:
            analysis['win_rate'] = (analysis['wins'] / analysis['total_trades']) * 100

        self.last_analysis = datetime.now()

        return analysis

    def _analyze_by_setup(self) -> Dict:
        """Analyze performance by setup type"""
        by_setup = defaultdict(lambda: {'trades': [], 'wins': 0, 'losses': 0})

        for entry in self.entries:
            setup = entry.setup_type.value
            by_setup[setup]['trades'].append(entry)

            if entry.is_win:
                by_setup[setup]['wins'] += 1
            else:
                by_setup[setup]['losses'] += 1

        # Calculate stats
        results = {}
        for setup, data in by_setup.items():
            total = len(data['trades'])
            win_rate = (data['wins'] / total) * 100 if total > 0 else 0
            avg_r = np.mean([t.r_multiple for t in data['trades']])

            results[setup] = {
                'total_trades': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'avg_r': avg_r
            }

        return results

    def _analyze_by_session(self) -> Dict:
        """Analyze performance by trading session"""
        by_session = defaultdict(lambda: {'trades': [], 'wins': 0, 'losses': 0})

        for entry in self.entries:
            session = entry.session
            by_session[session]['trades'].append(entry)

            if entry.is_win:
                by_session[session]['wins'] += 1
            else:
                by_session[session]['losses'] += 1

        # Calculate stats
        results = {}
        for session, data in by_session.items():
            total = len(data['trades'])
            win_rate = (data['wins'] / total) * 100 if total > 0 else 0
            avg_r = np.mean([t.r_multiple for t in data['trades']])

            results[session] = {
                'total_trades': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'avg_r': avg_r
            }

        return results

    def _analyze_by_day(self) -> Dict:
        """Analyze performance by day of week"""
        by_day = defaultdict(lambda: {'trades': [], 'wins': 0, 'losses': 0})

        for entry in self.entries:
            day = entry.day_of_week
            by_day[day]['trades'].append(entry)

            if entry.is_win:
                by_day[day]['wins'] += 1
            else:
                by_day[day]['losses'] += 1

        # Calculate stats
        results = {}
        for day, data in by_day.items():
            total = len(data['trades'])
            win_rate = (data['wins'] / total) * 100 if total > 0 else 0
            avg_r = np.mean([t.r_multiple for t in data['trades']])

            results[day] = {
                'total_trades': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': win_rate,
                'avg_r': avg_r
            }

        return results

    def _identify_strengths(self) -> List[str]:
        """Identify trading strengths"""
        strengths = []

        if len(self.entries) < 5:
            return ["Need more trades for analysis"]

        # Analyze by setup
        by_setup = self._analyze_by_setup()
        for setup, stats in by_setup.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] >= 70:
                    strengths.append(
                        f"✓ {setup} setups: {stats['wins']}/{stats['total_trades']} wins "
                        f"({stats['win_rate']:.0f}%)"
                    )

        # Analyze by session
        by_session = self._analyze_by_session()
        for session, stats in by_session.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] >= 65:
                    strengths.append(
                        f"✓ {session} session: {stats['win_rate']:.0f}% win rate"
                    )

        # Analyze by day
        by_day = self._analyze_by_day()
        for day, stats in by_day.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] >= 70:
                    strengths.append(
                        f"✓ Best day: {day} ({stats['wins']}/{stats['total_trades']} wins)"
                    )

        if not strengths:
            strengths.append("Building track record...")

        return strengths

    def _identify_weaknesses(self) -> List[str]:
        """Identify trading weaknesses"""
        weaknesses = []

        if len(self.entries) < 5:
            return ["Need more trades for analysis"]

        # Analyze by setup
        by_setup = self._analyze_by_setup()
        for setup, stats in by_setup.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] < 40:
                    weaknesses.append(
                        f"✗ {setup} setups: {stats['wins']}/{stats['total_trades']} wins "
                        f"({stats['win_rate']:.0f}%) - AVOID"
                    )

        # Analyze by session
        by_session = self._analyze_by_session()
        for session, stats in by_session.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] < 40:
                    weaknesses.append(
                        f"✗ {session} session: {stats['win_rate']:.0f}% win rate - SKIP"
                    )

        # Analyze by day
        by_day = self._analyze_by_day()
        for day, stats in by_day.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] < 35:
                    weaknesses.append(
                        f"✗ Worst day: {day} ({stats['wins']}/{stats['total_trades']} wins) - AVOID"
                    )

        if not weaknesses:
            weaknesses.append("No significant weaknesses detected")

        return weaknesses

    def _generate_ai_insights(self) -> List[str]:
        """Generate AI-powered insights"""
        insights = []

        if len(self.entries) < 10:
            return ["Collecting data for AI analysis..."]

        # Pattern detection
        recent_trades = self.entries[-20:] if len(self.entries) >= 20 else self.entries

        # Losing streak detection
        consecutive_losses = 0
        for trade in reversed(recent_trades):
            if not trade.is_win:
                consecutive_losses += 1
            else:
                break

        if consecutive_losses >= 3:
            insights.append(
                f"⚠️ {consecutive_losses} consecutive losses - Consider taking a break"
            )

        # Overtrading detection
        today_trades = [t for t in self.entries
                       if t.entry_time.date() == datetime.now().date()]

        if len(today_trades) > 5:
            insights.append(
                f"⚠️ {len(today_trades)} trades today - Possible overtrading"
            )

        # R-multiple analysis
        avg_winners = np.mean([t.r_multiple for t in self.entries if t.is_win]) if any(t.is_win for t in self.entries) else 0
        avg_losers = abs(np.mean([t.r_multiple for t in self.entries if not t.is_win])) if any(not t.is_win for t in self.entries) else 0

        if avg_losers > 1.2:
            insights.append(
                f"⚠️ Average loss is {avg_losers:.1f}R - Stops too wide or holding losers"
            )

        if avg_winners > 2.0:
            insights.append(
                f"✓ Average winner is {avg_winners:.1f}R - Excellent trade management"
            )

        if not insights:
            insights.append("✓ Trading patterns look healthy")

        return insights

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if len(self.entries) < 10:
            return ["Build more trade history for personalized recommendations"]

        # Based on setup analysis
        by_setup = self._analyze_by_setup()

        best_setup = None
        best_win_rate = 0

        worst_setup = None
        worst_win_rate = 100

        for setup, stats in by_setup.items():
            if stats['total_trades'] >= 3:
                if stats['win_rate'] > best_win_rate:
                    best_win_rate = stats['win_rate']
                    best_setup = setup

                if stats['win_rate'] < worst_win_rate:
                    worst_win_rate = stats['win_rate']
                    worst_setup = setup

        if best_setup:
            recommendations.append(
                f"💡 Focus on {best_setup} setups ({best_win_rate:.0f}% win rate)"
            )

        if worst_setup and worst_win_rate < 40:
            recommendations.append(
                f"💡 Avoid {worst_setup} setups ({worst_win_rate:.0f}% win rate)"
            )

        # Session recommendations
        by_session = self._analyze_by_session()

        best_session = max(by_session.items(),
                          key=lambda x: x[1]['win_rate'] if x[1]['total_trades'] >= 3 else 0)

        if best_session[1]['total_trades'] >= 3:
            recommendations.append(
                f"💡 Trade more during {best_session[0]} session "
                f"({best_session[1]['win_rate']:.0f}% win rate)"
            )

        # Day recommendations
        by_day = self._analyze_by_day()

        best_day = max(by_day.items(),
                      key=lambda x: x[1]['win_rate'] if x[1]['total_trades'] >= 3 else 0)

        if best_day[1]['total_trades'] >= 3:
            recommendations.append(
                f"💡 {best_day[0]} is your best day "
                f"({best_day[1]['wins']}/{best_day[1]['total_trades']} wins)"
            )

        if not recommendations:
            recommendations.append("Continue building your edge")

        return recommendations

    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'total_profit': 0,
            'avg_r': 0,
            'best_trade': None,
            'worst_trade': None,
            'by_setup': {},
            'by_session': {},
            'by_day': {},
            'strengths': [],
            'weaknesses': [],
            'ai_insights': [],
            'recommendations': []
        }

    def get_recent_trades(self, count: int = 20) -> List[TradeJournalEntry]:
        """Get most recent trades"""
        return sorted(self.entries, key=lambda x: x.exit_time, reverse=True)[:count]

    def format_trade_entry(self, entry: TradeJournalEntry) -> str:
        """Format a trade entry for display"""
        emoji = '✓' if entry.is_win else '✗'
        profit_str = f"+${entry.profit:.2f}" if entry.is_win else f"-${abs(entry.profit):.2f}"

        lines = []
        lines.append(f"═══ TRADE #{entry.trade_id} {emoji} ═══")
        lines.append(f"{entry.symbol} - {entry.direction} - {entry.setup_type.value}")
        lines.append(f"")
        lines.append(f"Entry:  {entry.entry_price:.5f} @ {entry.entry_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Exit:   {entry.exit_price:.5f} @ {entry.exit_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"SL:     {entry.stop_loss:.5f}")
        lines.append(f"TP:     {entry.take_profit:.5f}")
        lines.append(f"")
        lines.append(f"Result: {profit_str} ({entry.pips:+.1f} pips) [{entry.r_multiple:+.2f}R]")
        lines.append(f"Session: {entry.session} | Day: {entry.day_of_week}")

        return '\n'.join(lines)

    def export_to_csv(self, filename: str):
        """Export journal to CSV file"""
        if not self.entries:
            return

        df = pd.DataFrame([e.to_dict() for e in self.entries])
        df.to_csv(filename, index=False)

    def get_weekly_summary(self) -> Dict:
        """Generate weekly performance summary"""
        week_start = datetime.now() - timedelta(days=7)
        week_trades = [e for e in self.entries if e.exit_time >= week_start]

        if not week_trades:
            return {'trades': 0, 'profit': 0, 'win_rate': 0}

        wins = sum(1 for t in week_trades if t.is_win)
        total = len(week_trades)
        profit = sum(t.profit for t in week_trades)
        win_rate = (wins / total) * 100 if total > 0 else 0

        return {
            'trades': total,
            'wins': wins,
            'losses': total - wins,
            'profit': profit,
            'win_rate': win_rate,
            'avg_r': np.mean([t.r_multiple for t in week_trades])
        }


# Global instance
trade_journal = AutomatedTradeJournal()
