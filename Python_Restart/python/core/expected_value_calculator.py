"""
AppleTrader Pro - Expected Value Calculator
Calculates mathematical expectation for trading opportunities

Formula: EV = (Win% × AvgWin) - (Loss% × AvgLoss)

Only trade opportunities with positive expected value.
"""

from typing import Dict, Optional
from core.verbose_mode_manager import vprint


class ExpectedValueCalculator:
    """
    Expected Value Calculator for timeframe-specific analysis

    The Expected Value (EV) tells you the average profit/loss per trade
    over the long run. Only positive EV trades should be taken.

    Example:
    - Win Rate: 60%
    - Avg Win: 2.5R
    - Avg Loss: 1.0R
    - EV = (0.60 × 2.5) - (0.40 × 1.0) = 1.5 - 0.4 = +1.1R

    This means on average, you make 1.1R per trade.
    """

    def __init__(self, manager, timeframe: str):
        """
        Initialize EV calculator for specific timeframe

        Args:
            manager: StatisticalAnalysisManager instance
            timeframe: Trading timeframe (M15, H1, H4, D1)
        """
        self.manager = manager
        self.timeframe = timeframe
        self.min_sample_size = 20  # Minimum trades needed for reliable EV

        vprint(f"[EVCalculator] Initialized for {timeframe}")

    def calculate(self, opportunity: Dict) -> float:
        """
        Calculate Expected Value for given opportunity

        Args:
            opportunity: Dict containing pattern, symbol, setup info

        Returns:
            Expected value in R-multiples (positive = good, negative = bad)
        """
        pattern = opportunity.get('pattern', 'Unknown')
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            # No historical data - return neutral EV
            vprint(f"[EVCalculator] No data for {pattern} on {self.timeframe}")
            return 0.0

        # Calculate win rate
        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        total_trades = wins + losses

        if total_trades == 0:
            return 0.0

        win_rate = wins / total_trades

        # Get average win/loss
        avg_win = pattern_stats.get('avg_win', 0.0)
        avg_loss = pattern_stats.get('avg_loss', 1.0)  # Default to 1R loss

        # Calculate Expected Value
        # EV = (P(Win) × AvgWin) - (P(Loss) × AvgLoss)
        loss_rate = 1 - win_rate
        expected_value = (win_rate * avg_win) - (loss_rate * avg_loss)

        # Adjust confidence based on sample size
        confidence_multiplier = self._calculate_confidence_multiplier(total_trades)
        adjusted_ev = expected_value * confidence_multiplier

        vprint(f"[EVCalculator] {pattern} on {self.timeframe}:")
        vprint(f"  Win Rate: {win_rate*100:.1f}% ({wins}/{total_trades})")
        vprint(f"  Avg Win: {avg_win:.2f}R, Avg Loss: {avg_loss:.2f}R")
        vprint(f"  Raw EV: {expected_value:.3f}R")
        vprint(f"  Confidence: {confidence_multiplier*100:.0f}% (n={total_trades})")
        vprint(f"  Adjusted EV: {adjusted_ev:.3f}R")

        return adjusted_ev

    def _calculate_confidence_multiplier(self, sample_size: int) -> float:
        """
        Calculate confidence multiplier based on sample size

        Small sample = lower confidence = reduce EV estimate
        Large sample = higher confidence = use full EV estimate

        Args:
            sample_size: Number of historical trades

        Returns:
            Multiplier between 0.0 and 1.0
        """
        if sample_size >= self.min_sample_size * 2:  # 40+ trades
            return 1.0  # Full confidence
        elif sample_size >= self.min_sample_size:  # 20-39 trades
            return 0.8  # Good confidence
        elif sample_size >= self.min_sample_size // 2:  # 10-19 trades
            return 0.5  # Moderate confidence
        else:  # < 10 trades
            return 0.2  # Low confidence

    def get_detailed_analysis(self, opportunity: Dict) -> Dict:
        """
        Get detailed EV analysis with all components

        Returns dict with:
        - expected_value: float
        - win_rate: float
        - avg_win: float
        - avg_loss: float
        - sample_size: int
        - confidence_level: str
        - recommendation: str
        """
        pattern = opportunity.get('pattern', 'Unknown')
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            return {
                'expected_value': 0.0,
                'win_rate': 0.5,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'sample_size': 0,
                'confidence_level': 'No Data',
                'recommendation': 'Insufficient data - collect trades first'
            }

        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        total_trades = wins + losses
        win_rate = wins / total_trades if total_trades > 0 else 0.5

        avg_win = pattern_stats.get('avg_win', 0.0)
        avg_loss = pattern_stats.get('avg_loss', 1.0)

        loss_rate = 1 - win_rate
        ev = (win_rate * avg_win) - (loss_rate * avg_loss)

        # Determine confidence level
        if total_trades >= self.min_sample_size * 2:
            confidence = 'High'
        elif total_trades >= self.min_sample_size:
            confidence = 'Good'
        elif total_trades >= self.min_sample_size // 2:
            confidence = 'Moderate'
        else:
            confidence = 'Low'

        # Generate recommendation
        if ev > 0.5:
            recommendation = '✓ STRONG POSITIVE EV - Take this trade'
        elif ev > 0.0:
            recommendation = '✓ Positive EV - Trade acceptable'
        elif ev > -0.3:
            recommendation = '⚠ Near-zero EV - Consider passing'
        else:
            recommendation = '✗ NEGATIVE EV - Avoid this trade'

        if total_trades < self.min_sample_size:
            recommendation += f' (Collect {self.min_sample_size - total_trades} more trades for reliability)'

        return {
            'expected_value': ev,
            'adjusted_ev': self.calculate(opportunity),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'sample_size': total_trades,
            'confidence_level': confidence,
            'recommendation': recommendation
        }

    def get_historical_ev_trend(self, pattern: str, lookback: int = 50) -> list:
        """
        Get historical EV trend for pattern

        Useful for seeing if EV is improving or degrading over time

        Args:
            pattern: Pattern name
            lookback: Number of recent trades to analyze

        Returns:
            List of EV values over time
        """
        tf_data = self.manager.get_timeframe_data(self.timeframe)
        trades = tf_data.get('trades', [])

        # Filter trades for this pattern
        pattern_trades = [t for t in trades if t.get('pattern') == pattern]

        # Get last N trades
        recent_trades = pattern_trades[-lookback:] if len(pattern_trades) > lookback else pattern_trades

        ev_trend = []
        for i in range(len(recent_trades)):
            # Calculate EV at each point in time
            subset = recent_trades[:i+1]
            wins = sum(1 for t in subset if t.get('outcome') == 'win')
            losses = len(subset) - wins

            if len(subset) == 0:
                continue

            win_rate = wins / len(subset)
            avg_win = sum(t.get('r_multiple', 0) for t in subset if t.get('outcome') == 'win') / wins if wins > 0 else 0
            avg_loss = sum(abs(t.get('r_multiple', 0)) for t in subset if t.get('outcome') == 'loss') / losses if losses > 0 else 1.0

            ev = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            ev_trend.append({
                'trade_number': i + 1,
                'ev': ev,
                'win_rate': win_rate,
                'sample_size': len(subset)
            })

        return ev_trend

    def should_trade(self, opportunity: Dict, min_ev: float = 0.0) -> bool:
        """
        Simple decision helper: should we take this trade?

        Args:
            opportunity: Trading opportunity
            min_ev: Minimum EV threshold (default 0.0 = any positive EV)

        Returns:
            True if trade meets EV criteria, False otherwise
        """
        ev = self.calculate(opportunity)
        return ev >= min_ev
