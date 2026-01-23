"""
AppleTrader Pro - Statistical Analysis Widget
Comprehensive probability and statistics display

Displays:
- Expected Value analysis
- Kelly Criterion position sizing
- Bayesian pattern learning
- Confidence intervals
- Probabilistic confluence

All analysis is timeframe-specific (M15, H1, H4, D1)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QPushButton, QComboBox,
    QScrollArea, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from core.statistical_analysis_manager import statistical_analysis_manager
from core.verbose_mode_manager import vprint


# Simple theme matching existing widgets
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
    border_color = '#334155'
    font_size_sm = 12
    font_size_md = 14
    font_size_lg = 16
    font_size_xl = 18


class SimpleSettings:
    theme = SimpleTheme()


settings = SimpleSettings()


class StatisticalAnalysisWidget(QWidget):
    """
    Statistical Analysis Widget - Main UI for probability & statistics

    Features (Requirements):
    - ✓ Separate tab for statistical analysis (Req #1)
    - ✓ Analysis based on timeframes (Req #2)
    - ✓ Global enable/disable switch (Req #6)
    - ✓ Verifiable calculations (Req #4)
    - ✓ Non-destructive integration (Req #5)
    """

    # Signals
    stats_enabled_changed = pyqtSignal(bool)
    timeframe_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.manager = statistical_analysis_manager
        self.current_pattern = "Hammer"  # Default pattern for display
        self.current_symbol = "EURUSD"

        self.init_ui()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_all_displays)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

        # Initial update
        self.update_all_displays()

    def init_ui(self):
        """Initialize user interface"""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {settings.theme.background};
            }}
        """)

        # Content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # ============================================================
        # HEADER WITH MASTER SWITCH (Requirement #6)
        # ============================================================
        header_frame = self._create_header()
        content_layout.addWidget(header_frame)

        # ============================================================
        # TIMEFRAME SELECTOR (Requirement #2)
        # ============================================================
        timeframe_frame = self._create_timeframe_selector()
        content_layout.addWidget(timeframe_frame)

        # ============================================================
        # EXPECTED VALUE SECTION
        # ============================================================
        self.ev_frame = self._create_ev_section()
        content_layout.addWidget(self.ev_frame)

        # ============================================================
        # KELLY CRITERION SECTION
        # ============================================================
        self.kelly_frame = self._create_kelly_section()
        content_layout.addWidget(self.kelly_frame)

        # ============================================================
        # BAYESIAN LEARNING SECTION
        # ============================================================
        self.bayesian_frame = self._create_bayesian_section()
        content_layout.addWidget(self.bayesian_frame)

        # ============================================================
        # CONFIDENCE INTERVALS SECTION
        # ============================================================
        self.ci_frame = self._create_ci_section()
        content_layout.addWidget(self.ci_frame)

        # ============================================================
        # PROBABILISTIC CONFLUENCE SECTION
        # ============================================================
        self.confluence_frame = self._create_confluence_section()
        content_layout.addWidget(self.confluence_frame)

        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_header(self) -> QFrame:
        """Create header with master enable/disable switch"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QHBoxLayout(frame)

        # Title
        title = QLabel("📊 STATISTICAL ANALYSIS")
        title.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_primary};
                font-size: {settings.theme.font_size_xl}px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Master Enable/Disable Switch (Requirement #6 - Global Kill Switch)
        self.master_switch = QPushButton()
        self.update_master_switch_text()
        self.master_switch.clicked.connect(self.toggle_master_switch)
        self.master_switch.setFixedHeight(40)
        self.master_switch.setStyleSheet(self._get_switch_style())
        layout.addWidget(self.master_switch)

        return frame

    def _get_switch_style(self) -> str:
        """Get style for master switch based on state"""
        if self.manager.is_enabled():
            bg_color = settings.theme.success
            text = "ENABLED"
        else:
            bg_color = settings.theme.danger
            text = "DISABLED"

        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: {settings.theme.font_size_md}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """

    def update_master_switch_text(self):
        """Update master switch button text"""
        if self.manager.is_enabled():
            self.master_switch.setText("✓ STATISTICAL ANALYSIS ENABLED")
        else:
            self.master_switch.setText("✗ STATISTICAL ANALYSIS DISABLED")
        self.master_switch.setStyleSheet(self._get_switch_style())

    def toggle_master_switch(self):
        """Toggle master enable/disable (Requirement #6 - Layman Mode)"""
        self.manager.toggle()
        self.update_master_switch_text()
        self.stats_enabled_changed.emit(self.manager.is_enabled())
        self.update_all_displays()

        if self.manager.is_enabled():
            vprint("[StatWidget] ✓ Statistical analysis ENABLED")
        else:
            vprint("[StatWidget] ✗ Statistical analysis DISABLED (layman mode)")

    def _create_timeframe_selector(self) -> QFrame:
        """Create timeframe selector (Requirement #2)"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 1px solid {settings.theme.border_color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QHBoxLayout(frame)

        label = QLabel("Timeframe:")
        label.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.text_secondary};
                font-size: {settings.theme.font_size_md}px;
            }}
        """)
        layout.addWidget(label)

        # Timeframe buttons
        timeframes = ['M15', 'H1', 'H4', 'D1']
        self.tf_buttons = {}

        for tf in timeframes:
            btn = QPushButton(tf)
            btn.setFixedSize(80, 40)
            btn.clicked.connect(lambda checked, t=tf: self.change_timeframe(t))
            self.tf_buttons[tf] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Update button styles
        self.update_timeframe_buttons()

        return frame

    def update_timeframe_buttons(self):
        """Update timeframe button styles"""
        current_tf = self.manager.get_selected_timeframe()

        for tf, btn in self.tf_buttons.items():
            if tf == current_tf:
                # Selected
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {settings.theme.accent};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 6px;
                        font-size: {settings.theme.font_size_md}px;
                        font-weight: bold;
                    }}
                """)
            else:
                # Not selected
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {settings.theme.surface_light};
                        color: {settings.theme.text_primary};
                        border: 1px solid {settings.theme.border_color};
                        border-radius: 6px;
                        font-size: {settings.theme.font_size_md}px;
                    }}
                    QPushButton:hover {{
                        border-color: {settings.theme.accent};
                    }}
                """)

    def change_timeframe(self, timeframe: str):
        """Change selected timeframe"""
        self.manager.set_timeframe(timeframe)
        self.update_timeframe_buttons()
        self.timeframe_changed.emit(timeframe)
        self.update_all_displays()
        vprint(f"[StatWidget] Timeframe changed to {timeframe}")

    def _create_section_frame(self, title: str, icon: str = "") -> tuple:
        """Create a styled section frame"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {settings.theme.surface};
                border: 2px solid {settings.theme.border_color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)

        # Section header
        header = QLabel(f"{icon} {title}")
        header.setStyleSheet(f"""
            QLabel {{
                color: {settings.theme.accent};
                font-size: {settings.theme.font_size_lg}px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {settings.theme.border_color};")
        layout.addWidget(separator)

        return frame, layout

    def _create_ev_section(self) -> QFrame:
        """Create Expected Value analysis section"""
        frame, layout = self._create_section_frame("EXPECTED VALUE ANALYSIS", "💰")

        # Pattern selector
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Pattern:")
        pattern_label.setStyleSheet(f"color: {settings.theme.text_secondary};")
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(['Hammer', 'Engulfing', 'Morning Star', 'Doji', 'Shooting Star'])
        self.pattern_combo.currentTextChanged.connect(self.on_pattern_changed)
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self.pattern_combo)
        pattern_layout.addStretch()
        layout.addLayout(pattern_layout)

        # EV display labels
        self.ev_value_label = QLabel("Expected Value: --")
        self.ev_win_rate_label = QLabel("Win Rate: --")
        self.ev_avg_win_label = QLabel("Avg Win: --")
        self.ev_avg_loss_label = QLabel("Avg Loss: --")
        self.ev_sample_label = QLabel("Sample Size: --")
        self.ev_recommendation_label = QLabel("Recommendation: --")

        for label in [self.ev_value_label, self.ev_win_rate_label, self.ev_avg_win_label,
                      self.ev_avg_loss_label, self.ev_sample_label]:
            label.setStyleSheet(f"color: {settings.theme.text_primary}; font-size: {settings.theme.font_size_md}px;")
            layout.addWidget(label)

        self.ev_recommendation_label.setStyleSheet(f"""
            color: {settings.theme.text_primary};
            font-size: {settings.theme.font_size_md}px;
            font-weight: bold;
            padding: 8px;
            background-color: {settings.theme.surface_light};
            border-radius: 4px;
        """)
        layout.addWidget(self.ev_recommendation_label)

        return frame

    def _create_kelly_section(self) -> QFrame:
        """Create Kelly Criterion section"""
        frame, layout = self._create_section_frame("KELLY CRITERION POSITION SIZING", "📈")

        self.kelly_full_label = QLabel("Full Kelly: --")
        self.kelly_half_label = QLabel("Half Kelly (Recommended): --")
        self.kelly_quarter_label = QLabel("Quarter Kelly (Conservative): --")
        self.kelly_win_rate_label = QLabel("Win Rate: --")
        self.kelly_ratio_label = QLabel("Win/Loss Ratio: --")
        self.kelly_recommendation_label = QLabel("Recommendation: --")

        for label in [self.kelly_full_label, self.kelly_half_label, self.kelly_quarter_label,
                      self.kelly_win_rate_label, self.kelly_ratio_label]:
            label.setStyleSheet(f"color: {settings.theme.text_primary}; font-size: {settings.theme.font_size_md}px;")
            layout.addWidget(label)

        self.kelly_recommendation_label.setStyleSheet(f"""
            color: {settings.theme.text_primary};
            font-size: {settings.theme.font_size_md}px;
            font-weight: bold;
            padding: 8px;
            background-color: {settings.theme.surface_light};
            border-radius: 4px;
        """)
        layout.addWidget(self.kelly_recommendation_label)

        return frame

    def _create_bayesian_section(self) -> QFrame:
        """Create Bayesian learning section"""
        frame, layout = self._create_section_frame("BAYESIAN PATTERN LEARNING", "🧠")

        self.bayesian_posterior_label = QLabel("Posterior Probability: --")
        self.bayesian_ci_label = QLabel("95% Credible Interval: --")
        self.bayesian_sample_label = QLabel("Sample Size: --")
        self.bayesian_confidence_label = QLabel("Confidence Level: --")
        self.bayesian_prior_influence_label = QLabel("Prior Influence: --")
        self.bayesian_recommendation_label = QLabel("Recommendation: --")

        for label in [self.bayesian_posterior_label, self.bayesian_ci_label, self.bayesian_sample_label,
                      self.bayesian_confidence_label, self.bayesian_prior_influence_label]:
            label.setStyleSheet(f"color: {settings.theme.text_primary}; font-size: {settings.theme.font_size_md}px;")
            layout.addWidget(label)

        self.bayesian_recommendation_label.setStyleSheet(f"""
            color: {settings.theme.text_primary};
            font-size: {settings.theme.font_size_md}px;
            font-weight: bold;
            padding: 8px;
            background-color: {settings.theme.surface_light};
            border-radius: 4px;
        """)
        layout.addWidget(self.bayesian_recommendation_label)

        return frame

    def _create_ci_section(self) -> QFrame:
        """Create Confidence Intervals section"""
        frame, layout = self._create_section_frame("CONFIDENCE INTERVALS", "📊")

        self.ci_win_rate_label = QLabel("Win Rate Estimate: --")
        self.ci_interval_label = QLabel("95% CI: --")
        self.ci_width_label = QLabel("CI Width: --")
        self.ci_sample_label = QLabel("Sample Size: --")
        self.ci_interpretation_label = QLabel("Interpretation: --")

        for label in [self.ci_win_rate_label, self.ci_interval_label, self.ci_width_label, self.ci_sample_label]:
            label.setStyleSheet(f"color: {settings.theme.text_primary}; font-size: {settings.theme.font_size_md}px;")
            layout.addWidget(label)

        self.ci_interpretation_label.setStyleSheet(f"""
            color: {settings.theme.text_primary};
            font-size: {settings.theme.font_size_md}px;
            font-weight: bold;
            padding: 8px;
            background-color: {settings.theme.surface_light};
            border-radius: 4px;
        """)
        layout.addWidget(self.ci_interpretation_label)

        return frame

    def _create_confluence_section(self) -> QFrame:
        """Create Probabilistic Confluence section"""
        frame, layout = self._create_section_frame("PROBABILISTIC CONFLUENCE", "🎯")

        self.conf_base_label = QLabel("Base Probability: --")
        self.conf_final_label = QLabel("Final Probability: --")
        self.conf_factors_label = QLabel("Factors Applied: --")
        self.conf_score_label = QLabel("Confidence Score: --")
        self.conf_recommendation_label = QLabel("Recommendation: --")

        for label in [self.conf_base_label, self.conf_final_label, self.conf_factors_label, self.conf_score_label]:
            label.setStyleSheet(f"color: {settings.theme.text_primary}; font-size: {settings.theme.font_size_md}px;")
            layout.addWidget(label)

        self.conf_recommendation_label.setStyleSheet(f"""
            color: {settings.theme.text_primary};
            font-size: {settings.theme.font_size_md}px;
            font-weight: bold;
            padding: 8px;
            background-color: {settings.theme.surface_light};
            border-radius: 4px;
        """)
        layout.addWidget(self.conf_recommendation_label)

        return frame

    def on_pattern_changed(self, pattern: str):
        """Handle pattern selection change"""
        self.current_pattern = pattern
        self.update_all_displays()

    def update_all_displays(self):
        """Update all statistical displays"""
        if not self.manager.is_enabled():
            self._show_disabled_message()
            return

        timeframe = self.manager.get_selected_timeframe()

        # Update Expected Value
        self._update_ev_display(timeframe)

        # Update Kelly Criterion
        self._update_kelly_display(timeframe)

        # Update Bayesian Learning
        self._update_bayesian_display(timeframe)

        # Update Confidence Intervals
        self._update_ci_display(timeframe)

        # Update Probabilistic Confluence
        self._update_confluence_display(timeframe)

    def _show_disabled_message(self):
        """Show message when statistics are disabled"""
        disabled_msg = "Statistical analysis is DISABLED (layman mode)"

        self.ev_recommendation_label.setText(disabled_msg)
        self.kelly_recommendation_label.setText(disabled_msg)
        self.bayesian_recommendation_label.setText(disabled_msg)
        self.ci_interpretation_label.setText(disabled_msg)
        self.conf_recommendation_label.setText(disabled_msg)

        # Clear other labels
        for label in [self.ev_value_label, self.ev_win_rate_label, self.ev_avg_win_label,
                      self.ev_avg_loss_label, self.ev_sample_label]:
            label.setText("--")

        for label in [self.kelly_full_label, self.kelly_half_label, self.kelly_quarter_label,
                      self.kelly_win_rate_label, self.kelly_ratio_label]:
            label.setText("--")

        for label in [self.bayesian_posterior_label, self.bayesian_ci_label, self.bayesian_sample_label,
                      self.bayesian_confidence_label, self.bayesian_prior_influence_label]:
            label.setText("--")

        for label in [self.ci_win_rate_label, self.ci_interval_label, self.ci_width_label, self.ci_sample_label]:
            label.setText("--")

        for label in [self.conf_base_label, self.conf_final_label, self.conf_factors_label, self.conf_score_label]:
            label.setText("--")

    def _update_ev_display(self, timeframe: str):
        """Update Expected Value display"""
        try:
            ev_calc = self.manager.get_calculator(timeframe, 'ev')
            if not ev_calc:
                return

            opportunity = {'pattern': self.current_pattern, 'symbol': self.current_symbol}
            analysis = ev_calc.get_detailed_analysis(opportunity)

            self.ev_value_label.setText(f"Expected Value: {analysis['expected_value']:+.3f}R")
            self.ev_win_rate_label.setText(f"Win Rate: {analysis['win_rate']*100:.1f}%")
            self.ev_avg_win_label.setText(f"Avg Win: {analysis['avg_win']:.2f}R")
            self.ev_avg_loss_label.setText(f"Avg Loss: {analysis['avg_loss']:.2f}R")
            self.ev_sample_label.setText(f"Sample Size: {analysis['sample_size']} trades ({analysis['confidence_level']})")
            self.ev_recommendation_label.setText(analysis['recommendation'])

        except Exception as e:
            vprint(f"[StatWidget] Error updating EV: {e}")

    def _update_kelly_display(self, timeframe: str):
        """Update Kelly Criterion display"""
        try:
            kelly_calc = self.manager.get_calculator(timeframe, 'kelly')
            if not kelly_calc:
                return

            opportunity = {'pattern': self.current_pattern, 'symbol': self.current_symbol}
            kelly_data = kelly_calc.calculate_kelly_fraction(opportunity)

            self.kelly_full_label.setText(f"Full Kelly: {kelly_data['kelly_full']*100:.2f}%")
            self.kelly_half_label.setText(f"Half Kelly (Recommended): {kelly_data['kelly_half']*100:.2f}%")
            self.kelly_quarter_label.setText(f"Quarter Kelly (Conservative): {kelly_data['kelly_quarter']*100:.2f}%")
            self.kelly_win_rate_label.setText(f"Win Rate: {kelly_data['win_rate']*100:.1f}%")
            self.kelly_ratio_label.setText(f"Win/Loss Ratio: {kelly_data['win_loss_ratio']:.2f}")
            self.kelly_recommendation_label.setText(kelly_data['recommendation'])

        except Exception as e:
            vprint(f"[StatWidget] Error updating Kelly: {e}")

    def _update_bayesian_display(self, timeframe: str):
        """Update Bayesian learning display"""
        try:
            bayesian_calc = self.manager.get_calculator(timeframe, 'bayesian')
            if not bayesian_calc:
                return

            analysis = bayesian_calc.get_detailed_analysis(self.current_pattern)

            posterior = analysis['posterior_mean']
            ci = analysis['credible_interval']

            self.bayesian_posterior_label.setText(f"Posterior Probability: {posterior*100:.1f}%")
            self.bayesian_ci_label.setText(f"95% Credible Interval: [{ci[0]*100:.1f}%, {ci[1]*100:.1f}%]")
            self.bayesian_sample_label.setText(f"Sample Size: {analysis['sample_size']} trades")
            self.bayesian_confidence_label.setText(f"Confidence: {analysis['confidence']}")
            self.bayesian_prior_influence_label.setText(f"Prior Influence: {analysis['prior_influence']*100:.0f}%")
            self.bayesian_recommendation_label.setText(analysis['recommendation'])

        except Exception as e:
            vprint(f"[StatWidget] Error updating Bayesian: {e}")

    def _update_ci_display(self, timeframe: str):
        """Update Confidence Intervals display"""
        try:
            ci_calc = self.manager.get_calculator(timeframe, 'confidence')
            if not ci_calc:
                return

            ci_data = ci_calc.calculate_win_rate_ci(self.current_pattern)

            self.ci_win_rate_label.setText(f"Win Rate Estimate: {ci_data['win_rate']*100:.1f}%")
            self.ci_interval_label.setText(f"95% CI: [{ci_data['ci_lower']*100:.1f}%, {ci_data['ci_upper']*100:.1f}%]")
            self.ci_width_label.setText(f"CI Width: {ci_data['ci_width']*100:.1f}% (uncertainty measure)")
            self.ci_sample_label.setText(f"Sample Size: {ci_data['sample_size']} trades")
            self.ci_interpretation_label.setText(ci_data['interpretation'])

        except Exception as e:
            vprint(f"[StatWidget] Error updating CI: {e}")

    def _update_confluence_display(self, timeframe: str):
        """Update Probabilistic Confluence display"""
        try:
            conf_calc = self.manager.get_calculator(timeframe, 'confluence')
            if not conf_calc:
                return

            # Sample opportunity with some factors
            opportunity = {
                'pattern': self.current_pattern,
                'symbol': self.current_symbol,
                'volume_ok': True,
                'mtf_aligned': True,
                'pattern_strength': 8,
                'spread_ok': True
            }

            analysis = conf_calc.get_detailed_analysis(opportunity)

            self.conf_base_label.setText(f"Base Probability: {analysis['base_probability']*100:.1f}%")
            self.conf_final_label.setText(f"Final Probability: {analysis['final_probability']*100:.1f}%")
            self.conf_factors_label.setText(f"Factors Applied: {analysis['num_factors']} ({', '.join(analysis['factors_applied'][:3])}...)")
            self.conf_score_label.setText(f"Confidence Score: {analysis['confidence_score']:.0f}/100")
            self.conf_recommendation_label.setText(analysis['recommendation'])

        except Exception as e:
            vprint(f"[StatWidget] Error updating Confluence: {e}")
