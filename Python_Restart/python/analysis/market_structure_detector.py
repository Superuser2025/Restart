"""
Market Structure Detector - BOS vs CHoCH

Market structure defines the trend through swing highs and lows:
- Uptrend: Series of Higher Highs (HH) and Higher Lows (HL)
- Downtrend: Series of Lower Highs (LH) and Lower Lows (LL)

Two critical events:
1. Break of Structure (BOS): Continuation signal
   - Bullish BOS: Price breaks above previous swing high → uptrend continues
   - Bearish BOS: Price breaks below previous swing low → downtrend continues

2. Change of Character (CHoCH): Reversal signal
   - Bullish CHoCH: During downtrend, price breaks above previous swing high → reversal to uptrend
   - Bearish CHoCH: During uptrend, price breaks below previous swing low → reversal to downtrend

This module detects structure shifts for high-probability trend trading.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd


class MarketStructureDetector:
    """
    Detect market structure shifts (BOS and CHoCH)

    Key Features:
    - Track swing highs and lows
    - Detect HH/HL (uptrend) and LH/LL (downtrend) patterns
    - Identify BOS (continuation) vs CHoCH (reversal)
    - Determine current trend from structure
    """

    def __init__(self):
        self.structure_events = {}  # {symbol: [event1, event2, ...]}
        self.current_trends = {}  # {symbol: 'BULLISH'/'BEARISH'/'NEUTRAL'}

    def detect_structure_shifts(self, candles: List[Dict], symbol: str = "UNKNOWN",
                               lookback: int = 50) -> Tuple[List[Dict], str]:
        """
        Detect market structure shifts from candle data

        Args:
            candles: List of OHLC candles
            symbol: Trading symbol
            lookback: How many candles to analyze

        Returns:
            Tuple of (structure_events, current_trend)
        """
        if not candles or len(candles) < 10:
            return [], 'NEUTRAL'

        # Find swing highs and lows
        swings = self._identify_swing_points(candles, lookback)

        if len(swings) < 3:
            return [], 'NEUTRAL'  # Need at least 3 swings to determine structure

        # Detect initial trend from first swings
        current_trend = self._detect_initial_trend(swings)

        # Analyze structure shifts
        events = []

        for i in range(1, len(swings)):
            prev_swing = swings[i-1]
            current_swing = swings[i]

            # Analyze based on current trend
            if current_trend == 'BULLISH':
                event, trend_change = self._analyze_bullish_structure(
                    prev_swing, current_swing, i, symbol
                )
                if event:
                    events.append(event)
                    if trend_change:
                        current_trend = 'BEARISH'

            elif current_trend == 'BEARISH':
                event, trend_change = self._analyze_bearish_structure(
                    prev_swing, current_swing, i, symbol
                )
                if event:
                    events.append(event)
                    if trend_change:
                        current_trend = 'BULLISH'

            else:  # NEUTRAL
                # Determine trend from swing comparison
                if current_swing['type'] == 'high' and prev_swing['type'] == 'low':
                    if current_swing['price'] > swings[i-2]['price'] if i >= 2 else True:
                        current_trend = 'BULLISH'
                elif current_swing['type'] == 'low' and prev_swing['type'] == 'high':
                    if current_swing['price'] < swings[i-2]['price'] if i >= 2 else True:
                        current_trend = 'BEARISH'

        # Store results
        self.structure_events[symbol] = events
        self.current_trends[symbol] = current_trend

        return events, current_trend

    def _identify_swing_points(self, candles: List[Dict], lookback: int) -> List[Dict]:
        """
        Identify swing highs and swing lows from candle data

        Swing high: Local peak (higher than surrounding candles)
        Swing low: Local trough (lower than surrounding candles)
        """
        if len(candles) < lookback:
            lookback = len(candles)

        recent_candles = candles[-lookback:]
        swings = []

        # Use window of 2 candles on each side for swing detection
        window = 2

        for i in range(window, len(recent_candles) - window):
            candle = recent_candles[i]

            # Check for swing high
            is_swing_high = True
            for j in range(i - window, i + window + 1):
                if j == i:
                    continue
                if recent_candles[j]['high'] >= candle['high']:
                    is_swing_high = False
                    break

            if is_swing_high:
                swings.append({
                    'type': 'high',
                    'price': candle['high'],
                    'timestamp': candle.get('time', datetime.now()),
                    'candle_index': len(candles) - lookback + i
                })
                continue  # Can't be both swing high and low

            # Check for swing low
            is_swing_low = True
            for j in range(i - window, i + window + 1):
                if j == i:
                    continue
                if recent_candles[j]['low'] <= candle['low']:
                    is_swing_low = False
                    break

            if is_swing_low:
                swings.append({
                    'type': 'low',
                    'price': candle['low'],
                    'timestamp': candle.get('time', datetime.now()),
                    'candle_index': len(candles) - lookback + i
                })

        return swings

    def _detect_initial_trend(self, swings: List[Dict]) -> str:
        """
        Detect initial trend from first few swings

        HH + HL = Bullish
        LH + LL = Bearish
        """
        if len(swings) < 3:
            return 'NEUTRAL'

        # Look at first 3 swings to establish trend
        # Pattern: Low -> High -> Low OR High -> Low -> High

        if swings[0]['type'] == 'low' and swings[1]['type'] == 'high' and swings[2]['type'] == 'low':
            # Low -> High -> Low
            if swings[2]['price'] > swings[0]['price']:  # HL (Higher Low)
                return 'BULLISH'
            else:  # LL (Lower Low)
                return 'BEARISH'

        elif swings[0]['type'] == 'high' and swings[1]['type'] == 'low' and swings[2]['type'] == 'high':
            # High -> Low -> High
            if swings[2]['price'] > swings[0]['price']:  # HH (Higher High)
                return 'BULLISH'
            else:  # LH (Lower High)
                return 'BEARISH'

        return 'NEUTRAL'

    def _analyze_bullish_structure(self, prev_swing: Dict, current_swing: Dict,
                                   index: int, symbol: str) -> Tuple[Optional[Dict], bool]:
        """
        Analyze structure in bullish trend

        Returns: (event_dict, trend_changed)

        BOS (Bullish continuation):
        - Current high > Previous high (HH)
        - Current low > Previous low (HL)

        CHoCH (Bearish reversal):
        - Current low < Previous low (LL)
        """
        trend_changed = False

        if current_swing['type'] == 'high':
            # Check if HH (Higher High)
            if current_swing['price'] > prev_swing['price']:
                # Bullish BOS - continuation
                return {
                    'type': 'BOS',
                    'direction': 'bullish',
                    'signal': 'continuation',
                    'price': current_swing['price'],
                    'timestamp': current_swing['timestamp'],
                    'swing_index': index,
                    'description': 'Higher High - Bullish continuation'
                }, False

        elif current_swing['type'] == 'low':
            # Check previous swing (should be a high for proper analysis)
            # Find the previous swing high
            prev_high = None
            for j in range(index - 1, -1, -1):
                if index > j and prev_swing['type'] == 'high':
                    prev_high = prev_swing
                    break

            if prev_high:
                # Check for HL (Higher Low) or LL (Lower Low)
                # Need to compare with the low BEFORE the prev_high
                # For simplicity, check if current low < recent lows
                if current_swing['price'] < prev_swing['price']:
                    # LL - This breaks bullish structure
                    # CHoCH - Change of Character (reversal to bearish)
                    trend_changed = True
                    return {
                        'type': 'CHoCH',
                        'direction': 'bearish',
                        'signal': 'reversal',
                        'price': current_swing['price'],
                        'timestamp': current_swing['timestamp'],
                        'swing_index': index,
                        'description': 'Lower Low - Bearish reversal (CHoCH)'
                    }, True

        return None, False

    def _analyze_bearish_structure(self, prev_swing: Dict, current_swing: Dict,
                                   index: int, symbol: str) -> Tuple[Optional[Dict], bool]:
        """
        Analyze structure in bearish trend

        BOS (Bearish continuation):
        - Current low < Previous low (LL)
        - Current high < Previous high (LH)

        CHoCH (Bullish reversal):
        - Current high > Previous high (HH)
        """
        trend_changed = False

        if current_swing['type'] == 'low':
            # Check if LL (Lower Low)
            if current_swing['price'] < prev_swing['price']:
                # Bearish BOS - continuation
                return {
                    'type': 'BOS',
                    'direction': 'bearish',
                    'signal': 'continuation',
                    'price': current_swing['price'],
                    'timestamp': current_swing['timestamp'],
                    'swing_index': index,
                    'description': 'Lower Low - Bearish continuation'
                }, False

        elif current_swing['type'] == 'high':
            # Check if HH (Higher High) - breaks bearish structure
            if current_swing['price'] > prev_swing['price']:
                # HH - CHoCH (reversal to bullish)
                trend_changed = True
                return {
                    'type': 'CHoCH',
                    'direction': 'bullish',
                    'signal': 'reversal',
                    'price': current_swing['price'],
                    'timestamp': current_swing['timestamp'],
                    'swing_index': index,
                    'description': 'Higher High - Bullish reversal (CHoCH)'
                }, True

        return None, False

    def check_structure_aligned(self, candles: List[Dict], trade_direction: str,
                               symbol: str = "UNKNOWN") -> bool:
        """
        Check if market structure supports the trade direction

        Args:
            candles: Recent candle data
            trade_direction: 'BUY' or 'SELL'
            symbol: Trading symbol

        Returns:
            True if structure aligns with trade direction
        """
        # Detect structure if not already done
        if symbol not in self.current_trends:
            self.detect_structure_shifts(candles, symbol)

        current_trend = self.current_trends.get(symbol, 'NEUTRAL')

        if trade_direction == 'BUY':
            return current_trend == 'BULLISH'
        elif trade_direction == 'SELL':
            return current_trend == 'BEARISH'

        return False

    def get_current_trend(self, symbol: str) -> str:
        """Get current trend for symbol"""
        return self.current_trends.get(symbol, 'NEUTRAL')

    def get_recent_structure_events(self, symbol: str, lookback: int = 5) -> List[Dict]:
        """
        Get recent structure events (BOS/CHoCH)

        Args:
            symbol: Trading symbol
            lookback: Number of recent events to return

        Returns:
            List of recent structure event dictionaries
        """
        all_events = self.structure_events.get(symbol, [])

        # Return most recent events
        return all_events[-lookback:] if len(all_events) > lookback else all_events

    def get_last_structure_event(self, symbol: str) -> Optional[Dict]:
        """Get the most recent structure event"""
        events = self.structure_events.get(symbol, [])
        return events[-1] if events else None


# Global singleton instance
market_structure_detector = MarketStructureDetector()
