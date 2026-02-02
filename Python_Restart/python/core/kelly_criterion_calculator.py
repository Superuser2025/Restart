"""
AppleTrader Pro - Kelly Criterion Calculator
Calculates optimal position sizing based on win probability

Formula: f* = (p × b - q) / b
Where:
- p = win probability
- q = loss probability (1 - p)
- b = win/loss ratio (avg_win / avg_loss)
- f* = fraction of capital to risk

Example:
- Win Rate: 60% (p=0.6, q=0.4)
- Avg Win: 2.5R, Avg Loss: 1R (b=2.5)
- Kelly = (0.6 × 2.5 - 0.4) / 2.5 = 1.1 / 2.5 = 44%

This means risk 44% of capital for optimal growth!
(Usually use Half Kelly = 22% for safety)
"""

from typing import Dict, Optional
from core.verbose_mode_manager import vprint


class KellyCriterionCalculator:
    """
    Kelly Criterion Calculator for optimal position sizing

    The Kelly Criterion maximizes long-term growth rate by
    determining the optimal fraction of capital to risk per trade.

    IMPORTANT: Full Kelly is aggressive. Most pros use:
    - Half Kelly (0.5 × Kelly)
    - Quarter Kelly (0.25 × Kelly)
    """

    def __init__(self, manager, timeframe: str):
        """
        Initialize Kelly calculator for specific timeframe

        Args:
            manager: StatisticalAnalysisManager instance
            timeframe: Trading timeframe (M15, H1, H4, D1)
        """
        self.manager = manager
        self.timeframe = timeframe
        self.min_sample_size = 20  # Minimum trades for reliable Kelly

        vprint(f"[KellyCalculator] Initialized for {timeframe}")

    def calculate_kelly_fraction(self, opportunity: Dict) -> Dict:
        """
        Calculate Kelly fraction for given opportunity

        Args:
            opportunity: Dict containing pattern, symbol, setup info

        Returns:
            Dict with:
            - kelly_full: Full Kelly %
            - kelly_half: Half Kelly % (recommended)
            - kelly_quarter: Quarter Kelly % (conservative)
            - win_rate: Win probability
            - win_loss_ratio: Avg win / avg loss
            - recommendation: str
        """
        pattern = opportunity.get('pattern', 'Unknown')
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            vprint(f"[KellyCalculator] No data for {pattern} on {self.timeframe}")
            return {
                'kelly_full': 0.0,
                'kelly_half': 0.0,
                'kelly_quarter': 0.0,
                'win_rate': 0.5,
                'win_loss_ratio': 1.0,
                'recommendation': 'Insufficient data - use fixed risk'
            }

        # Calculate win rate
        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        total_trades = wins + losses

        if total_trades == 0:
            return {
                'kelly_full': 0.0,
                'kelly_half': 0.0,
                'kelly_quarter': 0.0,
                'win_rate': 0.5,
                'win_loss_ratio': 1.0,
                'recommendation': 'No trades recorded'
            }

        win_rate = wins / total_trades
        loss_rate = 1 - win_rate

        # Get average win/loss ratio
        avg_win = pattern_stats.get('avg_win', 0.0)
        avg_loss = pattern_stats.get('avg_loss', 1.0)

        if avg_loss == 0:
            avg_loss = 1.0  # Prevent division by zero

        win_loss_ratio = avg_win / avg_loss

        # Kelly Criterion Formula
        # f* = (p × b - q) / b
        # where p = win rate, q = loss rate, b = win/loss ratio
        numerator = (win_rate * win_loss_ratio) - loss_rate
        kelly_full = numerator / win_loss_ratio if win_loss_ratio > 0 else 0.0

        # Cap at maximum Kelly (usually 25%)
        max_kelly = self.manager.config.max_kelly_fraction
        kelly_full = max(0.0, min(kelly_full, max_kelly))

        # Calculate fractional Kellys
        kelly_half = kelly_full * 0.5
        kelly_quarter = kelly_full * 0.25

        # Generate recommendation
        if kelly_full <= 0:
            recommendation = '✗ NEGATIVE KELLY - Do not trade this setup'
        elif kelly_full < 0.01:
            recommendation = '⚠ Very small edge - Consider skipping'
        elif kelly_full < 0.05:
            recommendation = '✓ Small edge - Use Quarter Kelly'
        elif kelly_full < 0.15:
            recommendation = '✓✓ Moderate edge - Use Half Kelly (recommended)'
        else:
            recommendation = '✓✓✓ Strong edge - Half Kelly or Full Kelly'

        if total_trades < self.min_sample_size:
            recommendation += f' (Collect {self.min_sample_size - total_trades} more trades for reliability)'

        result = {
            'kelly_full': kelly_full,
            'kelly_half': kelly_half,
            'kelly_quarter': kelly_quarter,
            'win_rate': win_rate,
            'win_loss_ratio': win_loss_ratio,
            'sample_size': total_trades,
            'recommendation': recommendation
        }

        vprint(f"[KellyCalculator] {pattern} on {self.timeframe}:")
        vprint(f"  Win Rate: {win_rate*100:.1f}%")
        vprint(f"  Win/Loss Ratio: {win_loss_ratio:.2f}")
        vprint(f"  Full Kelly: {kelly_full*100:.2f}%")
        vprint(f"  Half Kelly: {kelly_half*100:.2f}% (recommended)")
        vprint(f"  Quarter Kelly: {kelly_quarter*100:.2f}%")

        return result

    def calculate_position_size(self, opportunity: Dict, base_risk_percent: float) -> float:
        """
        Calculate optimal position size using Kelly

        Args:
            opportunity: Trading opportunity
            base_risk_percent: Base risk % (e.g., 1.0 = 1%)

        Returns:
            Optimal risk % to use
        """
        kelly_data = self.calculate_kelly_fraction(opportunity)

        # Use Half Kelly by default (safer)
        if self.manager.config.use_half_kelly:
            optimal_kelly = kelly_data['kelly_half']
        else:
            optimal_kelly = kelly_data['kelly_full']

        # If Kelly is 0 or negative, use minimum position size
        if optimal_kelly <= 0:
            return base_risk_percent * 0.1  # 10% of base risk

        # Scale base risk by Kelly
        # If Kelly = 2%, and base = 1%, use 2%
        # If Kelly = 0.5%, and base = 1%, use 0.5%
        optimal_risk = optimal_kelly * 100  # Convert to percentage

        # Cap at reasonable maximum (don't exceed base risk by more than 3x)
        max_risk = base_risk_percent * 3
        optimal_risk = min(optimal_risk, max_risk)

        # Ensure minimum risk
        min_risk = base_risk_percent * 0.1
        optimal_risk = max(optimal_risk, min_risk)

        vprint(f"[KellyCalculator] Position size: {optimal_risk:.2f}% (base: {base_risk_percent}%)")

        return optimal_risk

    def get_detailed_analysis(self, opportunity: Dict, account_balance: float = 10000.0) -> Dict:
        """
        Get detailed Kelly analysis with dollar amounts

        Args:
            opportunity: Trading opportunity
            account_balance: Account balance in dollars

        Returns:
            Detailed analysis with dollar amounts
        """
        kelly_data = self.calculate_kelly_fraction(opportunity)

        # Calculate dollar amounts
        full_amount = account_balance * kelly_data['kelly_full']
        half_amount = account_balance * kelly_data['kelly_half']
        quarter_amount = account_balance * kelly_data['kelly_quarter']

        # Calculate expected monthly growth (approximate)
        # Assume 20 trades per month
        expected_trades_per_month = 20
        win_rate = kelly_data['win_rate']
        win_loss_ratio = kelly_data['win_loss_ratio']

        # Expected value per trade (in R-multiples)
        ev = (win_rate * win_loss_ratio) - (1 - win_rate)

        # Monthly growth = EV × trades × Kelly%
        kelly_used = kelly_data['kelly_half'] if self.manager.config.use_half_kelly else kelly_data['kelly_full']
        monthly_growth = ev * expected_trades_per_month * kelly_used * 100  # Convert to %

        return {
            **kelly_data,
            'account_balance': account_balance,
            'full_kelly_dollars': full_amount,
            'half_kelly_dollars': half_amount,
            'quarter_kelly_dollars': quarter_amount,
            'expected_monthly_growth_pct': monthly_growth,
            'expected_monthly_growth_dollars': account_balance * (monthly_growth / 100)
        }

    def simulate_kelly_growth(self, opportunity: Dict, initial_balance: float = 10000.0, num_trades: int = 100) -> list:
        """
        Simulate account growth using Kelly vs Fixed risk

        Args:
            opportunity: Trading opportunity
            initial_balance: Starting balance
            num_trades: Number of trades to simulate

        Returns:
            List of balance snapshots
        """
        kelly_data = self.calculate_kelly_fraction(opportunity)
        win_rate = kelly_data['win_rate']
        win_loss_ratio = kelly_data['win_loss_ratio']
        kelly_fraction = kelly_data['kelly_half']  # Use half Kelly

        balance_kelly = initial_balance
        balance_fixed = initial_balance
        fixed_risk = 0.01  # 1% fixed risk

        results = []

        import random
        random.seed(42)  # Reproducible results

        for i in range(num_trades):
            # Generate trade outcome
            is_win = random.random() < win_rate

            # Kelly position sizing
            risk_amount_kelly = balance_kelly * kelly_fraction
            if is_win:
                profit_kelly = risk_amount_kelly * win_loss_ratio
                balance_kelly += profit_kelly
            else:
                balance_kelly -= risk_amount_kelly

            # Fixed position sizing
            risk_amount_fixed = balance_fixed * fixed_risk
            if is_win:
                profit_fixed = risk_amount_fixed * win_loss_ratio
                balance_fixed += profit_fixed
            else:
                balance_fixed -= risk_amount_fixed

            results.append({
                'trade_number': i + 1,
                'balance_kelly': balance_kelly,
                'balance_fixed': balance_fixed,
                'kelly_advantage': ((balance_kelly - balance_fixed) / balance_fixed) * 100
            })

        return results

    def should_adjust_risk(self, opportunity: Dict, current_risk: float) -> Dict:
        """
        Determine if current risk % should be adjusted

        Args:
            opportunity: Trading opportunity
            current_risk: Current risk % (e.g., 1.0 = 1%)

        Returns:
            Dict with adjustment recommendation
        """
        optimal_risk = self.calculate_position_size(opportunity, current_risk)

        difference = optimal_risk - current_risk
        percent_change = (difference / current_risk) * 100 if current_risk > 0 else 0

        if percent_change > 50:
            adjustment = 'INCREASE SIGNIFICANTLY'
            action = f'Increase risk from {current_risk:.2f}% to {optimal_risk:.2f}%'
        elif percent_change > 20:
            adjustment = 'INCREASE'
            action = f'Increase risk from {current_risk:.2f}% to {optimal_risk:.2f}%'
        elif percent_change < -50:
            adjustment = 'DECREASE SIGNIFICANTLY'
            action = f'Decrease risk from {current_risk:.2f}% to {optimal_risk:.2f}%'
        elif percent_change < -20:
            adjustment = 'DECREASE'
            action = f'Decrease risk from {current_risk:.2f}% to {optimal_risk:.2f}%'
        else:
            adjustment = 'MAINTAIN'
            action = f'Keep risk at {current_risk:.2f}% (optimal: {optimal_risk:.2f}%)'

        return {
            'current_risk': current_risk,
            'optimal_risk': optimal_risk,
            'difference': difference,
            'percent_change': percent_change,
            'adjustment': adjustment,
            'action': action
        }
