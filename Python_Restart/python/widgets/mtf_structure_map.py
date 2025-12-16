"""
AppleTrader Pro - Multi-Timeframe Structure Map (IMPROVEMENT #6)
Visualizes support/resistance levels across W1/D1/H4/M15 timeframes
Detects confluence zones where multiple timeframes align
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict


class MTFStructureMap:
    """
    Multi-Timeframe Structure Map Engine

    Analyzes price structure across multiple timeframes to identify:
    - Key support/resistance levels per timeframe
    - Confluence zones where timeframes align
    - Trend direction per timeframe
    - Distance to nearest structure
    """

    # Timeframe hierarchy (importance weight)
    TIMEFRAMES = {
        'W1': {'weight': 4, 'lookback': 52, 'display': 'W1', 'line_width': 3},
        'D1': {'weight': 3, 'lookback': 90, 'display': 'D1', 'line_width': 2.5},
        'H4': {'weight': 2, 'lookback': 180, 'display': 'H4', 'line_width': 2},
        'H1': {'weight': 1.5, 'lookback': 240, 'display': 'H1', 'line_width': 1.5},
        'M15': {'weight': 1, 'lookback': 480, 'display': 'M15', 'line_width': 1}
    }

    def __init__(self):
        self.structure_levels = {}  # {timeframe: {support: [...], resistance: [...]}}
        self.confluence_zones = []  # List of confluence zone dicts
        self.trend_analysis = {}    # {timeframe: trend_direction}
        self.last_update = None

    def analyze_structure(self, data_by_timeframe: Dict[str, pd.DataFrame],
                         current_price: float) -> Dict:
        """
        Analyze structure across all available timeframes

        Args:
            data_by_timeframe: {timeframe: DataFrame with OHLC data}
            current_price: Current market price

        Returns:
            Complete structure analysis
        """
        self.structure_levels = {}
        self.trend_analysis = {}

        # Analyze each timeframe
        for tf, df in data_by_timeframe.items():
            if tf not in self.TIMEFRAMES:
                continue

            if df is None or len(df) < 20:
                continue

            # Find swing highs/lows
            levels = self._find_structure_levels(df, tf)
            self.structure_levels[tf] = levels

            # Determine trend
            trend = self._analyze_trend(df)
            self.trend_analysis[tf] = trend

        # Find confluence zones
        self.confluence_zones = self._find_confluence_zones(current_price)

        self.last_update = datetime.now()

        return self._generate_report(current_price)

    def _find_structure_levels(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Find swing highs and lows in the data

        Returns:
            {support: [...], resistance: [...]}
        """
        if 'high' not in df.columns or 'low' not in df.columns:
            return {'support': [], 'resistance': []}

        highs = df['high'].values
        lows = df['low'].values

        # Adaptive period based on timeframe
        period = 5 if timeframe in ['M15', 'H1'] else 3

        # Find swing highs (resistance)
        resistance_levels = []
        for i in range(period, len(highs) - period):
            if self._is_swing_high(highs, i, period):
                resistance_levels.append({
                    'price': highs[i],
                    'strength': self._calculate_level_strength(highs, i, period),
                    'touches': 1,
                    'last_touch_index': i
                })

        # Find swing lows (support)
        support_levels = []
        for i in range(period, len(lows) - period):
            if self._is_swing_low(lows, i, period):
                support_levels.append({
                    'price': lows[i],
                    'strength': self._calculate_level_strength(lows, i, period),
                    'touches': 1,
                    'last_touch_index': i
                })

        # Cluster nearby levels
        resistance_levels = self._cluster_levels(resistance_levels)
        support_levels = self._cluster_levels(support_levels)

        # Sort by strength
        resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
        support_levels.sort(key=lambda x: x['strength'], reverse=True)

        # Keep top 5 of each
        return {
            'support': support_levels[:5],
            'resistance': resistance_levels[:5]
        }

    def _is_swing_high(self, data: np.ndarray, index: int, period: int) -> bool:
        """Check if index is a swing high"""
        center = data[index]
        left = data[index - period:index]
        right = data[index + 1:index + period + 1]

        return (len(left) > 0 and center > max(left) and
                len(right) > 0 and center > max(right))

    def _is_swing_low(self, data: np.ndarray, index: int, period: int) -> bool:
        """Check if index is a swing low"""
        center = data[index]
        left = data[index - period:index]
        right = data[index + 1:index + period + 1]

        return (len(left) > 0 and center < min(left) and
                len(right) > 0 and center < min(right))

    def _calculate_level_strength(self, data: np.ndarray, index: int,
                                  period: int) -> float:
        """
        Calculate strength of a level based on:
        - How far it stood out from neighbors
        - Volume at that level (if available)
        """
        center = data[index]
        neighbors = np.concatenate([
            data[max(0, index - period):index],
            data[index + 1:min(len(data), index + period + 1)]
        ])

        if len(neighbors) == 0:
            return 0

        # Measure how much it stands out
        avg_neighbor = np.mean(neighbors)
        standout = abs(center - avg_neighbor) / avg_neighbor

        # Normalize to 0-100
        strength = min(100, standout * 1000)

        return strength

    def _cluster_levels(self, levels: List[Dict],
                       tolerance_pct: float = 0.001) -> List[Dict]:
        """
        Cluster nearby levels together

        Args:
            levels: List of level dicts
            tolerance_pct: Percentage tolerance for clustering (0.1% default)
        """
        if not levels:
            return []

        clustered = []
        sorted_levels = sorted(levels, key=lambda x: x['price'])

        current_cluster = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            # Check if within tolerance of cluster
            cluster_avg = np.mean([l['price'] for l in current_cluster])

            if abs(level['price'] - cluster_avg) / cluster_avg <= tolerance_pct:
                # Add to current cluster
                current_cluster.append(level)
            else:
                # Close current cluster and start new one
                clustered.append(self._merge_cluster(current_cluster))
                current_cluster = [level]

        # Don't forget last cluster
        if current_cluster:
            clustered.append(self._merge_cluster(current_cluster))

        return clustered

    def _merge_cluster(self, cluster: List[Dict]) -> Dict:
        """Merge multiple levels into one stronger level"""
        return {
            'price': np.mean([l['price'] for l in cluster]),
            'strength': sum(l['strength'] for l in cluster),
            'touches': len(cluster)
        }

    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """
        Determine trend direction

        Returns:
            'BULLISH', 'BEARISH', or 'RANGING'
        """
        if 'close' not in df.columns or len(df) < 20:
            return 'UNKNOWN'

        closes = df['close'].values

        # Simple trend: compare recent closes to earlier closes
        recent = closes[-20:]
        earlier = closes[-40:-20] if len(closes) >= 40 else closes[:20]

        recent_avg = np.mean(recent)
        earlier_avg = np.mean(earlier)

        change_pct = (recent_avg - earlier_avg) / earlier_avg

        if change_pct > 0.005:  # 0.5% threshold
            return 'BULLISH'
        elif change_pct < -0.005:
            return 'BEARISH'
        else:
            return 'RANGING'

    def _find_confluence_zones(self, current_price: float) -> List[Dict]:
        """
        Find zones where multiple timeframes have structure nearby

        Args:
            current_price: Current market price

        Returns:
            List of confluence zone dicts sorted by strength
        """
        confluence_zones = []

        # Collect all levels from all timeframes
        all_levels = []
        for tf, levels in self.structure_levels.items():
            tf_weight = self.TIMEFRAMES[tf]['weight']

            for support in levels['support']:
                all_levels.append({
                    'price': support['price'],
                    'type': 'support',
                    'timeframe': tf,
                    'weight': tf_weight,
                    'strength': support['strength']
                })

            for resistance in levels['resistance']:
                all_levels.append({
                    'price': resistance['price'],
                    'type': 'resistance',
                    'timeframe': tf,
                    'weight': tf_weight,
                    'strength': resistance['strength']
                })

        if not all_levels:
            return []

        # Sort by price
        all_levels.sort(key=lambda x: x['price'])

        # Find clusters of levels (confluence)
        tolerance_pct = 0.002  # 0.2% tolerance

        i = 0
        while i < len(all_levels):
            # Start a potential confluence zone
            zone_levels = [all_levels[i]]
            zone_price = all_levels[i]['price']

            # Look for nearby levels
            j = i + 1
            while j < len(all_levels):
                if abs(all_levels[j]['price'] - zone_price) / zone_price <= tolerance_pct:
                    zone_levels.append(all_levels[j])
                    j += 1
                else:
                    break

            # If we have levels from 2+ timeframes, it's a confluence zone
            unique_timeframes = set(l['timeframe'] for l in zone_levels)

            if len(unique_timeframes) >= 2:
                # Calculate zone strength
                total_weight = sum(l['weight'] * l['strength'] for l in zone_levels)
                avg_price = np.mean([l['price'] for l in zone_levels])

                # Determine zone type
                support_count = sum(1 for l in zone_levels if l['type'] == 'support')
                resistance_count = len(zone_levels) - support_count
                zone_type = 'support' if support_count > resistance_count else 'resistance'

                confluence_zones.append({
                    'price': avg_price,
                    'type': zone_type,
                    'strength': total_weight,
                    'timeframes': list(unique_timeframes),
                    'distance_pips': abs(avg_price - current_price) * 10000,
                    'level_count': len(zone_levels)
                })

            i = j if j > i else i + 1

        # Sort by strength
        confluence_zones.sort(key=lambda x: x['strength'], reverse=True)

        return confluence_zones[:10]  # Top 10 confluence zones

    def _generate_report(self, current_price: float) -> Dict:
        """Generate complete structure report"""

        # Find nearest support and resistance
        nearest_support = None
        nearest_resistance = None

        for tf, levels in self.structure_levels.items():
            for support in levels['support']:
                if support['price'] < current_price:
                    if nearest_support is None or support['price'] > nearest_support['price']:
                        nearest_support = {
                            'price': support['price'],
                            'timeframe': tf,
                            'strength': support['strength']
                        }

            for resistance in levels['resistance']:
                if resistance['price'] > current_price:
                    if nearest_resistance is None or resistance['price'] < nearest_resistance['price']:
                        nearest_resistance = {
                            'price': resistance['price'],
                            'timeframe': tf,
                            'strength': resistance['strength']
                        }

        # Find top confluence zone
        top_confluence = self.confluence_zones[0] if self.confluence_zones else None

        return {
            'structure_levels': self.structure_levels,
            'trend_analysis': self.trend_analysis,
            'confluence_zones': self.confluence_zones,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'top_confluence': top_confluence,
            'current_price': current_price,
            'last_update': self.last_update
        }

    def get_chart_overlays(self) -> List[Dict]:
        """
        Get structure levels formatted for chart overlay

        Returns:
            List of line dicts for matplotlib
        """
        overlays = []

        for tf, levels in self.structure_levels.items():
            tf_config = self.TIMEFRAMES[tf]
            line_width = tf_config['line_width']

            # Support levels (green)
            for support in levels['support']:
                overlays.append({
                    'type': 'hline',
                    'price': support['price'],
                    'color': 'green',
                    'alpha': 0.3 + (support['strength'] / 100) * 0.4,
                    'line_width': line_width,
                    'label': f"{tf} Support",
                    'timeframe': tf
                })

            # Resistance levels (red)
            for resistance in levels['resistance']:
                overlays.append({
                    'type': 'hline',
                    'price': resistance['price'],
                    'color': 'red',
                    'alpha': 0.3 + (resistance['strength'] / 100) * 0.4,
                    'line_width': line_width,
                    'label': f"{tf} Resistance",
                    'timeframe': tf
                })

        # Confluence zones (yellow with glow effect)
        for zone in self.confluence_zones[:5]:  # Top 5
            overlays.append({
                'type': 'hzone',
                'price': zone['price'],
                'height': zone['price'] * 0.0005,  # 0.05% height
                'color': 'yellow',
                'alpha': 0.2 + (zone['strength'] / 1000) * 0.3,
                'label': f"Confluence ({len(zone['timeframes'])} TFs)",
                'glow': True
            })

        return overlays

    def format_display_text(self) -> str:
        """
        Generate formatted text for display in GUI panel

        Returns:
            Formatted multi-line string
        """
        if not self.structure_levels:
            return "No structure data available"

        lines = []
        lines.append("═══ MULTI-TIMEFRAME STRUCTURE MAP ═══\n")

        # Show each timeframe
        for tf in ['W1', 'D1', 'H4', 'H1', 'M15']:
            if tf not in self.structure_levels:
                continue

            levels = self.structure_levels[tf]
            trend = self.trend_analysis.get(tf, 'UNKNOWN')

            # Trend emoji
            if trend == 'BULLISH':
                trend_symbol = '⬆️'
            elif trend == 'BEARISH':
                trend_symbol = '⬇️'
            else:
                trend_symbol = '➡️'

            lines.append(f"{tf}: {trend_symbol} {trend}")

            # Show key levels
            if levels['resistance']:
                top_resistance = levels['resistance'][0]
                strength_bars = '█' * int(top_resistance['strength'] / 20)
                lines.append(f"  Resistance: {top_resistance['price']:.5f} {strength_bars}")

            if levels['support']:
                top_support = levels['support'][0]
                strength_bars = '█' * int(top_support['strength'] / 20)
                lines.append(f"  Support: {top_support['price']:.5f} {strength_bars}")

            lines.append("")

        # Show top confluence zones
        if self.confluence_zones:
            lines.append("═══ CONFLUENCE ZONES ═══")
            for i, zone in enumerate(self.confluence_zones[:3], 1):
                tf_list = '+'.join(zone['timeframes'])
                lines.append(
                    f"{i}. {zone['price']:.5f} ({zone['type'].upper()}) "
                    f"[{tf_list}] - {zone['distance_pips']:.1f} pips"
                )

            # Highlight strongest
            if self.confluence_zones[0]['level_count'] >= 3:
                lines.append(f"\n⭐ STRONG CONFLUENCE at {self.confluence_zones[0]['price']:.5f}")

        return '\n'.join(lines)


# Global instance
mtf_structure_map = MTFStructureMap()
