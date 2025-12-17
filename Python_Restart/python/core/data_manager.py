"""
AppleTrader Pro - Data Manager
Manages real-time market data buffering and synchronization
"""

from datetime import datetime
from typing import Optional, Dict, List
from collections import deque
import pandas as pd

from core.risk_manager import risk_manager


class MarketDataBuffer:
    """
    Circular buffer for candlestick data
    Efficiently stores and updates real-time candles
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.candles = deque(maxlen=max_size)
        self.symbol = ""
        self.timeframe = ""
        self.last_update = None

    def update(self, candles_df: pd.DataFrame, symbol: str, timeframe: str):
        """Update buffer with new candle data"""
        self.symbol = symbol
        self.timeframe = timeframe
        self.last_update = datetime.now()

        # Convert DataFrame rows to list of dicts
        new_candles = candles_df.to_dict('records')

        # Replace all candles (for now - can optimize later with incremental updates)
        self.candles.clear()
        self.candles.extend(new_candles)

    def get_latest(self, count: int = 200) -> List[Dict]:
        """Get latest N candles"""
        return list(self.candles)[-count:] if self.candles else []

    def get_latest_df(self, count: int = 200) -> Optional[pd.DataFrame]:
        """Get latest N candles as DataFrame"""
        latest = self.get_latest(count)
        if not latest:
            return None
        return pd.DataFrame(latest)

    def get_last_candle(self) -> Optional[Dict]:
        """Get the most recent candle"""
        return self.candles[-1] if self.candles else None


class PatternBuffer:
    """
    Buffer for detected patterns
    Stores pattern information with timestamps
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.patterns = deque(maxlen=max_size)

    def add_pattern(self, pattern: Dict):
        """Add a new pattern"""
        pattern['detected_at'] = datetime.now()
        self.patterns.append(pattern)

    def get_active_patterns(self) -> List[Dict]:
        """Get all active (non-expired) patterns"""
        # For now, return all patterns
        # Can add expiry logic later
        return list(self.patterns)

    def clear(self):
        """Clear all patterns"""
        self.patterns.clear()


