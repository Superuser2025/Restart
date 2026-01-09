"""
Manual Trade Validator Widget
Validates user's manual trade ideas against ML predictions and market conditions
"""

import json
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QTextEdit, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# Import Wyckoff analyzer
try:
    from analysis.wyckoff_analyzer import WyckoffAnalyzer, WyckoffPhase
    WYCKOFF_AVAILABLE = True
except ImportError:
    WYCKOFF_AVAILABLE = False
    print("Warning: Wyckoff analyzer not available")


class TradeValidatorWidget(QWidget):
    """Widget for validating manual trade ideas"""

    # Signals
    validation_completed = pyqtSignal(str, bool)  # symbol, approved

    def __init__(self):
        super().__init__()
        self.current_symbol = "EURUSD"
        self.wyckoff_enabled = False  # Toggle for Wyckoff analysis

        # Initialize Wyckoff analyzer if available
        if WYCKOFF_AVAILABLE:
            self.wyckoff_analyzer = WyckoffAnalyzer()
        else:
            self.wyckoff_analyzer = None

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

        # === WYCKOFF TOGGLE ===
        if WYCKOFF_AVAILABLE:
            wyckoff_frame = QFrame()
            wyckoff_layout = QHBoxLayout(wyckoff_frame)
            wyckoff_layout.setContentsMargins(5, 5, 5, 5)

            self.wyckoff_checkbox = QCheckBox("🔵 Enable Wyckoff LPS/LPSY Analysis")
            self.wyckoff_checkbox.setChecked(False)
            self.wyckoff_checkbox.stateChanged.connect(self.toggle_wyckoff)
            wyckoff_font = QFont()
            wyckoff_font.setPointSize(10)
            wyckoff_font.setBold(True)
            self.wyckoff_checkbox.setFont(wyckoff_font)
            self.wyckoff_checkbox.setStyleSheet("""
                QCheckBox {
                    color: #64B5F6;
                    padding: 5px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
            wyckoff_layout.addWidget(self.wyckoff_checkbox)

            # Info label
            wyckoff_info = QLabel("(Detects accumulation/distribution phases, LPS/LPSY entry points)")
            wyckoff_info.setStyleSheet("color: #888; font-size: 9pt;")
            wyckoff_layout.addWidget(wyckoff_info)

            wyckoff_layout.addStretch()
            layout.addWidget(wyckoff_frame)

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

        # Set dark background to match the app theme
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
        """)

        layout.addWidget(self.results_display)

        # Initial message
        self.show_welcome_message()

    def show_welcome_message(self):
        """Show welcome message"""
        message = """
<div style="text-align: center; padding: 20px; background-color: #1e1e1e; color: #fff;">
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

    def toggle_wyckoff(self, state):
        """Toggle Wyckoff analysis on/off"""
        self.wyckoff_enabled = (state == Qt.CheckState.Checked.value)
        status = "ENABLED" if self.wyckoff_enabled else "DISABLED"
        print(f"Wyckoff LPS/LPSY analysis {status}")

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

        # WYCKOFF ANALYSIS (if enabled)
        wyckoff_data = None
        if self.wyckoff_enabled and self.wyckoff_analyzer and MT5_AVAILABLE:
            # Analyze multiple timeframes
            wyckoff_multi_tf = {}

            timeframes = {
                'H4': mt5.TIMEFRAME_H4,
                'H1': mt5.TIMEFRAME_H1,
                'M15': mt5.TIMEFRAME_M15
            }

            for tf_name, tf_value in timeframes.items():
                wyckoff_result = self.wyckoff_analyzer.analyze_symbol(symbol, tf_value, bars=100)
                if wyckoff_result:
                    wyckoff_multi_tf[tf_name] = wyckoff_result

            if wyckoff_multi_tf:
                wyckoff_data = wyckoff_multi_tf
                analysis['wyckoff'] = wyckoff_data

                # Add Wyckoff insights to reasons/warnings based on H4 (primary timeframe)
                if 'H4' in wyckoff_multi_tf:
                    h4_wyckoff = wyckoff_multi_tf['H4']
                    phase = h4_wyckoff['current_phase']
                    signals = h4_wyckoff['signals']

                    # Add phase information
                    analysis['reasons'].append(f"🔵 Wyckoff Phase: {phase.value}")

                    # Add LPS/LPSY signals
                    if signals['action'] != 'WAIT':
                        if signals['direction'] == direction or direction == "CHECK":
                            analysis['reasons'].append(f"🔵 Wyckoff: {signals['action']} signal detected ({signals['confidence']})")
                            for reason in signals['reasons'][:3]:  # Top 3 reasons
                                analysis['reasons'].append(f"  • {reason}")
                        else:
                            analysis['warnings'].append(f"⚠ Wyckoff suggests {signals['action']} but you want {direction}")

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
                    # RANGING markets: REJECT all trades - no clear direction
                    trend_aligned = False
                    analysis['warnings'].append("⚠ H4 is RANGING - no clear trend direction")

                    # Add specific guidance based on range position (H4)
                    range_info = market_conditions.get('range_info')
                    if range_info:
                        zone = range_info['zone']
                        position_pct = range_info['position_pct']

                        # Provide context-specific advice
                        if zone == "UPPER":
                            analysis['warnings'].append(f"💡 H4: Price is at {position_pct:.1f}% of range (UPPER zone - near resistance)")
                            if direction == "BUY":
                                analysis['warnings'].append("⚠ BUY at range top = HIGH RISK (likely to reverse down)")
                            elif direction == "SELL":
                                analysis['warnings'].append("💭 SELL from range top COULD work IF it breaks resistance")
                                analysis['warnings'].append("⚠ But wait for confirmation - premature entry risky")
                        elif zone == "LOWER":
                            analysis['warnings'].append(f"💡 H4: Price is at {position_pct:.1f}% of range (LOWER zone - near support)")
                            if direction == "SELL":
                                analysis['warnings'].append("⚠ SELL at range bottom = HIGH RISK (likely to reverse up)")
                            elif direction == "BUY":
                                analysis['warnings'].append("💭 BUY from range bottom COULD work IF it holds support")
                                analysis['warnings'].append("⚠ But wait for confirmation - premature entry risky")
                        else:
                            analysis['warnings'].append(f"💡 H4: Price is at {position_pct:.1f}% of range (MIDDLE zone)")
                            analysis['warnings'].append("⚠ No edge in the middle - wait for price to reach boundaries")
                    else:
                        analysis['warnings'].append("Cannot recommend BUY or SELL in ranging market")
                        analysis['warnings'].append("Wait for breakout or trend to establish")

                    # Check for SCALPING opportunities on lower timeframes
                    ranging_tfs = market_conditions.get('ranging_timeframes', {})
                    if 'M15' in ranging_tfs or 'H1' in ranging_tfs:
                        analysis['warnings'].append("💡 SCALPING OPPORTUNITIES detected on lower timeframes - see below")

                    if volatility == "HIGH":
                        analysis['warnings'].append("High volatility makes this even more uncertain")
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

            # MULTI-TIMEFRAME RANGING ANALYSIS - Calculate ranges for M15, H1, and H4
            # This helps with scalping (M15), intraday (H1), and position trading (H4)
            ranging_timeframes = {}

            scalping_tfs = {
                'M15': {'mt5_tf': mt5.TIMEFRAME_M15, 'bars': 50, 'bar_minutes': 15},
                'H1': {'mt5_tf': mt5.TIMEFRAME_H1, 'bars': 50, 'bar_minutes': 60},
                'H4': {'mt5_tf': mt5.TIMEFRAME_H4, 'bars': 50, 'bar_minutes': 240}
            }

            for tf_name, tf_config in scalping_tfs.items():
                # Only analyze ranges for timeframes that are actually RANGING
                if trends.get(tf_name) == "RANGING":
                    rates = mt5.copy_rates_from_pos(symbol, tf_config['mt5_tf'], 0, 100)
                    if rates is not None and len(rates) >= tf_config['bars']:
                        # Find recent swing high/low
                        range_high = np.max(rates[-tf_config['bars']:]['high'])
                        range_low = np.min(rates[-tf_config['bars']:]['low'])
                        range_size = range_high - range_low

                        # Calculate position within range (0-100%)
                        if range_size > 0:
                            position_pct = ((current_price - range_low) / range_size) * 100

                            # Determine zone
                            if position_pct >= 70:
                                zone = "UPPER"
                                zone_desc = "near resistance"
                            elif position_pct <= 30:
                                zone = "LOWER"
                                zone_desc = "near support"
                            else:
                                zone = "MIDDLE"
                                zone_desc = "in the middle"

                            # Count boundary touches (within 2% of boundaries)
                            upper_boundary = range_high * 0.98
                            lower_boundary = range_low * 1.02

                            upper_touches = np.sum(rates[-tf_config['bars']:]['high'] >= upper_boundary)
                            lower_touches = np.sum(rates[-tf_config['bars']:]['low'] <= lower_boundary)

                            # Calculate how long ranging (consecutive ranging bars)
                            ma50 = np.mean(rates[-tf_config['bars']:]['close'])
                            ranging_bars = 0
                            for i in range(len(rates)-1, -1, -1):
                                close_price = rates[i]['close']
                                if ma50 * 0.995 <= close_price <= ma50 * 1.005:
                                    ranging_bars += 1
                                else:
                                    break

                            ranging_timeframes[tf_name] = {
                                'high': range_high,
                                'low': range_low,
                                'size': range_size,
                                'size_pips': range_size * 10000,  # Approximate pips for FX
                                'position_pct': position_pct,
                                'zone': zone,
                                'zone_desc': zone_desc,
                                'upper_touches': upper_touches,
                                'lower_touches': lower_touches,
                                'ranging_bars': ranging_bars,
                                'ranging_duration': ranging_bars * tf_config['bar_minutes']  # Duration in minutes
                            }

            # Keep legacy range_info for H4 (for backward compatibility)
            range_info = ranging_timeframes.get('H4', None)

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
                'price': current_price,
                'range_info': range_info,  # H4 RANGING market details (backward compatibility)
                'ranging_timeframes': ranging_timeframes  # ALL ranging timeframes (M15, H1, H4)
            }

        except Exception as e:
            print(f"Error getting market conditions: {e}")
            if mt5.initialize():
                mt5.shutdown()
            return None

    def display_analysis(self, symbol, direction, analysis):
        """Display analysis results - CLEAN PROFESSIONAL DESIGN"""

        approved = analysis['approved']
        ml_signal = analysis['ml_signal']
        probability = analysis['probability']
        confidence = analysis['confidence']
        reasons = analysis['reasons']
        warnings = analysis['warnings']

        # Determine overall recommendation
        if approved:
            decision = "GO FOR IT"
            decision_color = "#4CAF50"  # Green
            decision_icon = "✅"
        elif ml_signal == "WAIT":
            decision = "WAIT"
            decision_color = "#FFC107"  # Yellow
            decision_icon = "⚠"
        else:
            decision = "SKIP THIS"
            decision_color = "#F44336"  # Red
            decision_icon = "❌"

        # Build CLEAN HTML output - NO ZEBRA STRIPES
        html = f"""
