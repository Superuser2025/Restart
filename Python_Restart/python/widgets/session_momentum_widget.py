"""
AppleTrader Pro - Session Momentum Scanner Widget (AI-Enhanced)
PyQt6 widget for displaying real-time momentum leaderboard with AI assistance
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTextEdit, QGroupBox, QPushButton, QListWidget,
                            QListWidgetItem, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from widgets.session_momentum_scanner import session_momentum_scanner
from core.ai_assist_base import AIAssistMixin
from core.verbose_mode_manager import vprint
from core.demo_mode_manager import is_demo_mode, get_demo_data, demo_mode_manager
from core.verbose_mode_manager import vprint
from core.multi_symbol_manager import get_all_symbols, get_active_symbol
from core.verbose_mode_manager import vprint
from core.ml_integration import create_ai_suggestion
from core.verbose_mode_manager import vprint


class MomentumListItem(QWidget):
    """Custom widget for a single momentum entry"""

    def __init__(self, rank: int, data: Dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.init_ui(rank)

    def init_ui(self, rank: int):
        """Initialize the list item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)

        # Rank
        rank_label = QLabel(f"{rank}.")
        rank_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        rank_label.setFixedWidth(25)
        layout.addWidget(rank_label)

        # Symbol
        symbol = self.data['symbol']
        symbol_label = QLabel(symbol)
        symbol_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        symbol_label.setFixedWidth(80)
        layout.addWidget(symbol_label)

        # Momentum bar
        momentum_score = self.data['momentum_score']
        momentum_bar = QProgressBar()
        momentum_bar.setMaximum(100)
        momentum_bar.setValue(int(momentum_score))
        momentum_bar.setTextVisible(False)
        momentum_bar.setFixedHeight(20)

        # Color based on score
        if momentum_score >= 80:
            color = "#00ff00"  # Bright green
        elif momentum_score >= 60:
            color = "#7fff00"  # Yellow-green
        elif momentum_score >= 40:
            color = "#ffaa00"  # Orange
        else:
            color = "#888888"  # Gray

        momentum_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2b2b2b;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(momentum_bar, 1)

        # Score percentage
        score_label = QLabel(f"{momentum_score:.0f}%")
        score_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        score_label.setFixedWidth(50)
        score_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(score_label)

        # Pips moved
        pips = self.data['session_range_pips']
        pips_label = QLabel(f"{pips:.0f} pips")
        pips_label.setFont(QFont("Courier", 9))
        pips_label.setFixedWidth(70)
        layout.addWidget(pips_label)

        # Direction indicator
        direction = self.data['direction']
        dir_emoji = '🟢' if direction == 'BULLISH' else '🔴'
        dir_label = QLabel(dir_emoji)
        dir_label.setFixedWidth(25)
        layout.addWidget(dir_label)

        # Trending indicator
        trend_strength = self.data['trending_strength']
        if trend_strength > 60:
            trend_indicator = '🔥'
        elif trend_strength > 40:
            trend_indicator = '⚡'
        else:
            trend_indicator = ''

        if trend_indicator:
            trend_label = QLabel(trend_indicator)
            trend_label.setFixedWidth(25)
            layout.addWidget(trend_label)


