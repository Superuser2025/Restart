"""
AppleTrader Pro - Controls Panel
All EA settings, filters, risk management, and trading controls
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QSlider, QFrame, QGroupBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from core.command_manager import command_manager


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
    border_color_light = '#475569'
    font_size_sm = 12
    font_size_md = 14
    font_size_lg = 16
    font_size_xl = 18

class SimpleTradingSettings:
    default_risk_percent = 1.0
    use_ml_filter = True

class SimpleAppSettings:
    update_speed_preset = None

class SimpleSettings:
    theme = SimpleTheme()
    trading = SimpleTradingSettings()
    app = SimpleAppSettings()

settings = SimpleSettings()

# Simple UpdateSpeed enum replacement
class UpdateSpeed:
    SLOW = "SLOW"
    NORMAL = "NORMAL"
    FAST = "FAST"
    REALTIME = "REALTIME"
    CUSTOM = "CUSTOM"

UPDATE_SPEED_CONFIGS = {
    "SLOW": {"description": "Slow (5s updates)"},
    "NORMAL": {"description": "Normal (2s updates)"},
    "FAST": {"description": "Fast (1s updates)"},
    "REALTIME": {"description": "Real-time (500ms)"},
}


class ControlsPanel(QWidget):
    """
    Trading controls panel with all EA settings
    Features:
    - Trading mode toggle
    - Update speed selector
    - Filter controls
    - Risk management
    - Quick order buttons
    - ML settings
    - Visual toggles
    """

    # Signals
    setting_changed = pyqtSignal(str, object)  # (setting_name, value)
    order_requested = pyqtSignal(str)  # 'BUY' or 'SELL'

    def __init__(self):
        super().__init__()

        # Lock states - start unlocked for better UX
        self.speed_locked = False  # Unlocked by default so users can change speed
        self.risk_locked = True    # Risk stays locked for safety

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""

        # Main scroll area for all controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {settings.theme.background};
                border: none;
            }}
        """)

        # Container widget
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {settings.theme.background};
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ============================================================
        # HEADER
        # ============================================================
        header = QLabel("⚙️ Settings")
        header.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_xl}px;
                font-weight: 700;
                padding: 8px 0;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(header)

        # ============================================================
        # STATUS FEEDBACK AREA
        # ============================================================
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(6)

        status_title = QLabel("📊 Status Log")
        status_title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_sm}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        status_layout.addWidget(status_title)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {settings.theme.background};
                border: 1px solid {settings.theme.border_color};
                border-radius: 4px;
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_sm}px;
                font-family: 'Courier New', monospace;
                padding: 4px;
            }}
        """)
        self.status_text.setPlainText(f"[{self._timestamp()}] Controls initialized\n[{self._timestamp()}] Ready to receive commands")
        status_layout.addWidget(self.status_text)

        layout.addWidget(status_frame)

        # ============================================================
        # TRADING MODE (Big Toggle)
        # ============================================================
        mode_section = self.create_trading_mode_section()
        layout.addWidget(mode_section)

        # ============================================================
        # UPDATE SPEED SELECTOR
        # ============================================================
        speed_section = self.create_update_speed_section()
        layout.addWidget(speed_section)

        # ============================================================
        # QUICK ORDER BUTTONS
        # ============================================================
        orders_section = self.create_quick_orders_section()
        layout.addWidget(orders_section)

        # ============================================================
        # RISK MANAGEMENT
        # ============================================================
        risk_section = self.create_risk_section()
        layout.addWidget(risk_section)

        # ============================================================
        # INSTITUTIONAL FILTERS
        # ============================================================
        filters_section = self.create_filters_section()
        layout.addWidget(filters_section)

        # ============================================================
        # SMART MONEY CONCEPTS
        # ============================================================
        smc_section = self.create_smc_section()
        layout.addWidget(smc_section)

        # ============================================================
        # MACHINE LEARNING
        # ============================================================
        ml_section = self.create_ml_section()
        layout.addWidget(ml_section)

        # ============================================================
        # VISUAL CONTROLS
        # ============================================================
        visual_section = self.create_visual_section()
        layout.addWidget(visual_section)

        layout.addStretch()

        scroll.setWidget(container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_trading_mode_section(self) -> QFrame:
        """Create trading mode toggle section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 2px solid {settings.theme.accent};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("TRADING MODE")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_lg}px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Toggle button (big and obvious)
        self.mode_button = QPushButton("🔴 INDICATOR MODE")
        self.mode_button.setCheckable(True)
        self.mode_button.setChecked(False)
        self.mode_button.clicked.connect(self.toggle_trading_mode)
        self.mode_button.setFixedHeight(60)
        self.mode_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.warning};
                color: {settings.theme.background};
                border: none;
                border-radius: 10px;
                font-size: {settings.theme.font_size_xl}px;
                font-weight: 700;
            }}
            QPushButton:checked {{
                background-color: {settings.theme.success};
            }}
            QPushButton:hover {{
            }}
        """)
        layout.addWidget(self.mode_button)

        return frame

    def create_update_speed_section(self) -> QFrame:
        """Create update speed selector"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title with lock button
        title_layout = QHBoxLayout()

        title = QLabel("⚡ Update Speed")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Lock button
        self.speed_lock_btn = QPushButton("🔓")  # Start unlocked
        self.speed_lock_btn.setCheckable(True)
        self.speed_lock_btn.setChecked(False)  # Start unchecked (unlocked)
        self.speed_lock_btn.setFixedSize(30, 30)
        self.speed_lock_btn.clicked.connect(self.toggle_speed_lock)
        self.speed_lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.danger};
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton:checked {{
                background-color: {settings.theme.danger};
            }}
            QPushButton:!checked {{
                background-color: {settings.theme.success};
            }}
        """)
        title_layout.addWidget(self.speed_lock_btn)

        layout.addLayout(title_layout)

        # Speed selector
        self.speed_combo = QComboBox()
        for speed_name in ['SLOW', 'NORMAL', 'FAST', 'REALTIME']:
            config = UPDATE_SPEED_CONFIGS[speed_name]
            self.speed_combo.addItem(config['description'], speed_name)

        self.speed_combo.setEnabled(True)  # Start unlocked for easy access
        self.speed_combo.currentIndexChanged.connect(self.on_speed_changed)
        self.speed_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                border: 1px solid {settings.theme.border_color};
                border-radius: 6px;
                padding: 10px;
                font-size: {settings.theme.font_size_sm}px;
            }}
            QComboBox:hover {{
                border-color: {settings.theme.accent};
            }}
            QComboBox QAbstractItemView {{
                background-color: {settings.theme.surface_light};
                color: {settings.theme.text_primary};
                selection-background-color: {settings.theme.accent};
                border: 1px solid {settings.theme.border_color};
            }}
        """)
        layout.addWidget(self.speed_combo)

        return frame

    def create_quick_orders_section(self) -> QFrame:
        """Create quick order buttons"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("🎯 Quick Orders")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # BUY button
        buy_button = QPushButton("📈 BUY")
        buy_button.clicked.connect(lambda: self._on_order_button('BUY'))
        buy_button.setFixedHeight(50)
        buy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.success};
                color: {settings.theme.background};
                border: none;
                border-radius: 8px;
                font-size: {settings.theme.font_size_lg}px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {settings.theme.bullish};
            }}
            QPushButton:pressed {{
            }}
        """)
        button_layout.addWidget(buy_button)

        # SELL button
        sell_button = QPushButton("📉 SELL")
        sell_button.clicked.connect(lambda: self._on_order_button('SELL'))
        sell_button.setFixedHeight(50)
        sell_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.danger};
                color: {settings.theme.background};
                border: none;
                border-radius: 8px;
                font-size: {settings.theme.font_size_lg}px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {settings.theme.bearish};
            }}
            QPushButton:pressed {{
            }}
        """)
        button_layout.addWidget(sell_button)

        layout.addLayout(button_layout)

        return frame

    def create_risk_section(self) -> QFrame:
        """Create risk management section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title with lock button
        title_layout = QHBoxLayout()

        title = QLabel("💰 Risk Management")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Lock button
        self.risk_lock_btn = QPushButton("🔒")
        self.risk_lock_btn.setCheckable(True)
        self.risk_lock_btn.setChecked(True)
        self.risk_lock_btn.setFixedSize(30, 30)
        self.risk_lock_btn.clicked.connect(self.toggle_risk_lock)
        self.risk_lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {settings.theme.danger};
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton:checked {{
                background-color: {settings.theme.danger};
            }}
            QPushButton:!checked {{
                background-color: {settings.theme.success};
            }}
        """)
        title_layout.addWidget(self.risk_lock_btn)

        layout.addLayout(title_layout)

        # Risk per trade slider
        risk_layout = QVBoxLayout()
        risk_layout.setSpacing(6)

        self.risk_label = QLabel(f"Risk per Trade: {settings.trading.default_risk_percent}%")
        self.risk_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_sm}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        risk_layout.addWidget(self.risk_label)

        self.risk_slider = QSlider(Qt.Orientation.Horizontal)
        self.risk_slider.setRange(10, 200)  # 0.1% to 2.0% (stored as int * 10)
        self.risk_slider.setValue(int(settings.trading.default_risk_percent * 10))
        self.risk_slider.setEnabled(False)  # Start locked
        self.risk_slider.valueChanged.connect(self.on_risk_changed)
        self.risk_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {settings.theme.surface_light};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {settings.theme.accent};
                border: 3px solid {settings.theme.background};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {settings.theme.success};
            }}
            QSlider::sub-page:horizontal {{
                background: {settings.theme.accent};
                border-radius: 4px;
            }}
        """)
        risk_layout.addWidget(self.risk_slider)

        layout.addLayout(risk_layout)

        return frame

    def create_filters_section(self) -> QFrame:
        """Create institutional filters section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("🔍 Institutional Filters")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # ALL 20 INSTITUTIONAL FILTERS (matching EA exactly)
        filters = [
            # Core Filters
            ('UseVolumeFilter', '📊 Volume Filter', True),
            ('UseSpreadFilter', '📉 Spread Filter', True),
            ('UseSlippageFilter', '⚡ Slippage Protection', True),
            ('UseSessionFilter', '🕒 Session Filter (London/NY)', True),
            ('UseNewsFilter', '📰 News Event Filter', True),

            # Technical Filters
            ('UseMTFConfirmation', '📈 Multi-Timeframe Confirmation', True),
            ('UseCorrelationFilter', '🔗 Correlation Filter', True),
            ('UseTrendFilter', '📊 Trend Filter', True),
            ('UseATRFilter', '📏 ATR Volatility Filter', True),

            # Smart Money Filters
            ('UseOrderBlockFilter', '💎 Order Block Filter', True),
            ('UseFVGFilter', '🔵 Fair Value Gap Filter', True),
            ('UseLiquidityFilter', '💧 Liquidity Sweep Filter', True),
            ('UseStructureFilter', '🏗️ Market Structure Filter', True),

            # Risk Filters
            ('UseMaxTradesFilter', '🎯 Max Trades Limit', True),
            ('UseDrawdownFilter', '📉 Drawdown Protection', True),
            ('UseWinStreakFilter', '🔥 Win Streak Management', True),
            ('UseLossStreakFilter', '❄️ Loss Streak Protection', True),

            # Advanced Filters
            ('UsePatternQualityFilter', '⭐ Pattern Quality Filter', True),
            ('UseConfluenceFilter', '✨ Confluence Filter (3+ required)', True),
            ('UseSwingFilter', '🎢 Swing Point Filter', True),
        ]

        self.filter_checkboxes = {}

        for key, label, default in filters:
            checkbox = self.create_styled_checkbox(label, default)
            # Use toggled signal instead of stateChanged for cleaner bool handling
            checkbox.toggled.connect(
                lambda checked, k=key: self.on_filter_toggled(k, checked)
            )
            self.filter_checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        return frame

    def create_smc_section(self) -> QFrame:
        """Create Smart Money Concepts section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("💎 Smart Money Concepts")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # SMC checkboxes
        smc_features = [
            ('liquidity', 'Liquidity Sweep', True),
            ('order_blocks', 'Order Blocks', True),
            ('fvg', 'Fair Value Gaps', True),
            ('market_structure', 'Market Structure', True),
        ]

        self.smc_checkboxes = {}

        for key, label, default in smc_features:
            checkbox = self.create_styled_checkbox(label, default)
            # Use toggled signal instead of stateChanged for cleaner bool handling
            checkbox.toggled.connect(
                lambda checked, k=key: self.setting_changed.emit(f'use_{k}', checked)
            )
            self.smc_checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        return frame

    def create_ml_section(self) -> QFrame:
        """Create Machine Learning section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("🤖 Machine Learning")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # ML enable checkbox
        self.ml_enable_checkbox = self.create_styled_checkbox("Enable ML Filter", settings.trading.use_ml_filter)
        # Use toggled signal instead of stateChanged for cleaner bool handling
        self.ml_enable_checkbox.toggled.connect(
            lambda checked: self.setting_changed.emit('use_ml_filter', checked)
        )
        layout.addWidget(self.ml_enable_checkbox)

        return frame

    def create_visual_section(self) -> QFrame:
        """Create visual controls section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Title
        title = QLabel("👁️ Chart Visuals")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # Visual checkboxes
        visuals = [
            ('patterns', 'Pattern Boxes', True),
            ('zones', 'FVG/OB Zones', True),
            ('liquidity', 'Liquidity Levels', True),
            ('indicators', 'Indicators', True),
        ]

        self.visual_checkboxes = {}

        for key, label, default in visuals:
            checkbox = self.create_styled_checkbox(label, default)
            # Use toggled signal instead of stateChanged for cleaner bool handling
            checkbox.toggled.connect(
                lambda checked, k=key: self.setting_changed.emit(f'show_{k}', checked)
            )
            self.visual_checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        return frame

    def create_styled_checkbox(self, text: str, checked: bool = False) -> QCheckBox:
        """Create styled checkbox"""

        checkbox = QCheckBox(text)
        checkbox.setChecked(checked)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_sm}px;
                spacing: 8px;
                background: transparent;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {settings.theme.border_color_light};
                border-radius: 4px;
                background-color: {settings.theme.surface_light};
            }}
            QCheckBox::indicator:checked {{
                background-color: {settings.theme.success};
                border-color: {settings.theme.success};
                image: none;
            }}
            QCheckBox::indicator:hover {{
                border-color: {settings.theme.accent};
            }}
        """)
        return checkbox

    def _timestamp(self):
        """Get formatted timestamp for status log"""
        return datetime.now().strftime("%H:%M:%S")

    def _log_status(self, message: str, color: str = None):
        """Add message to status log"""
        timestamp = self._timestamp()
        current_text = self.status_text.toPlainText()

        # Keep only last 5 messages
        lines = current_text.split('\n')
        if len(lines) > 5:
            lines = lines[-4:]

        new_message = f"[{timestamp}] {message}"
        lines.append(new_message)

        self.status_text.setPlainText('\n'.join(lines))

        # Scroll to bottom
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def _on_order_button(self, order_type: str):
        """Handle quick order button click"""
        self._log_status(f"✓ {order_type} order requested")
        self.order_requested.emit(order_type)

    def toggle_trading_mode(self):
        """Toggle between indicator and trading mode"""

        is_trading = self.mode_button.isChecked()

        if is_trading:
            self.mode_button.setText("🟢 AUTO TRADING")
            self.mode_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.success};
                    color: {settings.theme.background};
                    border: none;
                    border-radius: 10px;
                    font-size: {settings.theme.font_size_xl}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                }}
            """)
            self._log_status("✓ AUTO TRADING MODE ENABLED")
        else:
            self.mode_button.setText("🔴 INDICATOR MODE")
            self.mode_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {settings.theme.warning};
                    color: {settings.theme.background};
                    border: none;
                    border-radius: 10px;
                    font-size: {settings.theme.font_size_xl}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                }}
            """)
            self._log_status("✓ INDICATOR MODE ENABLED")

        # Send command to EA
        command_manager.send_trading_mode(is_trading)

        self.setting_changed.emit('enable_trading', is_trading)

    def on_speed_changed(self, index: int):
        """Handle update speed change"""

        speed = self.speed_combo.itemData(index)
        if speed:
            speed_text = UPDATE_SPEED_CONFIGS[speed]['description']
            self._log_status(f"✓ Update speed: {speed_text}")
            self.setting_changed.emit('update_speed', speed)

    def on_risk_changed(self, value: int):
        """Handle risk slider change"""

        risk_percent = value / 10.0  # Convert back to percentage
        self.risk_label.setText(f"Risk per Trade: {risk_percent:.1f}%")
        settings.trading.default_risk_percent = risk_percent
        self._log_status(f"✓ Risk per trade: {risk_percent:.1f}%")
        self.setting_changed.emit('risk_percent', risk_percent)

        # Send to EA
        command_manager.send_risk_update(risk_percent)

    def on_filter_toggled(self, filter_name: str, enabled: bool):
        """
        Handle filter checkbox toggle
        Sends command to MT5 EA to enable/disable the filter

        Args:
            filter_name: EA filter variable name (e.g., 'UseVolumeFilter')
            enabled: True to enable, False to disable
        """
        # Send command to EA via JSON
        command_manager.send_filter_toggle(filter_name, enabled)

        # Log the change
        status = "ENABLED" if enabled else "DISABLED"
        self._log_status(f"✓ {filter_name}: {status}")

        # Emit signal for any local listeners
        self.setting_changed.emit(filter_name, enabled)

    def toggle_speed_lock(self):
        """Toggle lock state for Update Speed control"""
        is_locked = self.speed_lock_btn.isChecked()
        self.speed_locked = is_locked
        self.speed_combo.setEnabled(not is_locked)

        if is_locked:
            self.speed_lock_btn.setText("🔒")
            self._log_status("✓ Update Speed LOCKED")
        else:
            self.speed_lock_btn.setText("🔓")
            self._log_status("✓ Update Speed UNLOCKED")

    def toggle_risk_lock(self):
        """Toggle lock state for Risk slider"""
        is_locked = self.risk_lock_btn.isChecked()
        self.risk_locked = is_locked
        self.risk_slider.setEnabled(not is_locked)

        if is_locked:
            self.risk_lock_btn.setText("🔒")
            self._log_status("✓ Risk slider LOCKED")
        else:
            self.risk_lock_btn.setText("🔓")
            self._log_status("✓ Risk slider UNLOCKED")