<div style="padding: 20px; background-color: #1e1e1e; font-family: 'Segoe UI', Arial, sans-serif; color: #fff;">

    <!-- DECISION -->
    <div style="padding: 30px 20px; text-align: center; margin-bottom: 25px; border-left: 8px solid {decision_color};">
        <div style="font-size: 64px; margin-bottom: 15px;">{decision_icon}</div>
        <h1 style="color: {decision_color}; font-size: 42px; margin: 0 0 10px 0; font-weight: bold;">{decision}</h1>
        <p style="color: #ccc; font-size: 22px; margin: 0;">{symbol} {direction}</p>
    </div>

    <hr style="border: none; border-top: 1px solid #444; margin: 25px 0;">

    <!-- ML STATS -->
    <h3 style="color: #64B5F6; margin: 0 0 20px 0; font-size: 20px; font-weight: bold;">📊 ML PREDICTION</h3>
    <table style="width: 100%; color: #fff; margin-bottom: 30px;">
        <tr>
            <td style="padding: 12px 0; color: #bbb; font-size: 16px;">Signal:</td>
            <td style="padding: 12px 0; text-align: right; color: {decision_color}; font-size: 24px; font-weight: bold;">{ml_signal}</td>
        </tr>
        <tr>
            <td style="padding: 12px 0; color: #bbb; font-size: 16px;">Win Probability:</td>
            <td style="padding: 12px 0; text-align: right; font-size: 28px; font-weight: bold; color: #fff;">{probability:.1f}%</td>
        </tr>
        <tr>
            <td style="padding: 12px 0; color: #bbb; font-size: 16px;">Confidence:</td>
            <td style="padding: 12px 0; text-align: right; font-size: 20px; font-weight: bold; color: #fff;">{confidence:.1f}%</td>
        </tr>
    </table>

    <hr style="border: none; border-top: 1px solid #444; margin: 25px 0;">
