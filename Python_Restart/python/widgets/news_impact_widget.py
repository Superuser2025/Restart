"""
AppleTrader Pro - News Event Impact Widget
PyQt6 widget for displaying economic calendar with impact predictions
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QListWidget, QListWidgetItem,
                            QPushButton, QTextEdit, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List
from datetime import datetime

from widgets.news_impact_predictor import (news_impact_predictor, NewsEvent,
                                          ImpactLevel)
from widgets.calendar_fetcher import calendar_fetcher


class NewsEventListItem(QWidget):
    """Custom widget for a single news event"""

    def __init__(self, event: NewsEvent, parent=None):
        super().__init__(parent)
        self.event = event
        self.init_ui()

    def init_ui(self):
        """Initialize the list item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header line
        header_layout = QHBoxLayout()

        # Impact indicator
        impact_emoji = {
            ImpactLevel.EXTREME: '🔴',
            ImpactLevel.HIGH: '🟠',
            ImpactLevel.MEDIUM: '🟡',
            ImpactLevel.LOW: '🟢'
        }[self.event.impact_level]

        impact_color = {
            ImpactLevel.EXTREME: '#ff0000',
            ImpactLevel.HIGH: '#ff6600',
            ImpactLevel.MEDIUM: '#ffaa00',
            ImpactLevel.LOW: '#00ff00'
        }[self.event.impact_level]

        impact_label = QLabel(impact_emoji)
        impact_label.setFont(QFont("Arial", 12))
        impact_label.setFixedWidth(25)
        header_layout.addWidget(impact_label)

        # Time
        time_str = self.event.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        time_label.setFixedWidth(60)
        header_layout.addWidget(time_label)

        # Currency
        currency_label = QLabel(self.event.currency)
        currency_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        currency_label.setFixedWidth(40)
        currency_label.setStyleSheet("color: #00aaff;")
        header_layout.addWidget(currency_label)

        # Event name
        event_label = QLabel(self.event.event_name)
        event_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(event_label, 1)

        layout.addLayout(header_layout)

        # Details line
        details_layout = QHBoxLayout()
        details_layout.setContentsMargins(30, 0, 0, 0)  # Indent

        if self.event.forecast is not None:
            forecast_text = f"Expected: {self.event.forecast}"
            forecast_label = QLabel(forecast_text)
            forecast_label.setFont(QFont("Courier", 8))
            details_layout.addWidget(forecast_label)

        if self.event.previous is not None:
            prev_text = f"| Previous: {self.event.previous}"
            prev_label = QLabel(prev_text)
            prev_label.setFont(QFont("Courier", 8))
            details_layout.addWidget(prev_label)

        details_layout.addStretch()

        # Impact info
        impact_text = f"{self.event.avg_pip_impact:.0f} pips"
        impact_info_label = QLabel(impact_text)
        impact_info_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
        impact_info_label.setStyleSheet(f"color: {impact_color};")
        details_layout.addWidget(impact_info_label)

        layout.addLayout(details_layout)


