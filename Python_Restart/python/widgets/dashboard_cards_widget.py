"""
AppleTrader Pro - Dashboard Summary Cards with AI Integration
Displays key metrics and actionable AI scenarios at the top of the interface
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from typing import Dict

from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import is_demo_mode, get_demo_data
from core.data_manager import data_manager
import random


class DashboardCard(QFrame):
    """Individual dashboard card widget"""

    def __init__(self, title: str, icon: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border: 1px solid #3B82F6;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame:hover {
                border: 1px solid #60A5FA;
                background-color: #242438;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 6, 8, 6)

        # Title with icon
        title_label = QLabel(f"{icon} {title}")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #3B82F6; border: none; padding: 0;")
        layout.addWidget(title_label)

        # Main value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #ffffff; border: none; padding: 2px 0;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(False)
        layout.addWidget(self.value_label)

        # Subtitle
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(QFont("Arial", 9))
        self.subtitle_label.setStyleSheet("color: #aaaaaa; border: none; padding: 0; line-height: 1.2;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)  # Allow wrapping for long text
        self.subtitle_label.setMaximumHeight(35)  # Limit height to prevent overflow
        layout.addWidget(self.subtitle_label)

    def update_value(self, value: str, subtitle: str = "", color: str = "#ffffff"):
        """Update card value and subtitle"""
        self.value_label.setText(value)
        self.value_label.setStyleSheet(f"color: {color}; border: none; padding: 2px 0; font-weight: bold;")
        self.subtitle_label.setText(subtitle)
        # Ensure subtitle stays visible with proper color
        self.subtitle_label.setStyleSheet("color: #aaaaaa; border: none; padding: 0; line-height: 1.2;")


class DashboardCardsWidget(AIAssistMixin, QWidget):
    """
    Dashboard Summary Cards with AI Integration

    Displays 4 key metric cards at the top with AI-powered actionable insights:
    - Account Status (Balance, P&L, Win Rate)
    - Market Condition (Trend, Volatility, Session)
    - Risk Status (Exposure, Margin, Drawdown)
    - AI Scenario (Next best action)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_symbol = "EURUSD"
        self.current_data = None  # Store current dashboard data for AI

        self.init_ui()
        self.setup_ai_assist("dashboard_cards")

        # Connect to mode changes
        from core.demo_mode_manager import demo_mode_manager
        demo_mode_manager.mode_changed.connect(self.on_mode_changed)

        # Auto-refresh timer (every 2 seconds)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(2000)

        # Initial update
        self.update_data()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        # Card 1: Account Status
        self.account_card = DashboardCard("Account", "💰")
        cards_layout.addWidget(self.account_card)

        # Card 2: Market Condition
        self.market_card = DashboardCard("Market", "📊")
        cards_layout.addWidget(self.market_card)

        # Card 3: Risk Status
        self.risk_card = DashboardCard("Risk", "🛡️")
        cards_layout.addWidget(self.risk_card)

        # Card 4: AI Scenario
        self.scenario_card = DashboardCard("AI Action (Account)", "🤖")
        cards_layout.addWidget(self.scenario_card)

        # AI checkbox placeholder (placed after cards)
        self.ai_checkbox_placeholder = cards_layout

        layout.addLayout(cards_layout)

        # AI suggestion placeholder
        self.ai_suggestion_placeholder = layout

    def set_symbol(self, symbol: str):
        """Update current symbol"""
        self.current_symbol = symbol
        self.update_data()

    def update_data(self):
        """Update all cards with current data"""
        if is_demo_mode():
            self.load_demo_data()
        else:
            self.load_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_data:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Dashboard Cards switching to {mode_text} mode")
        self.update_data()

    def load_demo_data(self):
        """Load demo data for cards"""
        # Account card
        balance = 10000 + random.uniform(-500, 1500)
        pnl = random.uniform(-300, 500)
        pnl_pct = (pnl / balance) * 100
        win_rate = random.uniform(45, 65)

        pnl_color = "#00ff00" if pnl >= 0 else "#ff0000"
        self.account_card.update_value(
            f"${balance:,.0f}",
            f"P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%) | WR: {win_rate:.0f}%",
            "#00aaff"
        )

        # Market card
        trends = ["BULLISH", "BEARISH", "NEUTRAL"]
        trend = random.choice(trends)
        volatility = random.choice(["HIGH", "NORMAL", "LOW"])
        sessions = ["Asian", "London", "New York"]
        session = random.choice(sessions)

        trend_color = "#00ff00" if trend == "BULLISH" else "#ff0000" if trend == "BEARISH" else "#ffaa00"
        self.market_card.update_value(
            trend,
            f"{volatility} Vol | {session} Session",
            trend_color
        )

        # Risk card
        exposure = random.uniform(1.0, 5.0)
        margin_used = random.uniform(10, 40)
        drawdown = random.uniform(0, 8)

        risk_color = "#00ff00" if exposure < 2.0 else "#ffaa00" if exposure < 3.5 else "#ff0000"
        self.risk_card.update_value(
            f"{exposure:.1f}%",
            f"Margin: {margin_used:.0f}% | DD: {drawdown:.1f}%",
            risk_color
        )

        # AI Scenario card
        scenarios = [
            ("WAIT", "No clear setup", "#ffaa00"),
            ("BUY DIP", "Pullback expected", "#00ff00"),
            ("SELL RALLY", "Resistance ahead", "#ff0000"),
            ("BREAKOUT", "Range breaking", "#00aaff"),
            ("REDUCE", "High risk", "#ff6600")
        ]
        action, reason, color = random.choice(scenarios)
        self.scenario_card.update_value(action, reason, color)

        # Store for AI analysis
        self.current_data = {
            'balance': balance,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'win_rate': win_rate,
            'trend': trend,
            'volatility': volatility,
            'session': session,
            'exposure': exposure,
            'margin_used': margin_used,
            'drawdown': drawdown,
            'scenario_action': action
        }

    def load_live_data(self):
        """Load live MT5 account data"""
        from core.market_analyzer import market_analyzer

        # Get real account data from data_manager
        account = data_manager.get_account_summary()
        market_state = data_manager.get_market_state()

        # Account card - REAL DATA
        balance = account.get('balance', 0)
        equity = account.get('equity', 0)
        profit = account.get('profit', 0)
        daily_pnl = account.get('daily_pnl', 0)

        pnl_pct = (daily_pnl / balance * 100) if balance > 0 else 0
        win_rate = 0  # TODO: Calculate from trade history

        pnl_color = "#00ff00" if daily_pnl >= 0 else "#ff0000"
        self.account_card.update_value(
            f"${balance:,.2f}",
            f"P&L: ${daily_pnl:+.2f} ({pnl_pct:+.1f}%) | Equity: ${equity:,.2f}",
            "#00aaff"
        )

        # Market card - REAL DATA with DIRECT session detection
        trend = market_state.get('bias', 'NEUTRAL')

        # Get REAL-TIME session directly from market_analyzer
        raw_session = market_analyzer.get_current_session()
        session_map = {
            'london_ny_overlap': 'London/NY',
            'london': 'London',
            'newyork': 'New York',
            'asian': 'Asian',
            'dead': 'Dead Zone'
        }
        session = session_map.get(raw_session, 'Unknown')

        # Calculate volatility status (HIGH/NORMAL/LOW)
        # Get current symbol from data_manager
        current_symbol = data_manager.current_price.get('symbol', 'EURUSD')
        try:
            current_atr = market_analyzer.calculate_atr(current_symbol, 'H1', period=14)
            avg_atr = market_analyzer.calculate_atr(current_symbol, 'H1', period=50)

            if current_atr > (avg_atr * 1.5):
                volatility = "HIGH"
            elif current_atr > (avg_atr * 0.8):
                volatility = "NORMAL"
            else:
                volatility = "LOW"
        except:
            # Fallback to data_manager value if calculation fails
            volatility = market_state.get('volatility', 'NORMAL')

        trend_color = "#00ff00" if trend == "BULLISH" else "#ff0000" if trend == "BEARISH" else "#ffaa00"
        self.market_card.update_value(
            trend,
            f"{volatility} Vol | {session} Session",
            trend_color
        )

        # Risk card - REAL DATA
        margin_level = account.get('margin_level', 0)
        margin_used_pct = 100 - margin_level if margin_level > 0 else 0

        # Calculate drawdown
        drawdown = 0
        if balance > 0 and equity < balance:
            drawdown = ((balance - equity) / balance) * 100

        exposure = abs(profit / balance * 100) if balance > 0 else 0

        risk_color = "#00ff00" if drawdown < 5.0 else "#ffaa00" if drawdown < 10.0 else "#ff0000"
        self.risk_card.update_value(
            f"{drawdown:.1f}%",
            f"Exposure: {exposure:.1f}% | Margin: {margin_used_pct:.0f}%",
            risk_color
        )

        # AI Scenario card - Based on real data
        if drawdown >= 10.0:
            action, reason, color = "STOP", "High drawdown!", "#ff0000"
        elif daily_pnl < -100:
            action, reason, color = "REDUCE", "Daily loss limit", "#ff6600"
        elif trend == "BULLISH" and volatility == "HIGH":
            action, reason, color = "BUY DIP", "Strong trend", "#00ff00"
        elif trend == "BEARISH" and volatility == "HIGH":
            action, reason, color = "SELL RALLY", "Strong trend", "#ff0000"
        else:
            action, reason, color = "WAIT", "No clear setup", "#ffaa00"

        self.scenario_card.update_value(action, reason, color)

        # Store for AI analysis (with corrected session data)
        self.current_data = {
            'balance': balance,
            'equity': equity,
            'pnl': daily_pnl,
            'pnl_pct': pnl_pct,
            'win_rate': win_rate,
            'trend': trend,
            'volatility': volatility,
            'session': session,  # Now uses real-time session from market_analyzer
            'raw_session': raw_session,  # Store raw session for logic
            'exposure': exposure,
            'margin_used': margin_used_pct,
            'drawdown': drawdown,
            'scenario_action': action
        }

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for dashboard metrics

        Analyzes:
        - Overall account health
        - Market condition opportunities
        - Risk management recommendations
        - Actionable next steps
        """
        from core.ml_integration import create_ai_suggestion

        if not self.current_data:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text="Loading dashboard data for AI analysis...",
                confidence=0.0
            )

        pnl_pct = self.current_data.get('pnl_pct', 0)
        win_rate = self.current_data.get('win_rate', 0)
        trend = self.current_data.get('trend', 'NEUTRAL')
        volatility = self.current_data.get('volatility', 'NORMAL')
        exposure = self.current_data.get('exposure', 0)
        drawdown = self.current_data.get('drawdown', 0)

        # CRITICAL: High drawdown situation
        if drawdown >= 10.0:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"🚨 CRITICAL: {drawdown:.1f}% drawdown! STOP TRADING. Review strategy. Reduce position sizes by 75% when you resume. Take a break!",
                confidence=0.98,
                emoji="🚨",
                color="red"
            )

        # WARNING: Excessive exposure
        if exposure >= 4.0:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"⚠️ OVEREXPOSED: {exposure:.1f}% risk! Close weakest positions NOW. Maximum should be 3%. You're risking account blow-up!",
                confidence=0.95,
                emoji="⚠️",
                color="orange"
            )

        # STRONG PERFORMANCE: Capitalize
        if pnl_pct > 3.0 and win_rate >= 60:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"🔥 EXCELLENT DAY: +{pnl_pct:.1f}%, {win_rate:.0f}% WR! You're in the zone. Keep discipline. Don't overtrade. Lock profits if hit daily target!",
                confidence=0.90,
                emoji="🔥",
                color="green"
            )

        # OPPORTUNITY: Trending market + good stats
        if trend in ["BULLISH", "BEARISH"] and volatility == "NORMAL" and exposure < 2.5:
            direction = "LONG" if trend == "BULLISH" else "SHORT"
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"📈 TRENDING MARKET: {trend} with normal volatility. Look for {direction} pullback entries. Low exposure ({exposure:.1f}%) = room to add quality trades.",
                confidence=0.85,
                emoji="📈",
                color="green"
            )

        # CAUTION: High volatility
        if volatility == "HIGH" and exposure > 2.0:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"⚡ HIGH VOLATILITY + {exposure:.1f}% exposure! Tighten stops. Reduce size by 50%. News or event-driven moves = dangerous!",
                confidence=0.82,
                emoji="⚡",
                color="orange"
            )

        # STRUGGLING: Losing day
        if pnl_pct < -2.0 or win_rate < 40:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"📉 TOUGH DAY: {pnl_pct:+.1f}%, {win_rate:.0f}% WR. STOP trading for today. Don't revenge trade. Review what went wrong. Come back fresh tomorrow!",
                confidence=0.88,
                emoji="📉",
                color="red"
            )

        # MODERATE DRAWDOWN: Caution
        if 5.0 <= drawdown < 10.0:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"⚠️ DRAWDOWN: {drawdown:.1f}%. Reduce position sizes by 50%. Focus on BEST setups only. No revenge trading. Recover slowly!",
                confidence=0.80,
                emoji="⚠️",
                color="orange"
            )

        # NEUTRAL MARKET: Patience
        if trend == "NEUTRAL" and volatility == "LOW":
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text="↔️ CHOPPY MARKET: Neutral trend, low volatility. Avoid trading chop. Wait for breakout or clear direction. Patience pays!",
                confidence=0.75,
                emoji="↔️",
                color="blue"
            )

        # GOOD SESSION: Maintain discipline
        if 0.5 <= pnl_pct <= 2.5 and 50 <= win_rate <= 60:
            return create_ai_suggestion(
                widget_type="dashboard_cards",
                text=f"✓ SOLID SESSION: +{pnl_pct:.1f}%, {win_rate:.0f}% WR. Good discipline! Stay consistent. Don't chase. Stick to your plan!",
                confidence=0.70,
                emoji="✓",
                color="green"
            )

        # DEFAULT
        return create_ai_suggestion(
            widget_type="dashboard_cards",
            text=f"Dashboard: {pnl_pct:+.1f}% P&L, {win_rate:.0f}% WR, {exposure:.1f}% risk, {trend} market. Monitor conditions and stay disciplined.",
            confidence=0.65,
            emoji="📊",
            color="blue"
        )