"""

        # MULTI-TIMEFRAME TRENDS
        if analysis['market_conditions'] and 'trends' in analysis['market_conditions']:
            mc = analysis['market_conditions']
            trends = mc['trends']

            html += """
    <h3 style="color: #FFD700; margin: 0 0 20px 0; font-size: 20px; font-weight: bold;">📈 MULTI-TIMEFRAME TRENDS</h3>
"""
            for tf in ['M15', 'H1', 'H4', 'D1']:
                if tf in trends:
                    trend_val = trends[tf]
                    if trend_val == "BULLISH":
                        trend_color = "#4CAF50"
                        trend_icon = "📈"
                    elif trend_val == "BEARISH":
                        trend_color = "#F44336"
                        trend_icon = "📉"
                    else:
                        trend_color = "#FFC107"
                        trend_icon = "↔️"

                    # Mark H4 as primary
                    if tf == "H4":
                        html += f"    <p style='margin: 12px 0; font-size: 18px; color: {trend_color}; font-weight: bold; padding-left: 20px; border-left: 5px solid {trend_color};'>{trend_icon} {tf}: {trend_val} ⭐ PRIMARY</p>\n"
                    else:
                        html += f"    <p style='margin: 10px 0; font-size: 16px; color: {trend_color}; padding-left: 20px;'>{trend_icon} {tf}: {trend_val}</p>\n"

            html += "\n    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>\n"

        # MULTI-TIMEFRAME RANGING MARKET DETAILS
        if analysis['market_conditions'] and analysis['market_conditions'].get('ranging_timeframes'):
            ranging_tfs = analysis['market_conditions']['ranging_timeframes']

            if ranging_tfs:  # Only show if there are ranging timeframes
                html += """
    <h3 style="color: #FF9800; margin: 0 0 20px 0; font-size: 20px; font-weight: bold;">↔️ RANGING MARKET ANALYSIS (MULTI-TIMEFRAME)</h3>
