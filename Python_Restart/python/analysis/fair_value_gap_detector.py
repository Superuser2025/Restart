"""
Fair Value Gap (FVG) Detector - Price Imbalances

A Fair Value Gap is a 3-candle pattern showing inefficient price delivery:
- Price moved so fast that it left a "gap" between candles
- Middle candle doesn't overlap with outer two candles
- These gaps act as magnets - price tends to return to fill them

Theory:
- Bullish FVG: Gap down (candle[i-2].low > candle[i].high)
  - Price dropped fast, leaving buyers above
  - Expect price to return UP to fill gap
  - Entry zone for long positions

- Bearish FVG: Gap up (candle[i-2].high < candle[i].low)
  - Price rose fast, leaving sellers below
  - Expect price to return DOWN to fill gap
  - Entry zone for short positions

This module detects and tracks FVGs for high-probability entry zones.
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class FairValueGapDetector:
    """
    Detect and track Fair Value Gaps (price imbalances)

    Key Features:
    - Detect bullish/bearish FVGs
    - Track fill status (unfilled, partial, complete)
    - Calculate fill probability
    - Validate FVG proximity for entries
    """

    def __init__(self):
        self.detected_fvgs = {}  # {symbol: [FVG1, FVG2, ...]}

    def detect_fair_value_gaps(self, candles: List[Dict], symbol: str = "UNKNOWN",
                               lookback: int = 50, min_gap_pips: float = 5) -> List[Dict]:
        """
        Detect fair value gaps from candle data

        Args:
            candles: List of OHLC candles
            symbol: Trading symbol
            lookback: How many candles to analyze
            min_gap_pips: Minimum gap size in pips to qualify (default 5)

        Returns:
            List of FVG dictionaries
        """
        if not candles or len(candles) < 10:
            return []

        fvgs = []

        # Determine pip value
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        min_gap_price = min_gap_pips * pip_value

        # Start from position 2 (need prev_prev, prev, current)
        start_idx = max(2, len(candles) - lookback)

        for i in range(start_idx, len(candles)):
            # Get 3-candle pattern
            prev_prev = candles[i-2]
            prev = candles[i-1]
            current = candles[i]

            # Check for bullish FVG (gap down)
            bullish_fvg = self._detect_bullish_fvg(
                prev_prev, prev, current, i, min_gap_price, symbol
            )
            if bullish_fvg:
                fvgs.append(bullish_fvg)

            # Check for bearish FVG (gap up)
            bearish_fvg = self._detect_bearish_fvg(
                prev_prev, prev, current, i, min_gap_price, symbol
            )
            if bearish_fvg:
                fvgs.append(bearish_fvg)

        # Update fill status for all FVGs
        if fvgs:
            self._update_fill_status(fvgs, candles)

        # Store for this symbol
        self.detected_fvgs[symbol] = fvgs

        return fvgs

    def _detect_bullish_fvg(self, prev_prev: Dict, prev: Dict, current: Dict,
                           index: int, min_gap: float, symbol: str) -> Optional[Dict]:
        """
        Detect bullish FVG (gap down)

        Pattern: prev_prev.low > current.high
        (Middle candle doesn't touch outer two)
        """
        # Check if there's a gap
        if prev_prev['low'] <= current['high']:
            return None  # No gap

        # Calculate gap size
        gap_size = prev_prev['low'] - current['high']

        if gap_size < min_gap:
            return None  # Gap too small

        # Calculate gap in pips
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        gap_pips = gap_size / pip_value

        return {
            'type': 'bullish',
            'direction': 'long',  # Expect price to fill gap by moving UP
            'top': prev_prev['low'],  # Gap top
            'bottom': current['high'],  # Gap bottom
            'mid': (prev_prev['low'] + current['high']) / 2,
            'size': gap_size,
            'size_pips': gap_pips,
            'timestamp': current.get('time', datetime.now()),
            'candle_index': index,
            'filled': False,
            'fill_percentage': 0.0,
            'strength': self._calculate_fvg_strength(gap_pips, prev_prev, prev, current)
        }

    def _detect_bearish_fvg(self, prev_prev: Dict, prev: Dict, current: Dict,
                           index: int, min_gap: float, symbol: str) -> Optional[Dict]:
        """
        Detect bearish FVG (gap up)

        Pattern: prev_prev.high < current.low
        """
        # Check if there's a gap
        if prev_prev['high'] >= current['low']:
            return None  # No gap

        # Calculate gap size
        gap_size = current['low'] - prev_prev['high']

        if gap_size < min_gap:
            return None

        # Calculate gap in pips
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        gap_pips = gap_size / pip_value

        return {
            'type': 'bearish',
            'direction': 'short',  # Expect price to fill gap by moving DOWN
            'top': current['low'],  # Gap top
            'bottom': prev_prev['high'],  # Gap bottom
            'mid': (current['low'] + prev_prev['high']) / 2,
            'size': gap_size,
            'size_pips': gap_pips,
            'timestamp': current.get('time', datetime.now()),
            'candle_index': index,
            'filled': False,
            'fill_percentage': 0.0,
            'strength': self._calculate_fvg_strength(gap_pips, prev_prev, prev, current)
        }

    def _calculate_fvg_strength(self, gap_pips: float, prev_prev: Dict,
                               prev: Dict, current: Dict) -> int:
        """
        Calculate FVG strength (0-100)

        Factors:
        - Gap size (larger = stronger magnet effect)
        - Middle candle momentum (larger middle candle = stronger)
        - Outer candle sizes (balanced = stronger)
        """
        strength = 50  # Base strength

        # Factor 1: Gap size (0-30 points)
        # 5 pips = base, 15+ pips = maximum
        if gap_pips >= 15:
            strength += 30
        elif gap_pips >= 10:
            strength += 20
        elif gap_pips >= 7:
            strength += 10

        # Factor 2: Middle candle momentum (0-20 points)
        middle_range = prev['high'] - prev['low']
        middle_body = abs(prev['close'] - prev['open'])

        if middle_range > 0:
            body_ratio = middle_body / middle_range
            if body_ratio > 0.7:  # Strong momentum candle
                strength += 20
            elif body_ratio > 0.5:
                strength += 10

        # Factor 3: Outer candles balance (0-10 points)
        prev_prev_range = prev_prev['high'] - prev_prev['low']
        current_range = current['high'] - current['low']

        if prev_prev_range > 0 and current_range > 0:
            balance_ratio = min(prev_prev_range, current_range) / max(prev_prev_range, current_range)
            if balance_ratio > 0.7:  # Well balanced
                strength += 10

        return min(100, strength)

    def _update_fill_status(self, fvgs: List[Dict], candles: List[Dict]):
        """
        Update fill status for all FVGs

        Fill detection:
        - Unfilled: Price hasn't entered gap (0%)
        - Partial: Price entered gap but didn't fill completely (1-99%)
        - Complete: Price moved through entire gap (100%)
        """
        if not candles:
            return

        # Check recent candles (after FVG formation) for fill
        for fvg in fvgs:
            if fvg['filled']:
                continue  # Already 100% filled

            # Check all candles after FVG formation
            fvg_candle_idx = fvg['candle_index']

            for i in range(fvg_candle_idx + 1, len(candles)):
                candle = candles[i]

                # Check if this candle entered the FVG zone
                if fvg['type'] == 'bullish':
                    # Bullish FVG: Check if price moved UP into gap
                    if candle['high'] >= fvg['bottom']:
                        # Calculate fill percentage
                        if candle['high'] >= fvg['top']:
                            # Complete fill
                            fvg['fill_percentage'] = 100.0
                            fvg['filled'] = True
                        else:
                            # Partial fill
                            fill_amount = candle['high'] - fvg['bottom']
                            total_gap = fvg['top'] - fvg['bottom']
                            fvg['fill_percentage'] = (fill_amount / total_gap) * 100 if total_gap > 0 else 0

                elif fvg['type'] == 'bearish':
                    # Bearish FVG: Check if price moved DOWN into gap
                    if candle['low'] <= fvg['top']:
                        # Calculate fill percentage
                        if candle['low'] <= fvg['bottom']:
                            # Complete fill
                            fvg['fill_percentage'] = 100.0
                            fvg['filled'] = True
                        else:
                            # Partial fill
                            fill_amount = fvg['top'] - candle['low']
                            total_gap = fvg['top'] - fvg['bottom']
                            fvg['fill_percentage'] = (fill_amount / total_gap) * 100 if total_gap > 0 else 0

    def get_unfilled_fvgs(self, symbol: str) -> List[Dict]:
        """
        Get all unfilled FVGs for a symbol

        Returns:
            List of unfilled FVG dictionaries
        """
        all_fvgs = self.detected_fvgs.get(symbol, [])

        # Filter for unfilled (fill_percentage < 100%)
        unfilled = [fvg for fvg in all_fvgs if not fvg['filled']]

        # Sort by strength (strongest first)
        unfilled.sort(key=lambda x: x['strength'], reverse=True)

        return unfilled

    def is_price_in_fvg(self, candles: List[Dict], current_price: float,
                       symbol: str = "UNKNOWN") -> bool:
        """
        Check if current price is within an unfilled FVG

        Args:
            candles: Recent candle data
            current_price: Current market price
            symbol: Trading symbol

        Returns:
            True if price is in an unfilled FVG zone
        """
        # Ensure FVGs are detected
        if symbol not in self.detected_fvgs:
            self.detect_fair_value_gaps(candles, symbol)

        unfilled = self.get_unfilled_fvgs(symbol)

        if not unfilled:
            return False

        # Check if current_price is within any unfilled FVG
        for fvg in unfilled:
            if fvg['bottom'] <= current_price <= fvg['top']:
                return True  # Price is in FVG zone!

        return False

    def get_nearest_fvg(self, candles: List[Dict], current_price: float,
                       symbol: str = "UNKNOWN", direction: str = None) -> Optional[Dict]:
        """
        Find the nearest unfilled FVG to current price

        Args:
            candles: Recent candle data
            current_price: Current market price
            symbol: Trading symbol
            direction: Optional - filter by 'bullish' or 'bearish'

        Returns:
            Nearest unfilled FVG or None
        """
        # Ensure FVGs are detected
        if symbol not in self.detected_fvgs:
            self.detect_fair_value_gaps(candles, symbol)

        unfilled = self.get_unfilled_fvgs(symbol)

        if not unfilled:
            return None

        # Filter by direction if specified
        if direction:
            unfilled = [fvg for fvg in unfilled if fvg['type'] == direction]

        if not unfilled:
            return None

        # Find nearest by distance to mid price
        nearest = min(unfilled, key=lambda fvg: abs(fvg['mid'] - current_price))

        return nearest

    def get_fvg_fill_targets(self, fvg: Dict) -> Dict:
        """
        Get target levels for FVG fill trades

        Returns:
            Dictionary with entry, target, and invalidation levels
        """
        if fvg['type'] == 'bullish':
            # Bullish FVG: Enter at bottom, target top, invalidate below
            return {
                'entry_zone_low': fvg['bottom'],
                'entry_zone_high': fvg['mid'],  # Best entry at mid or bottom
                'target': fvg['top'],  # Fill target
                'stop_loss': fvg['bottom'] - (fvg['size'] * 0.5),  # SL 50% below gap
                'direction': 'BUY'
            }
        else:  # bearish
            # Bearish FVG: Enter at top, target bottom, invalidate above
            return {
                'entry_zone_low': fvg['mid'],
                'entry_zone_high': fvg['top'],  # Best entry at mid or top
                'target': fvg['bottom'],  # Fill target
                'stop_loss': fvg['top'] + (fvg['size'] * 0.5),  # SL 50% above gap
                'direction': 'SELL'
            }


# Global singleton instance
fair_value_gap_detector = FairValueGapDetector()
