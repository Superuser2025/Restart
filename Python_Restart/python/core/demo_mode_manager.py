"""
Demo Mode Manager - Global demo/live mode toggle for all widgets

Provides:
1. Global demo mode state (demo vs live)
2. One-shot toggle to switch all widgets
3. Demo data generation for testing
4. Multi-symbol support
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any
import random
from datetime import datetime, timedelta


class DemoModeManager(QObject):
    """
    Manages demo/live mode state for entire application

    Signals:
        mode_changed: Emitted when mode switches (True=demo, False=live)
    """

    mode_changed = pyqtSignal(bool)  # True = demo mode, False = live mode

    def __init__(self):
        super().__init__()
        self._demo_mode = True  # Start in demo mode for safety
        self._symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]

    @property
    def demo_mode(self) -> bool:
        """Get current mode (True=demo, False=live)"""
        return self._demo_mode

    @demo_mode.setter
    def demo_mode(self, value: bool):
        """Set demo mode and notify all widgets"""
        if self._demo_mode != value:
            self._demo_mode = value
            self.mode_changed.emit(value)
            print(f"{'DEMO' if value else 'LIVE'} MODE ACTIVATED")

    def toggle_mode(self):
        """Toggle between demo and live mode"""
        self.demo_mode = not self._demo_mode

    def is_demo(self) -> bool:
        """Check if in demo mode"""
        return self._demo_mode

    def is_live(self) -> bool:
        """Check if in live mode"""
        return not self._demo_mode

    # ============================================================
    # DEMO DATA GENERATORS (for testing)
    # ============================================================

    def generate_demo_session_momentum(self, symbols: List[str] = None) -> List[Dict]:
        """Generate demo data for Session Momentum Scanner"""
        if symbols is None:
            symbols = self._symbols

        sessions = ["London", "NY", "Asian"]
        data = []

        for symbol in symbols:
            data.append({
                'symbol': symbol,
                'momentum_score': random.randint(50, 95),
                'session': random.choice(sessions),
                'atr': round(random.uniform(0.0010, 0.0050), 5),
                'volume_ratio': round(random.uniform(0.8, 2.5), 2),
            })

        # Sort by momentum score
        data.sort(key=lambda x: x['momentum_score'], reverse=True)
        return data

    def generate_demo_pattern_data(self, symbol: str) -> Dict:
        """Generate demo data for Pattern Scorer"""
        patterns = ["Bullish Engulfing", "Bearish Pin Bar", "Double Bottom", "Head & Shoulders"]

        return {
            'symbol': symbol,
            'pattern_type': random.choice(patterns),
            'confidence': random.randint(60, 95),
            'entry_price': 1.0850 + random.uniform(-0.01, 0.01),
            'stop_loss': 1.0800 + random.uniform(-0.01, 0.01),
            'take_profit': 1.0950 + random.uniform(-0.01, 0.01),
            'risk_reward': round(random.uniform(1.5, 3.5), 1),
            'at_key_level': random.choice([True, False]),
            'volume_confirmation': random.choice([True, False]),
        }

    def generate_demo_correlation_matrix(self, symbols: List[str] = None) -> Dict[str, Dict[str, float]]:
        """Generate demo correlation matrix"""
        if symbols is None:
            symbols = self._symbols[:5]

        matrix = {}
        for sym1 in symbols:
            matrix[sym1] = {}
            for sym2 in symbols:
                if sym1 == sym2:
                    matrix[sym1][sym2] = 1.0
                else:
                    # Generate correlation value (-1 to 1)
                    corr = round(random.uniform(-0.8, 0.8), 2)
                    matrix[sym1][sym2] = corr

        return matrix

    def generate_demo_order_flow(self, symbol: str) -> Dict:
        """Generate demo order flow data"""
        return {
            'symbol': symbol,
            'institutional_buy': random.choice([True, False]),
            'institutional_sell': random.choice([True, False]),
            'retail_sentiment': random.randint(-100, 100),
            'smart_money_direction': random.choice(['BUY', 'SELL', 'NEUTRAL']),
            'volume_spike': random.choice([True, False]),
            'liquidity_sweep': random.choice([True, False]),
        }

    def generate_demo_news_events(self) -> List[Dict]:
        """Generate demo news calendar events"""
        events = [
            "Non-Farm Payrolls (USD)",
            "ECB Interest Rate Decision (EUR)",
            "GDP Growth Rate (GBP)",
            "CPI Inflation (USD)",
        ]

        impacts = ["HIGH", "MEDIUM", "LOW"]
        currencies = ["USD", "EUR", "GBP", "JPY"]

        demo_events = []
        now = datetime.now()

        for i in range(5):
            demo_events.append({
                'event_name': random.choice(events),
                'currency': random.choice(currencies),
                'impact': random.choice(impacts),
                'time': (now + timedelta(hours=i)).isoformat(),
                'forecast': str(round(random.uniform(-1.0, 5.0), 1)) + "%",
                'previous': str(round(random.uniform(-1.0, 5.0), 1)) + "%",
            })

        return demo_events

    def generate_demo_opportunity(self, symbol: str) -> Dict:
        """Generate demo opportunity"""
        patterns = ["Bullish Engulfing", "Bearish Pin Bar", "Double Bottom"]
        setups = ["London Open Breakout", "NY Session Reversal", "Asian Range Breakout"]

        return {
            'symbol': symbol,
            'pattern': random.choice(patterns),
            'setup_type': random.choice(setups),
            'quality_score': random.randint(65, 95),
            'entry': 1.0850 + random.uniform(-0.02, 0.02),
            'stop_loss': 1.0800 + random.uniform(-0.01, 0.01),
            'take_profit': 1.0950 + random.uniform(-0.01, 0.01),
            'risk_reward': round(random.uniform(1.5, 3.5), 1),
            'timeframe': random.choice(['M15', 'H1', 'H4']),
            'confidence': random.randint(60, 90),
        }

    def generate_demo_mtf_structure(self, symbol: str) -> Dict:
        """Generate demo multi-timeframe structure"""
        return {
            'symbol': symbol,
            'h4_trend': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'h1_trend': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'm15_trend': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'key_support': 1.0750 + random.uniform(-0.01, 0.01),
            'key_resistance': 1.0950 + random.uniform(-0.01, 0.01),
            'structure_quality': random.randint(50, 90),
        }

    def generate_demo_risk_metrics(self, symbol: str) -> Dict:
        """Generate demo risk/reward metrics"""
        return {
            'symbol': symbol,
            'recommended_risk_pct': round(random.uniform(0.5, 2.0), 1),
            'position_size': round(random.uniform(0.01, 0.10), 2),
            'win_probability': round(random.uniform(0.55, 0.85), 2),
            'expected_value': round(random.uniform(-0.5, 2.5), 2),
            'max_loss_usd': round(random.uniform(50, 200), 2),
            'max_profit_usd': round(random.uniform(100, 500), 2),
        }


# Global singleton instance
demo_mode_manager = DemoModeManager()


# Convenience functions
def is_demo_mode() -> bool:
    """Check if in demo mode"""
    return demo_mode_manager.is_demo()


def is_live_mode() -> bool:
    """Check if in live mode"""
    return demo_mode_manager.is_live()


def toggle_demo_mode():
    """Toggle between demo and live mode"""
    demo_mode_manager.toggle_mode()


def set_demo_mode(enabled: bool):
    """Set demo mode"""
    demo_mode_manager.demo_mode = enabled


def get_demo_data(widget_type: str, symbol: str = None, **kwargs) -> Any:
    """
    Get demo data for any widget type

    Args:
        widget_type: Type of widget requesting data
        symbol: Symbol to generate data for (if applicable)
        **kwargs: Additional parameters

    Returns:
        Demo data appropriate for widget type
    """
    if widget_type == "session_momentum":
        return demo_mode_manager.generate_demo_session_momentum(kwargs.get('symbols'))
    elif widget_type == "pattern_scorer":
        return demo_mode_manager.generate_demo_pattern_data(symbol)
    elif widget_type == "correlation":
        return demo_mode_manager.generate_demo_correlation_matrix(kwargs.get('symbols'))
    elif widget_type == "order_flow":
        return demo_mode_manager.generate_demo_order_flow(symbol)
    elif widget_type == "news":
        return demo_mode_manager.generate_demo_news_events()
    elif widget_type == "opportunity":
        return demo_mode_manager.generate_demo_opportunity(symbol)
    elif widget_type == "mtf_structure":
        return demo_mode_manager.generate_demo_mtf_structure(symbol)
    elif widget_type == "risk_metrics":
        return demo_mode_manager.generate_demo_risk_metrics(symbol)
    else:
        return None