"""
                # Show ranging timeframes in order: M15, H1, H4
                for tf_name in ['M15', 'H1', 'H4']:
                    if tf_name in ranging_tfs:
                        range_info = ranging_tfs[tf_name]

                        # Determine color based on zone
                        if range_info['zone'] == "UPPER":
                            zone_color = "#F44336"  # Red
                            zone_icon = "🔴"
                        elif range_info['zone'] == "LOWER":
                            zone_color = "#4CAF50"  # Green
                            zone_icon = "🟢"
                        else:
                            zone_color = "#FFC107"  # Yellow
                            zone_icon = "🟡"

                        # Timeframe-specific styling
                        if tf_name == "H4":
                            border_color = "#FF9800"
                            tf_label = "H4 (Position Trading)"
                        elif tf_name == "H1":
                            border_color = "#2196F3"
                            tf_label = "H1 (Intraday/Swing)"
                        else:  # M15
                            border_color = "#9C27B0"
                            tf_label = "M15 (Scalping)"

                        html += f"""
    <div style="padding: 20px; border: 2px solid {border_color}; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="color: {border_color}; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">📊 {tf_label}</h4>

        <!-- Range Boundaries -->
        <table style="width: 100%; color: #fff; margin-bottom: 20px;">
            <tr>
                <td style="padding: 8px 0; color: #bbb; font-size: 14px;">Range High:</td>
                <td style="padding: 8px 0; text-align: right; font-size: 16px; font-weight: bold; color: #F44336;">{range_info['high']:.5f}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #bbb; font-size: 14px;">Current Price:</td>
                <td style="padding: 8px 0; text-align: right; font-size: 18px; font-weight: bold; color: {zone_color};">{analysis['market_conditions']['price']:.5f}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #bbb; font-size: 14px;">Range Low:</td>
                <td style="padding: 8px 0; text-align: right; font-size: 16px; font-weight: bold; color: #4CAF50;">{range_info['low']:.5f}</td>
            </tr>
        </table>

        <!-- Position Indicator -->
        <div style="margin: 20px 0;">
            <p style="color: #ccc; font-size: 14px; margin: 0 0 8px 0;">Price Position:</p>
            <div style="background-color: #333; height: 35px; border-radius: 5px; position: relative; overflow: hidden;">
                <!-- Range bar background -->
                <div style="position: absolute; left: 0; top: 0; width: 30%; height: 100%; background-color: rgba(76, 175, 80, 0.3);"></div>
                <div style="position: absolute; left: 70%; top: 0; width: 30%; height: 100%; background-color: rgba(244, 67, 54, 0.3);"></div>

                <!-- Position marker -->
                <div style="position: absolute; left: {range_info['position_pct']}%; top: 50%; transform: translateX(-50%) translateY(-50%); font-size: 20px;">
                    {zone_icon}
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 6px;">
                <span style="color: #4CAF50; font-size: 12px;">🟢 Support</span>
                <span style="color: {zone_color}; font-size: 14px; font-weight: bold;">{range_info['position_pct']:.1f}% ({range_info['zone']})</span>
                <span style="color: #F44336; font-size: 12px;">Resistance 🔴</span>
            </div>
        </div>

        <!-- Range Statistics -->
        <div style="margin-top: 15px; padding-top: 12px; border-top: 1px solid #555;">
            <p style="margin: 6px 0; font-size: 14px; color: #ddd;">▸ <strong style="color: #fff;">Range Size:</strong> {range_info['size_pips']:.1f} pips</p>
            <p style="margin: 6px 0; font-size: 14px; color: #ddd;">▸ <strong style="color: #fff;">Upper Tests:</strong> {range_info['upper_touches']} times</p>
            <p style="margin: 6px 0; font-size: 14px; color: #ddd;">▸ <strong style="color: #fff;">Lower Tests:</strong> {range_info['lower_touches']} times</p>
            <p style="margin: 6px 0; font-size: 14px; color: #ddd;">▸ <strong style="color: #fff;">Duration:</strong> {range_info['ranging_bars']} bars (~{range_info['ranging_duration']} min)</p>
        </div>

        <!-- Trading Strategy -->
        <div style="margin-top: 15px; padding: 12px; background-color: rgba(255, 152, 0, 0.1); border-left: 4px solid {border_color}; border-radius: 4px;">
