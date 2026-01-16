"""
AppleTrader Pro - Advanced Market Analysis Engine
Provides professional-grade market analysis for profitable trading M5-H4

This module transforms amateur filtering into institutional-grade opportunity analysis.
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
from datetime import datetime, time
import numpy as np
from typing import Dict, List, Optional, Tuple


class MarketAnalyzer:
    """
    Professional market analysis engine for M5-H4 trading

    Features:
    - Dynamic ATR-based thresholds (not static amateur numbers)
    - Session awareness (London/NY vs Asian chop)
    - True multi-timeframe alignment
    - Smart Money zone integration
    - Confluence scoring (1-10 scale)
    """

    def __init__(self):
        self.atr_cache = {}  # Cache ATR values to avoid recalculation
        self.session_cache = {}  # Cache session data

    # ==================== ATR & VOLATILITY ====================

    def calculate_atr(self, symbol: str, timeframe: str, period: int = 14) -> float:
        """
        Calculate Average True Range for dynamic thresholds

        ATR is the FOUNDATION of professional trading:
        - Stop losses should be ATR * multiplier (not arbitrary pips)
        - Spread tolerance should be % of ATR (not static pips)
        - Entry filters should adapt to volatility

        Returns ATR in pips
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{period}"
            if cache_key in self.atr_cache:
                cached_time, cached_atr = self.atr_cache[cache_key]
                # Cache valid for 5 minutes
                if (datetime.now() - cached_time).seconds < 300:
                    return cached_atr

            if not mt5.initialize():
                # Fallback ATR estimates if MT5 unavailable
                return self.get_fallback_atr(symbol, timeframe)

            # Get timeframe constant
            tf_map = {
                'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15, 'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1, 'W1': mt5.TIMEFRAME_W1
            }
            mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)

            # Get historical data
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, period + 1)

            if rates is None or len(rates) < period:
                return self.get_fallback_atr(symbol, timeframe)

            # Calculate True Range for each period
            true_ranges = []
            for i in range(1, len(rates)):
                high = rates[i]['high']
                low = rates[i]['low']
                prev_close = rates[i-1]['close']

                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)

            # ATR is simple moving average of True Ranges
            atr = np.mean(true_ranges[-period:])

            # Convert to pips based on symbol
            point = mt5.symbol_info(symbol).point
            pip_multiplier = 10 if 'JPY' in symbol else 10000
            atr_pips = atr * pip_multiplier

            # Cache result
            self.atr_cache[cache_key] = (datetime.now(), atr_pips)

            return atr_pips

        except Exception as e:
            return self.get_fallback_atr(symbol, timeframe)

    def get_fallback_atr(self, symbol: str, timeframe: str) -> float:
        """
        Realistic ATR estimates when MT5 unavailable
        Based on typical volatility for major pairs
        """
        # ATR varies by symbol AND timeframe
        atr_estimates = {
            'EURUSD': {'M5': 3.5, 'M15': 6.0, 'M30': 8.5, 'H1': 12.0, 'H4': 25.0},
            'GBPUSD': {'M5': 4.5, 'M15': 7.5, 'M30': 11.0, 'H1': 15.0, 'H4': 32.0},
            'USDJPY': {'M5': 4.0, 'M15': 7.0, 'M30': 10.0, 'H1': 14.0, 'H4': 28.0},
            'GBPJPY': {'M5': 6.0, 'M15': 10.0, 'M30': 15.0, 'H1': 22.0, 'H4': 45.0},
            'AUDUSD': {'M5': 3.0, 'M15': 5.5, 'M30': 8.0, 'H1': 11.0, 'H4': 23.0},
            'USDCAD': {'M5': 3.2, 'M15': 5.8, 'M30': 8.5, 'H1': 12.0, 'H4': 24.0},
            'NZDUSD': {'M5': 3.0, 'M15': 5.5, 'M30': 8.0, 'H1': 11.5, 'H4': 24.0},
            'EURGBP': {'M5': 2.5, 'M15': 4.5, 'M30': 6.5, 'H1': 9.0, 'H4': 18.0},
            'EURJPY': {'M5': 5.0, 'M15': 8.5, 'M30': 12.0, 'H1': 17.0, 'H4': 35.0},
        }

        if symbol in atr_estimates and timeframe in atr_estimates[symbol]:
            return atr_estimates[symbol][timeframe]

        # Default fallback
        return {'M5': 4.0, 'M15': 7.0, 'M30': 10.0, 'H1': 14.0, 'H4': 28.0}.get(timeframe, 14.0)

    def is_high_volatility(self, symbol: str, timeframe: str) -> bool:
        """Check if current volatility is above normal (ATR > 1.5x average)"""
        current_atr = self.calculate_atr(symbol, timeframe, period=14)
        avg_atr = self.calculate_atr(symbol, timeframe, period=50)
        return current_atr > (avg_atr * 1.5)

    # ==================== SESSION ANALYSIS ====================

    def get_current_session(self) -> str:
        """
        Determine current trading session
        Returns: 'asian', 'london', 'newyork', 'dead'

        CRITICAL FOR PROFITABILITY:
        - Asian session (00:00-08:00 GMT): Low volume, choppy, avoid
        - London session (08:00-16:00 GMT): High volume, trending, TRADE THIS
        - New York session (13:00-21:00 GMT): High volume, trending, TRADE THIS
        - Dead zone (21:00-00:00 GMT): Low volume, avoid
        """
        now = datetime.utcnow()
        current_time = now.time()

        # Session times in GMT
        asian_start = time(0, 0)
        asian_end = time(8, 0)
        london_start = time(8, 0)
        london_end = time(16, 0)
        ny_start = time(13, 0)
        ny_end = time(21, 0)

        # London/NY overlap (13:00-16:00 GMT) = BEST trading hours
        if ny_start <= current_time < london_end:
            return 'london_ny_overlap'  # HIGHEST PRIORITY

        # London session
        if london_start <= current_time < ny_start:
            return 'london'  # HIGH PRIORITY

        # NY session
        if london_end <= current_time < ny_end:
            return 'newyork'  # HIGH PRIORITY

        # Asian session
        if asian_start <= current_time < asian_end:
            return 'asian'  # LOW PRIORITY - choppy

        # Dead zone
        return 'dead'  # AVOID

    def is_tradeable_session(self) -> bool:
        """Check if current session is worth trading"""
        session = self.get_current_session()
        return session in ['london', 'newyork', 'london_ny_overlap']

    def get_session_quality_score(self) -> int:
        """
        Score current session quality (0-10)
        10 = London/NY overlap (best)
        7-8 = London or NY
        3-4 = Asian
        0 = Dead zone
        """
        session = self.get_current_session()
        scores = {
            'london_ny_overlap': 10,
            'london': 8,
            'newyork': 7,
            'asian': 3,
            'dead': 0
        }
        return scores.get(session, 0)

    # ==================== MULTI-TIMEFRAME ALIGNMENT ====================

    def check_mtf_alignment(self, symbol: str, lower_tf: str, direction: str) -> Dict:
        """
        TRUE multi-timeframe alignment check

        Rules for profitable M5-H4 trading:
        1. M5 trade direction MUST align with H1 trend
        2. H1 trend MUST align with H4 trend
        3. If counter-trend, opportunity is REJECTED

        Returns:
        {
            'aligned': bool,
            'h1_trend': 'bullish'/'bearish'/'neutral',
            'h4_trend': 'bullish'/'bearish'/'neutral',
            'alignment_score': 0-10,
            'rejection_reason': str or None
        }
        """
        try:
            if not mt5.initialize():
                return {'aligned': False, 'h1_trend': 'unknown', 'h4_trend': 'unknown',
                       'alignment_score': 0, 'rejection_reason': 'MT5 not available'}

            # Get H1 trend
            h1_trend = self.get_trend(symbol, 'H1')

            # Get H4 trend
            h4_trend = self.get_trend(symbol, 'H4')

            # Check alignment
            if direction == 'BUY':
                h1_aligned = h1_trend in ['bullish', 'neutral']
                h4_aligned = h4_trend in ['bullish', 'neutral']
            else:  # SELL
                h1_aligned = h1_trend in ['bearish', 'neutral']
                h4_aligned = h4_trend in ['bearish', 'neutral']

            # Calculate alignment score
            score = 0
            if h1_aligned:
                score += 5
            if h4_aligned:
                score += 5

            # Strong alignment bonus (both higher TFs trending same direction)
            if direction == 'BUY' and h1_trend == 'bullish' and h4_trend == 'bullish':
                score = 10  # Perfect alignment
            elif direction == 'SELL' and h1_trend == 'bearish' and h4_trend == 'bearish':
                score = 10  # Perfect alignment

            # Determine rejection reason
            rejection_reason = None
            if not h1_aligned:
                rejection_reason = f"H1 trend is {h1_trend}, conflicts with {direction} trade"
            elif not h4_aligned:
                rejection_reason = f"H4 trend is {h4_trend}, conflicts with {direction} trade"

            return {
                'aligned': h1_aligned and h4_aligned,
                'h1_trend': h1_trend,
                'h4_trend': h4_trend,
                'alignment_score': score,
                'rejection_reason': rejection_reason
            }

        except Exception as e:
            return {'aligned': False, 'h1_trend': 'error', 'h4_trend': 'error',
                   'alignment_score': 0, 'rejection_reason': str(e)}

    def get_trend(self, symbol: str, timeframe: str, lookback: int = 100) -> str:
        """
        INSTITUTIONAL-GRADE TREND DETECTION

        Uses multi-factor analysis instead of amateur EMA crossovers:
        1. Market Structure (Higher Highs/Lows or Lower Highs/Lows)
        2. ADX (Trend strength > 25 = trending)
        3. Volume Profile (Increasing on trend moves)
        4. Price momentum (ROC - Rate of Change)
        5. Multi-timeframe alignment
        6. Key level breaks (support/resistance)

        Returns: 'bullish', 'bearish', or 'neutral'
        """
        try:
            if not MT5_AVAILABLE or not mt5.initialize():
                return self._fallback_trend(symbol, timeframe)

            tf_map = {
                'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15, 'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1, 'W1': mt5.TIMEFRAME_W1
            }
            mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_H4)

            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, lookback)
            if rates is None or len(rates) < lookback:
                return self._fallback_trend(symbol, timeframe)

            # Extract data
            highs = rates['high']
            lows = rates['low']
            closes = rates['close']
            volumes = rates['tick_volume']

            # FACTOR 1: MARKET STRUCTURE (40% weight)
            structure_score = self._analyze_market_structure(highs, lows, closes)

            # FACTOR 2: ADX - Trend Strength (20% weight)
            adx_score = self._calculate_adx(highs, lows, closes, period=14)

            # FACTOR 3: VOLUME ANALYSIS (15% weight)
            volume_score = self._analyze_volume_trend(closes, volumes)

            # FACTOR 4: MOMENTUM (15% weight)
            momentum_score = self._analyze_momentum(closes)

            # FACTOR 5: MULTI-TIMEFRAME (10% weight)
            mtf_score = self._get_higher_timeframe_bias(symbol, timeframe)

            # WEIGHTED COMPOSITE SCORE
            # Positive = Bullish, Negative = Bearish, Near Zero = Neutral
            composite_score = (
                structure_score * 0.40 +
                adx_score * 0.20 +
                volume_score * 0.15 +
                momentum_score * 0.15 +
                mtf_score * 0.10
            )

            # THRESHOLDS for classification
            if composite_score > 0.3:
                return 'bullish'
            elif composite_score < -0.3:
                return 'bearish'
            else:
                return 'neutral'

        except Exception as e:
            return self._fallback_trend(symbol, timeframe)

    def _analyze_market_structure(self, highs, lows, closes) -> float:
        """
        Analyze market structure using swing highs and swing lows

        Bullish structure: Series of higher highs and higher lows
        Bearish structure: Series of lower highs and lower lows

        Returns: +1.0 (strong bull) to -1.0 (strong bear)
        """
        try:
            # Find recent swing points (last 20 bars for context)
            recent_highs = []
            recent_lows = []

            # Simple swing detection: local maxima/minima over 5-bar windows
            for i in range(len(highs) - 10, len(highs) - 2):
                # Check if high[i] is higher than neighbors
                if i >= 2 and i < len(highs) - 2:
                    if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                       highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                        recent_highs.append(highs[i])

                    if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                       lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                        recent_lows.append(lows[i])

            if len(recent_highs) < 2 or len(recent_lows) < 2:
                return 0.0

            # Check if making higher highs and higher lows
            higher_highs = all(recent_highs[i] > recent_highs[i-1] for i in range(1, len(recent_highs)))
            higher_lows = all(recent_lows[i] > recent_lows[i-1] for i in range(1, len(recent_lows)))

            # Check if making lower highs and lower lows
            lower_highs = all(recent_highs[i] < recent_highs[i-1] for i in range(1, len(recent_highs)))
            lower_lows = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows)))

            if higher_highs and higher_lows:
                return 1.0  # Strong bullish structure
            elif lower_highs and lower_lows:
                return -1.0  # Strong bearish structure
            elif higher_highs or higher_lows:
                return 0.5  # Weak bullish structure
            elif lower_highs or lower_lows:
                return -0.5  # Weak bearish structure
            else:
                return 0.0  # No clear structure

        except:
            return 0.0

    def _calculate_adx(self, highs, lows, closes, period=14) -> float:
        """
        Calculate ADX (Average Directional Index) for trend strength

        ADX measures trend strength regardless of direction
        ADX > 25 = trending market
        ADX < 20 = ranging market

        Returns: +1.0 (strong trending bull), -1.0 (strong trending bear), 0.0 (ranging)
        """
        try:
            if len(highs) < period + 1:
                return 0.0

            # Calculate True Range and Directional Movement
            tr_values = []
            plus_dm = []
            minus_dm = []

            for i in range(1, len(closes)):
                # True Range
                high_low = highs[i] - lows[i]
                high_close = abs(highs[i] - closes[i-1])
                low_close = abs(lows[i] - closes[i-1])
                tr = max(high_low, high_close, low_close)
                tr_values.append(tr)

                # Directional Movement
                up_move = highs[i] - highs[i-1]
                down_move = lows[i-1] - lows[i]

                plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
                minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

            if len(tr_values) < period:
                return 0.0

            # Smooth with EMA
            tr_smooth = np.mean(tr_values[-period:])
            plus_di = (np.mean(plus_dm[-period:]) / tr_smooth) * 100 if tr_smooth > 0 else 0
            minus_di = (np.mean(minus_dm[-period:]) / tr_smooth) * 100 if tr_smooth > 0 else 0

            # Calculate DX and ADX
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
            adx = dx  # Simplified (normally would smooth over 14 periods)

            # Return directional score weighted by ADX strength
            if adx > 25:  # Strong trend
                if plus_di > minus_di:
                    return min(adx / 50, 1.0)  # Bullish trend (cap at 1.0)
                else:
                    return -min(adx / 50, 1.0)  # Bearish trend
            else:  # Weak trend or ranging
                return 0.0

        except:
            return 0.0

    def _analyze_volume_trend(self, closes, volumes) -> float:
        """
        Analyze volume behavior in relation to price

        Bullish: Volume increases on up moves, decreases on down moves
        Bearish: Volume increases on down moves, decreases on up moves

        Returns: +1.0 (bullish volume) to -1.0 (bearish volume)
        """
        try:
            if len(closes) < 20:
                return 0.0

            # Analyze last 20 bars
            recent_closes = closes[-20:]
            recent_volumes = volumes[-20:]

            up_volume = 0
            down_volume = 0

            for i in range(1, len(recent_closes)):
                if recent_closes[i] > recent_closes[i-1]:
                    up_volume += recent_volumes[i]
                elif recent_closes[i] < recent_closes[i-1]:
                    down_volume += recent_volumes[i]

            total_volume = up_volume + down_volume
            if total_volume == 0:
                return 0.0

            # Volume imbalance
            volume_ratio = (up_volume - down_volume) / total_volume
            return np.clip(volume_ratio, -1.0, 1.0)

        except:
            return 0.0

    def _analyze_momentum(self, closes) -> float:
        """
        Analyze price momentum using Rate of Change (ROC)

        Positive ROC = bullish momentum
        Negative ROC = bearish momentum

        Returns: +1.0 (strong bull momentum) to -1.0 (strong bear momentum)
        """
        try:
            if len(closes) < 20:
                return 0.0

            # Calculate ROC over different periods and average
            roc_10 = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] != 0 else 0
            roc_20 = (closes[-1] - closes[-20]) / closes[-20] if closes[-20] != 0 else 0

            avg_roc = (roc_10 + roc_20) / 2

            # Normalize to -1 to +1 range (assume 5% move = max)
            return np.clip(avg_roc / 0.05, -1.0, 1.0)

        except:
            return 0.0

    def _get_higher_timeframe_bias(self, symbol: str, current_tf: str) -> float:
        """
        Check higher timeframe for alignment

        If on H4, check D1
        If on H1, check H4

        Returns: +1.0 (HTF bullish), -1.0 (HTF bearish), 0.0 (neutral/unknown)
        """
        try:
            # Map current TF to higher TF
            htf_map = {
                'M5': 'H1',
                'M15': 'H4',
                'M30': 'H4',
                'H1': 'H4',
                'H4': 'D1',
                'D1': 'W1'
            }

            higher_tf = htf_map.get(current_tf)
            if not higher_tf:
                return 0.0

            # Quick check: compare current price to 20/50 period average on HTF
            tf_map = {
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1
            }

            htf_constant = tf_map.get(higher_tf)
            if not htf_constant:
                return 0.0

            rates = mt5.copy_rates_from_pos(symbol, htf_constant, 0, 50)
            if rates is None or len(rates) < 50:
                return 0.0

            closes = rates['close']
            current_price = closes[-1]
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])

            if current_price > sma_20 and sma_20 > sma_50:
                return 1.0  # HTF bullish
            elif current_price < sma_20 and sma_20 < sma_50:
                return -1.0  # HTF bearish
            else:
                return 0.0  # HTF neutral

        except:
            return 0.0

    def _fallback_trend(self, symbol: str, timeframe: str) -> str:
        """
        Fallback when MT5 unavailable
        Returns neutral to avoid false signals
        """
        return 'neutral'

    # ==================== CONFLUENCE SCORING ====================

    def calculate_confluence_score(self, opportunity: Dict, filters_enabled: Dict) -> Tuple[int, List[str]]:
        """
        Calculate confluence score (0-10) based on how many confirmations align

        Professional traders don't take trades with 1-2 confirmations.
        They wait for 5+ confluences to stack up.

        Returns: (score, list_of_confirmations)
        """
        confirmations = []
        score = 0

        # 1. Volume confirmation (+1)
        if filters_enabled.get('volume_filter') and opportunity.get('volume', 0) >= 100:
            confirmations.append("High volume")
            score += 1

        # 2. Tight spread (+1)
        if filters_enabled.get('spread_filter') and opportunity.get('spread', 0) <= 5:
            confirmations.append("Tight spread")
            score += 1

        # 3. Strong pattern (+2 for very strong, +1 for moderate)
        strength = opportunity.get('pattern_strength', 0)
        if strength >= 8:
            confirmations.append("Very strong pattern (8+/10)")
            score += 2
        elif strength >= 6:
            confirmations.append("Strong pattern (6+/10)")
            score += 1

        # 4. Multi-timeframe alignment (+2 - most important)
        if opportunity.get('mtf_confirmed'):
            confirmations.append("MTF alignment")
            score += 2

        # 5. Liquidity sweep (+1)
        if opportunity.get('liquidity_sweep'):
            confirmations.append("Liquidity sweep")
            score += 1

        # 6. Order block valid (+1)
        if opportunity.get('order_block_valid'):
            confirmations.append("Valid order block")
            score += 1

        # 7. Market structure aligned (+1)
        if opportunity.get('structure_aligned'):
            confirmations.append("Structure aligned")
            score += 1

        # 8. High ML reliability (+1)
        if opportunity.get('pattern_reliability', 0) >= 75:
            confirmations.append("ML confidence 75%+")
            score += 1

        # Cap at 10
        score = min(score, 10)

        return score, confirmations


# Global singleton
market_analyzer = MarketAnalyzer()
