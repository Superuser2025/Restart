"""
Filter Manager - Controls which opportunities pass institutional filters

ENHANCED with professional-grade logic:
- Dynamic thresholds based on AGGRESSIVENESS LEVEL (1-5)
- Session awareness (avoids Asian chop)
- Quality scoring (min score varies by aggressiveness)
- MTF alignment checking
- Confluence-based filtering (not hard blocks)

AGGRESSIVENESS INTEGRATION:
- Level 1 (Ultra Conservative): Strictest filters, highest confluence required
- Level 5 (Maximum): Loosest filters, minimal confluence required
"""

from core.market_analyzer import market_analyzer
from core.verbose_mode_manager import vprint


class FilterManager:
    """Manages filter state and applies filters to trading opportunities"""

    def __init__(self):
        # Institutional Filters (on/off toggles)
        self.volume_filter = True
        self.spread_filter = False  # User can enable via UI if needed
        self.strong_price_model = True
        self.multi_timeframe = True
        self.volatility_filter = True
        self.sentiment_filter = True
        self.correlation_filter = True
        self.volatility_adaptation = True
        self.dynamic_risk = True
        self.pattern_decay = True

        # Smart Money Concepts
        self.liquidity_sweep = False  # DISABLED by default - let confluence scoring handle
        self.retail_trap_detection = True
        self.order_block_invalidation = False  # DISABLED by default - let confluence scoring handle
        self.market_structure = False  # DISABLED by default - let confluence scoring handle

        # Machine Learning
        self.pattern_tracking = False  # DISABLED - let confluence scoring handle
        self.parameter_adaptation = False  # DISABLED - let confluence scoring handle
        self.regime_strategy = False  # DISABLED - let confluence scoring handle

        # DYNAMIC THRESHOLDS (updated by aggressiveness manager)
        # These are the DEFAULT values - will be overwritten when aggressiveness level changes
        self.min_quality_score = 55  # Default for Level 3 (Balanced)
        self.min_pattern_strength = 5  # Default for Level 3
        self.max_spread_pct_of_atr = 0.50
        self.min_rr_ratio = 1.5  # Default for Level 3
        self.avoid_asian_session = False
        self.require_mtf_alignment = False
        self.min_session_quality = 0

        # CONFLUENCE SYSTEM (new - replaces hard blocks)
        self.confluence_required = 4  # Default for Level 3 - need 4/10 factors
        self.use_confluence_scoring = True  # Enable the new confluence system

        # Initialize from aggressiveness manager
        self._init_from_aggressiveness()

    def _init_from_aggressiveness(self):
        """Initialize thresholds from aggressiveness manager"""
        try:
            from core.aggressiveness_manager import aggressiveness_manager

            # Get initial thresholds
            thresholds = aggressiveness_manager.get_filter_thresholds()
            self._apply_thresholds(thresholds)

            # Register callback for future changes
            aggressiveness_manager.on_level_changed(self._on_aggressiveness_changed)

            level = aggressiveness_manager.get_level()
            name = aggressiveness_manager.get_level_name()
            vprint(f"[FilterManager] Initialized with Aggressiveness Level {level} ({name})")

        except Exception as e:
            vprint(f"[FilterManager] Could not init from aggressiveness manager: {e}")

    def _on_aggressiveness_changed(self, level: int, preset):
        """Callback when aggressiveness level changes"""
        vprint(f"[FilterManager] Aggressiveness changed to Level {level} ({preset.name})")
        thresholds = {
            'min_quality_score': preset.min_quality_score,
            'min_pattern_strength': preset.min_pattern_strength,
            'min_rr_ratio': preset.min_risk_reward,
            'confluence_required': preset.confluence_required,
        }
        self._apply_thresholds(thresholds)

    def _apply_thresholds(self, thresholds: dict):
        """Apply threshold values from aggressiveness manager"""
        if 'min_quality_score' in thresholds:
            self.min_quality_score = thresholds['min_quality_score']
        if 'min_pattern_strength' in thresholds:
            self.min_pattern_strength = thresholds['min_pattern_strength']
        if 'min_rr_ratio' in thresholds:
            self.min_rr_ratio = thresholds['min_rr_ratio']
        if 'confluence_required' in thresholds:
            self.confluence_required = thresholds['confluence_required']

        vprint(f"[FilterManager] Thresholds updated: quality>={self.min_quality_score}, "
               f"pattern>={self.min_pattern_strength}, R:R>={self.min_rr_ratio}, "
               f"confluence>={self.confluence_required}/10")

    def set_filter(self, filter_name: str, enabled: bool):
        """Enable/disable a specific filter"""
        # Normalize filter name to attribute name
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")

        if hasattr(self, attr_name):
            setattr(self, attr_name, enabled)
            vprint(f"[FilterManager] {filter_name} = {enabled}")
            return True
        else:
            vprint(f"[FilterManager] WARNING: Unknown filter '{filter_name}'")
            return False

    def get_filter(self, filter_name: str) -> bool:
        """Get current state of a filter"""
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")
        return getattr(self, attr_name, True)  # Default to True if not found

    def filter_opportunity(self, opportunity: dict) -> bool:
        """
        CONFLUENCE-BASED opportunity filtering with aggressiveness-driven thresholds

        NEW APPROACH (fixes MT5 EA's broken hard-blocking):
        1. Calculate confluence score (0-10) for the opportunity
        2. Compare against required confluence for current aggressiveness level
        3. NO HARD BLOCKS - everything contributes to the score
        4. Aggressiveness 1 = need 6/10 confluence, Aggressiveness 5 = need 2/10

        This means Level 1 (least aggressive) STILL TRADES when high confluence present,
        instead of the MT5 EA bug where it never trades.

        Returns True if opportunity meets confluence threshold for current aggressiveness.
        """
        symbol = opportunity.get('symbol', 'UNKNOWN')
        timeframe = opportunity.get('timeframe', 'UNKNOWN')

        # If using new confluence scoring system
        if self.use_confluence_scoring:
            return self._filter_by_confluence(opportunity, symbol, timeframe)

        # Legacy fallback: use old hard-block system
        return self._filter_legacy(opportunity, symbol, timeframe)

    def _filter_by_confluence(self, opportunity: dict, symbol: str, timeframe: str) -> bool:
        """
        NEW: Filter by confluence score (no hard blocks)

        This is the CORRECT implementation that the MT5 EA should have used.
        """
        try:
            from core.aggressiveness_manager import aggressiveness_manager

            # Calculate confluence score
            score = aggressiveness_manager.calculate_confluence_score(opportunity)
            required = self.confluence_required

            # Quality score still matters as a baseline
            quality_score = opportunity.get('quality_score', 0)
            if quality_score < self.min_quality_score:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Quality {quality_score} < {self.min_quality_score}")
                return False

            # R:R still matters as a baseline
            rr = opportunity.get('risk_reward', 0)
            if rr < self.min_rr_ratio:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: R:R {rr:.2f} < {self.min_rr_ratio}")
                return False

            # CONFLUENCE CHECK - the key decision
            if score >= required:
                vprint(f"[Filter] ✅ {symbol} {timeframe}: Confluence {score}/{required} - PASSED!")
                return True
            elif score == required - 1:
                vprint(f"[Filter] ⏸ {symbol} {timeframe}: Confluence {score}/{required} - CLOSE (need 1 more factor)")
                return False
            else:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Confluence {score}/{required} - SKIP")
                return False

        except Exception as e:
            vprint(f"[Filter] Error in confluence scoring: {e}")
            # Fallback to legacy if confluence scoring fails
            return self._filter_legacy(opportunity, symbol, timeframe)

    def _filter_legacy(self, opportunity: dict, symbol: str, timeframe: str) -> bool:
        """Legacy hard-block filtering (fallback)"""
        # CRITICAL: Quality score check FIRST (most important)
        quality_score = opportunity.get('quality_score', 0)
        if quality_score < self.min_quality_score:
            vprint(f"[Filter] ❌ {symbol} {timeframe}: Quality too low ({quality_score} < {self.min_quality_score})")
            return False

        # SESSION AWARENESS - Avoid Asian session chop
        if self.avoid_asian_session:
            session = opportunity.get('session', market_analyzer.get_current_session())
            if session == 'asian' or session == 'dead':
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Asian/dead session rejected")
                return False

        # VOLUME FILTER
        if self.volume_filter:
            volume = opportunity.get('volume', 0)
            min_volume = 50
            if volume < min_volume:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Volume too low ({volume} < {min_volume})")
                return False

        # SPREAD FILTER
        if self.spread_filter:
            spread = opportunity.get('spread', 0)
            atr = opportunity.get('atr', 10)
            spread_pct = spread / atr if atr > 0 else 1.0
            if spread_pct > self.max_spread_pct_of_atr:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Spread too wide")
                return False

        # PATTERN STRENGTH
        if self.strong_price_model:
            strength = opportunity.get('pattern_strength', 0)
            if strength < self.min_pattern_strength:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Pattern strength too low")
                return False

        # MTF ALIGNMENT
        if self.multi_timeframe and self.require_mtf_alignment:
            mtf_confirmed = opportunity.get('mtf_confirmed', False)
            if not mtf_confirmed:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: MTF not confirmed")
                return False

        # R:R RATIO
        if self.dynamic_risk:
            rr = opportunity.get('risk_reward', 0)
            if rr < self.min_rr_ratio:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: R:R too low ({rr:.2f})")
                return False

        # VOLATILITY FILTER
        if self.volatility_filter:
            atr = opportunity.get('atr', 0)
            if atr <= 0:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Invalid ATR")
                return False

        # SENTIMENT FILTER
        if self.sentiment_filter:
            h4_trend = opportunity.get('h4_trend', 'neutral')
            direction = opportunity.get('direction', 'BUY')
            if direction == 'BUY' and h4_trend == 'bearish':
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Counter-trend BUY")
                return False
            if direction == 'SELL' and h4_trend == 'bullish':
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Counter-trend SELL")
                return False

        # RETAIL TRAP DETECTION
        if self.retail_trap_detection:
            is_trap = opportunity.get('is_retail_trap', False)
            if is_trap:
                vprint(f"[Filter] ❌ {symbol} {timeframe}: Retail trap detected")
                return False

        vprint(f"[Filter] ✅ {symbol} {timeframe}: PASSED all legacy filters!")
        return True

    def get_active_filters(self) -> list:
        """Get list of currently active filter names"""
        active = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                if isinstance(getattr(self, attr_name), bool) and getattr(self, attr_name):
                    # Convert attr name back to display name
                    display_name = attr_name.replace('_', ' ').title()
                    active.append(display_name)
        return active


# Global singleton instance
filter_manager = FilterManager()
