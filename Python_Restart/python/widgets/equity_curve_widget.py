"""
AppleTrader Pro - Equity Curve & Drawdown Widget
PyQt6 widget for displaying equity curve and drawdown analysis
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QTextEdit, QFrame, QProgressBar,
                            QPushButton, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import datetime

from widgets.equity_curve_analyzer import equity_curve_analyzer


class EquityCurveCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for equity curve"""

    def __init__(self, parent=None):
        fig = Figure(figsize=(8, 4), facecolor='#1e1e1e')
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        # Style the plot
        self.axes.set_facecolor('#2b2b2b')
        self.axes.tick_params(colors='white')
        self.axes.spines['bottom'].set_color('#444')
        self.axes.spines['top'].set_color('#444')
        self.axes.spines['left'].set_color('#444')
        self.axes.spines['right'].set_color('#444')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')

    def plot_equity_curve(self, df):
        """Plot the equity curve"""
        self.axes.clear()

        if df is None or len(df) == 0:
            self.axes.text(0.5, 0.5, 'No data yet',
                          ha='center', va='center',
                          transform=self.axes.transAxes,
                          color='white', fontsize=14)
            self.draw()
            return

        # Plot equity line
        self.axes.plot(df['timestamp'], df['balance'],
                      color='#00ff00', linewidth=2, label='Equity')

        # Add starting balance line
        starting_balance = df['balance'].iloc[0]
        self.axes.axhline(y=starting_balance, color='#888',
                         linestyle='--', linewidth=1,
                         label='Starting Balance')

        # Format
        self.axes.set_xlabel('Date', color='white')
        self.axes.set_ylabel('Balance ($)', color='white')
        self.axes.set_title('Equity Curve (Last 30 Days)', color='white')
        self.axes.legend(facecolor='#2b2b2b', edgecolor='#444',
                        labelcolor='white')
        self.axes.grid(True, alpha=0.2, color='#444')

        # Rotate x-axis labels
        plt.setp(self.axes.xaxis.get_majorticklabels(), rotation=45, ha='right')

        self.figure.tight_layout()
        self.draw()