class ZoneBuffer:
    """
    Buffer for trading zones (FVGs, Order Blocks, Liquidity)
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.fvgs = deque(maxlen=max_size)
        self.order_blocks = deque(maxlen=max_size)
        self.liquidity_zones = deque(maxlen=max_size)

    def update_fvgs(self, fvgs: List[Dict]):
        """Update FVG zones"""
        self.fvgs.clear()
        self.fvgs.extend(fvgs)

    def update_order_blocks(self, order_blocks: List[Dict]):
        """Update Order Block zones"""
        self.order_blocks.clear()
        self.order_blocks.extend(order_blocks)

    def update_liquidity(self, liquidity: List[Dict]):
        """Update Liquidity zones"""
        self.liquidity_zones.clear()
        self.liquidity_zones.extend(liquidity)

    def get_all_zones(self) -> Dict:
        """Get all zones"""
        return {
            'fvgs': list(self.fvgs),
            'order_blocks': list(self.order_blocks),
            'liquidity': list(self.liquidity_zones),
        }


class DataManager:
    """
    Central data management system
    Coordinates all market data buffers and state
    """

    def __init__(self):
        # Buffers
        self.candle_buffer = MarketDataBuffer(max_size=1000)
        self.pattern_buffer = PatternBuffer(max_size=100)
        self.zone_buffer = ZoneBuffer(max_size=100)

        # Current market state
        self.current_price = {
            'bid': 0.0,
            'ask': 0.0,
            'last': 0.0,
            'spread': 0.0,
        }

        # Market analysis state
        self.market_state = {
            'regime': 'UNKNOWN',           # TRENDING, RANGING, CHOPPY
            'bias': 'NEUTRAL',             # BULLISH, BEARISH, NEUTRAL
            'session': 'UNKNOWN',          # LONDON, NY, ASIAN
            'volatility': 'NORMAL',        # LOW, NORMAL, HIGH
        }

        # Filter status
        self.filter_status = {
            'volume_ok': False,
            'spread_ok': False,
            'session_ok': False,
            'news_ok': False,
            'mtf_ok': False,
            'correlation_ok': False,
        }

        # Trade decision
        self.trade_decision = {
            'decision': 'WAIT',            # ENTER, SKIP, WAIT
            'confluence': 0,
            'required': 3,
            'primary_reason': '',
            'explanation': '',
        }

        # Active pattern
        self.active_pattern = None

        # Indicators
        self.indicators = {
            'ema_200': 0.0,
            'atr_14': 0.0,
            'rsi_14': 0.0,
        }

        # Positions
        self.positions = []
        self.position_count = 0  # Separate count from EA

        # Account info
        self.account = {
            'balance': 0.0,
            'equity': 0.0,
            'profit': 0.0,
            'daily_pnl': 0.0,
            'margin': 0.0,
            'margin_free': 0.0,
            'margin_level': 0.0,
            'currency': 'USD',
        }

        # ML data
        self.ml_data = {
            'enabled': False,
            'probability': 0.0,
            'confidence': 0.0,
            'signal': 'WAIT',
            'sample_count': 0,
        }

        # Last update timestamp
        self.last_update = None

        # Store last raw data from EA for debugging
        self.last_raw_data = {}

    def update_from_mt5_data(self, data: Dict):
        """
        Update all buffers from MT5 data (either from API or IPC file)

        Args:
            data: Market data dictionary from MT5
        """
        print("=" * 80)
        print("📊 [DATA MANAGER] RECEIVING REAL MT5 DATA")
        if 'symbol' in data:
            print(f"   Symbol: {data['symbol']}")
        if 'account_balance' in data:
            print(f"   ✓ REAL Account Balance: ${data['account_balance']:,.2f}")
        if 'account_equity' in data:
            print(f"   ✓ REAL Account Equity: ${data['account_equity']:,.2f}")
        print("=" * 80)

        try:
            timestamp = data.get('timestamp')
            if timestamp:
                # Handle both string ISO format and integer Unix timestamp
                if isinstance(timestamp, str):
                    self.last_update = datetime.fromisoformat(timestamp)
                elif isinstance(timestamp, (int, float)):
                    self.last_update = datetime.fromtimestamp(timestamp)
                else:
                    self.last_update = datetime.now()

            # Update price (EA sends bid/ask directly, not nested)
            if 'symbol' in data:
                self.current_price['symbol'] = data['symbol']
            if 'bid' in data:
                self.current_price['bid'] = data['bid']
            if 'ask' in data:
                self.current_price['ask'] = data['ask']
            if 'spread' in data:
                self.current_price['spread'] = data['spread']
            if 'timeframe' in data:
                self.current_price['timeframe'] = data['timeframe']

            # Update market state (EA sends these directly, not nested)
            if 'bias' in data:
                self.market_state['bias'] = data['bias']
            if 'regime' in data:
                self.market_state['regime'] = data['regime']
            if 'session' in data:
                self.market_state['session'] = data['session']
            if 'volatility' in data:
                self.market_state['volatility'] = data['volatility']

            # Update filter status (EA sends filters as array of 20 bools)
            if 'filters' in data:
                self.filter_status = data['filters']

            # Update trade decision fields
            if 'passed_filters' in data:
                self.trade_decision['confluence'] = data.get('passed_filters', 0)
            if 'confluence' in data:
                self.trade_decision['confluence'] = data['confluence']

            # Update active pattern (EA sends 'pattern' directly as string)
            if 'pattern' in data:
                self.active_pattern = data['pattern']

            # Update zones
            if 'zones' in data:
                zones = data['zones']
                if 'fvgs' in zones:
                    self.zone_buffer.update_fvgs(zones['fvgs'])
                if 'order_blocks' in zones:
                    self.zone_buffer.update_order_blocks(zones['order_blocks'])
                if 'liquidity' in zones:
                    self.zone_buffer.update_liquidity(zones['liquidity'])

            # Update indicators
            if 'indicators' in data:
                self.indicators.update(data['indicators'])

            # Update positions
            if 'positions' in data:
                positions_data = data['positions']
                # EA sends position count as int, not a list
                if isinstance(positions_data, (int, float)):
                    self.position_count = int(positions_data)
                elif isinstance(positions_data, list):
                    self.positions = positions_data
                    self.position_count = len(positions_data)

            # Update account (EA sends these directly, not nested)
            if 'account_balance' in data:
                self.account['balance'] = data['account_balance']
            if 'account_equity' in data:
                self.account['equity'] = data['account_equity']
            if 'total_pnl' in data:
                self.account['profit'] = data['total_pnl']
            if 'today_pnl' in data:
                self.account['daily_pnl'] = data['today_pnl']

            # Update ML data (EA sends these directly, not nested)
            if 'ml_enabled' in data:
                self.ml_data['enabled'] = data['ml_enabled']
            if 'ml_signal' in data:
                self.ml_data['signal'] = data['ml_signal']
            if 'ml_probability' in data:
                self.ml_data['probability'] = data['ml_probability']
            if 'ml_confidence' in data:
                self.ml_data['confidence'] = data['ml_confidence']

            # Store raw EA data for debugging
            self.last_raw_data = data

            # ========================================
            # CRITICAL: Update Risk Manager (USER REQUIREMENT - Symbol Position Limits)
            # ========================================
            try:
                # Update account tracking
                balance = self.account.get('balance', 0.0)
                equity = self.account.get('equity', 0.0)
                daily_pnl = self.account.get('daily_pnl', 0.0)

                if balance > 0:
                    risk_manager.update_account(balance, equity, daily_pnl)

                # Update position tracking (CRITICAL - enforces MaxLotsPerSymbol = 0.10)
                if self.positions:
                    risk_manager.update_from_positions(self.positions)

            except Exception as risk_error:
                pass

        except Exception as e:
            pass

    def update_candles(self, candles_df: pd.DataFrame, symbol: str, timeframe: str):
        """Update candle buffer"""
        self.candle_buffer.update(candles_df, symbol, timeframe)

    def get_candles(self, count: int = 200) -> List[Dict]:
        """Get latest candles"""
        return self.candle_buffer.get_latest(count)

    def get_candles_df(self, count: int = 200) -> Optional[pd.DataFrame]:
        """Get latest candles as DataFrame"""
        return self.candle_buffer.get_latest_df(count)

    def get_latest_price(self) -> Dict:
        """Get latest price data"""
        return self.current_price.copy()

    def get_market_state(self) -> Dict:
        """Get current market state"""
        result = {
            **self.market_state,
            'decision': self.trade_decision,
            'pattern': self.active_pattern,
        }

        # Handle filter_status as either dict or list
        if isinstance(self.filter_status, dict):
            result.update(self.filter_status)
        else:
            result['filters'] = self.filter_status

        return result

    def get_zones(self) -> Dict:
        """Get all trading zones"""
        return self.zone_buffer.get_all_zones()

    def get_positions(self) -> List[Dict]:
        """Get open positions"""
        return self.positions.copy()

    def get_position_count(self) -> int:
        """Get number of open positions"""
        return self.position_count

    def get_account_summary(self) -> Dict:
        """Get account summary"""
        return self.account.copy()

    def get_ml_status(self) -> Dict:
        """Get ML status and predictions"""
        return self.ml_data.copy()

    def is_data_fresh(self, max_age_seconds: int = 30) -> bool:
        """Check if data is recent"""
        if self.last_update is None:
            return False

        age = (datetime.now() - self.last_update).total_seconds()
        return age <= max_age_seconds


# Global data manager instance
data_manager = DataManager()
