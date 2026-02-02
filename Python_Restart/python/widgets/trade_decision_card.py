"""
Trade Decision Card - Visual Display of Plain-English Trade Guidance

Shows trade decisions in a simple, visual format that anyone can understand.

Author: AppleTrader Pro
Date: 2026-01-30
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QPushButton, QDialog, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from typing import Dict

from core.trade_decision_assistant import trade_decision_assistant, TradeDecision


class TradeDecisionCard(QFrame):
    """
    Visual card showing simplified trade decision

    Displays:
    - Large action button (TAKE/SKIP/MAYBE)
    - Quality score with stars
    - Plain English headline
    - Confidence indicator
    - Risk recommendation
    - "Learn More" button for details
    """

    clicked = pyqtSignal(dict)  # Emits opportunity dict when clicked

    def __init__(self, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.decision = None
        self.setObjectName("TradeDecisionCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.init_ui()

    def init_ui(self):
        """Initialize the decision card UI"""

        # Get decision from assistant
        self.decision = trade_decision_assistant.analyze_opportunity(self.opportunity)

        # Card styling based on action
        if self.decision.action == "TAKE":
            border_color = "#10B981"
            bg_color = "#064E3B"
        elif self.decision.action == "SKIP":
            border_color = "#EF4444"
            bg_color = "#7F1D1D"
        else:  # MAYBE
            border_color = "#F59E0B"
            bg_color = "#78350F"

        self.setStyleSheet(f"""
            TradeDecisionCard {{
                background-color: {bg_color};
                border: 3px solid {border_color};
                border-radius: 12px;
                padding: 16px;
            }}
            TradeDecisionCard QLabel {{
                background-color: transparent;
                border: none;
            }}
            TradeDecisionCard QPushButton {{
                background-color: transparent;
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                color: #FFFFFF;
            }}
            TradeDecisionCard QPushButton:hover {{
                background-color: {border_color};
            }}
        """)

        self.setMinimumHeight(200)
        self.setMaximumHeight(250)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Symbol + Timeframe header
        header_layout = QHBoxLayout()
        symbol_label = QLabel(f"{self.opportunity.get('symbol', '?')} {self.opportunity.get('timeframe', '?')}")
        symbol_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        symbol_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(symbol_label)

        direction = self.opportunity.get('direction', 'BUY')
        dir_icon = "📈" if direction == "BUY" else "📉"
        dir_label = QLabel(f"{dir_icon} {direction}")
        dir_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        dir_label.setStyleSheet("color: " + ("#10B981" if direction == "BUY" else "#EF4444"))
        header_layout.addWidget(dir_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # BIG ACTION INDICATOR
        action_label = QLabel(f"{self.decision.action_icon} {self.decision.action}")
        action_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        action_label.setStyleSheet(f"color: {self.decision.action_color}; padding: 8px;")
        action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(action_label)

        # Quality Score with Stars
        quality_layout = QHBoxLayout()
        quality_layout.addStretch()

        score_label = QLabel(f"{self.decision.quality_score}/10")
        score_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        score_label.setStyleSheet("color: #FFFFFF;")
        quality_layout.addWidget(score_label)

        stars_label = QLabel(self.decision.quality_stars)
        stars_label.setFont(QFont("Arial", 14))
        stars_label.setStyleSheet("color: #FCD34D;")
        quality_layout.addWidget(stars_label)

        quality_desc = QLabel(f"({self.decision.quality_description})")
        quality_desc.setFont(QFont("Arial", 11))
        quality_desc.setStyleSheet("color: #94A3B8;")
        quality_layout.addWidget(quality_desc)

        quality_layout.addStretch()
        layout.addLayout(quality_layout)

        # Confidence Indicator
        confidence_layout = QHBoxLayout()
        confidence_layout.addStretch()

        conf_label = QLabel(f"{self.decision.confidence_icon} {self.decision.confidence} Confidence")
        conf_label.setFont(QFont("Arial", 11))
        conf_label.setStyleSheet("color: #FFFFFF;")
        confidence_layout.addWidget(conf_label)

        confidence_layout.addStretch()
        layout.addLayout(confidence_layout)

        # Plain English Headline
        headline_label = QLabel(self.decision.headline)
        headline_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        headline_label.setStyleSheet("color: #FFFFFF; padding: 8px;")
        headline_label.setWordWrap(True)
        headline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(headline_label)

        # Risk Recommendation (if TAKE)
        if self.decision.action == "TAKE":
            risk_label = QLabel(f"💰 Risk {self.decision.risk_amount_balanced:.1f}% (Balanced)")
            risk_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            risk_label.setStyleSheet("color: #3B82F6;")
            risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(risk_label)

        # Learn More button
        learn_more_btn = QPushButton("📖 Learn More")
        learn_more_btn.setFont(QFont("Arial", 10))
        learn_more_btn.clicked.connect(self.show_detailed_explanation)
        layout.addWidget(learn_more_btn)

        layout.addStretch()

    def show_detailed_explanation(self):
        """Show detailed explanation dialog"""
        dialog = TradeDecisionDialog(self.decision, self.opportunity, self)
        dialog.exec()

    def mousePressEvent(self, event):
        """Handle card click"""
        self.clicked.emit(self.opportunity)


class TradeDecisionDialog(QDialog):
    """
    Full detailed explanation dialog

    Shows all the details, projections, warnings in a scrollable view
    """

    def __init__(self, decision: TradeDecision, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.decision = decision
        self.opportunity = opportunity
        self.setWindowTitle(f"Trade Decision Details - {opportunity.get('symbol', '?')}")
        self.setModal(False)
        self.resize(800, 700)
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""

        layout = QVBoxLayout(self)

        # Header with symbol and action
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.decision.action_color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        header_layout = QVBoxLayout(header_frame)

        title_label = QLabel(f"{self.opportunity.get('symbol', '?')} {self.opportunity.get('timeframe', '?')} - {self.opportunity.get('direction', '?')}")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(title_label)

        action_label = QLabel(f"{self.decision.action_icon} {self.decision.action}")
        action_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        action_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(action_label)

        layout.addWidget(header_frame)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E293B; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # Quality Section
        content_layout.addWidget(self._create_section("QUALITY ASSESSMENT",
            f"{self.decision.quality_score}/10 {self.decision.quality_stars}\n"
            f"{self.decision.quality_description}\n\n"
            f"{self.decision.explanation}"))

        # Confidence Section
        content_layout.addWidget(self._create_section("CONFIDENCE LEVEL",
            f"{self.decision.confidence} ({self.decision.confidence_percent}%)\n"
            f"{self.decision.confidence_icon}\n\n"
            f"{self.decision.confidence_explanation}"))

        # Recommendation Section
        content_layout.addWidget(self._create_section("RECOMMENDATION",
            self.decision.recommendation))

        # Risk Sizing Section
        risk_text = (
            f"Conservative: {self.decision.risk_amount_conservative:.1f}%\n"
            f"Balanced: {self.decision.risk_amount_balanced:.1f}% ← RECOMMENDED\n"
            f"Aggressive: {self.decision.risk_amount_aggressive:.1f}%\n\n"
            f"{self.decision.risk_explanation}"
        )
        content_layout.addWidget(self._create_section("RISK SIZING", risk_text))

        # 100-Trade Projection Section
        projection_text = (
            f"{self.decision.projection_100_trades}\n\n"
            f"{self.decision.projection_explanation}"
        )
        if self.decision.projection_warning:
            projection_text += f"\n\n{self.decision.projection_warning}"
        content_layout.addWidget(self._create_section("IF YOU TAKE 100 TRADES LIKE THIS", projection_text))

        # Track Record Section
        track_text = self.decision.historical_summary
        if self.decision.recent_trend:
            track_text += f"\n\n{self.decision.recent_trend}"
        content_layout.addWidget(self._create_section("HISTORICAL TRACK RECORD", track_text))

        # Warnings Section (if any)
        if self.decision.warnings:
            warnings_text = "\n".join(self.decision.warnings)
            content_layout.addWidget(self._create_section("⚠ WARNINGS", warnings_text, "#F59E0B"))

        # Positive Alerts Section (if any)
        if self.decision.alerts:
            alerts_text = "\n".join(self.decision.alerts)
            content_layout.addWidget(self._create_section("✓ POSITIVE SIGNALS", alerts_text, "#10B981"))

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Arial", 12))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _create_section(self, title: str, content: str, border_color: str = "#3B82F6") -> QFrame:
        """Create a styled section frame"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0F172A;
                border-left: 4px solid {border_color};
                border-radius: 6px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {border_color};")
        layout.addWidget(title_label)

        content_label = QLabel(content)
        content_label.setFont(QFont("Arial", 11))
        content_label.setStyleSheet("color: #E2E8F0; padding-top: 8px;")
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        return frame