"""

                        # Timeframe-specific advice
                        if tf_name == "M15":
                            html += f"""
            <p style="margin: 0; font-size: 13px; color: #FFB74D; font-weight: bold;">⚡ SCALPING STRATEGY (M15):</p>
            <p style="margin: 6px 0 0 0; font-size: 12px; color: #ddd; line-height: 1.5;">
"""
                            if range_info['zone'] == "UPPER":
                                html += """Quick SELL scalp possible IF rejection candle forms. Target: middle of range. SL: above range high."""
                            elif range_info['zone'] == "LOWER":
                                html += """Quick BUY scalp possible IF bounce candle forms. Target: middle of range. SL: below range low."""
                            else:
                                html += """NO scalp - price in dead zone. Wait for boundaries (30% or 70% level) for best risk/reward."""
                            html += """
            </p>
"""
                        elif tf_name == "H1":
                            html += f"""
            <p style="margin: 0; font-size: 13px; color: #FFB74D; font-weight: bold;">📈 INTRADAY STRATEGY (H1):</p>
            <p style="margin: 6px 0 0 0; font-size: 12px; color: #ddd; line-height: 1.5;">
"""
                            if range_info['zone'] == "UPPER":
                                html += """SELL opportunity at resistance. Wait for reversal confirmation. TP: range low. SL: 10-20 pips above high."""
                            elif range_info['zone'] == "LOWER":
                                html += """BUY opportunity at support. Wait for reversal confirmation. TP: range high. SL: 10-20 pips below low."""
                            else:
                                html += """No clear edge in middle. Trade boundaries only or wait for breakout setup."""
                            html += """
            </p>
