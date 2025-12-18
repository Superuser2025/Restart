"""
AppleTrader Pro - Matplotlib Chart Panel
Professional candlestick charts without WebEngine dependencies
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame
)
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
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
import warnings
import logging

# Suppress matplotlib font warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', message='.*Glyph.*missing from font.*')
logging.getLogger('matplotlib').setLevel(logging.ERROR)
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

from core.data_manager import data_manager
from core.visual_controls import visual_controls


# Simple theme and settings (inline replacement for config module)
class SimpleTheme:
    background = '#0A0E27'
    surface = '#1E293B'
    surface_light = '#334155'
    text_primary = '#F8FAFC'
    text_secondary = '#94A3B8'
    accent = '#3B82F6'
    success = '#10B981'
    danger = '#EF4444'
    warning = '#F59E0B'
    bullish = '#10B981'
    bearish = '#EF4444'
    border_color = '#334155'
    font_size_sm = 12
    font_size_md = 14
    font_size_lg = 16
    font_size_xl = 18

class SimpleAppSettings:
    default_symbol = 'EURUSD'
    default_timeframe = 'H4'
    chart_refresh_interval = 1000  # ms

class SimpleSettings:
    theme = SimpleTheme()
    app = SimpleAppSettings()

settings = SimpleSettings()


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for embedding in PyQt"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Create figure with dark theme
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#0A0E27')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#0A0E27')
        super().__init__(self.fig)


class ChartPanel(QWidget):
    """
    Professional matplotlib-based charting panel
    No WebEngine dependencies - works on all systems
    """

    # Signals
    timeframe_changed = pyqtSignal(str)
    symbol_changed = pyqtSignal(str)
    display_mode_changed = pyqtSignal(bool)  # True = max mode, False = small mode

    def __init__(self):
        super().__init__()

        self.current_symbol = settings.app.default_symbol
        self.current_timeframe = settings.app.default_timeframe

        # Display mode
        self.is_max_mode = False

        # Sample data for demonstration
        self.candle_data = []

        # Active patterns list for overlay panel
        self.active_patterns = []

        # Loading flag to prevent updates during data reload
        self.is_loading = False

        # Overlay visibility flags (user can toggle these) - OFF BY DEFAULT
        self.show_overlays = False  # FVG, OB, Liquidity zones - user turns ON when needed
        self.show_levels = False    # S/R, Pivots, PDH/PDL/PDC - user turns ON when needed

        # MT5 connection status
        self.mt5_initialized = False
        self.init_mt5_connection()

        self.init_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(settings.app.chart_refresh_interval)

    def init_ui(self):
        """Initialize UI components"""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Chart canvas
        self.canvas = MplCanvas(self, width=10, height=6, dpi=100)

        # CRITICAL: Set size policy to prevent squashing
        from PyQt6.QtWidgets import QSizePolicy
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumHeight(400)

        layout.addWidget(self.canvas, stretch=1)

        # Initialize chart
        self.init_chart()

    def create_toolbar(self) -> QFrame:
        """Create chart toolbar with controls"""

        toolbar = QFrame()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border-bottom: 1px solid {settings.theme.border_color};
                border-radius: 0;
            }}
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)

        # Symbol selector (allow user to view any symbol)
        symbol_label_text = QLabel("Symbol:")
        symbol_label_text.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(symbol_label_text)

        # Symbol dropdown
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['GBPUSD', 'EURUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
                                     'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY'])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        self.symbol_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                padding: 8px 12px;
                padding-right: 30px;
                min-width: 100px;
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {settings.theme.text_secondary};
                margin-right: 5px;
            }}
            QComboBox:hover {{
                border-color: {settings.theme.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                selection-background-color: {settings.theme.accent};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.symbol_combo)

        layout.addSpacing(20)

        # Timeframe selector
        tf_label = QLabel("Timeframe:")
        tf_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(tf_label)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1'])
        self.timeframe_combo.setCurrentText(self.current_timeframe)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        self.timeframe_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                padding: 8px 12px;
                padding-right: 30px;
                min-width: 80px;
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {settings.theme.text_secondary};
                margin-right: 5px;
            }}
            QComboBox:hover {{
                border-color: {settings.theme.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                selection-background-color: {settings.theme.accent};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.timeframe_combo)

        layout.addSpacing(20)

        # Update Speed selector
        speed_label = QLabel("Update Speed:")
        speed_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(speed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(['SLOW (5s)', 'NORMAL (2s)', 'FAST (1s)', 'REALTIME (500ms)'])
        self.speed_combo.setCurrentIndex(2)  # Default to FAST
        self.speed_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                padding: 8px 12px;
                padding-right: 30px;
                min-width: 120px;
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {settings.theme.text_secondary};
                margin-right: 5px;
            }}
            QComboBox:hover {{
                border-color: {settings.theme.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                selection-background-color: {settings.theme.accent};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.speed_combo)

        layout.addSpacing(20)

        # Display mode toggle button
        self.display_toggle_btn = QPushButton("⛶ MAX MODE")
        self.display_toggle_btn.clicked.connect(self.toggle_display_mode)
        self.display_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.accent};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: {settings.theme.font_size_md}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2563EB;
            }}
            QPushButton:pressed {{
                background-color: #1E40AF;
            }}
        """)
        layout.addWidget(self.display_toggle_btn)

        layout.addSpacing(20)

        # Performance metrics
        perf_label = QLabel("Performance:")
        perf_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_sm}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(perf_label)

        self.perf_today_label = QLabel("Day: +2.3%")
        self.perf_today_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.perf_today_label)

        self.perf_h1_label = QLabel("H1: +1.2%")
        self.perf_h1_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.perf_h1_label)

        self.perf_h4_label = QLabel("H4: +3.5%")
        self.perf_h4_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.perf_h4_label)

        self.perf_week_label = QLabel("Week: +8.7%")
        self.perf_week_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.perf_week_label)

        self.perf_month_label = QLabel("Month: +15.2%")
        self.perf_month_label.setStyleSheet("""
            QLabel {
                color: #10B981;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.perf_month_label)

        layout.addStretch()

        # Time display (moved from top toolbar)
        self.time_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.time_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_sm}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.time_label)

        # Spacing between time and overlays
        layout.addSpacing(30)

        # Overlay toggle button - OFF/RED by default
        self.overlay_toggle_btn = QPushButton("📊 Overlays: OFF")
        self.overlay_toggle_btn.clicked.connect(self.toggle_overlays)
        self.overlay_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: {settings.theme.font_size_sm}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
        """)
        layout.addWidget(self.overlay_toggle_btn)

        layout.addSpacing(10)

        # Levels toggle button - OFF/RED by default
        self.levels_toggle_btn = QPushButton("📈 Levels: OFF")
        self.levels_toggle_btn.clicked.connect(self.toggle_levels)
        self.levels_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: {settings.theme.font_size_sm}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
        """)
        layout.addWidget(self.levels_toggle_btn)

        layout.addSpacing(20)

        # MT5 Connection status (moved from top toolbar)
        self.connection_label = QLabel("🔴 MT5: Disconnected")
        self.connection_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.danger};
                font-size: {settings.theme.font_size_sm}px;
                font-weight: bold;
                background-color: {settings.theme.surface};
                padding: 5px 10px;
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.connection_label)

        return toolbar

    def init_mt5_connection(self):
        """Initialize connection to MetaTrader5"""
        try:
            if not mt5.initialize():
                self.mt5_initialized = False
                return

            self.mt5_initialized = True

        except Exception as e:
            self.mt5_initialized = False

    def get_mt5_timeframe(self, timeframe_str: str):
        """Convert timeframe string to MT5 constant"""
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
        }
        return timeframe_map.get(timeframe_str, mt5.TIMEFRAME_M5)

    def load_historical_data(self, symbol: str = None, timeframe: str = None, count: int = 100):
        """Load historical candles from MT5"""
        if not self.mt5_initialized:
            return False

        try:
            # CRITICAL FIX: Use user's selected symbol, don't override it!
            # If no symbol specified, use current_symbol (user's choice)
            if symbol is None:
                symbol = self.current_symbol
                print(f"[Chart] load_historical_data: Using current_symbol = {symbol}")
            else:
                print(f"[Chart] load_historical_data: Symbol parameter provided = {symbol}")

            timeframe = timeframe or self.current_timeframe
            mt5_timeframe = self.get_mt5_timeframe(timeframe)

            # Get historical rates from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

            if rates is None or len(rates) == 0:
                return False

            # Convert to our candle format
            self.candle_data = []
            for i, rate in enumerate(rates):
                candle = {
                    'time': i,
                    'open': rate['open'],
                    'high': rate['high'],
                    'low': rate['low'],
                    'close': rate['close'],
                    'timestamp': rate['time']
                }
                self.candle_data.append(candle)

            # CRITICAL: Update data_manager with new symbol's data!
            # This is what ALL widgets read from!
            import pandas as pd
            df = pd.DataFrame(rates)
            data_manager.candle_buffer.update(df, symbol, timeframe)
            print(f"[Chart] Updated data_manager with {symbol} data - {len(rates)} candles")

            return True

        except Exception as e:
            return False

    def init_chart(self):
        """Initialize chart with historical and live MT5 data"""

        # First, try to load historical data from MT5
        if self.mt5_initialized:
            success = self.load_historical_data()
            if not success:
                # Fallback to live data if historical load fails
                self.candle_data = []
                self.get_live_mt5_data()
        else:
            # MT5 not available, use live data from JSON
            self.candle_data = []
            self.get_live_mt5_data()

        self.plot_candlesticks()

    def get_live_mt5_data(self):
        """Get live price from MT5 data manager"""

        try:
            # Get current price from data manager
            price_data = data_manager.get_latest_price()

            bid = price_data.get('bid', 1.32000)
            ask = price_data.get('ask', 1.32020)

            # Validate prices - must be positive
            if bid <= 0 or ask <= 0:
                return

            mid_price = (bid + ask) / 2

            # Create a simple candle from current price
            if len(self.candle_data) == 0:
                # First candle - use current price
                new_candle = {
                    'time': 0,
                    'open': mid_price,
                    'high': ask,
                    'low': bid,
                    'close': mid_price
                }
            else:
                # Add new candle
                new_candle = {
                    'time': len(self.candle_data),
                    'open': self.candle_data[-1]['close'],
                    'high': ask,
                    'low': bid,
                    'close': mid_price
                }

            self.candle_data.append(new_candle)

            # Keep only last 50 candles
            if len(self.candle_data) > 50:
                self.candle_data.pop(0)
                # Adjust time indices
                for i, c in enumerate(self.candle_data):
                    c['time'] = i

        except Exception as e:
            pass

    def plot_candlesticks(self):
        """Plot candlestick chart - STANDARDIZED for all timeframes"""

        # CRITICAL: ALWAYS show exactly 100 candles regardless of timeframe
        # This keeps candle width consistent across M5, M15, H1, H4, etc.
        if len(self.candle_data) > 100:
            display_candles = self.candle_data[-100:]  # Last 100 candles only
        else:
            display_candles = self.candle_data

        # DEBUG: Print how many candles we're actually displaying
        print(f"[Chart] {self.current_timeframe}: Total={len(self.candle_data)}, Displaying={len(display_candles)}")

        self.canvas.axes.clear()

        if not display_candles:
            return

        # Extract data (use indices for plotting positions)
        indices = list(range(len(display_candles)))
        opens = [c['open'] for c in display_candles]
        highs = [c['high'] for c in display_candles]
        lows = [c['low'] for c in display_candles]
        closes = [c['close'] for c in display_candles]
        timestamps = [c.get('timestamp', 0) for c in display_candles]

        # Plot candlesticks with STANDARDIZED width using bar() for consistency
        for i, (idx, o, h, l, c) in enumerate(zip(indices, opens, highs, lows, closes)):
            color = '#10B981' if c >= o else '#EF4444'  # Green if bullish, red if bearish

            # Draw wick
            self.canvas.axes.plot([idx, idx], [l, h], color=color, linewidth=1, solid_capstyle='projecting')

            # Draw body using bar() - MORE RELIABLE than Rectangle for consistent width
            body_height = abs(c - o) if abs(c - o) > 0 else 0.00001  # Minimum height for doji
            body_bottom = min(o, c)

            # CRITICAL: Use bar() with ABSOLUTE width=0.95 for all timeframes (wider bars, minimal gaps)
            self.canvas.axes.bar(idx, body_height, width=0.95, bottom=body_bottom,
                                color=color, edgecolor=color, linewidth=0, align='center')

        # CRITICAL: Set fixed X-axis limits AFTER plotting to prevent squashing
        # Always show space for 100 candles, even if we have fewer
        self.canvas.axes.set_xlim(-2, 102)

        # CRITICAL: Let Y-axis autoscale to price data, but lock X-axis
        self.canvas.axes.autoscale(enable=True, axis='y')
        self.canvas.axes.autoscale(enable=False, axis='x')

        # FORCE lock the xlim one more time AFTER autoscale
        self.canvas.axes.set_xlim(-2, 102)

        # Disable automatic margin adjustment
        self.canvas.axes.margins(0, 0.05)  # 0 margin on X, 5% on Y

        # Styling
        self.canvas.axes.set_facecolor('#0A0E27')
        self.canvas.axes.grid(True, alpha=0.2, color='#1E293B')
        self.canvas.axes.set_xlabel('Time', color='#94A3B8', fontsize=10)
        self.canvas.axes.set_ylabel('Price', color='#94A3B8', fontsize=10)
        self.canvas.axes.tick_params(colors='#94A3B8', labelsize=9)

        # Set X-axis to show actual times instead of candle numbers
        if timestamps and timestamps[0] > 0:
            # Show time labels at regular intervals
            num_labels = min(8, len(indices))  # Show max 8 time labels
            step = max(1, len(indices) // num_labels)

            tick_positions = indices[::step]
            tick_labels = []

            for i in tick_positions:
                if i < len(timestamps):
                    ts = timestamps[i]
                    # Format timestamp as readable time
                    dt = datetime.fromtimestamp(ts)
                    # For intraday: show date and time (MM/DD HH:MM)
                    # For daily: show date only (MM/DD)
                    if self.current_timeframe in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']:
                        label = dt.strftime('%m/%d\n%H:%M')
                    else:
                        label = dt.strftime('%m/%d')
                    tick_labels.append(label)

            self.canvas.axes.set_xticks(tick_positions)
            self.canvas.axes.set_xticklabels(tick_labels, rotation=0, ha='center')

        # Set title
        if self.candle_data:
            current_price = self.candle_data[-1]['close']
            self.canvas.axes.set_title(
                f'{self.current_symbol} - {self.current_timeframe} | Price: {current_price:.5f}',
                color='#F8FAFC',
                fontsize=12,
                fontweight='bold',
                pad=10
            )

        # Draw overlays based on user toggle settings
        if self.show_overlays:
            # Draw institutional overlays (FVG, OB, Liquidity) - RESPECT VISUAL CONTROLS
            self.draw_chart_overlays()

            # Draw candlestick patterns with timeframes - CHECK VISUAL CONTROL
            if visual_controls.should_draw_pattern_boxes():
                self.draw_candlestick_patterns()

                # Draw active patterns panel overlay (MT5 EA style)
                self.draw_active_patterns_panel()

            # Draw price action commentary boxes (MT5 EA style) - CHECK VISUAL CONTROL
            if visual_controls.should_draw_commentary():
                self.draw_price_action_commentary()

                # Draw system status messages (MT5 EA style)
                self.draw_system_status_messages()

        if self.show_levels:
            # Draw key chart levels (support/resistance, pivots, PDH/PDL/PDC, sessions)
            self.draw_support_resistance_levels()
            self.draw_pivot_points()
            self.draw_previous_day_levels()
            self.draw_session_markers()

        # Adjust layout with proper margins
        try:
            self.canvas.fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.08)
        except:
            pass  # Ignore layout warnings

        # DEBUG: Check final xlim after all drawing
        final_xlim = self.canvas.axes.get_xlim()
        fig_width, fig_height = self.canvas.fig.get_size_inches()
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        print(f"[Chart] {self.current_timeframe}: Final xlim = {final_xlim}, Expected = (-2, 102)")
        print(f"[Chart] {self.current_timeframe}: Figure size = {fig_width}x{fig_height} inches, Canvas size = {canvas_width}x{canvas_height} pixels")

        self.canvas.draw()
        self.canvas.flush_events()

    def calculate_support_resistance(self):
        """Calculate support and resistance levels from swing highs/lows"""
        if not self.candle_data or len(self.candle_data) < 20:
            return []

        try:
            levels = []
            highs = [c['high'] for c in self.candle_data]
            lows = [c['low'] for c in self.candle_data]

            # Find swing highs (resistance)
            for i in range(5, len(self.candle_data) - 5):
                if highs[i] == max(highs[i-5:i+6]):
                    # Check if this level is unique (not too close to existing)
                    is_unique = True
                    for level in levels:
                        if abs(level['price'] - highs[i]) < (highs[i] * 0.0005):  # 0.05%
                            is_unique = False
                            break
                    if is_unique:
                        levels.append({'price': highs[i], 'type': 'resistance'})

            # Find swing lows (support)
            for i in range(5, len(self.candle_data) - 5):
                if lows[i] == min(lows[i-5:i+6]):
                    # Check if this level is unique
                    is_unique = True
                    for level in levels:
                        if abs(level['price'] - lows[i]) < (lows[i] * 0.0005):
                            is_unique = False
                            break
                    if is_unique:
                        levels.append({'price': lows[i], 'type': 'support'})

            # Keep only the 5 most significant levels (closest to current price)
            if levels:
                current_price = self.candle_data[-1]['close']
                levels.sort(key=lambda x: abs(x['price'] - current_price))
                levels = levels[:5]

            return levels

        except Exception as e:
            return []

    def draw_support_resistance_levels(self):
        """Draw support and resistance lines on chart"""
        if not self.candle_data:
            return

        try:
            # Get timeframe-appropriate settings
            settings = self.get_overlay_settings()

            levels = self.calculate_support_resistance()

            for level in levels:
                price = level['price']
                level_type = level['type']

                # Color: Blue for support, Purple for resistance
                color = '#3B82F6' if level_type == 'support' else '#A855F7'

                # Draw horizontal line with timeframe-based alpha and linewidth
                self.canvas.axes.axhline(
                    y=price,
                    color=color,
                    linestyle='--',
                    linewidth=settings['linewidth'],
                    alpha=settings['line_alpha'],
                    zorder=50
                )

                # Add label with timeframe-based font size
                label_text = f'{"S" if level_type == "support" else "R"}: {price:.5f}'
                self.canvas.axes.text(
                    len(self.candle_data) - 15,
                    price,
                    label_text,
                    fontsize=settings['font_size'],
                    color=color,
                    weight='bold',
                    ha='left',
                    va='bottom',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.9),
                    zorder=51
                )

        except Exception as e:
            pass

    def calculate_pivot_points(self):
        """Calculate daily pivot points (PP, S1-S3, R1-R3)"""
        if not self.mt5_initialized or not self.candle_data:
            return None

        try:
            # Get yesterday's daily candle from MT5
            rates = mt5.copy_rates_from_pos(self.current_symbol, mt5.TIMEFRAME_D1, 1, 1)

            if rates is None or len(rates) == 0:
                return None

            prev_day = rates[0]
            high = prev_day['high']
            low = prev_day['low']
            close = prev_day['close']

            # Classic Pivot Points formula
            pp = (high + low + close) / 3
            r1 = (2 * pp) - low
            r2 = pp + (high - low)
            r3 = high + 2 * (pp - low)
            s1 = (2 * pp) - high
            s2 = pp - (high - low)
            s3 = low - 2 * (high - pp)

            return {
                'PP': pp,
                'R1': r1, 'R2': r2, 'R3': r3,
                'S1': s1, 'S2': s2, 'S3': s3
            }

        except Exception as e:
            return None

    def draw_pivot_points(self):
        """Draw pivot point levels on chart"""
        if not self.candle_data:
            return

        try:
            # Get timeframe-appropriate settings
            settings = self.get_overlay_settings()

            pivots = self.calculate_pivot_points()

            if not pivots:
                return

            # Draw each pivot level
            pivot_config = [
                ('PP', '#FBBF24', '-'),  # Yellow, solid
                ('R1', '#EF4444', '--'),  # Red, dashed
                ('R2', '#DC2626', '--'),
                ('R3', '#B91C1C', ':'),
                ('S1', '#10B981', '--'),  # Green, dashed
                ('S2', '#059669', '--'),
                ('S3', '#047857', ':')
            ]

            for name, color, linestyle in pivot_config:
                price = pivots[name]

                # Draw pivot line with timeframe-based linewidth and alpha
                self.canvas.axes.axhline(
                    y=price,
                    color=color,
                    linestyle=linestyle,
                    linewidth=settings['linewidth'],
                    alpha=settings['line_alpha'],
                    zorder=45
                )

                # Add label with timeframe-based font size
                self.canvas.axes.text(
                    2,  # Left side
                    price,
                    f'{name}: {price:.5f}',
                    fontsize=settings['font_size'],
                    color=color,
                    weight='bold',
                    ha='left',
                    va='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.9),
                    zorder=46
                )

        except Exception as e:
            pass

    def draw_previous_day_levels(self):
        """Draw previous day High, Low, Close markers"""
        if not self.mt5_initialized or not self.candle_data:
            return

        try:
            # Get timeframe-appropriate settings
            settings = self.get_overlay_settings()

            # Get yesterday's daily candle
            rates = mt5.copy_rates_from_pos(self.current_symbol, mt5.TIMEFRAME_D1, 1, 1)

            if rates is None or len(rates) == 0:
                return

            prev_day = rates[0]
            pdh = prev_day['high']
            pdl = prev_day['low']
            pdc = prev_day['close']

            # Draw PDH (Previous Day High) - Red with timeframe-based settings
            self.canvas.axes.axhline(
                y=pdh,
                color='#F87171',
                linestyle='-.',
                linewidth=settings['linewidth'],
                alpha=settings['line_alpha'],
                zorder=48
            )
            self.canvas.axes.text(
                len(self.candle_data) // 2,
                pdh,
                f'PDH: {pdh:.5f}',
                fontsize=settings['font_size'],
                color='#F87171',
                weight='bold',
                ha='center',
                va='bottom',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0A0E27', edgecolor='#F87171', alpha=0.9, linewidth=settings['linewidth']),
                zorder=49
            )

            # Draw PDL (Previous Day Low) - Green with timeframe-based settings
            self.canvas.axes.axhline(
                y=pdl,
                color='#34D399',
                linestyle='-.',
                linewidth=settings['linewidth'],
                alpha=settings['line_alpha'],
                zorder=48
            )
            self.canvas.axes.text(
                len(self.candle_data) // 2,
                pdl,
                f'PDL: {pdl:.5f}',
                fontsize=settings['font_size'],
                color='#34D399',
                weight='bold',
                ha='center',
                va='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0A0E27', edgecolor='#34D399', alpha=0.9, linewidth=settings['linewidth']),
                zorder=49
            )

            # Draw PDC (Previous Day Close) - Yellow with timeframe-based settings
            self.canvas.axes.axhline(
                y=pdc,
                color='#FCD34D',
                linestyle='-.',
                linewidth=settings['linewidth'],
                alpha=settings['line_alpha'],
                zorder=48
            )
            self.canvas.axes.text(
                len(self.candle_data) // 2 + 10,
                pdc,
                f'PDC: {pdc:.5f}',
                fontsize=settings['font_size'],
                color='#FCD34D',
                weight='bold',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0A0E27', edgecolor='#FCD34D', alpha=0.9, linewidth=settings['linewidth']),
                zorder=49
            )

        except Exception as e:
            pass

    def draw_session_markers(self):
        """Draw London and NY session open markers (vertical lines)"""
        if not self.candle_data:
            return

        try:
            # Only draw session markers on intraday timeframes
            if self.current_timeframe not in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']:
                return

            # Get chart limits
            ylim = self.canvas.axes.get_ylim()

            # Find candles that correspond to London (08:00 GMT) and NY (13:00 GMT) opens
            for i, candle in enumerate(self.candle_data):
                timestamp = candle.get('timestamp', 0)
                if timestamp == 0:
                    continue

                dt = datetime.fromtimestamp(timestamp)
                hour = dt.hour
                minute = dt.minute

                # London Open (08:00 GMT) - Blue vertical line
                if hour == 8 and minute == 0:
                    self.canvas.axes.axvline(
                        x=i,
                        color='#60A5FA',
                        linestyle='--',
                        linewidth=1.5,
                        alpha=0.5,
                        zorder=40
                    )
                    # Label
                    self.canvas.axes.text(
                        i,
                        ylim[1] - (ylim[1] - ylim[0]) * 0.02,
                        'London Open',
                        fontsize=8,
                        color='#60A5FA',
                        weight='bold',
                        ha='center',
                        va='top',
                        rotation=90,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor='#60A5FA', alpha=0.8),
                        zorder=41
                    )

                # NY Open (13:00 GMT) - Orange vertical line
                if hour == 13 and minute == 0:
                    self.canvas.axes.axvline(
                        x=i,
                        color='#FB923C',
                        linestyle='--',
                        linewidth=1.5,
                        alpha=0.5,
                        zorder=40
                    )
                    # Label
                    self.canvas.axes.text(
                        i,
                        ylim[1] - (ylim[1] - ylim[0]) * 0.02,
                        'NY Open',
                        fontsize=8,
                        color='#FB923C',
                        weight='bold',
                        ha='center',
                        va='top',
                        rotation=90,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor='#FB923C', alpha=0.8),
                        zorder=41
                    )

        except Exception as e:
            pass

    def update_last_candle_only(self):
        """Update only the last (forming) candle with current price"""
        if not self.candle_data:
            return

        try:
            # Get current price from data_manager (EA's live data)
            price_data = data_manager.get_latest_price()
            bid = price_data.get('bid')
            ask = price_data.get('ask')

            # Validate: bid and ask must exist and be positive non-zero values
            if bid is None or ask is None or bid <= 0 or ask <= 0:
                return

            mid_price = (bid + ask) / 2

            # Update the last candle (the forming one)
            last_candle = self.candle_data[-1]
            last_candle['close'] = mid_price
            last_candle['high'] = max(last_candle['high'], ask)
            last_candle['low'] = min(last_candle['low'], bid)

            # Note: We don't change 'open' - it stays as it was when candle started

        except Exception as e:
            pass

    def draw_candlestick_patterns(self):
        """Detect and draw candlestick patterns on chart with TIMEFRAME labels"""
        if not self.candle_data or len(self.candle_data) < 3:
            return

        try:
            # Store active patterns for the active patterns panel
            self.active_patterns = []

            # Analyze last 20 candles for patterns
            num_candles = min(20, len(self.candle_data))
            start_idx = len(self.candle_data) - num_candles

            for i in range(start_idx, len(self.candle_data)):
                pattern = self.detect_pattern_at_index(i)
                if pattern:
                    # Add timeframe to pattern name (matching MT5 EA style)
                    pattern_with_tf = f"{pattern} [{self.current_timeframe}]"

                    # Store active pattern for overlay panel
                    if i >= len(self.candle_data) - 5:  # Last 5 candles are "active"
                        self.active_patterns.append(pattern_with_tf)

                    # Draw pattern annotation
                    candle = self.candle_data[i]
                    y_pos = candle['high'] + (candle['high'] - candle['low']) * 0.5

                    # Color based on pattern type
                    if 'BULLISH' in pattern or 'HAMMER' in pattern or 'ENGULF' in pattern and i > start_idx:
                        color = '#10B981'  # Green
                        marker = '▲'
                    elif 'BEARISH' in pattern or 'STAR' in pattern:
                        color = '#EF4444'  # Red
                        marker = '▼'
                    else:
                        color = '#F59E0B'  # Orange
                        marker = '●'

                    # Add pattern marker - VERY LARGE for visibility like MT5 EA
                    self.canvas.axes.plot(i, y_pos, marker=marker, color=color, markersize=18, zorder=100)

                    # Add pattern label with TIMEFRAME - MUCH LARGER font like MT5 EA
                    self.canvas.axes.text(
                        i, y_pos + (candle['high'] - candle['low']) * 0.4,
                        pattern_with_tf,
                        fontsize=11,  # Much larger font for visibility
                        color='#FFFFFF',  # White text for better visibility
                        weight='bold',
                        ha='center',
                        rotation=0,
                        bbox=dict(
                            boxstyle='round,pad=0.6',
                            facecolor=color,  # Colored background
                            edgecolor='#FFFFFF',  # White border
                            alpha=0.98,
                            linewidth=2.5
                        ),
                        zorder=101
                    )

        except Exception as e:
            pass

    def detect_pattern_at_index(self, idx):
        """Detect candlestick pattern at given index"""
        if idx < 2 or idx >= len(self.candle_data):
            return None

        current = self.candle_data[idx]
        prev1 = self.candle_data[idx - 1]
        prev2 = self.candle_data[idx - 2] if idx >= 2 else None

        # Calculate candle properties
        body = abs(current['close'] - current['open'])
        upper_wick = current['high'] - max(current['open'], current['close'])
        lower_wick = min(current['open'], current['close']) - current['low']
        total_range = current['high'] - current['low']

        is_bullish = current['close'] > current['open']
        is_bearish = current['close'] < current['open']

        # Engulfing patterns
        if prev1 and body > 0 and total_range > 0:
            prev_body = abs(prev1['close'] - prev1['open'])
            if is_bullish and prev1['close'] < prev1['open']:
                if current['close'] > prev1['open'] and current['open'] < prev1['close']:
                    if body > prev_body * 1.3:
                        return "BULLISH ENGULF"
            elif is_bearish and prev1['close'] > prev1['open']:
                if current['close'] < prev1['open'] and current['open'] > prev1['close']:
                    if body > prev_body * 1.3:
                        return "BEARISH ENGULF"

        # Hammer / Shooting Star
        if total_range > 0:
            body_ratio = body / total_range
            upper_wick_ratio = upper_wick / total_range
            lower_wick_ratio = lower_wick / total_range

            if body_ratio < 0.3:  # Small body
                if lower_wick_ratio > 0.6 and upper_wick_ratio < 0.1:
                    return "HAMMER"
                elif upper_wick_ratio > 0.6 and lower_wick_ratio < 0.1:
                    return "SHOOT STAR"

        # Doji
        if total_range > 0 and body / total_range < 0.1:
            return "DOJI"

        return None

    def draw_active_patterns_panel(self):
        """Draw active patterns indicator panel overlay on chart (MT5 EA style)"""
        if not hasattr(self, 'active_patterns') or not self.active_patterns:
            return

        try:
            # Get chart limits
            ylim = self.canvas.axes.get_ylim()
            xlim = self.canvas.axes.get_xlim()

            # Position panel in top-left corner (like MT5 EA)
            panel_x = xlim[0] + (xlim[1] - xlim[0]) * 0.02
            panel_y_start = ylim[1] - (ylim[1] - ylim[0]) * 0.05

            # Draw panel background
            panel_height = len(self.active_patterns) * 0.04 * (ylim[1] - ylim[0]) + 0.02 * (ylim[1] - ylim[0])
            panel_width = 0.30 * (xlim[1] - xlim[0])

            panel_rect = Rectangle(
                (panel_x, panel_y_start - panel_height),
                panel_width,
                panel_height,
                facecolor='#1E293B',
                edgecolor='#3B82F6',
                alpha=0.95,
                linewidth=2,
                zorder=200
            )
            self.canvas.axes.add_patch(panel_rect)

            # Add panel title
            title_y = panel_y_start - 0.015 * (ylim[1] - ylim[0])
            self.canvas.axes.text(
                panel_x + panel_width * 0.5,
                title_y,
                '🔍 ACTIVE PATTERNS',
                fontsize=10,
                color='#3B82F6',
                weight='bold',
                ha='center',
                va='top',
                zorder=201
            )

            # Add each active pattern
            y_offset = 0.045 * (ylim[1] - ylim[0])
            for i, pattern in enumerate(self.active_patterns):
                pattern_y = panel_y_start - y_offset - (i * 0.04 * (ylim[1] - ylim[0]))

                # Color based on pattern type
                if 'BULLISH' in pattern or 'HAMMER' in pattern:
                    color = '#10B981'
                    marker = '▲'
                elif 'BEARISH' in pattern or 'STAR' in pattern:
                    color = '#EF4444'
                    marker = '▼'
                else:
                    color = '#F59E0B'
                    marker = '●'

                # Draw pattern text with marker
                self.canvas.axes.text(
                    panel_x + panel_width * 0.05,
                    pattern_y,
                    f'{marker} {pattern}',
                    fontsize=9,
                    color=color,
                    weight='bold',
                    ha='left',
                    va='center',
                    zorder=201
                )

        except Exception as e:
            pass

    def draw_price_action_commentary(self):
        """Draw detailed price action commentary boxes (MT5 EA style)"""
        if not self.candle_data or len(self.candle_data) < 10:
            return

        try:
            # Get market analysis from data_manager or generate based on patterns
            ylim = self.canvas.axes.get_ylim()
            xlim = self.canvas.axes.get_xlim()

            # Generate commentary based on current patterns and trend
            commentaries = []

            # Analyze recent trend
            recent_closes = [c['close'] for c in self.candle_data[-10:]]
            trend = "BULLISH" if recent_closes[-1] > recent_closes[0] else "BEARISH"
            trend_color = '#10B981' if trend == "BULLISH" else '#EF4444'

            # Check for higher highs / lower lows
            recent_highs = [c['high'] for c in self.candle_data[-10:]]
            recent_lows = [c['low'] for c in self.candle_data[-10:]]

            if recent_highs[-1] > max(recent_highs[:-1]):
                structure = "Higher Highs forming"
            elif recent_lows[-1] < min(recent_lows[:-1]):
                structure = "Lower Lows forming"
            else:
                structure = "Consolidation phase"

            # Add symbol and timeframe header - BOTTOM LEFT
            commentaries.append({
                'text': f'📊 {self.current_symbol} | {self.current_timeframe}',
                'color': '#00aaff',
                'x_position': 0.02,  # 2% from left
                'y_position': 0.05  # 5% from bottom
            })

            commentaries.append({
                'text': f'Trend: {trend}\n{structure}',
                'color': trend_color,
                'x_position': 0.02,
                'y_position': 0.15  # 15% from bottom
            })

            # Add momentum commentary
            momentum_text = f'Momentum: {"Strong" if abs(recent_closes[-1] - recent_closes[0]) > 0.001 else "Weak"}'
            commentaries.append({
                'text': momentum_text,
                'color': '#3B82F6',
                'x_position': 0.02,
                'y_position': 0.25  # 25% from bottom
            })

            # Add pattern-specific commentary if patterns detected
            if hasattr(self, 'active_patterns') and self.active_patterns:
                pattern_text = f'Patterns detected:\n{len(self.active_patterns)} active [{self.current_timeframe}]'
                commentaries.append({
                    'text': pattern_text,
                    'color': '#F59E0B',
                    'x_position': 0.02,
                    'y_position': 0.35  # 35% from bottom
                })

            # Draw commentary boxes - positioned in BOTTOM LEFT to avoid zone overlaps
            for i, commentary in enumerate(commentaries):
                box_x = xlim[0] + (xlim[1] - xlim[0]) * commentary['x_position']
                box_y = ylim[0] + (ylim[1] - ylim[0]) * commentary['y_position']

                # Draw commentary box
                self.canvas.axes.text(
                    box_x,
                    box_y,
                    commentary['text'],
                    fontsize=9,
                    color='#FFFFFF',
                    weight='bold',
                    ha='left',
                    va='center',
                    bbox=dict(
                        boxstyle='round,pad=0.8',
                        facecolor=commentary['color'],
                        edgecolor='#FFFFFF',
                        alpha=0.90,
                        linewidth=2
                    ),
                    zorder=150
                )

        except Exception as e:
            pass

    def draw_system_status_messages(self):
        """Draw system status/advice messages on chart (MT5 EA style)"""
        if not self.candle_data:
            return

        try:
            # Get chart limits
            ylim = self.canvas.axes.get_ylim()
            xlim = self.canvas.axes.get_xlim()

            # Generate system messages based on timeframe and conditions
            messages = []

            # Timeframe recommendation with symbol
            if self.current_timeframe in ['M1', 'M5']:
                messages.append({
                    'text': f'⚠️ {self.current_symbol} {self.current_timeframe}: Switch to H1/H4 for optimal results',
                    'color': '#F59E0B',
                    'position': 'top'
                })
            elif self.current_timeframe in ['H4', 'H1']:
                messages.append({
                    'text': f'✅ {self.current_symbol} {self.current_timeframe}: Optimal timeframe for institutional trading',
                    'color': '#10B981',
                    'position': 'top'
                })

            # Market condition message
            if len(self.candle_data) >= 10:
                recent_range = max([c['high'] for c in self.candle_data[-10:]]) - min([c['low'] for c in self.candle_data[-10:]])
                avg_body = sum([abs(c['close'] - c['open']) for c in self.candle_data[-10:]]) / 10

                if avg_body < recent_range * 0.3:
                    messages.append({
                        'text': '📊 Low volatility - wait for breakout',
                        'color': '#94A3B8',
                        'position': 'middle'
                    })
                else:
                    messages.append({
                        'text': '⚡ High volatility - strong moves expected',
                        'color': '#3B82F6',
                        'position': 'middle'
                    })

            # Draw messages - positioned at TOP CENTER and BOTTOM CENTER
            for i, message in enumerate(messages):
                if message['position'] == 'top':
                    msg_y = ylim[1] - (ylim[1] - ylim[0]) * 0.08  # Closer to top edge
                    msg_x = xlim[0] + (xlim[1] - xlim[0]) * 0.50  # Center
                elif message['position'] == 'middle':
                    msg_y = ylim[0] + (ylim[1] - ylim[0]) * 0.50  # True middle
                    msg_x = xlim[0] + (xlim[1] - xlim[0]) * 0.75  # Right side
                else:
                    msg_y = ylim[0] + (ylim[1] - ylim[0]) * 0.08  # Bottom
                    msg_x = xlim[0] + (xlim[1] - xlim[0]) * 0.50  # Center

                # Draw message box
                self.canvas.axes.text(
                    msg_x,
                    msg_y,
                    message['text'],
                    fontsize=9,
                    color='#FFFFFF',
                    weight='bold',
                    ha='center',
                    va='center',
                    bbox=dict(
                        boxstyle='round,pad=0.6',
                        facecolor=message['color'],
                        edgecolor='#FFFFFF',
                        alpha=0.85,
                        linewidth=2
                    ),
                    zorder=150
                )

        except Exception as e:
            pass

    def get_overlay_settings(self):
        """Get overlay transparency and font size based on timeframe to reduce clutter"""
        # Lower timeframes = less opacity, smaller fonts to preserve candle visibility
        timeframe_settings = {
            'M1': {'zone_alpha': 0.08, 'line_alpha': 0.25, 'font_size': 7, 'linewidth': 1.0},
            'M5': {'zone_alpha': 0.10, 'line_alpha': 0.30, 'font_size': 7, 'linewidth': 1.0},
            'M15': {'zone_alpha': 0.12, 'line_alpha': 0.35, 'font_size': 8, 'linewidth': 1.2},
            'M30': {'zone_alpha': 0.13, 'line_alpha': 0.40, 'font_size': 8, 'linewidth': 1.2},
            'H1': {'zone_alpha': 0.15, 'line_alpha': 0.45, 'font_size': 8, 'linewidth': 1.5},
            'H4': {'zone_alpha': 0.18, 'line_alpha': 0.50, 'font_size': 9, 'linewidth': 1.5},
            'D1': {'zone_alpha': 0.20, 'line_alpha': 0.55, 'font_size': 9, 'linewidth': 2.0},
            'W1': {'zone_alpha': 0.22, 'line_alpha': 0.60, 'font_size': 10, 'linewidth': 2.0},
        }
        return timeframe_settings.get(self.current_timeframe, timeframe_settings['H4'])

    def draw_chart_overlays(self):
        """Draw FVG/OB/Liquidity zones on chart from REAL EA data - RESPECTS VISUAL CONTROLS"""
        try:
            # Get zone data from EA via data_manager
            zones = data_manager.get_zones()

            # Draw FVGs (Fair Value Gaps) - CHECK VISUAL CONTROL
            if visual_controls.should_draw_fvg_zones():
                fvgs = zones.get('fvgs', [])
                if fvgs and len(fvgs) > 0:
                    self.draw_fvg_zones(fvgs)
                else:
                    # Fallback to sample if no real data
                    self.draw_sample_fvg()

            # Draw Order Blocks - CHECK VISUAL CONTROL
            if visual_controls.should_draw_order_blocks():
                order_blocks = zones.get('order_blocks', [])
                if order_blocks and len(order_blocks) > 0:
                    self.draw_order_block_zones(order_blocks)
                else:
                    # Fallback to sample if no real data
                    self.draw_sample_order_block()

            # Draw Liquidity Zones - CHECK VISUAL CONTROL
            if visual_controls.should_draw_liquidity_lines():
                liquidity = zones.get('liquidity', [])
                if liquidity and len(liquidity) > 0:
                    self.draw_liquidity_zones(liquidity)
                else:
                    # Fallback to sample if no real data
                    self.draw_sample_liquidity()

        except Exception as e:
            pass

    def draw_fvg_zones(self, fvgs: list):
        """Draw actual FVG zones from EA data"""
        if not self.candle_data:
            return

        for fvg in fvgs:
            # Skip if filled or invalid
            if fvg.get('filled', False):
                continue

            top = fvg.get('top')
            bottom = fvg.get('bottom')
            is_bullish = fvg.get('is_bullish', True)
            ever_visited = fvg.get('ever_visited', False)

            if top is None or bottom is None:
                continue

            # Color: Cyan for bullish FVG, Magenta for bearish FVG
            # Dimmer if already visited
            if is_bullish:
                color = '#06B6D4' if not ever_visited else '#0E7490'
            else:
                color = '#D946EF' if not ever_visited else '#A21CAF'

            # Draw FVG rectangle spanning the entire chart width
            rect = Rectangle(
                (0, bottom),  # Start at x=0
                len(self.candle_data),  # Span entire chart width
                top - bottom,  # Height
                linewidth=1 if not ever_visited else 0.5,
                edgecolor=color,
                facecolor=color,
                alpha=0.15 if not ever_visited else 0.08,
                linestyle='--',
                label='FVG (Bullish)' if is_bullish else 'FVG (Bearish)'
            )
            self.canvas.axes.add_patch(rect)

            # Add label on the right side
            label_text = 'FVG↑' if is_bullish else 'FVG↓'
            self.canvas.axes.text(
                len(self.candle_data) - 2,
                (top + bottom) / 2,
                label_text,
                fontsize=7,
                color=color,
                weight='bold',
                ha='right',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0E27', edgecolor=color, alpha=0.9)
            )

    def draw_order_block_zones(self, order_blocks: list):
        """Draw actual Order Block zones from EA data"""
        if not self.candle_data:
            return

        for ob in order_blocks:
            # Skip if invalidated
            if ob.get('invalidated', False):
                continue

            top = ob.get('top')
            bottom = ob.get('bottom')
            is_bullish = ob.get('is_bullish', True)
            test_count = ob.get('test_count', 0)
            ever_visited = ob.get('ever_visited', False)

            if top is None or bottom is None:
                continue

            # Color: Yellow for bullish OB, Orange for bearish OB
            # Dimmer if tested multiple times
            if is_bullish:
                color = '#FBBF24' if test_count < 2 else '#D97706'
            else:
                color = '#F59E0B' if test_count < 2 else '#C2410C'

            # Draw OB rectangle
            rect = Rectangle(
                (0, bottom),
                len(self.candle_data),
                top - bottom,
                linewidth=2 if test_count == 0 else 1,
                edgecolor=color,
                facecolor=color,
                alpha=0.20 if test_count < 2 else 0.12,
                linestyle='-',
                label=f'OB ({"Bullish" if is_bullish else "Bearish"})'
            )
            self.canvas.axes.add_patch(rect)

            # Add label with test count
            label_text = f'OB↑ [{test_count}]' if is_bullish else f'OB↓ [{test_count}]'
            self.canvas.axes.text(
                len(self.candle_data) - 2,
                (top + bottom) / 2,
                label_text,
                fontsize=7,
                color=color,
                weight='bold',
                ha='right',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0E27', edgecolor=color, alpha=0.9)
            )

    def draw_liquidity_zones(self, liquidity: list):
        """Draw actual Liquidity zones from EA data"""
        if not self.candle_data:
            return

        for liq in liquidity:
            price = liq.get('price')
            is_high = liq.get('is_high', True)  # True = resistance, False = support
            swept = liq.get('swept', False)
            touch_count = liq.get('touch_count', 0)

            if price is None:
                continue

            # Color: Red for resistance, Green for support
            # Dimmer if already swept
            if is_high:
                color = '#EF4444' if not swept else '#B91C1C'
            else:
                color = '#10B981' if not swept else '#059669'

            # Draw liquidity line
            self.canvas.axes.axhline(
                y=price,
                color=color,
                linestyle=':' if not swept else '-.',
                linewidth=2 if not swept else 1,
                alpha=0.7 if not swept else 0.4,
                label=f'Liquidity ({"Resistance" if is_high else "Support"})'
            )

            # Add label
            label_text = f'LIQ↑ [{touch_count}]' if is_high else f'LIQ↓ [{touch_count}]'
            if swept:
                label_text += ' SWEPT'

            self.canvas.axes.text(
                len(self.candle_data) - 8,
                price,
                label_text,
                fontsize=7,
                color=color,
                weight='bold',
                ha='right',
                va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0E27', edgecolor=color, alpha=0.9)
            )

    def draw_sample_fvg(self):
        """Draw Fair Value Gap rectangle (sample)"""
        if not self.candle_data or len(self.candle_data) < 20:
            return

        # Get timeframe-appropriate settings
        settings = self.get_overlay_settings()

        # Sample FVG in middle of chart
        start_idx = len(self.candle_data) // 3
        end_idx = start_idx + 5
        low_price = min([c['low'] for c in self.candle_data[start_idx:end_idx]])
        high_price = max([c['high'] for c in self.candle_data[start_idx:end_idx]])

        # Draw FVG rectangle (cyan with timeframe-based transparency)
        rect = Rectangle(
            (start_idx, low_price),
            end_idx - start_idx,
            high_price - low_price,
            linewidth=settings['linewidth'],
            edgecolor='#06B6D4',
            facecolor='#06B6D4',
            alpha=settings['zone_alpha'],
            linestyle='--',
            label='FVG'
        )
        self.canvas.axes.add_patch(rect)

        # Add label with timeframe-based font size
        self.canvas.axes.text(
            start_idx + 0.5,
            high_price,
            'FVG',
            fontsize=settings['font_size'],
            color='#06B6D4',
            weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor='#06B6D4', alpha=0.8)
        )

    def draw_sample_order_block(self):
        """Draw Order Block rectangle (sample)"""
        if not self.candle_data or len(self.candle_data) < 40:
            return

        # Get timeframe-appropriate settings
        settings = self.get_overlay_settings()

        # Sample OB in latter part of chart
        start_idx = len(self.candle_data) // 2
        end_idx = start_idx + 8
        low_price = min([c['low'] for c in self.candle_data[start_idx:end_idx]])
        high_price = max([c['high'] for c in self.candle_data[start_idx:end_idx]])

        # Draw OB rectangle (yellow/orange with timeframe-based transparency)
        color = '#F59E0B'  # Orange for bearish OB
        rect = Rectangle(
            (start_idx, low_price),
            end_idx - start_idx,
            high_price - low_price,
            linewidth=settings['linewidth'],
            edgecolor=color,
            facecolor=color,
            alpha=settings['zone_alpha'],
            linestyle='-',
            label='Order Block'
        )
        self.canvas.axes.add_patch(rect)

        # Add label with timeframe-based font size
        self.canvas.axes.text(
            start_idx + 1,
            low_price,
            'OB',
            fontsize=settings['font_size'],
            color=color,
            weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.8)
        )

    def draw_sample_liquidity(self):
        """Draw Liquidity horizontal lines (sample)"""
        if not self.candle_data or len(self.candle_data) < 10:
            return

        # Find a swing high for liquidity
        highs = [c['high'] for c in self.candle_data]
        liquidity_price = max(highs[len(highs)//3:len(highs)//2])

        # Draw liquidity line (red)
        self.canvas.axes.axhline(
            y=liquidity_price,
            color='#EF4444',
            linestyle=':',
            linewidth=2,
            alpha=0.7,
            label='Liquidity'
        )

        # Add label
        self.canvas.axes.text(
            len(self.candle_data) - 5,
            liquidity_price,
            'LIQUIDITY',
            fontsize=8,
            color='#EF4444',
            weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor='#EF4444', alpha=0.8)
        )

    def update_chart(self):
        """Update chart - reload data from MT5 to show new candles"""

        try:
            # Update time display
            if hasattr(self, 'time_label'):
                self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

            # Update MT5 connection status
            if hasattr(self, 'connection_label'):
                if self.mt5_initialized and mt5.terminal_info() is not None:
                    self.connection_label.setText("🟢 MT5: Connected")
                    self.connection_label.setStyleSheet(f"""
                        QLabel {{
                            color: {settings.theme.success};
                            font-size: {settings.theme.font_size_sm}px;
                            font-weight: bold;
                            background-color: {settings.theme.surface};
                            padding: 5px 10px;
                            border-radius: 5px;
                        }}
                    """)
                else:
                    self.connection_label.setText("🔴 MT5: Disconnected")
                    self.connection_label.setStyleSheet(f"""
                        QLabel {{
                            color: {settings.theme.danger};
                            font-size: {settings.theme.font_size_sm}px;
                            font-weight: bold;
                            background-color: {settings.theme.surface};
                            padding: 5px 10px;
                            border-radius: 5px;
                        }}
                    """)

            # Skip update if we're currently loading new data (symbol/timeframe change)
            if self.is_loading:
                return

            # ALWAYS reload data to get new candles from MT5
            # This is needed so the chart actually updates with market movement
            print(f"[Chart] Reloading data at {datetime.now().strftime('%H:%M:%S')}")
            success = self.load_historical_data()  # CORRECT METHOD NAME

            # CRITICAL: Redraw the chart with new data!
            if success:
                self.plot_candlesticks()
                print(f"[Chart] ✓ Chart redrawn with {len(self.candle_data)} candles")
            else:
                print(f"[Chart] ✗ Failed to load data from MT5")

        except Exception as e:
            print(f"[Chart] Error updating: {e}")
            if hasattr(self, 'connection_label'):
                self.connection_label.setText("🔴 MT5: Error")
                self.connection_label.setStyleSheet(f"""
                    QLabel {{
                        color: {settings.theme.danger};
                        font-size: {settings.theme.font_size_sm}px;
                        font-weight: bold;
                        background-color: {settings.theme.surface};
                        padding: 5px 10px;
                        border-radius: 5px;
                    }}
                """)

    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""

        # Set loading flag to prevent update_chart from interfering
        self.is_loading = True

        self.current_timeframe = timeframe
        self.timeframe_changed.emit(timeframe)

        # Reload historical data for new timeframe
        if self.mt5_initialized:
            success = self.load_historical_data(timeframe=timeframe)
            if not success:
                # Fallback to live data if historical load fails
                self.candle_data = []
                self.get_live_mt5_data()
        else:
            # MT5 not available, use live data
            self.candle_data = []
            self.get_live_mt5_data()

        self.plot_candlesticks()

        # Clear loading flag - updates can resume
        self.is_loading = False

    def on_symbol_changed(self, symbol: str):
        """Handle symbol change - allows viewing any symbol independent of EA"""
        print(f"=" * 80)
        print(f"[Chart] on_symbol_changed CALLED: {symbol}")
        print(f"[Chart] Previous symbol was: {self.current_symbol}")
        print(f"=" * 80)

        # Set loading flag to prevent update_chart from interfering
        self.is_loading = True

        self.current_symbol = symbol
        print(f"[Chart] current_symbol set to: {self.current_symbol}")

        # Emit signal to notify main window
        self.symbol_changed.emit(symbol)

        # Reload historical data for new symbol
        if self.mt5_initialized:
            success = self.load_historical_data(symbol=symbol)
            if success:
                print(f"[Chart] ✓ Loaded {len(self.candle_data)} candles for {symbol} from MT5")
            else:
                print(f"[Chart] ✗ Failed to load {symbol} from MT5, trying fallback...")
                # Fallback to live data if historical load fails
                self.candle_data = []
                self.get_live_mt5_data()

                # CRITICAL: Even in fallback, update data_manager with current symbol!
                # This ensures widgets know we're on a different symbol even with no data
                import pandas as pd
                data_manager.candle_buffer.symbol = symbol
                data_manager.candle_buffer.timeframe = self.current_timeframe
                print(f"[Chart] Updated data_manager to {symbol} (fallback mode)")
        else:
            print(f"[Chart] MT5 not initialized, using live data for {symbol}")
            # MT5 not available, use live data
            self.candle_data = []
            self.get_live_mt5_data()

            # CRITICAL: Update data_manager symbol even without MT5
            data_manager.candle_buffer.symbol = symbol
            data_manager.candle_buffer.timeframe = self.current_timeframe
            print(f"[Chart] Updated data_manager to {symbol} (no MT5 mode)")

        self.plot_candlesticks()

        # Clear loading flag - updates can resume
        self.is_loading = False

    def toggle_display_mode(self):
        """Toggle between small and max display modes"""
        self.is_max_mode = not self.is_max_mode

        if self.is_max_mode:
            self.display_toggle_btn.setText("⊟ SMALL MODE")
            self.display_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.danger};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_md}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
                QPushButton:pressed {{
                    background-color: #B91C1C;
                }}
            """)
        else:
            self.display_toggle_btn.setText("⛶ MAX MODE")
            self.display_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.accent};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_md}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #2563EB;
                }}
                QPushButton:pressed {{
                    background-color: #1E40AF;
                }}
            """)

        # Emit signal to main window
        self.display_mode_changed.emit(self.is_max_mode)

    def toggle_overlays(self):
        """Toggle FVG/OB/Liquidity overlays on/off"""
        self.show_overlays = not self.show_overlays

        if self.show_overlays:
            self.overlay_toggle_btn.setText("📊 Overlays: ON")
            self.overlay_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_sm}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
                QPushButton:pressed {{
                    background-color: #047857;
                }}
            """)
        else:
            self.overlay_toggle_btn.setText("📊 Overlays: OFF")
            self.overlay_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_sm}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
                QPushButton:pressed {{
                    background-color: #B91C1C;
                }}
            """)

        # Redraw chart
        self.plot_candlesticks()

    def toggle_levels(self):
        """Toggle S/R, Pivots, PDH/PDL/PDC levels on/off"""
        self.show_levels = not self.show_levels

        if self.show_levels:
            self.levels_toggle_btn.setText("📈 Levels: ON")
            self.levels_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_sm}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
                QPushButton:pressed {{
                    background-color: #047857;
                }}
            """)
        else:
            self.levels_toggle_btn.setText("📈 Levels: OFF")
            self.levels_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: {settings.theme.font_size_sm}px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
                QPushButton:pressed {{
                    background-color: #B91C1C;
                }}
            """)

        # Redraw chart
        self.plot_candlesticks()

