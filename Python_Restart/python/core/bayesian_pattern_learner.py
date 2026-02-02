"""
AppleTrader Pro - Bayesian Pattern Learner
Self-learning system that updates pattern win probabilities based on outcomes

Uses Bayesian inference with Beta-Binomial conjugate prior.

Formula: P(Win|Pattern, History) = (α + wins) / (α + β + total_trades)

Where:
- α (alpha) = prior successes (starts at 10 = neutral belief)
- β (beta) = prior failures (starts at 10 = neutral belief)
- wins = actual wins observed
- total_trades = actual trades taken

Example:
- Prior: α=10, β=10 → 50% win rate (neutral)
- After 5 wins, 3 losses:
  - Posterior = (10+5) / (10+10+5+3) = 15/28 = 53.6%
- After 20 wins, 10 losses:
  - Posterior = (10+20) / (10+10+20+10) = 30/50 = 60%

The more data, the more the posterior converges to actual win rate.
"""

from typing import Dict, Optional, List
from core.verbose_mode_manager import vprint
import math


class BayesianPatternLearner:
    """
    Bayesian Pattern Learner for adaptive probability estimation

    This implements Bayesian inference to continuously update pattern
    win probabilities as new trade outcomes are observed.

    Key advantages:
    1. Starts with neutral prior (no bias)
    2. Updates smoothly as data comes in
    3. Handles small sample sizes gracefully
    4. Converges to true win rate with more data
    """

    def __init__(self, manager, timeframe: str):
        """
        Initialize Bayesian learner for specific timeframe

        Args:
            manager: StatisticalAnalysisManager instance
            timeframe: Trading timeframe (M15, H1, H4, D1)
        """
        self.manager = manager
        self.timeframe = timeframe

        # Beta distribution parameters (conjugate prior for binomial)
        self.prior_alpha = manager.config.bayesian_prior_alpha  # Prior successes
        self.prior_beta = manager.config.bayesian_prior_beta    # Prior failures

        vprint(f"[BayesianLearner] Initialized for {timeframe}")
        vprint(f"  Prior: α={self.prior_alpha}, β={self.prior_beta} → {self._prior_mean()*100:.1f}% win rate")

    def _prior_mean(self) -> float:
        """Calculate prior mean (starting win rate)"""
        return self.prior_alpha / (self.prior_alpha + self.prior_beta)

    def get_pattern_probability(self, pattern: str) -> Dict:
        """
        Get Bayesian probability estimate for pattern

        Args:
            pattern: Pattern name (e.g., 'Hammer', 'Engulfing')

        Returns:
            Dict with:
            - posterior_mean: Best estimate of win probability
            - posterior_std: Standard deviation (uncertainty)
            - credible_interval: 95% credible interval [lower, upper]
            - sample_size: Number of observed trades
            - prior_influence: How much prior affects estimate (0-1)
        """
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)

        if not pattern_stats:
            # No data - return prior
            return {
                'posterior_mean': self._prior_mean(),
                'posterior_std': self._calculate_std(self.prior_alpha, self.prior_beta),
                'credible_interval': self._calculate_credible_interval(self.prior_alpha, self.prior_beta),
                'sample_size': 0,
                'prior_influence': 1.0,
                'confidence': 'Low (using prior only)'
            }

        wins = pattern_stats.get('wins', 0)
        losses = pattern_stats.get('losses', 0)
        total = wins + losses

        if total == 0:
            return {
                'posterior_mean': self._prior_mean(),
                'posterior_std': self._calculate_std(self.prior_alpha, self.prior_beta),
                'credible_interval': self._calculate_credible_interval(self.prior_alpha, self.prior_beta),
                'sample_size': 0,
                'prior_influence': 1.0,
                'confidence': 'Low (no data)'
            }

        # Bayesian update: posterior parameters
        posterior_alpha = self.prior_alpha + wins
        posterior_beta = self.prior_beta + losses

        # Posterior mean = E[θ] = α / (α + β)
        posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)

        # Posterior standard deviation
        posterior_std = self._calculate_std(posterior_alpha, posterior_beta)

        # 95% credible interval
        credible_interval = self._calculate_credible_interval(posterior_alpha, posterior_beta)

        # Prior influence: how much the prior affects the estimate
        # prior_influence = prior_strength / (prior_strength + sample_size)
        prior_strength = self.prior_alpha + self.prior_beta
        prior_influence = prior_strength / (prior_strength + total)

        # Confidence level
        if total >= 50:
            confidence = 'High'
        elif total >= 30:
            confidence = 'Good'
        elif total >= 20:
            confidence = 'Moderate'
        elif total >= 10:
            confidence = 'Fair'
        else:
            confidence = 'Low'

        result = {
            'posterior_mean': posterior_mean,
            'posterior_std': posterior_std,
            'credible_interval': credible_interval,
            'sample_size': total,
            'prior_influence': prior_influence,
            'confidence': confidence,
            'raw_win_rate': wins / total if total > 0 else 0.5,
            'wins': wins,
            'losses': losses
        }

        vprint(f"[BayesianLearner] {pattern} on {timeframe}:")
        vprint(f"  Sample: {wins}W/{losses}L = {(wins/total)*100:.1f}%")
        vprint(f"  Posterior: {posterior_mean*100:.1f}% (95% CI: [{credible_interval[0]*100:.1f}%, {credible_interval[1]*100:.1f}%])")
        vprint(f"  Prior influence: {prior_influence*100:.1f}%")

        return result

    def _calculate_std(self, alpha: float, beta: float) -> float:
        """
        Calculate standard deviation of Beta distribution

        Var[θ] = (α × β) / ((α + β)² × (α + β + 1))
        Std[θ] = sqrt(Var[θ])
        """
        alpha_beta_sum = alpha + beta
        variance = (alpha * beta) / (alpha_beta_sum**2 * (alpha_beta_sum + 1))
        return math.sqrt(variance)

    def _calculate_credible_interval(self, alpha: float, beta: float, confidence: float = 0.95) -> tuple:
        """
        Calculate credible interval for Beta distribution

        Uses approximate method for 95% credible interval.
        For Beta(α, β), the 95% CI is approximately:
        [mean - 1.96×std, mean + 1.96×std]

        Args:
            alpha: Alpha parameter
            beta: Beta parameter
            confidence: Confidence level (default 0.95 for 95%)

        Returns:
            (lower_bound, upper_bound)
        """
        mean = alpha / (alpha + beta)
        std = self._calculate_std(alpha, beta)

        # Z-score for confidence level
        if confidence == 0.95:
            z = 1.96
        elif confidence == 0.99:
            z = 2.576
        else:
            z = 1.96  # Default to 95%

        lower = max(0.0, mean - z * std)
        upper = min(1.0, mean + z * std)

        return (lower, upper)

    def update_from_trade(self, pattern: str, outcome: str, r_multiple: float):
        """
        Update pattern probability from trade outcome

        This is called by the system when a trade completes.

        Args:
            pattern: Pattern name
            outcome: 'win' or 'loss'
            r_multiple: R-multiple (e.g., 2.5 for 2.5R win)
        """
        # Get current probability before update
        prob_before = self.get_pattern_probability(pattern)

        # Record trade in manager
        trade_data = {
            'pattern': pattern,
            'outcome': outcome,
            'r_multiple': r_multiple,
            'timestamp': self._get_timestamp()
        }
        self.manager.add_trade_result(self.timeframe, trade_data)

        # Get updated probability
        prob_after = self.get_pattern_probability(pattern)

        vprint(f"[BayesianLearner] Updated {pattern}:")
        vprint(f"  Before: {prob_before['posterior_mean']*100:.1f}%")
        vprint(f"  After: {prob_after['posterior_mean']*100:.1f}%")
        vprint(f"  Change: {(prob_after['posterior_mean']-prob_before['posterior_mean'])*100:.2f}%")

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_learning_curve(self, pattern: str) -> List[Dict]:
        """
        Get learning curve showing how probability evolved over time

        Shows how the Bayesian estimate changed with each trade.

        Args:
            pattern: Pattern name

        Returns:
            List of probability estimates at each trade
        """
        tf_data = self.manager.get_timeframe_data(self.timeframe)
        trades = tf_data.get('trades', [])

        # Filter trades for this pattern
        pattern_trades = [t for t in trades if t.get('pattern') == pattern]

        learning_curve = []
        wins = 0
        losses = 0

        for i, trade in enumerate(pattern_trades):
            # Update counts
            if trade.get('outcome') == 'win':
                wins += 1
            else:
                losses += 1

            # Calculate posterior at this point
            posterior_alpha = self.prior_alpha + wins
            posterior_beta = self.prior_beta + losses
            posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)

            learning_curve.append({
                'trade_number': i + 1,
                'wins': wins,
                'losses': losses,
                'posterior_mean': posterior_mean,
                'raw_win_rate': wins / (wins + losses),
                'timestamp': trade.get('timestamp', '')
            })

        return learning_curve

    def compare_patterns(self, patterns: List[str]) -> List[Dict]:
        """
        Compare Bayesian probabilities across multiple patterns

        Args:
            patterns: List of pattern names

        Returns:
            List of pattern data sorted by posterior probability
        """
        results = []

        for pattern in patterns:
            prob_data = self.get_pattern_probability(pattern)
            results.append({
                'pattern': pattern,
                'posterior_mean': prob_data['posterior_mean'],
                'credible_interval': prob_data['credible_interval'],
                'sample_size': prob_data['sample_size'],
                'confidence': prob_data['confidence']
            })

        # Sort by posterior probability (descending)
        results.sort(key=lambda x: x['posterior_mean'], reverse=True)

        return results

    def get_detailed_analysis(self, pattern: str) -> Dict:
        """
        Get comprehensive Bayesian analysis for pattern

        Returns:
            Detailed analysis including:
            - Prior vs Posterior
            - Credible intervals
            - Learning curve
            - Recommendations
        """
        prob_data = self.get_pattern_probability(pattern)
        learning_curve = self.get_learning_curve(pattern)

        # Generate recommendation
        posterior_mean = prob_data['posterior_mean']
        ci_lower = prob_data['credible_interval'][0]
        ci_upper = prob_data['credible_interval'][1]
        sample_size = prob_data['sample_size']

        if posterior_mean >= 0.65 and ci_lower >= 0.55:
            recommendation = '✓✓✓ STRONG EDGE - High probability setup'
        elif posterior_mean >= 0.60 and ci_lower >= 0.50:
            recommendation = '✓✓ GOOD EDGE - Profitable setup'
        elif posterior_mean >= 0.55:
            recommendation = '✓ SLIGHT EDGE - Marginally profitable'
        elif posterior_mean >= 0.45:
            recommendation = '⚠ NEUTRAL - No clear edge'
        else:
            recommendation = '✗ NEGATIVE EDGE - Avoid this pattern'

        if sample_size < 20:
            recommendation += f' (Need {20 - sample_size} more trades for confidence)'

        # Calculate convergence: how much has posterior moved from prior?
        prior_mean = self._prior_mean()
        convergence = abs(posterior_mean - prior_mean)
        if convergence < 0.05:
            convergence_status = 'Low convergence - similar to prior'
        elif convergence < 0.15:
            convergence_status = 'Moderate convergence - learning in progress'
        else:
            convergence_status = 'High convergence - strong signal from data'

        return {
            **prob_data,
            'prior_mean': prior_mean,
            'convergence': convergence,
            'convergence_status': convergence_status,
            'learning_curve': learning_curve,
            'recommendation': recommendation
        }

    def should_trade(self, pattern: str, min_probability: float = 0.55) -> Dict:
        """
        Bayesian decision: should we trade this pattern?

        Args:
            pattern: Pattern name
            min_probability: Minimum win probability threshold

        Returns:
            Dict with decision and reasoning
        """
        prob_data = self.get_pattern_probability(pattern)

        posterior_mean = prob_data['posterior_mean']
        ci_lower = prob_data['credible_interval'][0]
        sample_size = prob_data['sample_size']

        # Decision criteria:
        # 1. Posterior mean must exceed threshold
        # 2. Lower CI must be reasonable (not too much uncertainty)
        # 3. Prefer more data (higher sample size)

        meets_threshold = posterior_mean >= min_probability
        ci_acceptable = ci_lower >= (min_probability - 0.10)  # Allow 10% margin
        has_data = sample_size >= 10

        should_trade = meets_threshold and (ci_acceptable or sample_size >= 30)

        if should_trade:
            decision = 'TRADE'
            if sample_size >= 30:
                reasoning = f'Strong confidence: {posterior_mean*100:.1f}% win probability with {sample_size} trades'
            else:
                reasoning = f'Acceptable: {posterior_mean*100:.1f}% win probability, but collect more data'
        else:
            decision = 'SKIP'
            if not meets_threshold:
                reasoning = f'Below threshold: {posterior_mean*100:.1f}% < {min_probability*100:.0f}%'
            elif not ci_acceptable:
                reasoning = f'Too uncertain: 95% CI [{ci_lower*100:.1f}%, {prob_data["credible_interval"][1]*100:.1f}%] too wide'
            else:
                reasoning = f'Insufficient data: only {sample_size} trades'

        return {
            'decision': decision,
            'should_trade': should_trade,
            'reasoning': reasoning,
            'posterior_probability': posterior_mean,
            'credible_interval': prob_data['credible_interval'],
            'sample_size': sample_size
        }

    def reset_pattern(self, pattern: str):
        """
        Reset pattern to prior (forget learned data)

        Use this if pattern behavior has fundamentally changed.
        """
        tf_data = self.manager.get_timeframe_data(self.timeframe)

        # Remove pattern data
        if pattern in tf_data.get('patterns', {}):
            del tf_data['patterns'][pattern]

        # Remove pattern trades
        trades = tf_data.get('trades', [])
        tf_data['trades'] = [t for t in trades if t.get('pattern') != pattern]

        self.manager._save_historical_data()
        vprint(f"[BayesianLearner] Reset {pattern} to prior")

    def record_outcome(self, pattern: str, is_win: bool):
        """
        Record a trade outcome to update Bayesian probability

        This is the LEARNING mechanism - each trade outcome updates
        the posterior probability for this pattern.

        Args:
            pattern: Pattern name (e.g., 'Bullish_Engulfing')
            is_win: True if trade won, False if lost
        """
        # Update pattern statistics in manager
        self.manager.record_pattern_outcome(
            timeframe=self.timeframe,
            pattern=pattern,
            is_win=is_win,
            profit=0.0  # Profit tracked separately by EV calculator
        )

        vprint(f"[BayesianLearner] Recorded {pattern} outcome on {self.timeframe}: {'WIN' if is_win else 'LOSS'}")

        # Get updated probability
        updated_prob = self.get_pattern_probability(pattern)
        vprint(f"[BayesianLearner]   New probability: {updated_prob['posterior_mean']*100:.1f}% (from {updated_prob['sample_size']} trades)")
