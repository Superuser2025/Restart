"""
Institutional Trading Panel - Left Sidebar
Replicates the comprehensive filter and status panel from InstitutionalTradingRobot_v3.mq5
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QCheckBox, QGroupBox, QScrollArea,
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class InstitutionalPanel(QWidget):
    """
    Comprehensive left panel showing all institutional filters and status
    """

    # Signals
    filter_toggled = pyqtSignal(str, bool)  # filter_name, enabled
    mode_changed = pyqtSignal(str)  # AUTO/MANUAL

    def __init__(self):
        super().__init__()
        self.filters = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the institutional panel UI"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("INSTITUTIONAL TRADING ROBOT v3.0")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00ff00; background-color: #1a1a1a; padding: 10px; border-radius: 5px;")
        layout.addWidget(title)

        # === BUTTON STATUS ===
        layout.addWidget(self.create_button_status_section())

        # === INSTITUTIONAL FILTERS ===
        layout.addWidget(self.create_filters_section())

        # === HEAVY ZONES ===
        layout.addWidget(self.create_heavy_zones_section())

        # === MARKET STATUS ===
        layout.addWidget(self.create_market_status_section())

        # === MARKET CONTEXT ===
        layout.addWidget(self.create_market_context_section())

        # === RISK METRICS ===
        layout.addWidget(self.create_risk_metrics_section())

        # === PERFORMANCE ===
        layout.addWidget(self.create_performance_section())

        # === CHART VISUALS ===
        layout.addWidget(self.create_chart_visuals_section())

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
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #00ff00;
            }
        """)

    def create_button_status_section(self) -> QGroupBox:
        """Create button status section"""
        group = QGroupBox("🔴 BUTTON STATUS")
        layout = QVBoxLayout()

        # Auto Trading Mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("MODE: AUTO TRADING")
        mode_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.mode_toggle = QPushButton("ON")
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setChecked(True)
        self.mode_toggle.setFixedWidth(60)
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:checked {
                background-color: #00aa00;
            }
            QPushButton:!checked {
                background-color: #aa0000;
            }
        """)
        self.mode_toggle.clicked.connect(self.on_mode_toggled)
        mode_layout.addWidget(mode_label)
        mode_layout.addStretch()
        mode_layout.addWidget(self.mode_toggle)
        layout.addLayout(mode_layout)

        # AI System Status
        ai_label = QLabel("AI: SYSTEM ENABLED - Machine Learning active")
        ai_label.setStyleSheet("color: #00aaff; padding: 5px;")
        layout.addWidget(ai_label)

        # ML System Enable
        ml_layout = QHBoxLayout()
        ml_label = QLabel("ML System Enable:")
        ml_label.setStyleSheet("color: #ffffff;")
        self.ml_toggle = QPushButton("active/ON")
        self.ml_toggle.setCheckable(True)
        self.ml_toggle.setChecked(True)
        self.ml_toggle.setFixedWidth(80)
        self.ml_toggle.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        ml_layout.addWidget(ml_label)
        ml_layout.addStretch()
        ml_layout.addWidget(self.ml_toggle)
        layout.addLayout(ml_layout)

        group.setLayout(layout)
        return group

    def create_filters_section(self) -> QGroupBox:
        """Create institutional filters section"""
        group = QGroupBox("📊 INSTITUTIONAL FILTERS")
        layout = QVBoxLayout()

        # Define all filters with their initial states
        filter_list = [
            ("Volume Filter", True, 30),
            ("Spread Filter", True, 25),
            ("Strong Price Model", True, 45),
            ("Multi-Timeframe", True, 60),
            ("Volatility Filter", True, 35),
            ("Sentiment Filter", True, 50),
            ("Correlation Filter", True, 40),
            ("Volatility Adaptation", True, 55),
            ("Dynamic Risk", True, 70),
            ("Pattern Decay", True, 45)
        ]

        for filter_name, enabled, percentage in filter_list:
            filter_widget = self.create_filter_row(filter_name, enabled, percentage)
            layout.addWidget(filter_widget)
            layout.addSpacing(5)

        group.setLayout(layout)
        return group

    def create_filter_row(self, name: str, enabled: bool, percentage: int) -> QWidget:
        """Create a single filter row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)

        # Checkbox
        checkbox = QCheckBox(name)
        checkbox.setChecked(enabled)
        checkbox.setStyleSheet("color: #ffffff;")
        checkbox.stateChanged.connect(lambda state: self.on_filter_toggled(name, state == Qt.CheckState.Checked.value))

        # Percentage label
        pct_label = QLabel(f"{percentage}%")
        pct_label.setFixedWidth(50)
        pct_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        pct_label.setStyleSheet("color: #00ff00; font-weight: bold;")

        # Status indicator
        status = QLabel("ON" if enabled else "OFF")
        status.setFixedWidth(40)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet(f"""
            background-color: {'#00aa00' if enabled else '#aa0000'};
            color: white;
            font-weight: bold;
            border-radius: 3px;
            padding: 3px;
        """)

        layout.addWidget(checkbox)
        layout.addStretch()
        layout.addWidget(pct_label)
        layout.addWidget(status)

        # Store references
        self.filters[name] = {
            'checkbox': checkbox,
            'percentage': pct_label,
            'status': status
        }

        return widget

    def create_heavy_zones_section(self) -> QGroupBox:
        """Create heavy zones visualization section"""
        group = QGroupBox("🎨 HEAVY ZONES / CONCEPTS")
        layout = QGridLayout()

        # Define zone colors
        zones = [
            ("Bullish OB", "#00ff00"),
            ("Bearish OB", "#ff0000"),
            ("FVG Up", "#00ffff"),
            ("FVG Down", "#ff00ff"),
            ("Liquidity", "#ffaa00"),
            ("Mitigation", "#aa00ff")
        ]

        row = 0
        col = 0
        for zone_name, color in zones:
            # Zone box
            zone_widget = QWidget()
            zone_layout = QHBoxLayout(zone_widget)
            zone_layout.setContentsMargins(2, 2, 2, 2)

            color_box = QLabel()
            color_box.setFixedSize(30, 20)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #ffffff; border-radius: 3px;")

            label = QLabel(zone_name)
            label.setStyleSheet("color: #ffffff; font-size: 10px;")

            zone_layout.addWidget(color_box)
            zone_layout.addWidget(label)
            zone_layout.addStretch()

            layout.addWidget(zone_widget, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        group.setLayout(layout)
        return group

    def create_market_status_section(self) -> QGroupBox:
        """Create market status section"""
        group = QGroupBox("📈 MARKET STATUS")
        layout = QVBoxLayout()

        self.market_status_label = QLabel("Calculating...")
        self.market_status_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.market_status_label.setWordWrap(True)
        layout.addWidget(self.market_status_label)

        group.setLayout(layout)
        return group

    def create_market_context_section(self) -> QGroupBox:
        """Create market context section"""
        group = QGroupBox("📊 MARKET CONTEXT")
        layout = QVBoxLayout()

        # Session
        self.session_label = QLabel("Session: LONDON")
        self.session_label.setStyleSheet("color: #00aaff;")
        layout.addWidget(self.session_label)

        # Timeframe
        self.tf_label = QLabel("Timeframe: H4/H1")
        self.tf_label.setStyleSheet("color: #00aaff;")
        layout.addWidget(self.tf_label)

        # Trend
        self.trend_label = QLabel("Trend: BULLISH")
        self.trend_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        layout.addWidget(self.trend_label)

        # Structure
        self.structure_label = QLabel("Structure: HH forming")
        self.structure_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.structure_label)

        group.setLayout(layout)
        return group

    def create_risk_metrics_section(self) -> QGroupBox:
        """Create risk metrics section"""
        group = QGroupBox("⚠️ RISK METRICS")
        layout = QVBoxLayout()

        self.risk_label = QLabel("Account Risk: 2.0%\nDrawdown: 5.2%\nWin Rate: 68%")
        self.risk_label.setStyleSheet("color: #ffaa00; padding: 5px;")
        self.risk_label.setWordWrap(True)
        layout.addWidget(self.risk_label)

        group.setLayout(layout)
        return group

    def create_performance_section(self) -> QGroupBox:
        """Create performance section"""
        group = QGroupBox("📊 PERFORMANCE")
        layout = QVBoxLayout()

        self.performance_label = QLabel("Today: +2.3%\nWeek: +8.7%\nMonth: +15.2%")
        self.performance_label.setStyleSheet("color: #00ff00; padding: 5px; font-weight: bold;")
        self.performance_label.setWordWrap(True)
        layout.addWidget(self.performance_label)

        group.setLayout(layout)
        return group

    def create_chart_visuals_section(self) -> QGroupBox:
        """Create chart visuals toggle section"""
        group = QGroupBox("🎛️ CHART VISUALS")
        layout = QVBoxLayout()

        visuals = [
            "Pattern Boxes",
            "Liquidity Lines",
            "EV Values",
            "FVG Zones",
            "Order Blocks",
            "Monthly Zones",
            "Volatility Zones",
            "Fair Value Only",
            "Commentary"
        ]

        for visual in visuals:
            checkbox = QCheckBox(visual)
            checkbox.setChecked(True)
            checkbox.setStyleSheet("color: #ffffff;")
            checkbox.stateChanged.connect(lambda state, v=visual: self.on_visual_toggled(v, state == Qt.CheckState.Checked.value))
            layout.addWidget(checkbox)

        group.setLayout(layout)
        return group

    def on_mode_toggled(self):
        """Handle mode toggle"""
        if self.mode_toggle.isChecked():
            self.mode_toggle.setText("ON")
            self.mode_changed.emit("AUTO")
        else:
            self.mode_toggle.setText("OFF")
            self.mode_changed.emit("MANUAL")

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
                padding: 3px;
            """)

        self.filter_toggled.emit(name, enabled)
        print(f"[Institutional Panel] Filter {name} {'enabled' if enabled else 'disabled'}")

    def on_visual_toggled(self, name: str, enabled: bool):
        """Handle visual element toggle"""
        print(f"[Institutional Panel] Visual {name} {'enabled' if enabled else 'disabled'}")
        # This will be connected to chart panel to show/hide elements

    def update_market_status(self, status: str):
        """Update market status display"""
        self.market_status_label.setText(status)

    def update_context(self, session: str, timeframe: str, trend: str, structure: str):
        """Update market context"""
        self.session_label.setText(f"Session: {session}")
        self.tf_label.setText(f"Timeframe: {timeframe}")
        self.trend_label.setText(f"Trend: {trend}")
        self.trend_label.setStyleSheet(f"color: {'#00ff00' if 'BULL' in trend.upper() else '#ff0000'}; font-weight: bold;")
        self.structure_label.setText(f"Structure: {structure}")

    def update_risk_metrics(self, account_risk: float, drawdown: float, win_rate: float):
        """Update risk metrics"""
        self.risk_label.setText(
            f"Account Risk: {account_risk:.1f}%\n"
            f"Drawdown: {drawdown:.1f}%\n"
            f"Win Rate: {win_rate:.0f}%"
        )

    def update_performance(self, today: float, week: float, month: float):
        """Update performance stats"""
        self.performance_label.setText(
            f"Today: {today:+.1f}%\n"
            f"Week: {week:+.1f}%\n"
            f"Month: {month:+.1f}%"
        )

        # Color based on performance
        color = "#00ff00" if today >= 0 else "#ff0000"
        self.performance_label.setStyleSheet(f"color: {color}; padding: 5px; font-weight: bold;")
