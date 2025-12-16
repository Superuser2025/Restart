"""
Multi-Symbol Manager - Handles multiple trading symbols simultaneously

Manages:
1. Active symbols list
2. Current symbol selection per widget
3. Symbol-specific data caching
4. Symbol-specific AI predictions
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional, Any
from collections import defaultdict


class MultiSymbolManager(QObject):
    """
    Manages multiple symbols for the trading system

    Signals:
        symbol_added: Emitted when symbol is added
        symbol_removed: Emitted when symbol is removed
        active_symbol_changed: Emitted when active symbol changes
    """

    symbol_added = pyqtSignal(str)
    symbol_removed = pyqtSignal(str)
    active_symbol_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Default major pairs
        self._symbols = [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
        ]

        self._active_symbol = "EURUSD"

        # Symbol-specific data cache
        self._symbol_data = defaultdict(dict)

        # Symbol-specific AI predictions cache
        self._symbol_predictions = {}

    @property
    def symbols(self) -> List[str]:
        """Get list of all active symbols"""
        return self._symbols.copy()

    @property
    def active_symbol(self) -> str:
        """Get currently active symbol"""
        return self._active_symbol

    @active_symbol.setter
    def active_symbol(self, symbol: str):
        """Set active symbol"""
        if symbol in self._symbols:
            if self._active_symbol != symbol:
                self._active_symbol = symbol
                self.active_symbol_changed.emit(symbol)
                print(f"Active symbol changed to: {symbol}")
        else:
            print(f"Warning: Symbol {symbol} not in active list")

    def add_symbol(self, symbol: str):
        """Add a new symbol to the list"""
        symbol = symbol.upper()
        if symbol not in self._symbols:
            self._symbols.append(symbol)
            self.symbol_added.emit(symbol)
            print(f"Symbol added: {symbol}")

    def remove_symbol(self, symbol: str):
        """Remove a symbol from the list"""
        if symbol in self._symbols:
            self._symbols.remove(symbol)

            # Clear cached data
            if symbol in self._symbol_data:
                del self._symbol_data[symbol]
            if symbol in self._symbol_predictions:
                del self._symbol_predictions[symbol]

            self.symbol_removed.emit(symbol)

            # If removed symbol was active, switch to first symbol
            if self._active_symbol == symbol and self._symbols:
                self.active_symbol = self._symbols[0]

            print(f"Symbol removed: {symbol}")

    def get_symbols_for_widget(self, widget_type: str) -> List[str]:
        """
        Get list of symbols relevant for a widget type

        Some widgets show multiple symbols (e.g., correlation heatmap)
        Others show single symbol (e.g., pattern scorer)

        Args:
            widget_type: Type of widget requesting symbols

        Returns:
            List of relevant symbols
        """
        # Widgets that show multiple symbols
        multi_symbol_widgets = [
            'session_momentum',
            'correlation',
            'opportunity_scanner',
        ]

        if widget_type in multi_symbol_widgets:
            return self.symbols
        else:
            # Single symbol widgets use active symbol
            return [self.active_symbol]

    def cache_symbol_data(self, symbol: str, data_type: str, data: Any):
        """
        Cache data for a specific symbol

        Args:
            symbol: Symbol to cache data for
            data_type: Type of data (e.g., 'pattern', 'momentum', etc.)
            data: Data to cache
        """
        self._symbol_data[symbol][data_type] = data

    def get_symbol_data(self, symbol: str, data_type: str) -> Optional[Any]:
        """
        Get cached data for a specific symbol

        Args:
            symbol: Symbol to get data for
            data_type: Type of data to retrieve

        Returns:
            Cached data or None if not found
        """
        return self._symbol_data.get(symbol, {}).get(data_type)

    def cache_symbol_prediction(self, symbol: str, prediction: Dict[str, Any]):
        """
        Cache AI prediction for a specific symbol

        Args:
            symbol: Symbol to cache prediction for
            prediction: Prediction dictionary
        """
        self._symbol_predictions[symbol] = prediction

    def get_symbol_prediction(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached AI prediction for a specific symbol

        Args:
            symbol: Symbol to get prediction for

        Returns:
            Prediction dictionary or None
        """
        return self._symbol_predictions.get(symbol)

    def get_all_symbol_predictions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get predictions for all symbols

        Returns:
            Dictionary mapping symbol -> prediction
        """
        return self._symbol_predictions.copy()

    def clear_symbol_cache(self, symbol: str = None):
        """
        Clear cached data for symbol(s)

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            if symbol in self._symbol_data:
                self._symbol_data[symbol].clear()
            if symbol in self._symbol_predictions:
                del self._symbol_predictions[symbol]
        else:
            self._symbol_data.clear()
            self._symbol_predictions.clear()


# Global singleton instance
symbol_manager = MultiSymbolManager()


# Convenience functions
def get_active_symbol() -> str:
    """Get currently active symbol"""
    return symbol_manager.active_symbol


def set_active_symbol(symbol: str):
    """Set active symbol"""
    symbol_manager.active_symbol = symbol


def get_all_symbols() -> List[str]:
    """Get all active symbols"""
    return symbol_manager.symbols


def get_symbols_for_widget(widget_type: str) -> List[str]:
    """Get relevant symbols for widget"""
    return symbol_manager.get_symbols_for_widget(widget_type)


def add_symbol(symbol: str):
    """Add new symbol"""
    symbol_manager.add_symbol(symbol)


def remove_symbol(symbol: str):
    """Remove symbol"""
    symbol_manager.remove_symbol(symbol)