class EquityCurveWidget(QWidget):
    """
    Equity Curve & Drawdown Display Widget

    Shows:
    - Live equity curve chart
    - Current balance and equity
    - Drawdown metrics
    - Daily/weekly loss limits with warnings
    - Win rate and statistics
    - Psychological state alerts
    """

    alert_triggered = pyqtSignal(dict)  # Emits alert data

    def __init__(self, parent=None):
        super().__init__(parent)

        # CRITICAL: Initialize current_symbol BEFORE starting timer
        self.current_symbol = "EURUSD"

        self.init_ui()

        # Auto-refresh every 2 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_from_live_data)
        self.refresh_timer.start(2000)

        # Initial update with live data
        self.update_from_live_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        title = QLabel("📊 Equity Curve & Drawdown Analyzer")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # === BALANCE OVERVIEW ===
        balance_frame = QFrame()
        balance_frame.setFrameShape(QFrame.Shape.StyledPanel)
        balance_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a4a;
                border: 2px solid #00aaff;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        balance_layout = QHBoxLayout(balance_frame)

        # Balance
        balance_col = QVBoxLayout()
        balance_col.addWidget(QLabel("Balance"))
        self.balance_label = QLabel("$10,000.00")
        self.balance_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.balance_label.setStyleSheet("color: #00ff00; border: none;")
        balance_col.addWidget(self.balance_label)
        balance_layout.addLayout(balance_col)

        # Equity
        equity_col = QVBoxLayout()
        equity_col.addWidget(QLabel("Equity"))
        self.equity_label = QLabel("$10,000.00")
        self.equity_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.equity_label.setStyleSheet("color: #00aaff; border: none;")
        equity_col.addWidget(self.equity_label)
        balance_layout.addLayout(equity_col)

        # Return %
        return_col = QVBoxLayout()
        return_col.addWidget(QLabel("Return"))
        self.return_label = QLabel("+0.0%")
        self.return_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.return_label.setStyleSheet("color: #ffaa00; border: none;")
        return_col.addWidget(self.return_label)
        balance_layout.addLayout(return_col)

        layout.addWidget(balance_frame)

        # === EQUITY CURVE CHART ===
        chart_group = QGroupBox("Equity Curve")
        chart_layout = QVBoxLayout()

        self.equity_canvas = EquityCurveCanvas()
        chart_layout.addWidget(self.equity_canvas)

        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        # === DRAWDOWN ANALYSIS ===
        dd_group = QGroupBox("📉 Drawdown Analysis")
        dd_layout = QGridLayout()

        # Current DD
        dd_layout.addWidget(QLabel("Current:"), 0, 0)
        self.current_dd_label = QLabel("0.0%")
        self.current_dd_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
        dd_layout.addWidget(self.current_dd_label, 0, 1)

        self.current_dd_status = QLabel("✓ HEALTHY")
        self.current_dd_status.setStyleSheet("color: #00ff00;")
        dd_layout.addWidget(self.current_dd_status, 0, 2)

        # Max DD
        dd_layout.addWidget(QLabel("Max DD:"), 1, 0)
        self.max_dd_label = QLabel("0.0%")
        self.max_dd_label.setFont(QFont("Courier", 11))
        dd_layout.addWidget(self.max_dd_label, 1, 1)

        dd_group.setLayout(dd_layout)
        layout.addWidget(dd_group)

        # === LOSS LIMITS ===
        limits_group = QGroupBox("⚠️ Loss Limits")
        limits_layout = QVBoxLayout()

        # Daily limit
        daily_layout = QHBoxLayout()
        daily_layout.addWidget(QLabel("Daily:"))
        self.daily_progress = QProgressBar()
        self.daily_progress.setMaximum(100)
        self.daily_progress.setFormat("%p% used")
        daily_layout.addWidget(self.daily_progress, 1)
        self.daily_remaining_label = QLabel("2.0% remaining")
        self.daily_remaining_label.setFont(QFont("Courier", 9))
        daily_layout.addWidget(self.daily_remaining_label)
        limits_layout.addLayout(daily_layout)

        # Weekly limit
        weekly_layout = QHBoxLayout()
        weekly_layout.addWidget(QLabel("Weekly:"))
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setMaximum(100)
        self.weekly_progress.setFormat("%p% used")
        weekly_layout.addWidget(self.weekly_progress, 1)
        self.weekly_remaining_label = QLabel("5.0% remaining")
        self.weekly_remaining_label.setFont(QFont("Courier", 9))
        weekly_layout.addWidget(self.weekly_remaining_label)
        limits_layout.addLayout(weekly_layout)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # === STATISTICS ===
        stats_group = QGroupBox("📈 Statistics")
        stats_layout = QGridLayout()

        stats_layout.addWidget(QLabel("Win Rate:"), 0, 0)
        self.win_rate_label = QLabel("--")
        self.win_rate_label.setFont(QFont("Courier", 10))
        stats_layout.addWidget(self.win_rate_label, 0, 1)

        stats_layout.addWidget(QLabel("Profit Factor:"), 0, 2)
        self.profit_factor_label = QLabel("--")
        self.profit_factor_label.setFont(QFont("Courier", 10))
        stats_layout.addWidget(self.profit_factor_label, 0, 3)

        stats_layout.addWidget(QLabel("Avg Win:"), 1, 0)
        self.avg_win_label = QLabel("--")
        self.avg_win_label.setFont(QFont("Courier", 10))
        stats_layout.addWidget(self.avg_win_label, 1, 1)

        stats_layout.addWidget(QLabel("Avg Loss:"), 1, 2)
        self.avg_loss_label = QLabel("--")
        self.avg_loss_label.setFont(QFont("Courier", 10))
        stats_layout.addWidget(self.avg_loss_label, 1, 3)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # === ALERTS ===
        alerts_group = QGroupBox("🚨 Active Alerts")
        alerts_layout = QVBoxLayout()

        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(100)
        self.alerts_text.setFont(QFont("Courier", 9))
        alerts_layout.addWidget(self.alerts_text)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

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
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2b2b2b;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #ff6600;
                border-radius: 2px;
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
        # Equity data is managed internally, just refresh display
        self.refresh_display()

    def load_sample_data(self):
        """Load sample trades for demonstration"""
        from datetime import timedelta

        # Add 15 sample trades over the last 10 days
        base_time = datetime.now() - timedelta(days=10)

        sample_trades = [
            ('EURUSD', 'BUY', 1.10000, 1.10150, 0.1, 150, 15),
            ('GBPUSD', 'SELL', 1.26500, 1.26400, 0.1, 100, 10),
            ('USDJPY', 'BUY', 148.500, 148.700, 0.1, 200, 20),
            ('EURUSD', 'SELL', 1.10200, 1.10350, 0.1, -150, -15),  # Loss
            ('AUDUSD', 'BUY', 0.66000, 0.66120, 0.1, 120, 12),
            ('EURUSD', 'BUY', 1.10100, 1.10280, 0.1, 180, 18),
            ('GBPUSD', 'BUY', 1.26300, 1.26250, 0.1, -50, -5),  # Loss
            ('USDJPY', 'SELL', 149.000, 148.800, 0.1, 200, 20),
            ('EURUSD', 'BUY', 1.10050, 1.10200, 0.1, 150, 15),
            ('NZDUSD', 'BUY', 0.61000, 0.61080, 0.1, 80, 8),
            ('EURUSD', 'SELL', 1.10300, 1.10450, 0.1, -150, -15),  # Loss
            ('GBPUSD', 'BUY', 1.26400, 1.26550, 0.1, 150, 15),
            ('EURUSD', 'BUY', 1.10150, 1.10320, 0.1, 170, 17),
            ('USDJPY', 'BUY', 148.800, 149.000, 0.1, 200, 20),
            ('EURUSD', 'BUY', 1.10200, 1.10380, 0.1, 180, 18),
        ]

        for i, (symbol, direction, entry, exit, lots, profit, pips) in enumerate(sample_trades):
            entry_time = base_time + timedelta(hours=i*6)
            exit_time = entry_time + timedelta(hours=2)

            equity_curve_analyzer.add_trade(
                symbol, direction, entry, exit, lots,
                entry_time, exit_time, profit, pips
            )

    def refresh_display(self):
        """Refresh all displays with current data"""
        # Update balance/equity
        stats = equity_curve_analyzer.stats
        self.balance_label.setText(f"${equity_curve_analyzer.current_balance:,.2f}")
        self.equity_label.setText(f"${equity_curve_analyzer.current_equity:,.2f}")

        return_pct = stats['return_pct']
        return_color = '#00ff00' if return_pct >= 0 else '#ff0000'
        self.return_label.setText(f"{return_pct:+.1f}%")
        self.return_label.setStyleSheet(f"color: {return_color}; border: none;")

        # Update equity curve chart
        equity_df = equity_curve_analyzer.get_equity_curve_data(days=30)
        self.equity_canvas.plot_equity_curve(equity_df)

        # Update drawdown
        dd_analysis = equity_curve_analyzer.get_drawdown_analysis()

        current_dd = dd_analysis['current_drawdown_pct']
        self.current_dd_label.setText(f"{current_dd:.1f}%")

        # DD status
        if current_dd < 2:
            dd_status = "✓ HEALTHY"
            dd_color = "#00ff00"
        elif current_dd < 5:
            dd_status = "⚠️ MODERATE"
            dd_color = "#ffaa00"
        else:
            dd_status = "🛑 HIGH"
            dd_color = "#ff0000"

        self.current_dd_status.setText(dd_status)
        self.current_dd_status.setStyleSheet(f"color: {dd_color};")

        self.max_dd_label.setText(f"{dd_analysis['max_drawdown_pct']:.1f}%")

        # Update loss limits
        daily_used = abs(dd_analysis['daily_loss_pct'])
        daily_limit = dd_analysis['daily_limit_pct']
        daily_pct = min(100, (daily_used / daily_limit * 100)) if daily_limit > 0 else 0

        self.daily_progress.setValue(int(daily_pct))
        self.daily_remaining_label.setText(f"{dd_analysis['daily_remaining_pct']:.1f}% remaining")

        # Color code daily progress
        if daily_pct >= 100:
            daily_color = "#ff0000"
        elif daily_pct >= 75:
            daily_color = "#ff6600"
        else:
            daily_color = "#00ff00"

        self.daily_progress.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {daily_color}; }}
        """)

        weekly_used = abs(dd_analysis['weekly_loss_pct'])
        weekly_limit = dd_analysis['weekly_limit_pct']
        weekly_pct = min(100, (weekly_used / weekly_limit * 100)) if weekly_limit > 0 else 0

        self.weekly_progress.setValue(int(weekly_pct))
        self.weekly_remaining_label.setText(f"{dd_analysis['weekly_remaining_pct']:.1f}% remaining")

        # Color code weekly progress
        if weekly_pct >= 100:
            weekly_color = "#ff0000"
        elif weekly_pct >= 75:
            weekly_color = "#ff6600"
        else:
            weekly_color = "#00ff00"

        self.weekly_progress.setStyleSheet(f"""
            QProgressBar::chunk {{ background-color: {weekly_color}; }}
        """)

        # Update statistics
        if stats['total_trades'] > 0:
            self.win_rate_label.setText(
                f"{stats['win_rate']:.1f}% ({stats['wins']}/{stats['total_trades']})"
            )
            self.profit_factor_label.setText(f"{stats['profit_factor']:.2f}")
            self.avg_win_label.setText(f"${stats['avg_win']:.2f}")
            self.avg_loss_label.setText(f"${stats['avg_loss']:.2f}")
        else:
            self.win_rate_label.setText("No trades yet")
            self.profit_factor_label.setText("--")
            self.avg_win_label.setText("--")
            self.avg_loss_label.setText("--")

        # Update alerts
        alerts = equity_curve_analyzer.active_alerts
        if alerts:
            alert_lines = []
            for alert in alerts:
                alert_type = alert['type']
                message = alert['message']
                recommendation = alert['recommendation']

                alert_lines.append(f"{message}")
                alert_lines.append(f"→ {recommendation}")
                alert_lines.append("")

                # Emit signal for important alerts
                if alert_type == 'CRITICAL':
                    self.alert_triggered.emit(alert)

            self.alerts_text.setPlainText('\n'.join(alert_lines))
        else:
            self.alerts_text.setPlainText("✓ No alerts - Trading normally")

    def clear_display(self):
        """Clear all displays"""
        self.balance_label.setText("$0.00")
        self.equity_label.setText("$0.00")
        self.return_label.setText("0.0%")
        self.current_dd_label.setText("0.0%")
        self.max_dd_label.setText("0.0%")
        self.alerts_text.setPlainText("No data")
