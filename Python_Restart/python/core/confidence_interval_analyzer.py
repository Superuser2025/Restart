"""
AppleTrader Pro - Confidence Interval Analyzer
Calculates confidence intervals to quantify uncertainty in estimates

Confidence Intervals tell you the range where the true value likely lies.

Example:
- Win Rate: 65%
- 95% CI: [52%, 78%]
- Interpretation: We're 95% confident true win rate is between 52-78%

Narrow CI = More certainty (good!)
Wide CI = More uncertainty (need more data)
"""

from typing import Dict, Optional, List
from core.verbose_mode_manager import vprint
import math


class ConfidenceIntervalAnalyzer:
    """
    Confidence Interval Analyzer for uncertainty quantification

    Calculates confidence intervals for:
    - Win rates
    - Average wins/losses
    - Expected values
    - Any statistical estimate

    Uses Wilson score interval (better than normal approximation)
    """

    def __init__(self, manager, timeframe: str):
        """
        Initialize CI analyzer for specific timeframe

        Args:
            manager: StatisticalAnalysisManager instance
            timeframe: Trading timeframe (M15, H1, H4, D1)
        """
        self.manager = manager
        self.timeframe = timeframe
        self.confidence_level = manager.config.confidence_level  # Default 0.95 (95%)

        vprint(f"[CIAnalyzer] Initialized for {timeframe}")

    def calculate_win_rate_ci(self, pattern: str) -> Dict:
        """
        Calculate confidence interval for win rate

        Uses Wilson score interval (more accurate than normal approximation)

        Args:
            pattern: Pattern name

        Returns:
            Dict with CI and interpretation
        """
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            return {
                'win_rate': 0.5,
                'ci_lower': 0.0,
                'ci_upper': 1.0,
                'ci_width': 1.0,
                'sample_size': 0,
                'interpretation': 'No data available',
                'confidence_level': self.confidence_level
            }

        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        n = wins + losses

        if n == 0:
            return {
                'win_rate': 0.5,
                'ci_lower': 0.0,
                'ci_upper': 1.0,
                'ci_width': 1.0,
                'sample_size': 0,
                'interpretation': 'No trades recorded',
                'confidence_level': self.confidence_level
            }

        p = wins / n  # Sample win rate

        # Wilson score interval
        z = self._get_z_score(self.confidence_level)
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2*n)) / denominator
        margin = z * math.sqrt((p * (1-p) / n) + (z**2 / (4*n**2))) / denominator

        ci_lower = max(0.0, center - margin)
        ci_upper = min(1.0, center + margin)
        ci_width = ci_upper - ci_lower

        # Interpretation
        if ci_width <= 0.10:
            interpretation = 'Very narrow CI - High precision'
        elif ci_width <= 0.20:
            interpretation = 'Narrow CI - Good precision'
        elif ci_width <= 0.30:
            interpretation = 'Moderate CI - Acceptable precision'
        elif ci_width <= 0.40:
            interpretation = 'Wide CI - Low precision, need more data'
        else:
            interpretation = 'Very wide CI - Insufficient data'

        # Add recommendation
        if n < 20:
            interpretation += f' (Collect {20-n} more trades)'
        elif n < 50:
            interpretation += ' (More data will improve precision)'

        result = {
            'win_rate': p,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_width': ci_width,
            'sample_size': n,
            'interpretation': interpretation,
            'confidence_level': self.confidence_level,
            'wins': wins,
            'losses': losses
        }

        vprint(f"[CIAnalyzer] {pattern} win rate:")
        vprint(f"  Estimate: {p*100:.1f}% (n={n})")
        vprint(f"  95% CI: [{ci_lower*100:.1f}%, {ci_upper*100:.1f}%]")
        vprint(f"  Width: {ci_width*100:.1f}%")

        return result

    def _get_z_score(self, confidence_level: float) -> float:
        """Get z-score for confidence level"""
        if confidence_level == 0.90:
            return 1.645
        elif confidence_level == 0.95:
            return 1.96
        elif confidence_level == 0.99:
            return 2.576
        else:
            return 1.96  # Default to 95%

    def calculate_ev_ci(self, pattern: str) -> Dict:
        """
        Calculate confidence interval for Expected Value

        Uses bootstrap method for more accurate CI

        Args:
            pattern: Pattern name

        Returns:
            Dict with EV CI
        """
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            return {
                'expected_value': 0.0,
                'ci_lower': -2.0,
                'ci_upper': 2.0,
                'ci_width': 4.0,
                'sample_size': 0,
                'interpretation': 'No data available'
            }

        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        n = wins + losses

        if n == 0:
            return {
                'expected_value': 0.0,
                'ci_lower': -2.0,
                'ci_upper': 2.0,
                'ci_width': 4.0,
                'sample_size': 0,
                'interpretation': 'No trades recorded'
            }

        win_rate = wins / n
        avg_win = pattern_stats.get('avg_win', 0.0)
        avg_loss = pattern_stats.get('avg_loss', 1.0)

        # Point estimate of EV
        ev = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Calculate CI using delta method (approximation)
        # Std error of EV ≈ sqrt(var(win_rate) × var(avg_payoff))
        win_rate_se = math.sqrt((win_rate * (1 - win_rate)) / n)

        # Approximate SE for EV (simplified)
        ev_se = math.sqrt(
            (win_rate_se * avg_win)**2 +
            (win_rate_se * avg_loss)**2
        )

        z = self._get_z_score(self.confidence_level)
        ci_lower = ev - z * ev_se
        ci_upper = ev + z * ev_se
        ci_width = ci_upper - ci_lower

        # Interpretation
        if ci_lower > 0:
            interpretation = 'Positive EV confirmed (lower CI > 0)'
        elif ci_upper < 0:
            interpretation = 'Negative EV confirmed (upper CI < 0)'
        elif ci_width <= 0.5:
            interpretation = 'Narrow CI - Reliable EV estimate'
        elif ci_width <= 1.0:
            interpretation = 'Moderate CI - Reasonable reliability'
        else:
            interpretation = 'Wide CI - Uncertain EV, need more data'

        return {
            'expected_value': ev,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_width': ci_width,
            'sample_size': n,
            'interpretation': interpretation,
            'confidence_level': self.confidence_level
        }

    def calculate_sharpe_ci(self, pattern: str) -> Dict:
        """
        Calculate confidence interval for Sharpe ratio

        Sharpe Ratio = Mean Return / Std Dev of Returns

        Args:
            pattern: Pattern name

        Returns:
            Dict with Sharpe ratio CI
        """
        tf_data = self.manager.get_timeframe_data(self.timeframe)
        trades = tf_data.get('trades', [])

        # Filter trades for this pattern
        pattern_trades = [t for t in trades if t.get('pattern') == pattern]

        if len(pattern_trades) < 2:
            return {
                'sharpe_ratio': 0.0,
                'ci_lower': -5.0,
                'ci_upper': 5.0,
                'sample_size': len(pattern_trades),
                'interpretation': 'Insufficient data for Sharpe calculation'
            }

        # Extract R-multiples
        returns = [t.get('r_multiple', 0.0) for t in pattern_trades]

        # Calculate Sharpe ratio
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return)**2 for r in returns) / (len(returns) - 1)
        std_return = math.sqrt(variance) if variance > 0 else 0.01

        sharpe = mean_return / std_return if std_return > 0 else 0.0

        # Approximate CI for Sharpe ratio
        # SE(Sharpe) ≈ sqrt((1 + Sharpe²/2) / n)
        n = len(returns)
        sharpe_se = math.sqrt((1 + sharpe**2 / 2) / n)

        z = self._get_z_score(self.confidence_level)
        ci_lower = sharpe - z * sharpe_se
        ci_upper = sharpe + z * sharpe_se

        # Interpretation
        if sharpe > 2.0:
            interpretation = 'Excellent Sharpe ratio (> 2.0)'
        elif sharpe > 1.0:
            interpretation = 'Good Sharpe ratio (> 1.0)'
        elif sharpe > 0.5:
            interpretation = 'Acceptable Sharpe ratio (> 0.5)'
        elif sharpe > 0.0:
            interpretation = 'Poor Sharpe ratio (barely positive)'
        else:
            interpretation = 'Negative Sharpe ratio (losing strategy)'

        return {
            'sharpe_ratio': sharpe,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'mean_return': mean_return,
            'std_return': std_return,
            'sample_size': n,
            'interpretation': interpretation
        }

    def get_comprehensive_analysis(self, pattern: str) -> Dict:
        """
        Get comprehensive CI analysis for all metrics

        Returns:
            Complete uncertainty analysis
        """
        win_rate_ci = self.calculate_win_rate_ci(pattern)
        ev_ci = self.calculate_ev_ci(pattern)
        sharpe_ci = self.calculate_sharpe_ci(pattern)

        # Overall recommendation
        sample_size = win_rate_ci['sample_size']

        if sample_size >= 50:
            overall_confidence = 'High - Reliable estimates'
        elif sample_size >= 30:
            overall_confidence = 'Good - Reasonable confidence'
        elif sample_size >= 20:
            overall_confidence = 'Moderate - Acceptable for trading'
        elif sample_size >= 10:
            overall_confidence = 'Low - Use caution'
        else:
            overall_confidence = 'Very Low - Insufficient data'

        # Check if all CIs are favorable
        win_rate_favorable = win_rate_ci['ci_lower'] >= 0.50
        ev_favorable = ev_ci['ci_lower'] > 0.0
        sharpe_favorable = sharpe_ci.get('sharpe_ratio', 0) > 0.5

        if win_rate_favorable and ev_favorable and sharpe_favorable:
            recommendation = '✓✓✓ ALL METRICS POSITIVE - Strong setup'
        elif win_rate_favorable and ev_favorable:
            recommendation = '✓✓ WIN RATE & EV POSITIVE - Good setup'
        elif ev_favorable:
            recommendation = '✓ EV POSITIVE - Acceptable setup'
        else:
            recommendation = '✗ NEGATIVE METRICS - Avoid this pattern'

        if sample_size < 20:
            recommendation += f' (Need {20 - sample_size} more trades for confidence)'

        return {
            'pattern': pattern,
            'timeframe': self.timeframe,
            'sample_size': sample_size,
            'overall_confidence': overall_confidence,
            'recommendation': recommendation,
            'win_rate_ci': win_rate_ci,
            'ev_ci': ev_ci,
            'sharpe_ci': sharpe_ci
        }

    def compare_patterns_by_uncertainty(self, patterns: List[str]) -> List[Dict]:
        """
        Compare patterns by uncertainty levels

        Helps identify which patterns need more data

        Args:
            patterns: List of pattern names

        Returns:
            Patterns sorted by uncertainty (most certain first)
        """
        results = []

        for pattern in patterns:
            win_rate_ci = self.calculate_win_rate_ci(pattern)

            results.append({
                'pattern': pattern,
                'sample_size': win_rate_ci['sample_size'],
                'ci_width': win_rate_ci['ci_width'],
                'win_rate': win_rate_ci['win_rate'],
                'ci_range': f"[{win_rate_ci['ci_lower']*100:.1f}%, {win_rate_ci['ci_upper']*100:.1f}%]"
            })

        # Sort by CI width (ascending = most certain first)
        results.sort(key=lambda x: x['ci_width'])

        return results

    def should_collect_more_data(self, pattern: str) -> Dict:
        """
        Determine if more data collection is needed

        Args:
            pattern: Pattern name

        Returns:
            Recommendation on data collection
        """
        ci_data = self.calculate_win_rate_ci(pattern)

        sample_size = ci_data['sample_size']
        ci_width = ci_data['ci_width']

        # Decision criteria
        needs_more_data = sample_size < 20 or ci_width > 0.30

        if sample_size >= 50 and ci_width <= 0.20:
            status = 'SUFFICIENT DATA'
            action = 'Ready for full trading'
            trades_needed = 0
        elif sample_size >= 30 and ci_width <= 0.30:
            status = 'GOOD DATA'
            action = 'Can trade, but more data helps'
            trades_needed = max(0, 50 - sample_size)
        elif sample_size >= 20:
            status = 'MINIMUM DATA'
            action = 'Can trade cautiously, collect more data'
            trades_needed = 30 - sample_size
        else:
            status = 'INSUFFICIENT DATA'
            action = 'Collect more trades before full commitment'
            trades_needed = 20 - sample_size

        return {
            'pattern': pattern,
            'sample_size': sample_size,
            'ci_width': ci_width,
            'needs_more_data': needs_more_data,
            'status': status,
            'action': action,
            'trades_needed': trades_needed
        }
