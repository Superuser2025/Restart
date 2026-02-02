"""
Trade Decision Assistant - Make Statistics Accessible to Non-Math Traders

Translates complex statistical analysis into plain-English actionable insights.

Key Features:
1. Simple YES/NO/MAYBE recommendations
2. Plain English explanations (no jargon)
3. Visual quality scores (1-10 stars)
4. Risk amount guidance (exact % to risk)
5. "What if I take 100 trades like this?" projections
6. Confidence levels (Low/Medium/High/Very High)
7. Comparison to portfolio average

Author: AppleTrader Pro
Date: 2026-01-30
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from core.verbose_mode_manager import vprint
from core.statistical_analysis_manager import StatisticalAnalysisManager


@dataclass
class TradeDecision:
    """Plain-English trade decision with all guidance"""

    # PRIMARY DECISION
    action: str  # "TAKE", "SKIP", "MAYBE"
    action_color: str  # "#10B981" (green), "#EF4444" (red), "#F59E0B" (yellow)
    action_icon: str  # "✓", "✗", "⚠"

    # SIMPLE QUALITY SCORE (1-10)
    quality_score: int  # 1-10 rating
    quality_stars: str  # "★★★★★★★★☆☆" (8/10)
    quality_description: str  # "Excellent", "Good", "Fair", "Poor"

    # PLAIN ENGLISH SUMMARY
    headline: str  # "Strong Setup - Take This Trade"
    explanation: str  # "This pattern wins 65% of the time and makes +0.5R per trade on average"
    recommendation: str  # "Risk 3.2% of your account for optimal growth"

    # CONFIDENCE LEVEL
    confidence: str  # "Very High", "High", "Medium", "Low", "Very Low"
    confidence_percent: int  # 0-100%
    confidence_icon: str  # "🟢🟢🟢" (3 bars) or "🟡🟡" (2 bars) or "🔴" (1 bar)
    confidence_explanation: str  # "47 historical trades analyzed - statistically significant"

    # RISK GUIDANCE
    risk_amount_conservative: float  # 1.6% (Quarter Kelly)
    risk_amount_balanced: float  # 3.2% (Half Kelly) - RECOMMENDED
    risk_amount_aggressive: float  # 6.4% (Full Kelly)
    risk_recommendation: str  # "Conservative", "Balanced", "Aggressive"
    risk_explanation: str  # "Based on 62% win rate and 2.1 R:R ratio"

    # PROJECTIONS (What if I take 100 trades like this?)
    projection_100_trades: str  # "Win 62, Lose 38, Net +45R profit"
    projection_explanation: str  # "If each trade risks $100, expect to make $4,500 over 100 trades"
    projection_warning: Optional[str]  # "⚠ Based on limited data (only 8 trades)"

    # COMPARISON
    vs_portfolio: Optional[str]  # "23% BETTER than your average trade" or None if no history
    vs_other_opportunities: Optional[str]  # "BEST setup available now" or "3rd best of 12"

    # TRACK RECORD
    historical_summary: str  # "Last 30 trades: 19W / 11L (63.3%)"
    recent_trend: Optional[str]  # "↑ Improving (won 4 of last 5)" or "↓ Declining"

    # WARNINGS / ALERTS
    warnings: List[str]  # ["⚠ Limited data - only 8 trades", "⚠ Below 50% win rate"]
    alerts: List[str]  # ["✓ Statistical significance achieved", "✓ Consistent with theory"]


class TradeDecisionAssistant:
    """
    Translates complex statistics into actionable trading decisions

    Makes math accessible to traders who aren't statisticians
    """

    def __init__(self):
        """Initialize the decision assistant"""
        self.stats_manager = StatisticalAnalysisManager.get_instance()
        vprint("[DecisionAssist] Initialized - Making stats human-friendly")

    def analyze_opportunity(self, opportunity: Dict) -> TradeDecision:
        """
        Analyze opportunity and return plain-English decision

        Args:
            opportunity: Opportunity dict with statistical data

        Returns:
            TradeDecision with all guidance
        """
        # Extract statistical data (with defaults if not enhanced)
        win_prob = opportunity.get('statistical_win_prob', 0.50)
        ev = opportunity.get('statistical_ev', 0.0)
        sample_size = opportunity.get('statistical_sample_size', 0)
        confidence_level = opportunity.get('statistical_confidence', 'No data')
        ci_lower = opportunity.get('statistical_ci_lower', 0.40)
        ci_upper = opportunity.get('statistical_ci_upper', 0.60)
        kelly_half = opportunity.get('statistical_kelly_half', 0.02)
        kelly_quarter = opportunity.get('statistical_kelly_quarter', 0.01)
        kelly_full = kelly_half * 2

        # Calculate decision components
        action, action_color, action_icon = self._determine_action(win_prob, ev, sample_size)
        quality_score, quality_stars, quality_desc = self._calculate_quality_score(win_prob, ev, sample_size)
        confidence, conf_pct, conf_icon, conf_explain = self._assess_confidence(sample_size, ci_lower, ci_upper)

        # Generate plain-English text
        headline = self._generate_headline(action, quality_score, win_prob, ev)
        explanation = self._generate_explanation(win_prob, ev, sample_size)
        recommendation = self._generate_recommendation(action, kelly_half, win_prob)

        # Risk guidance
        risk_rec = "Balanced" if action == "TAKE" else "Conservative"
        risk_explain = self._generate_risk_explanation(win_prob, opportunity.get('risk_reward', 2.0))

        # Projections
        projection_100 = self._generate_100_trade_projection(win_prob, ev)
        projection_explain = self._generate_projection_explanation(ev)
        projection_warning = self._generate_projection_warning(sample_size, confidence_level)

        # Comparisons
        vs_portfolio = None  # TODO: Implement portfolio comparison
        vs_other = None  # TODO: Implement opportunity ranking

        # Track record
        historical = self._generate_historical_summary(sample_size, win_prob)
        trend = self._detect_trend(opportunity)

        # Warnings and alerts
        warnings = self._generate_warnings(win_prob, ev, sample_size, ci_lower, ci_upper)
        alerts = self._generate_alerts(sample_size, win_prob, ev)

        return TradeDecision(
            action=action,
            action_color=action_color,
            action_icon=action_icon,
            quality_score=quality_score,
            quality_stars=quality_stars,
            quality_description=quality_desc,
            headline=headline,
            explanation=explanation,
            recommendation=recommendation,
            confidence=confidence,
            confidence_percent=conf_pct,
            confidence_icon=conf_icon,
            confidence_explanation=conf_explain,
            risk_amount_conservative=kelly_quarter * 100,
            risk_amount_balanced=kelly_half * 100,
            risk_amount_aggressive=kelly_full * 100,
            risk_recommendation=risk_rec,
            risk_explanation=risk_explain,
            projection_100_trades=projection_100,
            projection_explanation=projection_explain,
            projection_warning=projection_warning,
            vs_portfolio=vs_portfolio,
            vs_other_opportunities=vs_other,
            historical_summary=historical,
            recent_trend=trend,
            warnings=warnings,
            alerts=alerts
        )

    def _determine_action(self, win_prob: float, ev: float, sample_size: int) -> Tuple[str, str, str]:
        """Determine primary action: TAKE, SKIP, or MAYBE"""

        # TAKE: Strong positive EV + good win rate + sufficient data
        if ev > 0.5 and win_prob >= 0.60 and sample_size >= 20:
            return "TAKE", "#10B981", "✓"

        # TAKE: Good positive EV + decent win rate + some data
        if ev > 0.3 and win_prob >= 0.55 and sample_size >= 10:
            return "TAKE", "#10B981", "✓"

        # SKIP: Negative EV (losing money long-term)
        if ev < 0:
            return "SKIP", "#EF4444", "✗"

        # SKIP: Poor win rate
        if win_prob < 0.50 and sample_size >= 10:
            return "SKIP", "#EF4444", "✗"

        # MAYBE: Positive but marginal
        if ev > 0 and win_prob >= 0.50:
            return "MAYBE", "#F59E0B", "⚠"

        # MAYBE: Insufficient data
        if sample_size < 10:
            return "MAYBE", "#F59E0B", "⚠"

        # Default: MAYBE
        return "MAYBE", "#F59E0B", "⚠"

    def _calculate_quality_score(self, win_prob: float, ev: float, sample_size: int) -> Tuple[int, str, str]:
        """Calculate simple 1-10 quality score"""

        # Start with base score from EV
        if ev > 0.8:
            score = 10
        elif ev > 0.6:
            score = 9
        elif ev > 0.4:
            score = 8
        elif ev > 0.2:
            score = 7
        elif ev > 0:
            score = 6
        elif ev > -0.2:
            score = 5
        elif ev > -0.4:
            score = 4
        elif ev > -0.6:
            score = 3
        else:
            score = 2

        # Adjust for win rate
        if win_prob >= 0.65:
            score = min(10, score + 1)
        elif win_prob < 0.50:
            score = max(1, score - 2)

        # Adjust for sample size (confidence)
        if sample_size < 5:
            score = max(1, score - 2)  # Penalize low data
        elif sample_size >= 30:
            score = min(10, score + 1)  # Reward lots of data

        # Generate star rating
        stars = "★" * score + "☆" * (10 - score)

        # Description
        if score >= 9:
            desc = "Exceptional"
        elif score >= 8:
            desc = "Excellent"
        elif score >= 7:
            desc = "Very Good"
        elif score >= 6:
            desc = "Good"
        elif score >= 5:
            desc = "Fair"
        elif score >= 4:
            desc = "Below Average"
        elif score >= 3:
            desc = "Poor"
        else:
            desc = "Very Poor"

        return score, stars, desc

    def _assess_confidence(self, sample_size: int, ci_lower: float, ci_upper: float) -> Tuple[str, int, str, str]:
        """Assess confidence in the prediction"""

        # Calculate confidence interval width (narrower = more confident)
        ci_width = ci_upper - ci_lower

        # Determine confidence level
        if sample_size >= 50 and ci_width < 0.20:
            confidence = "Very High"
            percent = 95
            icon = "🟢🟢🟢🟢"
            explain = f"{sample_size} trades analyzed - very statistically significant"
        elif sample_size >= 30 and ci_width < 0.25:
            confidence = "High"
            percent = 80
            icon = "🟢🟢🟢"
            explain = f"{sample_size} trades analyzed - statistically significant"
        elif sample_size >= 15 and ci_width < 0.30:
            confidence = "Medium"
            percent = 60
            icon = "🟡🟡"
            explain = f"{sample_size} trades analyzed - moderate confidence"
        elif sample_size >= 5:
            confidence = "Low"
            percent = 40
            icon = "🟡"
            explain = f"Only {sample_size} trades - limited confidence"
        else:
            confidence = "Very Low"
            percent = 20
            icon = "🔴"
            explain = f"Only {sample_size} trades - very limited confidence"

        return confidence, percent, icon, explain

    def _generate_headline(self, action: str, quality_score: int, win_prob: float, ev: float) -> str:
        """Generate attention-grabbing headline"""

        if action == "TAKE":
            if quality_score >= 9:
                return "🔥 EXCEPTIONAL SETUP - Take This Trade!"
            elif quality_score >= 8:
                return "✓ STRONG SETUP - High Probability Trade"
            elif quality_score >= 7:
                return "✓ GOOD SETUP - Worth Taking"
            else:
                return "✓ DECENT SETUP - Proceed Carefully"

        elif action == "SKIP":
            if ev < -0.3:
                return "✗ AVOID - High Risk of Loss"
            elif win_prob < 0.45:
                return "✗ SKIP - Poor Win Rate"
            else:
                return "✗ PASS - Not Worth the Risk"

        else:  # MAYBE
            if ev > 0.2:
                return "⚠ MARGINAL - Consider Your Risk Tolerance"
            else:
                return "⚠ UNCERTAIN - Need More Data"

    def _generate_explanation(self, win_prob: float, ev: float, sample_size: int) -> str:
        """Generate plain-English explanation"""

        # Win rate explanation
        win_pct = int(win_prob * 100)
        if win_prob >= 0.60:
            win_text = f"wins {win_pct}% of the time (strong edge)"
        elif win_prob >= 0.55:
            win_text = f"wins {win_pct}% of the time (good edge)"
        elif win_prob >= 0.50:
            win_text = f"wins {win_pct}% of the time (slight edge)"
        else:
            win_text = f"only wins {win_pct}% of the time (losing pattern)"

        # EV explanation
        if ev > 0.5:
            ev_text = f"makes +{ev:.2f}R profit per trade on average (excellent)"
        elif ev > 0.2:
            ev_text = f"makes +{ev:.2f}R profit per trade on average (good)"
        elif ev > 0:
            ev_text = f"makes +{ev:.2f}R profit per trade on average (marginal)"
        else:
            ev_text = f"loses {abs(ev):.2f}R per trade on average (losing trade)"

        # Data quality
        if sample_size >= 30:
            data_text = f"Based on {sample_size} historical trades (reliable)."
        elif sample_size >= 10:
            data_text = f"Based on {sample_size} historical trades (moderate reliability)."
        elif sample_size > 0:
            data_text = f"Based on only {sample_size} trades (limited data - use caution)."
        else:
            data_text = "No historical data yet (system is learning)."

        return f"This pattern {win_text} and {ev_text}. {data_text}"

    def _generate_recommendation(self, action: str, kelly_half: float, win_prob: float) -> str:
        """Generate actionable recommendation"""

        if action == "TAKE":
            risk_pct = kelly_half * 100
            if risk_pct > 5:
                return f"Risk {risk_pct:.1f}% of your account (or less if conservative). This is a strong setup with {int(win_prob*100)}% historical win rate."
            elif risk_pct > 2:
                return f"Risk {risk_pct:.1f}% of your account for optimal growth. Adjust down if you prefer lower risk."
            else:
                return f"Risk {risk_pct:.1f}% of your account. Small position due to marginal edge - be conservative."

        elif action == "SKIP":
            return "Do NOT take this trade. Historical data shows it loses money over time. Wait for better opportunities."

        else:  # MAYBE
            return f"If you take this, risk no more than {kelly_half*100:.1f}% of your account. Limited data means higher uncertainty - proceed with caution."

    def _generate_risk_explanation(self, win_prob: float, rr: float) -> str:
        """Explain risk sizing logic"""
        return f"Based on {int(win_prob*100)}% win rate and {rr:.1f}:1 risk/reward ratio using Kelly Criterion math"

    def _generate_100_trade_projection(self, win_prob: float, ev: float) -> str:
        """Project results over 100 trades"""

        expected_wins = int(win_prob * 100)
        expected_losses = 100 - expected_wins
        expected_profit = ev * 100

        if expected_profit > 0:
            return f"Win ~{expected_wins}, Lose ~{expected_losses}, Net +{expected_profit:.0f}R profit"
        else:
            return f"Win ~{expected_wins}, Lose ~{expected_losses}, Net {expected_profit:.0f}R loss"

    def _generate_projection_explanation(self, ev: float) -> str:
        """Explain projection in dollars"""

        if ev > 0:
            profit_per_100 = int(ev * 100 * 100)  # Assuming $100 risk per trade
            return f"If each trade risks $100, expect to make ~${profit_per_100:,} over 100 trades"
        else:
            loss_per_100 = int(abs(ev) * 100 * 100)
            return f"If each trade risks $100, expect to LOSE ~${loss_per_100:,} over 100 trades"

    def _generate_projection_warning(self, sample_size: int, confidence: str) -> Optional[str]:
        """Generate warning if projection is unreliable"""

        if sample_size < 5:
            return f"⚠ Projection based on only {sample_size} trades - treat as rough estimate"
        elif sample_size < 10:
            return f"⚠ Limited data ({sample_size} trades) - projection has wide uncertainty"
        elif "No data" in confidence:
            return "⚠ No historical data - projection is theoretical only"

        return None

    def _generate_historical_summary(self, sample_size: int, win_prob: float) -> str:
        """Summarize historical track record"""

        if sample_size == 0:
            return "No historical trades yet - system is learning"

        wins = int(win_prob * sample_size)
        losses = sample_size - wins
        win_pct = win_prob * 100

        return f"Historical: {wins}W / {losses}L ({win_pct:.1f}%) from {sample_size} trades"

    def _detect_trend(self, opportunity: Dict) -> Optional[str]:
        """Detect if pattern is improving or declining"""
        # TODO: Implement trend detection from recent vs older trades
        return None

    def _generate_warnings(self, win_prob: float, ev: float, sample_size: int, ci_lower: float, ci_upper: float) -> List[str]:
        """Generate warnings about this trade"""

        warnings = []

        if sample_size < 5:
            warnings.append(f"⚠ Very limited data - only {sample_size} historical trades")
        elif sample_size < 10:
            warnings.append(f"⚠ Limited data - only {sample_size} trades (need 20+ for confidence)")

        if win_prob < 0.50 and sample_size >= 10:
            warnings.append(f"⚠ Below 50% win rate ({win_prob*100:.1f}%) - losing pattern")

        if ev < 0:
            warnings.append(f"⚠ Negative expected value ({ev:.2f}R) - loses money long-term")

        if (ci_upper - ci_lower) > 0.40:
            warnings.append(f"⚠ Wide uncertainty range ({ci_lower*100:.0f}%-{ci_upper*100:.0f}%) - inconsistent results")

        return warnings

    def _generate_alerts(self, sample_size: int, win_prob: float, ev: float) -> List[str]:
        """Generate positive alerts"""

        alerts = []

        if sample_size >= 30:
            alerts.append("✓ Statistical significance achieved (30+ trades)")

        if win_prob >= 0.65 and sample_size >= 15:
            alerts.append(f"✓ Strong win rate ({win_prob*100:.1f}%) with good sample size")

        if ev > 0.5:
            alerts.append(f"✓ Excellent expected value (+{ev:.2f}R per trade)")

        if win_prob >= 0.60 and ev > 0.3 and sample_size >= 20:
            alerts.append("✓ High-quality setup - all metrics strong")

        return alerts

    def format_for_ui(self, decision: TradeDecision) -> str:
        """Format decision as readable text block for UI display"""

        output = []
        output.append("=" * 60)
        output.append(f"{decision.action_icon} {decision.headline}")
        output.append("=" * 60)
        output.append("")
        output.append(f"Quality: {decision.quality_score}/10 {decision.quality_stars} ({decision.quality_description})")
        output.append(f"Confidence: {decision.confidence} {decision.confidence_icon} ({decision.confidence_percent}%)")
        output.append("")
        output.append(f"EXPLANATION:")
        output.append(f"  {decision.explanation}")
        output.append("")
        output.append(f"RECOMMENDATION:")
        output.append(f"  {decision.recommendation}")
        output.append("")
        output.append(f"RISK SIZING:")
        output.append(f"  Conservative: {decision.risk_amount_conservative:.1f}%")
        output.append(f"  Balanced: {decision.risk_amount_balanced:.1f}% ← RECOMMENDED")
        output.append(f"  Aggressive: {decision.risk_amount_aggressive:.1f}%")
        output.append(f"  ({decision.risk_explanation})")
        output.append("")
        output.append(f"IF YOU TAKE 100 TRADES LIKE THIS:")
        output.append(f"  {decision.projection_100_trades}")
        output.append(f"  {decision.projection_explanation}")
        if decision.projection_warning:
            output.append(f"  {decision.projection_warning}")
        output.append("")
        output.append(f"TRACK RECORD:")
        output.append(f"  {decision.historical_summary}")

        if decision.warnings:
            output.append("")
            output.append("WARNINGS:")
            for warning in decision.warnings:
                output.append(f"  {warning}")

        if decision.alerts:
            output.append("")
            output.append("POSITIVE SIGNALS:")
            for alert in decision.alerts:
                output.append(f"  {alert}")

        output.append("")
        output.append("=" * 60)

        return "\n".join(output)


# Singleton instance
trade_decision_assistant = TradeDecisionAssistant()
