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

        # Start with initial ML assessment
        ml_allows_trade = False

        if ml_data:
            analysis['ml_signal'] = ml_data.get('signal', 'UNKNOWN')
            analysis['probability'] = ml_data.get('probability', 0.0) * 100  # Convert to percentage
            analysis['confidence'] = ml_data.get('confidence', 0.0) * 100

            # Check if ML approves (initial gate)
            if analysis['ml_signal'] == 'ENTER':
                ml_allows_trade = True
                analysis['reasons'].append(f"ML model shows high win probability ({analysis['probability']:.1f}%)")
                analysis['reasons'].append(f"Model confidence is good ({analysis['confidence']:.1f}%)")
            elif analysis['ml_signal'] == 'WAIT':
                analysis['warnings'].append(f"ML model shows moderate probability ({analysis['probability']:.1f}%)")
                analysis['warnings'].append("Wait for better setup")
            else:  # SKIP
                analysis['warnings'].append(f"ML model shows low probability ({analysis['probability']:.1f}%)")
                analysis['warnings'].append("Not recommended to enter")
        else:
            analysis['warnings'].append("ML prediction file not found")
            analysis['warnings'].append("Proceeding without ML analysis")

        # Get market conditions
        market_conditions = self.get_market_conditions(symbol)
        analysis['market_conditions'] = market_conditions

        # CRITICAL: Check trend alignment - REJECT if trading against trend
        trend_aligned = False
        if market_conditions and direction != "CHECK":
            trend = market_conditions.get('trend', 'UNKNOWN')
            volatility = market_conditions.get('volatility', 'UNKNOWN')

            if trend != 'UNKNOWN':
                if direction == "BUY" and trend == "BULLISH":
                    trend_aligned = True
                    analysis['reasons'].append("✅ H4 trend is BULLISH (aligned with BUY)")
                elif direction == "SELL" and trend == "BEARISH":
                    trend_aligned = True
                    analysis['reasons'].append("✅ H4 trend is BEARISH (aligned with SELL)")
                elif direction == "BUY" and trend == "BEARISH":
                    trend_aligned = False
                    analysis['warnings'].append("⚠ CRITICAL: H4 trend is BEARISH - trading AGAINST trend (counter-trend BUY)")
                    analysis['warnings'].append("This is a counter-trend trade - HIGH RISK")
                elif direction == "SELL" and trend == "BULLISH":
                    trend_aligned = False
                    analysis['warnings'].append("⚠ CRITICAL: H4 trend is BULLISH - trading AGAINST trend (counter-trend SELL)")
                    analysis['warnings'].append("This is a counter-trend trade - HIGH RISK")
                elif trend == "RANGING":
                    # RANGING markets: INFORM user but don't auto-reject
                    # Let ML decision stand, but warn about ranging conditions
                    trend_aligned = True  # Don't block on ranging (ML decides)
                    analysis['warnings'].append("ℹ️  Market is RANGING on H4 - no clear trend")
                    analysis['warnings'].append("Check multiple timeframes before entering")
                    if volatility == "HIGH":
                        analysis['warnings'].append("⚠ High volatility - choppy conditions")
            else:
                trend_aligned = True  # If we can't determine trend, don't block
        else:
            trend_aligned = True  # If no market data or CHECK mode, don't block on trend

        # FINAL DECISION: Must pass BOTH ML gate AND trend alignment
        analysis['approved'] = ml_allows_trade and trend_aligned

        # Add explanation if rejected due to trend
        if ml_allows_trade and not trend_aligned:
            analysis['warnings'].append("❌ REJECTED: ML approves but direction fights the trend")

        # Analyze volatility and session (additional context)
        if market_conditions:
            volatility = market_conditions.get('volatility', 'UNKNOWN')
            if volatility == 'LOW':
                analysis['reasons'].append("Volatility is low (good for entry)")
            elif volatility == 'HIGH':
                analysis['warnings'].append("Volatility is high (choppy price action)")

            session = market_conditions.get('session', 'UNKNOWN')
            if session in ['LONDON', 'NEW_YORK', 'OVERLAP']:
                analysis['reasons'].append(f"{session.title()} session (high liquidity)")
            elif session == 'ASIAN':
                analysis['warnings'].append("Asian session (lower liquidity)")

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
        Get current market conditions for the symbol with MULTI-TIMEFRAME analysis
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

            import numpy as np
            current_price = tick.bid

            # MULTI-TIMEFRAME TREND ANALYSIS
            timeframes = {
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }

            trends = {}
            for tf_name, tf_value in timeframes.items():
                rates = mt5.copy_rates_from_pos(symbol, tf_value, 0, 100)
                if rates is not None and len(rates) >= 50:
                    ma50 = np.mean(rates[-50:]['close'])

                    if current_price > ma50 * 1.005:  # 0.5% above MA
                        trends[tf_name] = "BULLISH"
                    elif current_price < ma50 * 0.995:  # 0.5% below MA
                        trends[tf_name] = "BEARISH"
                    else:
                        trends[tf_name] = "RANGING"

            # Primary trend (use H4 as main timeframe for decision)
            trend = trends.get('H4', 'UNKNOWN')

            # Analyze volatility (using H1)
            rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates_h1 is not None and len(rates_h1) >= 20:
                high_low = rates_h1[-20:]['high'] - rates_h1[-20:]['low']
                avg_range = np.mean(high_low)
                recent_range = high_low[-1]

                if recent_range > avg_range * 1.5:
                    volatility = "HIGH"
                elif recent_range < avg_range * 0.7:
                    volatility = "LOW"
                else:
                    volatility = "NORMAL"
            else:
                volatility = "UNKNOWN"

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
                'trend': trend,  # Primary trend (H4)
                'trends': trends,  # All timeframes
                'volatility': volatility,
                'session': session,
                'price': current_price
            }

        except Exception as e:
            print(f"Error getting market conditions: {e}")
            if mt5.initialize():
                mt5.shutdown()
            return None

    def display_analysis(self, symbol, direction, analysis):
        """Display analysis results in the results panel - PROFESSIONAL GRADE"""

        approved = analysis['approved']
        ml_signal = analysis['ml_signal']
        probability = analysis['probability']
        confidence = analysis['confidence']
        reasons = analysis['reasons']
        warnings = analysis['warnings']

        # Determine overall recommendation with traffic light colors
        if approved:
            decision = "GO FOR IT"
            decision_icon = "✅"
            bg_color = "#1B5E20"  # Dark green background
            border_color = "#4CAF50"  # Bright green border
            text_color = "#FFFFFF"  # White text
        elif ml_signal == "WAIT":
            decision = "WAIT"
            decision_icon = "⚠"
            bg_color = "#F57F17"  # Dark yellow/orange background
            border_color = "#FFC107"  # Bright yellow border
            text_color = "#FFFFFF"  # White text
        else:
            decision = "SKIP THIS"
            decision_icon = "❌"
            bg_color = "#B71C1C"  # Dark red background
            border_color = "#F44336"  # Bright red border
            text_color = "#FFFFFF"  # White text

        # Build professional HTML output with high contrast
        html = f"""
<div style="padding: 20px; background-color: #0a0a0a; font-family: 'Segoe UI', Arial, sans-serif;">

    <!-- MAIN DECISION BOX (Traffic Light Style) -->
    <div style="background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
                border: 4px solid {border_color};
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin-bottom: 25px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.4);">
        <div style="font-size: 72px; margin-bottom: 15px;">{decision_icon}</div>
        <h1 style="color: {text_color};
                   font-size: 42px;
                   font-weight: bold;
                   margin: 0 0 10px 0;
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">{decision}</h1>
        <p style="color: {text_color};
                  font-size: 24px;
                  margin: 0;
                  opacity: 0.95;">{symbol} {direction}</p>
    </div>

    <!-- PROBABILITY DISPLAY -->
    <div style="background-color: #1a1a1a;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #333;">
                    <span style="color: #aaa; font-size: 16px;">ML Signal:</span>
                </td>
                <td style="padding: 12px 0; border-bottom: 1px solid #333; text-align: right;">
                    <span style="color: {border_color}; font-size: 20px; font-weight: bold;">{ml_signal}</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 0; border-bottom: 1px solid #333;">
                    <span style="color: #aaa; font-size: 16px;">Win Probability:</span>
                </td>
                <td style="padding: 12px 0; border-bottom: 1px solid #333; text-align: right;">
                    <span style="color: #FFFFFF; font-size: 24px; font-weight: bold;">{probability:.1f}%</span>
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 0;">
                    <span style="color: #aaa; font-size: 16px;">Model Confidence:</span>
                </td>
                <td style="padding: 12px 0; text-align: right;">
                    <span style="color: #FFFFFF; font-size: 20px; font-weight: bold;">{confidence:.1f}%</span>
                </td>
            </tr>
        </table>
    </div>

    <!-- MARKET CONDITIONS -->
"""

        if analysis['market_conditions']:
            mc = analysis['market_conditions']
            html += """
    <div style="background-color: #1a1a1a;
                border-left: 4px solid #2196F3;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;">
        <h3 style="color: #2196F3;
                   font-size: 20px;
                   margin: 0 0 15px 0;
                   font-weight: bold;">📈 MARKET CONDITIONS</h3>
"""

            # Multi-timeframe trend display
            if 'trends' in mc:
                html += "        <p style='color: #FFD700; font-size: 16px; margin: 8px 0 12px 0;'><strong>📊 MULTI-TIMEFRAME TREND ANALYSIS:</strong></p>\n"
                trends = mc['trends']
                for tf in ['M15', 'H1', 'H4', 'D1']:
                    if tf in trends:
                        trend_value = trends[tf]
                        # Color code the trends
                        if trend_value == "BULLISH":
                            color = "#4CAF50"  # Green
                            icon = "📈"
                        elif trend_value == "BEARISH":
                            color = "#F44336"  # Red
                            icon = "📉"
                        else:  # RANGING
                            color = "#FFC107"  # Yellow
                            icon = "↔️"

                        # Highlight H4 (primary timeframe)
                        if tf == "H4":
                            html += f"        <p style='color: {color}; font-size: 17px; margin: 6px 0 6px 20px; font-weight: bold;'>{icon} <strong>{tf}: {trend_value}</strong> ⭐ (PRIMARY)</p>\n"
                        else:
                            html += f"        <p style='color: {color}; font-size: 15px; margin: 4px 0 4px 20px;'>{icon} {tf}: {trend_value}</p>\n"
                html += "        <hr style='border: none; border-top: 1px solid #333; margin: 12px 0;'>\n"

            if 'volatility' in mc:
                html += f"        <p style='color: #FFFFFF; font-size: 16px; margin: 8px 0;'>▸ <strong>Volatility (H1):</strong> {mc['volatility']}</p>\n"
            if 'session' in mc:
                html += f"        <p style='color: #FFFFFF; font-size: 16px; margin: 8px 0;'>▸ <strong>Session:</strong> {mc['session']}</p>\n"
            html += "    </div>\n"

        # POSITIVE FACTORS
        if reasons:
            html += """
    <div style="background-color: #1a1a1a;
                border-left: 4px solid #4CAF50;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;">
        <h3 style="color: #4CAF50;
                   font-size: 20px;
                   margin: 0 0 15px 0;
                   font-weight: bold;">✅ POSITIVE FACTORS</h3>
"""
            for reason in reasons:
                html += f"        <p style='color: #FFFFFF; font-size: 16px; margin: 8px 0; line-height: 1.5;'>▸ {reason}</p>\n"
            html += "    </div>\n"

        # WARNING FACTORS
        if warnings:
            html += """
    <div style="background-color: #1a1a1a;
                border-left: 4px solid #F44336;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;">
        <h3 style="color: #F44336;
                   font-size: 20px;
                   margin: 0 0 15px 0;
                   font-weight: bold;">❌ WARNING FACTORS</h3>
"""
            for warning in warnings:
                html += f"        <p style='color: #FFFFFF; font-size: 16px; margin: 8px 0; line-height: 1.5;'>▸ {warning}</p>\n"
            html += "    </div>\n"

        # FINAL VERDICT BOX
        verdict_text = "ML APPROVES THIS TRADE" if approved else "LOW PROBABILITY - WAIT FOR BETTER SETUP"
        html += f"""
    <div style="background-color: #1a1a1a;
                border: 3px solid {border_color};
                border-radius: 8px;
                padding: 25px;
                text-align: center;">
        <h2 style="color: {border_color};
                   font-size: 28px;
                   margin: 0 0 10px 0;
                   font-weight: bold;">{decision_icon} VERDICT</h2>
        <p style="color: #FFFFFF;
                  font-size: 20px;
                  margin: 0;
                  font-weight: 500;">{verdict_text}</p>
    </div>

    <!-- FOOTER NOTE -->
    <p style="text-align: center;
              color: #666;
              font-size: 13px;
              margin-top: 20px;
              font-style: italic;">
        Note: Check spread yourself before executing
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
