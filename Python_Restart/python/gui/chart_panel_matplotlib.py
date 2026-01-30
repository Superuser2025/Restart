"""
AppleTrader Pro - Matplotlib Chart Panel
Professional candlestick charts without WebEngine dependencies
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QLineEdit
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
from core.verbose_mode_manager import vprint
from core.visual_controls import visual_controls
from core.symbol_manager import SymbolManager
from core.statistical_analysis_manager import StatisticalAnalysisManager


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
        self.show_statistics = False  # Statistical analysis overlays - user turns ON when needed

        # MT5 connection status
        self.mt5_initialized = False
        self.init_mt5_connection()

        # Initialize symbol manager to get available symbols
        self.symbol_manager = SymbolManager()

        # Initialize statistical analysis manager (singleton)
        self.stats_manager = StatisticalAnalysisManager.get_instance()

        # Symbol favorites and recent history
        self.favorite_symbols = []  # Pinned symbols
        self.recent_symbols = []    # Last 5 viewed symbols
        self.max_recent = 5
        self._load_symbol_preferences()

        self.init_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_chart)
        self.update_timer.start(settings.app.chart_refresh_interval)

    def _load_symbol_preferences(self):
        """Load favorite and recent symbols from config file"""
        try:
            from pathlib import Path
            import json
            config_file = Path(__file__).parent.parent / "config" / "symbol_preferences.json"

            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.favorite_symbols = data.get('favorites', [])
                    self.recent_symbols = data.get('recent', [])
                    vprint(f"[Chart] Loaded {len(self.favorite_symbols)} favorites, {len(self.recent_symbols)} recent")
        except Exception as e:
            vprint(f"[Chart] Could not load symbol preferences: {e}")
            self.favorite_symbols = []
            self.recent_symbols = []

    def _save_symbol_preferences(self):
        """Save favorite and recent symbols to config file"""
        try:
            from pathlib import Path
            import json
            config_file = Path(__file__).parent.parent / "config" / "symbol_preferences.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'favorites': self.favorite_symbols,
                'recent': self.recent_symbols
            }

            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            vprint(f"[Chart] Saved symbol preferences")
        except Exception as e:
            vprint(f"[Chart] Could not save symbol preferences: {e}")

    def toggle_favorite(self, symbol: str):
        """Add or remove symbol from favorites"""
        if symbol in self.favorite_symbols:
            self.favorite_symbols.remove(symbol)
            vprint(f"[Chart] Removed {symbol} from favorites")
        else:
            self.favorite_symbols.append(symbol)
            vprint(f"[Chart] Added {symbol} to favorites")

        self._save_symbol_preferences()
        # Repopulate with current search filter
        search_text = self.symbol_search.text() if hasattr(self, 'symbol_search') else ""
        self.populate_symbol_dropdown(filter_text=search_text)

    def add_to_recent(self, symbol: str):
        """Add symbol to recent history"""
        # Remove if already in list
        if symbol in self.recent_symbols:
            self.recent_symbols.remove(symbol)

        # Add to front
        self.recent_symbols.insert(0, symbol)

        # Keep only last N symbols
        self.recent_symbols = self.recent_symbols[:self.max_recent]

        self._save_symbol_preferences()

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

        # Search box for filtering symbols
        search_label = QLabel("🔍")
        search_label.setStyleSheet(f"color: {settings.theme.text_secondary}; font-size: 18px;")
        layout.addWidget(search_label)

        self.symbol_search = QLineEdit()
        self.symbol_search.setPlaceholderText("Search symbols...")
        self.symbol_search.textChanged.connect(self.on_search_changed)
        self.symbol_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 150px;
                font-size: {settings.theme.font_size_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {settings.theme.accent};
            }}
        """)
        layout.addWidget(self.symbol_search)

        layout.addSpacing(10)

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
        self.symbol_combo.setEditable(False)
        self.populate_symbol_dropdown()
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

        # Favorite button
        self.favorite_btn = QPushButton("☆")
        self.favorite_btn.setFixedSize(36, 36)
        self.favorite_btn.clicked.connect(self.on_favorite_clicked)
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.warning};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {settings.theme.accent};
                color: #FFFFFF;
            }}
        """)
        layout.addWidget(self.favorite_btn)

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

        layout.addSpacing(10)

        # Statistics toggle button - OFF/RED by default
        self.statistics_toggle_btn = QPushButton("📊 Statistics: OFF")
        self.statistics_toggle_btn.clicked.connect(self.toggle_statistics)
        self.statistics_toggle_btn.setStyleSheet(f"""
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
        layout.addWidget(self.statistics_toggle_btn)

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

    def populate_symbol_dropdown(self, filter_text: str = ""):
        """Populate dropdown with favorites, recent, and grouped symbols"""
        self.symbol_combo.blockSignals(True)  # Prevent triggering on_symbol_changed during population
        # Use self.current_symbol if combo is empty (initialization), otherwise use combo's current text
        current_symbol = self.symbol_combo.currentText() if self.symbol_combo.currentText() else self.current_symbol
        self.symbol_combo.clear()

        if not self.symbol_manager.symbols:
            self.symbol_combo.addItems(['EURUSD'])
            self.symbol_combo.blockSignals(False)
            return

        from collections import defaultdict

        # Collect all symbols
        all_symbols = []

        # Filter by search text if provided
        filtered_symbols = {}
        for symbol, specs in self.symbol_manager.symbols.items():
            if not filter_text or filter_text.upper() in symbol.upper():
                filtered_symbols[symbol] = specs

        # SECTION 1: FAVORITES
        favorites_in_list = [s for s in self.favorite_symbols if s in filtered_symbols]
        if favorites_in_list:
            self.symbol_combo.addItem("★ FAVORITES")
            model = self.symbol_combo.model()
            item = model.item(self.symbol_combo.count() - 1)
            item.setEnabled(False)

            for symbol in favorites_in_list:
                self.symbol_combo.addItem(f"  ★ {symbol}")
                all_symbols.append(symbol)

        # SECTION 2: RECENT
        recent_in_list = [s for s in self.recent_symbols if s in filtered_symbols and s not in favorites_in_list]
        if recent_in_list:
            self.symbol_combo.addItem("🕐 RECENT")
            model = self.symbol_combo.model()
            item = model.item(self.symbol_combo.count() - 1)
            item.setEnabled(False)

            for symbol in recent_in_list:
                self.symbol_combo.addItem(f"  {symbol}")
                all_symbols.append(symbol)

        # SECTION 3: GROUPED BY ASSET CLASS
        grouped_symbols = defaultdict(list)
        for symbol, specs in filtered_symbols.items():
            # Skip if already in favorites or recent
            if symbol not in favorites_in_list and symbol not in recent_in_list:
                grouped_symbols[specs.asset_class].append(symbol)

        group_order = [
            ('forex', '═══ FOREX ═══'),
            ('index', '═══ INDICES ═══'),
            ('stock', '═══ STOCKS ═══'),
            ('commodity', '═══ COMMODITIES ═══'),
            ('crypto', '═══ CRYPTO ═══')
        ]

        for asset_class, group_label in group_order:
            if asset_class in grouped_symbols and grouped_symbols[asset_class]:
                self.symbol_combo.addItem(group_label)
                model = self.symbol_combo.model()
                item = model.item(self.symbol_combo.count() - 1)
                item.setEnabled(False)

                symbols_in_group = sorted(grouped_symbols[asset_class])
                for symbol in symbols_in_group:
                    self.symbol_combo.addItem(symbol)
                    all_symbols.append(symbol)

        # Restore selection or set first available
        if current_symbol in all_symbols:
            # Find the display text (might have prefix like "★ ")
            for i in range(self.symbol_combo.count()):
                item_text = self.symbol_combo.itemText(i)
                if current_symbol in item_text:
                    self.symbol_combo.setCurrentIndex(i)
                    break
        elif all_symbols:
            self.symbol_combo.setCurrentIndex(self.symbol_combo.findText(all_symbols[0], Qt.MatchFlag.MatchContains))

        self.symbol_combo.blockSignals(False)
        vprint(f"[Chart] Populated dropdown: {len(all_symbols)} symbols")

    def on_search_changed(self, text: str):
        """Filter symbol dropdown based on search text"""
        self.populate_symbol_dropdown(filter_text=text)

    def on_favorite_clicked(self):
        """Toggle favorite status of current symbol"""
        symbol = self.current_symbol
        if symbol:
            self.toggle_favorite(symbol)
            self.update_favorite_button()

    def update_favorite_button(self):
        """Update favorite button appearance based on current symbol"""
        if self.current_symbol in self.favorite_symbols:
            self.favorite_btn.setText("★")  # Filled star
            self.favorite_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.warning};
                    color: #FFFFFF;
                    border: 1px solid {settings.theme.warning};
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {settings.theme.surface_light};
                    color: {settings.theme.warning};
                }}
            """)
        else:
            self.favorite_btn.setText("☆")  # Empty star
            self.favorite_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.surface_light};
                    color: {settings.theme.warning};
                    border: 1px solid {settings.theme.border_color};
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {settings.theme.accent};
                    color: #FFFFFF;
                }}
            """)

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
                vprint(f"[Chart] load_historical_data: Using current_symbol = {symbol}")
            else:
                vprint(f"[Chart] load_historical_data: Symbol parameter provided = {symbol}")

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
            vprint(f"[Chart] Updated data_manager with {symbol} data - {len(rates)} candles")

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
        vprint(f"[Chart] {self.current_timeframe}: Total={len(self.candle_data)}, Displaying={len(display_candles)}")

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

        if self.show_statistics:
            # Draw statistical analysis overlays
            self.draw_statistics_overlay()

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
        vprint(f"[Chart] {self.current_timeframe}: Final xlim = {final_xlim}, Expected = (-2, 102)")
        vprint(f"[Chart] {self.current_timeframe}: Figure size = {fig_width}x{fig_height} inches, Canvas size = {canvas_width}x{canvas_height} pixels")

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
        """Draw FVG/OB/Liquidity zones on chart from REAL SMART MONEY DETECTORS"""
        try:
            # ============================================================
            # USE REAL SMART MONEY DETECTORS (not EA data!)
            # ============================================================
            from analysis.order_block_detector import order_block_detector
            from analysis.fair_value_gap_detector import fair_value_gap_detector
            from analysis.liquidity_sweep_detector import liquidity_sweep_detector

            # Get candles from chart data
            if self.candle_data is None or len(self.candle_data) < 10:
                return

            # Convert to candle list format (handle both DataFrame and list)
            candles = []

            # Check if candle_data is a DataFrame (has iterrows method)
            if hasattr(self.candle_data, 'iterrows'):
                # It's a DataFrame - convert to list
                for idx, row in self.candle_data.iterrows():
                    candles.append({
                        'time': row.get('time', idx),
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'tick_volume': row.get('tick_volume', 0)
                    })
            elif isinstance(self.candle_data, list):
                # It's already a list - use directly or ensure correct format
                for candle in self.candle_data:
                    if isinstance(candle, dict):
                        # Already correct format
                        candles.append(candle)
                    else:
                        # Unknown format - skip
                        continue
            else:
                vprint(f"[ChartOverlay] ERROR: Unknown candle_data type: {type(self.candle_data)}")
                return

            vprint(f"\n[ChartOverlay] ═══ SMART MONEY DETECTION for {self.current_symbol} ═══")
            vprint(f"[ChartOverlay] → Analyzing {len(candles)} candles")

            # Draw FVGs (Fair Value Gaps) - CHECK VISUAL CONTROL
            if visual_controls.should_draw_fvg_zones():
                vprint(f"[ChartOverlay] --- FVG DETECTION ---")
                fvgs = fair_value_gap_detector.detect_fair_value_gaps(
                    candles, self.current_symbol, lookback=150, min_gap_pips=3
                )
                vprint(f"[ChartOverlay] Total FVGs: {len(fvgs)}, Unfilled: {len([f for f in fvgs if not f['filled']])}")

                if fvgs and len(fvgs) > 0:
                    # Convert to chart format with timestamps
                    fvg_chart_data = []
                    for i, fvg in enumerate(fvgs[:10]):  # Top 10
                        if not fvg['filled']:
                            # Get timestamp from the candle at this index
                            candle_idx = fvg.get('candle_index', len(candles) - 1)
                            if 0 <= candle_idx < len(candles):
                                # Use 'timestamp' field (has real time), not 'time' (often 0)
                                candle_time = candles[candle_idx].get('timestamp') or candles[candle_idx].get('time')
                                vprint(f"[ChartOverlay]     FVG {i+1}: top={fvg['top']:.5f}, bottom={fvg['bottom']:.5f}, type={fvg['type']}, time={candle_time}")
                            else:
                                candle_time = None
                                vprint(f"[ChartOverlay]     FVG {i+1}: top={fvg['top']:.5f}, bottom={fvg['bottom']:.5f}, type={fvg['type']}, BAD INDEX={candle_idx}")

                            fvg_chart_data.append({
                                'top': fvg['top'],
                                'bottom': fvg['bottom'],
                                'is_bullish': fvg['type'] == 'bullish',
                                'filled': False,
                                'ever_visited': fvg['fill_percentage'] > 0,
                                'timestamp': candle_time,  # Use candle's actual time
                                'candle_index': candle_idx
                            })
                    self.draw_fvg_zones(fvg_chart_data)
                    vprint(f"[ChartOverlay]   → Drew {len(fvg_chart_data)} FVG zones")

            # Draw Order Blocks - CHECK VISUAL CONTROL
            if visual_controls.should_draw_order_blocks():
                vprint(f"[ChartOverlay] --- ORDER BLOCK DETECTION ---")
                order_blocks = order_block_detector.detect_order_blocks(
                    candles, self.current_symbol, lookback=150, min_impulse_pips=8
                )
                valid_obs = [ob for ob in order_blocks if ob['valid'] and not ob['mitigated']]
                vprint(f"[ChartOverlay] Total OBs: {len(order_blocks)}, Valid: {len(valid_obs)}")

                if order_blocks and len(order_blocks) > 0:
                    # Convert to chart format with timestamps
                    ob_chart_data = []
                    display_obs = valid_obs[:10] if valid_obs else order_blocks[:10]
                    for i, ob in enumerate(display_obs):
                        # Get timestamp from the candle at this index
                        candle_idx = ob.get('candle_index', len(candles) - 1)
                        if 0 <= candle_idx < len(candles):
                            # Use 'timestamp' field (has real time), not 'time' (often 0)
                            candle_time = candles[candle_idx].get('timestamp') or candles[candle_idx].get('time')
                            vprint(f"[ChartOverlay]     OB {i+1}: high={ob['price_high']:.5f}, low={ob['price_low']:.5f}, type={ob['type']}, time={candle_time}")
                        else:
                            candle_time = None
                            vprint(f"[ChartOverlay]     OB {i+1}: high={ob['price_high']:.5f}, low={ob['price_low']:.5f}, type={ob['type']}, BAD INDEX={candle_idx}")

                        ob_chart_data.append({
                            'top': ob['price_high'],
                            'bottom': ob['price_low'],
                            'is_bullish': ob['type'] == 'demand',
                            'invalidated': ob['mitigated'],
                            'timestamp': candle_time,  # Use candle's actual time
                            'candle_index': candle_idx
                        })
                    self.draw_order_block_zones(ob_chart_data)
                    vprint(f"[ChartOverlay]   → Drew {len(ob_chart_data)} OB zones")

            # Draw Liquidity Zones - CHECK VISUAL CONTROL
            if visual_controls.should_draw_liquidity_lines():
                vprint(f"[ChartOverlay] --- LIQUIDITY SWEEP DETECTION ---")
                sweeps = liquidity_sweep_detector.detect_liquidity_sweeps(
                    candles, self.current_symbol, lookback=150, tolerance_pips=5
                )
                vprint(f"[ChartOverlay] Total Sweeps: {len(sweeps)}")

                if sweeps and len(sweeps) > 0:
                    # Convert to chart format with timestamps
                    liq_chart_data = []
                    for sweep in sweeps[:5]:
                        liq_chart_data.append({
                            'level': sweep['level'],
                            'is_high': sweep['type'] == 'high_sweep',
                            'timestamp': sweep.get('timestamp'),  # Use timestamp directly from detector
                            'candle_index': sweep.get('candle_index')
                        })
                    self.draw_liquidity_zones(liq_chart_data)
                    vprint(f"[ChartOverlay]   → Drew {len(liq_chart_data)} liquidity lines")

            # Draw Legend (if enabled)
            if visual_controls.should_draw_smart_money_legend():
                self.draw_smart_money_legend()

        except Exception as e:
            vprint(f"[ChartOverlay] ERROR in draw_chart_overlays: {e}")
            import traceback
            traceback.print_exc()

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

            # Format timestamp from candle time
            from datetime import datetime
            timestamp = fvg.get('timestamp')
            time_str = ''
            if timestamp:
                try:
                    # Handle both datetime objects and unix timestamps
                    if isinstance(timestamp, datetime):
                        # Only show if year >= 2020 (skip epoch)
                        if timestamp.year >= 2020:
                            time_str = timestamp.strftime('%d.%m %H:%M')
                    elif isinstance(timestamp, (int, float)) and timestamp > 1577836800:  # After Jan 1, 2020
                        dt = datetime.fromtimestamp(timestamp)
                        time_str = dt.strftime('%d.%m %H:%M')
                except Exception as e:
                    vprint(f"[Chart] FVG timestamp={timestamp} (type:{type(timestamp).__name__})")

            # Add label - DON'T show epoch timestamps!
            if time_str:
                label_text = f"FVG {'↑' if is_bullish else '↓'} {time_str}"
            else:
                label_text = f"FVG {'↑' if is_bullish else '↓'}"
            self.canvas.axes.text(
                len(self.candle_data) - 2,
                (top + bottom) / 2,
                label_text,
                fontsize=8,
                color=color,
                weight='bold',
                ha='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.9, linewidth=1.5)
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

            # Format timestamp from candle time
            from datetime import datetime
            timestamp = ob.get('timestamp')
            time_str = ''
            if timestamp:
                try:
                    # Handle both datetime objects and unix timestamps
                    if isinstance(timestamp, datetime):
                        # Only show if year >= 2020 (skip epoch)
                        if timestamp.year >= 2020:
                            time_str = timestamp.strftime('%d.%m %H:%M')
                    elif isinstance(timestamp, (int, float)) and timestamp > 1577836800:  # After Jan 1, 2020
                        dt = datetime.fromtimestamp(timestamp)
                        time_str = dt.strftime('%d.%m %H:%M')
                except Exception as e:
                    vprint(f"[Chart] OB timestamp={timestamp} (type:{type(timestamp).__name__})")

            # Add label - DON'T show epoch timestamps!
            if time_str:
                label_text = f"OB {'↑' if is_bullish else '↓'} {time_str}"
            else:
                label_text = f"OB {'↑' if is_bullish else '↓'}"
            self.canvas.axes.text(
                len(self.candle_data) - 2,
                (top + bottom) / 2,
                label_text,
                fontsize=8,
                color=color,
                weight='bold',
                ha='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.9, linewidth=1.5)
            )

    def draw_liquidity_zones(self, liquidity: list):
        """Draw actual Liquidity zones from smart money detectors"""
        if not self.candle_data:
            return

        for liq in liquidity:
            price = liq.get('level')  # FIXED: Use 'level' from detector output
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

            # Format timestamp from candle time
            from datetime import datetime
            timestamp = liq.get('timestamp')
            time_str = ''
            if timestamp:
                try:
                    # Handle both datetime objects and unix timestamps
                    if isinstance(timestamp, datetime):
                        # Only show if year >= 2020 (skip epoch)
                        if timestamp.year >= 2020:
                            time_str = timestamp.strftime('%d.%m %H:%M')
                    elif isinstance(timestamp, (int, float)) and timestamp > 1577836800:  # After Jan 1, 2020
                        dt = datetime.fromtimestamp(timestamp)
                        time_str = dt.strftime('%d.%m %H:%M')
                except Exception as e:
                    vprint(f"[Chart] LIQ timestamp={timestamp} (type:{type(timestamp).__name__})")

            # Add label - DON'T show epoch timestamps!
            if time_str:
                label_text = f"LIQ {'↑' if is_high else '↓'} {time_str}"
            else:
                label_text = f"LIQ {'↑' if is_high else '↓'}"
            self.canvas.axes.text(
                len(self.candle_data) - 8,
                price,
                label_text,
                fontsize=8,
                color=color,
                weight='bold',
                ha='right',
                va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A0E27', edgecolor=color, alpha=0.9, linewidth=1.5)
            )

    def draw_smart_money_legend(self):
        """Draw legend explaining smart money zones (toggleable)"""
        try:
            from matplotlib.patches import Rectangle, FancyBboxPatch

            # Use normalized axes coordinates (0-1 range)
            # Position in top-left corner
            legend_x = 0.02  # 2% from left edge
            legend_y = 0.98  # 98% from bottom (top of chart)
            box_width = 0.11  # 11% of chart width
            item_height = 0.035  # 3.5% of chart height per item

            # Legend items with colors
            legend_items = [
                ('FVG Bull', '#06B6D4'),
                ('FVG Bear', '#D946EF'),
                ('OB Bull', '#FBBF24'),
                ('OB Bear', '#F59E0B'),
                ('Liq High', '#EF4444'),
                ('Liq Low', '#10B981'),
            ]

            # Calculate total height
            total_height = (len(legend_items) + 0.8) * item_height

            # Draw legend background
            legend_bg = FancyBboxPatch(
                (legend_x, legend_y - total_height),
                box_width,
                total_height,
                boxstyle="round,pad=0.01",
                facecolor='#0A0E27',
                edgecolor='#FFFFFF',
                alpha=0.92,
                linewidth=1.5,
                transform=self.canvas.axes.transAxes,  # USE AXES COORDINATES!
                zorder=1000,
                clip_on=False
            )
            self.canvas.axes.add_patch(legend_bg)

            # Draw legend title
            self.canvas.axes.text(
                legend_x + box_width/2,
                legend_y - item_height/2,
                'SMART MONEY',
                fontsize=8,
                color='#FFFFFF',
                weight='bold',
                ha='center',
                va='center',
                transform=self.canvas.axes.transAxes,  # USE AXES COORDINATES!
                zorder=1001,
                clip_on=False
            )

            # Draw legend items
            for i, (label, color) in enumerate(legend_items):
                y_pos = legend_y - (i + 1.3) * item_height

                # Color box
                color_box = Rectangle(
                    (legend_x + 0.01, y_pos - 0.008),
                    0.012,
                    0.016,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.85,
                    transform=self.canvas.axes.transAxes,  # USE AXES COORDINATES!
                    zorder=1001,
                    clip_on=False
                )
                self.canvas.axes.add_patch(color_box)

                # Label text
                self.canvas.axes.text(
                    legend_x + 0.028,
                    y_pos,
                    label,
                    fontsize=7,
                    color='#FFFFFF',
                    va='center',
                    transform=self.canvas.axes.transAxes,  # USE AXES COORDINATES!
                    zorder=1001,
                    clip_on=False
                )

        except Exception as e:
            vprint(f"[Chart] Error drawing legend: {e}")
            import traceback
            traceback.print_exc()

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

            # NOTE: MT5 connection status removed from here
            # Connection status is now managed by MT5Connector with proper debouncing
            # to prevent flapping. Status updates via connection_status_changed signal.

            # Skip update if we're currently loading new data (symbol/timeframe change)
            if self.is_loading:
                return

            # ALWAYS reload data to get new candles from MT5
            # This is needed so the chart actually updates with market movement
            vprint(f"[Chart] Reloading data at {datetime.now().strftime('%H:%M:%S')}")
            success = self.load_historical_data()  # CORRECT METHOD NAME

            # CRITICAL: Redraw the chart with new data!
            if success:
                self.plot_candlesticks()
                vprint(f"[Chart] ✓ Chart redrawn with {len(self.candle_data)} candles")
            else:
                vprint(f"[Chart] ✗ Failed to load data from MT5")

        except Exception as e:
            vprint(f"[Chart] Error updating: {e}")
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
        vprint(f"=" * 80)
        vprint(f"[Chart] on_symbol_changed CALLED: {symbol}")
        vprint(f"[Chart] Previous symbol was: {self.current_symbol}")
        vprint(f"=" * 80)

        # Set loading flag to prevent update_chart from interfering
        self.is_loading = True

        # Clean symbol name (remove prefixes like "★ " or "  ")
        clean_symbol = symbol.replace("★", "").strip()

        self.current_symbol = clean_symbol
        vprint(f"[Chart] current_symbol set to: {self.current_symbol}")

        # Add to recent history
        self.add_to_recent(clean_symbol)

        # Update favorite button
        self.update_favorite_button()

        # Emit signal to notify main window (use clean_symbol for consistency)
        self.symbol_changed.emit(clean_symbol)

        # Reload historical data for new symbol
        if self.mt5_initialized:
            success = self.load_historical_data(symbol=clean_symbol)  # Use clean_symbol, not raw symbol
            if success:
                vprint(f"[Chart] ✓ Loaded {len(self.candle_data)} candles for {clean_symbol} from MT5")
            else:
                vprint(f"[Chart] ✗ Failed to load {clean_symbol} from MT5, trying fallback...")
                # Fallback to live data if historical load fails
                self.candle_data = []
                self.get_live_mt5_data()

                # CRITICAL: Even in fallback, update data_manager with current symbol!
                # This ensures widgets know we're on a different symbol even with no data
                import pandas as pd
                data_manager.candle_buffer.symbol = clean_symbol
                data_manager.candle_buffer.timeframe = self.current_timeframe
                vprint(f"[Chart] Updated data_manager to {clean_symbol} (fallback mode)")
        else:
            vprint(f"[Chart] MT5 not initialized, using live data for {clean_symbol}")
            # MT5 not available, use live data
            self.candle_data = []
            self.get_live_mt5_data()

            # CRITICAL: Update data_manager symbol even without MT5
            data_manager.candle_buffer.symbol = clean_symbol
            data_manager.candle_buffer.timeframe = self.current_timeframe
            vprint(f"[Chart] Updated data_manager to {symbol} (no MT5 mode)")

        self.plot_candlesticks()

        # Clear loading flag - updates can resume
        self.is_loading = False

    def refresh_symbol_list(self):
        """Refresh symbol dropdown from Symbol Manager (called when symbols are updated)"""
        vprint("[Chart] Refreshing symbol dropdown from Symbol Manager...")

        # Refresh symbols from MT5
        self.symbol_manager.refresh_symbols()

        # Repopulate using the standard method (includes favorites, recent, and groups)
        self.populate_symbol_dropdown()

        # Update favorite button for current symbol
        self.update_favorite_button()

        vprint("[Chart] ✓ Symbol dropdown refreshed")

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

    def toggle_statistics(self):
        """Toggle statistical analysis overlays on/off"""
        # Check if statistical analysis is globally enabled
        if not self.stats_manager.is_enabled():
            vprint("[Chart] Statistics system is globally disabled. Enable it in the Statistics tab.")
            # You could add a QMessageBox here to notify the user
            return

        self.show_statistics = not self.show_statistics

        if self.show_statistics:
            self.statistics_toggle_btn.setText("📊 Statistics: ON")
            self.statistics_toggle_btn.setStyleSheet(f"""
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
            self.statistics_toggle_btn.setText("📊 Statistics: OFF")
            self.statistics_toggle_btn.setStyleSheet(f"""
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

    def get_latest_pattern(self) -> str:
        """
        Detect the most recent candlestick pattern on the chart
        Returns pattern name or None if no pattern detected
        """
        if not self.candle_data or len(self.candle_data) < 3:
            return None

        # Check last 10 candles for patterns (most recent first)
        for i in range(len(self.candle_data) - 1, max(2, len(self.candle_data) - 11), -1):
            pattern = self.detect_pattern_at_index(i)
            if pattern:
                # Normalize pattern names to match Bayesian learner format
                # "BULLISH ENGULF" -> "Bullish_Engulfing"
                # "BEARISH ENGULF" -> "Bearish_Engulfing"
                # "HAMMER" -> "Hammer"
                # "SHOOT STAR" -> "Shooting_Star"
                # "DOJI" -> "Doji"
                pattern_map = {
                    "BULLISH ENGULF": "Bullish_Engulfing",
                    "BEARISH ENGULF": "Bearish_Engulfing",
                    "HAMMER": "Hammer",
                    "SHOOT STAR": "Shooting_Star",
                    "DOJI": "Doji"
                }
                normalized = pattern_map.get(pattern, pattern)
                vprint(f"[Chart] Detected pattern: {normalized} at index {i}")
                return normalized

        # No pattern detected in recent candles
        return None

    def draw_statistics_overlay(self):
        """Draw statistical analysis information as overlay on chart"""
        if not self.stats_manager.is_enabled():
            return

        try:
            # DETECT REAL PATTERN from chart data
            current_pattern = self.get_latest_pattern()

            # If no pattern detected, show message and return
            if not current_pattern:
                self.draw_no_pattern_message()
                return

            # Get calculators for current timeframe
            ev_calc = self.stats_manager.get_calculator(self.current_timeframe, 'expected_value')
            kelly_calc = self.stats_manager.get_calculator(self.current_timeframe, 'kelly')
            bayesian_calc = self.stats_manager.get_calculator(self.current_timeframe, 'bayesian')
            ci_calc = self.stats_manager.get_calculator(self.current_timeframe, 'confidence_interval')

            # Create overlay panel (top-right corner of chart)
            ax = self.canvas.axes
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Panel dimensions
            panel_width = (xlim[1] - xlim[0]) * 0.25  # 25% of chart width
            panel_height = (ylim[1] - ylim[0]) * 0.35  # 35% of chart height
            panel_x = xlim[1] - panel_width - 2  # 2 units from right edge
            panel_y = ylim[1] - panel_height - (ylim[1] - ylim[0]) * 0.02  # Small margin from top

            # Draw panel background
            from matplotlib.patches import FancyBboxPatch
            panel_bg = FancyBboxPatch(
                (panel_x, panel_y),
                panel_width,
                panel_height,
                boxstyle="round,pad=0.05",
                facecolor='#1E293B',
                edgecolor='#3B82F6',
                alpha=0.95,
                linewidth=2,
                zorder=1000
            )
            ax.add_patch(panel_bg)

            # Get Bayesian probability for current pattern
            try:
                bayesian_data = bayesian_calc.get_pattern_probability(current_pattern)
                win_prob = bayesian_data['posterior_mean']
                ci_lower = bayesian_data['credible_interval'][0]
                ci_upper = bayesian_data['credible_interval'][1]
                sample_size = bayesian_data['sample_size']
            except:
                win_prob = 0.50
                ci_lower = 0.40
                ci_upper = 0.60
                sample_size = 0

            # Get Expected Value
            try:
                # Create a mock opportunity for EV calculation
                mock_opportunity = {
                    'pattern': current_pattern,
                    'timeframe': self.current_timeframe
                }
                ev_data = ev_calc.get_detailed_analysis(mock_opportunity)
                expected_value = ev_data['adjusted_ev']
                confidence = ev_data['confidence']
            except:
                expected_value = 0.0
                confidence = 'No data'

            # Get Kelly fraction
            try:
                kelly_data = kelly_calc.calculate_kelly_fraction(mock_opportunity)
                kelly_half = kelly_data['kelly_half']
                kelly_quarter = kelly_data['kelly_quarter']
            except:
                kelly_half = 0.0
                kelly_quarter = 0.0

            # Text positioning
            text_x = panel_x + panel_width * 0.05
            text_y_start = panel_y + panel_height * 0.90
            line_height = panel_height * 0.12

            # Title
            ax.text(
                text_x, text_y_start,
                f'📊 STATISTICS - {self.current_timeframe}',
                fontsize=10,
                fontweight='bold',
                color='#3B82F6',
                verticalalignment='top',
                zorder=1001
            )

            # Win Probability
            prob_color = '#10B981' if win_prob >= 0.55 else '#EF4444'
            ax.text(
                text_x, text_y_start - line_height * 1,
                f'Win Rate: {win_prob*100:.1f}%',
                fontsize=9,
                fontweight='bold',
                color=prob_color,
                verticalalignment='top',
                zorder=1001
            )

            # Credible Interval
            ax.text(
                text_x, text_y_start - line_height * 1.8,
                f'95% CI: [{ci_lower*100:.1f}%-{ci_upper*100:.1f}%]',
                fontsize=8,
                color='#94A3B8',
                verticalalignment='top',
                zorder=1001
            )

            # Expected Value
            ev_color = '#10B981' if expected_value > 0 else '#EF4444'
            ax.text(
                text_x, text_y_start - line_height * 2.8,
                f'Expected Value: {expected_value:+.2f}R',
                fontsize=9,
                fontweight='bold',
                color=ev_color,
                verticalalignment='top',
                zorder=1001
            )

            # Kelly sizing
            ax.text(
                text_x, text_y_start - line_height * 3.8,
                f'Kelly: {kelly_half*100:.1f}% (½) / {kelly_quarter*100:.1f}% (¼)',
                fontsize=8,
                color='#94A3B8',
                verticalalignment='top',
                zorder=1001
            )

            # Sample size
            ax.text(
                text_x, text_y_start - line_height * 4.6,
                f'Data: {sample_size} trades | {confidence}',
                fontsize=7,
                color='#64748B',
                verticalalignment='top',
                zorder=1001
            )

            # Recommendation
            if expected_value > 0.5 and win_prob >= 0.60:
                recommendation = "✓ STRONG SETUP"
                rec_color = '#10B981'
            elif expected_value > 0 and win_prob >= 0.55:
                recommendation = "✓ Good Setup"
                rec_color = '#F59E0B'
            elif expected_value > 0:
                recommendation = "⚠ Marginal"
                rec_color = '#F59E0B'
            else:
                recommendation = "✗ Skip"
                rec_color = '#EF4444'

            ax.text(
                text_x, text_y_start - line_height * 5.8,
                recommendation,
                fontsize=9,
                fontweight='bold',
                color=rec_color,
                verticalalignment='top',
                zorder=1001
            )

            vprint(f"[Chart] Drew statistics overlay for {self.current_timeframe}")

        except Exception as e:
            vprint(f"[Chart] Error drawing statistics overlay: {e}")
            import traceback
            traceback.print_exc()

    def draw_no_pattern_message(self):
        """Draw message when no pattern is detected"""
        try:
            ax = self.canvas.axes
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Small panel in top-right
            panel_width = (xlim[1] - xlim[0]) * 0.20
            panel_height = (ylim[1] - ylim[0]) * 0.15
            panel_x = xlim[1] - panel_width - 2
            panel_y = ylim[1] - panel_height - (ylim[1] - ylim[0]) * 0.02

            # Panel background
            from matplotlib.patches import FancyBboxPatch
            panel_bg = FancyBboxPatch(
                (panel_x, panel_y),
                panel_width,
                panel_height,
                boxstyle="round,pad=0.05",
                facecolor='#1E293B',
                edgecolor='#64748B',
                alpha=0.90,
                linewidth=1,
                zorder=1000
            )
            ax.add_patch(panel_bg)

            # Message
            text_x = panel_x + panel_width * 0.5
            text_y = panel_y + panel_height * 0.5

            ax.text(
                text_x, text_y,
                '📊 STATISTICS\n\nNo Pattern\nDetected',
                fontsize=9,
                color='#94A3B8',
                ha='center',
                va='center',
                zorder=1001
            )

        except Exception as e:
            vprint(f"[Chart] Error drawing no pattern message: {e}")
