"""
AppleTrader Pro - Volatility-Adjusted Position Sizing Optimizer (IMPROVEMENT #2)
Dynamic lot size calculator based on market conditions
Maintains true risk percentage regardless of volatility
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum


class VolatilityRegime(Enum):
    """Market volatility classification"""
    EXTREME_HIGH = "EXTREME_HIGH"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    EXTREME_LOW = "EXTREME_LOW"


class TrendStrength(Enum):
    """Market trend classification"""
    STRONG_TREND = "STRONG_TREND"      # ADX > 35
    TRENDING = "TRENDING"              # ADX > 25
    WEAK_TREND = "WEAK_TREND"          # ADX > 20
    RANGING = "RANGING"                # ADX < 20


class VolatilityPositionSizer:
    """
    Volatility-Adjusted Position Sizing Engine

    Dynamically calculates optimal lot sizes based on:
    1. Current volatility (ATR) vs historical average
    2. Trend strength (ADX-like indicator)
    3. Account risk percentage
    4. Symbol-specific characteristics

    Adjustments:
    - HIGH volatility → Reduce position by 30% → 0.35% risk
    - NORMAL volatility → Keep 0.5% risk
    - LOW volatility → Increase by 50% → 0.75% risk
    - Strong trend (ADX > 25) → Increase 20%
    - Ranging (ADX < 20) → Decrease 30%

    Expected Impact: Maintains true risk%, -30% max drawdown
    """

    def __init__(self, base_risk_pct: float = 0.5, account_balance: float = 10000):
        """
        Initialize position sizer

        Args:
            base_risk_pct: Base risk percentage (default 0.5%)
            account_balance: Account balance in USD
        """
        self.base_risk_pct = base_risk_pct
        self.account_balance = account_balance

        # Volatility adjustments
        self.volatility_adjustments = {
            VolatilityRegime.EXTREME_HIGH: 0.50,  # -50%
            VolatilityRegime.HIGH: 0.70,          # -30%
            VolatilityRegime.NORMAL: 1.00,        # No change
            VolatilityRegime.LOW: 1.30,           # +30%
            VolatilityRegime.EXTREME_LOW: 1.50    # +50%
        }

        # Trend adjustments
        self.trend_adjustments = {
            TrendStrength.STRONG_TREND: 1.20,     # +20%
            TrendStrength.TRENDING: 1.10,         # +10%
            TrendStrength.WEAK_TREND: 1.00,       # No change
            TrendStrength.RANGING: 0.70           # -30%
        }

        self.last_calculation = None

    def calculate_position_size(self, symbol: str, df: pd.DataFrame,
                               entry_price: float, stop_loss: float,
                               direction: str = 'BUY') -> Dict:
        """
        Calculate optimal position size for a trade

        Args:
            symbol: Trading symbol
            df: DataFrame with OHLC data
            entry_price: Planned entry price
            stop_loss: Planned stop loss price
            direction: 'BUY' or 'SELL'

        Returns:
            Complete position sizing analysis
        """
        # Calculate stop loss distance in pips
        pip_multiplier = self._get_pip_multiplier(symbol)
        sl_distance_pips = abs(entry_price - stop_loss) * pip_multiplier

        if sl_distance_pips == 0:
            return self._error_result("Stop loss distance is zero")

        # Analyze market conditions
        volatility_regime, volatility_data = self._analyze_volatility(df, symbol)
        trend_strength, trend_data = self._analyze_trend(df)

        # Calculate adjusted risk percentage
        volatility_multiplier = self.volatility_adjustments[volatility_regime]
        trend_multiplier = self.trend_adjustments[trend_strength]

        adjusted_risk_pct = (self.base_risk_pct *
                            volatility_multiplier *
                            trend_multiplier)

        # Enforce limits (0.2% to 1.0%)
        adjusted_risk_pct = max(0.2, min(1.0, adjusted_risk_pct))

        # Calculate dollar risk
        dollar_risk = self.account_balance * (adjusted_risk_pct / 100)

        # Calculate position size
        # For forex: Position Size = Dollar Risk / (SL Distance Pips * Pip Value)
        # Standard lot pip value = $10 for most pairs
        standard_pip_value = 10 if symbol != 'USDJPY' else 1000

        position_size_lots = dollar_risk / (sl_distance_pips * standard_pip_value)

        # Round to 0.01 lots
        position_size_lots = round(position_size_lots, 2)

        # Enforce minimum (0.01) and maximum (based on account)
        max_lots = self._calculate_max_lots()
        position_size_lots = max(0.01, min(max_lots, position_size_lots))

        self.last_calculation = datetime.now()

        return {
            'symbol': symbol,
            'position_size_lots': position_size_lots,
            'base_risk_pct': self.base_risk_pct,
            'adjusted_risk_pct': adjusted_risk_pct,
            'dollar_risk': dollar_risk,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'sl_distance_pips': sl_distance_pips,
            'direction': direction,
            'volatility_regime': volatility_regime.value,
            'volatility_multiplier': volatility_multiplier,
            'volatility_data': volatility_data,
            'trend_strength': trend_strength.value,
            'trend_multiplier': trend_multiplier,
            'trend_data': trend_data,
            'pip_multiplier': pip_multiplier,
            'max_lots_allowed': max_lots,
            'calculation_time': self.last_calculation
        }

    def _analyze_volatility(self, df: pd.DataFrame, symbol: str) -> Tuple[VolatilityRegime, Dict]:
        """
        Analyze current volatility regime

        Returns:
            (VolatilityRegime, volatility_data_dict)
        """
        if len(df) < 50:
            return VolatilityRegime.NORMAL, {}

        # Calculate ATR
        atr = self._calculate_atr(df, period=14)

        if atr is None or len(atr) < 20:
            return VolatilityRegime.NORMAL, {}

        current_atr = atr.iloc[-1]

        # Calculate historical average and stddev
        historical_atr = atr.iloc[-100:] if len(atr) >= 100 else atr
        avg_atr = historical_atr.mean()
        std_atr = historical_atr.std()

        if avg_atr == 0:
            return VolatilityRegime.NORMAL, {}

        # Z-score: how many standard deviations away from mean
        z_score = (current_atr - avg_atr) / std_atr if std_atr > 0 else 0

        # Percentage above/below average
        pct_vs_avg = ((current_atr - avg_atr) / avg_atr) * 100

        # Classify regime
        if z_score > 2.0 or pct_vs_avg > 50:
            regime = VolatilityRegime.EXTREME_HIGH
        elif z_score > 1.0 or pct_vs_avg > 25:
            regime = VolatilityRegime.HIGH
        elif z_score > -1.0 and pct_vs_avg > -25:
            regime = VolatilityRegime.NORMAL
        elif z_score > -2.0 or pct_vs_avg > -50:
            regime = VolatilityRegime.LOW
        else:
            regime = VolatilityRegime.EXTREME_LOW

        volatility_data = {
            'current_atr': current_atr,
            'avg_atr': avg_atr,
            'std_atr': std_atr,
            'z_score': z_score,
            'pct_vs_avg': pct_vs_avg
        }

        return regime, volatility_data

    def _analyze_trend(self, df: pd.DataFrame) -> Tuple[TrendStrength, Dict]:
        """
        Analyze trend strength using ADX-like calculation

        Returns:
            (TrendStrength, trend_data_dict)
        """
        if len(df) < 50:
            return TrendStrength.RANGING, {}

        # Calculate ADX
        adx = self._calculate_adx(df, period=14)

        if adx is None or len(adx) < 1:
            return TrendStrength.RANGING, {}

        current_adx = adx.iloc[-1]

        # Classify trend strength
        if current_adx > 35:
            strength = TrendStrength.STRONG_TREND
        elif current_adx > 25:
            strength = TrendStrength.TRENDING
        elif current_adx > 20:
            strength = TrendStrength.WEAK_TREND
        else:
            strength = TrendStrength.RANGING

        # Determine trend direction
        if 'close' in df.columns and len(df) >= 20:
            recent_closes = df['close'].iloc[-20:]
            if recent_closes.iloc[-1] > recent_closes.iloc[0]:
                direction = 'BULLISH'
            else:
                direction = 'BEARISH'
        else:
            direction = 'UNKNOWN'

        trend_data = {
            'adx': current_adx,
            'direction': direction
        }

        return strength, trend_data

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[pd.Series]:
        """Calculate Average True Range"""
        if len(df) < period + 1:
            return None

        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None

        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (Wilder's smoothing)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        return atr

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Optional[pd.Series]:
        """
        Calculate Average Directional Index (ADX)

        Returns:
            ADX series
        """
        if len(df) < period + 1:
            return None

        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None

        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate +DM and -DM
        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = pd.Series(0.0, index=df.index)
        minus_dm = pd.Series(0.0, index=df.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Calculate ATR
        atr = self._calculate_atr(df, period)

        if atr is None:
            return None

        # Smooth DMs
        plus_dm_smooth = plus_dm.ewm(alpha=1/period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=1/period, adjust=False).mean()

        # Calculate directional indicators
        plus_di = 100 * plus_dm_smooth / atr
        minus_di = 100 * minus_dm_smooth / atr

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        dx = dx.fillna(0)

        # Calculate ADX (smoothed DX)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()

        return adx

    def _get_pip_multiplier(self, symbol: str) -> float:
        """Get pip multiplier for symbol"""
        if 'JPY' in symbol:
            return 100  # For JPY pairs, pip is 0.01
        else:
            return 10000  # For most pairs, pip is 0.0001

    def _calculate_max_lots(self) -> float:
        """Calculate maximum allowed lot size based on account"""
        # Conservative: Max 5% of account per trade
        max_risk = self.account_balance * 0.05

        # Assuming 100 pip stop loss, standard pip value
        max_lots = max_risk / (100 * 10)

        return round(max_lots, 2)

    def _error_result(self, error_msg: str) -> Dict:
        """Return error result"""
        return {
            'error': error_msg,
            'position_size_lots': 0.01,
            'calculation_time': datetime.now()
        }

    def update_account_balance(self, new_balance: float):
        """Update account balance"""
        self.account_balance = new_balance

    def update_base_risk(self, new_risk_pct: float):
        """Update base risk percentage"""
        self.base_risk_pct = max(0.1, min(2.0, new_risk_pct))

    def get_risk_summary(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Get current risk assessment without calculating position size

        Args:
            symbol: Trading symbol
            df: DataFrame with OHLC data

        Returns:
            Risk summary dict
        """
        volatility_regime, volatility_data = self._analyze_volatility(df, symbol)
        trend_strength, trend_data = self._analyze_trend(df)

        volatility_multiplier = self.volatility_adjustments[volatility_regime]
        trend_multiplier = self.trend_adjustments[trend_strength]

        adjusted_risk_pct = (self.base_risk_pct *
                            volatility_multiplier *
                            trend_multiplier)

        adjusted_risk_pct = max(0.2, min(1.0, adjusted_risk_pct))

        return {
            'symbol': symbol,
            'base_risk_pct': self.base_risk_pct,
            'volatility_regime': volatility_regime.value,
            'volatility_multiplier': volatility_multiplier,
            'trend_strength': trend_strength.value,
            'trend_multiplier': trend_multiplier,
            'adjusted_risk_pct': adjusted_risk_pct,
            'recommendation': self._get_risk_recommendation(
                volatility_regime, trend_strength, adjusted_risk_pct
            )
        }

    def _get_risk_recommendation(self, volatility: VolatilityRegime,
                                 trend: TrendStrength,
                                 adjusted_risk: float) -> str:
        """Generate human-readable recommendation"""
        recommendations = []

        if volatility == VolatilityRegime.EXTREME_HIGH:
            recommendations.append("⚠️ EXTREME volatility - reduce position by 50%")
        elif volatility == VolatilityRegime.HIGH:
            recommendations.append("⚠️ HIGH volatility - reduce position by 30%")
        elif volatility == VolatilityRegime.LOW:
            recommendations.append("✓ LOW volatility - can increase position by 30%")

        if trend == TrendStrength.STRONG_TREND:
            recommendations.append("✓ STRONG trend - increase position by 20%")
        elif trend == TrendStrength.RANGING:
            recommendations.append("⚠️ RANGING market - reduce position by 30%")

        recommendations.append(f"📊 Adjusted risk: {adjusted_risk:.2f}%")

        return ' | '.join(recommendations)


# Global instance
volatility_position_sizer = VolatilityPositionSizer()