"""
                        else:  # H4
                            html += f"""
            <p style="margin: 0; font-size: 13px; color: #FFB74D; font-weight: bold;">💡 POSITION STRATEGY (H4):</p>
            <p style="margin: 6px 0 0 0; font-size: 12px; color: #ddd; line-height: 1.5;">
"""
                            if range_info['zone'] == "UPPER":
                                html += """Near resistance - consider SELL for swing trade. Best entry: rejection + lower timeframe confirmation."""
                            elif range_info['zone'] == "LOWER":
                                html += """Near support - consider BUY for swing trade. Best entry: bounce + lower timeframe confirmation."""
                            else:
                                html += """Middle of range - LOW probability setup. Wait for boundaries or trend breakout."""
                            html += """
            </p>
"""

                        html += """
        </div>
    </div>
"""

                html += """
    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>
"""

        # SESSION & VOLATILITY
        if analysis['market_conditions']:
            mc = analysis['market_conditions']
            html += """
    <h3 style="color: #9C27B0; margin: 0 0 20px 0; font-size: 20px; font-weight: bold;">⏰ MARKET INFO</h3>
"""
            if 'session' in mc:
                html += f"    <p style='margin: 10px 0; font-size: 17px; color: #ddd;'>▸ <strong style='color: #fff;'>Session:</strong> {mc['session']}</p>\n"
            if 'volatility' in mc:
                html += f"    <p style='margin: 10px 0; font-size: 17px; color: #ddd;'>▸ <strong style='color: #fff;'>Volatility (H1):</strong> {mc['volatility']}</p>\n"
            html += "\n    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>\n"

        # WYCKOFF LPS/LPSY ANALYSIS
        if 'wyckoff' in analysis and analysis['wyckoff']:
            wyckoff_data = analysis['wyckoff']

            html += """
    <h3 style="color: #00BFFF; margin: 0 0 20px 0; font-size: 20px; font-weight: bold;">🔵 WYCKOFF LPS/LPSY ANALYSIS</h3>
"""

            # Display each timeframe's Wyckoff analysis
            for tf_name in ['H4', 'H1', 'M15']:
                if tf_name not in wyckoff_data:
                    continue

                tf_data = wyckoff_data[tf_name]
                phase = tf_data['current_phase']
                lps_lpsy = tf_data.get('lps_lpsy')
                signals = tf_data['signals']
                volume_analysis = tf_data['volume_analysis']

                # Timeframe colors
                if tf_name == 'H4':
                    tf_color = "#FF9800"
                elif tf_name == 'H1':
                    tf_color = "#2196F3"
                else:  # M15
                    tf_color = "#9C27B0"

                # Phase colors
                phase_colors = {
                    'ACCUMULATION': '#00FF00',
                    'MARKUP': '#4CAF50',
                    'DISTRIBUTION': '#FF0000',
                    'MARKDOWN': '#F44336',
                    'UNKNOWN': '#888888'
                }
                phase_color = phase_colors.get(phase.value, '#888888')

                html += f"""
    <div style="padding: 20px; border: 2px solid {tf_color}; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="color: {tf_color}; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">📊 {tf_name} Timeframe</h4>

        <!-- Wyckoff Phase -->
        <div style="padding: 15px; background-color: rgba(0, 191, 255, 0.1); border-left: 4px solid {phase_color}; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 15px; color: #ddd;">
                <strong style="color: {phase_color};">Phase:</strong> {phase.value}
            </p>
        </div>
