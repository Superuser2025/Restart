"""
AppleTrader Pro - Trade Journal Widget
PyQt6 widget for displaying automated trade journal with AI insights
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QListWidget, QListWidgetItem,
                            QPushButton, QTextEdit, QFrame, QTabWidget, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List

from widgets.trade_journal import (trade_journal, TradeJournalEntry,
                                   TradeSetupType)
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data


class TradeJournalWidget(AIAssistMixin, QWidget):
    """
    Automated Trade Journal Display Widget

    Shows:
    - Recent trade entries
    - Performance analysis by setup/session/day
    - Strengths and weaknesses
    - AI-powered insights
    - Personalized recommendations
    - Weekly summary
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # CRITICAL: Initialize current_symbol BEFORE calling update_from_live_data
        self.current_symbol = "EURUSD"
        self.current_journal_analysis = None  # Store for AI

        self.init_ui()
        self.setup_ai_assist("trade_journal")

        # Auto-refresh every 5 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(5000)

        # Initial update
        self.update_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("📝 Automated Trade Journal")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()
        self.ai_checkbox_placeholder = header_layout

        # Export button
        self.export_btn = QPushButton("💾 Export CSV")
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.export_btn.setMaximumWidth(120)
        header_layout.addWidget(self.export_btn)

        layout.addLayout(header_layout)

        # === TABS ===
        tabs = QTabWidget()

        # Tab 1: Recent Trades
        trades_tab = self.create_trades_tab()
        tabs.addTab(trades_tab, "Recent Trades")

        # Tab 2: Analysis
        analysis_tab = self.create_analysis_tab()
        tabs.addTab(analysis_tab, "Analysis")

        # Tab 3: Insights
        insights_tab = self.create_insights_tab()
        tabs.addTab(insights_tab, "AI Insights")

        layout.addWidget(tabs)

        # AI suggestion frame placeholder
        self.ai_suggestion_placeholder = layout

        # Apply dark theme
        self.apply_dark_theme()

    def create_trades_tab(self) -> QWidget:
        """Create recent trades tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Weekly summary
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a3a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        # Trades
        trades_col = QVBoxLayout()
        trades_col.addWidget(QLabel("Trades (7d)"))
        self.weekly_trades_label = QLabel("0")
        self.weekly_trades_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.weekly_trades_label.setStyleSheet("color: #00aaff; border: none;")
        trades_col.addWidget(self.weekly_trades_label)
        summary_layout.addLayout(trades_col)

        # Win rate
        winrate_col = QVBoxLayout()
        winrate_col.addWidget(QLabel("Win Rate"))
        self.weekly_winrate_label = QLabel("0%")
        self.weekly_winrate_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.weekly_winrate_label.setStyleSheet("color: #00ff00; border: none;")
        winrate_col.addWidget(self.weekly_winrate_label)
        summary_layout.addLayout(winrate_col)

        # Profit
        profit_col = QVBoxLayout()
        profit_col.addWidget(QLabel("Profit"))
        self.weekly_profit_label = QLabel("$0")
        self.weekly_profit_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.weekly_profit_label.setStyleSheet("color: #00ff00; border: none;")
        profit_col.addWidget(self.weekly_profit_label)
        summary_layout.addLayout(profit_col)

        layout.addWidget(summary_frame)

        # Trades list
        self.trades_list = QListWidget()
        self.trades_list.setFont(QFont("Courier", 9))
        self.trades_list.itemClicked.connect(self.on_trade_clicked)
        layout.addWidget(self.trades_list)

        return widget

    def create_analysis_tab(self) -> QWidget:
        """Create analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # By setup
        setup_group = QGroupBox("📊 Performance by Setup Type")
        setup_layout = QVBoxLayout()

        self.setup_text = QTextEdit()
        self.setup_text.setReadOnly(True)
        self.setup_text.setMaximumHeight(150)
        self.setup_text.setFont(QFont("Courier", 9))
        setup_layout.addWidget(self.setup_text)

        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        # By session
        session_group = QGroupBox("⏰ Performance by Session")
        session_layout = QVBoxLayout()

        self.session_text = QTextEdit()
        self.session_text.setReadOnly(True)
        self.session_text.setMaximumHeight(100)
        self.session_text.setFont(QFont("Courier", 9))
        session_layout.addWidget(self.session_text)

        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        # By day
        day_group = QGroupBox("📅 Performance by Day of Week")
        day_layout = QVBoxLayout()

        self.day_text = QTextEdit()
        self.day_text.setReadOnly(True)
        self.day_text.setMaximumHeight(100)
        self.day_text.setFont(QFont("Courier", 9))
        day_layout.addWidget(self.day_text)

        day_group.setLayout(day_layout)
        layout.addWidget(day_group)

        layout.addStretch()

        return widget

    def create_insights_tab(self) -> QWidget:
        """Create insights tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Strengths
        strengths_group = QGroupBox("🎯 Your Strengths")
        strengths_layout = QVBoxLayout()

        self.strengths_text = QTextEdit()
        self.strengths_text.setReadOnly(True)
        self.strengths_text.setMaximumHeight(120)
        self.strengths_text.setFont(QFont("Courier", 9))
        self.strengths_text.setStyleSheet("color: #00ff00;")
        strengths_layout.addWidget(self.strengths_text)

        strengths_group.setLayout(strengths_layout)
        layout.addWidget(strengths_group)

        # Weaknesses
        weaknesses_group = QGroupBox("⚠️ Areas to Improve")
        weaknesses_layout = QVBoxLayout()

        self.weaknesses_text = QTextEdit()
        self.weaknesses_text.setReadOnly(True)
        self.weaknesses_text.setMaximumHeight(120)
        self.weaknesses_text.setFont(QFont("Courier", 9))
        self.weaknesses_text.setStyleSheet("color: #ff6600;")
        weaknesses_layout.addWidget(self.weaknesses_text)

        weaknesses_group.setLayout(weaknesses_layout)
        layout.addWidget(weaknesses_group)

        # AI Insights
        ai_group = QGroupBox("🤖 AI Insights")
        ai_layout = QVBoxLayout()

        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setMaximumHeight(100)
        self.ai_text.setFont(QFont("Courier", 9))
        ai_layout.addWidget(self.ai_text)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Recommendations
        rec_group = QGroupBox("💡 Personalized Recommendations")
        rec_layout = QVBoxLayout()

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setMaximumHeight(100)
        self.recommendations_text.setFont(QFont("Courier", 9))
        self.recommendations_text.setStyleSheet("color: #ffaa00;")
        rec_layout.addWidget(self.recommendations_text)

        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

        layout.addStretch()

        return widget

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
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #444;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
            }
        """)

    def set_symbol(self, symbol: str):
        """Update the current symbol and refresh display"""
        self.current_symbol = symbol
        self.update_from_live_data()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager
        symbol = self.current_symbol
        # Trade journal data is managed internally, just refresh display
        self.refresh_display()

    def load_sample_data(self):
        """Load sample trades for demonstration"""
        from datetime import timedelta

        # Add 12 sample journal entries over the last 7 days
        base_time = datetime.now() - timedelta(days=7)

        sample_trades = [
            ('EURUSD', TradeSetupType.BULLISH_OB, 'BUY', 1.10000, 1.10200, 1.09800, 1.10300, 0.1, 200, 20, 2.0),
            ('GBPUSD', TradeSetupType.FVG_LONG, 'BUY', 1.26500, 1.26650, 1.26350, 1.26800, 0.1, 150, 15, 1.5),
            ('USDJPY', TradeSetupType.LIQUIDITY_SWEEP, 'BUY', 148.500, 148.700, 148.300, 148.900, 0.1, 200, 20, 2.0),
            ('EURUSD', TradeSetupType.BEARISH_OB, 'SELL', 1.10200, 1.10350, 1.09900, 1.10400, 0.1, -150, -15, -1.5),  # Loss
            ('AUDUSD', TradeSetupType.TREND_CONTINUATION, 'BUY', 0.66000, 0.66120, 0.65900, 0.66200, 0.1, 120, 12, 1.2),
            ('EURUSD', TradeSetupType.BULLISH_OB, 'BUY', 1.10100, 1.10280, 1.09900, 1.10400, 0.1, 180, 18, 1.8),
            ('GBPUSD', TradeSetupType.FVG_SHORT, 'SELL', 1.26300, 1.26250, 1.26100, 1.26450, 0.1, -50, -5, -0.5),  # Loss
            ('USDJPY', TradeSetupType.REVERSAL, 'SELL', 149.000, 148.800, 148.600, 149.200, 0.1, 200, 20, 2.0),
            ('EURUSD', TradeSetupType.BULLISH_OB, 'BUY', 1.10050, 1.10200, 1.09850, 1.10350, 0.1, 150, 15, 1.5),
            ('NZDUSD', TradeSetupType.BREAKOUT, 'BUY', 0.61000, 0.61080, 0.60920, 0.61180, 0.1, 80, 8, 0.8),
            ('EURUSD', TradeSetupType.FVG_SHORT, 'SELL', 1.10300, 1.10450, 1.10050, 1.10550, 0.1, -150, -15, -1.5),  # Loss
            ('GBPUSD', TradeSetupType.TREND_CONTINUATION, 'BUY', 1.26400, 1.26550, 1.26250, 1.26700, 0.1, 150, 15, 1.5),
        ]

        for i, (symbol, setup, direction, entry, exit, sl, tp, lots, profit, pips, r_mult) in enumerate(sample_trades):
            entry_time = base_time + timedelta(hours=i*12)
            exit_time = entry_time + timedelta(hours=3)

            trade_journal.add_trade(
                symbol, setup, direction, entry, exit, sl, tp, lots,
                entry_time, exit_time, profit, pips, r_mult
            )

    def refresh_display(self):
        """Refresh all displays with current data"""
        # Get analysis
        analysis = trade_journal.analyze_performance()

        # Update weekly summary
        weekly = trade_journal.get_weekly_summary()
        self.weekly_trades_label.setText(str(weekly['trades']))
        self.weekly_winrate_label.setText(f"{weekly['win_rate']:.0f}%")

        profit = weekly['profit']
        profit_color = '#00ff00' if profit >= 0 else '#ff0000'
        self.weekly_profit_label.setText(f"${profit:+.2f}")
        self.weekly_profit_label.setStyleSheet(f"color: {profit_color}; border: none;")

        # Store analysis data for AI
        self.current_journal_analysis = {
            'best_setup': self._get_best_setup(analysis.get('by_setup', {})),
            'worst_setup': self._get_worst_setup(analysis.get('by_setup', {})),
            'best_session': self._get_best_session(analysis.get('by_session', {})),
            'total_trades': weekly.get('trades', 0),
            'win_rate': weekly.get('win_rate', 0.0),
            'avg_rr': analysis.get('avg_r_multiple', 0.0),
            'trades_today': self._count_trades_today()
        }

        # Update trades list
        self.trades_list.clear()
        recent_trades = trade_journal.get_recent_trades(20)

        for trade in recent_trades:
            emoji = '✓' if trade.is_win else '✗'
            profit_str = f"+${trade.profit:.2f}" if trade.is_win else f"-${abs(trade.profit):.2f}"

            item_text = (f"#{trade.trade_id:03d} {emoji} {trade.symbol} {trade.direction} "
                        f"[{trade.r_multiple:+.2f}R] {profit_str}")

            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, trade)

            # Color code
            if trade.is_win:
                list_item.setForeground(QColor('#00ff00'))
            else:
                list_item.setForeground(QColor('#ff6600'))

            self.trades_list.addItem(list_item)

        # Update analysis
        self.update_analysis_displays(analysis)

        # Update AI if enabled
        if self.ai_enabled and self.current_journal_analysis:
            self.update_ai_suggestions()

    def _get_best_setup(self, by_setup: Dict) -> Dict:
        """Extract best performing setup"""
        if not by_setup:
            return {}
        best = max(by_setup.items(), key=lambda x: x[1]['win_rate'])
        return {
            'name': best[0],
            'win_rate': best[1]['win_rate'],
            'count': best[1]['total_trades']
        }

    def _get_worst_setup(self, by_setup: Dict) -> Dict:
        """Extract worst performing setup"""
        if not by_setup:
            return {}
        worst = min(by_setup.items(), key=lambda x: x[1]['win_rate'])
        return {
            'name': worst[0],
            'win_rate': worst[1]['win_rate'],
            'count': worst[1]['total_trades'],
            'total_loss': worst[1].get('total_profit', 0)  # Negative for losses
        }

    def _get_best_session(self, by_session: Dict) -> Dict:
        """Extract best performing session"""
        if not by_session:
            return {}
        best = max(by_session.items(), key=lambda x: x[1].get('profit', 0))
        return {
            'name': best[0],
            'profit': best[1].get('profit', 0),
            'win_rate': best[1]['win_rate']
        }

    def _count_trades_today(self) -> int:
        """Count trades executed today"""
        from datetime import datetime, date
        today = date.today()
        recent_trades = trade_journal.get_recent_trades(100)
        count = sum(1 for t in recent_trades if t.entry_time.date() == today)
        return count

    def update_analysis_displays(self, analysis: Dict):
        """Update analysis tab displays"""
        # By setup
        if analysis['by_setup']:
            setup_lines = []
            for setup, stats in sorted(analysis['by_setup'].items(),
                                      key=lambda x: x[1]['win_rate'],
                                      reverse=True):
                setup_lines.append(
                    f"{setup}: {stats['wins']}/{stats['total_trades']} "
                    f"({stats['win_rate']:.0f}%) | {stats['avg_r']:.2f}R"
                )
            self.setup_text.setPlainText('\n'.join(setup_lines))
        else:
            self.setup_text.setPlainText("No data yet")

        # By session
        if analysis['by_session']:
            session_lines = []
            for session, stats in sorted(analysis['by_session'].items(),
                                        key=lambda x: x[1]['win_rate'],
                                        reverse=True):
                session_lines.append(
                    f"{session}: {stats['wins']}/{stats['total_trades']} "
                    f"({stats['win_rate']:.0f}%)"
                )
            self.session_text.setPlainText('\n'.join(session_lines))
        else:
            self.session_text.setPlainText("No data yet")

        # By day
        if analysis['by_day']:
            # Order days properly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            day_lines = []

            for day in day_order:
                if day in analysis['by_day']:
                    stats = analysis['by_day'][day]
                    day_lines.append(
                        f"{day}: {stats['wins']}/{stats['total_trades']} "
                        f"({stats['win_rate']:.0f}%)"
                    )

            self.day_text.setPlainText('\n'.join(day_lines))
        else:
            self.day_text.setPlainText("No data yet")

        # Strengths, weaknesses, insights, recommendations
        self.strengths_text.setPlainText('\n'.join(analysis['strengths']))
        self.weaknesses_text.setPlainText('\n'.join(analysis['weaknesses']))
        self.ai_text.setPlainText('\n'.join(analysis['ai_insights']))
        self.recommendations_text.setPlainText('\n'.join(analysis['recommendations']))

    def on_trade_clicked(self, item):
        """Handle trade click to show details"""
        trade = item.data(Qt.ItemDataRole.UserRole)

        if trade:
            # Could show a detailed popup or update a details panel
            pass

    def on_export_clicked(self):
        """Handle export button click"""
        filename = f"trade_journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        trade_journal.export_to_csv(filename)
        # Could show a success message

    def clear_display(self):
        """Clear all displays"""
        self.trades_list.clear()
        self.setup_text.setPlainText("No data")
        self.session_text.setPlainText("No data")
        self.day_text.setPlainText("No data")
        self.strengths_text.setPlainText("No data")
        self.weaknesses_text.setPlainText("No data")
        self.ai_text.setPlainText("No data")
        self.recommendations_text.setPlainText("No data")

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # Load demo journal data
            self.load_sample_data()
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_journal_analysis:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Trade Journal switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for trade journal patterns

        Analyzes:
        - Best/worst setup types
        - Session performance patterns
        - Overtrading tendencies
        - Consistency and discipline
        - Behavioral patterns and biases
        """
        from core.ml_integration import create_ai_suggestion

        if not self.current_journal_analysis:
            return create_ai_suggestion(
                widget_type="trade_journal",
                text="Record trades to get AI coaching insights",
                confidence=0.0
            )

        # Extract metrics
        best_setup = self.current_journal_analysis.get('best_setup', {})
        worst_setup = self.current_journal_analysis.get('worst_setup', {})
        best_session = self.current_journal_analysis.get('best_session', {})
        total_trades = self.current_journal_analysis.get('total_trades', 0)
        win_rate = self.current_journal_analysis.get('win_rate', 0.0)
        avg_rr = self.current_journal_analysis.get('avg_rr', 0.0)
        trades_today = self.current_journal_analysis.get('trades_today', 0)

        # OVERTRADING ALERT
        if trades_today >= 8:
            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"⚠️ OVERTRADING: {trades_today} trades today! Quality > Quantity. You're forcing trades. Stop for today - you've done enough.",
                confidence=0.92,
                emoji="⚠️",
                color="orange"
            )

        # EXCELLENT PERFORMANCE PATTERN
        if best_setup and best_setup.get('win_rate', 0) >= 70.0 and best_setup.get('count', 0) >= 10:
            setup_name = best_setup.get('name', 'Unknown')
            setup_wr = best_setup.get('win_rate', 0)
            setup_count = best_setup.get('count', 0)

            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"🔥 EDGE IDENTIFIED: {setup_name} setup = {setup_wr:.0f}% win rate ({setup_count} trades)! This is your A+ setup. ONLY trade this setup for next week. Ignore everything else!",
                confidence=0.90,
                emoji="🔥",
                color="green"
            )

        # MAJOR WEAKNESS DETECTED
        if worst_setup and worst_setup.get('win_rate', 100) < 30.0 and worst_setup.get('count', 0) >= 5:
            setup_name = worst_setup.get('name', 'Unknown')
            setup_wr = worst_setup.get('win_rate', 0)
            setup_loss = worst_setup.get('total_loss', 0)

            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"🛑 STOP TRADING {setup_name}: Only {setup_wr:.0f}% win rate, ${setup_loss:.0f} lost! This setup is costing you money. BAN it from your strategy immediately!",
                confidence=0.95,
                emoji="🛑",
                color="red"
            )

        # SESSION PATTERN INSIGHT
        if best_session and best_session.get('profit', 0) > 0:
            session_name = best_session.get('name', 'Unknown')
            session_profit = best_session.get('profit', 0)
            session_wr = best_session.get('win_rate', 0)

            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"✓ BEST SESSION: {session_name} - ${session_profit:.0f} profit, {session_wr:.0f}% WR. Focus trading during this session only. Avoid other times.",
                confidence=0.85,
                emoji="✓",
                color="green"
            )

        # GOOD CONSISTENCY
        if total_trades >= 20 and 52.0 <= win_rate <= 58.0 and avg_rr >= 1.8:
            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"📈 SOLID CONSISTENCY: {total_trades} trades, {win_rate:.0f}% WR, {avg_rr:.1f}R avg. You're trading like a pro! Keep this exact routine.",
                confidence=0.82,
                emoji="📈",
                color="green"
            )

        # INCONSISTENT RESULTS
        if total_trades >= 15 and (win_rate < 45.0 or avg_rr < 1.2):
            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"📉 STRUGGLING: {win_rate:.0f}% WR, {avg_rr:.1f}R avg after {total_trades} trades. Strategy needs work. Reduce size to 0.25% per trade while you fix your edge.",
                confidence=0.80,
                emoji="📉",
                color="orange"
            )

        # EARLY STAGE
        if total_trades < 10:
            return create_ai_suggestion(
                widget_type="trade_journal",
                text=f"📊 BUILDING DATA: {total_trades} trades logged. Keep journaling every trade! Need 20+ trades to identify real patterns. Stay patient.",
                confidence=0.72,
                emoji="📊",
                color="blue"
            )

        # DEFAULT
        return create_ai_suggestion(
            widget_type="trade_journal",
            text=f"Journal: {total_trades} trades, {win_rate:.0f}% WR, {avg_rr:.1f}R avg. Continue logging all trades for pattern analysis.",
            confidence=0.68,
            emoji="📝",
            color="blue"
        )


from datetime import datetime
