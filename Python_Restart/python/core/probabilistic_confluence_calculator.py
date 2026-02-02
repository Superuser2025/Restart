"""
AppleTrader Pro - Probabilistic Confluence Calculator
Calculates confluence using proper probability mathematics

Instead of adding points, multiply probability boosts.

Example:
- Base probability: 50%
- Volume confirmation: ×1.15 (15% boost) → 57.5%
- MTF alignment: ×1.30 (30% boost) → 74.8%
- Pattern strength 8/10: ×1.20 (20% boost) → 89.7%
- Final: 89.7% win probability

This is mathematically correct vs. just adding points.
"""

from typing import Dict, List, Optional
from core.verbose_mode_manager import vprint


class ProbabilisticConfluenceCalculator:
    """
    Probabilistic Confluence Calculator

    Uses probability multiplication to properly combine multiple factors.

    Key advantages over additive scoring:
    1. Mathematically correct probability combination
    2. Factors can't push probability above 100%
    3. Each factor has meaningful impact
    4. Results in actual win probability (not arbitrary score)
    """

    def __init__(self, manager, timeframe: str):
        """
        Initialize confluence calculator for specific timeframe

        Args:
            manager: StatisticalAnalysisManager instance
            timeframe: Trading timeframe (M15, H1, H4, D1)
        """
        self.manager = manager
        self.timeframe = timeframe

        # Probability multipliers for each factor
        # These are the boost percentages when factor is present
        self.factor_multipliers = {
            'volume_confirmation': 1.15,      # 15% boost
            'mtf_alignment': 1.30,            # 30% boost (strongest)
            'pattern_strength': 1.20,         # 20% boost (if strong pattern)
            'liquidity_sweep': 1.10,          # 10% boost
            'order_block': 1.15,              # 15% boost
            'fair_value_gap': 1.10,           # 10% boost
            'structure_break': 1.12,          # 12% boost
            'session_quality': 1.08,          # 8% boost
            'low_spread': 1.05,               # 5% boost
            'news_avoidance': 1.05,           # 5% boost
            'correlation_check': 1.08,        # 8% boost
            'ml_confirmation': 1.15           # 15% boost
        }

        vprint(f"[ConfluenceCalculator] Initialized for {timeframe}")

    def calculate_probability(self, opportunity: Dict) -> Dict:
        """
        Calculate win probability using probabilistic confluence

        Args:
            opportunity: Dict containing setup factors

        Returns:
            Dict with:
            - final_probability: Combined win probability
            - base_probability: Starting probability
            - factors_applied: List of factors that boosted probability
            - factor_breakdown: Detailed breakdown of each factor's contribution
        """
        # Start with base probability from pattern
        pattern = opportunity.get('pattern', 'Unknown')

        # Get historical win rate as base (or 50% if no data)
        pattern_stats = self.manager.get_pattern_statistics(self.timeframe, pattern)
        if pattern_stats and pattern_stats.get('wins', 0) + pattern_stats.get('losses', 0) >= 10:
            wins = pattern_stats.get('wins', 0)
            total = wins + pattern_stats.get('losses', 0)
            base_probability = wins / total
            vprint(f"[ConfluenceCalculator] Using historical base: {base_probability*100:.1f}%")
        else:
            base_probability = 0.50  # Neutral starting point
            vprint(f"[ConfluenceCalculator] Using neutral base: 50%")

        current_probability = base_probability
        factors_applied = []
        factor_breakdown = []

        # Apply each factor
        factors_to_check = [
            ('volume_confirmation', opportunity.get('volume_ok', False)),
            ('mtf_alignment', opportunity.get('mtf_aligned', False)),
            ('pattern_strength', opportunity.get('pattern_strength', 0) >= 8),
            ('liquidity_sweep', opportunity.get('liquidity_sweep', False)),
            ('order_block', opportunity.get('order_block', False)),
            ('fair_value_gap', opportunity.get('fvg', False)),
            ('structure_break', opportunity.get('structure_break', False)),
            ('session_quality', opportunity.get('good_session', False)),
            ('low_spread', opportunity.get('spread_ok', False)),
            ('news_avoidance', opportunity.get('no_news', False)),
            ('correlation_check', opportunity.get('correlation_ok', False)),
            ('ml_confirmation', opportunity.get('ml_confirmed', False))
        ]

        for factor_name, is_present in factors_to_check:
            if is_present:
                multiplier = self.factor_multipliers.get(factor_name, 1.0)
                previous_prob = current_probability
                current_probability *= multiplier

                # Normalize to never exceed 95% (keep some uncertainty)
                current_probability = min(0.95, current_probability)

                factors_applied.append(factor_name)
                factor_breakdown.append({
                    'factor': factor_name,
                    'multiplier': multiplier,
                    'probability_before': previous_prob,
                    'probability_after': current_probability,
                    'boost': (current_probability - previous_prob)
                })

                vprint(f"  + {factor_name}: ×{multiplier:.2f} → {current_probability*100:.1f}%")

        # Calculate confidence score (0-100)
        confidence_score = current_probability * 100

        result = {
            'final_probability': current_probability,
            'base_probability': base_probability,
            'confidence_score': confidence_score,
            'factors_applied': factors_applied,
            'factor_breakdown': factor_breakdown,
            'num_factors': len(factors_applied),
            'pattern': pattern
        }

        vprint(f"[ConfluenceCalculator] Final: {current_probability*100:.1f}% ({len(factors_applied)} factors)")

        return result

    def get_detailed_analysis(self, opportunity: Dict) -> Dict:
        """
        Get detailed confluence analysis with recommendations

        Args:
            opportunity: Trading opportunity

        Returns:
            Comprehensive analysis
        """
        prob_data = self.calculate_probability(opportunity)

        final_prob = prob_data['final_probability']
        num_factors = prob_data['num_factors']

        # Generate recommendation
        if final_prob >= 0.75 and num_factors >= 5:
            recommendation = '✓✓✓ EXCEPTIONAL SETUP - Very high probability'
            strength = 'Exceptional'
        elif final_prob >= 0.70 and num_factors >= 4:
            recommendation = '✓✓✓ EXCELLENT SETUP - High probability'
            strength = 'Excellent'
        elif final_prob >= 0.65 and num_factors >= 3:
            recommendation = '✓✓ STRONG SETUP - Good probability'
            strength = 'Strong'
        elif final_prob >= 0.60:
            recommendation = '✓ GOOD SETUP - Above average probability'
            strength = 'Good'
        elif final_prob >= 0.55:
            recommendation = '✓ ACCEPTABLE SETUP - Slight edge'
            strength = 'Acceptable'
        elif final_prob >= 0.50:
            recommendation = '⚠ MARGINAL SETUP - Minimal edge'
            strength = 'Marginal'
        else:
            recommendation = '✗ POOR SETUP - Below 50% probability'
            strength = 'Poor'

        # Calculate Expected Value integration
        # EV = P(Win) × AvgWin - P(Loss) × AvgLoss
        pattern_stats = self.manager.get_pattern_statistics(
            self.timeframe,
            opportunity.get('pattern', 'Unknown')
        )

        if pattern_stats:
            avg_win = pattern_stats.get('avg_win', 2.5)
            avg_loss = pattern_stats.get('avg_loss', 1.0)
            ev = (final_prob * avg_win) - ((1 - final_prob) * avg_loss)
        else:
            # Assume 2.5:1 reward/risk ratio
            avg_win = 2.5
            avg_loss = 1.0
            ev = (final_prob * avg_win) - ((1 - final_prob) * avg_loss)

        return {
            **prob_data,
            'recommendation': recommendation,
            'strength': strength,
            'expected_value': ev,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }

    def compare_setups(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Compare multiple opportunities by probability

        Args:
            opportunities: List of trading opportunities

        Returns:
            Sorted list (highest probability first)
        """
        results = []

        for opp in opportunities:
            prob_data = self.calculate_probability(opp)
            results.append({
                'opportunity': opp,
                'probability': prob_data['final_probability'],
                'confidence_score': prob_data['confidence_score'],
                'num_factors': prob_data['num_factors'],
                'pattern': opp.get('pattern', 'Unknown'),
                'symbol': opp.get('symbol', 'Unknown')
            })

        # Sort by probability (descending)
        results.sort(key=lambda x: x['probability'], reverse=True)

        return results

    def get_factor_importance(self) -> List[Dict]:
        """
        Get factor importance ranking

        Returns:
            Factors sorted by impact (multiplier strength)
        """
        factors = []

        for factor_name, multiplier in self.factor_multipliers.items():
            boost_pct = (multiplier - 1.0) * 100

            factors.append({
                'factor': factor_name,
                'multiplier': multiplier,
                'boost_percent': boost_pct,
                'impact': self._classify_impact(boost_pct)
            })

        # Sort by boost percentage (descending)
        factors.sort(key=lambda x: x['boost_percent'], reverse=True)

        return factors

    def _classify_impact(self, boost_pct: float) -> str:
        """Classify factor impact"""
        if boost_pct >= 25:
            return 'Very High'
        elif boost_pct >= 15:
            return 'High'
        elif boost_pct >= 10:
            return 'Medium'
        elif boost_pct >= 5:
            return 'Low'
        else:
            return 'Very Low'

    def calibrate_multipliers(self, historical_data: List[Dict]):
        """
        Calibrate multipliers based on historical performance

        This is advanced: analyze which factors actually improve win rate

        Args:
            historical_data: List of past trades with factors and outcomes
        """
        # Calculate empirical win rates for each factor
        factor_impact = {}

        for factor_name in self.factor_multipliers.keys():
            # Trades with this factor
            with_factor = [t for t in historical_data if t.get(factor_name, False)]
            # Trades without this factor
            without_factor = [t for t in historical_data if not t.get(factor_name, False)]

            if len(with_factor) >= 10 and len(without_factor) >= 10:
                # Calculate win rates
                with_win_rate = sum(1 for t in with_factor if t.get('outcome') == 'win') / len(with_factor)
                without_win_rate = sum(1 for t in without_factor if t.get('outcome') == 'win') / len(without_factor)

                # Calculate empirical multiplier
                if without_win_rate > 0:
                    empirical_multiplier = with_win_rate / without_win_rate
                    factor_impact[factor_name] = {
                        'empirical_multiplier': empirical_multiplier,
                        'with_win_rate': with_win_rate,
                        'without_win_rate': without_win_rate,
                        'sample_with': len(with_factor),
                        'sample_without': len(without_factor)
                    }

        vprint("[ConfluenceCalculator] Factor calibration:")
        for factor, data in factor_impact.items():
            vprint(f"  {factor}: ×{data['empirical_multiplier']:.2f} (with: {data['with_win_rate']*100:.1f}%, without: {data['without_win_rate']*100:.1f}%)")

        return factor_impact

    def should_trade(self, opportunity: Dict, min_probability: float = 0.60) -> Dict:
        """
        Decision helper: should we take this trade?

        Args:
            opportunity: Trading opportunity
            min_probability: Minimum probability threshold

        Returns:
            Decision dict
        """
        prob_data = self.calculate_probability(opportunity)

        final_prob = prob_data['final_probability']
        num_factors = prob_data['num_factors']

        should_trade = final_prob >= min_probability

        if should_trade:
            if num_factors >= 5:
                reasoning = f'Strong confluence: {final_prob*100:.1f}% probability with {num_factors} factors'
            elif num_factors >= 3:
                reasoning = f'Good confluence: {final_prob*100:.1f}% probability with {num_factors} factors'
            else:
                reasoning = f'Acceptable: {final_prob*100:.1f}% probability, but only {num_factors} factors'
        else:
            if num_factors < 3:
                reasoning = f'Too few factors: only {num_factors} confluence factors present'
            else:
                reasoning = f'Below threshold: {final_prob*100:.1f}% < {min_probability*100:.0f}%'

        return {
            'should_trade': should_trade,
            'decision': 'TRADE' if should_trade else 'SKIP',
            'reasoning': reasoning,
            'final_probability': final_prob,
            'num_factors': num_factors,
            'factors': prob_data['factors_applied']
        }

    def simulate_factor_addition(self, opportunity: Dict, new_factor: str) -> Dict:
        """
        Simulate what happens if we add a new factor

        Useful for: "What if MTF was also aligned?"

        Args:
            opportunity: Current opportunity
            new_factor: Factor to add

        Returns:
            Comparison before/after
        """
        # Calculate current
        current_prob = self.calculate_probability(opportunity)

        # Add new factor
        modified_opp = opportunity.copy()
        factor_key = new_factor.replace('_', ' ').lower()

        if new_factor == 'mtf_alignment':
            modified_opp['mtf_aligned'] = True
        elif new_factor == 'volume_confirmation':
            modified_opp['volume_ok'] = True
        elif new_factor == 'liquidity_sweep':
            modified_opp['liquidity_sweep'] = True
        # Add more mappings as needed

        # Calculate new probability
        new_prob = self.calculate_probability(modified_opp)

        improvement = new_prob['final_probability'] - current_prob['final_probability']
        improvement_pct = (improvement / current_prob['final_probability']) * 100

        return {
            'current_probability': current_prob['final_probability'],
            'new_probability': new_prob['final_probability'],
            'improvement': improvement,
            'improvement_percent': improvement_pct,
            'factor_added': new_factor,
            'multiplier': self.factor_multipliers.get(new_factor, 1.0)
        }
