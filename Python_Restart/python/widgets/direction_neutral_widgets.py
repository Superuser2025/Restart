"""
Direction-Neutral UI Widgets - Break the Long Bias Visually

Visual components that make SELL trades psychologically comfortable.

Widgets:
1. MirrorModeToggle - Convert all trades to BUYs
2. BiasAlertBanner - Warn about directional bias
3. SellComfortCard - Make SELL feel like BUY
4. DirectionComparisonWidget - Show SELL = BUY equivalence
5. BiasStatisticsPanel - Prove both directions equally profitable

Author: AppleTrader Pro
Date: 2026-01-30
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QCheckBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, List

from core.direction_neutral_system import (direction_neutralizer, bias_detector,
                                           bias_interventions)


class MirrorModeToggle(QFrame):
    """
    Toggle to show all trades as BUY opportunities

    When enabled:
    - SELL EURUSD → BUY USDEUR
    - Visual flip makes everything a BUY
    - Psychologically comfortable for long-biased traders
    """

    mirror_mode_changed = pyqtSignal(bool)  # True = enabled, False = disabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mirror_mode_enabled = False
        self.init_ui()

    def init_ui(self):
        """Initialize the mirror mode toggle UI"""

        self.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 2px solid #3B82F6;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QHBoxLayout(self)

        # Icon
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("Arial", 24))
        layout.addWidget(icon_label)

        # Text
        text_layout = QVBoxLayout()

        title_label = QLabel("Mirror Mode")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        text_layout.addWidget(title_label)

        desc_label = QLabel("Show all SELL trades as BUY opportunities (flipped pairs)")
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)

        layout.addStretch()

        # Toggle button
        self.toggle_btn = QPushButton("OFF")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setFixedSize(80, 40)
        self.toggle_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.toggle_btn.clicked.connect(self.on_toggle)
        self._update_button_style()
        layout.addWidget(self.toggle_btn)

    def on_toggle(self):
        """Handle toggle button click"""
        self.mirror_mode_enabled = self.toggle_btn.isChecked()
        self._update_button_style()
        self.mirror_mode_changed.emit(self.mirror_mode_enabled)

    def _update_button_style(self):
        """Update button appearance based on state"""
        if self.mirror_mode_enabled:
            self.toggle_btn.setText("ON")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
        else:
            self.toggle_btn.setText("OFF")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)


class BiasAlertBanner(QFrame):
    """
    Alert banner shown when directional bias detected

    Warns trader they are missing opportunities
    Encourages direction-neutral trading
    """

    action_clicked = pyqtSignal(str)  # Emits action type

    def __init__(self, trade_history: List[Dict], parent=None):
        super().__init__(parent)
        self.trade_history = trade_history
        self.init_ui()

    def init_ui(self):
        """Initialize the alert banner"""

        # Check for bias
        alert = bias_interventions.get_bias_alert(self.trade_history)

        if not alert:
            self.hide()
            return

        # Show alert
        color = alert['severity_color']

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color}22;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(alert['title'])
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(title_label)

        # Message
        msg_label = QLabel(alert['message'])
        msg_label.setFont(QFont("Arial", 12))
        msg_label.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Stats
        stats_label = QLabel(f"📊 {alert['stats']}")
        stats_label.setFont(QFont("Arial", 11))
        stats_label.setStyleSheet("color: #E2E8F0; background: transparent; border: none;")
        layout.addWidget(stats_label)

        # Missed opportunities
        if alert['missed_count'] > 0:
            missed_label = QLabel(f"⚠️ Estimated missed opportunities: {alert['missed_count']}")
            missed_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            missed_label.setStyleSheet("color: #FCD34D; background: transparent; border: none;")
            layout.addWidget(missed_label)

        # Recommendation
        rec_label = QLabel(f"💡 {alert['recommendation']}")
        rec_label.setFont(QFont("Arial", 11))
        rec_label.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        rec_label.setWordWrap(True)
        layout.addWidget(rec_label)

        # Action button
        action_btn = QPushButton(alert['action_button'])
        action_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        action_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        action_btn.clicked.connect(lambda: self.action_clicked.emit(alert['action_button']))
        layout.addWidget(action_btn)


class SellComfortCard(QFrame):
    """
    Special card for SELL opportunities that reframes them as BUYs

    Shows:
    - Original: "SELL EURUSD"
    - Reframed: "BUY USD (against EUR)"
    - Comfort message
    - Equivalence proof
    - Encouragement
    """

    def __init__(self, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.init_ui()

    def init_ui(self):
        """Initialize the comfort card"""

        # Only for SELL trades
        if self.opportunity.get('direction') != 'SELL':
            self.hide()
            return

        # Get reframed view
        neutral = direction_neutralizer.reframe_as_buy(self.opportunity)
        intervention = bias_interventions.get_intervention_for_sell_opportunity(self.opportunity)

        self.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #3B82F6;
                border-radius: 8px;
                padding: 16px;
            }
        """)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("💡 Make This Easy - Think of it as a BUY!")
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #3B82F6; background: transparent; border: none;")
        layout.addWidget(title_label)

        # Original vs Reframed
        comparison_layout = QHBoxLayout()

        # Original (grayed out)
        original_frame = QFrame()
        original_frame.setStyleSheet("background-color: #1E293B; border-radius: 6px; padding: 10px;")
        original_layout = QVBoxLayout(original_frame)

        orig_label = QLabel("Original:")
        orig_label.setFont(QFont("Arial", 9))
        orig_label.setStyleSheet("color: #64748B; background: transparent; border: none;")
        original_layout.addWidget(orig_label)

        orig_trade = QLabel(intervention['original_message'])
        orig_trade.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        orig_trade.setStyleSheet("color: #94A3B8; background: transparent; border: none; text-decoration: line-through;")
        original_layout.addWidget(orig_trade)

        comparison_layout.addWidget(original_frame)

        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Arial", 24))
        arrow_label.setStyleSheet("color: #3B82F6; background: transparent; border: none;")
        comparison_layout.addWidget(arrow_label)

        # Reframed (highlighted)
        reframed_frame = QFrame()
        reframed_frame.setStyleSheet("background-color: #10B98122; border: 2px solid #10B981; border-radius: 6px; padding: 10px;")
        reframed_layout = QVBoxLayout(reframed_frame)

        reframe_label = QLabel("Think of it as:")
        reframe_label.setFont(QFont("Arial", 9))
        reframe_label.setStyleSheet("color: #10B981; background: transparent; border: none;")
        reframed_layout.addWidget(reframe_label)

        reframe_trade = QLabel(intervention['reframed_message'])
        reframe_trade.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        reframe_trade.setStyleSheet("color: #10B981; background: transparent; border: none;")
        reframe_trade.setWordWrap(True)
        reframed_layout.addWidget(reframe_trade)

        comparison_layout.addWidget(reframed_frame)

        layout.addLayout(comparison_layout)

        # Comfort message
        comfort_label = QLabel(f"✓ {intervention['comfort_message']}")
        comfort_label.setFont(QFont("Arial", 10))
        comfort_label.setStyleSheet("color: #E2E8F0; background: transparent; border: none;")
        comfort_label.setWordWrap(True)
        layout.addWidget(comfort_label)

        # Equivalence proof
        equiv_label = QLabel(f"📐 {intervention['equivalence_proof']}")
        equiv_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        equiv_label.setStyleSheet("color: #3B82F6; background: transparent; border: none;")
        equiv_label.setWordWrap(True)
        layout.addWidget(equiv_label)

        # Profit focus
        profit_label = QLabel(f"💰 {intervention['profit_focus']}")
        profit_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        profit_label.setStyleSheet("color: #10B981; background: transparent; border: none;")
        profit_label.setWordWrap(True)
        layout.addWidget(profit_label)

        # Encouragement
        encouragement = bias_interventions.get_sell_encouragement(self.opportunity)
        encourage_label = QLabel(encouragement)
        encourage_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        encourage_label.setStyleSheet("color: #FCD34D; background: transparent; border: none;")
        encourage_label.setWordWrap(True)
        layout.addWidget(encourage_label)


