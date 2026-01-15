"""
AppleTrader Pro - Volatility Position Sizing Widget
PyQt6 widget for displaying volatility-adjusted position sizing
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QLineEdit, QPushButton, QSpinBox,
                            QDoubleSpinBox, QFrame, QGridLayout, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, Optional
import pandas as pd

from widgets.volatility_position_sizer import (volatility_position_sizer,
                                               VolatilityRegime, TrendStrength)
from core.ai_assist_base import AIAssistMixin
from core.verbose_mode_manager import vprint
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.verbose_mode_manager import vprint


class VolatilityPositionWidget(AIAssistMixin, QWidget):
    """
    Volatility-Adjusted Position Sizing Display Widget

    Shows:
    - Current volatility regime and multiplier
    - Trend strength and multiplier
    - Adjusted risk percentage
    - Calculated position size
    - Risk recommendation
    """

    position_calculated = pyqtSignal(dict)  # Emits position size data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = "EURUSD"
        self.current_data = None
        self.init_ui()
        self.setup_ai_assist("volatility_position")

        # Auto-refresh timer to get live data
        from PyQt6.QtCore import QTimer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(3000)  # Refresh every 3 seconds

        # Initial update
        self.update_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()
        title = QLabel("🎯 Volatility-Adjusted Position Sizer")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.ai_checkbox_placeholder = header_layout
        layout.addLayout(header_layout)

        # === ACCOUNT SETTINGS ===
        account_group = QGroupBox("Account Settings")
        account_layout = QGridLayout()

        account_layout.addWidget(QLabel("Account Balance:"), 0, 0)
        self.balance_input = QDoubleSpinBox()
        self.balance_input.setRange(100, 1000000)
        self.balance_input.setValue(10000)
        self.balance_input.setSingleStep(100)  # Step by $100
        self.balance_input.setPrefix("$ ")
        self.balance_input.setMinimumHeight(35)  # Taller for bigger buttons
        self.balance_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.balance_input.valueChanged.connect(self.on_settings_changed)
        account_layout.addWidget(self.balance_input, 0, 1)

        account_layout.addWidget(QLabel("Base Risk %:"), 1, 0)
        self.risk_input = QDoubleSpinBox()
        self.risk_input.setRange(0.1, 5.0)  # Increased max to 5%
        self.risk_input.setValue(0.5)
        self.risk_input.setSingleStep(0.1)
        self.risk_input.setDecimals(1)
        self.risk_input.setSuffix(" %")
        self.risk_input.setMinimumHeight(35)  # Taller for bigger buttons
        self.risk_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.risk_input.valueChanged.connect(self.on_settings_changed)
        account_layout.addWidget(self.risk_input, 1, 1)

        account_group.setLayout(account_layout)
        layout.addWidget(account_group)

        # === MARKET CONDITIONS ===
        conditions_group = QGroupBox("Current Market Conditions")
        conditions_layout = QVBoxLayout()

        # Volatility
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volatility:"))
        self.volatility_label = QLabel("--")
        self.volatility_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        vol_layout.addWidget(self.volatility_label)
        vol_layout.addStretch()
        self.volatility_multiplier_label = QLabel("--")
        self.volatility_multiplier_label.setFont(QFont("Courier", 9))
        vol_layout.addWidget(self.volatility_multiplier_label)
        conditions_layout.addLayout(vol_layout)

        # Trend
        trend_layout = QHBoxLayout()
        trend_layout.addWidget(QLabel("Trend:"))
        self.trend_label = QLabel("--")
        self.trend_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        trend_layout.addWidget(self.trend_label)
        trend_layout.addStretch()
        self.trend_multiplier_label = QLabel("--")
        self.trend_multiplier_label.setFont(QFont("Courier", 9))
        trend_layout.addWidget(self.trend_multiplier_label)
        conditions_layout.addLayout(trend_layout)

        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)

        # === TRADE INPUTS ===
        trade_group = QGroupBox("Trade Parameters")
        trade_layout = QGridLayout()

        trade_layout.addWidget(QLabel("Entry Price:"), 0, 0)
        self.entry_input = QDoubleSpinBox()
        self.entry_input.setRange(0.0001, 100000)
        self.entry_input.setDecimals(5)
        self.entry_input.setValue(1.10000)
        self.entry_input.setSingleStep(0.0001)  # Step by 1 pip
        self.entry_input.setMinimumHeight(35)  # Taller for bigger buttons
        self.entry_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.entry_input.valueChanged.connect(self.on_trade_params_changed)
        trade_layout.addWidget(self.entry_input, 0, 1)

        trade_layout.addWidget(QLabel("Stop Loss:"), 1, 0)
        self.sl_input = QDoubleSpinBox()
        self.sl_input.setRange(0.0001, 100000)
        self.sl_input.setDecimals(5)
        self.sl_input.setValue(1.09500)
        self.sl_input.setSingleStep(0.0001)  # Step by 1 pip
        self.sl_input.setMinimumHeight(35)  # Taller for bigger buttons
        self.sl_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.sl_input.valueChanged.connect(self.on_trade_params_changed)
        trade_layout.addWidget(self.sl_input, 1, 1)

        trade_layout.addWidget(QLabel("Direction:"), 2, 0)
        direction_layout = QHBoxLayout()
        self.buy_btn = QPushButton("BUY")
        self.buy_btn.setCheckable(True)
        self.buy_btn.setChecked(True)
        self.buy_btn.clicked.connect(lambda: self.set_direction('BUY'))
        direction_layout.addWidget(self.buy_btn)

        self.sell_btn = QPushButton("SELL")
        self.sell_btn.setCheckable(True)
        self.sell_btn.clicked.connect(lambda: self.set_direction('SELL'))
        direction_layout.addWidget(self.sell_btn)
        trade_layout.addLayout(direction_layout, 2, 1)

        # Calculate button
        self.calculate_btn = QPushButton("📊 Calculate Position Size")
        self.calculate_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.calculate_btn.clicked.connect(self.calculate_position)
        trade_layout.addWidget(self.calculate_btn, 3, 0, 1, 2)

        trade_group.setLayout(trade_layout)
        layout.addWidget(trade_group)

        # === RESULTS ===
        results_group = QGroupBox("📋 Position Size Results")
        results_layout = QVBoxLayout()

        # Adjusted risk
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Adjusted Risk:"))
        self.adjusted_risk_label = QLabel("--")
        self.adjusted_risk_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
        risk_layout.addWidget(self.adjusted_risk_label)
        risk_layout.addStretch()
        results_layout.addLayout(risk_layout)

        # Dollar risk
        dollar_layout = QHBoxLayout()
        dollar_layout.addWidget(QLabel("Dollar Risk:"))
        self.dollar_risk_label = QLabel("--")
        self.dollar_risk_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
        dollar_layout.addWidget(self.dollar_risk_label)
        dollar_layout.addStretch()
        results_layout.addLayout(dollar_layout)

        # Position size (MAIN RESULT)
        size_frame = QFrame()
        size_frame.setFrameShape(QFrame.Shape.StyledPanel)
        size_frame.setStyleSheet("""
            QFrame {
                background-color: #2a4a4a;
                border: 2px solid #00aaff;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        size_layout = QHBoxLayout(size_frame)

        size_layout.addWidget(QLabel("POSITION SIZE:"))
        self.position_size_label = QLabel("-- lots")
        self.position_size_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.position_size_label.setStyleSheet("color: #00ff00; border: none;")
        size_layout.addWidget(self.position_size_label)
        size_layout.addStretch()

        results_layout.addWidget(size_frame)

        # SL distance
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(QLabel("SL Distance:"))
        self.sl_distance_label = QLabel("--")
        self.sl_distance_label.setFont(QFont("Courier", 10))
        sl_layout.addWidget(self.sl_distance_label)
        sl_layout.addStretch()
        results_layout.addLayout(sl_layout)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # === RECOMMENDATION ===
        rec_group = QGroupBox("💡 Recommendation")
        rec_layout = QVBoxLayout()

        self.recommendation_label = QLabel("Enter trade parameters to calculate")
        self.recommendation_label.setFont(QFont("Courier", 9))
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("color: #ffaa00;")
        rec_layout.addWidget(self.recommendation_label)

        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        # AI suggestion frame placeholder
        self.ai_suggestion_placeholder = layout

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
            QLineEdit, QDoubleSpinBox, QSpinBox {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                min-height: 30px;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 25px;
                height: 16px;
                border-left: 1px solid #555;
                border-bottom: 1px solid #555;
                background-color: #3a3a3a;
                border-top-right-radius: 3px;
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {
                background-color: #0d7377;
            }
            QDoubleSpinBox::up-button:pressed, QSpinBox::up-button:pressed {
                background-color: #0a5a5d;
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 7px solid #ffffff;
                margin: 2px;
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 25px;
                height: 16px;
                border-left: 1px solid #555;
                border-top: 1px solid #555;
                background-color: #3a3a3a;
                border-bottom-right-radius: 3px;
            }
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background-color: #0d7377;
            }
            QDoubleSpinBox::down-button:pressed, QSpinBox::down-button:pressed {
                background-color: #0a5a5d;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #ffffff;
                margin: 2px;
            }
            QPushButton {
                background-color: #0d7377;
                border: none;
                border-radius: 3px;
                padding: 8px;
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

    def set_market_data(self, symbol: str, df: pd.DataFrame):
        """
        Set market data for position sizing calculations

        Args:
            symbol: Trading symbol
            df: DataFrame with OHLC data
        """
        self.current_symbol = symbol
        self.current_data = df

        # Update market conditions display
        self.update_market_conditions()

        # Auto-update entry price to current market price
        if 'close' in df.columns and len(df) > 0:
            current_price = df['close'].iloc[-1]
            self.entry_input.setValue(current_price)

            # Auto-set stop loss at a reasonable distance (50 pips for forex)
            if symbol.endswith('JPY'):
                sl_distance = 0.50  # 50 pips for JPY pairs
            else:
                sl_distance = 0.0050  # 50 pips for other pairs

            # Set SL based on current direction
            if self.buy_btn.isChecked():
                self.sl_input.setValue(current_price - sl_distance)
            else:
                self.sl_input.setValue(current_price + sl_distance)

            vprint(f"[VolatilityPosition]   → Auto-set Entry: {current_price:.5f}, SL: {self.sl_input.value():.5f}")

            # Auto-calculate position with updated prices
            self.auto_calculate_position()

    def set_symbol(self, symbol: str):
        """Update current symbol and refresh with live data from data_manager"""
        if symbol != self.current_symbol:
            self.current_symbol = symbol
            # CRITICAL: Get live data from data_manager!
            self.update_from_live_data()

    def update_from_live_data(self):
        """Get live data from data_manager and update position sizing"""
        from core.data_manager import data_manager

        vprint(f"\n[VolatilityPosition] update_from_live_data() called for {self.current_symbol}")

        # Get candles from data_manager (uses currently loaded symbol)
        candles = data_manager.get_candles(count=100)

        if not candles:
            vprint(f"[VolatilityPosition] ❌ No data available from data_manager")
            self.clear_display()
            return

        # Convert to DataFrame
        df = pd.DataFrame(candles)

        vprint(f"[VolatilityPosition] ✓ Got {len(df)} candles for {self.current_symbol}")

        # Show last close price for verification
        if 'close' in df.columns:
            last_close = df['close'].iloc[-1]
            vprint(f"[VolatilityPosition]   → Last close: {last_close:.5f}")

        # Set the market data (this will trigger calculations)
        self.set_market_data(self.current_symbol, df)

        vprint(f"[VolatilityPosition] ✓ Market data updated successfully")

    def update_market_conditions(self):
        """Update volatility and trend displays"""
        if self.current_symbol is None or self.current_data is None:
            vprint(f"[VolatilityPosition] ❌ Cannot update - missing symbol or data")
            return

        vprint(f"[VolatilityPosition] Calculating market conditions...")

        try:
            # Get risk summary
            summary = volatility_position_sizer.get_risk_summary(
                self.current_symbol, self.current_data
            )

            # Update volatility
            vol_regime = summary['volatility_regime']
            vol_mult = summary['volatility_multiplier']

            vprint(f"[VolatilityPosition]   → Volatility: {vol_regime} (×{vol_mult:.2f})")

            vol_color = self._get_volatility_color(vol_regime)
            self.volatility_label.setText(vol_regime.replace('_', ' '))
            self.volatility_label.setStyleSheet(f"color: {vol_color};")
            self.volatility_multiplier_label.setText(f"×{vol_mult:.2f}")

            # Update trend
            trend_strength = summary['trend_strength']
            trend_mult = summary['trend_multiplier']

            vprint(f"[VolatilityPosition]   → Trend: {trend_strength} (×{trend_mult:.2f})")

            trend_color = self._get_trend_color(trend_strength)
            self.trend_label.setText(trend_strength.replace('_', ' '))
            self.trend_label.setStyleSheet(f"color: {trend_color};")
            self.trend_multiplier_label.setText(f"×{trend_mult:.2f}")

            # Update recommendation
            recommendation = summary['recommendation']
            self.recommendation_label.setText(recommendation)

            vprint(f"[VolatilityPosition]   → Recommendation: {recommendation[:60]}...")
            vprint(f"[VolatilityPosition] ✓ Market conditions updated successfully")

        except Exception as e:
            vprint(f"[VolatilityPosition] ❌ Error updating market conditions: {e}")
            import traceback
            traceback.print_exc()

    def auto_calculate_position(self):
        """Silently calculate position size when market data updates"""
        if self.current_symbol is None or self.current_data is None:
            return

        # Get inputs
        entry = self.entry_input.value()
        sl = self.sl_input.value()
        direction = 'BUY' if self.buy_btn.isChecked() else 'SELL'

        # Validate
        if entry == sl:
            return

        try:
            # Update sizer settings
            volatility_position_sizer.update_account_balance(self.balance_input.value())
            volatility_position_sizer.update_base_risk(self.risk_input.value())

            # Calculate
            result = volatility_position_sizer.calculate_position_size(
                self.current_symbol,
                self.current_data,
                entry,
                sl,
                direction
            )

            if 'error' not in result:
                # Display results
                self.adjusted_risk_label.setText(f"{result['adjusted_risk_pct']:.2f}%")
                self.dollar_risk_label.setText(f"${result['dollar_risk']:.2f}")
                self.position_size_label.setText(f"{result['position_size_lots']:.2f} lots")
                self.sl_distance_label.setText(f"{result['sl_distance_pips']:.1f} pips")

                # Update recommendation with detailed breakdown
                rec_parts = []
                rec_parts.append(f"Base risk {result['base_risk_pct']:.1f}%")
                rec_parts.append(f"× Vol {result['volatility_multiplier']:.2f}")
                rec_parts.append(f"× Trend {result['trend_multiplier']:.2f}")
                rec_parts.append(f"= {result['adjusted_risk_pct']:.2f}%")

                self.recommendation_label.setText(' '.join(rec_parts))

                vprint(f"[VolatilityPosition]   → Position: {result['position_size_lots']:.2f} lots at {result['adjusted_risk_pct']:.2f}% risk")

                # Emit signal
                self.position_calculated.emit(result)

        except Exception as e:
            vprint(f"[VolatilityPosition] ⚠️ Auto-calculate error: {e}")

    def calculate_position(self):
        """Calculate and display position size (manual button click)"""
        if self.current_symbol is None or self.current_data is None:
            self.recommendation_label.setText("⚠️ No market data available")
            return

        # Get inputs
        entry = self.entry_input.value()
        sl = self.sl_input.value()
        direction = 'BUY' if self.buy_btn.isChecked() else 'SELL'

        # Validate
        if entry == sl:
            self.recommendation_label.setText("⚠️ Entry and SL cannot be equal")
            return

        # Update sizer settings
        volatility_position_sizer.update_account_balance(self.balance_input.value())
        volatility_position_sizer.update_base_risk(self.risk_input.value())

        # Calculate
        result = volatility_position_sizer.calculate_position_size(
            self.current_symbol,
            self.current_data,
            entry,
            sl,
            direction
        )

        if 'error' in result:
            self.recommendation_label.setText(f"⚠️ {result['error']}")
            return

        # Display results
        self.adjusted_risk_label.setText(f"{result['adjusted_risk_pct']:.2f}%")
        self.dollar_risk_label.setText(f"${result['dollar_risk']:.2f}")
        self.position_size_label.setText(f"{result['position_size_lots']:.2f} lots")
        self.sl_distance_label.setText(f"{result['sl_distance_pips']:.1f} pips")

        # Update recommendation with detailed breakdown
        rec_parts = []
        rec_parts.append(f"Base risk {result['base_risk_pct']:.1f}%")
        rec_parts.append(f"× Vol {result['volatility_multiplier']:.2f}")
        rec_parts.append(f"× Trend {result['trend_multiplier']:.2f}")
        rec_parts.append(f"= {result['adjusted_risk_pct']:.2f}%")

        self.recommendation_label.setText(' '.join(rec_parts))

        # Emit signal
        self.position_calculated.emit(result)

    def on_settings_changed(self):
        """Handle account settings change"""
        # Recalculate if we have data
        if self.current_symbol and self.current_data is not None and not self.current_data.empty:
            self.update_market_conditions()

    def on_trade_params_changed(self):
        """Handle trade parameter changes"""
        # Could auto-calculate here if desired
        pass

    def set_direction(self, direction: str):
        """Set trade direction"""
        if direction == 'BUY':
            self.buy_btn.setChecked(True)
            self.sell_btn.setChecked(False)
        else:
            self.buy_btn.setChecked(False)
            self.sell_btn.setChecked(True)

    def _get_volatility_color(self, regime: str) -> str:
        """Get color for volatility regime"""
        if 'EXTREME_HIGH' in regime or 'HIGH' in regime:
            return '#ff0000'  # Red
        elif 'LOW' in regime:
            return '#00ff00'  # Green
        else:
            return '#ffaa00'  # Orange

    def _get_trend_color(self, strength: str) -> str:
        """Get color for trend strength"""
        if 'STRONG' in strength or 'TRENDING' in strength:
            return '#00ff00'  # Green
        elif 'RANGING' in strength:
            return '#ff0000'  # Red
        else:
            return '#ffaa00'  # Orange

    def load_sample_conditions(self):
        """Load sample market conditions for demonstration"""
        # Set sample volatility and trend
        self.volatility_label.setText("NORMAL")
        self.volatility_label.setStyleSheet("color: #ffaa00;")  # Orange for normal
        self.volatility_multiplier_label.setText("x1.0")

        self.trend_label.setText("STRONG TRENDING")
        self.trend_label.setStyleSheet("color: #00ff00;")  # Green for strong trend
        self.trend_multiplier_label.setText("x1.3")

    def clear_display(self):
        """Clear all displays"""
        self.volatility_label.setText("--")
        self.trend_label.setText("--")
        self.adjusted_risk_label.setText("--")
        self.dollar_risk_label.setText("--")
        self.position_size_label.setText("-- lots")
        self.sl_distance_label.setText("--")
        self.recommendation_label.setText("No data")

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        vprint(f"\n[VolatilityPosition] ====== Timer fired: update_data() ======")

        if is_demo_mode():
            vprint(f"[VolatilityPosition] Mode: DEMO - loading sample conditions")
            # Load demo volatility data
            self.load_sample_conditions()
        else:
            vprint(f"[VolatilityPosition] Mode: LIVE - fetching real data")
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_data is not None and not self.current_data.empty:
            vprint(f"[VolatilityPosition] AI enabled - updating suggestions")
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        vprint(f"Volatility Position Sizer switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for volatility-adjusted position sizing

        Analyzes:
        - Volatility regime risk assessment
        - Trend strength alignment
        - Position size appropriateness
        - Risk/reward optimization
        - Market regime warnings
        """
        from core.ml_integration import create_ai_suggestion

        if not widget_data:
            return create_ai_suggestion(
                widget_type="volatility_position",
                text="Calculate position size to get AI analysis",
                confidence=0.0
            )

        volatility_regime = widget_data.get('volatility_regime', 'UNKNOWN')
        trend_strength = widget_data.get('trend_strength', 'UNKNOWN')
        adjusted_risk = widget_data.get('adjusted_risk_percent', 0)
        position_size = widget_data.get('position_size', 0)
        volatility_mult = widget_data.get('volatility_multiplier', 1.0)
        trend_mult = widget_data.get('trend_multiplier', 1.0)

        # EXTREME VOLATILITY WARNING
        if volatility_regime == 'EXTREME':
            if adjusted_risk > 0.3:  # Risk reduced below 0.3%
                return create_ai_suggestion(
                    widget_type="volatility_position",
                    text=f"🚨 EXTREME VOLATILITY: Position size reduced by {(1-volatility_mult)*100:.0f}%. Risk now {adjusted_risk:.2f}% (from base). CONSIDER STAYING FLAT until volatility normalizes!",
                    confidence=0.95,
                    emoji="🚨",
                    color="red"
                )
            else:
                return create_ai_suggestion(
                    widget_type="volatility_position",
                    text=f"⚠️ EXTREME VOLATILITY: Micro position ({position_size:.3f} lots) recommended. Risk {adjusted_risk:.2f}%. Only trade with strict discipline.",
                    confidence=0.88,
                    emoji="⚠️",
                    color="orange"
                )

        # HIGH VOLATILITY + WEAK TREND = DANGEROUS
        if volatility_regime == 'HIGH' and trend_strength in ['WEAK', 'NEUTRAL']:
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"⚠️ HIGH RISK: High volatility ({volatility_mult:.2f}x reducer) + {trend_strength} trend. Position: {position_size:.3f} lots at {adjusted_risk:.2f}% risk. Wait for clearer direction.",
                confidence=0.82,
                emoji="⚠️",
                color="orange"
            )

        # OPTIMAL: LOW VOLATILITY + STRONG TREND
        if volatility_regime == 'LOW' and trend_strength == 'STRONG':
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"🔥 OPTIMAL CONDITIONS: Low volatility + STRONG trend! Position boosted to {position_size:.3f} lots ({adjusted_risk:.2f}% risk). EXCELLENT risk/reward setup!",
                confidence=0.92,
                emoji="🔥",
                color="green"
            )

        # GOOD: NORMAL VOLATILITY + STRONG TREND
        if volatility_regime == 'NORMAL' and trend_strength == 'STRONG':
            multiplier_effect = volatility_mult * trend_mult
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"✓ GOOD SETUP: Normal volatility + STRONG trend. Position: {position_size:.3f} lots at {adjusted_risk:.2f}% risk. Combined multiplier: {multiplier_effect:.2f}x",
                confidence=0.85,
                emoji="✓",
                color="green"
            )

        # MODERATE: NORMAL CONDITIONS
        if volatility_regime == 'NORMAL' and trend_strength == 'MODERATE':
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"📊 MODERATE: Normal market conditions. Standard position sizing ({position_size:.3f} lots, {adjusted_risk:.2f}% risk). Monitor for changes.",
                confidence=0.75,
                emoji="📊",
                color="yellow"
            )

        # CONSERVATIVE: LOW VOLATILITY + WEAK TREND
        if volatility_regime == 'LOW' and trend_strength in ['WEAK', 'NEUTRAL']:
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"⚠️ MIXED SIGNALS: Low volatility BUT weak trend direction. Position: {position_size:.3f} lots. Be ready to exit if trend doesn't develop.",
                confidence=0.70,
                emoji="⚠️",
                color="yellow"
            )

        # HIGH VOLATILITY BUT STRONG TREND
        if volatility_regime == 'HIGH' and trend_strength == 'STRONG':
            return create_ai_suggestion(
                widget_type="volatility_position",
                text=f"📈 ACTIVE MARKET: High volatility but STRONG trend compensates. Position: {position_size:.3f} lots ({adjusted_risk:.2f}% risk). Use wide stops!",
                confidence=0.80,
                emoji="📈",
                color="yellow"
            )

        # DEFAULT
        return create_ai_suggestion(
            widget_type="volatility_position",
            text=f"Position calculated: {position_size:.3f} lots at {adjusted_risk:.2f}% risk. Volatility: {volatility_regime}, Trend: {trend_strength}",
            confidence=0.72,
            emoji="📊",
            color="blue"
        )
