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
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.multi_symbol_manager import get_all_symbols


class MTFStructureWidget(QWidget, AIAssistMixin):
    """
    Multi-Timeframe Structure Map Display Widget (AI-Enhanced)

    Shows:
    - Trend per timeframe (W1/D1/H4/H1/M15)
    - Key support/resistance levels
    - Confluence zones highlighted
    - Distance to nearest structure
    - AI-powered structure analysis
    """

    structure_updated = pyqtSignal(dict)  # Emits structure data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = "EURUSD"
        self.structure_data = None

        # Setup AI assistance
        self.setup_ai_assist("mtf_structure")

        self.init_ui()

        # Connect to demo mode changes
        demo_mode_manager.mode_changed.connect(self.on_mode_changed)

        # Auto-refresh every 5 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(5000)

        # Initial update
        self.update_data()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager

        print(f"\n[MTF Structure] update_from_live_data() called for {self.current_symbol}")

        try:
            # Get candle data
            candles = data_manager.get_candles()

            if not candles or len(candles) < 50:
                print(f"[MTF Structure] ⚠️ Not enough data ({len(candles) if candles else 0} candles, need 50+)")
                self.status_label.setText(f"Live: {self.current_symbol} (waiting for data...)")
                return

            print(f"[MTF Structure] ✓ Got {len(candles)} candles for {self.current_symbol}")

            # Get current price
            current_price = candles[-1]['close']
            print(f"[MTF Structure]   → Current price: {current_price:.5f}")

            # Build data by timeframe dictionary
            # Note: data_manager tracks one timeframe, so we'll use what we have
            # and extrapolate trend across timeframes from longer period analysis
            import pandas as pd
            df = pd.DataFrame(candles)

            # Use the available data as the base timeframe
            current_timeframe = data_manager.candle_buffer.timeframe or 'M15'

            # Analyze trends at different lookback periods to simulate MTF analysis
            trends = {}

            # M15: Last 15 candles (15-60 min)
            if len(candles) >= 15:
                recent = candles[-15:]
                m15_trend = self._analyze_trend(recent)
                trends['M15'] = m15_trend

            # H1: Last 60 candles (4 hours if M15)
            if len(candles) >= 60:
                h1_candles = candles[-60:]
                h1_trend = self._analyze_trend(h1_candles)
                trends['H1'] = h1_trend

            # H4: Last 100 candles
            if len(candles) >= 100:
                h4_candles = candles[-100:]
                h4_trend = self._analyze_trend(h4_candles)
                trends['H4'] = h4_trend

            # D1: All available candles
            d1_trend = self._analyze_trend(candles)
            trends['D1'] = d1_trend
            trends['W1'] = d1_trend  # Use same as D1 for simplicity

            # Find nearest support/resistance from recent swing highs/lows
            highs = [c['high'] for c in candles[-50:]]
            lows = [c['low'] for c in candles[-50:]]

            # Find nearest resistance (high above current price)
            resistances = [h for h in highs if h > current_price]
            nearest_resistance = None
            if resistances:
                nearest_res_price = min(resistances)
                nearest_resistance = {
                    'price': nearest_res_price,
                    'timeframe': current_timeframe
                }

            # Find nearest support (low below current price)
            supports = [l for l in lows if l < current_price]
            nearest_support = None
            if supports:
                nearest_sup_price = max(supports)
                nearest_support = {
                    'price': nearest_sup_price,
                    'timeframe': current_timeframe
                }

            # Build structure data
            structure_data = {
                'trend_analysis': trends,
                'nearest_support': nearest_support,
                'nearest_resistance': nearest_resistance,
                'current_price': current_price,
                'confluence_zones': [],  # Would require multi-timeframe data
                'last_update': datetime.now()
            }

            # Log trend analysis results
            print(f"[MTF Structure]   → Trends: M15={trends.get('M15', 'N/A')}, H1={trends.get('H1', 'N/A')}, H4={trends.get('H4', 'N/A')}, D1={trends.get('D1', 'N/A')}")
            if nearest_resistance:
                print(f"[MTF Structure]   → Nearest Resistance: {nearest_resistance['price']:.5f}")
            if nearest_support:
                print(f"[MTF Structure]   → Nearest Support: {nearest_support['price']:.5f}")

            self.update_structure_data(structure_data)
            self.status_label.setText(f"Live: {self.current_symbol}")

            print(f"[MTF Structure] ✓ Structure analysis completed successfully")

        except Exception as e:
            print(f"[MTF Structure] Error fetching live data: {e}")
            self.status_label.setText(f"Live: Error - {str(e)[:30]}")

    def _analyze_trend(self, candles) -> str:
        """Analyze trend from candle data"""
        if not candles or len(candles) < 10:
            return 'UNKNOWN'

        # Simple SMA trend analysis
        closes = [c['close'] for c in candles]
        current_price = closes[-1]

        # Calculate moving average
        ma_period = min(20, len(closes) // 2)
        if ma_period < 3:
            return 'UNKNOWN'

        sma = sum(closes[-ma_period:]) / ma_period

        # Determine trend
        if current_price > sma * 1.002:  # 0.2% above
            return 'BULLISH'
        elif current_price < sma * 0.998:  # 0.2% below
            return 'BEARISH'
        else:
            return 'NEUTRAL'

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

        # AI Assist checkbox
        self.create_ai_checkbox(header_layout)

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

        # === AI SUGGESTION FRAME ===
        self.create_ai_suggestion_frame(layout)

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

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # Get demo MTF structure data
            demo_data = get_demo_data('mtf_structure', symbol=self.current_symbol)
            if demo_data:
                # Transform demo data to expected format
                current_price = 1.0850
                structure_data = {
                    'trend_analysis': {
                        'M15': demo_data.get('m15_trend', 'UNKNOWN'),
                        'H1': demo_data.get('h1_trend', 'UNKNOWN'),
                        'H4': demo_data.get('h4_trend', 'UNKNOWN'),
                        'D1': demo_data.get('d1_trend', 'NEUTRAL'),
                        'H4 ': demo_data.get('h4_trend', 'UNKNOWN')  # Duplicate for 5-item display
                    },
                    'nearest_support': {
                        'price': demo_data.get('key_support', 1.0750),
                        'timeframe': 'H4'
                    },
                    'nearest_resistance': {
                        'price': demo_data.get('key_resistance', 1.0950),
                        'timeframe': 'H1'
                    },
                    'current_price': current_price,
                    'confluence_zones': []  # No confluence zones in demo
                }
                self.update_structure_data(structure_data)
                self.status_label.setText(f"Demo Mode - {self.current_symbol}")
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.structure_data:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"MTF Structure widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Custom AI analysis for MTF structure

        Args:
            prediction: ML prediction data from ml_integration
            widget_data: Current structure data

        Returns:
            Formatted suggestion dictionary
        """
        from core.ml_integration import create_ai_suggestion

        if not self.structure_data:
            return create_ai_suggestion(
                widget_type="mtf_structure",
                text="No structure data available",
                confidence=0.0
            )

        # Analyze trend alignment across timeframes
        trends = self.structure_data.get('trends', {})
        bullish_count = sum(1 for t in trends.values() if 'BULLISH' in str(t).upper())
        bearish_count = sum(1 for t in trends.values() if 'BEARISH' in str(t).upper())
        total_tfs = len(trends)

        # Calculate alignment score
        alignment_score = max(bullish_count, bearish_count) / total_tfs if total_tfs > 0 else 0

        if alignment_score >= 0.8:
            confidence = 0.90
            alignment = "VERY STRONG"
            action_emoji = "🔥"
            action = f"{max(bullish_count, bearish_count)}/{total_tfs} timeframes aligned"
            color = "green"
        elif alignment_score >= 0.6:
            confidence = 0.75
            alignment = "STRONG"
            action_emoji = "✓"
            action = f"{max(bullish_count, bearish_count)}/{total_tfs} timeframes aligned"
            color = "green"
        elif alignment_score >= 0.4:
            confidence = 0.55
            alignment = "MODERATE"
            action_emoji = "⚠️"
            action = "Mixed timeframe structure"
            color = "yellow"
        else:
            confidence = 0.35
            alignment = "WEAK"
            action_emoji = "❌"
            action = "Conflicting timeframe signals"
            color = "red"

        # Determine direction
        if bullish_count > bearish_count:
            direction = "BULLISH"
        elif bearish_count > bullish_count:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Build suggestion text
        suggestion_text = f"{action}\n\n"
        suggestion_text += f"📊 Trend Alignment: {alignment} ({alignment_score:.0%})\n"
        suggestion_text += f"📈 Direction: {direction}\n"
        suggestion_text += f"⏰ Bullish TFs: {bullish_count}/{total_tfs}\n"
        suggestion_text += f"⏰ Bearish TFs: {bearish_count}/{total_tfs}\n\n"

        # Add recommendation
        if alignment_score >= 0.8:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += f"✓ Excellent MTF alignment for {direction.lower()} trades\n"
            suggestion_text += "✓ High probability directional moves\n"
            suggestion_text += "✓ Trade with trend on all timeframes"
        elif alignment_score >= 0.6:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += f"✓ Good MTF alignment for {direction.lower()} bias\n"
            suggestion_text += "⚠️ Watch for pullbacks on conflicting timeframes"
        else:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += "❌ Poor MTF alignment - avoid directional trades\n"
            suggestion_text += "⚠️ Wait for timeframes to align or trade range"

        return create_ai_suggestion(
            widget_type="mtf_structure",
            text=suggestion_text,
            confidence=confidence,
            emoji=action_emoji,
            color=color
        )

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
