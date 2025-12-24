"""
Merged Institutional Controls Panel
Combines the best of institutional_panel.py and controls_panel.py
No duplication, all features in one comprehensive left panel
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                             QPushButton, QSlider, QFrame, QGroupBox, QComboBox,
                             QDoubleSpinBox, QScrollArea, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime


class MergedInstitutionalPanel(QWidget):
    """
    Comprehensive institutional trading panel merging all features
    """

    # Signals
    filter_toggled = pyqtSignal(str, bool)  # filter_name, enabled
    mode_changed = pyqtSignal(str)  # AUTO/MANUAL
    setting_changed = pyqtSignal(str, object)  # setting_name, value
    order_requested = pyqtSignal(str)  # BUY/SELL

    def __init__(self):
        super().__init__()
        self.filters = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the comprehensive panel UI"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)

        # === TITLE ===
        title = QLabel("INSTITUTIONAL TRADING ROBOT v3.0")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))  # Increased from 11 to 15
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00ff00; background-color: #1a1a1a; padding: 8px; border-radius: 5px;")
        layout.addWidget(title)

        # === STATUS LOG ===
        layout.addWidget(self.create_status_log_section())

        # === BUTTON STATUS (MODE + ML) ===
        layout.addWidget(self.create_button_status_section())

        # === QUICK ORDER BUTTONS ===
        layout.addWidget(self.create_quick_orders_section())

        # === RISK MANAGEMENT ===
        layout.addWidget(self.create_risk_management_section())

        # === INSTITUTIONAL FILTERS ===
        layout.addWidget(self.create_filters_section())

        # === SMART MONEY CONCEPTS ===
        layout.addWidget(self.create_smart_money_section())

        # === MACHINE LEARNING ===
        layout.addWidget(self.create_ml_section())

        # === CHART VISUALS ===
        layout.addWidget(self.create_chart_visuals_section())

        # === HEAVY ZONES LEGEND ===
        layout.addWidget(self.create_heavy_zones_section())

        # === MARKET STATUS ===
        layout.addWidget(self.create_market_status_section())

        # === MARKET CONTEXT ===
        layout.addWidget(self.create_market_context_section())

        # === RISK METRICS ===
        layout.addWidget(self.create_risk_metrics_section())

        # PERFORMANCE section removed per user request (redundant with chart display)

        layout.addStretch()

        # Set container to scroll area
        scroll.setWidget(container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 2px solid #00ff00;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                font-size: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #00ff00;
                font-size: 15px;
            }
        """)

    def create_status_log_section(self) -> QGroupBox:
        """Create status log section"""
        group = QGroupBox("📊 STATUS LOG")
        layout = QVBoxLayout()

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(80)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #00ff00;
                border-radius: 3px;
                color: #00ff00;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                padding: 4px;
            }
        """)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.setPlainText(f"[{timestamp}] Panel initialized\n[{timestamp}] Ready")
        layout.addWidget(self.status_text)

        group.setLayout(layout)
        return group

    def create_button_status_section(self) -> QGroupBox:
        """Create button status section"""
        group = QGroupBox("🔴 TRADING MODE")
        layout = QVBoxLayout()

        # Auto Trading Mode
        mode_layout = QHBoxLayout()
        self.mode_toggle = QPushButton("MODE: AUTO TRADING")
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setChecked(True)
        self.mode_toggle.setFixedHeight(55)  # Increased from 45 to 55
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:!checked {
                background-color: #aa5500;
            }
        """)
        self.mode_toggle.clicked.connect(self.on_mode_toggled)
        mode_layout.addWidget(self.mode_toggle)
        layout.addLayout(mode_layout)

        # AI System Status
        ai_label = QLabel("AI: SYSTEM ENABLED - ML Active")
        ai_label.setStyleSheet("color: #00aaff; padding: 5px; font-size: 14px;")
        ai_label.setWordWrap(True)
        layout.addWidget(ai_label)

        # ML System Enable
        ml_layout = QHBoxLayout()
        ml_label = QLabel("ML System:")
        ml_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        self.ml_toggle = QPushButton("ON")
        self.ml_toggle.setCheckable(True)
        self.ml_toggle.setChecked(True)
        self.ml_toggle.setFixedWidth(80)  # Increased from 60 to 80
        self.ml_toggle.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        ml_layout.addWidget(ml_label)
        ml_layout.addStretch()
        ml_layout.addWidget(self.ml_toggle)
        layout.addLayout(ml_layout)

        group.setLayout(layout)
        return group

    def create_quick_orders_section(self) -> QGroupBox:
        """Create quick order buttons"""
        group = QGroupBox("⚡ QUICK ORDERS")
        layout = QHBoxLayout()

        # Buy button
        buy_btn = QPushButton("📈 BUY")
        buy_btn.setFixedHeight(50)  # Increased from 40 to 50
        buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
        """)
        buy_btn.clicked.connect(lambda: self.order_requested.emit("BUY"))
        layout.addWidget(buy_btn)

        # Sell button
        sell_btn = QPushButton("📉 SELL")
        sell_btn.setFixedHeight(50)  # Increased from 40 to 50
        sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #aa0000;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        sell_btn.clicked.connect(lambda: self.order_requested.emit("SELL"))
        layout.addWidget(sell_btn)

        group.setLayout(layout)
        return group

    def create_risk_management_section(self) -> QGroupBox:
        """Create risk management controls"""
        group = QGroupBox("⚠️ RISK MANAGEMENT")
        layout = QVBoxLayout()

        # Risk %
        risk_layout = QHBoxLayout()
        risk_label = QLabel("Risk %:")
        risk_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        self.risk_spin = QDoubleSpinBox()
        self.risk_spin.setRange(0.1, 5.0)
        self.risk_spin.setValue(1.0)
        self.risk_spin.setSingleStep(0.1)
        self.risk_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #00ff00;
                border-radius: 3px;
                padding: 6px;
                font-size: 14px;
                min-height: 30px;
            }
        """)
        risk_layout.addWidget(risk_label)
        risk_layout.addWidget(self.risk_spin)
        layout.addLayout(risk_layout)

        group.setLayout(layout)
        return group

    def create_filters_section(self) -> QGroupBox:
        """Create institutional filters section"""
        group = QGroupBox("📊 INSTITUTIONAL FILTERS")
        layout = QVBoxLayout()

        # Import filter_manager to sync with backend state
        from core.filter_manager import filter_manager

        # Define all filters - SYNC with filter_manager defaults!
        filter_list = [
            ("Volume Filter", filter_manager.volume_filter),
            ("Spread Filter", filter_manager.spread_filter),  # Now syncs with backend (False)
            ("Strong Price Model", filter_manager.strong_price_model),
            ("Multi-Timeframe", filter_manager.multi_timeframe),
            ("Volatility Filter", filter_manager.volatility_filter),
            ("Sentiment Filter", filter_manager.sentiment_filter),
            ("Correlation Filter", filter_manager.correlation_filter),
            ("Volatility Adaptation", filter_manager.volatility_adaptation),
            ("Dynamic Risk", filter_manager.dynamic_risk),
            ("Pattern Decay", filter_manager.pattern_decay)
        ]

        for filter_name, enabled in filter_list:
            filter_widget = self.create_filter_row(filter_name, enabled)
            layout.addWidget(filter_widget)

        group.setLayout(layout)
        return group

    def create_filter_row(self, name: str, enabled: bool) -> QWidget:
        """Create a single filter row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)

        # Checkbox
        checkbox = QCheckBox(name)
        checkbox.setChecked(enabled)
        checkbox.setStyleSheet("color: #ffffff; font-size: 14px;")
        checkbox.stateChanged.connect(lambda state: self.on_filter_toggled(name, state == Qt.CheckState.Checked.value))

        # Status indicator
        status = QLabel("ON" if enabled else "OFF")
        status.setFixedWidth(50)  # Increased from 35 to 50
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet(f"""
            background-color: {'#00aa00' if enabled else '#aa0000'};
            color: white;
            font-weight: bold;
            border-radius: 3px;
            padding: 2px;
            font-size: 13px;
        """)

        layout.addWidget(checkbox)
        layout.addStretch()
        layout.addWidget(status)

        # Store references
        self.filters[name] = {
            'checkbox': checkbox,
            'status': status
        }

        return widget

    def create_smart_money_section(self) -> QGroupBox:
        """Create smart money concepts section"""
        group = QGroupBox("💰 SMART MONEY CONCEPTS")
        layout = QVBoxLayout()

        # Import filter_manager to sync with backend state
        from core.filter_manager import filter_manager

        smc_list = [
            ("Liquidity Sweep", filter_manager.liquidity_sweep),
            ("Retail Trap Detection", filter_manager.retail_trap_detection),
            ("Order Block Invalidation", filter_manager.order_block_invalidation),
            ("Market Structure", filter_manager.market_structure)
        ]

        for smc_name, enabled in smc_list:
            smc_widget = self.create_filter_row(smc_name, enabled)
            layout.addWidget(smc_widget)

        # Add Show Chart Legend checkbox (for overlay legend on chart)
        legend_checkbox = QCheckBox("Show Chart Legend")
        legend_checkbox.setChecked(False)  # Off by default
        legend_checkbox.setStyleSheet("color: #ffffff; font-size: 14px; padding: 5px;")
        legend_checkbox.stateChanged.connect(
            lambda state: self.on_legend_toggled(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(legend_checkbox)

        group.setLayout(layout)
        return group

    def create_ml_section(self) -> QGroupBox:
        """Create machine learning section"""
        group = QGroupBox("🤖 MACHINE LEARNING")
        layout = QVBoxLayout()

        # Import filter_manager to sync with backend state
        from core.filter_manager import filter_manager

        ml_list = [
            ("Pattern Tracking", filter_manager.pattern_tracking),
            ("Parameter Adaptation", filter_manager.parameter_adaptation),
            ("Regime Strategy", filter_manager.regime_strategy)
        ]

        for ml_name, enabled in ml_list:
            ml_widget = self.create_filter_row(ml_name, enabled)
            layout.addWidget(ml_widget)

        group.setLayout(layout)
        return group

    def create_chart_visuals_section(self) -> QGroupBox:
        """Create chart visuals toggle section"""
        group = QGroupBox("🎛️ CHART VISUALS")
        layout = QVBoxLayout()

        visuals = [
            "Pattern Boxes",
            "Liquidity Lines",
            "FVG Zones",
            "Order Blocks",
            "Monthly Zones",
            "Volatility Zones",
            "Commentary"
        ]

        for visual in visuals:
            checkbox = QCheckBox(visual)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("color: #ffffff; font-size: 14px;")
            checkbox.stateChanged.connect(lambda state, v=visual: self.on_visual_toggled(v, state == Qt.CheckState.Checked.value))
            layout.addWidget(checkbox)

        group.setLayout(layout)
        return group

    def create_heavy_zones_section(self) -> QGroupBox:
        """Create heavy zones color legend"""
        group = QGroupBox("🎨 ZONE LEGEND")
        layout = QVBoxLayout()

        zones = [
            ("Bullish OB", "#00ff00"),
            ("Bearish OB", "#ff0000"),
            ("FVG Up", "#00ffff"),
            ("FVG Down", "#ff00ff"),
            ("Liquidity", "#ffaa00")
        ]

        for zone_name, color in zones:
            zone_layout = QHBoxLayout()

            color_box = QLabel()
            color_box.setFixedSize(25, 15)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #ffffff; border-radius: 2px;")

            label = QLabel(zone_name)
            label.setStyleSheet("color: #ffffff; font-size: 14px;")

            zone_layout.addWidget(color_box)
            zone_layout.addWidget(label)
            zone_layout.addStretch()

            layout.addLayout(zone_layout)

        group.setLayout(layout)
        return group

    def create_market_status_section(self) -> QGroupBox:
        """Create market status section"""
        group = QGroupBox("📈 MARKET STATUS")
        layout = QVBoxLayout()

        self.market_status_label = QLabel("Analyzing market...")
        self.market_status_label.setStyleSheet("color: #ffffff; padding: 5px; font-size: 14px;")
        self.market_status_label.setWordWrap(True)
        layout.addWidget(self.market_status_label)

        group.setLayout(layout)
        return group

    def create_market_context_section(self) -> QGroupBox:
        """Create market context section"""
        group = QGroupBox("📊 MARKET CONTEXT")
        layout = QVBoxLayout()

        self.session_label = QLabel("Session: LONDON")
        self.session_label.setStyleSheet("color: #00aaff; font-size: 14px;")
        layout.addWidget(self.session_label)

        self.tf_label = QLabel("Timeframe: H4/H1")
        self.tf_label.setStyleSheet("color: #00aaff; font-size: 14px;")
        layout.addWidget(self.tf_label)

        self.trend_label = QLabel("Trend: BULLISH")
        self.trend_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.trend_label)

        self.structure_label = QLabel("Structure: HH forming")
        self.structure_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        layout.addWidget(self.structure_label)

        group.setLayout(layout)
        return group

    def create_risk_metrics_section(self) -> QGroupBox:
        """Create risk metrics section"""
        group = QGroupBox("⚠️ RISK METRICS")
        layout = QVBoxLayout()

        self.risk_label = QLabel("Account Risk: 2.0%\nDrawdown: 5.2%\nWin Rate: 68%")
        self.risk_label.setStyleSheet("color: #ffaa00; padding: 5px; font-size: 14px;")
        self.risk_label.setWordWrap(True)
        layout.addWidget(self.risk_label)

        group.setLayout(layout)
        return group

    # PERFORMANCE SECTION REMOVED - User confirmed it's redundant with chart display
    # def create_performance_section(self) -> QGroupBox:
    #     """Create performance section"""
    #     group = QGroupBox("📊 PERFORMANCE")
    #     layout = QVBoxLayout()
    #
    #     self.performance_label = QLabel("Today: +2.3%\nWeek: +8.7%\nMonth: +15.2%")
    #     self.performance_label.setStyleSheet("color: #00ff00; padding: 5px; font-weight: bold; font-size: 14px;")
    #     self.performance_label.setWordWrap(True)
    #     layout.addWidget(self.performance_label)
    #
    #     group.setLayout(layout)
    #     return group

    def on_mode_toggled(self):
        """Handle mode toggle"""
        if self.mode_toggle.isChecked():
            self.mode_toggle.setText("MODE: AUTO TRADING")
            self.mode_changed.emit("AUTO")
            self.log_status("Switched to AUTO TRADING mode")
        else:
            self.mode_toggle.setText("MODE: INDICATOR ONLY")
            self.mode_changed.emit("MANUAL")
            self.log_status("Switched to INDICATOR ONLY mode")

    def on_filter_toggled(self, name: str, enabled: bool):
        """Handle filter toggle"""
        if name in self.filters:
            status_label = self.filters[name]['status']
            status_label.setText("ON" if enabled else "OFF")
            status_label.setStyleSheet(f"""
                background-color: {'#00aa00' if enabled else '#aa0000'};
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 2px;
                font-size: 13px;
            """)

        self.filter_toggled.emit(name, enabled)
        self.log_status(f"Filter {name} {'enabled' if enabled else 'disabled'}")

    def on_visual_toggled(self, name: str, enabled: bool):
        """Handle visual element toggle"""
        self.setting_changed.emit(f'visual_{name}', enabled)
        self.log_status(f"Visual {name} {'enabled' if enabled else 'disabled'}")

    def on_legend_toggled(self, enabled: bool):
        """Handle chart legend toggle"""
        self.setting_changed.emit('visual_smart_money_legend', enabled)
        self.log_status(f"Chart Legend {'enabled' if enabled else 'disabled'}")

    def log_status(self, message: str):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

    def update_market_status(self, status: str):
        """Update market status display"""
        self.market_status_label.setText(status)

    def update_context(self, session: str, timeframe: str, trend: str, structure: str):
        """Update market context"""
        self.session_label.setText(f"Session: {session}")
        self.tf_label.setText(f"Timeframe: {timeframe}")
        self.trend_label.setText(f"Trend: {trend}")
        self.trend_label.setStyleSheet(f"color: {'#00ff00' if 'BULL' in trend.upper() else '#ff0000'}; font-weight: bold; font-size: 14px;")
        self.structure_label.setText(f"Structure: {structure}")

    def update_risk_metrics(self, account_risk: float, drawdown: float, win_rate: float):
        """Update risk metrics"""
        self.risk_label.setText(
            f"Account Risk: {account_risk:.1f}%\n"
            f"Drawdown: {drawdown:.1f}%\n"
            f"Win Rate: {win_rate:.0f}%"
        )

    # PERFORMANCE SECTION REMOVED - No longer needed
    # def update_performance(self, today: float, week: float, month: float):
    #     """Update performance stats"""
    #     self.performance_label.setText(
    #         f"Today: {today:+.1f}%\n"
    #         f"Week: {week:+.1f}%\n"
    #         f"Month: {month:+.1f}%"
    #     )
    #     color = "#00ff00" if today >= 0 else "#ff0000"
    #     self.performance_label.setStyleSheet(f"color: {color}; padding: 5px; font-weight: bold; font-size: 14px;")
