"""
AppleTrader Pro - Risk-Reward Optimizer Widget
PyQt6 widget for displaying optimized TP levels
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QPushButton, QTextEdit, QFrame,
                            QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List, Optional

from widgets.risk_reward_optimizer import risk_reward_optimizer
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.multi_symbol_manager import get_all_symbols


class TPLevelWidget(QWidget):
    """Widget for displaying a single TP level"""

    def __init__(self, tp_number: int, tp_data: Dict, parent=None):
        super().__init__(parent)
        self.tp_number = tp_number
        self.tp_data = tp_data
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with TP number and stars
        header_layout = QHBoxLayout()

        tp_label = QLabel(f"TP{self.tp_number}")
        tp_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header_layout.addWidget(tp_label)

        stars = '⭐' * self.tp_data['quality_stars']
        stars_label = QLabel(stars)
        header_layout.addWidget(stars_label)

        header_layout.addStretch()

        # R multiple
        r_label = QLabel(f"{self.tp_data['r_multiple']:.1f}R")
        r_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        r_label.setStyleSheet("color: #00ff00;")
        header_layout.addWidget(r_label)

        layout.addLayout(header_layout)

        # Price
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        price_label = QLabel(f"{self.tp_data['price']:.5f}")
        price_label.setFont(QFont("Courier", 10))
        price_layout.addWidget(price_label)
        price_layout.addStretch()
        layout.addLayout(price_layout)

        # Structure info
        structure = f"{self.tp_data['timeframe']} {self.tp_data['structure_type'].upper()}"
        structure_label = QLabel(structure)
        structure_label.setFont(QFont("Courier", 9))
        structure_label.setStyleSheet("color: #00aaff;")
        layout.addWidget(structure_label)

        # Probability and partial close
        info_layout = QHBoxLayout()

        prob_label = QLabel(f"📊 {self.tp_data['probability']:.0f}% reach")
        prob_label.setFont(QFont("Courier", 9))
        info_layout.addWidget(prob_label)

        info_layout.addStretch()

        partial_label = QLabel(f"Close {self.tp_data['partial_close_pct']}%")
        partial_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
        partial_label.setStyleSheet("color: #ffaa00;")
        info_layout.addWidget(partial_label)

        layout.addLayout(info_layout)

        # Expected value
        ev_label = QLabel(f"EV: {self.tp_data['expected_value']:.2f}R")
        ev_label.setFont(QFont("Courier", 9))
        ev_label.setStyleSheet("color: #888;")
        layout.addWidget(ev_label)

        # Style frame
        self.setStyleSheet("""
            QWidget {
                background-color: #2a2a3a;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """)


class RiskRewardWidget(QWidget, AIAssistMixin):
    """
    Risk-Reward Optimizer Display Widget (AI-Enhanced)

    Shows:
    - Optimized TP levels at structure
    - Quality rating for each TP (stars)
    - Probability of reaching each level
    - Partial close percentages
    - Total expected value
    - AI-powered trade recommendations
    """

    tp_calculated = pyqtSignal(dict)  # Emits TP analysis

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = "EURUSD"
        self.current_analysis = None

        # Setup AI assistance
        self.setup_ai_assist("risk_reward")

        self.init_ui()

        # Connect to demo mode changes
        demo_mode_manager.mode_changed.connect(self.on_mode_changed)

        # Auto-refresh timer
        from PyQt6.QtCore import QTimer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(3000)

        # Initial update
        self.update_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🎯 Risk-Reward Optimizer")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # AI Assist checkbox
        self.create_ai_checkbox(header_layout)

        layout.addLayout(header_layout)

        # === TRADE SETUP ===
        setup_group = QGroupBox("Trade Setup")
        setup_layout = QGridLayout()

        setup_layout.addWidget(QLabel("Entry:"), 0, 0)
        self.entry_input = QDoubleSpinBox()
        self.entry_input.setRange(0.0001, 100000)
        self.entry_input.setDecimals(5)
        self.entry_input.setValue(1.10000)
        setup_layout.addWidget(self.entry_input, 0, 1)

        setup_layout.addWidget(QLabel("Stop Loss:"), 1, 0)
        self.sl_input = QDoubleSpinBox()
        self.sl_input.setRange(0.0001, 100000)
        self.sl_input.setDecimals(5)
        self.sl_input.setValue(1.09500)
        setup_layout.addWidget(self.sl_input, 1, 1)

        setup_layout.addWidget(QLabel("Direction:"), 2, 0)
        dir_layout = QHBoxLayout()
        self.buy_btn = QPushButton("BUY")
        self.buy_btn.setCheckable(True)
        self.buy_btn.setChecked(True)
        self.buy_btn.clicked.connect(lambda: self.set_direction('BUY'))
        dir_layout.addWidget(self.buy_btn)

        self.sell_btn = QPushButton("SELL")
        self.sell_btn.setCheckable(True)
        self.sell_btn.clicked.connect(lambda: self.set_direction('SELL'))
        dir_layout.addWidget(self.sell_btn)
        setup_layout.addLayout(dir_layout, 2, 1)

        # Calculate button
        self.calculate_btn = QPushButton("🎯 Optimize TPs")
        self.calculate_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.calculate_btn.clicked.connect(self.calculate_tps)
        setup_layout.addWidget(self.calculate_btn, 3, 0, 1, 2)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # === EXPECTED VALUE DISPLAY ===
        ev_frame = QFrame()
        ev_frame.setFrameShape(QFrame.Shape.StyledPanel)
        ev_frame.setStyleSheet("""
            QFrame {
                background-color: #2a3a4a;
                border: 2px solid #00aaff;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        ev_layout = QHBoxLayout(ev_frame)

        ev_layout.addWidget(QLabel("EXPECTED VALUE:"))
        self.ev_label = QLabel("-- R")
        self.ev_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.ev_label.setStyleSheet("color: #00ff00; border: none;")
        ev_layout.addWidget(self.ev_label)
        ev_layout.addStretch()

        layout.addWidget(ev_frame)

        # === TP LEVELS ===
        tp_group = QGroupBox("📍 Optimized Take Profit Levels")
        self.tp_layout = QVBoxLayout()

        self.tp_widgets = []  # Will hold TP widgets

        # Placeholder
        self.no_tp_label = QLabel("Enter trade setup and click 'Optimize TPs'")
        self.no_tp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_tp_label.setStyleSheet("color: #888;")
        self.tp_layout.addWidget(self.no_tp_label)

        tp_group.setLayout(self.tp_layout)
        layout.addWidget(tp_group)

        # === RECOMMENDATION ===
        rec_group = QGroupBox("💡 Recommendation")
        rec_layout = QVBoxLayout()

        self.recommendation_text = QTextEdit()
        self.recommendation_text.setReadOnly(True)
        self.recommendation_text.setMaximumHeight(80)
        self.recommendation_text.setFont(QFont("Courier", 9))
        rec_layout.addWidget(self.recommendation_text)

        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        # === AI SUGGESTION FRAME ===
        self.create_ai_suggestion_frame(layout)

        layout.addStretch()

        # Apply dark theme
        self.apply_dark_theme()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager

        # Get candles from data_manager (uses currently loaded symbol)
        candles = data_manager.get_candles(count=200)

        if not candles:
            print(f"[RiskReward] No data available from data_manager")
            return

        # Convert to DataFrame for analysis
        import pandas as pd
        df = pd.DataFrame(candles)

        # Extract structure levels from the data (support/resistance)
        # For now, use high/low of recent candles as proxy for structure
        if len(df) >= 50:
            recent = df.tail(50)
            # Format as dict with 'price' and 'strength' keys (required by optimizer)
            self.structure_levels = {
                'resistance': [{'price': float(recent['high'].max()), 'strength': 1.0}],
                'support': [{'price': float(recent['low'].min()), 'strength': 1.0}]
            }

        symbol = self.current_symbol
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Live: {symbol}")

        print(f"[RiskReward] Updated with {len(candles)} candles for {symbol}")

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
            QDoubleSpinBox {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
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

    def load_sample_data(self):
        """Load sample structure levels and calculate TPs for demonstration"""
        # Sample structure levels for EURUSD - must be dictionaries with price, strength, timeframe
        sample_structure = {
            'support': [
                {'price': 1.09200, 'strength': 750, 'timeframe': 'H4'},
                {'price': 1.08850, 'strength': 620, 'timeframe': 'H1'},
                {'price': 1.08500, 'strength': 800, 'timeframe': 'D1'}
            ],
            'resistance': [
                {'price': 1.10500, 'strength': 700, 'timeframe': 'H4'},
                {'price': 1.10800, 'strength': 850, 'timeframe': 'D1'},
                {'price': 1.11200, 'strength': 680, 'timeframe': 'H4'},
                {'price': 1.11650, 'strength': 900, 'timeframe': 'D1'}
            ]
        }
        self.set_structure_levels(sample_structure)

        # Set sample entry and SL
        self.entry_input.setValue(1.10000)
        self.sl_input.setValue(1.09500)
        self.set_direction('BUY')

        # Auto-calculate to show sample data
        self.calculate_tps()

    def set_structure_levels(self, structure_levels: Dict):
        """
        Set structure levels for TP optimization

        Args:
            structure_levels: {support: [...], resistance: [...]}
        """
        self.structure_levels = structure_levels

    def set_symbol(self, symbol: str):
        """Update current symbol and fetch live data from data_manager"""
        if symbol != self.current_symbol:
            self.current_symbol = symbol
            # CRITICAL: Get NEW structure levels from data_manager for the new symbol!
            self.update_from_live_data()

    def calculate_tps(self):
        """Calculate and display optimized TPs"""
        if not hasattr(self, 'structure_levels'):
            self.recommendation_text.setPlainText(
                "⚠️ No structure data available. Please load market data first."
            )
            return

        # Get inputs
        entry = self.entry_input.value()
        sl = self.sl_input.value()
        direction = 'BUY' if self.buy_btn.isChecked() else 'SELL'
        symbol = self.current_symbol

        # Validate
        if entry == sl:
            self.recommendation_text.setPlainText("⚠️ Entry and SL cannot be equal")
            return

        # Calculate
        analysis = risk_reward_optimizer.optimize_take_profits(
            symbol, direction, entry, sl, self.structure_levels, 'H4'
        )

        if 'error' in analysis:
            self.recommendation_text.setPlainText(f"⚠️ {analysis['error']}")
            return

        self.current_analysis = analysis

        # Update display
        self.display_analysis(analysis)

        # Emit signal
        self.tp_calculated.emit(analysis)

    def display_analysis(self, analysis: Dict):
        """Display the TP analysis"""
        # Update expected value
        ev = analysis['total_expected_value']
        self.ev_label.setText(f"{ev:.2f}R")

        # Color code EV
        if ev >= 2.0:
            ev_color = "#00ff00"  # Green
        elif ev >= 1.5:
            ev_color = "#7fff00"  # Yellow-green
        elif ev >= 1.0:
            ev_color = "#ffaa00"  # Orange
        else:
            ev_color = "#ff6600"  # Red-orange

        self.ev_label.setStyleSheet(f"color: {ev_color}; border: none;")

        # Clear old TP widgets
        for widget in self.tp_widgets:
            widget.deleteLater()
        self.tp_widgets = []

        if self.no_tp_label:
            self.no_tp_label.deleteLater()
            self.no_tp_label = None

        # Create TP widgets
        tp_levels = analysis.get('tp_levels', [])
        for i, tp_data in enumerate(tp_levels, 1):
            tp_widget = TPLevelWidget(i, tp_data)
            self.tp_layout.addWidget(tp_widget)
            self.tp_widgets.append(tp_widget)

        # Update recommendation
        self.recommendation_text.setPlainText(analysis['recommendation'])

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # In demo mode, use preset values for demonstration
            pass  # Risk/Reward uses manual inputs, no demo data needed
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_analysis:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Risk/Reward Optimizer widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Custom AI analysis for risk/reward optimization

        Args:
            prediction: ML prediction data from ml_integration
            widget_data: Current TP analysis

        Returns:
            Formatted suggestion dictionary
        """
        from core.ml_integration import create_ai_suggestion

        if not self.current_analysis:
            return create_ai_suggestion(
                widget_type="risk_reward",
                text="Calculate TPs to get AI analysis",
                confidence=0.0
            )

        tp_levels = self.current_analysis.get('tp_levels', [])
        total_ev = self.current_analysis.get('total_expected_value', 0)

        if not tp_levels:
            return create_ai_suggestion(
                widget_type="risk_reward",
                text="No TP levels calculated",
                confidence=0.0
            )

        # Analyze TP quality
        best_tp = max(tp_levels, key=lambda x: x['quality_stars'])
        avg_quality = sum(tp['quality_stars'] for tp in tp_levels) / len(tp_levels)

        if avg_quality >= 4.5:
            confidence = 0.90
            quality = "EXCELLENT"
            action_emoji = "🔥"
            action = f"Exceptional TP structure alignment"
            color = "green"
        elif avg_quality >= 3.5:
            confidence = 0.80
            quality = "GOOD"
            action_emoji = "✓"
            action = f"Good TP levels at key structure"
            color = "green"
        elif avg_quality >= 2.5:
            confidence = 0.65
            quality = "MODERATE"
            action_emoji = "⚠️"
            action = f"Moderate TP quality"
            color = "yellow"
        else:
            confidence = 0.40
            quality = "POOR"
            action_emoji = "❌"
            action = f"Weak TP structure alignment"
            color = "red"

        # Build suggestion text
        suggestion_text = f"{action}\n\n"
        suggestion_text += f"⭐ Average Quality: {avg_quality:.1f}/5 ({quality})\n"
        suggestion_text += f"🎯 Best TP: {best_tp['r_multiple']:.1f}R ({best_tp['quality_stars']}⭐)\n"
        suggestion_text += f"💰 Total EV: +{total_ev:.1f}R\n\n"

        # Add recommendation
        if avg_quality >= 4:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += "✓ Excellent structure alignment - high confidence setup\n"
            suggestion_text += "✓ Consider taking full position size\n"
            suggestion_text += f"✓ Follow partial close plan ({len(tp_levels)} TPs)"
        elif avg_quality >= 3:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += "✓ Good TP structure - proceed with trade\n"
            suggestion_text += "⚠️ Consider reducing size slightly for lower quality TPs"
        else:
            suggestion_text += "💡 AI Recommendation:\n"
            suggestion_text += "❌ Weak structure - reconsider trade setup\n"
            suggestion_text += "❌ Look for better entry or wait for structure to form"

        return create_ai_suggestion(
            widget_type="risk_reward",
            text=suggestion_text,
            confidence=confidence,
            emoji=action_emoji,
            color=color
        )

    def set_direction(self, direction: str):
        """Set trade direction"""
        if direction == 'BUY':
            self.buy_btn.setChecked(True)
            self.sell_btn.setChecked(False)
        else:
            self.buy_btn.setChecked(False)
            self.sell_btn.setChecked(True)

    def set_entry_and_sl(self, entry: float, sl: float):
        """Convenience method to set entry and SL"""
        self.entry_input.setValue(entry)
        self.sl_input.setValue(sl)

    def clear_display(self):
        """Clear all displays"""
        for widget in self.tp_widgets:
            widget.deleteLater()
        self.tp_widgets = []

        self.ev_label.setText("-- R")
        self.recommendation_text.setPlainText("No data")

        if not self.no_tp_label:
            self.no_tp_label = QLabel("Enter trade setup and click 'Optimize TPs'")
            self.no_tp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_tp_label.setStyleSheet("color: #888;")
            self.tp_layout.addWidget(self.no_tp_label)
