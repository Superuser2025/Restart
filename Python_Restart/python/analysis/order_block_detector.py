"""
Order Block Detector - Institutional Smart Money Entry Zones

An Order Block (OB) is the last opposite-color candle before a strong impulse move.
It represents where institutional traders (smart money) entered positions.

Theory:
- Bullish Order Block (Demand Zone): Last red candle before bullish impulse
- Bearish Order Block (Supply Zone): Last green candle before bearish impulse
- Price often returns to OBs for retests before continuing the move

This module detects, validates, and tracks order blocks for trading opportunities.
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class OrderBlockDetector:
    """
    Detect and validate institutional order blocks from price action

    Key Features:
    - Detect bullish/bearish order blocks
    - Track OB strength based on impulse quality
    - Monitor OB mitigation (touched/broken)
    - Validate OB for entry opportunities
    """

    def __init__(self):
        self.detected_order_blocks = {}  # {symbol: [OB1, OB2, ...]}

    def detect_order_blocks(self, candles: List[Dict], symbol: str = "UNKNOWN",
                           lookback: int = 50, min_impulse_pips: float = 15) -> List[Dict]:
        """
        Detect order blocks from candle data

        Args:
            candles: List of OHLC candles (dicts with open, high, low, close, time)
            symbol: Trading symbol (for tracking)
            lookback: How many candles to analyze
            min_impulse_pips: Minimum pip move to qualify as impulse (default 15)

        Returns:
            List of order block dictionaries
        """
        if not candles or len(candles) < 10:
            return []

        order_blocks = []

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(candles)

        # Determine pip value (0.01 for JPY pairs, 0.0001 for others)
        pip_value = 0.01 if 'JPY' in symbol else 0.0001
        min_impulse_price = min_impulse_pips * pip_value

        # Start from position `lookback` to have historical context
        start_idx = max(10, len(candles) - lookback)

        for i in range(start_idx, len(candles)):
            # Check for bullish impulse (3+ consecutive green candles with significant move)
            bullish_ob = self._detect_bullish_order_block(candles, df, i, min_impulse_price)
            if bullish_ob:
                order_blocks.append(bullish_ob)

            # Check for bearish impulse (3+ consecutive red candles with significant move)
            bearish_ob = self._detect_bearish_order_block(candles, df, i, min_impulse_price)
            if bearish_ob:
                order_blocks.append(bearish_ob)

        # Store for this symbol
        self.detected_order_blocks[symbol] = order_blocks

        return order_blocks

    def _detect_bullish_order_block(self, candles: List[Dict], df: pd.DataFrame,
                                   index: int, min_impulse_price: float) -> Optional[Dict]:
        """
        Detect bullish order block (demand zone)

        Logic:
        1. Find bullish impulse: 3+ consecutive green candles
        2. Impulse must move > min_impulse_price
        3. Find last red candle before impulse
        4. That red candle = bullish order block (demand zone)
        """
        if index < 5:  # Need at least 5 candles of history
            return None

        # Check if we have a bullish impulse starting at index-2
        impulse_candles = candles[index-2:index+1]  # 3 candles

        if len(impulse_candles) < 3:
            return None

        # Check all candles are bullish (close > open)
        all_bullish = all(c['close'] > c['open'] for c in impulse_candles)
        if not all_bullish:
            return None

        # Check total impulse size
        impulse_low = min(c['low'] for c in impulse_candles)
        impulse_high = max(c['high'] for c in impulse_candles)
        impulse_size = impulse_high - impulse_low

        if impulse_size < min_impulse_price:
            return None  # Impulse too small

        # Find last bearish (red) candle before impulse
        last_red_idx = None
        for j in range(index - 3, max(0, index - 10), -1):  # Look back up to 10 candles
            if candles[j]['close'] < candles[j]['open']:  # Red candle
                last_red_idx = j
                break

        if last_red_idx is None:
            return None  # No red candle found

        # This red candle is the bullish order block!
        ob_candle = candles[last_red_idx]

        # Calculate order block strength based on impulse quality
        strength = self._calculate_ob_strength(impulse_candles, impulse_size)

        return {
            'type': 'demand',  # Bullish OB = demand zone
            'direction': 'bullish',
            'price_high': ob_candle['high'],
            'price_low': ob_candle['low'],
            'price_mid': (ob_candle['high'] + ob_candle['low']) / 2,
            'timestamp': ob_candle.get('time', datetime.now()),
            'candle_index': last_red_idx,
            'strength': strength,
            'impulse_size_pips': impulse_size / (0.01 if 'JPY' in str(ob_candle) else 0.0001),
            'valid': True,
            'mitigated': False,
            'touch_count': 0
        }

    def _detect_bearish_order_block(self, candles: List[Dict], df: pd.DataFrame,
                                   index: int, min_impulse_price: float) -> Optional[Dict]:
        """
        Detect bearish order block (supply zone)

        Logic:
        1. Find bearish impulse: 3+ consecutive red candles
        2. Impulse must move > min_impulse_price
        3. Find last green candle before impulse
        4. That green candle = bearish order block (supply zone)
        """
        if index < 5:
            return None

        # Check if we have a bearish impulse
        impulse_candles = candles[index-2:index+1]  # 3 candles

        if len(impulse_candles) < 3:
            return None

        # Check all candles are bearish (close < open)
        all_bearish = all(c['close'] < c['open'] for c in impulse_candles)
        if not all_bearish:
            return None

        # Check total impulse size
        impulse_low = min(c['low'] for c in impulse_candles)
        impulse_high = max(c['high'] for c in impulse_candles)
        impulse_size = impulse_high - impulse_low

        if impulse_size < min_impulse_price:
            return None  # Impulse too small

        # Find last bullish (green) candle before impulse
        last_green_idx = None
        for j in range(index - 3, max(0, index - 10), -1):
            if candles[j]['close'] > candles[j]['open']:  # Green candle
                last_green_idx = j
                break

        if last_green_idx is None:
            return None

        # This green candle is the bearish order block!
        ob_candle = candles[last_green_idx]

        # Calculate strength
        strength = self._calculate_ob_strength(impulse_candles, impulse_size)

        return {
            'type': 'supply',  # Bearish OB = supply zone
            'direction': 'bearish',
            'price_high': ob_candle['high'],
            'price_low': ob_candle['low'],
            'price_mid': (ob_candle['high'] + ob_candle['low']) / 2,
            'timestamp': ob_candle.get('time', datetime.now()),
            'candle_index': last_green_idx,
            'strength': strength,
            'impulse_size_pips': impulse_size / (0.01 if 'JPY' in str(ob_candle) else 0.0001),
            'valid': True,
            'mitigated': False,
            'touch_count': 0
        }

    def _calculate_ob_strength(self, impulse_candles: List[Dict], impulse_size: float) -> int:
        """
        Calculate order block strength (0-100)

        Factors:
        - Impulse size (larger = stronger)
        - Number of consecutive impulse candles
        - Candle body size vs wick ratio (clean candles = stronger)
        """
        strength = 50  # Base strength

        # Factor 1: Impulse size (0-25 points)
        # Assume 15 pips = base, 30+ pips = excellent
        if impulse_size > 0:
            pip_equivalent = impulse_size / 0.0001  # Rough pip estimate
            strength += min(25, int(pip_equivalent / 30 * 25))

        # Factor 2: Number of impulse candles (0-15 points)
        num_candles = len(impulse_candles)
        if num_candles >= 5:
            strength += 15
        elif num_candles == 4:
            strength += 10
        elif num_candles == 3:
            strength += 5

        # Factor 3: Clean candles (small wicks) = stronger (0-10 points)
        clean_count = 0
        for candle in impulse_candles:
            body_size = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']
            if total_range > 0:
                body_ratio = body_size / total_range
                if body_ratio > 0.7:  # Body is >70% of total range
                    clean_count += 1

        strength += int((clean_count / len(impulse_candles)) * 10)

        return min(100, strength)

    def validate_order_block(self, candles: List[Dict], price_level: float,
                            symbol: str = "UNKNOWN") -> bool:
        """
        Check if a specific price level is near a valid (unmitigated) order block

        Args:
            candles: Recent candle data
            price_level: Price to check (e.g., entry price)
            symbol: Trading symbol

        Returns:
            True if price is within a valid order block zone
        """
        # Detect order blocks if not already done for this symbol
        if symbol not in self.detected_order_blocks:
            self.detect_order_blocks(candles, symbol)

        order_blocks = self.detected_order_blocks.get(symbol, [])

        if not order_blocks:
            return False

        # Update mitigation status for all OBs
        self._update_mitigation_status(order_blocks, candles)

        # Check if price_level is within any valid (unmitigated) OB
        for ob in order_blocks:
            if not ob['valid'] or ob['mitigated']:
                continue  # Skip invalid or mitigated OBs

            # Check if price is within OB zone (with small tolerance)
            tolerance = (ob['price_high'] - ob['price_low']) * 0.1  # 10% tolerance

            if (ob['price_low'] - tolerance) <= price_level <= (ob['price_high'] + tolerance):
                return True  # Price is at a valid order block!

        return False

    def _update_mitigation_status(self, order_blocks: List[Dict], candles: List[Dict]):
        """
        Update mitigation status for all order blocks

        Mitigation = Price moved through the order block zone
        - Bullish OB mitigated if price closes below OB low
        - Bearish OB mitigated if price closes above OB high
        """
        if not candles:
            return

        recent_candles = candles[-20:]  # Check last 20 candles

        for ob in order_blocks:
            if ob['mitigated']:
                continue  # Already mitigated

            for candle in recent_candles:
                # Check if price touched the OB
                if ob['price_low'] <= candle['low'] <= ob['price_high'] or \
                   ob['price_low'] <= candle['high'] <= ob['price_high']:
                    ob['touch_count'] += 1

                # Check for mitigation
                if ob['direction'] == 'bullish':
                    # Bullish OB mitigated if price closes BELOW OB low
                    if candle['close'] < ob['price_low']:
                        ob['mitigated'] = True
                        ob['valid'] = False
                        break

                elif ob['direction'] == 'bearish':
                    # Bearish OB mitigated if price closes ABOVE OB high
                    if candle['close'] > ob['price_high']:
                        ob['mitigated'] = True
                        ob['valid'] = False
                        break

    def get_active_order_blocks(self, symbol: str, max_age_candles: int = 100) -> List[Dict]:
        """
        Get currently active (valid, unmitigated) order blocks for a symbol

        Args:
            symbol: Trading symbol
            max_age_candles: Maximum age of OB to consider (default 100 candles)

        Returns:
            List of active order blocks
        """
        all_obs = self.detected_order_blocks.get(symbol, [])

        # Filter for active OBs
        active = [
            ob for ob in all_obs
            if ob['valid'] and not ob['mitigated']
        ]

        # Sort by strength (strongest first)
        active.sort(key=lambda x: x['strength'], reverse=True)

        return active

    def get_nearest_order_block(self, candles: List[Dict], current_price: float,
                               symbol: str = "UNKNOWN", direction: str = None) -> Optional[Dict]:
        """
        Find the nearest order block to current price

        Args:
            candles: Recent candle data
            current_price: Current market price
            symbol: Trading symbol
            direction: Optional - filter by 'bullish' or 'bearish'

        Returns:
            Nearest valid order block or None
        """
        # Ensure OBs are detected
        if symbol not in self.detected_order_blocks:
            self.detect_order_blocks(candles, symbol)

        active_obs = self.get_active_order_blocks(symbol)

        if not active_obs:
            return None

        # Filter by direction if specified
        if direction:
            active_obs = [ob for ob in active_obs if ob['direction'] == direction]

        if not active_obs:
            return None

        # Find nearest by distance to price_mid
        nearest = min(active_obs, key=lambda ob: abs(ob['price_mid'] - current_price))

        return nearest


# Global singleton instance
order_block_detector = OrderBlockDetector()
