"""
AppleTrader Pro - Multi-Symbol Correlation Heatmap Widget
PyQt6 widget for displaying correlation matrix and divergence alerts
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem,
                            QPushButton, QHeaderView, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from typing import Dict, List
import pandas as pd

from widgets.correlation_analyzer import correlation_analyzer
from core.ai_assist_base import AIAssistMixin
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.multi_symbol_manager import get_all_symbols


class CorrelationHeatmapWidget(QWidget, AIAssistMixin):
    """
    Multi-Symbol Correlation Heatmap Display Widget (AI-Enhanced)

    Shows:
    - Correlation matrix (color-coded heatmap)
    - Strongest positive/negative correlations
    - Divergence alerts (when correlations break)
    - Historical average vs current
    - AI-powered correlation insights
    """

    divergence_detected = pyqtSignal(dict)  # Emits divergence alert

    def __init__(self, parent=None):
        super().__init__(parent)

        # CRITICAL: Initialize current_symbol BEFORE calling update_from_live_data
        self.current_symbol = "EURUSD"
        self.correlation_data = None

        # Setup AI assistance
        self.setup_ai_assist("correlation_heatmap")

        self.init_ui()

        # Connect to demo mode changes
        demo_mode_manager.mode_changed.connect(self.on_mode_changed)

        # Auto-refresh every 5 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(5000)

        # Initial update
        self.update_data()

    def update_from_live_data(self):
        """Update with live data - MULTI-SYMBOL support via MT5"""
        from core.data_manager import data_manager

        print("    → [Correlation] Fetching multi-symbol data for correlation analysis")

        try:
            # STRATEGY 1: Fetch multi-symbol data directly from MT5
            multi_symbol_data = self.fetch_multi_symbol_data_from_mt5()

            if multi_symbol_data and len(multi_symbol_data) >= 2:
                # SUCCESS: We have real multi-symbol data!
                print(f"    ✓ Got REAL data for {len(multi_symbol_data)} symbols from MT5")

                # Calculate correlations
                correlation_report = correlation_analyzer.calculate_correlations(
                    multi_symbol_data,
                    short_period=20,  # Current correlation (20 bars)
                    long_period=100   # Historical average (100 bars)
                )

                # Update display
                self.update_correlation_data(correlation_report)
                self.status_label.setText(f"Live: {len(multi_symbol_data)} symbols analyzed")
                print(f"    ✓ LIVE CORRELATION: {correlation_report['pairs_calculated']} pairs calculated")
                return

            # STRATEGY 2: Try mt5_connector (JSON file approach)
            from core.mt5_connector import mt5_connector
            all_symbols_data = mt5_connector.get_all_symbols_data()

            if all_symbols_data and len(all_symbols_data) >= 2:
                print(f"    ✓ Got data for {len(all_symbols_data)} symbols from MT5 JSON")
                correlation_report = correlation_analyzer.calculate_correlations(
                    all_symbols_data, short_period=20, long_period=100
                )
                self.update_correlation_data(correlation_report)
                self.status_label.setText(f"Live: {len(all_symbols_data)} symbols analyzed")
                return

            # FALLBACK: Not enough data for correlation
            print("    ⚠️ Need at least 2 symbols for correlation analysis")
            self.status_label.setText("Live: Need at least 2 symbols")

        except Exception as e:
            print(f"[Correlation] Error fetching live data: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText("Live: Error fetching data")

    def fetch_multi_symbol_data_from_mt5(self) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols directly from MT5"""
        try:
            import MetaTrader5 as mt5
            import pandas as pd

            # Check if MT5 is initialized
            if not mt5.initialize():
                return {}

            symbols_data = {}

            # Get all symbols for correlation
            symbols = get_all_symbols()

            print(f"    → Fetching data from MT5 for {len(symbols)} symbols (correlation analysis)...")

            for symbol in symbols:
                try:
                    # Fetch H4 candles for correlation (need decent sample size)
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 200)

                    if rates is not None and len(rates) > 0:
                        # Convert to DataFrame
                        df = pd.DataFrame(rates)

                        # Add required columns
                        if 'time' in df.columns:
                            df['time'] = pd.to_datetime(df['time'], unit='s')

                        symbols_data[symbol] = df
                        print(f"    ✓ {symbol}: Got {len(df)} candles")

                except Exception as e:
                    print(f"    ✗ {symbol}: Failed ({str(e)[:50]})")
                    continue

            return symbols_data

        except ImportError:
            print("    ⚠️ MetaTrader5 module not available")
            return {}
        except Exception as e:
            print(f"    ⚠️ MT5 fetch error: {e}")
            return {}

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # Get demo correlation data
            symbols = get_all_symbols()
            demo_matrix = get_demo_data('correlation', symbols=symbols)
            if demo_matrix:
                # Wrap demo matrix in expected report format
                correlation_report = {
                    'correlation_matrix': demo_matrix,
                    'divergence_alerts': []  # No alerts in demo mode
                }
                self.update_correlation_data(correlation_report)
                self.status_label.setText(f"Demo Mode - {len(symbols)} symbols")
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.correlation_data:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        print(f"Correlation Heatmap widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Custom AI analysis for correlation heatmap

        Args:
            prediction: ML prediction data from ml_integration
            widget_data: Current correlation data

        Returns:
            Formatted suggestion dictionary
        """
        from core.ml_integration import create_ai_suggestion

        if not self.correlation_data:
            return create_ai_suggestion(
                widget_type="correlation_heatmap",
                text="No correlation data available",
                confidence=0.0
            )

        # Find strongest correlations
        strongest_pos = max(
            [(k, v) for k, v in self.correlation_data.items() if v > 0],
            key=lambda x: x[1],
            default=(None, 0)
        )
        strongest_neg = min(
            [(k, v) for k, v in self.correlation_data.items() if v < 0],
            key=lambda x: x[1],
            default=(None, 0)
        )

        # Analyze correlation strength
        if strongest_pos[1] >= 0.8:
            confidence = 0.85
            action_emoji = "🔥"
            action = f"Strong positive correlation detected"
            color = "green"
        elif strongest_neg[1] <= -0.8:
            confidence = 0.85
            action_emoji = "⚡"
            action = f"Strong negative correlation detected"
            color = "red"
        elif strongest_pos[1] >= 0.6 or strongest_neg[1] <= -0.6:
            confidence = 0.70
            action_emoji = "✓"
            action = f"Moderate correlations present"
            color = "yellow"
        else:
            confidence = 0.50
            action_emoji = "ℹ️"
            action = f"Weak correlations across pairs"
            color = "blue"

        # Build suggestion text
        suggestion_text = f"{action}\n\n"
        if strongest_pos[0]:
            suggestion_text += f"📈 Strongest Positive: {strongest_pos[0]} ({strongest_pos[1]:.2f})\n"
        if strongest_neg[0]:
            suggestion_text += f"📉 Strongest Negative: {strongest_neg[0]} ({strongest_neg[1]:.2f})\n"
        suggestion_text += "\n"

        # Add trading implications
        if strongest_pos[1] >= 0.8:
            suggestion_text += "💡 Trading Implication:\n"
            suggestion_text += "✓ Pairs moving together - hedge or diversify\n"
            suggestion_text += "✓ Consider portfolio risk concentration"
        elif strongest_neg[1] <= -0.8:
            suggestion_text += "💡 Trading Implication:\n"
            suggestion_text += "✓ Pairs moving opposite - hedging opportunity\n"
            suggestion_text += "✓ Consider mean reversion strategies"
        else:
            suggestion_text += "💡 Trading Implication:\n"
            suggestion_text += "⚠️ Pairs moving independently\n"
            suggestion_text += "⚠️ Diversification benefits may be limited"

        return create_ai_suggestion(
            widget_type="correlation_heatmap",
            text=suggestion_text,
            confidence=confidence,
            emoji=action_emoji,
            color=color
        )

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🔥 Multi-Symbol Correlation Heatmap")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # AI Assist checkbox
        self.create_ai_checkbox(header_layout)

        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_requested)
        self.refresh_btn.setMaximumWidth(100)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # === DIVERGENCE ALERTS ===
        alerts_group = QGroupBox("🚨 Divergence Opportunities")
        alerts_layout = QVBoxLayout()

        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(120)
        self.alerts_text.setFont(QFont("Courier", 9))
        alerts_layout.addWidget(self.alerts_text)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # === CORRELATION MATRIX TABLE ===
        matrix_group = QGroupBox("Correlation Matrix")
        matrix_layout = QVBoxLayout()

        self.correlation_table = QTableWidget()
        self.correlation_table.setFont(QFont("Courier", 9))
        self.correlation_table.verticalHeader().setVisible(True)
        self.correlation_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.correlation_table.setMaximumHeight(250)
        matrix_layout.addWidget(self.correlation_table)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))

        legend_items = [
            ("Strong +", "#006400"),
            ("Moderate +", "#90EE90"),
            ("Neutral", "#808080"),
            ("Moderate -", "#FFA500"),
            ("Strong -", "#8B0000")
        ]

        for text, color in legend_items:
            legend_label = QLabel(f"  {text}  ")
            legend_label.setStyleSheet(f"""
                background-color: {color};
                color: white;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 8pt;
            """)
            legend_layout.addWidget(legend_label)

        legend_layout.addStretch()
        matrix_layout.addLayout(legend_layout)

        matrix_group.setLayout(matrix_layout)
        layout.addWidget(matrix_group)

        # === TOP CORRELATIONS ===
        top_group = QGroupBox("🔝 Top Correlations")
        top_layout = QHBoxLayout()

        # Positive
        positive_col = QVBoxLayout()
        positive_col.addWidget(QLabel("🟢 Strongest Positive:"))
        self.positive_text = QTextEdit()
        self.positive_text.setReadOnly(True)
        self.positive_text.setMaximumHeight(100)
        self.positive_text.setFont(QFont("Courier", 9))
        positive_col.addWidget(self.positive_text)
        top_layout.addLayout(positive_col)

        # Negative
        negative_col = QVBoxLayout()
        negative_col.addWidget(QLabel("🔴 Strongest Negative:"))
        self.negative_text = QTextEdit()
        self.negative_text.setReadOnly(True)
        self.negative_text.setMaximumHeight(100)
        self.negative_text.setFont(QFont("Courier", 9))
        negative_col.addWidget(self.negative_text)
        top_layout.addLayout(negative_col)

        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        # === AI SUGGESTION FRAME ===
        self.create_ai_suggestion_frame(layout)

        # === STATUS ===
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 8))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Apply dark theme
        self.apply_dark_theme()

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
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                gridline-color: #444;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444;
                padding: 5px;
                font-weight: bold;
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
        """)

    def update_correlation_data(self, correlation_report: Dict):
        """
        Update display with new correlation data

        Args:
            correlation_report: Report from correlation_analyzer
        """
        self.correlation_data = correlation_report

        # Update divergence alerts
        alerts = correlation_report.get('divergence_alerts', [])
        if alerts:
            alert_lines = []
            for alert in alerts[:5]:  # Top 5
                alert_lines.append(alert['message'])
                alert_lines.append(f"→ {alert['recommendation']}")
                alert_lines.append("")

                # Emit signal for critical divergences
                if alert['type'] in ['CORRELATION_BREAKDOWN', 'INVERSE_BREAKDOWN']:
                    self.divergence_detected.emit(alert)

            self.alerts_text.setPlainText('\n'.join(alert_lines))
        else:
            self.alerts_text.setPlainText("✓ No significant divergences detected")

        # Update correlation matrix table
        self.update_correlation_table(correlation_report)

        # Update top correlations
        strongest_positive = correlation_report.get('strongest_positive', [])
        strongest_negative = correlation_report.get('strongest_negative', [])

        if strongest_positive:
            pos_lines = []
            for item in strongest_positive[:5]:
                # Handle both tuple formats: (s1, s2, corr) or ((s1, s2), corr)
                if len(item) == 3:
                    s1, s2, corr = item
                else:
                    (s1, s2), corr = item
                pos_lines.append(f"{s1}/{s2}: {corr:+.3f}")
            self.positive_text.setPlainText('\n'.join(pos_lines))
        else:
            self.positive_text.setPlainText("No data")

        if strongest_negative:
            neg_lines = []
            for item in strongest_negative[:5]:
                # Handle both tuple formats: (s1, s2, corr) or ((s1, s2), corr)
                if len(item) == 3:
                    s1, s2, corr = item
                else:
                    (s1, s2), corr = item
                neg_lines.append(f"{s1}/{s2}: {corr:+.3f}")
            self.negative_text.setPlainText('\n'.join(neg_lines))
        else:
            self.negative_text.setPlainText("No data")

        # Update status
        pairs_count = correlation_report.get('pairs_calculated', 0)
        symbols_count = correlation_report.get('symbols_analyzed', 0)
        last_update = correlation_report.get('last_update')

        if last_update:
            time_str = last_update.strftime("%H:%M:%S")
            self.status_label.setText(
                f"Updated: {time_str} | {pairs_count} pairs, {symbols_count} symbols"
            )

    def update_correlation_table(self, correlation_report: Dict):
        """Update the correlation matrix table"""
        correlation_matrix = correlation_report.get('correlation_matrix', None)

        # Check if correlation_matrix is None or empty
        if correlation_matrix is None:
            self.correlation_table.setRowCount(0)
            self.correlation_table.setColumnCount(0)
            return

        # Handle DataFrame format (from sample data)
        if isinstance(correlation_matrix, pd.DataFrame):
            if correlation_matrix.empty:
                self.correlation_table.setRowCount(0)
                self.correlation_table.setColumnCount(0)
                return

            symbols = list(correlation_matrix.index)[:8]  # Limit to 8 for display

            # Setup table
            self.correlation_table.setRowCount(len(symbols))
            self.correlation_table.setColumnCount(len(symbols))
            self.correlation_table.setHorizontalHeaderLabels(symbols)
            self.correlation_table.setVerticalHeaderLabels(symbols)

            # Fill table from DataFrame
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    corr = correlation_matrix.loc[sym1, sym2]

                    # Format value
                    item = QTableWidgetItem(f"{corr:+.2f}")

                    # Color code based on correlation strength
                    if corr >= 0.7:
                        color = '#00ff00'  # Strong positive - green
                    elif corr >= 0.3:
                        color = '#88ff88'  # Moderate positive - light green
                    elif corr >= -0.3:
                        color = '#808080'  # Weak - gray
                    elif corr >= -0.7:
                        color = '#ff8888'  # Moderate negative - light red
                    else:
                        color = '#ff0000'  # Strong negative - red

                    item.setBackground(QBrush(QColor(color)))
                    item.setForeground(QBrush(QColor("#ffffff")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.correlation_table.setItem(i, j, item)

        else:
            # Handle dict format (nested dict: {sym1: {sym2: corr}})
            if not correlation_matrix:
                self.correlation_table.setRowCount(0)
                self.correlation_table.setColumnCount(0)
                return

            # Get symbols from outer dictionary keys
            symbols = sorted(list(correlation_matrix.keys()))[:8]  # Limit to 8 for display

            # Setup table
            self.correlation_table.setRowCount(len(symbols))
            self.correlation_table.setColumnCount(len(symbols))
            self.correlation_table.setHorizontalHeaderLabels(symbols)
            self.correlation_table.setVerticalHeaderLabels(symbols)

            # Fill table from nested dictionary
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    # Get correlation value from nested dict
                    corr = correlation_matrix.get(sym1, {}).get(sym2, None)

                    if corr is not None:
                        # Format value
                        item = QTableWidgetItem(f"{corr:+.2f}")

                        # Color code based on correlation strength
                        if corr >= 0.7:
                            color = '#00ff00'  # Strong positive - green
                        elif corr >= 0.3:
                            color = '#88ff88'  # Moderate positive - light green
                        elif corr >= -0.3:
                            color = '#808080'  # Weak - gray
                        elif corr >= -0.7:
                            color = '#ff8888'  # Moderate negative - light red
                        else:
                            color = '#ff0000'  # Strong negative - red

                        item.setBackground(QBrush(QColor(color)))
                        item.setForeground(QBrush(QColor("#ffffff")))
                    else:
                        item = QTableWidgetItem("--")
                        item.setBackground(QBrush(QColor("#2b2b2b")))
                        item.setForeground(QBrush(QColor("#888888")))

                    # Center align
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Make read-only
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.correlation_table.setItem(i, j, item)

    def set_symbol(self, symbol: str):
        """Update current symbol (triggers refresh)"""
        # This widget shows ALL pairs correlation, but we refresh on symbol change
        self.on_refresh_requested()

    def on_refresh_requested(self):
        """Handle refresh request"""
        self.status_label.setText("Refreshing...")
        # Actual data calculation done by parent/controller

    def scan_and_update(self, market_data: Dict[str, pd.DataFrame],
                       short_period: int = 20, long_period: int = 100):
        """
        Convenience method to scan and update in one call

        Args:
            market_data: {symbol: DataFrame} with OHLC data
            short_period: Period for current correlation
            long_period: Period for historical average
        """
        # Run analysis
        report = correlation_analyzer.calculate_correlations(
            market_data, short_period, long_period
        )

        # Update display
        self.update_correlation_data(report)

    def clear_display(self):
        """Clear all displays"""
        self.alerts_text.setPlainText("No data")
        self.positive_text.setPlainText("No data")
        self.negative_text.setPlainText("No data")
        self.correlation_table.setRowCount(0)
        self.correlation_table.setColumnCount(0)
        self.status_label.setText("Status: Waiting for data")

    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        return correlation_analyzer.get_correlation(symbol1, symbol2)

    def get_correlated_pairs(self, symbol: str, threshold: float = 0.7) -> List:
        """Get pairs correlated with given symbol"""
        return correlation_analyzer.get_correlated_pairs(symbol, threshold)

    def load_sample_data(self):
        """Load sample correlation data for demonstration"""
        import numpy as np

        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF', 'USDCAD']

        # Create sample correlation matrix
        corr_matrix = pd.DataFrame(
            [
                [1.00, 0.85, -0.72, 0.68, -0.91, -0.65],  # EURUSD
                [0.85, 1.00, -0.68, 0.72, -0.88, -0.61],  # GBPUSD
                [-0.72, -0.68, 1.00, -0.45, 0.74, 0.58],  # USDJPY
                [0.68, 0.72, -0.45, 1.00, -0.71, -0.55],  # AUDUSD
                [-0.91, -0.88, 0.74, -0.71, 1.00, 0.68],  # USDCHF
                [-0.65, -0.61, 0.58, -0.55, 0.68, 1.00],  # USDCAD
            ],
            index=symbols,
            columns=symbols
        )

        # Create sample divergence alerts
        divergences = [
            {
                'pair1': 'EURUSD',
                'pair2': 'GBPUSD',
                'current_corr': 0.85,
                'avg_corr': 0.92,
                'divergence_score': 8.2,
                'type': 'BREAKDOWN'
            },
            {
                'pair1': 'USDJPY',
                'pair2': 'USDCHF',
                'current_corr': 0.74,
                'avg_corr': 0.68,
                'divergence_score': 6.5,
                'type': 'STRENGTHENING'
            }
        ]

        # Create report structure
        report = {
            'correlation_matrix': corr_matrix,
            'divergences': divergences,
            'strongest_positive': [
                ('EURUSD', 'USDCHF', -0.91),
                ('EURUSD', 'GBPUSD', 0.85)
            ],
            'strongest_negative': [
                ('EURUSD', 'USDJPY', -0.72),
                ('GBPUSD', 'USDJPY', -0.68)
            ]
        }

        self.update_correlation_data(report)