"""

                # Show LPS/LPSY if detected
                if lps_lpsy:
                    lps_type = lps_lpsy['type']
                    lps_color = '#00FF00' if lps_type == 'LPS' else '#FF0000'
                    lps_icon = '🟢' if lps_type == 'LPS' else '🔴'

                    confirmation = "CONFIRMED ✅" if lps_lpsy['confirmed'] else "PENDING ⏳"
                    strength = lps_lpsy['strength']

                    html += f"""
        <!-- LPS/LPSY Detection -->
        <div style="padding: 15px; background-color: rgba(0, 255, 0, 0.05); border: 2px solid {lps_color}; border-radius: 6px; margin-bottom: 15px;">
            <h5 style="color: {lps_color}; margin: 0 0 10px 0; font-size: 16px;">{lps_icon} {lps_type} Detected ({strength})</h5>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Status: {confirmation}</p>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Entry: {lps_lpsy['entry_trigger']:.5f}</p>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Stop Loss: {lps_lpsy['stop_loss']:.5f}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #aaa; font-style: italic;">{lps_lpsy['description']}</p>
        </div>
"""

                # Show signals
                if signals['action'] != 'WAIT':
                    signal_color = '#00FF00' if signals['action'] == 'BUY' else '#FF0000'

                    html += f"""
        <!-- Wyckoff Signals -->
        <div style="padding: 12px; background-color: rgba(255, 255, 255, 0.03); border-left: 4px solid {signal_color}; margin-bottom: 15px;">
            <p style="margin: 0 0 8px 0; font-size: 15px; color: {signal_color}; font-weight: bold;">
                Signal: {signals['action']} ({signals['confidence']})
            </p>
"""
                    for reason in signals['reasons'][:3]:
                        html += f"            <p style='margin: 4px 0 4px 10px; font-size: 13px; color: #ddd;'>• {reason}</p>\n"

                    html += """
        </div>
"""

                # Volume analysis
                if volume_analysis:
                    html += f"""
        <!-- Volume Analysis -->
        <div style="padding: 10px; background-color: rgba(0, 0, 0, 0.2); border-radius: 4px;">
            <p style="margin: 0 0 6px 0; font-size: 14px; color: #FFD700; font-weight: bold;">Volume Analysis:</p>
            <p style="margin: 4px 0; font-size: 13px; color: #ddd;">▸ {volume_analysis.get('effort_result', 'N/A')}</p>
            <p style="margin: 4px 0; font-size: 13px; color: #ddd;">▸ {volume_analysis.get('divergence', 'N/A')}</p>
        </div>
"""

                html += """
    </div>
"""

            html += """
    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>
"""

        # POSITIVE FACTORS
        if reasons:
            html += """
    <h3 style="color: #4CAF50; margin: 0 0 15px 0; font-size: 20px; font-weight: bold; border-left: 5px solid #4CAF50; padding-left: 15px;">✅ POSITIVE FACTORS</h3>
"""
            for reason in reasons:
                html += f"    <p style='margin: 8px 0 8px 20px; font-size: 15px; line-height: 1.6; color: #ddd;'>• {reason}</p>\n"
            html += "\n    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>\n"

        # WARNING FACTORS
        if warnings:
            html += """
    <h3 style="color: #F44336; margin: 0 0 15px 0; font-size: 20px; font-weight: bold; border-left: 5px solid #F44336; padding-left: 15px;">❌ WARNING FACTORS</h3>
"""
            for warning in warnings:
                html += f"    <p style='margin: 8px 0 8px 20px; font-size: 15px; line-height: 1.6; color: #ddd;'>• {warning}</p>\n"
            html += "\n    <hr style='border: none; border-top: 1px solid #444; margin: 25px 0;'>\n"

        # VERDICT
        verdict_text = "ML APPROVES THIS TRADE" if approved else "LOW PROBABILITY - WAIT FOR BETTER SETUP"
        html += f"""
    <div style="padding: 25px 20px; text-align: center; border: 3px solid {decision_color}; border-radius: 8px;">
        <h3 style="color: {decision_color}; margin: 0 0 10px 0; font-size: 24px; font-weight: bold;">{decision_icon} VERDICT</h3>
        <p style="color: #fff; font-size: 18px; margin: 0; font-weight: 500;">{verdict_text}</p>
    </div>

    <p style="text-align: center; color: #777; font-size: 13px; margin-top: 20px; font-style: italic;">
        Note: Check spread yourself before executing
    </p>
</div>
"""

        self.results_display.setHtml(html)

    def show_error(self, message):
        """Show error message"""
        html = f"""
<div style="padding: 20px; text-align: center; background-color: #1e1e1e; color: #fff;">
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
