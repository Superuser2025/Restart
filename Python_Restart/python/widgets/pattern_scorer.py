"""
AppleTrader Pro - AI Pattern Quality Scorer
Rates trading setups from 0-100 based on confluence factors
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatternScore:
    """Pattern quality score breakdown"""
    total_score: int  # 0-100
    zone_alignment_score: int  # 0-20
    volume_score: int  # 0-25
    liquidity_score: int  # 0-15
    mtf_score: int  # 0-15
    session_score: int  # 0-10
    structure_score: int  # 0-10
    historical_score: int  # 0-5

    pattern_type: str
    price_level: float
    timestamp: datetime

    # Historical stats
    historical_win_rate: float  # 0.0 - 1.0
    historical_avg_rr: float
    historical_sample_size: int

    # Recommendation
    quality_tier: str  # "MUST TAKE", "STRONG", "GOOD", "WEAK", "SKIP"
    stars: int  # 1-5
    recommendation: str  # Detailed recommendation text


class PatternQualityScorer:
    """
    AI-powered pattern quality scoring system

    Evaluates trading setups based on multiple confluence factors
    and provides actionable recommendations
    """

    def __init__(self):
        # Historical pattern database (would be loaded from file/database)
        self.pattern_history: Dict[str, List[Dict]] = {}

        # Quality tier thresholds
        self.tier_thresholds = {
            90: ("MUST TAKE", 5, "⭐⭐⭐⭐⭐ Institutional Grade"),
            75: ("STRONG", 4, "⭐⭐⭐⭐ High Confidence"),
            60: ("GOOD", 3, "⭐⭐⭐ Acceptable"),
            40: ("WEAK", 2, "⭐⭐ Caution"),
            0:  ("SKIP", 1, "⭐ Low Quality")
        }

    def score_pattern(
        self,
        pattern_type: str,
        price_level: float,
        at_fvg: bool = False,
        at_order_block: bool = False,
        at_liquidity: bool = False,
        volume_ratio: float = 1.0,
        after_sweep: bool = False,
        mtf_h4_aligned: bool = False,
        mtf_h1_aligned: bool = False,
        mtf_m15_aligned: bool = False,
        in_session: str = "ASIAN",
        with_structure: bool = False,
        swing_level: bool = False,
    ) -> PatternScore:
        """
        Score a trading pattern based on confluence factors

        Args:
            pattern_type: Pattern name (e.g., "Bullish Engulfing", "Pin Bar")
            price_level: Price where pattern formed
            at_fvg: Pattern at FVG zone
            at_order_block: Pattern at Order Block
            at_liquidity: Pattern at Liquidity zone
            volume_ratio: Volume compared to average (1.0 = average, 3.0 = 3x average)
            after_sweep: Pattern formed after liquidity sweep
            mtf_h4_aligned: H4 timeframe aligned
            mtf_h1_aligned: H1 timeframe aligned
            mtf_m15_aligned: M15 timeframe aligned
            in_session: Trading session (LONDON, NY, ASIAN)
            with_structure: Aligned with market structure
            swing_level: At swing high/low

        Returns:
            PatternScore object with full breakdown
        """

        # ========================================
        # ZONE ALIGNMENT SCORING (0-20 points)
        # ========================================
        zone_score = 0

        if at_order_block and at_fvg:
            zone_score = 20  # Perfect: OB + FVG confluence
        elif at_order_block:
            zone_score = 15  # Strong: At Order Block
        elif at_fvg:
            zone_score = 12  # Good: At FVG
        elif at_liquidity:
            zone_score = 10  # Decent: At Liquidity
        elif swing_level:
            zone_score = 8   # Fair: At swing level
        else:
            zone_score = 0   # Weak: No zone alignment

        # ========================================
        # VOLUME CONFIRMATION (0-25 points)
        # ========================================
        volume_score = 0

        if volume_ratio >= 3.0:
            volume_score = 25  # Extreme volume spike
        elif volume_ratio >= 2.0:
            volume_score = 20  # High volume
        elif volume_ratio >= 1.5:
            volume_score = 15  # Above average volume
        elif volume_ratio >= 1.0:
            volume_score = 10  # Average volume
        else:
            volume_score = 5   # Low volume (weak)

        # ========================================
        # LIQUIDITY CONTEXT (0-15 points)
        # ========================================
        liquidity_score = 0

        if after_sweep and at_liquidity:
            liquidity_score = 15  # Perfect: Sweep + retest
        elif after_sweep:
            liquidity_score = 12  # Strong: After sweep
        elif at_liquidity:
            liquidity_score = 8   # Good: At liquidity
        else:
            liquidity_score = 0   # No liquidity context

        # ========================================
        # MULTI-TIMEFRAME CONFLUENCE (0-15 points)
        # ========================================
        mtf_score = 0
        aligned_count = sum([mtf_h4_aligned, mtf_h1_aligned, mtf_m15_aligned])

        if aligned_count == 3:
            mtf_score = 15  # All timeframes aligned
        elif aligned_count == 2:
            mtf_score = 12  # 2 timeframes aligned
        elif aligned_count == 1:
            mtf_score = 7   # 1 timeframe aligned
        else:
            mtf_score = 0   # No MTF confirmation

        # ========================================
        # SESSION QUALITY (0-10 points)
        # ========================================
        session_scores = {
            'LONDON': 10,   # Best session
            'NY': 10,       # Best session
            'OVERLAP': 8,   # London/NY overlap
            'ASIAN': 3,     # Low volatility
            'UNKNOWN': 0
        }
        session_score = session_scores.get(in_session, 0)

        # ========================================
        # STRUCTURE ALIGNMENT (0-10 points)
        # ========================================
        structure_score = 0

        if with_structure and swing_level:
            structure_score = 10  # Perfect: Structure + swing
        elif with_structure:
            structure_score = 7   # Good: With structure
        elif swing_level:
            structure_score = 5   # Fair: At swing only
        else:
            structure_score = 0   # No structure alignment

        # ========================================
        # HISTORICAL PERFORMANCE (0-5 points)
        # ========================================
        historical_win_rate, historical_avg_rr, sample_size = self._get_historical_stats(pattern_type)

        if sample_size >= 30 and historical_win_rate >= 0.70:
            historical_score = 5  # Proven high win rate
        elif sample_size >= 20 and historical_win_rate >= 0.60:
            historical_score = 4  # Good historical performance
        elif sample_size >= 10 and historical_win_rate >= 0.50:
            historical_score = 3  # Average performance
        elif sample_size > 0:
            historical_score = 2  # Some data available
        else:
            historical_score = 0  # No historical data

        # ========================================
        # TOTAL SCORE CALCULATION
        # ========================================
        total_score = (
            zone_score +
            volume_score +
            liquidity_score +
            mtf_score +
            session_score +
            structure_score +
            historical_score
        )

        # Determine quality tier
        tier, stars, tier_text = self._get_quality_tier(total_score)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            pattern_type, total_score, tier,
            zone_score, volume_score, liquidity_score,
            mtf_score, session_score, structure_score,
            historical_win_rate, historical_avg_rr
        )

        return PatternScore(
            total_score=total_score,
            zone_alignment_score=zone_score,
            volume_score=volume_score,
            liquidity_score=liquidity_score,
            mtf_score=mtf_score,
            session_score=session_score,
            structure_score=structure_score,
            historical_score=historical_score,
            pattern_type=pattern_type,
            price_level=price_level,
            timestamp=datetime.now(),
            historical_win_rate=historical_win_rate,
            historical_avg_rr=historical_avg_rr,
            historical_sample_size=sample_size,
            quality_tier=tier,
            stars=stars,
            recommendation=recommendation
        )

    def _get_historical_stats(self, pattern_type: str) -> Tuple[float, float, int]:
        """Get historical statistics for a pattern type"""

        if pattern_type not in self.pattern_history:
            return 0.0, 0.0, 0

        history = self.pattern_history[pattern_type]
        if not history:
            return 0.0, 0.0, 0

        wins = sum(1 for trade in history if trade.get('profit', 0) > 0)
        total = len(history)
        win_rate = wins / total if total > 0 else 0.0

        avg_rr = sum(trade.get('rr', 0) for trade in history) / total if total > 0 else 0.0

        return win_rate, avg_rr, total

    def _get_quality_tier(self, score: int) -> Tuple[str, int, str]:
        """Get quality tier based on score"""

        for threshold in sorted(self.tier_thresholds.keys(), reverse=True):
            if score >= threshold:
                tier, stars, text = self.tier_thresholds[threshold]
                return tier, stars, text

        return "SKIP", 1, "⭐ Low Quality"

    def _generate_recommendation(
        self,
        pattern_type: str,
        total_score: int,
        tier: str,
        zone_score: int,
        volume_score: int,
        liquidity_score: int,
        mtf_score: int,
        session_score: int,
        structure_score: int,
        historical_win_rate: float,
        historical_avg_rr: float
    ) -> str:
        """Generate detailed recommendation text"""

        if tier == "MUST TAKE":
            recommendation = f"✓ STRONG {pattern_type.upper()}\n"
            recommendation += f"Confidence: VERY HIGH\n"
            recommendation += f"This setup has {total_score}/100 quality score with excellent confluence.\n"

        elif tier == "STRONG":
            recommendation = f"✓ {pattern_type}\n"
            recommendation += f"Confidence: HIGH\n"
            recommendation += f"Quality score: {total_score}/100 - Strong setup worth taking.\n"

        elif tier == "GOOD":
            recommendation = f"→ {pattern_type}\n"
            recommendation += f"Confidence: MODERATE\n"
            recommendation += f"Acceptable setup ({total_score}/100) but not optimal.\n"

        elif tier == "WEAK":
            recommendation = f"⚠ {pattern_type}\n"
            recommendation += f"Confidence: LOW\n"
            recommendation += f"Weak setup ({total_score}/100) - consider skipping.\n"

        else:  # SKIP
            recommendation = f"✗ SKIP {pattern_type}\n"
            recommendation += f"Confidence: VERY LOW\n"
            recommendation += f"Poor quality ({total_score}/100) - avoid this trade.\n"

        # Add specific strengths/weaknesses
        if historical_win_rate > 0:
            recommendation += f"\nHistorical Win Rate: {historical_win_rate*100:.0f}% ({historical_avg_rr:.1f}R avg)\n"

        strengths = []
        if zone_score >= 15:
            strengths.append("Strong zone alignment")
        if volume_score >= 20:
            strengths.append("High volume confirmation")
        if liquidity_score >= 12:
            strengths.append("Liquidity sweep context")
        if mtf_score >= 12:
            strengths.append("MTF confluence")

        if strengths:
            recommendation += "\nStrengths: " + ", ".join(strengths)

        return recommendation

    def add_historical_trade(self, pattern_type: str, profit: float, rr: float):
        """Add a completed trade to historical database"""

        if pattern_type not in self.pattern_history:
            self.pattern_history[pattern_type] = []

        self.pattern_history[pattern_type].append({
            'profit': profit,
            'rr': rr,
            'timestamp': datetime.now()
        })


# Global scorer instance
pattern_scorer = PatternQualityScorer()
