"""
AggressivenessManager - Controls trading aggressiveness levels

Based on MT5 EA v4 aggressiveness system, but FIXED to work correctly:
- MT5 EA BUG: require_mtf/require_volume act as hard blockers (broken design)
- OUR FIX: All factors contribute to confluence score, no absolute blockers

Levels:
- Level 1 (Ultra Conservative): Strictest - requires most confluence (6/10 factors)
- Level 2 (Conservative): Strict - 5/10 factors required
- Level 3 (Balanced): Default - 4/10 factors required
- Level 4 (Aggressive): Lenient - 3/10 factors required
- Level 5 (Maximum): Most lenient - 2/10 factors required

CRITICAL INSIGHT: "Least aggressive" means STRICTER requirements (more confirmation needed),
NOT that it never trades. Level 1 should still trade when high confluence is present.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AggressivenessPreset:
    """Defines thresholds for a specific aggressiveness level"""

    # Core settings
    level: int
    name: str
    description: str

    # Confluence requirements (out of 10 possible factors)
    confluence_required: int  # How many factors must be present to trade

    # Pattern requirements
    min_pattern_strength: int  # Minimum pattern strength (1-10 scale)
    min_quality_score: int  # Minimum quality score (0-100)

    # Trade limits
    max_trades_per_symbol: int

    # Risk adjustment
    risk_multiplier: float  # Multiplier for position size (0.5 = half size)

    # TP adjustment (higher = larger targets)
    tp_multiplier: float

    # Importance weights for each factor (how much each contributes to score)
    # These don't block - they just affect the score calculation
    volume_weight: float  # How important is volume confirmation (0.0-2.0)
    mtf_weight: float  # How important is MTF alignment (0.0-2.0)
    structure_weight: float  # How important is market structure (0.0-2.0)

    # R:R requirements
    min_risk_reward: float


class AggressivenessManager:
    """
    Manages trading aggressiveness levels and dynamically adjusts filter thresholds

    Usage:
        aggressiveness_manager.set_level(3)  # Set to Balanced
        thresholds = aggressiveness_manager.get_current_thresholds()

    Signals are emitted when level changes so UI can update.
    """

    def __init__(self):
        self.current_level = 3  # Default: Balanced
        self.presets: Dict[int, AggressivenessPreset] = {}
        self._callbacks = []  # Functions to call when level changes

        # Initialize all 5 presets
        self._init_presets()

    def _init_presets(self):
        """Initialize the 5 aggressiveness presets based on MT5 EA specs"""

        # Level 1: ULTRA CONSERVATIVE
        # Requires maximum confluence - only the BEST setups
        # Still trades when 6+ factors align
        self.presets[1] = AggressivenessPreset(
            level=1,
            name="Ultra Conservative",
            description="Maximum confluence required. Only A+ setups.",
            confluence_required=6,  # Need 6 out of 10 factors
            min_pattern_strength=7,  # Strong patterns only (7-10)
            min_quality_score=75,  # High quality minimum
            max_trades_per_symbol=1,
            risk_multiplier=0.5,  # Half position size
            tp_multiplier=1.5,  # Conservative targets
            volume_weight=1.5,  # Volume is important
            mtf_weight=2.0,  # MTF is very important
            structure_weight=1.5,  # Structure is important
            min_risk_reward=2.0  # Minimum 2:1 R:R
        )

        # Level 2: CONSERVATIVE
        # High confluence requirement - quality over quantity
        self.presets[2] = AggressivenessPreset(
            level=2,
            name="Conservative",
            description="High confluence required. Quality setups only.",
            confluence_required=5,  # Need 5 out of 10 factors
            min_pattern_strength=6,  # Decent patterns (6-10)
            min_quality_score=65,  # Good quality minimum
            max_trades_per_symbol=2,
            risk_multiplier=0.75,
            tp_multiplier=1.8,
            volume_weight=1.2,
            mtf_weight=1.5,
            structure_weight=1.2,
            min_risk_reward=1.8
        )

        # Level 3: BALANCED (Default)
        # Moderate confluence - the sweet spot
        self.presets[3] = AggressivenessPreset(
            level=3,
            name="Balanced",
            description="Moderate confluence. Good balance of quality and quantity.",
            confluence_required=4,  # Need 4 out of 10 factors
            min_pattern_strength=5,  # Standard patterns (5-10)
            min_quality_score=55,  # Moderate quality
            max_trades_per_symbol=3,
            risk_multiplier=1.0,  # Standard position size
            tp_multiplier=2.0,
            volume_weight=1.0,
            mtf_weight=1.0,
            structure_weight=1.0,
            min_risk_reward=1.5
        )

        # Level 4: AGGRESSIVE
        # Lower confluence - more trades, accept more risk
        self.presets[4] = AggressivenessPreset(
            level=4,
            name="Aggressive",
            description="Lower confluence required. More frequent trading.",
            confluence_required=3,  # Need 3 out of 10 factors
            min_pattern_strength=4,  # Accept weaker patterns
            min_quality_score=45,  # Lower quality accepted
            max_trades_per_symbol=5,
            risk_multiplier=1.25,  # Slightly larger positions
            tp_multiplier=2.5,  # Larger targets
            volume_weight=0.8,  # Volume less critical
            mtf_weight=0.8,  # MTF less critical
            structure_weight=0.8,
            min_risk_reward=1.3
        )

        # Level 5: MAXIMUM AGGRESSION
        # Minimal confluence - trade almost anything that looks viable
        self.presets[5] = AggressivenessPreset(
            level=5,
            name="Maximum",
            description="Minimal confluence. Maximum opportunity capture.",
            confluence_required=2,  # Need only 2 out of 10 factors
            min_pattern_strength=3,  # Accept weak patterns
            min_quality_score=35,  # Low quality threshold
            max_trades_per_symbol=8,
            risk_multiplier=1.5,  # Larger positions
            tp_multiplier=3.0,  # Ambitious targets
            volume_weight=0.5,  # Volume optional
            mtf_weight=0.5,  # MTF optional
            structure_weight=0.5,  # Structure optional
            min_risk_reward=1.2  # Lower R:R acceptable
        )

    def set_level(self, level: int) -> bool:
        """
        Set the aggressiveness level (1-5)

        Returns:
            True if level was changed, False if invalid level
        """
        if level < 1 or level > 5:
            return False

        old_level = self.current_level
        self.current_level = level

        # Notify callbacks if level changed
        if old_level != level:
            for callback in self._callbacks:
                try:
                    callback(level, self.presets[level])
                except Exception as e:
                    print(f"[AggressivenessManager] Callback error: {e}")

        return True

    def get_level(self) -> int:
        """Get current aggressiveness level"""
        return self.current_level

    def get_preset(self, level: int = None) -> Optional[AggressivenessPreset]:
        """Get preset for specified level (or current if not specified)"""
        level = level or self.current_level
        return self.presets.get(level)

    def get_current_preset(self) -> AggressivenessPreset:
        """Get the current active preset"""
        return self.presets[self.current_level]

    def get_filter_thresholds(self) -> Dict:
        """
        Get filter thresholds based on current aggressiveness level

        This returns a dict that can be applied to FilterManager
        """
        preset = self.presets[self.current_level]

        return {
            'min_quality_score': preset.min_quality_score,
            'min_pattern_strength': preset.min_pattern_strength,
            'min_rr_ratio': preset.min_risk_reward,
            'confluence_required': preset.confluence_required,
            'max_trades_per_symbol': preset.max_trades_per_symbol,
            'risk_multiplier': preset.risk_multiplier,
            'tp_multiplier': preset.tp_multiplier,
            'volume_weight': preset.volume_weight,
            'mtf_weight': preset.mtf_weight,
            'structure_weight': preset.structure_weight,
        }

    def on_level_changed(self, callback):
        """Register callback for level changes: callback(level, preset)"""
        self._callbacks.append(callback)

    def get_level_name(self, level: int = None) -> str:
        """Get human-readable name for level"""
        level = level or self.current_level
        preset = self.presets.get(level)
        return preset.name if preset else "Unknown"

    def get_level_description(self, level: int = None) -> str:
        """Get description for level"""
        level = level or self.current_level
        preset = self.presets.get(level)
        return preset.description if preset else ""

    def calculate_confluence_score(self, opportunity: Dict) -> int:
        """
        Calculate confluence score for an opportunity (0-10)

        This is the FIXED implementation that scores ALL factors,
        not the broken MT5 EA approach of hard blocking.

        Factors scored:
        1. Pattern strength >= threshold
        2. MTF alignment
        3. Volume confirmation
        4. Market structure aligned
        5. Quality score >= threshold
        6. R:R ratio >= threshold
        7. Session quality (not Asian/dead)
        8. Spread acceptable
        9. Liquidity sweep present
        10. Order block valid
        """
        score = 0
        preset = self.presets[self.current_level]

        # 1. Pattern strength
        pattern_strength = opportunity.get('pattern_strength', 5)
        if pattern_strength >= preset.min_pattern_strength:
            score += 1

        # 2. MTF alignment (weighted)
        mtf_confirmed = opportunity.get('mtf_confirmed', False)
        if mtf_confirmed:
            score += min(2, int(preset.mtf_weight))  # Can add up to 2 points if weight high

        # 3. Volume confirmation (weighted)
        volume = opportunity.get('volume', 0)
        min_volume = 50  # Reasonable minimum
        if volume >= min_volume:
            score += min(2, int(preset.volume_weight))  # Can add up to 2 points

        # 4. Market structure aligned (weighted)
        structure_aligned = opportunity.get('structure_aligned', False)
        if structure_aligned:
            score += min(2, int(preset.structure_weight))  # Can add up to 2 points

        # 5. Quality score
        quality_score = opportunity.get('quality_score', 0)
        if quality_score >= preset.min_quality_score:
            score += 1

        # 6. R:R ratio
        rr = opportunity.get('risk_reward', 0)
        if rr >= preset.min_risk_reward:
            score += 1

        # 7. Session quality (not Asian/dead)
        session = opportunity.get('session', 'unknown')
        session_quality = opportunity.get('session_quality', 5)
        if session not in ['asian', 'dead'] and session_quality >= 5:
            score += 1

        # 8. Spread acceptable
        spread = opportunity.get('spread', 100)
        atr = opportunity.get('atr', 10)
        spread_ratio = spread / atr if atr > 0 else 1.0
        if spread_ratio < 0.3:  # Spread < 30% of ATR
            score += 1

        # 9. Liquidity sweep present
        has_sweep = opportunity.get('liquidity_sweep', False)
        if has_sweep:
            score += 1

        # 10. Order block valid
        ob_valid = opportunity.get('order_block_valid', True)
        if ob_valid:
            score += 1

        # Cap at 10
        return min(10, score)

    def should_trade(self, opportunity: Dict) -> tuple:
        """
        Determine if opportunity should be traded based on confluence

        Returns:
            (should_trade: bool, score: int, required: int, reason: str)
        """
        score = self.calculate_confluence_score(opportunity)
        preset = self.presets[self.current_level]
        required = preset.confluence_required

        if score >= required:
            return (True, score, required, f"Confluence {score}/{required} - TRADE")
        elif score == required - 1:
            return (False, score, required, f"Confluence {score}/{required} - CLOSE (wait for 1 more)")
        else:
            return (False, score, required, f"Confluence {score}/{required} - SKIP")

    def __str__(self) -> str:
        preset = self.presets[self.current_level]
        return f"Aggressiveness Level {self.current_level}: {preset.name}"


# Global singleton
aggressiveness_manager = AggressivenessManager()
