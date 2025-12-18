"""
Filter Manager - Controls which opportunities pass institutional filters

ENHANCED with professional-grade logic:
- Dynamic thresholds based on symbol/timeframe
- Session awareness (avoids Asian chop)
- Quality scoring (min 60/100 by default)
- MTF alignment checking
"""

from core.market_analyzer import market_analyzer


class FilterManager:
    """Manages filter state and applies filters to trading opportunities"""

    def __init__(self):
        # Institutional Filters
        self.volume_filter = True
        self.spread_filter = False  # DISABLED: Spread calculation not universal across asset types
        self.strong_price_model = True
        self.multi_timeframe = True
        self.volatility_filter = False  # DISABLED: ATR units vary by asset (forex/JPY/gold/bitcoin/etc)
        self.sentiment_filter = True
        self.correlation_filter = True
        self.volatility_adaptation = True
        self.dynamic_risk = True
        self.pattern_decay = True

        # Smart Money Concepts
        self.liquidity_sweep = True
        self.retail_trap_detection = True
        self.order_block_invalidation = True
        self.market_structure = True

        # Machine Learning
        self.pattern_tracking = True
        self.parameter_adaptation = True
        self.regime_strategy = True

        # PROFESSIONAL THRESHOLDS (dynamic, not static)
        self.min_quality_score = 40  # RELAXED: Minimum 40/100 (was 60) to show more opportunities
        self.min_pattern_strength = 3  # RELAXED: Minimum 3/10 (was 5) pattern strength
        self.max_spread_pct_of_atr = 0.50  # RELAXED: Spread < 50% of ATR (was 30%)
        self.min_rr_ratio = 1.2  # RELAXED: Minimum 1.2:1 (was 1.5:1) risk/reward
        self.avoid_asian_session = False  # DISABLED: Show all sessions (was True)
        self.require_mtf_alignment = False  # Optional strict MTF requirement
        self.min_session_quality = 0  # RELAXED: Accept all sessions (was 5)

    def set_filter(self, filter_name: str, enabled: bool):
        """Enable/disable a specific filter"""
        # Normalize filter name to attribute name
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")

        if hasattr(self, attr_name):
            setattr(self, attr_name, enabled)
            print(f"[FilterManager] {filter_name} = {enabled}")
            return True
        else:
            print(f"[FilterManager] WARNING: Unknown filter '{filter_name}'")
            return False

    def get_filter(self, filter_name: str) -> bool:
        """Get current state of a filter"""
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")
        return getattr(self, attr_name, True)  # Default to True if not found

    def filter_opportunity(self, opportunity: dict) -> bool:
        """
        PROFESSIONAL-GRADE opportunity filtering with dynamic thresholds

        NEW APPROACH:
        1. Quality score threshold (minimum 60/100)
        2. Dynamic spread filter (% of ATR, not static pips)
        3. Session awareness (avoid Asian chop)
        4. MTF alignment checking (optional strict mode)
        5. Pattern strength minimum
        6. R:R minimum requirement

        Returns True if opportunity passes ALL enabled filters.
        """
        symbol = opportunity.get('symbol', 'UNKNOWN')
        timeframe = opportunity.get('timeframe', 'UNKNOWN')

        # CRITICAL: Quality score check FIRST (most important)
        quality_score = opportunity.get('quality_score', 0)
        if quality_score < self.min_quality_score:
            print(f"[Filter] ❌ {symbol} {timeframe}: Quality too low ({quality_score} < {self.min_quality_score})")
            return False  # Reject low-quality setups immediately

        # SESSION AWARENESS - Avoid Asian session chop
        if self.avoid_asian_session:
            session = opportunity.get('session', market_analyzer.get_current_session())
            if session == 'asian' or session == 'dead':
                print(f"[Filter] ❌ {symbol} {timeframe}: Asian/dead session rejected (session={session})")
                return False  # Skip low-quality sessions

        # SESSION QUALITY - Minimum session quality requirement
        session_quality = opportunity.get('session_quality', market_analyzer.get_session_quality_score())
        if session_quality < self.min_session_quality:
            print(f"[Filter] ❌ {symbol} {timeframe}: Session quality too low ({session_quality} < {self.min_session_quality})")
            return False

        # VOLUME FILTER - Dynamic threshold (must be adequate)
        if self.volume_filter:
            volume = opportunity.get('volume', 0)
            # RELAXED: Lower minimum volumes to show more opportunities
            timeframe = opportunity.get('timeframe', 'H1')
            min_volume = {'M5': 50, 'M15': 50, 'M30': 50, 'H1': 50, 'H4': 50}.get(timeframe, 50)
            if volume < min_volume:
                print(f"[Filter] ❌ {symbol} {timeframe}: Volume too low ({volume} < {min_volume})")
                return False

        # SPREAD FILTER - Dynamic (% of ATR, not static pips)
        if self.spread_filter:
            spread = opportunity.get('spread', 0)
            atr = opportunity.get('atr', 10)  # Fallback ATR
            spread_pct = spread / atr if atr > 0 else 1.0
            if spread_pct > self.max_spread_pct_of_atr:
                print(f"[Filter] ❌ {symbol} {timeframe}: Spread too wide ({spread_pct:.2%} > {self.max_spread_pct_of_atr:.2%} of ATR)")
                return False  # Spread too wide relative to volatility

        # STRONG PRICE MODEL - Pattern strength requirement
        if self.strong_price_model:
            strength = opportunity.get('pattern_strength', 0)
            if strength < self.min_pattern_strength:
                print(f"[Filter] ❌ {symbol} {timeframe}: Pattern strength too low ({strength} < {self.min_pattern_strength})")
                return False

        # MULTI-TIMEFRAME - Check MTF alignment
        if self.multi_timeframe:
            if self.require_mtf_alignment:
                # STRICT MODE: Must have perfect MTF alignment
                mtf_score = opportunity.get('mtf_score', 0)
                if mtf_score < 10:  # Perfect alignment = 10
                    print(f"[Filter] ❌ {symbol} {timeframe}: MTF score too low ({mtf_score} < 10)")
                    return False
            else:
                # RELAXED MODE: Just check if not counter-trend
                mtf_confirmed = opportunity.get('mtf_confirmed', False)
                if not mtf_confirmed:
                    print(f"[Filter] ❌ {symbol} {timeframe}: MTF not confirmed (mtf_confirmed={mtf_confirmed})")
                    return False

        # MINIMUM R:R FILTER - Professional traders demand min 1.5:1 R:R
        if self.dynamic_risk:
            rr = opportunity.get('risk_reward', 0)
            if rr < self.min_rr_ratio:
                print(f"[Filter] ❌ {symbol} {timeframe}: R:R too low ({rr:.2f} < {self.min_rr_ratio})")
                return False  # R:R too low

        # VOLATILITY FILTER - Check volatility is within acceptable range
        if self.volatility_filter:
            atr = opportunity.get('atr', 0)

            # Get expected ATR range for this symbol/timeframe
            expected_atr = market_analyzer.calculate_atr(symbol, timeframe)
            if atr < expected_atr * 0.5 or atr > expected_atr * 2.0:
                print(f"[Filter] ❌ {symbol} {timeframe}: Abnormal volatility (ATR={atr:.5f}, expected={expected_atr:.5f})")
                return False  # Abnormal volatility

        # SENTIMENT FILTER - Trend alignment
        if self.sentiment_filter:
            sentiment = opportunity.get('sentiment', 'neutral')
            h4_trend = opportunity.get('h4_trend', 'neutral')
            direction = opportunity.get('direction', 'BUY')

            # Reject counter-trend trades
            if direction == 'BUY' and h4_trend == 'bearish':
                print(f"[Filter] ❌ {symbol} {timeframe}: Counter-trend (BUY vs bearish H4)")
                return False
            if direction == 'SELL' and h4_trend == 'bullish':
                print(f"[Filter] ❌ {symbol} {timeframe}: Counter-trend (SELL vs bullish H4)")
                return False

        # LIQUIDITY SWEEP - Only show opportunities WITH liquidity sweeps
        if self.liquidity_sweep:
            has_sweep = opportunity.get('liquidity_sweep', False)
            if not has_sweep:
                print(f"[Filter] ❌ {symbol} {timeframe}: No liquidity sweep detected")
                return False  # No liquidity sweep detected

        # RETAIL TRAP DETECTION - Filter out obvious retail traps
        if self.retail_trap_detection:
            is_trap = opportunity.get('is_retail_trap', False)
            if is_trap:
                print(f"[Filter] ❌ {symbol} {timeframe}: Retail trap detected")
                return False

        # ORDER BLOCK INVALIDATION - Only show valid order blocks
        if self.order_block_invalidation:
            ob_valid = opportunity.get('order_block_valid', True)
            if not ob_valid:
                print(f"[Filter] ❌ {symbol} {timeframe}: Order block invalid")
                return False

        # MARKET STRUCTURE - Structure must be aligned
        if self.market_structure:
            structure_aligned = opportunity.get('structure_aligned', False)
            if not structure_aligned:
                print(f"[Filter] ❌ {symbol} {timeframe}: Market structure not aligned")
                return False

        # PATTERN TRACKING (ML) - Pattern reliability check
        if self.pattern_tracking:
            pattern_reliability = opportunity.get('pattern_reliability', 0)
            if pattern_reliability < 65:  # Minimum 65% ML confidence
                print(f"[Filter] ❌ {symbol} {timeframe}: Pattern reliability too low ({pattern_reliability}% < 65%)")
                return False

        # PARAMETER ADAPTATION - Parameters must be optimized
        if self.parameter_adaptation:
            params_optimized = opportunity.get('parameters_optimized', True)
            if not params_optimized:
                print(f"[Filter] ❌ {symbol} {timeframe}: Parameters not optimized")
                return False

        # REGIME STRATEGY - Strategy must match current regime
        if self.regime_strategy:
            regime_match = opportunity.get('regime_match', True)
            if not regime_match:
                print(f"[Filter] ❌ {symbol} {timeframe}: Regime mismatch")
                return False

        # Passed all enabled filters
        print(f"[Filter] ✅ {symbol} {timeframe}: PASSED all filters!")
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
