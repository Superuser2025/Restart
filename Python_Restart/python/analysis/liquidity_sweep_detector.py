"""
Liquidity Sweep Detector - Smart Money Stop Hunts

A Liquidity Sweep (aka Stop Hunt) occurs when price:
1. Reaches an area of equal highs/lows (liquidity pool)
2. Wicks above/below to grab stops
3. Quickly rejects back (closes opposite direction)

Theory:
- Institutional traders "hunt" retail stop losses before reversing
- Equal highs/lows = clusters of stop loss orders = liquidity
- Sweep + rejection = high-probability reversal zone
- After sweep, price often moves strongly in opposite direction

This module detects liquidity sweeps for high-probability trading opportunities.
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class LiquiditySweepDetector:
    """
    Detect liquidity sweeps (stop hunts) from price action

    Key Features:
    - Detect equal highs/lows (liquidity pools)
    - Identify sweep patterns (wick + rejection)
    - Track sweep strength and reliability
    - Validate recent sweeps for entries
    """

    def __init__(self):
        self.detected_sweeps = {}  # {symbol: [sweep1, sweep2, ...]}

    def detect_liquidity_sweeps(self, candles: List[Dict], symbol: str = "UNKNOWN",
                               lookback: int = 50, tolerance_pips: float = 3) -> List[Dict]:
        """
        Detect liquidity sweeps from candle data

        Args:
            candles: List of OHLC candles
            symbol: Trading symbol
            lookback: How many candles to analyze
            tolerance_pips: How close highs/lows must be to qualify as "equal" (default 3 pips)

        Returns:
            List of detected sweep dictionaries
        """
        if not candles or len(candles) < 20:
            return []

        sweeps = []

        # Determine pip value
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        tolerance_price = tolerance_pips * pip_value

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(candles)

        # Find equal highs (liquidity pools above price)
        equal_highs = self._find_equal_levels(candles, 'high', tolerance_price, lookback)

        # Find equal lows (liquidity pools below price)
        equal_lows = self._find_equal_levels(candles, 'low', tolerance_price, lookback)

        # Check recent candles for sweeps of these levels
        recent_start = max(0, len(candles) - lookback)

        for i in range(recent_start, len(candles)):
            candle = candles[i]

            # Check for high sweeps (bearish reversal expected)
            for level in equal_highs:
                sweep = self._check_high_sweep(candle, level, i, symbol)
                if sweep:
                    sweeps.append(sweep)

            # Check for low sweeps (bullish reversal expected)
            for level in equal_lows:
                sweep = self._check_low_sweep(candle, level, i, symbol)
                if sweep:
                    sweeps.append(sweep)

        # Store for this symbol
        self.detected_sweeps[symbol] = sweeps

        return sweeps

    def _find_equal_levels(self, candles: List[Dict], level_type: str,
                          tolerance: float, lookback: int) -> List[float]:
        """
        Find equal highs or lows (liquidity pools)

        Args:
            candles: Candle data
            level_type: 'high' or 'low'
            tolerance: Price tolerance for "equal"
            lookback: How far back to look

        Returns:
            List of liquidity levels
        """
        if len(candles) < lookback:
            lookback = len(candles)

        recent_candles = candles[-lookback:]
        levels = []

        # Extract the relevant values
        values = [c[level_type] for c in recent_candles]

        # Find swing points (local peaks for highs, local troughs for lows)
        swing_indices = self._find_swing_points(values, level_type)

        # Group swing points that are within tolerance of each other
        swing_values = [values[i] for i in swing_indices]

        if not swing_values:
            return []

        # Cluster values within tolerance
        clusters = []
        for value in swing_values:
            # Check if this value belongs to an existing cluster
            found_cluster = False
            for cluster in clusters:
                if abs(value - cluster[0]) <= tolerance:
                    cluster.append(value)
                    found_cluster = True
                    break

            if not found_cluster:
                clusters.append([value])

        # Only keep clusters with 2+ swings (= equal highs/lows)
        equal_levels = []
        for cluster in clusters:
            if len(cluster) >= 2:
                # Use the highest value in cluster for equal highs, lowest for equal lows
                if level_type == 'high':
                    equal_levels.append(max(cluster))
                else:
                    equal_levels.append(min(cluster))

        return equal_levels

    def _find_swing_points(self, values: List[float], level_type: str) -> List[int]:
        """
        Find swing highs or swing lows in a series of values

        Args:
            values: List of price values
            level_type: 'high' or 'low'

        Returns:
            List of indices where swings occur
        """
        if len(values) < 5:
            return []

        swings = []

        for i in range(2, len(values) - 2):
            if level_type == 'high':
                # Swing high: higher than 2 candles before and after
                if (values[i] > values[i-1] and values[i] > values[i-2] and
                    values[i] > values[i+1] and values[i] > values[i+2]):
                    swings.append(i)
            else:  # 'low'
                # Swing low: lower than 2 candles before and after
                if (values[i] < values[i-1] and values[i] < values[i-2] and
                    values[i] < values[i+1] and values[i] < values[i+2]):
                    swings.append(i)

        return swings

    def _check_high_sweep(self, candle: Dict, level: float, index: int,
                         symbol: str) -> Optional[Dict]:
        """
        Check if this candle swept a high level (bearish sweep)

        Criteria:
        1. High wicks ABOVE the level
        2. Close is BELOW the level (rejection)
        3. Bearish reversal expected
        """
        # Did the high reach above the level?
        if candle['high'] <= level:
            return None  # Didn't touch the level

        # Did it close below the level? (rejection)
        if candle['close'] >= level:
            return None  # No rejection

        # Calculate rejection strength
        rejection_distance = candle['high'] - candle['close']
        candle_range = candle['high'] - candle['low']

        if candle_range == 0:
            return None

        rejection_ratio = rejection_distance / candle_range

        # Strong rejection = wick is >50% of candle range
        if rejection_ratio < 0.5:
            return None  # Weak rejection

        # Calculate sweep strength (0-100)
        strength = self._calculate_sweep_strength(
            candle, level, rejection_ratio, 'high'
        )

        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        sweep_distance_pips = (candle['high'] - level) / pip_value

        return {
            'type': 'high_sweep',
            'direction': 'bearish',  # Expect bearish move after high sweep
            'level': level,
            'sweep_high': candle['high'],
            'sweep_distance_pips': sweep_distance_pips,
            'close': candle['close'],
            'rejection_ratio': rejection_ratio,
            'strength': strength,
            'timestamp': candle.get('time', datetime.now()),
            'candle_index': index,
            'expected_direction': 'SELL'  # Trading signal
        }

    def _check_low_sweep(self, candle: Dict, level: float, index: int,
                        symbol: str) -> Optional[Dict]:
        """
        Check if this candle swept a low level (bullish sweep)

        Criteria:
        1. Low wicks BELOW the level
        2. Close is ABOVE the level (rejection)
        3. Bullish reversal expected
        """
        # Did the low reach below the level?
        if candle['low'] >= level:
            return None

        # Did it close above the level? (rejection)
        if candle['close'] <= level:
            return None

        # Calculate rejection strength
        rejection_distance = candle['close'] - candle['low']
        candle_range = candle['high'] - candle['low']

        if candle_range == 0:
            return None

        rejection_ratio = rejection_distance / candle_range

        # Strong rejection = wick is >50% of candle range
        if rejection_ratio < 0.5:
            return None

        # Calculate strength
        strength = self._calculate_sweep_strength(
            candle, level, rejection_ratio, 'low'
        )

        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        sweep_distance_pips = (level - candle['low']) / pip_value

        return {
            'type': 'low_sweep',
            'direction': 'bullish',  # Expect bullish move after low sweep
            'level': level,
            'sweep_low': candle['low'],
            'sweep_distance_pips': sweep_distance_pips,
            'close': candle['close'],
            'rejection_ratio': rejection_ratio,
            'strength': strength,
            'timestamp': candle.get('time', datetime.now()),
            'candle_index': index,
            'expected_direction': 'BUY'  # Trading signal
        }

    def _calculate_sweep_strength(self, candle: Dict, level: float,
                                  rejection_ratio: float, sweep_type: str) -> int:
        """
        Calculate liquidity sweep strength (0-100)

        Factors:
        - Rejection ratio (larger wick = stronger)
        - Sweep distance (further past level = more stops grabbed)
        - Candle body size (small body = stronger rejection)
        """
        strength = 50  # Base strength

        # Factor 1: Rejection ratio (0-30 points)
        # 50% rejection = 0, 100% rejection = 30
        if rejection_ratio >= 0.5:
            strength += int((rejection_ratio - 0.5) * 60)  # Scale 0.5-1.0 to 0-30

        # Factor 2: Sweep distance (0-20 points)
        if sweep_type == 'high':
            sweep_distance = candle['high'] - level
        else:
            sweep_distance = level - candle['low']

        candle_range = candle['high'] - candle['low']
        if candle_range > 0:
            sweep_ratio = sweep_distance / candle_range
            strength += int(sweep_ratio * 20)

        # Factor 3: Small candle body = strong rejection (0-20 points)
        body_size = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']

        if total_range > 0:
            body_ratio = body_size / total_range
            # Inverse: smaller body = higher score
            strength += int((1 - body_ratio) * 20)

        return min(100, max(0, strength))

    def has_recent_sweep(self, candles: List[Dict], symbol: str = "UNKNOWN",
                        lookback_candles: int = 5) -> bool:
        """
        Check if a liquidity sweep occurred in the last N candles

        Args:
            candles: Recent candle data
            symbol: Trading symbol
            lookback_candles: How recent to check (default 5 candles)

        Returns:
            True if sweep detected in recent candles
        """
        # Detect sweeps if not already done
        if symbol not in self.detected_sweeps:
            self.detect_liquidity_sweeps(candles, symbol)

        sweeps = self.detected_sweeps.get(symbol, [])

        if not sweeps:
            return False

        # Check if any sweep is in the last N candles
        last_candle_idx = len(candles) - 1

        for sweep in sweeps:
            candle_idx = sweep['candle_index']
            if last_candle_idx - candle_idx <= lookback_candles:
                return True  # Recent sweep found!

        return False

    def get_recent_sweeps(self, symbol: str, lookback_candles: int = 10) -> List[Dict]:
        """
        Get all liquidity sweeps from the last N candles

        Args:
            symbol: Trading symbol
            lookback_candles: How recent to check

        Returns:
            List of recent sweep dictionaries
        """
        all_sweeps = self.detected_sweeps.get(symbol, [])

        if not all_sweeps:
            return []

        # Filter for recent sweeps
        # Note: We need to track the total candle count to determine recency
        # For now, just return all sweeps (caller should ensure detect_liquidity_sweeps
        # was called with appropriate lookback)

        return all_sweeps

    def get_sweep_near_price(self, candles: List[Dict], current_price: float,
                            symbol: str = "UNKNOWN", tolerance_pips: float = 10) -> Optional[Dict]:
        """
        Find if there's a recent sweep near the current price

        Args:
            candles: Recent candle data
            current_price: Current market price
            symbol: Trading symbol
            tolerance_pips: How close sweep must be to current price

        Returns:
            Nearest recent sweep or None
        """
        # Ensure sweeps are detected
        if symbol not in self.detected_sweeps:
            self.detect_liquidity_sweeps(candles, symbol)

        sweeps = self.detected_sweeps.get(symbol, [])

        if not sweeps:
            return None

        # Find sweeps within tolerance of current price
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        tolerance_price = tolerance_pips * pip_value

        nearby_sweeps = [
            s for s in sweeps
            if abs(s['level'] - current_price) <= tolerance_price
        ]

        if not nearby_sweeps:
            return None

        # Return the strongest nearby sweep
        return max(nearby_sweeps, key=lambda s: s['strength'])


# Global singleton instance
liquidity_sweep_detector = LiquiditySweepDetector()
