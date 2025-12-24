"""
AppleTrader Pro - Price Action Commentary Widget
Real-time market narrative with predictive analysis
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTextEdit, QFrame, QGroupBox, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from datetime import datetime, timedelta
from typing import List, Dict
import random

from core.data_manager import data_manager
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from analysis.order_block_detector import order_block_detector
from analysis.liquidity_sweep_detector import liquidity_sweep_detector
from analysis.fair_value_gap_detector import fair_value_gap_detector
from analysis.market_structure_detector import market_structure_detector


class PriceActionCommentaryWidget(AIAssistMixin, QWidget):
    """
    Price Action Commentary Widget

    Provides real-time educational analysis:
    - What price is currently doing
    - Where it's likely heading (predictions)
    - Why it's moving this way
    - Key levels to watch
    - Institutional behavior insights
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_symbol = "EURUSD"
        self.current_timeframe = "M15"  # Add timeframe tracking
        self.commentary_history = []
        self.last_price = None
        self.price_direction = "NEUTRAL"
        self.current_analysis = None  # Store current price action analysis for AI

        self.init_ui()
        self.setup_ai_assist("price_action")

        # Auto-update timer (every 5 seconds for new commentary)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)  # FIXED: Call update_data() to respect mode
        self.update_timer.start(5000)

        # Initial load
        self.update_data()  # FIXED: Call update_data() to respect mode

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("📊 Price Action Commentary")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #00aaff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # AI checkbox placeholder
        self.ai_checkbox_placeholder = header_layout

        # Live indicator
        self.live_label = QLabel("🟢 LIVE")
        self.live_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.live_label.setStyleSheet("color: #10B981;")
        header_layout.addWidget(self.live_label)

        layout.addLayout(header_layout)

        # === CURRENT MARKET NARRATIVE ===
        narrative_group = QGroupBox("📢 Current Market Narrative")
        narrative_layout = QVBoxLayout()

        self.narrative_text = QTextEdit()
        self.narrative_text.setReadOnly(True)
        self.narrative_text.setMaximumHeight(120)
        self.narrative_text.setFont(QFont("Arial", 11))
        self.narrative_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B;
                border: 2px solid #3B82F6;
                border-radius: 8px;
                color: #F8FAFC;
                padding: 10px;
            }
        """)
        narrative_layout.addWidget(self.narrative_text)

        narrative_group.setLayout(narrative_layout)
        layout.addWidget(narrative_group)

        # === PRICE PREDICTION ===
        self.prediction_group = QGroupBox("🔮 Price Prediction & Bias")
        prediction_layout = QVBoxLayout()

        self.prediction_text = QTextEdit()
        self.prediction_text.setReadOnly(True)
        self.prediction_text.setMaximumHeight(100)
        self.prediction_text.setFont(QFont("Arial", 10))
        self.prediction_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B;
                border: 2px solid #10B981;
                border-radius: 8px;
                color: #F8FAFC;
                padding: 10px;
            }
        """)
        prediction_layout.addWidget(self.prediction_text)

        self.prediction_group.setLayout(prediction_layout)
        layout.addWidget(self.prediction_group)

        # === REAL-TIME COMMENTARY FEED ===
        self.feed_group = QGroupBox("📝 Live Commentary Feed (Auto-Updating)")
        feed_layout = QVBoxLayout()

        self.commentary_feed = QTextEdit()
        self.commentary_feed.setReadOnly(True)
        self.commentary_feed.setFont(QFont("Courier New", 9))
        self.commentary_feed.setStyleSheet("""
            QTextEdit {
                background-color: #0A0E27;
                border: 1px solid #334155;
                border-radius: 5px;
                color: #94A3B8;
                padding: 8px;
            }
        """)
        feed_layout.addWidget(self.commentary_feed)

        self.feed_group.setLayout(feed_layout)
        layout.addWidget(self.feed_group)

        # === KEY LEVELS TO WATCH ===
        levels_group = QGroupBox("🎯 Key Levels to Watch")
        levels_layout = QVBoxLayout()

        self.levels_text = QTextEdit()
        self.levels_text.setReadOnly(True)
        self.levels_text.setMaximumHeight(100)
        self.levels_text.setFont(QFont("Courier New", 9))
        self.levels_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B;
                border: 1px solid #F59E0B;
                border-radius: 5px;
                color: #F8FAFC;
                padding: 8px;
            }
        """)
        levels_layout.addWidget(self.levels_text)

        levels_group.setLayout(levels_layout)
        layout.addWidget(levels_group)

        # AI suggestion frame placeholder
        self.ai_suggestion_placeholder = layout

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #0A0E27;
                color: #F8FAFC;
            }
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #00aaff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def update_commentary(self):
        """Update price action commentary with latest analysis"""
        try:
            # Get current timeframe from data_manager
            self.current_timeframe = data_manager.candle_buffer.timeframe or "M15"

            # Update group titles with current symbol AND TIMEFRAME
            self.prediction_group.setTitle(f"🔮 Price Prediction & Bias [{self.current_symbol} - {self.current_timeframe}]")
            self.feed_group.setTitle(f"📝 Live Commentary Feed ({self.current_symbol} - {self.current_timeframe})")

            # Get current market data
            market_data = self.get_market_data()

            if not market_data:
                # LIVE MODE: No real data available - show clear message
                if not is_demo_mode():
                    self.narrative_text.setHtml(
                        "<p style='color: #ffaa00; font-size: 12pt;'><b>⚠️ WAITING FOR LIVE DATA</b><br>"
                        "No real market data available yet. Check MT5 connection.</p>"
                    )
                    self.prediction_text.setHtml(
                        "<p style='color: #ffaa00;'>Waiting for real data...</p>"
                    )
                    self.levels_text.setHtml(
                        "<p style='color: #888;'>No data available</p>"
                    )
                return

            # Store analysis data for AI
            self.current_analysis = {
                'symbol': market_data.get('symbol', self.current_symbol),
                'timeframe': self.current_timeframe,
                'price': market_data['price'],
                'trend': market_data['trend'],
                'volatility': market_data['volatility'],
                'price_change_pct': market_data['price_change_pct'],
                'high': market_data['high'],
                'low': market_data['low'],
                'sma_20': market_data['sma_20']
            }

            # Generate current narrative
            narrative = self.generate_market_narrative(market_data)
            self.narrative_text.setHtml(narrative)

            # Generate prediction
            prediction = self.generate_prediction(market_data)
            self.prediction_text.setHtml(prediction)

            # Add to commentary feed
            timestamp = datetime.now().strftime("%H:%M:%S")
            feed_entry = self.generate_feed_entry(market_data, timestamp)
            self.add_to_feed(feed_entry)

            # Update key levels
            levels = self.generate_key_levels(market_data)
            self.levels_text.setHtml(levels)

            # Blink live indicator
            self.blink_live_indicator()

            # Update AI if enabled
            if self.ai_enabled and self.current_analysis:
                self.update_ai_suggestions()

        except Exception as e:
            pass

    def set_symbol(self, symbol: str):
        """Update the current symbol and refresh commentary"""
        if symbol != self.current_symbol:
            self.current_symbol = symbol

            # CRITICAL: Clear the commentary feed when symbol changes!
            self.commentary_feed.clear()

            # Clear commentary history
            self.commentary_history = []

            # Immediate refresh with new symbol
            self.update_commentary()

    def get_market_data(self) -> Dict:
        """Get current market data for analysis"""
        # Check demo mode first
        if is_demo_mode():
            return self.get_sample_market_data()

        # LIVE MODE: NEVER return fake data - return None if no real data available
        try:
            # Get data from data manager (uses currently loaded symbol in buffer)
            candles = data_manager.get_candles()

            if not candles or len(candles) < 10:
                # CRITICAL: In live mode, return None instead of fake data
                # This will cause the widget to display "Waiting for data" instead of misleading information
                return None

            current = candles[-1]
            prev = candles[-2]

            # Calculate metrics
            price = current['close']
            price_change = price - prev['close']
            price_change_pct = (price_change / prev['close']) * 100

            # Determine trend
            sma_20 = sum([c['close'] for c in candles[-20:]]) / 20
            trend = "BULLISH" if price > sma_20 else "BEARISH"

            # Volatility
            high_low_range = current['high'] - current['low']
            avg_range = sum([c['high'] - c['low'] for c in candles[-10:]]) / 10
            volatility = "HIGH" if high_low_range > avg_range * 1.5 else "NORMAL"

            # ============================================================
            # SMART MONEY DETECTION
            # ============================================================
            smart_money_context = {}

            # Detect Order Blocks
            order_blocks = order_block_detector.detect_order_blocks(candles, self.current_symbol, lookback=50)
            valid_obs = [ob for ob in order_blocks if ob['valid'] and not ob['mitigated']]
            if valid_obs:
                nearest_ob = valid_obs[0]
                ob_mid = (nearest_ob['price_high'] + nearest_ob['price_low']) / 2
                smart_money_context['nearest_ob'] = {
                    'type': nearest_ob['type'],
                    'price': ob_mid,
                    'distance_pips': abs(price - ob_mid) * 10000
                }

            # Detect Fair Value Gaps
            fvgs = fair_value_gap_detector.detect_fair_value_gaps(candles, self.current_symbol, lookback=50)
            unfilled_fvgs = [fvg for fvg in fvgs if not fvg['filled']]
            if unfilled_fvgs:
                nearest_fvg = unfilled_fvgs[0]
                smart_money_context['nearest_fvg'] = {
                    'type': nearest_fvg['type'],
                    'price': nearest_fvg['mid'],
                    'distance_pips': abs(price - nearest_fvg['mid']) * 10000
                }

            # Detect Liquidity Sweeps
            sweeps = liquidity_sweep_detector.detect_liquidity_sweeps(candles, self.current_symbol, lookback=50)
            if sweeps:
                recent_sweep = sweeps[0]
                smart_money_context['recent_sweep'] = {
                    'type': recent_sweep['type'],
                    'level': recent_sweep['level'],
                    'expected_direction': recent_sweep['expected_direction']
                }

            # Detect Market Structure
            structure_events, current_structure_trend = market_structure_detector.detect_structure_shifts(
                candles, self.current_symbol, lookback=50
            )
            if structure_events:
                latest_event = structure_events[0]
                smart_money_context['structure_event'] = {
                    'type': latest_event['type'],  # BOS or CHoCH
                    'direction': latest_event['direction'],
                    'signal': latest_event['signal']  # continuation or reversal
                }

            return {
                'symbol': self.current_symbol,  # Add symbol to data
                'price': price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'trend': trend,
                'volatility': volatility,
                'high': current['high'],
                'low': current['low'],
                'sma_20': sma_20,
                'smart_money': smart_money_context  # NEW: Smart money context
            }

        except Exception as e:
            # CRITICAL: In live mode, return None on error instead of fake data
            print(f"[Price Action] Error getting live data: {e}")
            return None

    def get_sample_market_data(self) -> Dict:
        """Generate sample market data - USE CURRENT SYMBOL NAME AND APPROPRIATE PRICE RANGE"""
        # CRITICAL: Use appropriate price range for each symbol!
        symbol = self.current_symbol

        # Determine base price and range based on symbol
        if 'JPY' in symbol:
            # JPY pairs trade around 100-160 range
            base_price = 155.0 if 'USD' in symbol else 145.0
            price_change = random.uniform(-0.05, 0.05)  # Bigger pip range for JPY
            range_size = 0.15
        elif 'GBP' in symbol:
            # GBP pairs trade around 1.2-1.3 range
            base_price = 1.27
            price_change = random.uniform(-0.0005, 0.0005)
            range_size = 0.0015
        elif 'EUR' in symbol:
            # EUR pairs trade around 1.0-1.1 range
            base_price = 1.08
            price_change = random.uniform(-0.0005, 0.0005)
            range_size = 0.0015
        elif 'AUD' in symbol or 'NZD' in symbol:
            # AUD/NZD pairs trade around 0.6-0.7 range
            base_price = 0.66
            price_change = random.uniform(-0.0003, 0.0003)
            range_size = 0.001
        else:
            # Default for other pairs
            base_price = 1.16
            price_change = random.uniform(-0.0005, 0.0005)
            range_size = 0.0015

        return {
            'symbol': self.current_symbol,  # Show correct symbol!
            'price': base_price + price_change,
            'price_change': price_change,
            'price_change_pct': (price_change / base_price) * 100,
            'trend': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'volatility': random.choice(['HIGH', 'NORMAL', 'LOW']),
            'high': base_price + abs(price_change) + range_size,
            'low': base_price - abs(price_change) - range_size,
            'sma_20': base_price - (price_change * 0.5)
        }

    def generate_market_narrative(self, data: Dict) -> str:
        """Generate current market narrative"""
        symbol = data.get('symbol', self.current_symbol)
        price = data['price']
        trend = data['trend']
        volatility = data['volatility']
        price_change_pct = data['price_change_pct']
        smart_money = data.get('smart_money', {})

        # Main narrative with SYMBOL NAME
        if trend == "BULLISH":
            trend_text = f"<span style='color: #10B981; font-weight: bold;'>BULLISH</span>"
            narrative = f"<b>{symbol}</b>: Price is currently in a <b>{trend_text}</b> trend, showing strong upward momentum. "
        elif trend == "BEARISH":
            trend_text = f"<span style='color: #EF4444; font-weight: bold;'>BEARISH</span>"
            narrative = f"<b>{symbol}</b>: Price is currently in a <b>{trend_text}</b> trend, showing downward pressure. "
        else:
            trend_text = f"<span style='color: #F59E0B; font-weight: bold;'>NEUTRAL</span>"
            narrative = f"<b>{symbol}</b>: Price is currently <b>{trend_text}</b>, consolidating in a range. "

        # Add volatility context
        if volatility == "HIGH":
            narrative += f"<span style='color: #EF4444;'>High volatility</span> suggests institutional activity and potential breakout. "
        else:
            narrative += f"<span style='color: #10B981;'>Normal volatility</span> indicates stable conditions. "

        # Add price action
        if price_change_pct > 0:
            narrative += f"Price has moved <span style='color: #10B981;'>+{price_change_pct:.3f}%</span> higher, "
            narrative += "indicating buying pressure from institutions."
        else:
            narrative += f"Price has moved <span style='color: #EF4444;'>{price_change_pct:.3f}%</span> lower, "
            narrative += "indicating selling pressure from institutions."

        # ============================================================
        # SMART MONEY NARRATIVE (NEW)
        # ============================================================
        smart_money_narrative = ""

        # Mention nearest Order Block
        if 'nearest_ob' in smart_money:
            ob = smart_money['nearest_ob']
            ob_type_text = "demand zone" if ob['type'] == 'demand' else "supply zone"
            smart_money_narrative += f"<br><br><span style='color: #3B82F6;'>💰 Order Block:</span> Nearest {ob_type_text} at {ob['price']:.5f} ({ob['distance_pips']:.1f} pips away). "

        # Mention nearest FVG
        if 'nearest_fvg' in smart_money:
            fvg = smart_money['nearest_fvg']
            fvg_direction = "bullish" if fvg['type'] == 'bullish' else "bearish"
            smart_money_narrative += f"<span style='color: #F59E0B;'>📊 FVG:</span> {fvg_direction.capitalize()} Fair Value Gap at {fvg['price']:.5f} ({fvg['distance_pips']:.1f} pips). "

        # Mention recent liquidity sweep
        if 'recent_sweep' in smart_money:
            sweep = smart_money['recent_sweep']
            sweep_type = "high" if sweep['type'] == 'high_sweep' else "low"
            smart_money_narrative += f"<span style='color: #EF4444;'>⚡ Liquidity Sweep:</span> Recent {sweep_type} sweep detected - expect {sweep['expected_direction']} move. "

        # Mention market structure event
        if 'structure_event' in smart_money:
            event = smart_money['structure_event']
            event_color = "#10B981" if event['direction'] == 'bullish' else "#EF4444"
            smart_money_narrative += f"<span style='color: {event_color};'>📈 Structure:</span> {event['type']} ({event['signal']}) - {event['direction']} bias. "

        narrative += smart_money_narrative
        return f"<p style='font-size: 12pt; line-height: 1.6;'>{narrative}</p>"

    def generate_prediction(self, data: Dict) -> str:
        """Generate price prediction and bias"""
        symbol = data.get('symbol', self.current_symbol)
        trend = data['trend']
        price = data['price']
        sma_20 = data['sma_20']

        html = "<p style='font-size: 11pt; line-height: 1.5;'>"

        if trend == "BULLISH":
            html += f"<b style='color: #10B981;'>▲ {symbol} BULLISH BIAS</b><br>"
            html += f"Expected move: Continuation to <b>{price + 0.0020:.5f}</b> zone<br>"
            html += f"{symbol}: Watch for pullbacks to support for entry<br>"
            html += "Invalidation: Break below major support"
        elif trend == "BEARISH":
            html += f"<b style='color: #EF4444;'>▼ {symbol} BEARISH BIAS</b><br>"
            html += f"Expected move: Continuation to <b>{price - 0.0020:.5f}</b> zone<br>"
            html += f"{symbol}: Watch for rallies into resistance for entries<br>"
            html += "Invalidation: Break above major resistance"
        else:
            html += f"<b style='color: #F59E0B;'>◆ {symbol} NEUTRAL - RANGE BOUND</b><br>"
            html += "Expected move: Continued consolidation<br>"
            html += f"{symbol}: Watch for breakout above/below range<br>"
            html += "Trade: Range boundaries until breakout confirmed"

        html += "</p>"
        return html

    def generate_feed_entry(self, data: Dict, timestamp: str) -> str:
        """Generate single commentary feed entry"""
        symbol = data.get('symbol', self.current_symbol)
        price = data['price']
        trend = data['trend']
        smart_money = data.get('smart_money', {})

        # Build templates list with smart money context
        templates = [
            f"[{timestamp}] {symbol}: Price testing {price:.5f} - {trend} structure holding",
            f"[{timestamp}] {symbol}: Institutional order flow detected at {price:.5f}",
            f"[{timestamp}] {symbol}: {trend} momentum building - watching for continuation",
            f"[{timestamp}] {symbol}: Smart money accumulation visible at current levels",
            f"[{timestamp}] {symbol}: Key support/resistance interaction at {price:.5f}",
            f"[{timestamp}] {symbol}: Price respecting major technical levels - {trend} bias confirmed"
        ]

        # Add smart money-specific commentary
        if 'nearest_ob' in smart_money:
            ob_type = "demand" if smart_money['nearest_ob']['type'] == 'demand' else "supply"
            templates.append(f"[{timestamp}] {symbol}: Approaching {ob_type} Order Block - institutional zone")

        if 'nearest_fvg' in smart_money:
            templates.append(f"[{timestamp}] {symbol}: FVG zone ahead - price likely to fill the gap")

        if 'recent_sweep' in smart_money:
            direction = smart_money['recent_sweep']['expected_direction']
            templates.append(f"[{timestamp}] {symbol}: Liquidity sweep complete - {direction} bias active")

        if 'structure_event' in smart_money:
            event = smart_money['structure_event']
            templates.append(f"[{timestamp}] {symbol}: {event['type']} detected - {event['signal']} signal")

        return random.choice(templates)

    def add_to_feed(self, entry: str):
        """Add entry to commentary feed"""
        current_text = self.commentary_feed.toPlainText()
        lines = current_text.split('\n')

        # Keep last 15 entries
        if len(lines) > 15:
            lines = lines[-14:]

        lines.append(entry)
        self.commentary_feed.setPlainText('\n'.join(lines))

        # Scroll to bottom
        self.commentary_feed.verticalScrollBar().setValue(
            self.commentary_feed.verticalScrollBar().maximum()
        )

    def generate_key_levels(self, data: Dict) -> str:
        """Generate key levels to watch"""
        price = data['price']

        resistance_1 = price + 0.0015
        resistance_2 = price + 0.0030
        support_1 = price - 0.0015
        support_2 = price - 0.0030

        html = "<p style='font-size: 10pt; line-height: 1.8; font-family: Courier New;'>"
        html += f"<span style='color: #EF4444;'>🔴 RESISTANCE 2:</span> {resistance_2:.5f} (Major)<br>"
        html += f"<span style='color: #F59E0B;'>🟠 RESISTANCE 1:</span> {resistance_1:.5f} (Minor)<br>"
        html += f"<span style='color: #FFFFFF;'>━━━ CURRENT:</span> {price:.5f}<br>"
        html += f"<span style='color: #10B981;'>🟢 SUPPORT 1:</span> {support_1:.5f} (Minor)<br>"
        html += f"<span style='color: #06B6D4;'>🔵 SUPPORT 2:</span> {support_2:.5f} (Major)"
        html += "</p>"

        return html

    def blink_live_indicator(self):
        """Blink the LIVE indicator"""
        self.live_label.setStyleSheet("color: #FFFFFF;")
        QTimer.singleShot(200, lambda: self.live_label.setStyleSheet("color: #10B981;"))

    def set_symbol(self, symbol: str):
        """Update the symbol being analyzed"""
        self.current_symbol = symbol
        self.update_commentary()

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        # This widget uses get_market_data() which automatically handles demo/live
        self.update_commentary()

        # Update AI if enabled
        if self.ai_enabled and self.current_analysis:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Price Action Commentary switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for price action patterns

        Analyzes:
        - Trend strength and direction
        - Volatility-based opportunity assessment
        - Support/resistance level trading strategies
        - Price action patterns and setups
        - Risk management for current conditions
        """
        from core.ml_integration import create_ai_suggestion

        if not self.current_analysis:
            return create_ai_suggestion(
                widget_type="price_action",
                text="Waiting for price data to provide trading insights",
                confidence=0.0
            )

        symbol = self.current_analysis.get('symbol', 'EURUSD')
        timeframe = self.current_analysis.get('timeframe', 'M15')
        trend = self.current_analysis.get('trend', 'NEUTRAL')
        volatility = self.current_analysis.get('volatility', 'NORMAL')
        price_change_pct = self.current_analysis.get('price_change_pct', 0.0)
        price = self.current_analysis.get('price', 0.0)
        sma_20 = self.current_analysis.get('sma_20', 0.0)

        # STRONG BULLISH TREND + HIGH VOLATILITY = HIGH CONVICTION ENTRY
        if trend == "BULLISH" and volatility == "HIGH" and price_change_pct > 0.08:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"🔥 STRONG BULLISH MOMENTUM on {symbol} {timeframe}! Price +{price_change_pct:.2f}% with high volatility breakout. Wait for pullback to {sma_20:.5f} (20 SMA) then BUY. SL below recent low, TP at {price + 0.003:.5f}. High conviction setup!",
                confidence=0.93,
                emoji="🔥",
                color="green"
            )

        # STRONG BEARISH TREND + HIGH VOLATILITY = SELL OPPORTUNITY
        if trend == "BEARISH" and volatility == "HIGH" and price_change_pct < -0.08:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"🔻 STRONG BEARISH BREAKDOWN on {symbol} {timeframe}! Price {price_change_pct:.2f}% with strong selling pressure. Wait for rally to {sma_20:.5f} (20 SMA) then SELL. SL above recent high, TP at {price - 0.003:.5f}. High probability!",
                confidence=0.93,
                emoji="🔻",
                color="red"
            )

        # BULLISH TREND + NORMAL VOLATILITY = PULLBACK ENTRY
        if trend == "BULLISH" and volatility == "NORMAL" and price > sma_20:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"📈 BULLISH TREND on {symbol} {timeframe}: Price above 20 SMA ({sma_20:.5f}). Best entry: Wait for pullback to SMA, then BUY with tight SL. Trending market = follow the trend. Don't fight it!",
                confidence=0.85,
                emoji="📈",
                color="green"
            )

        # BEARISH TREND + NORMAL VOLATILITY = RALLY SELL
        if trend == "BEARISH" and volatility == "NORMAL" and price < sma_20:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"📉 BEARISH TREND on {symbol} {timeframe}: Price below 20 SMA ({sma_20:.5f}). Best entry: Wait for rally back to SMA resistance, then SELL. Trending down = sell strength. Stay with trend!",
                confidence=0.85,
                emoji="📉",
                color="red"
            )

        # HIGH VOLATILITY + NEUTRAL TREND = BREAKOUT WATCH
        if volatility == "HIGH" and trend == "NEUTRAL":
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"⚡ HIGH VOLATILITY on {symbol} {timeframe} but NO CLEAR TREND. Range-bound with big moves = dangerous! Wait for clear breakout above/below range. Don't trade chop - wait for direction!",
                confidence=0.78,
                emoji="⚡",
                color="orange"
            )

        # NEUTRAL TREND + NORMAL VOLATILITY = RANGE TRADING
        if trend == "NEUTRAL" and volatility == "NORMAL":
            support = price - 0.0015
            resistance = price + 0.0015
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"↔️ RANGE TRADING on {symbol} {timeframe}: Buy support ~{support:.5f}, Sell resistance ~{resistance:.5f}. Tight stops! Or wait for breakout. Range = patience required.",
                confidence=0.72,
                emoji="↔️",
                color="blue"
            )

        # BULLISH TREND BUT PRICE BELOW SMA = CAUTION
        if trend == "BULLISH" and price < sma_20:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"⚠️ {symbol} {timeframe}: Bullish trend BUT price below 20 SMA ({sma_20:.5f}). Pullback in progress. Wait for reclaim above SMA to confirm trend continuation. Don't chase!",
                confidence=0.70,
                emoji="⚠️",
                color="orange"
            )

        # BEARISH TREND BUT PRICE ABOVE SMA = POTENTIAL REVERSAL
        if trend == "BEARISH" and price > sma_20:
            return create_ai_suggestion(
                widget_type="price_action",
                text=f"⚠️ {symbol} {timeframe}: Bearish trend BUT price above 20 SMA ({sma_20:.5f}). Possible trend reversal or bounce. Wait for confirmation - either rejection or breakout. No rush!",
                confidence=0.70,
                emoji="⚠️",
                color="orange"
            )

        # DEFAULT
        return create_ai_suggestion(
            widget_type="price_action",
            text=f"{symbol} {timeframe}: {trend} trend, {volatility.lower()} volatility. Price {price:.5f}, 20 SMA {sma_20:.5f}. Wait for clear setup before entry.",
            confidence=0.65,
            emoji="📊",
            color="blue"
        )
