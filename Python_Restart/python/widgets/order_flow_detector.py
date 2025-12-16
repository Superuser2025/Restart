"""
AppleTrader Pro - Institutional Order Flow Footprint (IMPROVEMENT #4)
Detects large institutional orders and smart money positioning
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import deque


class InstitutionalOrder:
    """Represents a detected institutional order"""

    def __init__(self, symbol: str, timestamp: datetime, price: float,
                 direction: str, volume_multiplier: float, pip_move: float,
                 order_type: str, confidence: float):
        self.symbol = symbol
        self.timestamp = timestamp
        self.price = price
        self.direction = direction  # 'BUY' or 'SELL'
        self.volume_multiplier = volume_multiplier  # e.g., 3.5× average
        self.pip_move = pip_move
        self.order_type = order_type  # 'absorption', 'sweep', 'accumulation'
        self.confidence = confidence  # 0-100
        self.estimated_size_usd = self._estimate_size()

    def _estimate_size(self) -> float:
        """Estimate order size in USD (simplified)"""
        # Rough estimate: 1 standard lot = $100k notional
        # Volume multiplier gives relative size
        base_size = 100000  # $100k
        estimated = base_size * self.volume_multiplier
        return estimated

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'price': self.price,
            'direction': self.direction,
            'volume_multiplier': self.volume_multiplier,
            'pip_move': self.pip_move,
            'order_type': self.order_type,
            'confidence': self.confidence,
            'estimated_size_usd': self.estimated_size_usd
        }


class InstitutionalOrderFlowDetector:
    """
    Institutional Order Flow Footprint Detector

    Detects large institutional orders using:
    - Volume spike analysis (3× average volume)
    - Immediate price impact (20+ pip move)
    - Rejection wicks (absorption)
    - Order flow patterns (sweeps, accumulation)

    Visualization:
    - Red/Green circles on chart (sized by order volume)
    - Labels: "🔴 SELL: 1.3255 (150M USD) - Rejection wick"

    Expected Impact: Trade WITH institutions, not against them
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize detector

        Args:
            max_history: Maximum orders to keep in history
        """
        self.max_history = max_history
        self.order_history = deque(maxlen=max_history)
        self.active_levels = {}  # {symbol: [price_levels]}
        self.last_scan = None

        # Detection thresholds
        self.volume_spike_threshold = 3.0  # 3× average volume
        self.pip_move_threshold = 20  # Minimum 20 pip move
        self.wick_ratio_threshold = 0.6  # 60% of candle is wick

    def scan_for_orders(self, symbol: str, df: pd.DataFrame,
                       lookback: int = 50) -> List[InstitutionalOrder]:
        """
        Scan for institutional orders in recent price action

        Args:
            symbol: Trading symbol
            df: DataFrame with OHLC and volume data
            lookback: Number of recent candles to analyze

        Returns:
            List of detected institutional orders
        """
        if df is None or len(df) < lookback:
            return []

        required_cols = ['open', 'high', 'low', 'close', 'time']
        if not all(col in df.columns for col in required_cols):
            return []

        # Get volume column (prefer volume, fallback to tick_volume)
        volume_col = None
        if 'volume' in df.columns:
            volume_col = 'volume'
        elif 'tick_volume' in df.columns:
            volume_col = 'tick_volume'

        if volume_col is None:
            return []

        detected_orders = []

        # Analyze recent candles
        recent_df = df.tail(lookback).copy()

        # Calculate average volume
        avg_volume = recent_df[volume_col].mean()

        if avg_volume == 0:
            return []

        # Scan each candle
        for idx in range(len(recent_df)):
            candle = recent_df.iloc[idx]

            # Skip if not enough data for comparison
            if idx < 10:
                continue

            # Volume spike detection
            current_volume = candle[volume_col]
            volume_multiplier = current_volume / avg_volume

            if volume_multiplier < self.volume_spike_threshold:
                continue

            # Price movement analysis
            open_price = candle['open']
            high_price = candle['high']
            low_price = candle['low']
            close_price = candle['close']

            pip_multiplier = 10000 if symbol != 'USDJPY' else 100

            # Bullish or bearish candle
            is_bullish = close_price > open_price
            body_size = abs(close_price - open_price) * pip_multiplier
            candle_range = (high_price - low_price) * pip_multiplier

            # Upper and lower wicks
            if is_bullish:
                upper_wick = (high_price - close_price) * pip_multiplier
                lower_wick = (open_price - low_price) * pip_multiplier
            else:
                upper_wick = (high_price - open_price) * pip_multiplier
                lower_wick = (close_price - low_price) * pip_multiplier

            # Check for various order patterns

            # 1. ABSORPTION (Large wick rejection)
            if upper_wick > candle_range * self.wick_ratio_threshold:
                if upper_wick > self.pip_move_threshold:
                    # Sellers absorbed buying pressure
                    order = InstitutionalOrder(
                        symbol=symbol,
                        timestamp=candle['time'],
                        price=high_price,
                        direction='SELL',
                        volume_multiplier=volume_multiplier,
                        pip_move=upper_wick,
                        order_type='absorption',
                        confidence=min(100, volume_multiplier * 20)
                    )
                    detected_orders.append(order)

            elif lower_wick > candle_range * self.wick_ratio_threshold:
                if lower_wick > self.pip_move_threshold:
                    # Buyers absorbed selling pressure
                    order = InstitutionalOrder(
                        symbol=symbol,
                        timestamp=candle['time'],
                        price=low_price,
                        direction='BUY',
                        volume_multiplier=volume_multiplier,
                        pip_move=lower_wick,
                        order_type='absorption',
                        confidence=min(100, volume_multiplier * 20)
                    )
                    detected_orders.append(order)

            # 2. SWEEP (Strong directional move with volume)
            elif body_size > self.pip_move_threshold:
                if body_size > candle_range * 0.7:  # Strong body, small wicks
                    direction = 'BUY' if is_bullish else 'SELL'
                    order_price = close_price

                    order = InstitutionalOrder(
                        symbol=symbol,
                        timestamp=candle['time'],
                        price=order_price,
                        direction=direction,
                        volume_multiplier=volume_multiplier,
                        pip_move=body_size,
                        order_type='sweep',
                        confidence=min(100, volume_multiplier * 15)
                    )
                    detected_orders.append(order)

            # 3. ACCUMULATION (Large volume, small body - consolidation)
            elif candle_range < 10 * (1 / pip_multiplier):  # Small range
                if volume_multiplier > 4.0:  # Even higher volume threshold
                    # Accumulation at this level
                    order = InstitutionalOrder(
                        symbol=symbol,
                        timestamp=candle['time'],
                        price=(high_price + low_price) / 2,
                        direction='NEUTRAL',
                        volume_multiplier=volume_multiplier,
                        pip_move=candle_range,
                        order_type='accumulation',
                        confidence=min(100, volume_multiplier * 12)
                    )
                    detected_orders.append(order)

        # Add to history
        for order in detected_orders:
            self.order_history.append(order)

        self.last_scan = datetime.now()

        return detected_orders

    def get_recent_orders(self, symbol: Optional[str] = None,
                         hours: int = 24) -> List[InstitutionalOrder]:
        """
        Get recent institutional orders

        Args:
            symbol: Filter by symbol (None = all)
            hours: Hours to look back

        Returns:
            List of recent orders
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        recent = []
        for order in self.order_history:
            if order.timestamp >= cutoff:
                if symbol is None or order.symbol == symbol:
                    recent.append(order)

        return sorted(recent, key=lambda x: x.timestamp, reverse=True)

    def get_order_clusters(self, symbol: str,
                          price_tolerance_pips: float = 10) -> List[Dict]:
        """
        Find price levels with multiple institutional orders (clusters)

        Args:
            symbol: Symbol to analyze
            price_tolerance_pips: Pip tolerance for clustering

        Returns:
            List of cluster dicts with aggregated data
        """
        orders = self.get_recent_orders(symbol, hours=24)

        if not orders:
            return []

        pip_multiplier = 10000 if symbol != 'USDJPY' else 100
        price_tolerance = price_tolerance_pips / pip_multiplier

        clusters = []

        # Sort by price
        sorted_orders = sorted(orders, key=lambda x: x.price)

        current_cluster = [sorted_orders[0]]

        for order in sorted_orders[1:]:
            cluster_avg_price = np.mean([o.price for o in current_cluster])

            if abs(order.price - cluster_avg_price) <= price_tolerance:
                # Add to current cluster
                current_cluster.append(order)
            else:
                # Close current cluster and start new one
                if len(current_cluster) >= 2:
                    clusters.append(self._create_cluster_summary(current_cluster, symbol))

                current_cluster = [order]

        # Don't forget last cluster
        if len(current_cluster) >= 2:
            clusters.append(self._create_cluster_summary(current_cluster, symbol))

        # Sort by strength
        clusters.sort(key=lambda x: x['strength'], reverse=True)

        return clusters

    def _create_cluster_summary(self, orders: List[InstitutionalOrder],
                               symbol: str) -> Dict:
        """Create summary for order cluster"""
        avg_price = np.mean([o.price for o in orders])
        total_volume = sum(o.volume_multiplier for o in orders)
        buy_count = sum(1 for o in orders if o.direction == 'BUY')
        sell_count = sum(1 for o in orders if o.direction == 'SELL')

        # Determine dominant direction
        if buy_count > sell_count:
            direction = 'BUY'
        elif sell_count > buy_count:
            direction = 'SELL'
        else:
            direction = 'NEUTRAL'

        # Calculate strength
        strength = len(orders) * (total_volume / len(orders))

        return {
            'symbol': symbol,
            'price': avg_price,
            'order_count': len(orders),
            'total_volume_multiplier': total_volume,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'direction': direction,
            'strength': strength,
            'latest_timestamp': max(o.timestamp for o in orders)
        }

    def format_order_display(self, order: InstitutionalOrder) -> str:
        """Format order for display"""
        emoji = '🔴' if order.direction == 'SELL' else '🟢'
        time_str = order.timestamp.strftime("%H:%M:%S")

        return (f"{emoji} {order.direction}: {order.price:.5f} "
                f"({order.estimated_size_usd / 1e6:.0f}M USD) - "
                f"{order.order_type.upper()} - {time_str}")

    def get_chart_overlays(self, symbol: str, hours: int = 4) -> List[Dict]:
        """
        Get institutional orders for chart overlay

        Args:
            symbol: Symbol to get orders for
            hours: Hours to look back

        Returns:
            List of overlay dicts for matplotlib
        """
        orders = self.get_recent_orders(symbol, hours)

        overlays = []

        for order in orders:
            # Size circle based on volume
            marker_size = min(200, 50 + (order.volume_multiplier * 20))

            # Color based on direction
            if order.direction == 'BUY':
                color = 'green'
                marker = '^'  # Triangle up
            elif order.direction == 'SELL':
                color = 'red'
                marker = 'v'  # Triangle down
            else:
                color = 'yellow'
                marker = 'o'  # Circle

            overlays.append({
                'type': 'marker',
                'timestamp': order.timestamp,
                'price': order.price,
                'color': color,
                'marker': marker,
                'size': marker_size,
                'alpha': 0.6,
                'label': f"{order.order_type.upper()} - {order.estimated_size_usd / 1e6:.0f}M"
            })

        return overlays

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        total_orders = len(self.order_history)

        if total_orders == 0:
            return {
                'total_orders': 0,
                'buy_count': 0,
                'sell_count': 0,
                'avg_volume_multiplier': 0,
                'avg_confidence': 0
            }

        buy_count = sum(1 for o in self.order_history if o.direction == 'BUY')
        sell_count = sum(1 for o in self.order_history if o.direction == 'SELL')
        neutral_count = total_orders - buy_count - sell_count

        avg_volume = np.mean([o.volume_multiplier for o in self.order_history])
        avg_confidence = np.mean([o.confidence for o in self.order_history])

        return {
            'total_orders': total_orders,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'neutral_count': neutral_count,
            'avg_volume_multiplier': avg_volume,
            'avg_confidence': avg_confidence,
            'last_scan': self.last_scan
        }


# Global instance
order_flow_detector = InstitutionalOrderFlowDetector()
