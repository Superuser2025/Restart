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
from core.verbose_mode_manager import vprint
from core.symbol_manager import symbol_manager

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
    from core.verbose_mode_manager import vprint
    vprint("Warning: Wyckoff analyzer not available")


class TradeValidatorWidget(QWidget):
    """Widget for validating manual trade ideas"""

    # Signals
    validation_completed = pyqtSignal(str, bool)  # symbol, approved
    wyckoff_analysis_ready = pyqtSignal(str, dict)  # symbol, wyckoff_data

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
        vprint(f"Wyckoff LPS/LPSY analysis {status}")

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

        # VALIDATE SYMBOL EXISTS
        symbol_specs = symbol_manager.get_symbol_specs(symbol)
        if not symbol_specs:
            # Symbol doesn't exist - show helpful error with suggestions
            self.show_invalid_symbol_error(symbol)
            return

        # Get ML analysis
        analysis = self.analyze_trade(symbol, direction)

        # Display results
        self.display_analysis(symbol, direction, analysis)

        # Emit signal
        self.validation_completed.emit(symbol, analysis['approved'])

        # Emit Wyckoff analysis signal if available
        if 'wyckoff' in analysis and analysis['wyckoff']:
            self.wyckoff_analysis_ready.emit(symbol, analysis['wyckoff'])

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

                # Get comprehensive phase interpretation
                phase_interpretation = self._get_phase_interpretation(phase.value, direction)

                html += f"""
    <div style="padding: 20px; border: 2px solid {tf_color}; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="color: {tf_color}; margin: 0 0 15px 0; font-size: 18px; font-weight: bold;">📊 {tf_name} Timeframe</h4>

        <!-- Wyckoff Phase -->
        <div style="padding: 15px; background-color: rgba(0, 191, 255, 0.1); border-left: 4px solid {phase_color}; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 15px; color: #ddd;">
                <strong style="color: {phase_color};">Phase:</strong> {phase.value}
            </p>
        </div>

        <!-- Comprehensive Phase Story -->
        <div style="padding: 20px; background-color: rgba(255, 215, 0, 0.05); border: 2px solid #FFD700; border-radius: 8px; margin-bottom: 15px;">
            <h5 style="color: #FFD700; margin: 0 0 12px 0; font-size: 16px; font-weight: bold;">📖 THE COMPLETE MARKET STORY</h5>
            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #87CEEB; margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">🎭 What's Really Happening:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{phase_interpretation['story']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #FFD700; margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">🧠 The Psychology Behind It:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{phase_interpretation['psychology']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #4CAF50; margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">💰 How Smart Money Operates Here:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{phase_interpretation['smart_money']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #FF6B6B; margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">⚠️ What Retail Traders Are Doing Wrong:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{phase_interpretation['retail_mistake']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(76, 175, 80, 0.15); border-left: 3px solid #4CAF50; border-radius: 6px;">
                <h6 style="color: #4CAF50; margin: 0 0 8px 0; font-size: 14px; font-weight: bold;">✅ Your Trading Strategy:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{phase_interpretation['strategy']}</p>
            </div>
        </div>
"""

                # Show LPS/LPSY if detected
                if lps_lpsy:
                    lps_type = lps_lpsy['type']
                    lps_color = '#00FF00' if lps_type == 'LPS' else '#FF0000'
                    lps_icon = '🟢' if lps_type == 'LPS' else '🔴'

                    confirmation = "CONFIRMED ✅" if lps_lpsy['confirmed'] else "PENDING ⏳"
                    strength = lps_lpsy['strength']

                    # Get LPS/LPSY interpretation
                    signal_interpretation = self._get_lps_lpsy_interpretation(lps_type, strength, lps_lpsy['confirmed'], direction)

                    html += f"""
        <!-- LPS/LPSY Detection -->
        <div style="padding: 15px; background-color: rgba(0, 255, 0, 0.05); border: 2px solid {lps_color}; border-radius: 6px; margin-bottom: 15px;">
            <h5 style="color: {lps_color}; margin: 0 0 10px 0; font-size: 16px;">{lps_icon} {lps_type} Detected ({strength})</h5>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Status: {confirmation}</p>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Entry: {lps_lpsy['entry_trigger']:.5f}</p>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd;">Stop Loss: {lps_lpsy['stop_loss']:.5f}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #aaa; font-style: italic;">{lps_lpsy['description']}</p>
        </div>

        <!-- LPS/LPSY Interpretation -->
        <div style="padding: 15px; background-color: rgba(135, 206, 250, 0.08); border-left: 4px solid #87CEEB; margin-bottom: 15px;">
            <h5 style="color: #87CEEB; margin: 0 0 10px 0; font-size: 15px; font-weight: bold;">💡 Trading Implications:</h5>
            <p style="margin: 5px 0; font-size: 14px; color: #ddd; line-height: 1.6;">{signal_interpretation['meaning']}</p>
            <p style="margin: 8px 0 5px 0; font-size: 13px; color: #87CEEB; font-weight: bold;">Recommended Action:</p>
            <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.5;">{signal_interpretation['action']}</p>
            <p style="margin: 8px 0 5px 0; font-size: 13px; color: #FF6B6B; font-weight: bold;">Risk Management:</p>
            <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.5;">{signal_interpretation['risk']}</p>
            <p style="margin: 8px 0 5px 0; font-size: 13px; color: #FFA500; font-weight: bold;">Confirmation Needed:</p>
            <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.5;">{signal_interpretation['confirmation']}</p>
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
                    # Get comprehensive volume interpretation
                    volume_interpretation = self._get_volume_interpretation(volume_analysis, phase.value)

                    html += f"""
        <!-- Volume Analysis RAW DATA -->
        <div style="padding: 10px; background-color: rgba(0, 0, 0, 0.2); border-radius: 4px; margin-bottom: 15px;">
            <p style="margin: 0 0 6px 0; font-size: 14px; color: #FFD700; font-weight: bold;">Volume Analysis:</p>
            <p style="margin: 4px 0; font-size: 13px; color: #ddd;">▸ {volume_analysis.get('effort_result', 'N/A')}</p>
            <p style="margin: 4px 0; font-size: 13px; color: #ddd;">▸ {volume_analysis.get('divergence', 'N/A')}</p>
        </div>

        <!-- DEEP VOLUME INTERPRETATION -->
        <div style="padding: 18px; background-color: rgba(138, 43, 226, 0.05); border: 2px solid #8A2BE2; border-radius: 8px; margin-bottom: 15px;">
            <h5 style="color: #8A2BE2; margin: 0 0 12px 0; font-size: 15px; font-weight: bold;">📊 VOLUME: THE BATTLE BETWEEN BUYERS & SELLERS</h5>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #FFD700; margin: 0 0 8px 0; font-size: 13px; font-weight: bold;">⚙️ What's Happening Mechanically:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{volume_interpretation['mechanics']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #87CEEB; margin: 0 0 8px 0; font-size: 13px; font-weight: bold;">🥊 The Order Book Story:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{volume_interpretation['order_book']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(0, 0, 0, 0.3); border-radius: 6px; margin-bottom: 12px;">
                <h6 style="color: #4CAF50; margin: 0 0 8px 0; font-size: 13px; font-weight: bold;">🏦 What Institutions Are Doing:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{volume_interpretation['institutional']}</p>
            </div>

            <div style="padding: 12px; background-color: rgba(138, 43, 226, 0.15); border-left: 3px solid #8A2BE2; border-radius: 6px;">
                <h6 style="color: #8A2BE2; margin: 0 0 8px 0; font-size: 13px; font-weight: bold;">💡 What This Means For Your Trade:</h6>
                <p style="margin: 5px 0; font-size: 13px; color: #ddd; line-height: 1.8;">{volume_interpretation['trade_impact']}</p>
            </div>
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

    def show_invalid_symbol_error(self, invalid_symbol: str):
        """Show detailed error for invalid symbol with suggestions"""
        # Find similar symbols (fuzzy match)
        all_symbols = symbol_manager.get_all_symbols()
        suggestions = []

        # Check for typos - look for symbols with similar letters
        for sym in all_symbols:
            # Calculate simple similarity (how many characters match)
            matches = sum(1 for a, b in zip(invalid_symbol, sym) if a == b)
            if matches >= 4:  # At least 4 chars match (USDJOY vs USDJPY = 5 matches)
                suggestions.append(sym)

        # If no close matches, show symbols by asset class
        if not suggestions:
            # Get asset class summary
            asset_summary = symbol_manager.get_asset_class_summary()
            by_class = {}
            for asset_class in ['forex', 'stock', 'index', 'commodity', 'crypto']:
                symbols = symbol_manager.get_symbols_by_asset_class(asset_class)
                if symbols:
                    by_class[asset_class] = symbols[:10]  # First 10 of each

        # Build HTML
        html = f"""
<div style="padding: 20px; background-color: #1e1e1e; color: #fff; font-family: 'Segoe UI', Arial, sans-serif;">

    <!-- ERROR HEADER -->
    <div style="padding: 30px 20px; text-align: center; background-color: #2C1810; border-left: 8px solid #F44336;">
        <div style="font-size: 64px; margin-bottom: 15px;">❌</div>
        <h1 style="color: #F44336; font-size: 36px; margin: 0 0 10px 0; font-weight: bold;">INVALID SYMBOL</h1>
        <p style="color: #FFB74D; font-size: 22px; margin: 0; font-weight: 500;">"{invalid_symbol}" not found</p>
    </div>

    <hr style="border: none; border-top: 1px solid #444; margin: 25px 0;">
"""

        # Add suggestions if found
        if suggestions:
            html += f"""
    <div style="padding: 20px; background-color: #1C2833; border-left: 4px solid #4CAF50; margin-bottom: 20px;">
        <h3 style="color: #4CAF50; margin: 0 0 15px 0; font-size: 20px;">💡 Did you mean one of these?</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px;">
"""
            for sym in suggestions[:10]:
                specs = symbol_manager.get_symbol_specs(sym)
                asset_badge = specs.asset_class.upper() if specs else "?"
                badge_color = {
                    'forex': '#2196F3',
                    'stock': '#9C27B0',
                    'index': '#FF9800',
                    'commodity': '#FFD700',
                    'crypto': '#00BCD4'
                }.get(specs.asset_class if specs else '', '#666')

                html += f"""
            <div style="padding: 10px; background-color: #263238; border: 1px solid {badge_color}; border-radius: 4px; text-align: center;">
                <div style="color: #fff; font-weight: bold; font-size: 14px;">{sym}</div>
                <div style="color: {badge_color}; font-size: 10px; margin-top: 3px;">{asset_badge}</div>
            </div>
"""
            html += """
        </div>
    </div>
"""

        # Show available symbols by asset class
        html += """
    <div style="padding: 20px; background-color: #1C2833; border-left: 4px solid #2196F3;">
        <h3 style="color: #2196F3; margin: 0 0 15px 0; font-size: 18px;">📊 Available Symbols</h3>
"""

        total_symbols = symbol_manager.symbol_count()
        asset_summary = symbol_manager.get_asset_class_summary()

        for asset_class in ['forex', 'stock', 'index', 'commodity', 'crypto']:
            if asset_class in asset_summary:
                count = asset_summary[asset_class]
                badge_color = {
                    'forex': '#2196F3',
                    'stock': '#9C27B0',
                    'index': '#FF9800',
                    'commodity': '#FFD700',
                    'crypto': '#00BCD4'
                }[asset_class]

                symbols = symbol_manager.get_symbols_by_asset_class(asset_class)
                examples = ', '.join(symbols[:5])

                html += f"""
        <div style="padding: 10px; margin-bottom: 10px; background-color: #263238; border-left: 3px solid {badge_color};">
            <div style="color: {badge_color}; font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                {asset_class.upper()} ({count} available)
            </div>
            <div style="color: #aaa; font-size: 12px;">
                Examples: {examples}
            </div>
        </div>
"""

        html += f"""
    </div>

    <div style="padding: 15px; text-align: center; background-color: #263238; border-radius: 4px; margin-top: 20px;">
        <p style="color: #aaa; font-size: 13px; margin: 0;">
            <strong>{total_symbols} symbols</strong> loaded from MT5 Market Watch
        </p>
    </div>

</div>
"""

        self.results_display.setHtml(html)
        vprint(f"[TradeValidator] ❌ Invalid symbol '{invalid_symbol}' - showing suggestions")

    def _get_phase_interpretation(self, phase: str, trade_direction: str) -> dict:
        """
        Get comprehensive educational interpretation for Wyckoff phase
        Returns detailed story, psychology, smart money behavior, retail mistakes, and strategy
        """
        interpretations = {
            'ACCUMULATION': {
                'story': "After a prolonged downtrend has exhausted sellers, a dramatic shift occurs beneath the surface. While the price chart looks boring—stuck in a sideways range with no clear direction—institutional players (banks, hedge funds, market makers) are methodically building LONG positions. They can't just buy aggressively all at once because that would spike the price and force them to pay higher prices for their positions. Instead, they disguise their buying by absorbing EVERY sell order that hits the market. When retail traders panic-sell at support, institutions are there waiting to buy. When weak hands throw in the towel, smart money accumulates their shares. The range you see on the chart IS the accumulation process—institutions need time (weeks or months) to build positions worth hundreds of millions without alerting the market. Each retest of support with LOWER volume tells you sellers are exhausting. Each rally on HIGHER volume tells you buyers are gaining control. This is the calm before the storm.",
                'psychology': "Fear dominates retail trader psychology. After getting burned by the previous downtrend, most traders are too scared to buy even though prices are at attractive levels. Headlines are negative. Social media traders are bearish. Everyone 'knows' the market is going lower. This pessimism is EXACTLY what institutions need—fearful sellers willing to exit at low prices. Meanwhile, professional traders see opportunity where retail sees danger. They know that when everyone is bearish, there's no one left to sell, which means the next big move must be UP. The psychological battle is asymmetric: retail trades on emotion (fear), institutions trade on structure (accumulation patterns). By the time retail traders feel comfortable buying again, institutions will already be sitting on profitable positions ready to sell to them.",
                'smart_money': "Institutions operate like stealth submarines. Their primary goal during accumulation is to build MAXIMUM position size at MINIMUM average price without alerting other market participants. How do they do this? (1) They place large BUY orders at support levels to absorb all selling pressure, creating a price floor. (2) They allow 'Springs' (fake breakdowns below support) to trigger retail stop-losses, then aggressively buy the panic selling. (3) They buy on weakness and reduce buying on strength, keeping price rangebound. (4) They use 'Secondary Tests'—deliberately pushing price down to prior lows to see if more sellers emerge. When price holds on LOW volume, it confirms no supply left = mission accomplished. (5) Finally, they engineer an LPS (Last Point of Support), the final spring-loaded test before markup begins. This is your signal that accumulation is nearly complete.",
                'retail_mistake': "Retail traders make catastrophic mistakes during accumulation. Most damaging: they SELL into support because 'the trend is down' or 'it could go lower.' They're providing the exact liquidity institutions want! They set stop-losses just below obvious support levels (where Springs will trigger them). They wait for 'confirmation' (breakout above the range) before buying—by which time institutions have already accumulated and will sell INTO that breakout. They mistake ranging price action for 'nothing happening' when in reality, the most important positioning is occurring. They trade based on news and sentiment instead of volume and price structure. They sell on fear at the worst possible time. The cruel irony: retail traders are CREATING the accumulation by being fearful sellers, then they'll become enthusiastic buyers during distribution (the opposite of what they should do).",
                'strategy': f"{'✅ EXCELLENT TIMING! ' if trade_direction == 'BUY' else '⚠️ CAUTION - Selling during accumulation fights the smart money! '}Your strategy: BE THE BUYER when retail is selling. Look for LPS (Last Point of Support) signals which mark the end of accumulation and start of markup. Enter LONG positions when: (1) Price holds at support on decreasing volume (no sellers left), (2) Springs occur (false breakdowns that reverse quickly), (3) Signs of Strength appear (rallies on increasing volume). Set stops below the Spring lows (structure invalidation point). Don't be aggressive until LPS confirms, then load up. Think like an institution: accumulate patiently during fear, distribute during greed. This phase rewards patience and courage. Position sizing: Start with 30% of intended size early in accumulation, add 40% at LPS confirmation, keep 30% for breakout above range. Time horizon: weeks to months. The money is made by WAITING, not trading."
            },
            'DISTRIBUTION': {
                'story': "Markup has run its course and institutions are now sitting on massive profitable long positions. But there's a problem: they can't just dump everything at once—that would crash the price and they'd get terrible exits. So they create a DISTRIBUTION range, a sideways trading zone near the highs where they methodically SELL their positions to willing buyers (mostly retail traders who are now euphoric and greedy). The chart looks similar to accumulation—boring sideways action—but the underlying mechanics are opposite. Each rally to resistance is met with institutional SELLING. Each dip is bought by retail traders thinking they're 'buying the dip,' but they're actually absorbing institutional supply. Volume spikes on rallies (institutions selling) but price barely moves higher—this is supply overwhelming demand. Secondary tests of highs on LIGHTER volume confirm: fewer buyers at these levels, distribution is working. Upthrusts (fake breakouts above resistance) trap late-arriving bulls, triggering their buys so institutions can sell to them. The range you see IS the distribution in action—this process takes weeks or months because institutions need to exit massive positions without collapsing the market prematurely.",
                'psychology': "Greed and euphoria dominate retail psychology. The recent uptrend has made everyone money. Social media is full of success stories. News headlines are bullish. Everyone 'knows' prices are going higher. This optimism is EXACTLY what institutions need—greedy buyers willing to chase at high prices. Retail traders think 'buy the dip' is free money because 'dips always get bought.' They're not wrong—dips DO get bought... by them, selling institutions! Meanwhile, professional traders recognize the topping pattern and begin reducing exposure or preparing shorts. The psychological battle: retail trades on greed (FOMO), institutions trade on structure (distribution patterns). By the time retail traders panic and want to sell, institutions will have already exited and will be ready to short into the decline. Retail buys tops because it FEELS safe after a rally. Institutions sell tops because they know nothing rises forever.",
                'smart_money': "Institutions become stealth sellers. Their goal: unload MAXIMUM position size at MAXIMUM average price without triggering a collapse. How? (1) They place large SELL orders at resistance to cap rallies, creating a price ceiling. (2) They engineer 'Upthrusts'—fake breakouts above resistance that trigger retail buy stops, then aggressively sell into that buying pressure. (3) They sell on strength and reduce selling on weakness, keeping price rangebound. (4) They use 'Secondary Tests'—pushing price back up to prior highs to see if more buyers emerge. When price fails on LOW volume, it confirms no demand left = mission accomplished. (5) They allow small bounces to keep retail hopeful ('see, it's still going up!') while steadily unloading. (6) Finally, they create LPSY (Last Point of Supply), the final high-risk test before markdown begins. This is your signal distribution is complete and collapse is imminent. Every rally you see is an institution saying 'thank you for buying what I need to sell.'",
                'retail_mistake': "Retail traders commit financial suicide during distribution. Worst mistake: they BUY near resistance because 'momentum is strong' or 'it's breaking out.' They're providing exit liquidity institutions desperately need! They set stop-losses above obvious resistance (where Upthrusts will trigger them). They interpret ranging as 'consolidation before next leg up' when it's actually supply distribution. They chase breakouts above the range—exactly when institutions have finished distribution and are ready to short. They mistake institutional selling volume for 'strength' when price barely moves higher. They believe the bullish news narrative instead of reading volume/price divergences. They buy on greed at the worst possible time. The tragic pattern: retail creates distribution by being greedy buyers, then becomes panic sellers during markdown (again, opposite of optimal). They're always the liquidity provider, never the liquidity taker.",
                'strategy': f"{'✅ EXCELLENT TIMING! ' if trade_direction == 'SELL' else '⚠️ CAUTION - Buying during distribution fights the smart money! '}Your strategy: BE THE SELLER when retail is buying. EXIT ALL LONG POSITIONS immediately—distribution means the uptrend is over. Look for LPSY (Last Point of Supply) signals marking distribution completion and markdown beginning. Enter SHORT positions when: (1) Price fails at resistance on decreasing volume (no buyers left), (2) Upthrusts occur (false breakouts that reverse quickly), (3) Signs of Weakness appear (declines on increasing volume). Set stops above Upthrust highs (structure invalidation point). Don't be aggressive until LPSY confirms, then short heavily. Think like an institution: distribute during euphoria, accumulate during fear. This phase rewards ruthless discipline and contrarian thinking. Position sizing for shorts: 30% early in distribution, 40% at LPSY, 30% reserved for breakdown below range. Time horizon: weeks to months. The money is made by EXITING what everyone wants to buy."
            },
            'MARKUP': {
                'story': "The accumulation campaign was successful—institutions are now fully loaded with long positions. Now they let the market rise. But here's the secret: institutions don't NEED to do much during markup. They simply stop selling, let normal market mechanics work, and watch retail traders push prices higher for them. The initial breakout from accumulation triggers technical traders ('breakout above range!'). Then momentum traders pile in ('trend is your friend'). Then fundamental traders justify it with news ('economy is strong'). Each group adds buying pressure, and institutions just sit back with their cheaper positions acquired during accumulation. Volume increases on rallies (real demand), price makes consistent higher highs and higher lows (uptrend structure intact). This is the 'easy' phase where everything works. Pullbacks to support (former resistance) are shallow and bought quickly. Dips don't last. Every fundamental seems bullish, every indicator turns green. The trend IS your friend—until it isn't (distribution phase starts).",
                'psychology': "Psychology transitions from fear (accumulation) to optimism to greed. Early in markup, smart retail traders who bought accumulation start feeling vindicated. Later, cautious investors gain confidence and add positions. By late markup, everyone is bullish—taxi drivers are giving stock tips, your barber is buying, FOMO is everywhere. Each group enters at progressively WORSE prices. Institutions entered at accumulation lows; early retail at breakout; late retail near tops. The psychological trap: markup FEELS safe because price is rising, but actually becomes RISKIER as it progresses because institutions are getting ready to distribute. The best risk/reward was during scary accumulation. By the time everyone feels comfortable (late markup), the smart money is preparing exits. Remember: markets exist to transfer wealth from the impatient to the patient. Markup rewards those who had courage to buy fear (accumulation), and punishes those who wait for confirmation (late markup/early distribution).",
                'smart_money': "During markup, institutions are in 'hold and lighten' mode. Early markup: they hold positions, occasionally adding on pullbacks to major support. Mid markup: they begin selective profit-taking on rallies to resistance, but overall remain net long. Late markup: they aggressively lighten positions on strength, preparing for distribution phase. Key signs institutions are preparing to distribute: (1) Price advances but gains are diminishing (running into supply), (2) Volume increases on rallies but price barely moves higher (selling into strength), (3) Buying Climaxes appear—parabolic moves that exhaust buyers, (4) Price fails to make new highs despite strong efforts. At this point, smart money transitions from 'hold' to 'prepare to exit' mode. They let retail drive the final rallies, then cap them with heavy selling. The institution's markup playbook: accumulate fear → hold through uncertainty → distribute into greed.",
                'retail_mistake': "Retail's biggest mistake during markup: waiting too long to enter or chasing late. Many retail traders missed accumulation (too scary) and only notice the uptrend after significant gains already occurred. Then they buy late markup at terrible prices, just as institutions prepare to distribute. Other mistakes: overleveraging because 'trend is strong,' adding positions as price extends further from value, ignoring signs of distribution starting, holding through LPSY signals because they're 'in a strong uptrend.' The painful truth: by the time retail feels confident enough to be fully invested, the move is largely over. They enter late (bad prices) with large size (greed) right when institutions are preparing exits (bad timing). Perfect recipe for buying the top. Smart traders scale OUT during markup; retail scales IN during markup. That's why institutions make money and retail loses it.",
                'strategy': f"Your strategy: Trail stops on existing longs—lock in profits as you go. DON'T chase here if you're not already in; better to miss the move than buy the top. Look for pullbacks to support (former resistance) for selective additions, but reduce size as markup matures. Watch for distribution signals: price struggling to make new highs, volume spikes with limited upside, LPSYs forming. When distribution begins, EXIT IMMEDIATELY—don't hope for 'one more rally.' Position management: Take 25% profits at first resistance, 25% at second resistance, trail stops on remaining 50%. If late markup shows weakness, exit everything and prepare for shorts. The goal isn't maximizing this trade's profit; it's protecting capital for the next accumulation cycle. Markup is where you REALIZE the gains from accumulation—don't get greedy and give them back during distribution."
            },
            'MARKDOWN': {
                'story': "Distribution was successful—institutions have exited most long positions and may now hold shorts. They step aside and let gravity do its work. Markdown is the mirror opposite of markup: price declines consistently, rallies are weak and short-lived, every bounce gets sold. The breakdown from distribution triggers technical traders' stops ('broke support!'). Then margin calls force liquidation ('my account!'). Then panic sellers capitulate ('just get me out!'). Each wave adds selling pressure, and institutions just watch from the sidelines with short positions. Volume increases on declines (real supply), price makes consistent lower lows and lower highs (downtrend intact). This is the 'everything is broken' phase where nothing works for longs. Rallies to resistance are weak and fail quickly. Bounces don't last. Every news item seems bearish, every indicator turns red. The trend IS your enemy if you're long—but your friend if you positioned shorts at LPSY during distribution.",
                'psychology': "Psychology transitions from greed (distribution) to hope to fear to capitulation. Early markdown, retail holds losing positions hoping for recovery ('it's just a correction'). Mid markdown, hope turns to concern ('maybe I should reduce size'). Late markdown, fear turns to panic ('just sell everything!'). The psychology is backwards: retail should sell early (small losses) but holds hoping; then sells late (large losses) in panic. Meanwhile, institutions who sold at distribution highs watch the decline calmly—maybe even short into rallies. The cruel irony: retail needs to sell when it's psychologically hardest (early downtrend) and should consider buying when it's scariest (late markdown / early accumulation). But emotion dominates, so they do the opposite.",
                'smart_money': "Institutions are in 'short and cover' mode. Early markdown: they may add shorts on rallies to resistance. Mid markdown: they hold shorts, occasionally covering on panic selloffs. Late markdown: they begin covering shorts aggressively, preparing for accumulation. Key signs institutions are preparing to accumulate: (1) Price declines but losses are diminishing, (2) Volume increases on drops but price barely moves lower (buying into weakness), (3) Selling Climaxes appear—panic moves that exhaust sellers, (4) Price fails to make new lows despite selling pressure. At this point, smart money shifts from 'short' to 'prepare to accumulate' mode. They let retail panic-sell the final lows, then absorb that supply. The institutional markdown playbook: distribute greed → short through fear → accumulate panic.",
                'retail_mistake': "Retail's mistakes during markdown are catastrophic. They hold losing longs too long ('it'll come back'), they add to losers ('averaging down'), they deny the downtrend ('just a correction'), they panic-sell at bottoms ('I can't take more pain'). By the time they capitulate and sell, institutions are ready to accumulate. The pattern repeats: retail buys tops (distribution greed), holds through declines (denial), sells bottoms (panic). They do everything backwards. Smart traders cut losses quick and look for accumulation signs; retail hopes and holds until forced to exit at the worst prices.",
                'strategy': f"Your strategy: Trail stops on any remaining shorts—lock in gains. Look for rallies to resistance (former support) for selective short additions, but reduce size as markdown matures and volume shows climactic selling (exhaustion). Watch for accumulation signals: price holding at lows on high volume (buying), Springs forming (final lows), LPS developing. When accumulation begins, COVER ALL SHORTS and prepare to flip LONG. The goal isn't squeezing every pip from the downtrend; it's recognizing the cycle shift to accumulation. Position management for shorts: Take 25% profits at first support break, 25% at second support break, trail stops on remaining 50%. If late markdown shows buying absorption, exit all shorts and start looking for accumulation longs. The real money isn't made shorting markdown—it's made buying the next accumulation phase."
            },
            'UNKNOWN': {
                'story': "The market structure is cloudy and ambiguous. This typically occurs during: (1) Transition periods between phases (accumulation ending, markup starting), (2) Low volatility environments when institutions aren't active, (3) Major news events creating erratic price action, (4) Low-volume holiday periods. Price action lacks clear patterns. Volume is inconsistent. Wyckoff events aren't appearing. Both bullish and bearish cases have merit. This is the market saying: 'I'm not ready to show my hand yet.' Trying to force trades in unclear structure is like sailing without wind—lots of effort, no progress, high risk of going in circles.",
                'psychology': "Traders feel confused and frustrated. 'Is it going up or down?' Technical indicators give mixed signals. News provides no clarity. This uncertainty is actually healthy—it means no strong directional bias exists yet, which means the next clear move (when it comes) will likely be tradeable. The psychological trap: boredom leads to overtrading. Traders force positions just to 'be in the market' even though there's no edge. Better to accept uncertainty and wait patiently.",
                'smart_money': "Institutions during unknown phases are either: (1) Inactive—waiting for better opportunities, (2) Testing—probing for areas of supply/demand, or (3) Transitioning—finishing one phase before starting another. They're comfortable doing NOTHING when structure isn't clear. Retail traders can't stand doing nothing. This patience gap is a key edge for professionals. When institutions return with size, you'll see it: volume increases, clear patterns emerge, Wyckoff events appear. Until then, they're content watching from sidelines.",
                'retail_mistake': "Retail's biggest mistake in unclear structure: overtrading. They force positions in choppy markets, get stopped out repeatedly (death by 1000 cuts), chase false breakouts, revenge trade after losses. They confuse activity with productivity. Better to trade once with clarity than ten times with confusion. Every trade should have edge; if structure is unclear, there's no edge. Waiting IS a position.",
                'strategy': f"Your strategy: REDUCE SIZE OR STEP ASIDE. This is the hardest thing for active traders—doing nothing. But preserving capital during unclear periods lets you deploy size when clarity returns. If you must trade: use smallest position sizes, widest stops, quickest exits if proven wrong. Better approach: wait for clarity. Watch for: (1) Volume increasing (institutions returning), (2) Clear Wyckoff events forming, (3) Phase structure emerging (accumulation/distribution patterns). When these appear, phase will become clear and tradeable. Until then, paper trade, study structure, prepare watchlists. The trader who waits for clarity and then acts decisively will outperform the trader who constantly trades unclear structure. Sometimes the best trade is no trade. Patience isn't passive; it's active preparation for the next high-probability opportunity."
            }
        }

        interpretation = interpretations.get(phase, interpretations['UNKNOWN'])

        # Add trade-specific context
        if phase == 'ACCUMULATION' and trade_direction == 'BUY':
            interpretation['strategy'] = "✅ EXCELLENT TIMING! " + interpretation['strategy']
        elif phase == 'DISTRIBUTION' and trade_direction == 'SELL':
            interpretation['strategy'] = "✅ EXCELLENT TIMING! " + interpretation['strategy']
        elif phase == 'ACCUMULATION' and trade_direction == 'SELL':
            interpretation['strategy'] = "⚠️ CAUTION - Selling during accumulation fights the smart money! " + interpretation['strategy']
        elif phase == 'DISTRIBUTION' and trade_direction == 'BUY':
            interpretation['strategy'] = "⚠️ CAUTION - Buying during distribution fights the smart money! " + interpretation['strategy']

        return interpretation

    def _get_lps_lpsy_interpretation(self, signal_type: str, strength: str, confirmed: bool, trade_direction: str) -> dict:
        """
        Get educational interpretation for LPS/LPSY signals
        Returns meaning, recommended action, risk management, and confirmation needs
        """
        if signal_type == 'LPS':
            meaning = "Last Point of Support (LPS) is the FINAL low-risk buying opportunity after accumulation. It represents the last time price tests support before markup begins. Smart money uses this point to add final positions before the big move up. This is one of the highest probability trade setups in Wyckoff methodology."

            if strength == 'STRONG':
                action = "This is a HIGH PROBABILITY long entry. Consider entering at the trigger price with appropriate position sizing. The strong rating indicates multiple confirming factors: volume characteristics, price action structure, and phase alignment."
            elif strength == 'MODERATE':
                action = "This is a GOOD long entry opportunity. Consider entering with slightly reduced position size compared to strong signals. Wait for additional confirmation if possible (price holding above LPS on retest, volume drying up)."
            else:  # WEAK
                action = "This is a MARGINAL long setup. Only enter with small position size and tight stops. Ideally, wait for stronger confirmation or look for a better LPS setup. Weak signals have lower win rates."

            if confirmed:
                risk = f"Stop loss is placed below the LPS low. If price breaks below this level, the accumulation structure is invalidated and you must exit. Risk 1-2% of account per trade. The confirmation adds confidence - failure rate is lower on confirmed LPS."
            else:
                risk = f"Stop loss is placed below the LPS low. However, this signal is NOT YET CONFIRMED - price hasn't demonstrated follow-through. Consider waiting for confirmation (price moving up from LPS, volume increasing on rallies) or use smaller position size with tighter stops."

            confirmation = "Watch for: (1) Price holding above LPS on any retest, (2) Volume decreasing on pullbacks (no supply), (3) Volume increasing on rallies (demand present), (4) Higher lows forming (uptrend structure). If these appear, add to position."

            # Trade-specific context
            if trade_direction == 'SELL':
                action = f"⚠️ WARNING: You want to SELL but LPS suggests BUYING! This is contradictory. LPS marks the end of accumulation and start of markup (uptrend). Selling here fights institutional buying pressure. Reconsider your trade direction or wait for market structure to change."
            elif trade_direction == 'BUY':
                action = f"✅ ALIGNMENT CONFIRMED! Your BUY trade aligns with the LPS signal. {action}"

        else:  # LPSY
            meaning = "Last Point of Supply (LPSY) is the FINAL low-risk selling opportunity after distribution. It represents the last time price tests resistance before markdown begins. Smart money uses this point to add final short positions or exit remaining longs before the big move down. This is one of the highest probability short setups in Wyckoff methodology."

            if strength == 'STRONG':
                action = "This is a HIGH PROBABILITY short entry. Consider entering at the trigger price with appropriate position sizing. The strong rating indicates multiple confirming factors: volume characteristics, price action structure, and phase alignment."
            elif strength == 'MODERATE':
                action = "This is a GOOD short entry opportunity. Consider entering with slightly reduced position size compared to strong signals. Wait for additional confirmation if possible (price failing below LPSY on retest, volume drying up on rallies)."
            else:  # WEAK
                action = "This is a MARGINAL short setup. Only enter with small position size and tight stops. Ideally, wait for stronger confirmation or look for a better LPSY setup. Weak signals have lower win rates."

            if confirmed:
                risk = f"Stop loss is placed above the LPSY high. If price breaks above this level, the distribution structure is invalidated and you must exit. Risk 1-2% of account per trade. The confirmation adds confidence - failure rate is lower on confirmed LPSY."
            else:
                risk = f"Stop loss is placed above the LPSY high. However, this signal is NOT YET CONFIRMED - price hasn't demonstrated follow-through. Consider waiting for confirmation (price moving down from LPSY, volume increasing on declines) or use smaller position size with tighter stops."

            confirmation = "Watch for: (1) Price failing below LPSY on any retest, (2) Volume decreasing on rallies (no demand), (3) Volume increasing on declines (supply present), (4) Lower highs forming (downtrend structure). If these appear, add to position."

            # Trade-specific context
            if trade_direction == 'BUY':
                action = f"⚠️ WARNING: You want to BUY but LPSY suggests SELLING! This is contradictory. LPSY marks the end of distribution and start of markdown (downtrend). Buying here fights institutional selling pressure. Reconsider your trade direction or wait for market structure to change."
            elif trade_direction == 'SELL':
                action = f"✅ ALIGNMENT CONFIRMED! Your SELL trade aligns with the LPSY signal. {action}"

        return {
            'meaning': meaning,
            'action': action,
            'risk': risk,
            'confirmation': confirmation
        }

    def _get_volume_interpretation(self, volume_analysis: dict, phase: str) -> dict:
        """
        Get comprehensive educational interpretation for volume analysis
        Returns detailed mechanics, order book story, institutional behavior, and trade impact
        """
        effort_result = volume_analysis.get('effort_result', '').lower()
        divergence = volume_analysis.get('divergence', '').lower()

        # Initialize return fields
        mechanics = ""
        order_book = ""
        institutional = ""
        trade_impact = ""

        # HIGH VOLUME + NARROW SPREAD = ABSORPTION
        if 'high volume' in effort_result and 'narrow spread' in effort_result:
            mechanics = "You're witnessing ABSORPTION in real-time. Here's what's physically happening: Thousands of orders are being executed (high volume), but despite all this trading activity, price is barely moving (narrow spread). This is NOT normal—usually high volume causes significant price movement. The lack of movement tells you one side is AGGRESSIVELY absorbing everything the other side throws at them. Think of it like a sponge soaking up water: no matter how much water (volume) you pour, the sponge (absorbing party) just keeps taking it in without overflowing (price staying stable). Every market or limit order hitting the tape is being instantly matched by the opposing side. The order book is in fierce battle, but one side has deeper pockets and refuses to let price move."

            if phase == 'ACCUMULATION':
                order_book = "Zoom into the order book: Sellers are throwing SELL orders at the BID (market sells) or placing LIMIT sells, trying to push price down or exit positions. But here's what you can't see on the chart—institutions have MASSIVE buy orders sitting at support levels. Every time a seller hits 'sell market order,' an institutional buy order absorbs it instantly. The bid doesn't drop because institutions keep refilling it. It's like a brick wall: sellers keep punching it, but it doesn't break. The high volume represents sellers exhausting their supply. The narrow spread means institutions are defending this price level with huge capital. They WANT sellers to panic here because it lets them accumulate positions at attractive prices without chasing price higher."

                institutional = "Institutions are executing their accumulation playbook perfectly. They've identified this price level as VALUE and committed massive capital to defend it. Their algorithm: 'Buy EVERY dip, absorb EVERY seller, don't let price fall.' They're not trying to push price up yet (that comes in markup)—they're just stopping it from going down while building positions. This is stealth accumulation at its finest. Retail sees 'boring range-bound action.' Institutions see 'successful absorption of supply.' When sellers finally exhaust (volume drops, Springs fail), institutions stop buying and let price rise naturally into markup. The absorption you're seeing NOW is the foundation for the markup move LATER."

                trade_impact = "FOR YOUR TRADE: This is EXTREMELY BULLISH. High volume absorption at support during accumulation is one of the strongest signs that: (1) Institutions are accumulating aggressively, (2) Selling pressure is being exhausted, (3) Price has found a floor that won't break, (4) Markup phase is approaching. DO NOT SELL HERE—you'd be selling to institutional buyers at exactly the wrong time. Instead, consider this a gift: you're seeing real-time evidence of institutional buying. Enter LONG on this absorption, or wait for the Spring/LPS that typically follows. Set stops below the absorbed low (if institutions let price break there, their accumulation failed = your signal to exit). Target: the top of the accumulation range initially, then markup highs. This is the 'easy money' setup that happens once or twice per major cycle."

            elif phase == 'DISTRIBUTION':
                order_book = "Order book perspective: Buyers are throwing BUY orders at the ASK (market buys) or placing LIMIT buys, trying to push price up or chase momentum. But institutions have MASSIVE sell orders sitting at resistance levels. Every time a buyer hits 'buy market order,' an institutional sell order fills it instantly. The ask doesn't rise because institutions keep refilling it with supply. It's a ceiling: buyers keep pushing, but can't break through. The high volume represents buyers exhausting their capital. The narrow spread means institutions are defending this ceiling with unlimited supply. They WANT buyers to chase here because it lets them distribute (sell) positions at favorable prices without crashing the market."

                institutional = "Institutions are executing their distribution playbook. They've identified this price level as OVERVALUED and committed to exit all longs here. Their algorithm: 'Sell EVERY rally, absorb EVERY buyer, don't let price rise.' They're not trying to crash price yet (that comes in markdown)—they're just capping gains while offloading positions. This is stealth distribution. Retail sees 'healthy consolidation before breakout.' Institutions see 'successful distribution of supply.' When buyers finally exhaust (volume drops, Upthrusts fail), institutions step aside and let price collapse naturally into markdown. The distribution you're seeing NOW is what causes the markdown crash LATER."

                trade_impact = "FOR YOUR TRADE: This is EXTREMELY BEARISH. High volume absorption at resistance during distribution is one of the strongest signs that: (1) Institutions are distributing (selling) aggressively, (2) Buying pressure is being exhausted, (3) Price has hit a ceiling that won't break, (4) Markdown phase is approaching. EXIT ALL LONGS IMMEDIATELY—you're holding what institutions are desperate to sell. DO NOT BUY HERE—you'd be buying from institutional sellers at exactly the wrong time. Consider SHORT positions: enter on this absorption, or wait for the Upthrust/LPSY that typically follows. Set stops above the absorbed high (if institutions let price break there, their distribution failed). Target: bottom of distribution range initially, then markdown lows. This setup precedes major declines."

            else:  # Other phases
                order_book = "The order book shows intense fighting between buyers and sellers. One side is throwing everything they have (high volume), but the other side is matching every order (narrow spread). It's tug-of-war at equilibrium. Whoever runs out of ammunition first will lose, and price will move sharply in the opposite direction. Watch for volume to dry up—that signals exhaustion of the losing side."

                institutional = "Institutions are clearly active (evidenced by volume large enough to absorb heavy one-sided flow). They're either: (1) Defending a level they consider important, (2) Transitioning between phases, or (3) Testing market appetite at this price. Their willingness to absorb high volume without letting price move indicates strong conviction about this price level's strategic importance. Stay alert—when absorption ends, a sharp move typically follows."

                trade_impact = "FOR YOUR TRADE: Absorption means imminent volatility. The coiled spring will release soon. Direction depends on who exhausts first: if sellers exhaust (volume drops, price holds), buy the breakout UP. If buyers exhaust (volume drops, price fails), short the breakdown DOWN. Don't trade the chop—wait for resolution. The side being absorbed is losing; trade with the absorber, not against them."

        # HIGH VOLUME + WIDE SPREAD = MOMENTUM/AGREEMENT
        elif 'high volume' in effort_result and 'wide spread' in effort_result:
            mechanics = "This is MOMENTUM—effort (volume) and result (price movement) are perfectly aligned. Thousands of orders are executing (high volume) AND price is moving significantly (wide spread). This represents one-sided agreement: either buyers are overwhelming sellers, or sellers are overwhelming buyers. There's no equilibrium, no absorption—just pure directional force. Every market order pushes price further because there's insufficient counter-pressure. The order book is getting steamrolled in one direction. Stops are triggering (adding fuel), momentum traders are piling in (more fuel), and the move feeds on itself."

            if 'up' in effort_result or phase in ['MARKUP', 'ACCUMULATION']:
                order_book = "The BUY side is winning decisively. Picture the order book: BUY market orders are hitting the ASK aggressively, taking out each price level like dominoes. Limited SELL orders exist to absorb the buying pressure, so price gaps higher with each wave of buys. SELL limit orders at each level get consumed instantly. Sellers who want out have to chase price UP to find buyers—that's STRENGTH. The spread widening means buyers aren't finding resistance—they're pushing into thin air, which accelerates the move. This is what 'strong demand' looks like mechanically: not just buyers present, but buyers OVERWHELMING available supply."

                institutional = "Institutions are either: (1) Leading the move (early markup from accumulation), (2) Allowing it to happen (mid markup), or (3) Selling into it (late markup / distribution). Context matters: If this occurs during accumulation breakout or early markup, institutions are likely buyers letting the move run (they want higher prices to distribute later). If during late markup / distribution, institutions are likely SELLERS using retail buying pressure to exit. Volume profile helps: increasing volume + wid spread = healthy rally (institutions participating). Decreasing volume + wide spread = climax rally (institutions exiting). Pay attention to follow-through: does price consolidate and continue (bullish), or reverse (bearish)?"

                trade_impact = f"FOR YOUR TRADE {'(UPWARD)' if 'up' in effort_result else ''}: High volume + wide spread UP during ACCUMULATION/MARKUP is bullish confirmation. This is the 'Signs of Strength' Wyckoff traders look for. It confirms buyers are in control and markup is underway. IF YOU'RE LONG: Trail stops aggressively—let winners run, but protect profits. IF YOU'RE CONSIDERING entry: wait for pullback to support (former resistance), don't chase. IF YOU'RE SHORT: Cut losses immediately—fighting this strength will hurt. However, be cautious if this occurs during DISTRIBUTION: it might be an Upthrust (bull trap) where institutions sell into euphoric buying. Watch follow-through: strong moves consolidate and continue; climax moves reverse sharply."

            else:  # Downward or markdown/distribution
                order_book = "The SELL side is winning decisively. Picture the order book: SELL market orders are hitting the BID aggressively, taking out each price level in rapid succession. Limited BUY orders exist to absorb the selling pressure, so price gaps lower with each wave of sells. BUY limit orders at each level get consumed instantly. Buyers who want in have to chase price DOWN to find sellers—that's WEAKNESS. The spread widening means sellers aren't finding support—they're pushing into thin air, which accelerates the decline. This is what 'strong supply' looks like mechanically: not just sellers present, but sellers OVERWHELMING available demand."

                institutional = "Institutions are either: (1) Leading the move (early markdown from distribution), (2) Allowing it to happen (mid markdown), or (3) Buying into it (late markdown / accumulation). Context matters: If this occurs during distribution breakdown or early markdown, institutions are likely sellers/shorts letting the move run. If during late markdown / accumulation, institutions are likely BUYERS using retail panic to accumulate. Volume profile helps: increasing volume + wide spread = healthy decline (institutions participating). Decreasing volume + wide spread = climax decline (institutions covering/buying). Pay attention to follow-through: does price consolidate and continue down (bearish), or reverse up (bullish)?"

                trade_impact = "FOR YOUR TRADE (DOWNWARD): High volume + wide spread DOWN during DISTRIBUTION/MARKDOWN is bearish confirmation. This is the 'Signs of Weakness' Wyckoff traders watch for. It confirms sellers are in control and markdown is underway. IF YOU'RE SHORT: Trail stops—lock in profits while letting the move play out. IF YOU'RE LONG: Cut losses immediately and exit. IF YOU'RE CONSIDERING SHORTS: Wait for rally to resistance (former support), don't chase. However, be cautious if this occurs during ACCUMULATION: it might be a Spring (bear trap) where institutions buy into panic selling. Watch follow-through: strong declines consolidate and continue; climax declines reverse sharply (selling exhaustion)."

        # LOW VOLUME + NARROW SPREAD = INDECISION/APATHY
        elif 'low volume' in effort_result and 'narrow spread' in effort_result:
            mechanics = "This is APATHY—nobody cares. Low volume means few orders are executing. Narrow spread means price isn't moving. Both buyers and sellers are absent or indecisive. The order book is thin on both sides: not many buy orders, not many sell orders. No institutional interest, no retail interest, no momentum, no volatility. This is the 'dead zone' where trading is frustrating and unprofitable. Price drifts aimlessly. Spreads widen (less liquidity). Slippage increases. Nothing matters because nobody's participating."

            order_book = "Imagine an order book with scattered, small orders on both sides. A BUY market order moves price up slightly (thin asks), then a SELL market order moves it back down (thin bids). Neither side has conviction. Market makers are in control by default—they widen spreads and clip retail traders on both sides. There's no large institutional orders (those create volume and movement). Just random retail positions being opened/closed with minimal impact. The book is 'balanced' but only because neither side cares, not because of equilibrium from strong participants."

            institutional = "Institutions are ABSENT. Low volume environments occur when smart money is on holiday, between major market phases, or waiting for catalysts (news, data releases, events). They're not accumulating (that creates volume at lows), not distributing (that creates volume at highs), not marking up or down (that creates movement). They're simply not participating. This is retail-only trading—and retail doesn't move markets. Without institutional participation, there's no edge, no trends, no meaningful structure. Just noise."

            trade_impact = "FOR YOUR TRADE: AVOID TRADING THIS ENVIRONMENT. Low volume + narrow spread is a profit graveyard. Why? (1) No trends to ride, (2) Wide spreads eat your edge, (3) False breakouts everywhere (thin books mean small orders can cause spikes), (4) Whipsaws constant (no directional conviction), (5) Opportunity cost (capital deployed here could be deployed in better setups). Better strategy: WAIT. Preserve capital, study structure, prepare watchlists. When institutions return (volume increases, patterns form), THEN trade aggressively. The trader who can do nothing during low-probability environments and go all-in during high-probability environments will massively outperform the trader who trades constantly. Patience IS a position. Boredom is not a reason to trade."

        # LOW VOLUME + WIDE SPREAD = NO RESISTANCE
        elif 'low volume' in effort_result and 'wide spread' in effort_result:
            mechanics = "This is the 'NO RESISTANCE' scenario—price moves significantly (wide spread) on minimal volume (low effort). This seems counterintuitive: how can price move a lot with little activity? Answer: lack of opposition. The side opposing the move is ABSENT from the market. If price is rising, it means no sellers are defending higher levels—buy orders easily push price up because asks are thin. If price is falling, it means no buyers are defending lower levels—sell orders easily push price down because bids are thin. It's like pushing a door you expect to be locked but finding it wide open—you stumble forward with minimal effort."

            if phase in ['MARKUP', 'ACCUMULATION'] or 'up' in effort_result:
                order_book = "Order book perspective: Price is rising, but it's not due to aggressive buying (volume is low). Instead, the ASK side of the book is THIN—few sell orders are posted. Each small buy order 'climbs the ladder' of asks, moving price up easily. Sellers aren't defending higher prices; they're either: (1) Not interested in selling (holding), or (2) Already sold (exhausted during accumulation). This is the classic 'NO SUPPLY' condition. Price rises not because buyers are strong, but because sellers are absent. It's passive strength—the path of least resistance is UP."

                institutional = "This is BULLISH and indicates successful accumulation. During accumulation, institutions absorbed all available supply (sellers). Now that selling pressure is exhausted, even modest buying moves price higher—there's no supply to absorb the demand. Institutions don't need to push hard (hence low volume); they just step aside and let natural dynamics work. The lack of resistance confirms their accumulation was successful and markdown/distribution phase truly ended. This setup typically occurs: (1) After Spring (false low) traps sellers, (2) At LPS (last point of support), or (3) Early markup when retail hasn't noticed yet."

                trade_impact = "FOR YOUR TRADE: This is a STRONG BUY signal. Low volume + wide spread UP = 'NO SUPPLY' = very bullish. It means: (1) Sellers are exhausted (already sold during accumulation), (2) No institutional resistance to upside (they want higher prices), (3) Trend can continue with minimal effort (efficient move), (4) Any real buying will accelerate move significantly. STRATEGY: Hold longs with trailing stops, add on any pullbacks to support. This is the 'effortless uptrend' that can run for weeks/months. Don't overthink it—absence of supply is pure bullishness. Only concern: watch for increased volume at resistance (supply returning). But while volume stays low and price rises easily, stay long and enjoy the ride. This is what 'easy money' looks like."

            elif phase in ['MARKDOWN', 'DISTRIBUTION'] or 'down' in effort_result:
                order_book = "Order book perspective: Price is falling, but it's not due to aggressive selling (volume is low). Instead, the BID side of the book is THIN—few buy orders are posted. Each small sell order 'descends the ladder' of bids, moving price down easily. Buyers aren't defending lower prices; they're either: (1) Not interested in buying (afraid), or (2) Already bought and holding losing positions (stuck). This is the classic 'NO DEMAND' condition. Price falls not because sellers are strong, but because buyers are absent. It's passive weakness—the path of least resistance is DOWN."

                institutional = "This is BEARISH and indicates successful distribution. During distribution, institutions offloaded their positions to willing buyers (retail). Now that buying pressure is exhausted, even modest selling moves price lower—there's no demand to absorb the supply. Institutions don't need to push hard (hence low volume); they just step aside and let gravity work. The lack of support confirms their distribution was successful and markup phase truly ended. This setup typically occurs: (1) After Upthrust (false high) traps buyers, (2) At LPSY (last point of supply), or (3) Early markdown when retail is still hopeful."

                trade_impact = "FOR YOUR TRADE: This is a STRONG SELL signal. Low volume + wide spread DOWN = 'NO DEMAND' = very bearish. It means: (1) Buyers are exhausted (already bought during distribution), (2) No institutional support (they want lower prices), (3) Trend can continue with minimal effort (efficient decline), (4) Any real selling will accelerate move significantly. STRATEGY: If long, EXIT immediately. If short, hold with trailing stops or add on any rallies to resistance. This is the 'effortless downtrend' that can run for weeks/months. Don't try to catch falling knives—absence of demand is pure bearishness. Only concern: watch for increased volume at support (demand returning). But while volume stays low and price falls easily, stay flat or short. This is how markup gains are given back."

        # Handle divergences
        divergence_insight = ""
        if 'bullish' in divergence:
            divergence_insight = " ADDITIONALLY: Bullish divergence detected—price making lower lows but volume decreasing. This means selling pressure is EXHAUSTING. Each new low requires less volume (effort), indicating sellers are running out of ammunition. When sellers exhaust, buyers take control by default. This is a strong early warning of trend reversal from down to up. Combined with current volume pattern, it reinforces the bullish case. Watch for Accumulation signals (Spring, LPS) to confirm the reversal."
        elif 'bearish' in divergence:
            divergence_insight = " ADDITIONALLY: Bearish divergence detected—price making higher highs but volume decreasing. This means buying pressure is EXHAUSTING. Each new high requires less volume (effort), indicating buyers are running out of ammunition. When buyers exhaust, sellers take control by default. This is a strong early warning of trend reversal from up to down. Combined with current volume pattern, it reinforces the bearish case. Watch for Distribution signals (Upthrust, LPSY) to confirm the reversal."
        elif 'no divergence' in divergence:
            divergence_insight = " ADDITIONALLY: No divergence present—volume and price are moving in harmony. This indicates the current trend is healthy and sustainable. There are no warning signs of exhaustion yet. Trends tend to continue until divergences appear, so the path of least resistance remains in the current direction. Stay with the trend until volume/price harmony breaks."

        # Add divergence insight to trade_impact
        trade_impact += divergence_insight

        return {
            'mechanics': mechanics,
            'order_book': order_book,
            'institutional': institutional,
            'trade_impact': trade_impact
        }

    def set_symbol(self, symbol):
        """Update the current symbol"""
        self.current_symbol = symbol

    def update_data(self):
        """Update widget data - called periodically"""
        pass  # No periodic updates needed for this widget