class SessionMomentumWidget(QWidget, AIAssistMixin):
    """
    Session Momentum Scanner Display Widget (AI-Enhanced)

    Shows real-time momentum leaderboard:
    - Top 10 pairs ranked by momentum
    - Visual bars showing momentum percentage
    - Pips moved and direction
    - AI-powered trade recommendations
    - Demo/Live mode support
    """

    symbol_selected = pyqtSignal(str)  # Emits symbol when clicked
    momentum_alert = pyqtSignal(str)   # Emits alert messages

    def __init__(self, parent=None):
        super().__init__(parent)
        self.leaderboard_data = []

        # CRITICAL: Initialize current_symbol BEFORE calling update_from_live_data
        self.current_symbol = "EURUSD"

        # Setup AI assistance
        self.setup_ai_assist("session_momentum")

        self.init_ui()

        # Connect to demo mode changes
        demo_mode_manager.mode_changed.connect(self.on_mode_changed)

        # Auto-refresh every 3 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(3000)

        # Initial data load
        self.update_data()

    def update_from_live_data(self):
        """Update with live data - MULTI-SYMBOL support via MT5"""
        from core.data_manager import data_manager

        vprint("    → update_from_live_data() called - fetching multi-symbol data")

        try:
            # STRATEGY 1: Fetch multi-symbol data directly from MT5
            multi_symbol_data = self.fetch_multi_symbol_data_from_mt5()

            if multi_symbol_data and len(multi_symbol_data) > 0:
                # SUCCESS: We have real multi-symbol data!
                vprint(f"    ✓ Got REAL data for {len(multi_symbol_data)} symbols from MT5")

                # Run momentum scan
                leaderboard = session_momentum_scanner.scan_momentum(multi_symbol_data)
                vprint(f"    ✓ LIVE MOMENTUM DATA: Top pair = {leaderboard[0]['symbol']} ({leaderboard[0]['momentum_score']:.0f}% momentum)")
                self.update_momentum_data(leaderboard)
                self.status_label.setText(f"Live: {len(multi_symbol_data)} symbols scanned")
                return

            # STRATEGY 2: Try mt5_connector (JSON file approach)
            from core.mt5_connector import mt5_connector
            all_symbols_data = mt5_connector.get_all_symbols_data()

            if all_symbols_data and len(all_symbols_data) > 0:
                vprint(f"    ✓ Got data for {len(all_symbols_data)} symbols from MT5 JSON")
                leaderboard = session_momentum_scanner.scan_momentum(all_symbols_data)
                self.update_momentum_data(leaderboard)
                self.status_label.setText(f"Live: {len(all_symbols_data)} symbols scanned")
                return

            # FALLBACK: Use data_manager for single symbol
            vprint("    ⚠️ MT5 multi-symbol data not available, using single symbol fallback")
            candles = data_manager.get_candles()

            if candles and len(candles) > 20:
                vprint(f"    → Using single symbol fallback with {len(candles)} REAL candles")
                # Create simple momentum data for current symbol
                current = candles[-1]
                prev = candles[-20]

                price_change = current['close'] - prev['close']
                session_range = current['high'] - current['low']

                # Determine pip size (rough estimate)
                if 'JPY' in self.current_symbol:
                    pip_multiplier = 100
                else:
                    pip_multiplier = 10000

                pips_moved = abs(price_change) * pip_multiplier
                direction = 'BULLISH' if price_change > 0 else 'BEARISH'

                # Calculate simple momentum score (0-100)
                momentum_score = min(100, (pips_moved / 50) * 100) if pips_moved > 0 else 30

                leaderboard = [{
                    'symbol': self.current_symbol,
                    'momentum_score': momentum_score,
                    'session_range_pips': pips_moved,
                    'direction': direction,
                    'trending_strength': momentum_score * 0.8,
                    'hourly_volatility': session_range,
                    'volume_ratio': 1.0,
                    'session': 'Active',
                    'recommendation': 'LIVE DATA'
                }]

                self.update_momentum_data(leaderboard)
                self.status_label.setText(f"Live: {self.current_symbol}")
            else:
                self.status_label.setText("Live: Waiting for data...")

        except Exception as e:
            vprint(f"[Session Momentum] Error fetching live data: {e}")
            self.status_label.setText("Live: Error fetching data")

    def fetch_multi_symbol_data_from_mt5(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols directly from MT5"""
        try:
            import MetaTrader5 as mt5
            import pandas as pd

            # Check if MT5 is initialized
            if not mt5.initialize():
                return {}

            symbols_data = {}

            # Get all symbols
            symbols = get_all_symbols()

            vprint(f"    → Fetching data from MT5 for {len(symbols)} symbols...")

            for symbol in symbols:
                try:
                    # Fetch H4 candles for momentum analysis
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 100)

                    if rates is not None and len(rates) > 0:
                        # Convert to DataFrame
                        df = pd.DataFrame(rates)

                        # Add required columns
                        if 'time' in df.columns:
                            df['time'] = pd.to_datetime(df['time'], unit='s')

                        symbols_data[symbol] = df
                        vprint(f"    ✓ {symbol}: Got {len(df)} candles - Last close: {df['close'].iloc[-1]:.5f}")

                except Exception as e:
                    vprint(f"    ✗ {symbol}: Failed ({str(e)[:50]})")
                    continue

            return symbols_data

        except ImportError:
            vprint("    ⚠️ MetaTrader5 module not available")
            return {}
        except Exception as e:
            vprint(f"    ⚠️ MT5 fetch error: {e}")
            return {}

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            print("🟡 [Session Momentum] DEMO MODE - Using fake generated data")
            # Get demo data for all symbols
            symbols = get_all_symbols()
            demo_data = get_demo_data('session_momentum', symbols=symbols)

            if demo_data:
                self.update_momentum_data(demo_data)
                self.status_label.setText(f"Demo Mode - {len(symbols)} symbols")
        else:
            vprint("🔴 [Session Momentum] LIVE MODE - Fetching REAL MT5 data from data_manager")
            # Get live data
            self.update_from_live_data()

        # Update AI suggestions if enabled
        if self.ai_enabled and self.leaderboard_data:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        vprint(f"Session Momentum widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Custom AI analysis for session momentum

        Args:
            prediction: ML prediction data from ml_integration
            widget_data: Current widget data (leaderboard)

        Returns:
            Formatted suggestion dictionary
        """
        from core.ml_integration import create_ai_suggestion

        if not self.leaderboard_data:
            return create_ai_suggestion(
                widget_type="session_momentum",
                text="No momentum data available for analysis",
                confidence=0.0
            )

        # Get top momentum pair
        top_pair = self.leaderboard_data[0]
        symbol = top_pair['symbol']
        momentum = top_pair['momentum_score']
        pips = top_pair['session_range_pips']
        direction = top_pair['direction']

        # Analyze momentum strength
        if momentum >= 85:
            confidence = 0.85
            strength = "VERY STRONG"
            action_emoji = "🔥"
            action = f"Prime opportunity on {symbol}"
            color = "green"
        elif momentum >= 75:
            confidence = 0.75
            strength = "STRONG"
            action_emoji = "⚡"
            action = f"Good momentum on {symbol}"
            color = "green"
        elif momentum >= 65:
            confidence = 0.65
            strength = "MODERATE"
            action_emoji = "✓"
            action = f"Decent setup on {symbol}"
            color = "yellow"
        else:
            confidence = 0.50
            strength = "WEAK"
            action_emoji = "⚠️"
            action = f"Low momentum on {symbol}"
            color = "red"

        # Build suggestion text
        suggestion_text = f"{action}\n\n"
        suggestion_text += f"📊 Momentum: {momentum:.0f}% ({strength})\n"
        suggestion_text += f"📈 Direction: {direction}\n"
        suggestion_text += f"📏 Session Range: {pips:.0f} pips\n\n"

        # Add recommendation
        if momentum >= 75:
            suggestion_text += f"💡 Recommendation: Consider {direction.lower()} entry\n"
            suggestion_text += f"✓ Strong trend + volume + session alignment\n"
            suggestion_text += f"✓ Risk/Reward should be favorable"
        elif momentum >= 65:
            suggestion_text += f"💡 Recommendation: Watch for confirmation\n"
            suggestion_text += f"⚠️ Wait for pullback to key level"
        else:
            suggestion_text += f"💡 Recommendation: Wait for better setup\n"
            suggestion_text += f"⚠️ Momentum insufficient for entry"

        return create_ai_suggestion(
            widget_type="session_momentum",
            text=suggestion_text,
            confidence=confidence,
            emoji=action_emoji,
            color=color
        )

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("⚡ Session Momentum Scanner")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # AI Assist checkbox
        self.create_ai_checkbox(header_layout)

        # Auto-focus toggle
        self.auto_focus_btn = QPushButton("🎯 Auto-Focus")
        self.auto_focus_btn.setCheckable(True)
        self.auto_focus_btn.setMaximumWidth(100)
        self.auto_focus_btn.setToolTip("Auto-switch to highest momentum pair")
        header_layout.addWidget(self.auto_focus_btn)

        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.clicked.connect(self.on_refresh_requested)
        self.refresh_btn.setMaximumWidth(40)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # === BEST OPPORTUNITY HIGHLIGHT ===
        self.best_opportunity_frame = QFrame()
        self.best_opportunity_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.best_opportunity_frame.setStyleSheet("""
            QFrame {
                background-color: #2a4a2a;
                border: 2px solid #00ff00;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        best_layout = QVBoxLayout(self.best_opportunity_frame)
        best_layout.setContentsMargins(5, 5, 5, 5)

        best_title = QLabel("⭐ BEST OPPORTUNITY")
        best_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        best_title.setStyleSheet("color: #00ff00; border: none;")
        best_title.setToolTip("Currency pair with highest momentum score - strongest trend + volume + session alignment")
        best_layout.addWidget(best_title)

        self.best_opportunity_label = QLabel("Scanning...")
        self.best_opportunity_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
        self.best_opportunity_label.setStyleSheet("color: #ffffff; border: none;")
        self.best_opportunity_label.setWordWrap(True)
        best_layout.addWidget(self.best_opportunity_label)

        # Add explanation
        explanation = QLabel("Highest momentum = Strong trend + High volume + Active session")
        explanation.setFont(QFont("Arial", 8))
        explanation.setStyleSheet("color: #88ff88; border: none; font-style: italic;")
        explanation.setWordWrap(True)
        best_layout.addWidget(explanation)

        layout.addWidget(self.best_opportunity_frame)

        # === LEADERBOARD ===
        leaderboard_group = QGroupBox("Momentum Leaderboard")
        leaderboard_layout = QVBoxLayout()

        self.leaderboard_list = QListWidget()
        self.leaderboard_list.setMinimumHeight(300)
        self.leaderboard_list.setFont(QFont("Courier", 9))
        self.leaderboard_list.itemClicked.connect(self.on_symbol_clicked)
        leaderboard_layout.addWidget(self.leaderboard_list)

        leaderboard_group.setLayout(leaderboard_layout)
        layout.addWidget(leaderboard_group)

        # === ALERTS ===
        alerts_group = QGroupBox("🚨 High Momentum Alerts")
        alerts_layout = QVBoxLayout()

        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(100)
        self.alerts_text.setFont(QFont("Courier", 9))
        alerts_layout.addWidget(self.alerts_text)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # === AI SUGGESTION FRAME ===
        self.create_ai_suggestion_frame(layout)

        # === STATUS ===
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 8))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

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
            QPushButton:checked {
                background-color: #00ff00;
                color: #000000;
            }
        """)

    def update_momentum_data(self, leaderboard: List[Dict]):
        """
        Update display with new momentum data

        Args:
            leaderboard: Sorted list of momentum data dicts
        """
        self.leaderboard_data = leaderboard

        # Update best opportunity
        if leaderboard:
            best = leaderboard[0]
            best_text = (
                f"{best['symbol']} - {best['momentum_score']:.0f}% momentum, "
                f"{best['session_range_pips']:.0f} pips, {best['direction']}"
            )
            self.best_opportunity_label.setText(best_text)

            # Auto-focus if enabled
            if self.auto_focus_btn.isChecked():
                self.symbol_selected.emit(best['symbol'])
        else:
            self.best_opportunity_label.setText("No data")

        # Update leaderboard
        self.leaderboard_list.clear()

        for i, data in enumerate(leaderboard[:10], 1):
            # Create custom widget for this item
            item_widget = MomentumListItem(i, data)

            # Create list item
            list_item = QListWidgetItem(self.leaderboard_list)
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, data['symbol'])

            # Add widget to list
            self.leaderboard_list.addItem(list_item)
            self.leaderboard_list.setItemWidget(list_item, item_widget)

        # Update alerts
        alerts = session_momentum_scanner.get_momentum_alerts(threshold=70)
        if alerts:
            self.alerts_text.setPlainText('\n'.join(alerts))

            # Emit alert signal
            for alert in alerts:
                self.momentum_alert.emit(alert)
        else:
            self.alerts_text.setPlainText("No high momentum alerts")

        # Update status
        time_str = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(
            f"Updated: {time_str} | {len(leaderboard)} symbols scanned"
        )

    def set_symbol(self, symbol: str):
        """Update current symbol (triggers refresh)"""
        # This widget shows ALL pairs leaderboard, but we refresh on symbol change
        self.on_refresh_requested()

    def on_refresh_requested(self):
        """Handle refresh request"""
        self.status_label.setText("Refreshing...")
        # Actual data fetching done by parent/controller

    def on_symbol_clicked(self, item):
        """Handle symbol click in leaderboard"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.symbol_selected.emit(symbol)

    def scan_and_update(self, market_data: Dict[str, pd.DataFrame]):
        """
        Convenience method to scan and update in one call

        Args:
            market_data: {symbol: DataFrame} with OHLC data
        """
        # Run scan
        leaderboard = session_momentum_scanner.scan_momentum(market_data)

        # Update display
        self.update_momentum_data(leaderboard)

    def clear_display(self):
        """Clear all displays"""
        self.best_opportunity_label.setText("--")
        self.leaderboard_list.clear()
        self.alerts_text.setPlainText("No data")
        self.status_label.setText("Status: Waiting for data")

    def set_auto_focus(self, enabled: bool):
        """Enable/disable auto-focus on best opportunity"""
        self.auto_focus_btn.setChecked(enabled)

    def get_selected_symbol(self) -> Optional[str]:
        """Get currently selected symbol from leaderboard"""
        current_item = self.leaderboard_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def load_sample_data(self):
        """Load sample momentum data for demonstration"""
        sample_data = [
            {
                'symbol': 'GBPUSD',
                'momentum_score': 89.5,
                'session_range_pips': 142,
                'direction': 'BULLISH',
                'trending_strength': 85,
                'hourly_volatility': 0.0032,
                'volume_ratio': 1.8,
                'session': 'London',
                'recommendation': 'BEST OPPORTUNITY'
            },
            {
                'symbol': 'EURUSD',
                'momentum_score': 76.2,
                'session_range_pips': 98,
                'direction': 'BULLISH',
                'trending_strength': 72,
                'hourly_volatility': 0.0028,
                'volume_ratio': 1.5,
                'session': 'London',
                'recommendation': 'STRONG'
            },
            {
                'symbol': 'USDJPY',
                'momentum_score': 68.3,
                'session_range_pips': 85,
                'direction': 'BEARISH',
                'trending_strength': 65,
                'hourly_volatility': 0.0025,
                'volume_ratio': 1.3,
                'session': 'Tokyo',
                'recommendation': 'GOOD'
            },
            {
                'symbol': 'AUDUSD',
                'momentum_score': 55.7,
                'session_range_pips': 62,
                'direction': 'BULLISH',
                'trending_strength': 58,
                'hourly_volatility': 0.0022,
                'volume_ratio': 1.1,
                'session': 'Sydney',
                'recommendation': 'MODERATE'
            },
            {
                'symbol': 'NZDUSD',
                'momentum_score': 45.2,
                'session_range_pips': 48,
                'direction': 'BEARISH',
                'trending_strength': 42,
                'hourly_volatility': 0.0019,
                'volume_ratio': 0.9,
                'session': 'Sydney',
                'recommendation': 'WEAK'
            }
        ]

        self.update_momentum_data(sample_data)


# Need to import at the end to avoid circular import
from datetime import datetime
import pandas as pd
