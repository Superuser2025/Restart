"""
AppleTrader Pro - MT5 Connector
Reads JSON data exported by MT5 EA and provides it to GUI widgets
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import pandas as pd
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class MT5Connector(QObject):
    """
    Connects to MT5 EA via JSON file communication

    The EA exports data to: %APPDATA%\MetaQuotes\Terminal\Common\Files\AppleTrader\
    """

    # Signals
    data_updated = pyqtSignal(dict)  # Emits when new data available
    connection_status_changed = pyqtSignal(bool)  # Emits connection status
    error_occurred = pyqtSignal(str)  # Emits error messages

    def __init__(self):
        super().__init__()

        # Find MT5 data directory
        self.data_dir = self._find_mt5_data_dir()
        self.market_data_file = None
        self.commands_file = None

        if self.data_dir:
            self.market_data_file = self.data_dir / "market_data.json"
            self.commands_file = self.data_dir / "commands.json"

        # Data cache
        self.last_data = {}
        self.last_file_modified = None
        self.is_connected = False

        # Connection stability - prevent flapping
        self.connection_fail_count = 0
        self.connection_required_fails = 5  # Must fail 5 times before disconnecting (5 seconds)

        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Check every 1 second

    def _find_mt5_data_dir(self) -> Optional[Path]:
        """Find MT5 data directory"""
        # Try common locations
        appdata = os.getenv('APPDATA')

        if not appdata:
            return None

        # Standard MT5 location
        mt5_common = Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / "AppleTrader"

        if mt5_common.exists():
            return mt5_common

        # Try to create directory
        try:
            mt5_common.mkdir(parents=True, exist_ok=True)
            return mt5_common
        except:
            return None

    def update_data(self):
        """Check for and load new data from MT5 (with connection stability)"""
        if not self.market_data_file or not self.market_data_file.exists():
            # File missing - increment fail counter
            self.connection_fail_count += 1

            # Only disconnect after sustained failure (5+ consecutive checks)
            if self.is_connected and self.connection_fail_count >= self.connection_required_fails:
                self.is_connected = False
                self.connection_status_changed.emit(False)
                print(f"[MT5] Disconnected after {self.connection_fail_count} failed checks")
            return

        try:
            # Check if file was modified
            modified = self.market_data_file.stat().st_mtime

            if modified == self.last_file_modified:
                # File exists but hasn't been modified - still good, reset fail counter
                self.connection_fail_count = 0
                return  # No changes

            self.last_file_modified = modified

            # Read JSON data
            with open(self.market_data_file, 'r') as f:
                data = json.load(f)

            self.last_data = data

            # Reset fail counter on successful read
            self.connection_fail_count = 0

            # Update connection status
            if not self.is_connected:
                self.is_connected = True
                self.connection_status_changed.emit(True)
                print(f"[MT5] Connected - market_data.json found and readable")

            # Emit data update
            self.data_updated.emit(data)

        except Exception as e:
            # Read error - increment fail counter
            self.connection_fail_count += 1

            self.error_occurred.emit(f"Error reading MT5 data: {str(e)}")

            # Only disconnect after sustained failure
            if self.is_connected and self.connection_fail_count >= self.connection_required_fails:
                self.is_connected = False
                self.connection_status_changed.emit(False)
                print(f"[MT5] Disconnected after {self.connection_fail_count} read errors")

    def get_candles(self, symbol: str, timeframe: str, count: int = 200) -> Optional[pd.DataFrame]:
        """
        Get candle data for symbol and timeframe

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M15, H1, H4, D1, W1)
            count: Number of candles

        Returns:
            DataFrame with OHLC data or None
        """
        if not self.last_data:
            return None

        # Look for candles in data
        candles_key = f"candles_{symbol}_{timeframe}"

        if candles_key not in self.last_data:
            return None

        candles = self.last_data[candles_key]

        if not candles:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(candles)

        # Ensure required columns
        required_cols = ['time', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return None

        # Convert time to datetime
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])

        return df.tail(count)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        if not self.last_data:
            return None

        price_key = f"price_{symbol}"
        return self.last_data.get(price_key)

    def get_positions(self) -> List[Dict]:
        """Get open positions"""
        if not self.last_data:
            return []

        return self.last_data.get('positions', [])

    def get_zones(self, symbol: str) -> Dict:
        """
        Get trading zones (FVG, OB, Liquidity)

        Returns:
            {fvgs: [...], order_blocks: [...], liquidity: [...]}
        """
        if not self.last_data:
            return {'fvgs': [], 'order_blocks': [], 'liquidity': []}

        zones_key = f"zones_{symbol}"
        return self.last_data.get(zones_key, {'fvgs': [], 'order_blocks': [], 'liquidity': []})

    def get_ml_data(self, symbol: str) -> Optional[Dict]:
        """Get ML prediction data"""
        if not self.last_data:
            return None

        ml_key = f"ml_{symbol}"
        return self.last_data.get(ml_key)

    def send_command(self, command: str, parameters: Dict = None):
        """
        Send command to MT5 EA

        Args:
            command: Command name
            parameters: Command parameters
        """
        if not self.commands_file:
            return

        try:
            command_data = {
                'command': command,
                'parameters': parameters or {},
                'timestamp': datetime.now().isoformat()
            }

            with open(self.commands_file, 'w') as f:
                json.dump(command_data, f, indent=2)

        except Exception as e:
            self.error_occurred.emit(f"Error sending command: {str(e)}")

    def get_all_symbols_data(self) -> Dict[str, pd.DataFrame]:
        """
        Get candle data for all available symbols

        Returns:
            {symbol: DataFrame}
        """
        if not self.last_data:
            return {}

        symbols_data = {}

        # Look for all candles_ keys
        for key in self.last_data.keys():
            if key.startswith('candles_'):
                parts = key.split('_')
                if len(parts) >= 3:
                    symbol = parts[1]
                    timeframe = parts[2]

                    if timeframe == 'H4':  # Use H4 as default
                        df = self.get_candles(symbol, timeframe)
                        if df is not None:
                            symbols_data[symbol] = df

        return symbols_data

    def is_connection_active(self) -> bool:
        """Check if connection to MT5 is active"""
        return self.is_connected

    def get_data_directory(self) -> Optional[Path]:
        """Get MT5 data directory path"""
        return self.data_dir


# Global instance
mt5_connector = MT5Connector()
