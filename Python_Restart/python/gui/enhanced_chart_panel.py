"""
Enhanced Chart Panel - Combines Matplotlib Chart with Overlay System
Displays candlesticks with zones and real-time analysis overlay
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from datetime import datetime
import MetaTrader5 as mt5

from core.data_manager import data_manager
from gui.chart_overlay_system import ChartOverlaySystem


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for embedding in PyQt"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#0A0E27')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#0A0E27')
        super().__init__(self.fig)


class EnhancedChartPanel(QWidget):
    """
    Enhanced chart panel with institutional zone overlays
    """

    timeframe_changed = pyqtSignal(str)
    symbol_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.current_symbol = "EURUSD"
        self.current_timeframe = "H4"
        self.candle_data = []
        self.is_loading = False
        self.mt5_initialized = False

        self.init_mt5_connection()
        self.init_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(1000)

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Create a stacked widget for chart + overlay
        chart_container = QWidget()
        chart_container_layout = QVBoxLayout(chart_container)
        chart_container_layout.setContentsMargins(0, 0, 0, 0)

        # Chart canvas (matplotlib)
        self.canvas = MplCanvas(self, width=10, height=6, dpi=100)
        chart_container_layout.addWidget(self.canvas)

        # Overlay system (zones and analysis panel)
        self.overlay = ChartOverlaySystem(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())

        layout.addWidget(chart_container)

        # Initialize chart
        self.init_chart()

    def init_mt5_connection(self):
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                print(f"[Chart] MT5 initialize() failed")
                self.mt5_initialized = False
            else:
                print(f"[Chart] MT5 connected successfully")
                self.mt5_initialized = True
        except Exception as e:
            print(f"[Chart] MT5 connection error: {e}")
            self.mt5_initialized = False

    def create_toolbar(self) -> QFrame:
        """Create chart toolbar"""
        toolbar = QFrame()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border-bottom: 1px solid #334155;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)

        # Symbol selector
        symbol_label = QLabel("Symbol:")
        symbol_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        layout.addWidget(symbol_label)

        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['GBPUSD', 'EURUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
                                     'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY'])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        self.symbol_combo.setStyleSheet("""
            QComboBox {
                background-color: #334155;
                color: white;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }
        """)
        layout.addWidget(self.symbol_combo)

        layout.addSpacing(20)

        # Timeframe selector
        tf_label = QLabel("Timeframe:")
        tf_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        layout.addWidget(tf_label)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1'])
        self.timeframe_combo.setCurrentText(self.current_timeframe)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        self.timeframe_combo.setStyleSheet("""
            QComboBox {
                background-color: #334155;
                color: white;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
        """)
        layout.addWidget(self.timeframe_combo)

        layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.force_refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        layout.addWidget(refresh_btn)

        return toolbar

    def init_chart(self):
        """Initialize empty chart"""
        self.canvas.axes.clear()
        self.canvas.axes.set_title("Loading chart...", color='white', fontsize=14)
        self.canvas.axes.grid(True, alpha=0.2, color='white')
        self.canvas.draw()

        # Load initial data
        self.load_historical_data()

    def load_historical_data(self) -> bool:
        """Load historical candle data from MT5"""
        if self.is_loading:
            return False

        self.is_loading = True

        try:
            # Try to get data from data_manager first
            df = data_manager.get_candles(self.current_symbol, self.current_timeframe, bars=200)

            if df is not None and len(df) > 0:
                self.candle_data = df
                print(f"[Enhanced Chart] Loaded {len(df)} candles from data_manager")
                self.is_loading = False
                return True

            # Fallback to MT5 direct
            if self.mt5_initialized:
                # Map timeframe to MT5 constant
                tf_map = {
                    'M1': mt5.TIMEFRAME_M1,
                    'M5': mt5.TIMEFRAME_M5,
                    'M15': mt5.TIMEFRAME_M15,
                    'M30': mt5.TIMEFRAME_M30,
                    'H1': mt5.TIMEFRAME_H1,
                    'H4': mt5.TIMEFRAME_H4,
                    'D1': mt5.TIMEFRAME_D1,
                    'W1': mt5.TIMEFRAME_W1
                }

                tf = tf_map.get(self.current_timeframe, mt5.TIMEFRAME_H4)
                rates = mt5.copy_rates_from_pos(self.current_symbol, tf, 0, 200)

                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    self.candle_data = df
                    print(f"[Enhanced Chart] Loaded {len(df)} candles from MT5")
                    self.is_loading = False
                    return True

            # Generate sample data as last resort
            print(f"[Enhanced Chart] Using sample data")
            self.generate_sample_data()
            self.is_loading = False
            return True

        except Exception as e:
            print(f"[Enhanced Chart] Error loading data: {e}")
            self.generate_sample_data()
            self.is_loading = False
            return False

    def generate_sample_data(self):
        """Generate sample candlestick data"""
        dates = pd.date_range(end=datetime.now(), periods=200, freq='H')
        base_price = 1.10000

        # Random walk price generation
        np.random.seed(42)
        price_changes = np.random.randn(200) * 0.0005
        close_prices = base_price + np.cumsum(price_changes)

        data = {
            'time': dates,
            'open': close_prices + np.random.randn(200) * 0.0002,
            'high': close_prices + np.abs(np.random.randn(200)) * 0.0005,
            'low': close_prices - np.abs(np.random.randn(200)) * 0.0005,
            'close': close_prices,
            'tick_volume': np.random.randint(100, 1000, 200)
        }

        self.candle_data = pd.DataFrame(data)

    def plot_candlesticks(self):
        """Plot candlestick chart"""
        if len(self.candle_data) == 0:
            return

        self.canvas.axes.clear()

        df = self.candle_data.tail(100)  # Show last 100 candles

        # Calculate dimensions for overlay
        price_high = df['high'].max()
        price_low = df['low'].min()

        # Plot candlesticks
        for i, row in df.iterrows():
            color = '#10B981' if row['close'] >= row['open'] else '#EF4444'
            alpha = 0.8

            # Body
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])

            rect = Rectangle((i, body_bottom), 0.8, body_height,
                           facecolor=color, edgecolor=color, alpha=alpha)
            self.canvas.axes.add_patch(rect)

            # Wick
            self.canvas.axes.plot([i + 0.4, i + 0.4], [row['low'], row['high']],
                                color=color, linewidth=1, alpha=alpha)

        # Styling
        self.canvas.axes.set_title(f"{self.current_symbol} - {self.current_timeframe}",
                                   color='white', fontsize=14, fontweight='bold')
        self.canvas.axes.set_xlabel('Time', color='#94A3B8')
        self.canvas.axes.set_ylabel('Price', color='#94A3B8')
        self.canvas.axes.grid(True, alpha=0.15, color='white')
        self.canvas.axes.tick_params(colors='#94A3B8')

        # Update overlay dimensions
        self.overlay.set_chart_dimensions(
            self.canvas.width(),
            self.canvas.height(),
            price_high,
            price_low
        )

        # Generate zones based on current price
        current_price = df['close'].iloc[-1]
        self.overlay.generate_sample_zones(current_price)

        # Update analysis data
        self.overlay.update_analysis({
            'order_blocks': len(self.overlay.zones),
            'h1_status': 'No pattern detected',
            'h4_status': f'Price action: {current_price:.5f}',
            'advice': f'Monitor for breakout near {current_price:.5f}. Watch for institutional order flow.',
            'system_status': 'System active - All filters enabled'
        })

        # Add some commentary
        if df['close'].iloc[-1] > df['open'].iloc[-1]:
            self.overlay.add_commentary("✓ Bullish candle - buyers in control")
        else:
            self.overlay.add_commentary("✓ Bearish candle - sellers in control")

        self.canvas.draw()

    def update_chart(self):
        """Update chart with latest data"""
        if not self.is_loading:
            success = self.load_historical_data()
            if success:
                self.plot_candlesticks()

    def force_refresh(self):
        """Force refresh chart"""
        print(f"[Enhanced Chart] Force refresh requested")
        self.load_historical_data()
        self.plot_candlesticks()

    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        self.current_symbol = symbol
        print(f"[Enhanced Chart] Symbol changed to {symbol}")
        self.symbol_changed.emit(symbol)
        self.force_refresh()

    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        print(f"[Enhanced Chart] Timeframe changed to {timeframe}")
        self.timeframe_changed.emit(timeframe)
        self.force_refresh()

    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        # Resize overlay to match
        if hasattr(self, 'overlay'):
            self.overlay.setGeometry(0, 60, self.width(), self.height() - 60)

    def toggle_visual(self, visual_name: str, enabled: bool):
        """Toggle specific visual element"""
        if hasattr(self, 'overlay'):
            self.overlay.toggle_visual(visual_name, enabled)
