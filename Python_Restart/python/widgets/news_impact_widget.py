"""
AppleTrader Pro - News Event Impact Widget
PyQt6 widget for displaying economic calendar with impact predictions
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QListWidget, QListWidgetItem,
                            QPushButton, QTextEdit, QFrame, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List
from datetime import datetime

from widgets.news_impact_predictor import (news_impact_predictor, NewsEvent,
                                          ImpactLevel)
from widgets.calendar_fetcher import calendar_fetcher
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data


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


class NewsImpactWidget(AIAssistMixin, QWidget):
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
        self.current_events = []  # Store current news events for AI analysis

        self.init_ui()
        self.setup_ai_assist("news_impact")

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
        self.live_data_timer.timeout.connect(self.update_data)
        self.live_data_timer.start(3000)

        # Initial update
        self.update_data()

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

        # AI Assist checkbox (created by mixin, we'll add it here)
        self.ai_checkbox_placeholder = header_layout

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.reload_calendar_data)
        self.refresh_btn.setMaximumWidth(100)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # === CALENDAR IMPORT ===
        import_group = QGroupBox("📥 Import Calendar Data (Paste monthly calendar from Investing.com)")
        import_group.setCheckable(True)
        import_group.setChecked(False)  # Collapsed by default
        import_layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Copy the monthly calendar from Investing.com and paste it here.\n"
            "Format: Tab-delimited with Date, Time, Country, Event Name, Previous, Forecast"
        )
        instructions.setFont(QFont("Arial", 9))
        instructions.setStyleSheet("color: #aaaaaa; padding: 5px;")
        instructions.setWordWrap(True)
        import_layout.addWidget(instructions)

        # Text area for pasting
        self.calendar_paste_area = QTextEdit()
        self.calendar_paste_area.setPlaceholderText(
            "Paste monthly calendar here...\n\n"
            "Example format:\n"
            "Friday January 02 2026    Actual    Previous\n"
            "02:30 PM    US    Non Farm Payrolls DEC    64K    70K\n"
            "03:45 PM    US    S&P Global Manufacturing PMI    52.2    51.8"
        )
        self.calendar_paste_area.setMaximumHeight(180)
        self.calendar_paste_area.setFont(QFont("Courier New", 9))
        self.calendar_paste_area.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #00ff00;
                border-radius: 3px;
                color: #ffffff;
                padding: 8px;
            }
        """)
        import_layout.addWidget(self.calendar_paste_area)

        # Import button
        import_btn = QPushButton("📥 Parse & Import Calendar")
        import_btn.clicked.connect(self.on_import_calendar)
        import_btn.setMaximumWidth(250)
        import_btn.setFixedHeight(35)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #00cc00;
            }
            QPushButton:pressed {
                background-color: #008800;
            }
        """)
        import_layout.addWidget(import_btn)

        # Import status
        self.import_status_label = QLabel("")
        self.import_status_label.setFont(QFont("Arial", 9))
        self.import_status_label.setWordWrap(True)
        import_layout.addWidget(self.import_status_label)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

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

        # === AI SUGGESTION FRAME (placeholder, created by mixin) ===
        self.ai_suggestion_placeholder = layout

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
        # Load real calendar events
        self.load_sample_data()

        # Update status with current symbol
        from core.data_manager import data_manager
        symbol = self.current_symbol
        if hasattr(self, 'status_label'):
            current_status = self.status_label.text()
            if "Loaded" not in current_status:
                self.status_label.setText(f"Live: {symbol}")

    def load_sample_data(self):
        """Load real news events from calendar sources"""
        from datetime import timedelta

        # Fetch real calendar events
        try:
            print("📰 Fetching calendar events...")
            real_events = calendar_fetcher.fetch_events(days_ahead=7)
            print(f"📰 Calendar fetcher returned {len(real_events) if real_events else 0} events")

            if real_events:
                # Clear old events
                news_impact_predictor.events = []

                # Add each event to the predictor (this enriches them with historical data)
                for event in real_events:
                    news_impact_predictor.add_event(event)

                print(f"✓ Loaded {len(real_events)} real events from calendar")
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"Loaded {len(real_events)} real events from calendar")
            else:
                # NO FALLBACK TO FAKE DATA - Show nothing if no real events
                print("⚠️ No real calendar events available")
                news_impact_predictor.events = []  # Clear any old events
                if hasattr(self, 'status_label'):
                    self.status_label.setText("⚠️ No real calendar data - Add events to economic_calendar.json")

        except Exception as e:
            # If fetching fails, DO NOT show fake data
            print(f"❌ Calendar fetch failed: {e}")
            import traceback
            traceback.print_exc()
            news_impact_predictor.events = []  # Clear events
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"❌ Calendar unavailable - {str(e)[:50]}")

        # Refresh display (will show empty list if no events)
        self.refresh_display()

    def _load_fallback_sample_data(self):
        """
        Load intelligent sample news events based on real economic calendar patterns

        This generates realistic events based on:
        - Current day of week (NFP on 1st Friday, etc.)
        - Typical event times (US events at 8:30 AM ET, etc.)
        - Real event importance and impact levels
        """
        from datetime import timedelta
        import calendar as cal

        sample_events = []
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 4=Friday

        # Helper function to create event at specific time
        def create_event(name, currency, hours_ahead, forecast, previous, impact_level, avg_pips):
            event = NewsEvent(
                event_name=name,
                currency=currency,
                timestamp=now + timedelta(hours=hours_ahead),
                forecast=forecast,
                previous=previous
            )
            event.impact_level = impact_level
            event.avg_pip_impact = avg_pips
            return event

        # CRITICAL EVENTS (Based on real economic calendar patterns)

        # 1. US Non-Farm Payrolls (First Friday of month, 8:30 AM ET)
        # One of the most market-moving events
        sample_events.append(create_event(
            'US Non-Farm Payrolls',
            'USD',
            hours_ahead=2,  # 2 hours from now
            forecast=185.0,
            previous=180.0,
            impact_level=ImpactLevel.EXTREME,
            avg_pips=150
        ))

        # 2. FOMC Interest Rate Decision (Every 6 weeks, 2:00 PM ET)
        # Extreme volatility event
        sample_events.append(create_event(
            'FOMC Interest Rate Decision',
            'USD',
            hours_ahead=6,
            forecast=5.25,
            previous=5.00,
            impact_level=ImpactLevel.EXTREME,
            avg_pips=175
        ))

        # 3. ECB Interest Rate Decision (Every 6 weeks, varies)
        # Major EUR event
        sample_events.append(create_event(
            'ECB Interest Rate Decision',
            'EUR',
            hours_ahead=10,
            forecast=4.50,
            previous=4.25,
            impact_level=ImpactLevel.EXTREME,
            avg_pips=140
        ))

        # 4. US CPI (Consumer Price Index) - Mid-month
        # High impact inflation data
        sample_events.append(create_event(
            'US CPI m/m',
            'USD',
            hours_ahead=14,
            forecast=0.3,
            previous=0.2,
            impact_level=ImpactLevel.EXTREME,
            avg_pips=130
        ))

        # 5. UK GDP Growth Rate
        sample_events.append(create_event(
            'UK GDP Growth Rate q/q',
            'GBP',
            hours_ahead=18,
            forecast=0.3,
            previous=0.2,
            impact_level=ImpactLevel.HIGH,
            avg_pips=95
        ))

        # 6. US Retail Sales
        sample_events.append(create_event(
            'US Retail Sales m/m',
            'USD',
            hours_ahead=22,
            forecast=0.5,
            previous=0.3,
            impact_level=ImpactLevel.HIGH,
            avg_pips=85
        ))

        # 7. AUD Employment Change
        sample_events.append(create_event(
            'AUD Employment Change',
            'AUD',
            hours_ahead=26,
            forecast=25.0,
            previous=20.5,
            impact_level=ImpactLevel.HIGH,
            avg_pips=75
        ))

        # 8. German Manufacturing PMI
        sample_events.append(create_event(
            'German Manufacturing PMI',
            'EUR',
            hours_ahead=32,
            forecast=48.5,
            previous=48.2,
            impact_level=ImpactLevel.MEDIUM,
            avg_pips=55
        ))

        # 9. US Consumer Confidence
        sample_events.append(create_event(
            'US Consumer Confidence',
            'USD',
            hours_ahead=38,
            forecast=102.5,
            previous=101.3,
            impact_level=ImpactLevel.MEDIUM,
            avg_pips=45
        ))

        # 10. CAD Trade Balance
        sample_events.append(create_event(
            'CAD Trade Balance',
            'CAD',
            hours_ahead=44,
            forecast=-1.5,
            previous=-1.8,
            impact_level=ImpactLevel.MEDIUM,
            avg_pips=40
        ))

        # 11. JPY Manufacturing PMI
        sample_events.append(create_event(
            'JPY Manufacturing PMI',
            'JPY',
            hours_ahead=50,
            forecast=49.8,
            previous=49.5,
            impact_level=ImpactLevel.LOW,
            avg_pips=25
        ))

        # 12. NZD Business Confidence
        sample_events.append(create_event(
            'NZD Business Confidence',
            'NZD',
            hours_ahead=56,
            forecast=15.0,
            previous=14.2,
            impact_level=ImpactLevel.LOW,
            avg_pips=18
        ))

        # Add all events to the predictor
        news_impact_predictor.events = sample_events

        print(f"📊 Generated {len(sample_events)} intelligent sample events")
        print("   Based on real economic calendar patterns:")
        print("   - 4 EXTREME impact events (120-175 pips)")
        print("   - 3 HIGH impact events (75-95 pips)")
        print("   - 3 MEDIUM impact events (40-55 pips)")
        print("   - 2 LOW impact events (18-25 pips)")

    def on_import_calendar(self):
        """Handle calendar import from pasted data"""
        import os
        from utils.calendar_parser import CalendarParser

        # Get pasted text
        calendar_text = self.calendar_paste_area.toPlainText().strip()

        if not calendar_text:
            self.import_status_label.setText("❌ Please paste calendar data first!")
            self.import_status_label.setStyleSheet("color: #ff0000;")
            return

        try:
            self.import_status_label.setText("⏳ Parsing calendar data...")
            self.import_status_label.setStyleSheet("color: #ffaa00;")

            # Parse the calendar
            parser = CalendarParser()
            events = parser.parse(calendar_text)

            if not events:
                self.import_status_label.setText("❌ No events found. Check the format and try again.")
                self.import_status_label.setStyleSheet("color: #ff0000;")
                return

            # Save to file
            calendar_file = os.path.join(
                os.path.dirname(__file__),
                '../data/economic_calendar.json'
            )

            parser.save_to_file(calendar_file)

            # Success message
            self.import_status_label.setText(
                f"✅ SUCCESS! Imported {len(events)} events - Refreshing display..."
            )
            self.import_status_label.setStyleSheet("color: #00ff00;")

            # Clear the paste area
            self.calendar_paste_area.clear()

            # Immediately reload and refresh the display
            self.reload_calendar_data()

            # Update success message after reload
            self.import_status_label.setText(
                f"✅ {len(events)} events imported and loaded successfully!"
            )

        except Exception as e:
            self.import_status_label.setText(f"❌ Error: {str(e)}")
            self.import_status_label.setStyleSheet("color: #ff0000;")
            print(f"Calendar import error: {e}")
            import traceback
            traceback.print_exc()

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

        # Store for AI analysis
        self.current_events = upcoming

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

        # Update AI if enabled
        if self.ai_enabled and self.current_events:
            self.update_ai_suggestions()

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

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # In demo mode, load sample events with CLEAR warning
            self._load_fallback_sample_data()
            self.refresh_display()
            if hasattr(self, 'status_label'):
                self.status_label.setText("🎭 DEMO MODE - FAKE EVENTS (NOT REAL!)")
        else:
            # Get live data - NO FAKE DATA in live mode
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_events:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"News Impact widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for news event impact

        Analyzes:
        - Event timing and clustering
        - Impact level and surprise factor
        - Currency-specific volatility
        - Multi-event cumulative risk
        - Optimal trading windows
        """
        from core.ml_integration import create_ai_suggestion
        from datetime import timedelta

        if not self.current_events:
            return create_ai_suggestion(
                widget_type="news_impact",
                text="No upcoming news events to analyze",
                confidence=0.0
            )

        now = datetime.now()

        # Get events in next 24 hours
        upcoming_events = [e for e in self.current_events
                          if now <= e.timestamp <= now + timedelta(hours=24)]

        if not upcoming_events:
            return create_ai_suggestion(
                widget_type="news_impact",
                text="No significant events in next 24 hours - Safe trading window",
                confidence=0.85,
                emoji="✓",
                color="green"
            )

        # Analyze imminent events (within 2 hours)
        imminent = [e for e in upcoming_events
                   if e.timestamp <= now + timedelta(hours=2)]

        # Analyze high-impact events
        high_impact = [e for e in upcoming_events
                      if e.impact_level in [ImpactLevel.EXTREME, ImpactLevel.HIGH]]

        # CRITICAL ANALYSIS: Imminent high-impact events
        if imminent and high_impact:
            critical_events = [e for e in imminent
                             if e.impact_level == ImpactLevel.EXTREME]

            if critical_events:
                event = critical_events[0]
                minutes_away = int((event.timestamp - now).total_seconds() / 60)

                return create_ai_suggestion(
                    widget_type="news_impact",
                    text=f"🚨 CRITICAL: {event.event_name} ({event.currency}) in {minutes_away}min - Expected {event.avg_pip_impact:.0f} pip move. FLATTEN POSITIONS NOW!",
                    confidence=0.95,
                    emoji="🚨",
                    color="red"
                )

        # HIGH RISK: Multiple high-impact events clustering
        if len(high_impact) >= 3:
            currencies = set(e.currency for e in high_impact)
            next_event = min(high_impact, key=lambda e: e.timestamp)
            hours_away = int((next_event.timestamp - now).total_seconds() / 3600)

            return create_ai_suggestion(
                widget_type="news_impact",
                text=f"⚠️ HIGH RISK: {len(high_impact)} major events today affecting {', '.join(currencies)}. Next: {next_event.event_name} in {hours_away}h. Reduce position sizes by 50%.",
                confidence=0.88,
                emoji="⚠️",
                color="orange"
            )

        # MODERATE: Single high-impact event coming
        if high_impact:
            event = high_impact[0]
            hours_away = int((event.timestamp - now).total_seconds() / 3600)

            # Analyze surprise factor (forecast vs previous deviation)
            surprise_factor = "Unknown"
            if event.forecast and event.previous:
                deviation = abs(event.forecast - event.previous) / abs(event.previous) if event.previous != 0 else 0
                if deviation > 0.05:  # >5% deviation
                    surprise_factor = "HIGH surprise potential"
                elif deviation > 0.02:  # >2% deviation
                    surprise_factor = "MODERATE surprise"
                else:
                    surprise_factor = "Low surprise (consensus)"

            action_text = "Avoid new trades" if hours_away < 4 else "Tighten stops"

            return create_ai_suggestion(
                widget_type="news_impact",
                text=f"📊 {event.event_name} ({event.currency}) in {hours_away}h - {event.avg_pip_impact:.0f} pip avg impact. {surprise_factor}. {action_text} 2h before release.",
                confidence=0.80,
                emoji="📊",
                color="yellow"
            )

        # LOW RISK: Only low/medium impact events
        medium_count = len([e for e in upcoming_events
                           if e.impact_level == ImpactLevel.MEDIUM])

        if medium_count > 0:
            return create_ai_suggestion(
                widget_type="news_impact",
                text=f"📈 {medium_count} medium-impact events today - Normal trading conditions. Monitor for surprises.",
                confidence=0.75,
                emoji="📈",
                color="green"
            )

        # SAFE WINDOW
        return create_ai_suggestion(
            widget_type="news_impact",
            text="✓ Safe trading window - Only low-impact events scheduled. Normal position sizing OK.",
            confidence=0.82,
            emoji="✓",
            color="green"
        )
