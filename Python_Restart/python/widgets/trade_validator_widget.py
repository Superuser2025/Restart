"""
Manual Trade Validator Widget
Validates user's manual trade ideas against ML predictions and market conditions
"""

import json
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class TradeValidatorWidget(QWidget):
    """Widget for validating manual trade ideas"""

    # Signals
    validation_completed = pyqtSignal(str, bool)  # symbol, approved

    def __init__(self):
        super().__init__()
        self.current_symbol = "EURUSD"
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === TITLE ===
        title_label = QLabel("🎯 MANUAL TRADE VALIDATOR")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # === INPUT SECTION ===
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        input_layout = QHBoxLayout(input_frame)

        input_label = QLabel("Enter Trade:")
        input_label.setMinimumWidth(100)
        input_layout.addWidget(input_label)

        self.trade_input = QLineEdit()
        self.trade_input.setPlaceholderText("e.g., BUY EURUSD, SELL GBPUSD, LONG USDJPY")
        self.trade_input.returnPressed.connect(self.validate_trade)
        input_layout.addWidget(self.trade_input)

        self.check_button = QPushButton("✓ Check Trade")
        self.check_button.setMinimumWidth(120)
        self.check_button.clicked.connect(self.validate_trade)
        input_layout.addWidget(self.check_button)

        layout.addWidget(input_frame)

        # === RESULTS SECTION ===
        results_label = QLabel("📊 ANALYSIS RESULT:")
        results_font = QFont()
        results_font.setPointSize(11)
        results_font.setBold(True)
        results_label.setFont(results_font)
        layout.addWidget(results_label)

        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setMinimumHeight(400)
        layout.addWidget(self.results_display)

        # Initial message
        self.show_welcome_message()

    def show_welcome_message(self):
        """Show welcome message"""
        message = """
<div style="text-align: center; padding: 20px;">
<h2 style="color: #4CAF50;">Manual Trade Validator Ready</h2>
<p style="font-size: 14px; color: #aaa;">
Enter your trade idea above and click "Check Trade" to get ML analysis.
</p>
<p style="font-size: 13px; color: #888;">
Examples:
<ul style="text-align: left; color: #bbb;">
<li>BUY EURUSD</li>
<li>SELL GBPUSD</li>
<li>LONG USDJPY</li>
<li>SHORT AUDUSD</li>
<li>Just "EURUSD" to check both directions</li>
</ul>
</p>
<p style="font-size: 12px; color: #666;">
Note: Spread is YOUR call - we focus on ML predictions and market conditions.
</p>
</div>
"""
        self.results_display.setHtml(message)

    def validate_trade(self):
        """Validate the trade input"""
        trade_text = self.trade_input.text().strip().upper()

        if not trade_text:
            self.show_error("Please enter a trade command")
            return

        # Parse the trade command
        parsed = self.parse_trade_command(trade_text)

        if not parsed:
            self.show_error("Invalid trade command. Use format like: BUY EURUSD, SELL GBPUSD")
            return

        direction, symbol = parsed

        # Get ML analysis
        analysis = self.analyze_trade(symbol, direction)

        # Display results
        self.display_analysis(symbol, direction, analysis)

        # Emit signal
        self.validation_completed.emit(symbol, analysis['approved'])

    def parse_trade_command(self, text):
        """
        Parse trade command like "BUY EURUSD" or "SELL GBPUSD"
        Returns: (direction, symbol) or None
        """
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Pattern 1: "BUY EURUSD" or "SELL GBPUSD"
        match = re.match(r'(BUY|SELL|LONG|SHORT)\s+([A-Z]{6})', text)
        if match:
            direction = "BUY" if match.group(1) in ["BUY", "LONG"] else "SELL"
            symbol = match.group(2)
            return (direction, symbol)

        # Pattern 2: Just "EURUSD" (check both directions)
        match = re.match(r'([A-Z]{6})$', text)
        if match:
            symbol = match.group(1)
            return ("CHECK", symbol)  # Will analyze both

        return None

    def analyze_trade(self, symbol, direction):
        """
        Analyze the trade using ML predictions and market conditions
        Returns: dict with analysis results
        """
        analysis = {
            'approved': False,
            'ml_signal': 'UNKNOWN',
            'probability': 0.0,
            'confidence': 0.0,
            'reasons': [],
            'warnings': [],
            'market_conditions': {}
        }

        # Read ML prediction
        ml_data = self.read_ml_prediction(symbol)

        if ml_data:
            analysis['ml_signal'] = ml_data.get('signal', 'UNKNOWN')
            analysis['probability'] = ml_data.get('probability', 0.0) * 100  # Convert to percentage
            analysis['confidence'] = ml_data.get('confidence', 0.0) * 100

            # Check if ML approves
            if analysis['ml_signal'] == 'ENTER':
                analysis['approved'] = True
                analysis['reasons'].append(f"ML model shows high win probability ({analysis['probability']:.1f}%)")
                analysis['reasons'].append(f"Model confidence is good ({analysis['confidence']:.1f}%)")
            elif analysis['ml_signal'] == 'WAIT':
                analysis['approved'] = False
                analysis['warnings'].append(f"ML model shows moderate probability ({analysis['probability']:.1f}%)")
                analysis['warnings'].append("Wait for better setup")
            else:  # SKIP
                analysis['approved'] = False
                analysis['warnings'].append(f"ML model shows low probability ({analysis['probability']:.1f}%)")
                analysis['warnings'].append("Not recommended to enter")

        else:
            analysis['warnings'].append("ML prediction file not found")
            analysis['warnings'].append("Proceeding without ML analysis")

        # Get market conditions
        market_conditions = self.get_market_conditions(symbol)
        analysis['market_conditions'] = market_conditions

        # Analyze market conditions
        if market_conditions:
            # Trend
            trend = market_conditions.get('trend', 'UNKNOWN')
            if trend != 'UNKNOWN':
                if direction == "BUY" and trend == "BULLISH":
                    analysis['reasons'].append("Trend is bullish (aligned with BUY)")
                elif direction == "SELL" and trend == "BEARISH":
                    analysis['reasons'].append("Trend is bearish (aligned with SELL)")
                elif direction == "CHECK":
                    analysis['reasons'].append(f"Current trend: {trend}")
                else:
                    analysis['warnings'].append(f"Trading against {trend} trend")

            # Volatility
            volatility = market_conditions.get('volatility', 'UNKNOWN')
            if volatility == 'LOW':
                analysis['reasons'].append("Volatility is low (good for entry)")
            elif volatility == 'HIGH':
                analysis['warnings'].append("Volatility is high (choppy price action)")

            # Session
            session = market_conditions.get('session', 'UNKNOWN')
            if session in ['LONDON', 'NEW_YORK', 'OVERLAP']:
                analysis['reasons'].append(f"{session.title()} session (high liquidity)")
            elif session == 'ASIAN':
                analysis['warnings'].append("Asian session (lower liquidity)")

        # Final decision
        if not analysis['approved'] and len(analysis['warnings']) > len(analysis['reasons']):
            analysis['approved'] = False

        return analysis

    def read_ml_prediction(self, symbol):
        """
        Read ML prediction for the symbol from prediction.json
        Returns: dict with prediction data or None
        """
        try:
            # Try to find prediction.json in MT5 Files directory
            if MT5_AVAILABLE and mt5.initialize():
                terminal_path = mt5.terminal_info().data_path
                mt5.shutdown()
                prediction_file = Path(terminal_path) / "MQL5" / "Files" / "ML_Data" / "prediction.json"
            else:
                # Fallback: look in common location
                prediction_file = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "*" / "MQL5" / "Files" / "ML_Data" / "prediction.json"

            # Try to read the file
            if isinstance(prediction_file, Path) and prediction_file.exists():
                with open(prediction_file, 'r') as f:
                    data = json.load(f)

                # Check if multi-symbol format
                if 'symbols' in data and symbol in data['symbols']:
                    return data['symbols'][symbol]
                # Check if single-symbol format and matches
                elif 'symbol' in data and data['symbol'] == symbol:
                    return data
                # Check if direct symbol key (alternative multi-symbol format)
                elif symbol in data:
                    return data[symbol]

            return None

        except Exception as e:
            print(f"Error reading ML prediction: {e}")
            return None

    def get_market_conditions(self, symbol):
        """
        Get current market conditions for the symbol
        Returns: dict with market data or None
        """
        if not MT5_AVAILABLE:
            return None

        try:
            if not mt5.initialize():
                return None

            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                mt5.shutdown()
                return None

            # Get recent bars to analyze trend
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates is None or len(rates) < 50:
                mt5.shutdown()
                return None

            # Analyze trend (simple: compare current price to MA50)
            import numpy as np
            ma50 = np.mean(rates[-50:]['close'])
            current_price = tick.bid

            if current_price > ma50 * 1.002:  # 0.2% above MA
                trend = "BULLISH"
            elif current_price < ma50 * 0.998:  # 0.2% below MA
                trend = "BEARISH"
            else:
                trend = "RANGING"

            # Analyze volatility (ATR-like)
            high_low = rates[-20:]['high'] - rates[-20:]['low']
            avg_range = np.mean(high_low)
            recent_range = high_low[-1]

            if recent_range > avg_range * 1.5:
                volatility = "HIGH"
            elif recent_range < avg_range * 0.7:
                volatility = "LOW"
            else:
                volatility = "NORMAL"

            # Determine session
            now = datetime.now()
            hour = now.hour

            if 8 <= hour < 16:  # London session
                if 13 <= hour < 16:
                    session = "OVERLAP"  # London + NY
                else:
                    session = "LONDON"
            elif 13 <= hour < 20:  # NY session
                session = "NEW_YORK"
            elif 0 <= hour < 8:  # Asian session
                session = "ASIAN"
            else:
                session = "TOKYO"

            mt5.shutdown()

            return {
                'trend': trend,
                'volatility': volatility,
                'session': session,
                'price': current_price,
                'ma50': ma50
            }

        except Exception as e:
            print(f"Error getting market conditions: {e}")
            if mt5.initialize():
                mt5.shutdown()
            return None

    def display_analysis(self, symbol, direction, analysis):
        """Display analysis results in the results panel"""

        approved = analysis['approved']
        ml_signal = analysis['ml_signal']
        probability = analysis['probability']
        confidence = analysis['confidence']
        reasons = analysis['reasons']
        warnings = analysis['warnings']

        # Determine overall recommendation
        if approved:
            recommendation = "✅ GO FOR IT - Good Setup"
            rec_color = "#4CAF50"  # Green
        elif ml_signal == "WAIT":
            recommendation = "⏸ WAIT - Moderate Setup"
            rec_color = "#FFC107"  # Yellow
        else:
            recommendation = "❌ SKIP - Not Recommended"
            rec_color = "#F44336"  # Red

        # Build HTML output
        html = f"""
<div style="padding: 15px; background-color: #1e1e1e; border-radius: 5px;">
    <h2 style="color: {rec_color}; text-align: center; margin-bottom: 20px;">
        {recommendation}
    </h2>

    <div style="background-color: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
        <p style="font-size: 14px; margin: 5px 0;"><strong>Symbol:</strong> {symbol}</p>
        <p style="font-size: 14px; margin: 5px 0;"><strong>Direction:</strong> {direction}</p>
        <p style="font-size: 14px; margin: 5px 0;"><strong>ML Signal:</strong> <span style="color: {'#4CAF50' if ml_signal == 'ENTER' else '#FFC107' if ml_signal == 'WAIT' else '#F44336'};">{ml_signal}</span></p>
        <p style="font-size: 14px; margin: 5px 0;"><strong>Win Probability:</strong> {probability:.1f}%</p>
        <p style="font-size: 14px; margin: 5px 0;"><strong>Model Confidence:</strong> {confidence:.1f}%</p>
    </div>
"""

        # Market Conditions
        if analysis['market_conditions']:
            mc = analysis['market_conditions']
            html += """
    <div style="background-color: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
        <h3 style="color: #64B5F6; margin-top: 0;">📈 Market Conditions:</h3>
"""
            if 'trend' in mc:
                html += f"        <p style="margin: 5px 0;">• <strong>Trend:</strong> {mc['trend']}</p>\n"
            if 'volatility' in mc:
                html += f"        <p style="margin: 5px 0;">• <strong>Volatility:</strong> {mc['volatility']}</p>\n"
            if 'session' in mc:
                html += f"        <p style="margin: 5px 0;">• <strong>Session:</strong> {mc['session']}</p>\n"

            html += "    </div>\n"

        # Reasons (if any)
        if reasons:
            html += """
    <div style="background-color: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
        <h3 style="color: #4CAF50; margin-top: 0;">✅ Positive Factors:</h3>
"""
            for reason in reasons:
                html += f"        <p style="margin: 5px 0;">• {reason}</p>\n"
            html += "    </div>\n"

        # Warnings (if any)
        if warnings:
            html += """
    <div style="background-color: #2a2a2a; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
        <h3 style="color: #F44336; margin-top: 0;">❌ Warning Factors:</h3>
"""
            for warning in warnings:
                html += f"        <p style="margin: 5px 0;">• {warning}</p>\n"
            html += "    </div>\n"

        # Bottom line
        html += f"""
    <div style="background-color: #2a2a2a; padding: 15px; border-radius: 5px; text-align: center;">
        <h3 style="color: {rec_color}; margin-top: 0;">{'✅' if approved else '❌'} Bottom Line:</h3>
        <p style="font-size: 15px;">{'ML approves this trade' if approved else 'Low probability - wait for better setup'}</p>
    </div>

    <p style="text-align: center; color: #888; font-size: 12px; margin-top: 15px;">
        Note: Check spread yourself before executing. This analysis focuses on ML predictions and market conditions.
    </p>
</div>
"""

        self.results_display.setHtml(html)

    def show_error(self, message):
        """Show error message"""
        html = f"""
<div style="padding: 20px; text-align: center;">
    <h3 style="color: #F44336;">❌ Error</h3>
    <p style="color: #aaa;">{message}</p>
</div>
"""
        self.results_display.setHtml(html)

    def set_symbol(self, symbol):
        """Update the current symbol"""
        self.current_symbol = symbol

    def update_data(self):
        """Update widget data - called periodically"""
        pass  # No periodic updates needed for this widget
