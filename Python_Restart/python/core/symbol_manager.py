"""
AppleTrader Pro - Symbol Manager
Manages multi-asset symbol specifications (Forex, Stocks, Indices, Commodities, Crypto)
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from core.verbose_mode_manager import vprint


@dataclass
class SymbolSpecs:
    """Symbol specifications for position sizing and display"""
    symbol: str
    asset_class: str  # 'forex', 'stock', 'index', 'commodity', 'crypto'
    point: float  # Minimum price movement (e.g., 0.0001 for EURUSD)
    digits: int  # Decimal places (e.g., 5 for EURUSD)
    contract_size: float  # Contract size (100,000 for forex, 1 for stocks)
    tick_value: float  # Value of 1 tick in account currency
    currency_base: str  # Base currency (EUR in EURUSD)
    currency_profit: str  # Profit currency (USD in EURUSD)
    default_sl_distance: float  # Default SL distance for this asset
    description: str  # Human-readable name


class SymbolManager:
    """
    Manages symbol specifications across multiple asset classes

    Features:
    - Imports up to 100 symbols from MT5 Market Watch
    - Auto-detects asset class (forex, stock, commodity, crypto, index)
    - Provides dynamic specs for position sizing
    - Falls back to config file when MT5 unavailable
    """

    def __init__(self):
        self.symbols: Dict[str, SymbolSpecs] = {}
        self.max_symbols = 100
        self.config_file = Path(__file__).parent.parent / "config" / "symbols_config.json"

        # Load symbols from MT5 or fallback
        self.refresh_symbols()

    def refresh_symbols(self):
        """Refresh symbol list from MT5 Market Watch or fallback config"""
        vprint("[SymbolManager] Refreshing symbols...")

        if MT5_AVAILABLE and self._init_mt5():
            success = self._import_from_mt5_market_watch()
            if success:
                vprint(f"[SymbolManager] ✓ Loaded {len(self.symbols)} symbols from MT5")
                return

        # Fallback to config file
        vprint("[SymbolManager] MT5 unavailable, loading from config file...")
        self._load_from_config()
        vprint(f"[SymbolManager] ✓ Loaded {len(self.symbols)} symbols from config")

    def _init_mt5(self) -> bool:
        """Initialize MT5 connection"""
        if not mt5:
            return False

        if not mt5.initialize():
            vprint("[SymbolManager] ❌ MT5 initialization failed")
            return False

        return True

    def _import_from_mt5_market_watch(self) -> bool:
        """Import symbols from MT5 Market Watch (user's selected symbols)"""
        try:
            # Get all symbols from Market Watch (only visible ones)
            symbols_info = mt5.symbols_get()

            if not symbols_info:
                vprint("[SymbolManager] ❌ No symbols found in MT5")
                return False

            # Filter to visible symbols only (in Market Watch)
            visible_symbols = [s for s in symbols_info if s.visible]

            # Cap at max_symbols
            visible_symbols = visible_symbols[:self.max_symbols]

            vprint(f"[SymbolManager] Found {len(visible_symbols)} symbols in Market Watch")

            # Process each symbol
            for symbol_info in visible_symbols:
                try:
                    specs = self._create_specs_from_mt5(symbol_info)
                    self.symbols[specs.symbol] = specs
                    vprint(f"[SymbolManager]   → {specs.symbol} ({specs.asset_class})")
                except Exception as e:
                    vprint(f"[SymbolManager] ⚠️ Error processing {symbol_info.name}: {e}")
                    continue

            return True

        except Exception as e:
            vprint(f"[SymbolManager] ❌ Error importing from MT5: {e}")
            return False

    def _create_specs_from_mt5(self, symbol_info) -> SymbolSpecs:
        """Create SymbolSpecs from MT5 symbol_info object"""
        symbol = symbol_info.name

        # Detect asset class
        asset_class = self._detect_asset_class(symbol, symbol_info)

        # Calculate default SL distance based on asset class
        default_sl = self._calculate_default_sl(symbol, asset_class, symbol_info)

        return SymbolSpecs(
            symbol=symbol,
            asset_class=asset_class,
            point=symbol_info.point,
            digits=symbol_info.digits,
            contract_size=symbol_info.trade_contract_size,
            tick_value=symbol_info.trade_tick_value,
            currency_base=symbol_info.currency_base if hasattr(symbol_info, 'currency_base') else 'USD',
            currency_profit=symbol_info.currency_profit if hasattr(symbol_info, 'currency_profit') else 'USD',
            default_sl_distance=default_sl,
            description=symbol_info.description if hasattr(symbol_info, 'description') else symbol
        )

    def _detect_asset_class(self, symbol: str, symbol_info=None) -> str:
        """
        Auto-detect asset class from symbol name and properties

        Returns: 'forex', 'stock', 'index', 'commodity', 'crypto'
        """
        symbol_upper = symbol.upper()

        # Forex pairs (6 characters, currency codes)
        forex_currencies = ['EUR', 'USD', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
        if len(symbol) == 6:
            base = symbol[:3].upper()
            quote = symbol[3:].upper()
            if base in forex_currencies and quote in forex_currencies:
                return 'forex'

        # Indices
        if any(idx in symbol_upper for idx in ['SPX', 'NAS', 'DOW', 'DAX', 'FTSE', 'NIKKEI', 'US30', 'US100', 'US500', 'UK100', 'GER40', 'JP225']):
            return 'index'

        # Commodities
        if any(com in symbol_upper for com in ['XAU', 'XAG', 'GOLD', 'SILVER', 'OIL', 'BRENT', 'WTI', 'XAUUSD', 'XAGUSD']):
            return 'commodity'

        # Crypto
        if any(cry in symbol_upper for cry in ['BTC', 'ETH', 'LTC', 'XRP', 'ADA', 'SOL', 'DOGE']):
            return 'crypto'

        # Stocks (anything else, typically single name or short codes)
        if symbol_info and hasattr(symbol_info, 'trade_contract_size'):
            # Stocks usually have contract_size = 1 or 100
            if symbol_info.trade_contract_size in [1, 100] and len(symbol) <= 5:
                return 'stock'

        # Default to stock for short symbols
        if len(symbol) <= 5:
            return 'stock'

        return 'forex'  # Default fallback

    def _calculate_default_sl(self, symbol: str, asset_class: str, symbol_info=None) -> float:
        """Calculate appropriate default SL distance based on asset class"""

        if asset_class == 'forex':
            # 50 pips for most forex pairs
            if 'JPY' in symbol:
                return 0.50  # 50 pips for JPY pairs (2 decimals)
            else:
                return 0.0050  # 50 pips for standard pairs (4 decimals)

        elif asset_class == 'stock':
            # $2.00 for stocks
            return 2.00

        elif asset_class == 'index':
            # 20 points for indices
            return 20.0

        elif asset_class == 'commodity':
            # Gold: $5, Silver: $0.50
            if 'XAU' in symbol or 'GOLD' in symbol:
                return 5.0
            elif 'XAG' in symbol or 'SILVER' in symbol:
                return 0.50
            else:
                return 1.0  # Generic commodity

        elif asset_class == 'crypto':
            # Bitcoin: $500, others: $50
            if 'BTC' in symbol:
                return 500.0
            elif 'ETH' in symbol:
                return 100.0
            else:
                return 50.0

        return 50.0  # Generic fallback

    def _load_from_config(self):
        """Load symbols from config file (fallback when MT5 unavailable)"""
        if not self.config_file.exists():
            vprint(f"[SymbolManager] ⚠️ Config file not found: {self.config_file}")
            self._create_default_config()

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            for symbol_name, specs_dict in config.items():
                specs = SymbolSpecs(**specs_dict)
                self.symbols[symbol_name] = specs

        except Exception as e:
            vprint(f"[SymbolManager] ❌ Error loading config: {e}")
            # Create minimal fallback
            self._create_minimal_fallback()

    def _create_default_config(self):
        """Create default config file with common symbols"""
        default_symbols = {
            "EURUSD": {
                "symbol": "EURUSD",
                "asset_class": "forex",
                "point": 0.00001,
                "digits": 5,
                "contract_size": 100000.0,
                "tick_value": 1.0,
                "currency_base": "EUR",
                "currency_profit": "USD",
                "default_sl_distance": 0.0050,
                "description": "Euro vs US Dollar"
            },
            "GBPUSD": {
                "symbol": "GBPUSD",
                "asset_class": "forex",
                "point": 0.00001,
                "digits": 5,
                "contract_size": 100000.0,
                "tick_value": 1.0,
                "currency_base": "GBP",
                "currency_profit": "USD",
                "default_sl_distance": 0.0050,
                "description": "British Pound vs US Dollar"
            },
            "USDJPY": {
                "symbol": "USDJPY",
                "asset_class": "forex",
                "point": 0.001,
                "digits": 3,
                "contract_size": 100000.0,
                "tick_value": 1.0,
                "currency_base": "USD",
                "currency_profit": "JPY",
                "default_sl_distance": 0.50,
                "description": "US Dollar vs Japanese Yen"
            },
            "XAUUSD": {
                "symbol": "XAUUSD",
                "asset_class": "commodity",
                "point": 0.01,
                "digits": 2,
                "contract_size": 100.0,
                "tick_value": 1.0,
                "currency_base": "XAU",
                "currency_profit": "USD",
                "default_sl_distance": 5.0,
                "description": "Gold vs US Dollar"
            },
            "BTCUSD": {
                "symbol": "BTCUSD",
                "asset_class": "crypto",
                "point": 1.0,
                "digits": 2,
                "contract_size": 1.0,
                "tick_value": 1.0,
                "currency_base": "BTC",
                "currency_profit": "USD",
                "default_sl_distance": 500.0,
                "description": "Bitcoin vs US Dollar"
            },
            "AAPL": {
                "symbol": "AAPL",
                "asset_class": "stock",
                "point": 0.01,
                "digits": 2,
                "contract_size": 1.0,
                "tick_value": 0.01,
                "currency_base": "USD",
                "currency_profit": "USD",
                "default_sl_distance": 2.0,
                "description": "Apple Inc."
            },
            "US30": {
                "symbol": "US30",
                "asset_class": "index",
                "point": 1.0,
                "digits": 2,
                "contract_size": 10.0,
                "tick_value": 1.0,
                "currency_base": "USD",
                "currency_profit": "USD",
                "default_sl_distance": 20.0,
                "description": "Dow Jones Industrial Average"
            }
        }

        # Create config directory if needed
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(self.config_file, 'w') as f:
            json.dump(default_symbols, f, indent=2)

        vprint(f"[SymbolManager] ✓ Created default config: {self.config_file}")

    def _create_minimal_fallback(self):
        """Create minimal symbol list as last resort"""
        self.symbols['EURUSD'] = SymbolSpecs(
            symbol='EURUSD',
            asset_class='forex',
            point=0.00001,
            digits=5,
            contract_size=100000.0,
            tick_value=1.0,
            currency_base='EUR',
            currency_profit='USD',
            default_sl_distance=0.0050,
            description='Euro vs US Dollar'
        )

    # ==================== PUBLIC API ====================

    def get_symbol_specs(self, symbol: str) -> Optional[SymbolSpecs]:
        """
        Get specifications for a symbol

        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'AAPL')

        Returns:
            SymbolSpecs or None if not found
        """
        return self.symbols.get(symbol)

    def get_all_symbols(self) -> List[str]:
        """Get list of all available symbols"""
        return list(self.symbols.keys())

    def get_symbols_by_asset_class(self, asset_class: str) -> List[str]:
        """
        Get symbols filtered by asset class

        Args:
            asset_class: 'forex', 'stock', 'index', 'commodity', 'crypto'

        Returns:
            List of symbol names
        """
        return [
            symbol for symbol, specs in self.symbols.items()
            if specs.asset_class == asset_class
        ]

    def calculate_pip_value(self, symbol: str, distance: float) -> float:
        """
        Calculate pip/point value in account currency

        Args:
            symbol: Symbol name
            distance: Price distance

        Returns:
            Value in account currency
        """
        specs = self.get_symbol_specs(symbol)
        if not specs:
            return distance * 10  # Fallback

        if specs.asset_class == 'forex':
            # For forex: pip value = (point * contract_size * lots) / quote_currency_rate
            # Simplified: distance in pips * pip_value
            if 'JPY' in symbol:
                return distance * 100  # JPY pairs: 2 decimals
            else:
                return distance * 10000  # Standard pairs: 4 decimals

        elif specs.asset_class == 'stock':
            # For stocks: value = price_change * shares
            return distance

        elif specs.asset_class in ['index', 'commodity', 'crypto']:
            # Point-based assets
            return distance

        return distance

    def get_display_unit(self, symbol: str) -> str:
        """
        Get appropriate display unit for symbol

        Returns: 'pips', 'points', 'dollars', etc.
        """
        specs = self.get_symbol_specs(symbol)
        if not specs:
            return 'pips'

        if specs.asset_class == 'forex':
            return 'pips'
        elif specs.asset_class in ['index', 'commodity']:
            return 'points'
        elif specs.asset_class == 'stock':
            return 'dollars'
        elif specs.asset_class == 'crypto':
            return 'dollars'

        return 'pips'

    def format_price(self, symbol: str, price: float) -> str:
        """Format price with appropriate decimal places"""
        specs = self.get_symbol_specs(symbol)
        if not specs:
            return f"{price:.5f}"

        return f"{price:.{specs.digits}f}"

    def symbol_count(self) -> int:
        """Get total number of loaded symbols"""
        return len(self.symbols)

    def get_asset_class_summary(self) -> Dict[str, int]:
        """Get count of symbols by asset class"""
        summary = {}
        for specs in self.symbols.values():
            summary[specs.asset_class] = summary.get(specs.asset_class, 0) + 1
        return summary


# Global singleton instance
symbol_specs_manager = SymbolManager()