class NewsImpactWidget(QWidget):
    """
    News Event Impact Display Widget

    Shows:
    - Upcoming economic events (next 24h)
    - Historical average pip impact
    - Impact level classification
    - Trading recommendations
    - Auto-flatten alerts
    """

    news_alert = pyqtSignal(dict)  # Emits high-impact alerts

    def __init__(self, parent=None):
        super().__init__(parent)

        # CRITICAL: Initialize current_symbol BEFORE calling refresh_display
        self.current_symbol = "EURUSD"

        self.init_ui()

        # Auto-refresh every 60 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(60000)

        # Alert check every 10 seconds
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(10000)

        # Live data update timer
        self.live_data_timer = QTimer()
        self.live_data_timer.timeout.connect(self.update_from_live_data)
        self.live_data_timer.start(3000)

        # Initial update with live data
        self.update_from_live_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("📰 News Event Impact Predictor")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.reload_calendar_data)
        self.refresh_btn.setMaximumWidth(100)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # === IMMINENT ALERTS ===
        alerts_group = QGroupBox("⚠️ Imminent High-Impact Events")
        alerts_layout = QVBoxLayout()

        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(100)
        self.alerts_text.setFont(QFont("Courier", 9))
        alerts_layout.addWidget(self.alerts_text)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # === UPCOMING EVENTS ===
        events_group = QGroupBox("📅 Upcoming Events (Next 24h)")
        events_layout = QVBoxLayout()

        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(250)
        self.events_list.setFont(QFont("Courier", 9))
        self.events_list.itemClicked.connect(self.on_event_clicked)
        events_layout.addWidget(self.events_list)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Impact:"))

        legend_items = [
            ("🔴 EXTREME", "#ff0000"),
            ("🟠 HIGH", "#ff6600"),
            ("🟡 MEDIUM", "#ffaa00"),
            ("🟢 LOW", "#00ff00")
        ]

        for text, color in legend_items:
            legend_label = QLabel(f"  {text}  ")
            legend_label.setStyleSheet(f"color: {color}; font-size: 8pt;")
            legend_layout.addWidget(legend_label)

        legend_layout.addStretch()
        events_layout.addLayout(legend_layout)

        events_group.setLayout(events_layout)
        layout.addWidget(events_group)

        # === EVENT DETAILS ===
        details_group = QGroupBox("📋 Event Details & Recommendation")
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setFont(QFont("Courier", 9))
        details_layout.addWidget(self.details_text)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # === STATUS ===
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 8))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply modern dark theme"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #00aaff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #333;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0d7377;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d7377;
                border: none;
                border-radius: 3px;
                padding: 5px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14b1b8;
            }
            QPushButton:pressed {
                background-color: #0a5a5d;
            }
        """)

    def set_symbol(self, symbol: str):
        """Update the current symbol and refresh display"""
        self.current_symbol = symbol
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Live: {symbol}")
        self.update_from_live_data()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager
        symbol = self.current_symbol
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Live: {symbol}")

    def load_sample_data(self):
        """Load real news events from calendar sources"""
        from datetime import timedelta

        # Fetch real calendar events
        try:
            real_events = calendar_fetcher.fetch_events(days_ahead=7)

            if real_events:
                # Clear old events
                news_impact_predictor.events = []

                # Add each event to the predictor (this enriches them with historical data)
                for event in real_events:
                    news_impact_predictor.add_event(event)

                self.status_label.setText(f"Loaded {len(real_events)} real events from calendar")
            else:
                # Fallback to sample data if no real events available
                self._load_fallback_sample_data()
                self.status_label.setText("Using sample data (no calendar source available)")

        except Exception as e:
            # If fetching fails, use fallback sample data
            self._load_fallback_sample_data()
            self.status_label.setText(f"Using sample data (fetch failed: {str(e)[:30]})")

        # Refresh display
        self.refresh_display()

    def _load_fallback_sample_data(self):
        """Load fallback sample news events if real data unavailable"""
        from datetime import timedelta

        # Create sample news events using correct constructor
        sample_events = []

        # Event 0: IMMINENT - US Retail Sales (in 10 minutes)
        event0 = NewsEvent(
            event_name='US Retail Sales',
            currency='USD',
            timestamp=datetime.now() + timedelta(minutes=10),
            forecast=0.5,
            previous=0.3
        )
        event0.avg_pip_impact = 85
        event0.impact_level = ImpactLevel.HIGH
        sample_events.append(event0)

        # Event 1: US Non-Farm Payrolls
        event1 = NewsEvent(
            event_name='US Non-Farm Payrolls',
            currency='USD',
            timestamp=datetime.now() + timedelta(hours=2),
            forecast=185.0,
            previous=180.0
        )
        event1.avg_pip_impact = 120
        event1.impact_level = ImpactLevel.EXTREME
        sample_events.append(event1)

        # Event 2: ECB Interest Rate Decision
        event2 = NewsEvent(
            event_name='ECB Interest Rate Decision',
            currency='EUR',
            timestamp=datetime.now() + timedelta(hours=6),
            forecast=4.50,
            previous=4.50
        )
        event2.avg_pip_impact = 95
        event2.impact_level = ImpactLevel.EXTREME
        sample_events.append(event2)

        # Event 3: UK GDP Growth Rate
        event3 = NewsEvent(
            event_name='UK GDP Growth Rate',
            currency='GBP',
            timestamp=datetime.now() + timedelta(hours=8),
            forecast=0.3,
            previous=0.2
        )
        event3.avg_pip_impact = 55
        event3.impact_level = ImpactLevel.HIGH
        sample_events.append(event3)

        # Event 4: US Consumer Confidence
        event4 = NewsEvent(
            event_name='US Consumer Confidence',
            currency='USD',
            timestamp=datetime.now() + timedelta(hours=12),
            forecast=102.5,
            previous=101.3
        )
        event4.avg_pip_impact = 35
        event4.impact_level = ImpactLevel.MEDIUM
        sample_events.append(event4)

        # Event 5: JPY Manufacturing PMI
        event5 = NewsEvent(
            event_name='JPY Manufacturing PMI',
            currency='JPY',
            timestamp=datetime.now() + timedelta(hours=18),
            forecast=49.8,
            previous=49.5
        )
        event5.avg_pip_impact = 18
        event5.impact_level = ImpactLevel.LOW
        sample_events.append(event5)

        # Add sample events to the predictor
        news_impact_predictor.events = sample_events

    def reload_calendar_data(self):
        """Reload calendar data from source"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Loading...")
        self.load_sample_data()
        self.refresh_btn.setText("🔄 Refresh")
        self.refresh_btn.setEnabled(True)

    def refresh_display(self):
        """Refresh the display with current data"""
        # Get upcoming events
        upcoming = news_impact_predictor.get_upcoming_events(hours=24)

        # Update events list
        self.events_list.clear()

        for event in upcoming:
            # Create custom widget
            item_widget = NewsEventListItem(event)

            # Create list item
            list_item = QListWidgetItem(self.events_list)
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, event)

            # Add widget
            self.events_list.addItem(list_item)
            self.events_list.setItemWidget(list_item, item_widget)

        # Update status
        self.status_label.setText(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')} | "
            f"{len(upcoming)} events in next 24h"
        )

    def check_alerts(self):
        """Check for and display high-impact alerts"""
        alerts = news_impact_predictor.get_high_impact_alerts()

        if alerts:
            alert_lines = []
            for alert in alerts:
                alert_lines.append(alert['message'])
                alert_lines.append(alert['recommendation'])
                alert_lines.append(f"Expected Move: {alert['avg_move']}")
                alert_lines.append(f"Direction: {alert['direction_prob']}")
                alert_lines.append("")

                # Emit signal for critical alerts
                if alert['severity'] == 'CRITICAL':
                    self.news_alert.emit(alert)

            self.alerts_text.setPlainText('\n'.join(alert_lines))
        else:
            self.alerts_text.setPlainText("✓ No imminent high-impact events")

    def on_event_clicked(self, item):
        """Handle event click to show details"""
        event = item.data(Qt.ItemDataRole.UserRole)

        if event:
            analysis = news_impact_predictor.analyze_event(event)
            self.details_text.setPlainText(analysis['trading_recommendation'])

    def add_sample_events(self):
        """Add sample events for testing"""
        from datetime import timedelta

        # Sample events
        now = datetime.now()

        # Upcoming NFP
        nfp = NewsEvent(
            event_name="Non-Farm Payrolls",
            currency="USD",
            timestamp=now + timedelta(hours=2),
            forecast=150000,
            previous=130000
        )
        news_impact_predictor.add_event(nfp)

        # CPI tomorrow
        cpi = NewsEvent(
            event_name="CPI",
            currency="USD",
            timestamp=now + timedelta(hours=20),
            forecast=3.2,
            previous=3.0
        )
        news_impact_predictor.add_event(cpi)

        # ECB Rate Decision
        ecb = NewsEvent(
            event_name="ECB Rate Decision",
            currency="EUR",
            timestamp=now + timedelta(hours=8),
            forecast=4.5,
            previous=4.25
        )
        news_impact_predictor.add_event(ecb)

        self.refresh_display()

    def clear_display(self):
        """Clear all displays"""
        self.events_list.clear()
        self.alerts_text.setPlainText("No data")
        self.details_text.setPlainText("Select an event to see details")
        self.status_label.setText("Status: Waiting for data")

    def should_flatten_positions(self, symbol: str) -> tuple:
        """Check if positions should be flattened"""
        return news_impact_predictor.should_flatten_positions(symbol)
