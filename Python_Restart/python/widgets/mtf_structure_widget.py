"""
AppleTrader Pro - Multi-Timeframe Structure Widget
PyQt6 widget for displaying the MTF Structure Map
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTextEdit, QGroupBox, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Dict, Optional
from datetime import datetime

from widgets.mtf_structure_map import mtf_structure_map


class MTFStructureWidget(QWidget):
    """
    Multi-Timeframe Structure Map Display Widget

    Shows:
    - Trend per timeframe (W1/D1/H4/H1/M15)
    - Key support/resistance levels
    - Confluence zones highlighted
    - Distance to nearest structure
    """

    structure_updated = pyqtSignal(dict)  # Emits structure data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = "EURUSD"
        self.structure_data = None
        self.init_ui()

        # Auto-refresh every 5 seconds with LIVE data
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_from_live_data)
        self.refresh_timer.start(5000)

        # NO SAMPLE DATA - use live data from data_manager
        self.update_from_live_data()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        # Use self.current_symbol, don't overwrite it from data_manager!
        self.status_label.setText(f"Live: {self.current_symbol}")

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("📊 Multi-Timeframe Structure")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_requested)
        self.refresh_btn.setMaximumWidth(100)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # === TREND OVERVIEW ===
        trend_group = QGroupBox("Trend Analysis")
        trend_layout = QVBoxLayout()

        self.trend_labels = {}
        for tf in ['W1', 'D1', 'H4', 'H1', 'M15']:
            label = QLabel(f"{tf}: Loading...")
            label.setFont(QFont("Courier", 10))
            trend_layout.addWidget(label)
            self.trend_labels[tf] = label

        trend_group.setLayout(trend_layout)
        layout.addWidget(trend_group)

        # === NEAREST STRUCTURE ===
        structure_group = QGroupBox("Nearest Structure")
        structure_layout = QVBoxLayout()

        self.nearest_support_label = QLabel("Support: --")
        self.nearest_support_label.setFont(QFont("Courier", 10))
        structure_layout.addWidget(self.nearest_support_label)

        self.nearest_resistance_label = QLabel("Resistance: --")
        self.nearest_resistance_label.setFont(QFont("Courier", 10))
        structure_layout.addWidget(self.nearest_resistance_label)

        structure_group.setLayout(structure_layout)
        layout.addWidget(structure_group)

        # === CONFLUENCE ZONES ===
        confluence_group = QGroupBox("🎯 Confluence Zones")
        confluence_layout = QVBoxLayout()

        self.confluence_text = QTextEdit()
        self.confluence_text.setReadOnly(True)
        self.confluence_text.setMaximumHeight(150)
        self.confluence_text.setFont(QFont("Courier", 9))
        confluence_layout.addWidget(self.confluence_text)

        confluence_group.setLayout(confluence_layout)
        layout.addWidget(confluence_group)

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

    def update_structure_data(self, structure_data: Dict):
        """
        Update the display with new structure data

        Args:
            structure_data: Structure analysis from MTFStructureMap
        """
        self.structure_data = structure_data

        # Update trend labels
        trend_analysis = structure_data.get('trend_analysis', {})
        for tf, label in self.trend_labels.items():
            trend = trend_analysis.get(tf, 'UNKNOWN')

            # Emoji based on trend
            if trend == 'BULLISH':
                emoji = '⬆️'
                color = '#00ff00'
            elif trend == 'BEARISH':
                emoji = '⬇️'
                color = '#ff0000'
            else:
                emoji = '➡️'
                color = '#ffaa00'

            label.setText(f"{tf}: {emoji} {trend}")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Update nearest structure
        nearest_support = structure_data.get('nearest_support')
        nearest_resistance = structure_data.get('nearest_resistance')
        current_price = structure_data.get('current_price', 0)

        if nearest_support:
            distance_pips = (current_price - nearest_support['price']) * 10000
            self.nearest_support_label.setText(
                f"Support: {nearest_support['price']:.5f} "
                f"({nearest_support['timeframe']}) "
                f"↓ {distance_pips:.1f} pips"
            )
            self.nearest_support_label.setStyleSheet("color: #00ff00;")
        else:
            self.nearest_support_label.setText("Support: None found")
            self.nearest_support_label.setStyleSheet("color: #888;")

        if nearest_resistance:
            distance_pips = (nearest_resistance['price'] - current_price) * 10000
            self.nearest_resistance_label.setText(
                f"Resistance: {nearest_resistance['price']:.5f} "
                f"({nearest_resistance['timeframe']}) "
                f"↑ {distance_pips:.1f} pips"
            )
            self.nearest_resistance_label.setStyleSheet("color: #ff0000;")
        else:
            self.nearest_resistance_label.setText("Resistance: None found")
            self.nearest_resistance_label.setStyleSheet("color: #888;")

        # Update confluence zones
        confluence_zones = structure_data.get('confluence_zones', [])
        if confluence_zones:
            confluence_text = []
            for i, zone in enumerate(confluence_zones[:5], 1):
                tf_str = '+'.join(zone['timeframes'])
                zone_type = zone['type'].upper()
                color_code = 'green' if zone_type == 'SUPPORT' else 'red'

                confluence_text.append(
                    f"{i}. {zone['price']:.5f} ({zone_type})\n"
                    f"   [{tf_str}] - {zone['distance_pips']:.1f} pips\n"
                    f"   Strength: {zone['strength']:.0f}/1000\n"
                )

            # Highlight top confluence
            top_zone = confluence_zones[0]
            if top_zone['level_count'] >= 3:
                confluence_text.insert(0,
                    f"⭐ STRONG CONFLUENCE ⭐\n"
                    f"   {top_zone['price']:.5f} "
                    f"({len(top_zone['timeframes'])} timeframes)\n\n"
                )

            self.confluence_text.setPlainText(''.join(confluence_text))
        else:
            self.confluence_text.setPlainText("No confluence zones detected")

        # Update status
        last_update = structure_data.get('last_update')
        if last_update:
            time_str = last_update.strftime("%H:%M:%S")
            self.status_label.setText(f"Updated: {time_str}")

        # Emit signal
        self.structure_updated.emit(structure_data)

    def set_symbol(self, symbol: str):
        """Update current symbol and refresh structure"""
        if symbol != self.current_symbol:
            self.current_symbol = symbol
            self.on_refresh_requested()

    def on_refresh_requested(self):
        """Handle refresh request - external handler should provide new data"""
        self.status_label.setText("Refreshing...")
        # Note: Actual data fetching should be done by parent/controller
        # This just signals that refresh was requested

    def get_chart_overlays(self):
        """Get structure levels for chart overlay"""
        return mtf_structure_map.get_chart_overlays()

    def analyze_and_update(self, data_by_timeframe: Dict, current_price: float):
        """
        Convenience method to analyze and update in one call

        Args:
            data_by_timeframe: {timeframe: DataFrame} with OHLC data
            current_price: Current market price
        """
        # Run analysis
        structure_data = mtf_structure_map.analyze_structure(
            data_by_timeframe, current_price
        )

        # Update display
        self.update_structure_data(structure_data)

    def clear_display(self):
        """Clear all displays"""
        for label in self.trend_labels.values():
            label.setText("--")
            label.setStyleSheet("")

        self.nearest_support_label.setText("Support: --")
        self.nearest_resistance_label.setText("Resistance: --")
        self.confluence_text.setPlainText("No data")
        self.status_label.setText("Status: Waiting for data")

    def load_sample_data(self):
        """Load sample structure data for demonstration"""
        sample_structure = {
            'trends': {
                'W1': 'BULLISH',
                'D1': 'BULLISH',
                'H4': 'BULLISH',
                'H1': 'RANGING',
                'M15': 'BEARISH'
            },
            'current_price': 1.16080,
            'nearest_support': {
                'price': 1.15850,
                'timeframe': 'H4',
                'strength': 850
            },
            'nearest_resistance': {
                'price': 1.16320,
                'timeframe': 'D1',
                'strength': 920
            },
            'confluence_zones': [
                {
                    'price': 1.15850,
                    'type': 'SUPPORT',
                    'timeframes': ['H4', 'D1'],
                    'strength': 850,
                    'distance_pips': 23.0,
                    'level_count': 2
                },
                {
                    'price': 1.16320,
                    'type': 'RESISTANCE',
                    'timeframes': ['D1', 'W1'],
                    'strength': 920,
                    'distance_pips': 24.0,
                    'level_count': 2
                },
                {
                    'price': 1.15500,
                    'type': 'SUPPORT',
                    'timeframes': ['W1', 'D1', 'H4'],
                    'strength': 950,
                    'distance_pips': 58.0,
                    'level_count': 3
                }
            ],
            'last_update': datetime.now()
        }

        self.update_structure_data(sample_structure)
