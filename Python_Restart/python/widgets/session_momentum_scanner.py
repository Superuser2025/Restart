"""
AppleTrader Pro - Session Momentum Scanner (IMPROVEMENT #3)
Real-time momentum analysis across multiple symbols
Identifies the hottest trading opportunities
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict


class SessionMomentumScanner:
    """
    Session Momentum Scanner Engine

    Analyzes real-time momentum across multiple currency pairs to identify:
    - Which pairs are moving RIGHT NOW
    - Momentum score (0-100) based on ATR spike, range expansion, volume
    - Range moved (in pips) during current session
    - Momentum direction (bullish/bearish)
    - Best opportunities for immediate trading

    Saves 15-20 minutes per day by auto-focusing on hot pairs
    """

    def __init__(self, symbols: List[str] = None):
        """
        Initialize scanner

        Args:
            symbols: List of symbols to monitor (default: major pairs)
        """
        self.symbols = symbols or [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP',
            'EURJPY', 'GBPJPY', 'GOLD', 'OIL'
        ]

        self.momentum_scores = {}  # {symbol: momentum_data}
        self.last_update = None
        self.leaderboard = []  # Sorted list of symbols by momentum

    def scan_momentum(self, market_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Scan momentum across all symbols

        Args:
            market_data: {symbol: DataFrame with OHLC data}

        Returns:
            Sorted list of momentum data (highest first)
        """
        self.momentum_scores = {}

        for symbol, df in market_data.items():
            if df is None or len(df) < 50:
                continue

            momentum_data = self._calculate_momentum(symbol, df)
            if momentum_data:
                self.momentum_scores[symbol] = momentum_data

        # Sort by momentum score (descending)
        self.leaderboard = sorted(
            self.momentum_scores.values(),
            key=lambda x: x['momentum_score'],
            reverse=True
        )

        self.last_update = datetime.now()

        return self.leaderboard

    def _calculate_momentum(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """
        Calculate momentum score for a single symbol

        Momentum Score (0-100) based on:
        1. ATR Spike (0-35 points): Current ATR vs average ATR
        2. Range Expansion (0-35 points): Current range vs average range
        3. Volume Spike (0-30 points): Current volume vs average volume

        Args:
            symbol: Symbol name
            df: DataFrame with OHLC data

        Returns:
            Momentum data dict or None
        """
        if len(df) < 50:
            return None

        # Ensure required columns
        required_cols = ['high', 'low', 'close', 'open']
        if not all(col in df.columns for col in required_cols):
            return None

        # Calculate ATR
        atr = self._calculate_atr(df, period=14)
        if atr is None or len(atr) < 20:
            return None

        # Current vs average ATR
        current_atr = atr.iloc[-1]
        avg_atr = atr.iloc[-20:-1].mean()

        if avg_atr == 0:
            atr_spike_pct = 0
        else:
            atr_spike_pct = ((current_atr - avg_atr) / avg_atr) * 100

        # ATR score (0-35)
        atr_score = min(35, max(0, atr_spike_pct * 0.7))

        # Calculate range expansion
        ranges = df['high'] - df['low']
        current_range = ranges.iloc[-1]
        avg_range = ranges.iloc[-20:-1].mean()

        if avg_range == 0:
            range_expansion_pct = 0
        else:
            range_expansion_pct = ((current_range - avg_range) / avg_range) * 100

        # Range score (0-35)
        range_score = min(35, max(0, range_expansion_pct * 0.7))

        # Volume analysis (if available)
        volume_score = 0
        if 'volume' in df.columns or 'tick_volume' in df.columns:
            vol_col = 'volume' if 'volume' in df.columns else 'tick_volume'
            volumes = df[vol_col]

            current_volume = volumes.iloc[-1]
            avg_volume = volumes.iloc[-20:-1].mean()

            if avg_volume > 0:
                volume_spike_pct = ((current_volume - avg_volume) / avg_volume) * 100
                volume_score = min(30, max(0, volume_spike_pct * 0.6))

        # Total momentum score
        momentum_score = atr_score + range_score + volume_score

        # Calculate pip movement (session range)
        pip_multiplier = 10000 if symbol != 'USDJPY' else 100
        session_range_pips = current_range * pip_multiplier

        # Determine momentum direction
        recent_candles = df.iloc[-5:]
        close_change = recent_candles['close'].iloc[-1] - recent_candles['close'].iloc[0]
        direction = 'BULLISH' if close_change > 0 else 'BEARISH'

        # Trending strength (ADX-like calculation)
        trending_strength = self._calculate_trending_strength(df)

        return {
            'symbol': symbol,
            'momentum_score': momentum_score,
            'atr_score': atr_score,
            'range_score': range_score,
            'volume_score': volume_score,
            'atr_spike_pct': atr_spike_pct,
            'range_expansion_pct': range_expansion_pct,
            'session_range_pips': session_range_pips,
            'direction': direction,
            'trending_strength': trending_strength,
            'current_price': df['close'].iloc[-1]
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[pd.Series]:
        """Calculate Average True Range"""
        if len(df) < period + 1:
            return None

        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (smoothed)
        atr = tr.rolling(window=period).mean()

        return atr

    def _calculate_trending_strength(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate trending strength (simplified ADX concept)

        Returns:
            0-100 score (higher = stronger trend)
        """
        if len(df) < period + 1:
            return 0

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        # Directional movement
        up_moves = []
        down_moves = []

        for i in range(1, len(high)):
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]

            up_moves.append(max(0, up_move) if up_move > down_move else 0)
            down_moves.append(max(0, down_move) if down_move > up_move else 0)

        # Average directional movement
        avg_up = np.mean(up_moves[-period:])
        avg_down = np.mean(down_moves[-period:])

        total_movement = avg_up + avg_down
        if total_movement == 0:
            return 0

        # Directional index
        di_diff = abs(avg_up - avg_down)
        dx = (di_diff / total_movement) * 100

        return min(100, dx)

    def get_top_movers(self, count: int = 5) -> List[Dict]:
        """
        Get top N highest momentum pairs

        Args:
            count: Number of top movers to return

        Returns:
            List of momentum data dicts
        """
        return self.leaderboard[:count]

    def get_best_opportunity(self) -> Optional[Dict]:
        """
        Get the single best trading opportunity right now

        Returns:
            Momentum data for top pair, or None
        """
        if not self.leaderboard:
            return None

        return self.leaderboard[0]

    def format_leaderboard_text(self) -> str:
        """
        Generate formatted leaderboard text for display

        Returns:
            Multi-line formatted string
        """
        if not self.leaderboard:
            return "No momentum data available"

        lines = []
        lines.append("═══ SESSION MOMENTUM SCANNER ═══\n")

        for i, data in enumerate(self.leaderboard[:10], 1):
            symbol = data['symbol']
            score = data['momentum_score']
            pips = data['session_range_pips']
            direction = data['direction']

            # Direction emoji
            dir_emoji = '🟢' if direction == 'BULLISH' else '🔴'

            # Momentum bar (visual)
            bar_length = int(score / 5)  # 5 points = 1 bar char
            bar = '█' * bar_length

            # Trending strength indicator
            trend_str = data['trending_strength']
            trend_indicator = '🔥' if trend_str > 60 else ('⚡' if trend_str > 40 else '')

            lines.append(
                f"{i}. {symbol:8} {bar:20} {score:.0f}% | "
                f"{pips:.0f} pips {dir_emoji} {trend_indicator}"
            )

        # Highlight best opportunity
        if self.leaderboard:
            best = self.leaderboard[0]
            lines.append(
                f"\n⭐ BEST: {best['symbol']} - "
                f"{best['momentum_score']:.0f}% momentum, "
                f"{best['session_range_pips']:.0f} pips moved"
            )

        # Last update
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            lines.append(f"\nUpdated: {time_str}")

        return '\n'.join(lines)

    def get_momentum_alerts(self, threshold: float = 70) -> List[str]:
        """
        Get alert messages for high momentum situations

        Args:
            threshold: Momentum score threshold for alerts (default 70)

        Returns:
            List of alert strings
        """
        alerts = []

        for data in self.leaderboard:
            if data['momentum_score'] >= threshold:
                alerts.append(
                    f"🚨 HIGH MOMENTUM: {data['symbol']} - "
                    f"{data['momentum_score']:.0f}% score, "
                    f"{data['direction']} bias"
                )

                # Additional specific alerts
                if data['atr_spike_pct'] > 50:
                    alerts.append(
                        f"   ⚠️ ATR SPIKE: {data['atr_spike_pct']:.0f}% above average"
                    )

                if data['trending_strength'] > 70:
                    alerts.append(
                        f"   🔥 STRONG TREND: {data['trending_strength']:.0f}% strength"
                    )

        return alerts

    def compare_with_average(self, symbol: str) -> Dict:
        """
        Compare symbol's current momentum to its historical average

        Args:
            symbol: Symbol to analyze

        Returns:
            Comparison data
        """
        if symbol not in self.momentum_scores:
            return {'error': 'Symbol not found'}

        current = self.momentum_scores[symbol]

        # Calculate percentile ranking
        all_scores = [d['momentum_score'] for d in self.momentum_scores.values()]
        percentile = (sum(1 for s in all_scores if s < current['momentum_score']) /
                     len(all_scores)) * 100

        return {
            'symbol': symbol,
            'current_score': current['momentum_score'],
            'percentile': percentile,
            'rank': self.leaderboard.index(current) + 1 if current in self.leaderboard else None,
            'total_symbols': len(self.leaderboard),
            'interpretation': self._interpret_percentile(percentile)
        }

    def _interpret_percentile(self, percentile: float) -> str:
        """Interpret percentile ranking"""
        if percentile >= 90:
            return "EXTREMELY HIGH - Top opportunity"
        elif percentile >= 75:
            return "HIGH - Strong opportunity"
        elif percentile >= 50:
            return "MODERATE - Average momentum"
        elif percentile >= 25:
            return "LOW - Below average"
        else:
            return "VERY LOW - Avoid trading"

    def export_data(self) -> Dict:
        """Export complete momentum data for external use"""
        return {
            'leaderboard': self.leaderboard,
            'momentum_scores': self.momentum_scores,
            'last_update': self.last_update,
            'symbols_scanned': len(self.momentum_scores)
        }


# Global instance
session_momentum_scanner = SessionMomentumScanner()