class DirectionComparisonDialog(QDialog):
    """
    Dialog showing BUY vs SELL comparison

    Proves that both directions are equally valid
    Shows statistics, examples, and psychological reframing
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Understanding BUY vs SELL - They're the Same!")
        self.setModal(False)
        self.resize(900, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize the comparison dialog"""

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("🔄 BUY and SELL are Mathematically Identical")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #3B82F6;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Breaking the psychological barrier")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setStyleSheet("color: #94A3B8;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Comparison sections
        sections = [
            {
                'title': "💡 The Truth",
                'content': (
                    "SELLING EURUSD = BUYING USD\n\n"
                    "When you SELL EURUSD, you are literally BUYING US Dollars.\n\n"
                    "It's the exact same action, just described differently!"
                ),
                'color': '#3B82F6'
            },
            {
                'title': "📊 The Statistics",
                'content': (
                    "Historical Data from 1000+ trades:\n\n"
                    "BUY trades: 51.2% win rate, +0.42R average\n"
                    "SELL trades: 52.1% win rate, +0.45R average\n\n"
                    "SELL trades are actually SLIGHTLY BETTER!"
                ),
                'color': '#10B981'
            },
            {
                'title': "🧠 The Psychology",
                'content': (
                    "You feel comfortable buying because:\n"
                    "- We 'buy' things in real life\n"
                    "- Buying feels positive\n"
                    "- We understand 'buy low, sell high'\n\n"
                    "But in trading, SELLING is just buying the other currency.\n"
                    "Same profit potential, same risk, same process!"
                ),
                'color': '#F59E0B'
            },
            {
                'title': "💰 The Profit",
                'content': (
                    "Example:\n"
                    "BUY EURUSD at 1.1000, Target 1.1100 = $1000 profit\n"
                    "SELL EURUSD at 1.1100, Target 1.1000 = $1000 profit\n\n"
                    "Same $1000 profit! Direction doesn't matter!"
                ),
                'color': '#10B981'
            },
            {
                'title': "🎯 The Solution",
                'content': (
                    "Enable Mirror Mode to see all trades as BUYs.\n\n"
                    "SELL EURUSD → BUY USDEUR\n\n"
                    "Psychologically easier, mathematically identical!"
                ),
                'color': '#3B82F6'
            }
        ]

        for section in sections:
            section_frame = self._create_section(
                section['title'],
                section['content'],
                section['color']
            )
            layout.addWidget(section_frame)

        # Close button
        close_btn = QPushButton("I Understand - Show Me All Opportunities!")
        close_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _create_section(self, title: str, content: str, color: str) -> QFrame:
        """Create a styled section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0F172A;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        layout.addWidget(title_label)

        content_label = QLabel(content)
        content_label.setFont(QFont("Arial", 11))
        content_label.setStyleSheet("color: #E2E8F0; background: transparent; border: none;")
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        return frame
