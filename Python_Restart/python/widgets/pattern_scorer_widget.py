"""
AppleTrader Pro - Pattern Scorer Widget
Visual display of pattern quality scores
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from widgets.pattern_scorer import pattern_scorer, PatternScore
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.multi_symbol_manager import get_all_symbols


# Simple theme and settings (inline replacement for config module)
class SimpleTheme:
    background = '#0A0E27'
    surface = '#1E293B'
    surface_light = '#334155'
    text_primary = '#F8FAFC'
    text_secondary = '#94A3B8'
    accent = '#3B82F6'
    success = '#10B981'
    danger = '#EF4444'
    warning = '#F59E0B'
    bullish = '#10B981'
    bearish = '#EF4444'
    border_color = '#334155'
    font_size_xs = 10
    font_size_sm = 12
    font_size_md = 14
    font_size_lg = 16
    font_size_xl = 18
    font_family_mono = 'Consolas, Monaco, monospace'

class SimpleSettings:
    theme = SimpleTheme()

settings = SimpleSettings()


class PatternScorerWidget(QWidget, AIAssistMixin):
    """
    Visual display widget for pattern quality scores (AI-Enhanced)

    Shows:
    - Overall score (0-100)
    - Star rating (⭐⭐⭐⭐⭐)
    - Score breakdown by factor
    - Historical win rate
    - Recommendation
    - AI-powered pattern validation
    """

    def __init__(self):
        super().__init__()

        self.current_symbol = "EURUSD"
        self.current_score: PatternScore = None

        # Setup AI assistance
        self.setup_ai_assist("pattern_scorer")

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
        """Initialize user interface"""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ============================================================
        # HEADER
        # ============================================================
        header_layout = QHBoxLayout()

        header = QLabel("⭐ PATTERN QUALITY SCORER")
        header.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_lg}px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()

        # AI Assist checkbox
        self.create_ai_checkbox(header_layout)

        layout.addLayout(header_layout)

        # ============================================================
        # PATTERN INFO
        # ============================================================
        self.pattern_label = QLabel("No pattern detected")
        self.pattern_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_sm}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.pattern_label)

        # ============================================================
        # OVERALL SCORE CARD
        # ============================================================
        score_card = self.create_score_card()
        layout.addWidget(score_card)

        # ============================================================
        # SCORE BREAKDOWN
        # ============================================================
        breakdown_frame = self.create_breakdown_section()
        layout.addWidget(breakdown_frame)

        # ============================================================
        # RECOMMENDATION
        # ============================================================
        recommendation_frame = self.create_recommendation_section()
        layout.addWidget(recommendation_frame)

        # ============================================================
        # AI SUGGESTION FRAME
        # ============================================================
        self.create_ai_suggestion_frame(layout)

        layout.addStretch()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager

        print(f"\n[PatternScorer] update_from_live_data() called")

        try:
            # Get current candle data
            candles = data_manager.get_candles()

            if not candles or len(candles) < 20:
                print(f"[PatternScorer] ⚠️ Not enough data ({len(candles) if candles else 0} candles)")
                return

            print(f"[PatternScorer] ✓ Got {len(candles)} candles")

            # Get market state for context
            market_state = data_manager.get_market_state()
            print(f"[PatternScorer]   → Market state: {market_state.get('trend', 'UNKNOWN')}, Session: {market_state.get('session', 'UNKNOWN')}")

            # Check if there's an opportunity detected (if method exists)
            opportunities = None
            if hasattr(data_manager, 'get_current_opportunities'):
                opportunities = data_manager.get_current_opportunities()
                print(f"[PatternScorer]   → Found {len(opportunities) if opportunities else 0} opportunities")
            else:
                print(f"[PatternScorer]   → Using market structure fallback (get_current_opportunities not available)")

            if opportunities and len(opportunities) > 0:
                # Score the first opportunity
                opp = opportunities[0]

                # Determine pattern type from opportunity
                pattern_type = opp.get('pattern_type', 'Unknown Pattern')
                entry_price = opp.get('entry_price', 0.0)

                # CRITICAL: Use REAL smart money flags from Week 1 detectors!
                # These are now set by real detector logic, not random values
                at_order_block = opp.get('order_block_valid', False)
                at_fvg = opp.get('at_fvg', False)
                liquidity_sweep = opp.get('liquidity_sweep', False)
                structure_aligned = opp.get('structure_aligned', False)

                # Calculate volume ratio from opportunity data
                quality = opp.get('quality', 50)
                volume_ratio = 1.0 + (quality / 100.0)  # 50% quality = 1.5x volume

                # Use pattern scorer to create a score with REAL smart money data
                pattern_score = pattern_scorer.score_pattern(
                    pattern_type=pattern_type,
                    price_level=entry_price,
                    at_fvg=at_fvg,  # REAL FVG detection
                    at_order_block=at_order_block,  # REAL OB validation
                    at_liquidity=liquidity_sweep,  # REAL liquidity sweep detection
                    volume_ratio=volume_ratio,
                    after_sweep=liquidity_sweep,  # Same as at_liquidity
                    mtf_h4_aligned=structure_aligned,  # REAL structure alignment
                    mtf_h1_aligned=structure_aligned,
                    mtf_m15_aligned=structure_aligned,
                    in_session=market_state.get('session', 'UNKNOWN'),
                    with_structure=structure_aligned,
                    swing_level=at_order_block or at_fvg  # OB/FVG are swing levels
                )

                print(f"[PatternScorer]   → Scored opportunity pattern: {pattern_type}, Score: {pattern_score.total_score:.1f}")
                self.update_score(pattern_score)
            else:
                # No opportunity - create a basic score from current market conditions
                current = candles[-1]
                price = current['close']

                # Analyze basic trend
                sma_20 = sum([c['close'] for c in candles[-20:]]) / 20
                is_bullish = price > sma_20

                print(f"[PatternScorer]   → No opportunity, scoring market structure (price: {price:.5f}, SMA20: {sma_20:.5f}, {'Bullish' if is_bullish else 'Bearish'})")

                # Create a basic pattern score
                pattern_score = pattern_scorer.score_pattern(
                    pattern_type="Market Structure" if is_bullish else "Market Structure",
                    price_level=price,
                    at_fvg=False,
                    at_order_block=False,
                    at_liquidity=False,
                    volume_ratio=1.0,
                    after_sweep=False,
                    mtf_h4_aligned=is_bullish,
                    mtf_h1_aligned=is_bullish,
                    mtf_m15_aligned=is_bullish,
                    in_session=market_state.get('session', 'UNKNOWN'),
                    with_structure=True,
                    swing_level=False
                )

                print(f"[PatternScorer]   → Market structure score: {pattern_score.total_score:.1f}")
                self.update_score(pattern_score)

            print(f"[PatternScorer] ✓ Pattern scoring completed successfully")

        except Exception as e:
            print(f"[Pattern Scorer] Error fetching live data: {e}")
            # Keep existing score if error occurs

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # Get demo pattern data
            demo_data = get_demo_data('pattern_scorer', symbols=[self.current_symbol])
            if demo_data:
                # Convert demo dict to PatternScore object
                from datetime import datetime

                total_score = demo_data.get('total_score', 75)
                pattern_score = PatternScore(
                    total_score=total_score,
                    zone_alignment_score=int(total_score * 0.20),
                    volume_score=int(total_score * 0.25),
                    liquidity_score=int(total_score * 0.15),
                    mtf_score=int(total_score * 0.15),
                    session_score=int(total_score * 0.10),
                    structure_score=int(total_score * 0.10),
                    historical_score=int(total_score * 0.05),
                    pattern_type=demo_data.get('pattern_type', 'Unknown'),
                    price_level=demo_data.get('entry_price', 1.0850),
                    timestamp=datetime.now(),
                    historical_win_rate=demo_data.get('historical_win_rate', 65.0) / 100.0,
                    historical_avg_rr=demo_data.get('risk_reward', 2.5),
                    historical_sample_size=50,
                    quality_tier="STRONG" if total_score >= 75 else "GOOD" if total_score >= 60 else "WEAK",
                    stars=5 if total_score >= 90 else 4 if total_score >= 75 else 3 if total_score >= 60 else 2,
                    recommendation=f"{demo_data.get('pattern_type', 'Pattern')} with {total_score}% confidence"
                )
                self.update_score(pattern_score)
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_score:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Pattern Scorer widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Custom AI analysis for pattern scoring

        Args:
            prediction: ML prediction data from ml_integration
            widget_data: Current pattern score data

        Returns:
            Formatted suggestion dictionary
        """
        from core.ml_integration import create_ai_suggestion

        if not self.current_score:
            return create_ai_suggestion(
                widget_type="pattern_scorer",
                text="No pattern detected yet",
                confidence=0.0
            )

        score = self.current_score.total_score
        pattern_type = self.current_score.pattern_type
        win_rate = self.current_score.historical_win_rate

        # Analyze pattern quality
        if score >= 85:
            confidence = 0.90
            quality = "EXCELLENT"
            action_emoji = "🔥"
            action = f"{pattern_type} pattern is very high quality"
            color = "green"
        elif score >= 75:
            confidence = 0.80
            quality = "GOOD"
            action_emoji = "✓"
            action = f"{pattern_type} pattern quality is good"
            color = "green"
        elif score >= 60:
            confidence = 0.65
            quality = "MODERATE"
            action_emoji = "⚠️"
            action = f"{pattern_type} pattern quality is moderate"
            color = "yellow"
        else:
            confidence = 0.40
            quality = "POOR"
            action_emoji = "❌"
            action = f"{pattern_type} pattern quality is poor"
            color = "red"

        # Build suggestion text
        suggestion_text = f"{action}\n\n"
        suggestion_text += f"📊 Pattern Score: {score:.0f}/100 ({quality})\n"
        suggestion_text += f"📈 Historical Win Rate: {win_rate:.1f}%\n"
        suggestion_text += f"🎯 Pattern Type: {pattern_type}\n\n"

        # Add recommendation
        if score >= 75 and win_rate >= 60:
            suggestion_text += "💡 Recommendation: Pattern confirms trade setup\n"
            suggestion_text += "✓ High probability setup based on historical performance\n"
            suggestion_text += "✓ Pattern quality supports entry decision"
        elif score >= 60:
            suggestion_text += "💡 Recommendation: Pattern provides moderate confirmation\n"
            suggestion_text += "⚠️ Wait for additional confirmation signals"
        else:
            suggestion_text += "💡 Recommendation: Pattern unreliable for trading\n"
            suggestion_text += "❌ Low quality - do not trade based on this pattern alone"

        return create_ai_suggestion(
            widget_type="pattern_scorer",
            text=suggestion_text,
            confidence=confidence,
            emoji=action_emoji,
            color=color
        )

    def create_score_card(self) -> QFrame:
        """Create overall score display card"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 2px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(8)

        # Score number
        self.score_number = QLabel("0")
        self.score_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_number.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: 48px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.score_number)

        # Score label
        score_label = QLabel("/100")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(score_label)

        # Stars
        self.stars_label = QLabel("☆☆☆☆☆")
        self.stars_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stars_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.warning};
                font-size: {settings.theme.font_size_xl}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.stars_label)

        # Tier label
        self.tier_label = QLabel("NOT RATED")
        self.tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tier_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                padding: 8px;
                background-color: {settings.theme.surface_light};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.tier_label)

        return frame

    def create_breakdown_section(self) -> QFrame:
        """Create score breakdown section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        # Title
        title = QLabel("── SCORE BREAKDOWN ──")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_sm}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # Score factors
        self.score_bars = {}

        factors = [
            ('zone_alignment', 'Zone Alignment', 20),
            ('volume', 'Volume Confirmation', 25),
            ('liquidity', 'Liquidity Context', 15),
            ('mtf', 'MTF Confluence', 15),
            ('session', 'Session Quality', 10),
            ('structure', 'Structure Alignment', 10),
            ('historical', 'Historical Performance', 5),
        ]

        for key, label, max_score in factors:
            bar_widget = self.create_score_bar(label, max_score)
            self.score_bars[key] = bar_widget.findChild(QProgressBar)
            layout.addWidget(bar_widget)

        return frame

    def create_score_bar(self, label: str, max_score: int) -> QWidget:
        """Create individual score bar"""

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        label_widget = QLabel(f"{label} (0/{max_score})")
        label_widget.setObjectName(f"{label}_label")
        label_widget.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_xs}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(label_widget)

        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, max_score)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {settings.theme.surface_light};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {settings.theme.accent};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(progress)

        return widget

    def create_recommendation_section(self) -> QFrame:
        """Create recommendation section"""

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        # Title
        title = QLabel("── RECOMMENDATION ──")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_sm}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title)

        # Recommendation text
        self.recommendation_text = QLabel("Waiting for pattern...")
        self.recommendation_text.setWordWrap(True)
        self.recommendation_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.recommendation_text.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_sm}px;
                font-family: {settings.theme.font_family_mono};
                padding: 12px;
                background-color: {settings.theme.surface_light};
                border-radius: 8px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(self.recommendation_text)

        # Historical stats
        self.historical_label = QLabel("")
        self.historical_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.historical_label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_xs}px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.historical_label)

        return frame

    def load_sample_data(self):
        """Load sample pattern score for demonstration"""
        # Create a high-quality pattern score example
        sample_score = pattern_scorer.score_pattern(
            pattern_type="Bullish Order Block",
            price_level=1.10000,
            at_fvg=True,
            at_order_block=True,
            at_liquidity=True,
            volume_ratio=2.5,
            after_sweep=True,
            mtf_h4_aligned=True,
            mtf_h1_aligned=True,
            mtf_m15_aligned=True,
            in_session="LONDON",
            with_structure=True,
            swing_level=True
        )
        self.update_score(sample_score)

    def set_symbol(self, symbol: str):
        """Update current symbol"""
        self.current_symbol = symbol
        # Note: Pattern scores are updated externally via update_score()

    def update_score(self, score: PatternScore):
        """Update display with new pattern score"""

        self.current_score = score

        # Update pattern info
        self.pattern_label.setText(
            f"{score.pattern_type} @ {score.price_level:.5f} | "
            f"{score.timestamp.strftime('%H:%M:%S')}"
        )

        # Update overall score
        self.score_number.setText(str(score.total_score))

        # Color based on tier
        color_map = {
            "MUST TAKE": settings.theme.success,
            "STRONG": settings.theme.bullish,
            "GOOD": settings.theme.accent,
            "WEAK": settings.theme.warning,
            "SKIP": settings.theme.danger
        }
        score_color = color_map.get(score.quality_tier, settings.theme.text_secondary)

        self.score_number.setStyleSheet(f"""
            QLabel {{
                color: {score_color};
                font-size: 48px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
        """)

        # Update stars
        filled_stars = "⭐" * score.stars
        empty_stars = "☆" * (5 - score.stars)
        self.stars_label.setText(filled_stars + empty_stars)

        # Update tier
        self.tier_label.setText(score.quality_tier)
        self.tier_label.setStyleSheet(f"""
            QLabel {{
                color: {score_color};
                font-size: {settings.theme.font_size_md}px;
                font-weight: 600;
                padding: 8px;
                background-color: {settings.theme.surface_light};
                border-radius: 6px;
                border: 2px solid {score_color};
            }}
        """)

        # Update score breakdown bars
        self.score_bars['zone_alignment'].setValue(score.zone_alignment_score)
        self.score_bars['volume'].setValue(score.volume_score)
        self.score_bars['liquidity'].setValue(score.liquidity_score)
        self.score_bars['mtf'].setValue(score.mtf_score)
        self.score_bars['session'].setValue(score.session_score)
        self.score_bars['structure'].setValue(score.structure_score)
        self.score_bars['historical'].setValue(score.historical_score)

        # Update recommendation
        self.recommendation_text.setText(score.recommendation)

        # Update historical stats
        if score.historical_sample_size > 0:
            self.historical_label.setText(
                f"Historical: {score.historical_win_rate*100:.0f}% Win Rate | "
                f"{score.historical_avg_rr:.1f}R Avg | "
                f"{score.historical_sample_size} Samples"
            )
        else:
            self.historical_label.setText("No historical data available")
