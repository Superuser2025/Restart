"""
AppleTrader Pro - EMA Guide Widget
Real-time trading guidance based on EMA Ribbon analysis

EMAs: 216, 108, 54, 27, 9, 3 (fractal halving pattern)

Provides actionable guidance based on:
1. Trend Identification (stacking)
2. Entry Points (pullbacks)
3. Dynamic Support/Resistance
4. Momentum Reading (ribbon width)
5. Reversal Detection (crossovers)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTextEdit, QFrame, QGroupBox, QScrollArea,
                            QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np

from core.data_manager import data_manager
from core.verbose_mode_manager import vprint

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None


class EMAGuideWidget(QWidget):
    """
    EMA Guide Widget - Your Personal Trading Advisor

    Analyzes the EMA ribbon state and provides clear,
    actionable trading guidance based on current conditions.
    """

    # Signal emitted when analysis updates
    analysis_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_symbol = "EURUSD"
        self.current_timeframe = "H4"

        # EMA configuration (your signature setup)
        self.ema_periods = [216, 108, 54, 27, 9, 3]
        self.ema_colors = {
            216: '#8B5CF6',  # Deep Purple
            108: '#A855F7',  # Purple
            54: '#D946EF',   # Magenta
            27: '#F472B6',   # Pink
            9: '#38BDF8',    # Sky Blue
            3: '#06B6D4',    # Cyan
        }
        self.ema_names = {
            216: 'Major Trend',
            108: 'Long-term',
            54: 'Medium-term',
            27: 'Swing',
            9: 'Short-term',
            3: 'Immediate',
        }

        # Analysis cache
        self.current_analysis = None
        self.ema_values = {}
        self.candle_data = []

        self.init_ui()

        # Auto-update timer (every 3 seconds)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_analysis)
        self.update_timer.start(3000)

        # Initial analysis
        self.update_analysis()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # === HEADER ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #06B6D4);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header)

        title = QLabel("EMA TRADING GUIDE")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Symbol/Timeframe display
        self.symbol_label = QLabel(f"{self.current_symbol} | {self.current_timeframe}")
        self.symbol_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.symbol_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        header_layout.addWidget(self.symbol_label)

        layout.addWidget(header)

        # === MAIN BIAS DISPLAY ===
        self.bias_frame = QFrame()
        self.bias_frame.setMinimumHeight(80)
        self.bias_frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 3px solid #3B82F6;
                border-radius: 10px;
            }
        """)
        bias_layout = QVBoxLayout(self.bias_frame)

        self.bias_label = QLabel("ANALYZING...")
        self.bias_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.bias_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bias_label.setStyleSheet("color: #F59E0B;")
        bias_layout.addWidget(self.bias_label)

        self.bias_detail = QLabel("Loading EMA data...")
        self.bias_detail.setFont(QFont("Arial", 11))
        self.bias_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bias_detail.setStyleSheet("color: #94A3B8;")
        bias_layout.addWidget(self.bias_detail)

        layout.addWidget(self.bias_frame)

        # === ACTIVE CONDITIONS ===
        conditions_group = QGroupBox("ACTIVE CONDITIONS")
        conditions_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        conditions_group.setStyleSheet("""
            QGroupBox {
                color: #00aaff;
                border: 2px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        conditions_layout = QVBoxLayout(conditions_group)

        # Scrollable area for conditions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_widget)
        self.conditions_layout.setSpacing(8)
        scroll.setWidget(self.conditions_widget)

        conditions_layout.addWidget(scroll)
        layout.addWidget(conditions_group)

        # === EMA VALUES DISPLAY ===
        ema_group = QGroupBox("EMA VALUES")
        ema_group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        ema_group.setStyleSheet("""
            QGroupBox {
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        ema_grid = QGridLayout(ema_group)
        ema_grid.setSpacing(4)

        self.ema_value_labels = {}
        for i, period in enumerate(self.ema_periods):
            # Period label
            period_label = QLabel(f"EMA {period}")
            period_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            period_label.setStyleSheet(f"color: {self.ema_colors[period]};")
            ema_grid.addWidget(period_label, i // 3, (i % 3) * 2)

            # Value label
            value_label = QLabel("---")
            value_label.setFont(QFont("Courier", 9))
            value_label.setStyleSheet("color: #E2E8F0;")
            ema_grid.addWidget(value_label, i // 3, (i % 3) * 2 + 1)
            self.ema_value_labels[period] = value_label

        layout.addWidget(ema_group)

        # === TRADING PERSPECTIVE ===
        perspective_group = QGroupBox("TRADING PERSPECTIVE")
        perspective_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        perspective_group.setStyleSheet("""
            QGroupBox {
                color: #10B981;
                border: 2px solid #10B981;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        perspective_layout = QVBoxLayout(perspective_group)

        self.perspective_text = QTextEdit()
        self.perspective_text.setReadOnly(True)
        self.perspective_text.setMaximumHeight(150)
        self.perspective_text.setFont(QFont("Arial", 10))
        self.perspective_text.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                border: none;
                border-radius: 6px;
                color: #E2E8F0;
                padding: 10px;
            }
        """)
        perspective_layout.addWidget(self.perspective_text)

        layout.addWidget(perspective_group)

        layout.addStretch()

    def set_symbol(self, symbol: str):
        """Update the current symbol"""
        self.current_symbol = symbol
        self.symbol_label.setText(f"{self.current_symbol} | {self.current_timeframe}")
        self.update_analysis()

    def set_timeframe(self, timeframe: str):
        """Update the current timeframe"""
        self.current_timeframe = timeframe
        self.symbol_label.setText(f"{self.current_symbol} | {self.current_timeframe}")
        self.update_analysis()

    def calculate_ema(self, closes: list, period: int) -> list:
        """Calculate Exponential Moving Average"""
        if not closes or len(closes) < period:
            return [None] * len(closes)

        multiplier = 2.0 / (period + 1)
        ema_values = [None] * len(closes)

        # First EMA is SMA
        sma = sum(closes[:period]) / period
        ema_values[period - 1] = sma

        # Calculate subsequent EMAs
        for i in range(period, len(closes)):
            ema_values[i] = (closes[i] - ema_values[i-1]) * multiplier + ema_values[i-1]

        return ema_values

    def load_candle_data(self) -> bool:
        """Load candle data from MT5 or data manager"""
        try:
            if MT5_AVAILABLE and mt5.initialize():
                # Get timeframe constant
                tf_map = {
                    'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5,
                    'M15': mt5.TIMEFRAME_M15, 'M30': mt5.TIMEFRAME_M30,
                    'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
                    'D1': mt5.TIMEFRAME_D1, 'W1': mt5.TIMEFRAME_W1,
                }
                tf = tf_map.get(self.current_timeframe, mt5.TIMEFRAME_H4)

                # Get 300 candles (enough for 216 EMA + buffer)
                rates = mt5.copy_rates_from_pos(self.current_symbol, tf, 0, 300)

                if rates is not None and len(rates) > 0:
                    self.candle_data = []
                    for rate in rates:
                        self.candle_data.append({
                            'open': rate['open'],
                            'high': rate['high'],
                            'low': rate['low'],
                            'close': rate['close'],
                            'time': rate['time']
                        })
                    return True

            # Fallback to data manager
            df = data_manager.candle_buffer.get_data()
            if df is not None and len(df) > 0:
                self.candle_data = df.to_dict('records')
                return True

            return False

        except Exception as e:
            vprint(f"[EMA Guide] Error loading data: {e}")
            return False

    def update_analysis(self):
        """Update the EMA analysis and display"""
        if not self.load_candle_data():
            self.bias_label.setText("NO DATA")
            self.bias_detail.setText("Waiting for market data...")
            return

        if len(self.candle_data) < 220:
            self.bias_label.setText("INSUFFICIENT DATA")
            self.bias_detail.setText(f"Need 220+ candles, have {len(self.candle_data)}")
            return

        # Calculate all EMAs
        closes = [c['close'] for c in self.candle_data]
        current_price = closes[-1]
        current_idx = len(closes) - 1

        self.ema_values = {}
        for period in self.ema_periods:
            ema = self.calculate_ema(closes, period)
            if ema[current_idx] is not None:
                self.ema_values[period] = ema[current_idx]
                # Update value label
                self.ema_value_labels[period].setText(f"{ema[current_idx]:.5f}")

        if len(self.ema_values) < 6:
            self.bias_label.setText("CALCULATING...")
            return

        # Perform comprehensive analysis
        analysis = self.analyze_ema_conditions(current_price)
        self.current_analysis = analysis

        # Update UI
        self.update_bias_display(analysis)
        self.update_conditions_display(analysis)
        self.update_perspective_display(analysis)

        # Emit signal
        self.analysis_updated.emit(analysis)

    def analyze_ema_conditions(self, current_price: float) -> dict:
        """
        Comprehensive EMA analysis covering all 5 trading scenarios
        """
        analysis = {
            'price': current_price,
            'ema_values': self.ema_values.copy(),
            'conditions': [],
            'bias': 'NEUTRAL',
            'bias_strength': 0,
            'perspective': '',
            'action': 'WAIT',
        }

        ema = self.ema_values

        # ═══════════════════════════════════════════════════════════════
        # 1. TREND IDENTIFICATION (Stacking Analysis)
        # ═══════════════════════════════════════════════════════════════

        # Check bullish stack: 3 > 9 > 27 > 54 > 108 > 216
        bullish_stack = all(
            ema[self.ema_periods[i]] > ema[self.ema_periods[i+1]]
            for i in range(len(self.ema_periods) - 1)
        )

        # Check bearish stack: 3 < 9 < 27 < 54 < 108 < 216
        bearish_stack = all(
            ema[self.ema_periods[i]] < ema[self.ema_periods[i+1]]
            for i in range(len(self.ema_periods) - 1)
        )

        # Partial stacking
        fast_bullish = ema[3] > ema[9] > ema[27]  # Short-term bullish
        fast_bearish = ema[3] < ema[9] < ema[27]  # Short-term bearish
        slow_bullish = ema[54] > ema[108] > ema[216]  # Long-term bullish
        slow_bearish = ema[54] < ema[108] < ema[216]  # Long-term bearish

        if bullish_stack:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'STRONG UPTREND CONFIRMED',
                'description': 'All EMAs perfectly stacked bullish (3 > 9 > 27 > 54 > 108 > 216). This is the strongest bullish signal.',
                'color': '#10B981',
                'icon': '1',
                'action': 'Look for BUY opportunities on pullbacks to short EMAs'
            })
            analysis['bias'] = 'STRONG_BULL'
            analysis['bias_strength'] = 100

        elif bearish_stack:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'STRONG DOWNTREND CONFIRMED',
                'description': 'All EMAs perfectly stacked bearish (3 < 9 < 27 < 54 < 108 < 216). This is the strongest bearish signal.',
                'color': '#EF4444',
                'icon': '1',
                'action': 'Look for SELL opportunities on pullbacks to short EMAs'
            })
            analysis['bias'] = 'STRONG_BEAR'
            analysis['bias_strength'] = 100

        elif fast_bullish and slow_bullish:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'UPTREND IN PROGRESS',
                'description': 'Fast and slow EMAs both bullish aligned. Trend is healthy but watch for consolidation.',
                'color': '#10B981',
                'icon': '1',
                'action': 'Favor BUY trades, but be cautious of overextension'
            })
            analysis['bias'] = 'BULL'
            analysis['bias_strength'] = 75

        elif fast_bearish and slow_bearish:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'DOWNTREND IN PROGRESS',
                'description': 'Fast and slow EMAs both bearish aligned. Trend is healthy but watch for consolidation.',
                'color': '#EF4444',
                'icon': '1',
                'action': 'Favor SELL trades, but be cautious of overextension'
            })
            analysis['bias'] = 'BEAR'
            analysis['bias_strength'] = 75

        elif fast_bullish and slow_bearish:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'POTENTIAL TREND REVERSAL (Bullish)',
                'description': 'Fast EMAs turning bullish while slow EMAs still bearish. Watch for confirmation.',
                'color': '#F59E0B',
                'icon': '1',
                'action': 'Wait for slow EMAs to align before aggressive longs'
            })
            analysis['bias'] = 'NEUTRAL_BULL'
            analysis['bias_strength'] = 40

        elif fast_bearish and slow_bullish:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'POTENTIAL TREND REVERSAL (Bearish)',
                'description': 'Fast EMAs turning bearish while slow EMAs still bullish. Watch for confirmation.',
                'color': '#F59E0B',
                'icon': '1',
                'action': 'Wait for slow EMAs to align before aggressive shorts'
            })
            analysis['bias'] = 'NEUTRAL_BEAR'
            analysis['bias_strength'] = 40
        else:
            analysis['conditions'].append({
                'type': 'TREND',
                'title': 'CONSOLIDATION / CHOPPY',
                'description': 'EMAs are tangled with no clear direction. This is a low-probability trading environment.',
                'color': '#94A3B8',
                'icon': '1',
                'action': 'AVOID trading or use tight stops with reduced size'
            })
            analysis['bias'] = 'NEUTRAL'
            analysis['bias_strength'] = 20

        # ═══════════════════════════════════════════════════════════════
        # 2. ENTRY POINTS (Pullback Analysis)
        # ═══════════════════════════════════════════════════════════════

        # Price relative to EMAs
        above_3 = current_price > ema[3]
        above_9 = current_price > ema[9]
        above_27 = current_price > ema[27]
        above_54 = current_price > ema[54]
        above_108 = current_price > ema[108]
        above_216 = current_price > ema[216]

        # Distance from EMA 3 (as percentage)
        dist_from_3 = ((current_price - ema[3]) / current_price) * 100
        dist_from_9 = ((current_price - ema[9]) / current_price) * 100
        dist_from_27 = ((current_price - ema[27]) / current_price) * 100

        # Bullish pullback entries
        if analysis['bias'] in ['STRONG_BULL', 'BULL']:
            if not above_3 and above_9:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'SCALP BUY ZONE',
                    'description': f'Price pulled back to EMA 3 ({ema[3]:.5f}). In uptrend, this is a scalp entry point.',
                    'color': '#10B981',
                    'icon': '2',
                    'action': 'Consider SCALP BUY with tight stop below EMA 9'
                })
            elif not above_9 and above_27:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'SWING BUY ZONE',
                    'description': f'Price pulled back to EMA 9 ({ema[9]:.5f}). In uptrend, this is a quality swing entry.',
                    'color': '#10B981',
                    'icon': '2',
                    'action': 'Consider SWING BUY with stop below EMA 27'
                })
            elif not above_27 and above_54:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'DEEP PULLBACK BUY',
                    'description': f'Price at EMA 27 ({ema[27]:.5f}). Deep pullback in uptrend - higher risk but potential high reward.',
                    'color': '#F59E0B',
                    'icon': '2',
                    'action': 'Consider BUY with stop below EMA 54 - watch for confirmation'
                })

        # Bearish pullback entries
        elif analysis['bias'] in ['STRONG_BEAR', 'BEAR']:
            if above_3 and not above_9:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'SCALP SELL ZONE',
                    'description': f'Price pulled back to EMA 3 ({ema[3]:.5f}). In downtrend, this is a scalp entry point.',
                    'color': '#EF4444',
                    'icon': '2',
                    'action': 'Consider SCALP SELL with tight stop above EMA 9'
                })
            elif above_9 and not above_27:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'SWING SELL ZONE',
                    'description': f'Price pulled back to EMA 9 ({ema[9]:.5f}). In downtrend, this is a quality swing entry.',
                    'color': '#EF4444',
                    'icon': '2',
                    'action': 'Consider SWING SELL with stop above EMA 27'
                })
            elif above_27 and not above_54:
                analysis['conditions'].append({
                    'type': 'ENTRY',
                    'title': 'DEEP PULLBACK SELL',
                    'description': f'Price at EMA 27 ({ema[27]:.5f}). Deep pullback in downtrend - higher risk but potential high reward.',
                    'color': '#F59E0B',
                    'icon': '2',
                    'action': 'Consider SELL with stop above EMA 54 - watch for confirmation'
                })

        # ═══════════════════════════════════════════════════════════════
        # 3. DYNAMIC SUPPORT/RESISTANCE
        # ═══════════════════════════════════════════════════════════════

        # Find nearest EMA levels
        ema_distances = {}
        for period, value in ema.items():
            ema_distances[period] = abs(current_price - value)

        nearest_ema = min(ema_distances, key=ema_distances.get)
        nearest_dist_pct = (ema_distances[nearest_ema] / current_price) * 100

        if nearest_dist_pct < 0.1:  # Within 0.1% of an EMA
            ema_type = 'SUPPORT' if current_price > ema[nearest_ema] else 'RESISTANCE'
            analysis['conditions'].append({
                'type': 'SR_LEVEL',
                'title': f'AT EMA {nearest_ema} {ema_type}',
                'description': f'Price is testing EMA {nearest_ema} ({ema[nearest_ema]:.5f}) as dynamic {ema_type.lower()}. Key decision point.',
                'color': '#3B82F6',
                'icon': '3',
                'action': f'Watch for bounce (continuation) or break (reversal) of EMA {nearest_ema}'
            })

        # EMA confluence zones
        close_emas = [p for p, d in ema_distances.items() if (d / current_price) * 100 < 0.3]
        if len(close_emas) >= 2:
            analysis['conditions'].append({
                'type': 'SR_LEVEL',
                'title': 'EMA CONFLUENCE ZONE',
                'description': f'Multiple EMAs clustered near price: {", ".join([f"EMA {p}" for p in close_emas])}. Strong support/resistance area.',
                'color': '#8B5CF6',
                'icon': '3',
                'action': 'High probability reaction zone - watch for decisive move'
            })

        # ═══════════════════════════════════════════════════════════════
        # 4. MOMENTUM READING (Ribbon Width)
        # ═══════════════════════════════════════════════════════════════

        ribbon_width = abs(ema[3] - ema[216])
        ribbon_pct = (ribbon_width / current_price) * 100

        # Compare fast vs slow ribbon sections
        fast_ribbon = abs(ema[3] - ema[27])
        slow_ribbon = abs(ema[54] - ema[216])

        if ribbon_pct > 1.0:
            analysis['conditions'].append({
                'type': 'MOMENTUM',
                'title': 'EXTREME MOMENTUM',
                'description': f'Ribbon width is {ribbon_pct:.2f}% - very wide spread. Strong momentum but may be overextended.',
                'color': '#F59E0B',
                'icon': '4',
                'action': 'Trend strong but AVOID chasing. Wait for pullback or take profits'
            })
        elif ribbon_pct > 0.5:
            analysis['conditions'].append({
                'type': 'MOMENTUM',
                'title': 'HEALTHY MOMENTUM',
                'description': f'Ribbon width is {ribbon_pct:.2f}% - good spread indicating strong trend momentum.',
                'color': '#10B981',
                'icon': '4',
                'action': 'Momentum confirms trend - good environment for trend trades'
            })
        elif ribbon_pct > 0.2:
            analysis['conditions'].append({
                'type': 'MOMENTUM',
                'title': 'MODERATE MOMENTUM',
                'description': f'Ribbon width is {ribbon_pct:.2f}% - moderate spread. Trend present but not explosive.',
                'color': '#3B82F6',
                'icon': '4',
                'action': 'Trade with trend but use tighter stops'
            })
        else:
            analysis['conditions'].append({
                'type': 'MOMENTUM',
                'title': 'LOW MOMENTUM / COMPRESSION',
                'description': f'Ribbon width is {ribbon_pct:.2f}% - narrow spread. EMAs compressing, breakout likely coming.',
                'color': '#94A3B8',
                'icon': '4',
                'action': 'WAIT for breakout direction before trading'
            })

        # ═══════════════════════════════════════════════════════════════
        # 5. REVERSAL DETECTION (Crossovers)
        # ═══════════════════════════════════════════════════════════════

        # Check for recent crossovers (approximate by comparing distances)
        # 3/9 cross = scalp signal
        if abs(ema[3] - ema[9]) / current_price < 0.05:  # Very close
            cross_type = 'BULLISH' if ema[3] > ema[9] else 'BEARISH'
            analysis['conditions'].append({
                'type': 'CROSSOVER',
                'title': f'EMA 3/9 {cross_type} CROSS',
                'description': f'EMA 3 and EMA 9 are crossing. Short-term momentum shift detected.',
                'color': '#10B981' if cross_type == 'BULLISH' else '#EF4444',
                'icon': '5',
                'action': f'Scalp signal: Consider {"BUY" if cross_type == "BULLISH" else "SELL"} with quick targets'
            })

        # 27/54 cross = swing signal
        if abs(ema[27] - ema[54]) / current_price < 0.08:
            cross_type = 'BULLISH' if ema[27] > ema[54] else 'BEARISH'
            analysis['conditions'].append({
                'type': 'CROSSOVER',
                'title': f'EMA 27/54 {cross_type} CROSS',
                'description': f'EMA 27 and EMA 54 are crossing. Medium-term trend shift brewing.',
                'color': '#10B981' if cross_type == 'BULLISH' else '#EF4444',
                'icon': '5',
                'action': f'Swing signal: {"Bullish" if cross_type == "BULLISH" else "Bearish"} bias building'
            })

        # 108/216 cross = major trend shift
        if abs(ema[108] - ema[216]) / current_price < 0.1:
            cross_type = 'BULLISH' if ema[108] > ema[216] else 'BEARISH'
            analysis['conditions'].append({
                'type': 'CROSSOVER',
                'title': f'MAJOR TREND SHIFT ({cross_type})',
                'description': f'EMA 108 and EMA 216 are crossing. This is a significant long-term trend change.',
                'color': '#D946EF',
                'icon': '5',
                'action': f'Position signal: Major {"bullish" if cross_type == "BULLISH" else "bearish"} shift underway'
            })

        # Generate overall perspective
        analysis['perspective'] = self.generate_perspective(analysis)

        return analysis

    def generate_perspective(self, analysis: dict) -> str:
        """Generate the overall trading perspective text"""
        bias = analysis['bias']
        conditions = analysis['conditions']
        price = analysis['price']

        perspective = []

        # Main bias statement
        if bias == 'STRONG_BULL':
            perspective.append("PERSPECTIVE: You are in a STRONG UPTREND. The path of least resistance is UP.")
            perspective.append("")
            perspective.append("STRATEGY: Look ONLY for BUY opportunities. Sell signals should be ignored unless you see a major trend break.")
        elif bias == 'STRONG_BEAR':
            perspective.append("PERSPECTIVE: You are in a STRONG DOWNTREND. The path of least resistance is DOWN.")
            perspective.append("")
            perspective.append("STRATEGY: Look ONLY for SELL opportunities. Buy signals should be ignored unless you see a major trend break.")
        elif bias == 'BULL':
            perspective.append("PERSPECTIVE: The market has a BULLISH bias. Favor long positions but be selective.")
            perspective.append("")
            perspective.append("STRATEGY: Buy pullbacks to EMA 9 or EMA 27. Avoid buying at highs.")
        elif bias == 'BEAR':
            perspective.append("PERSPECTIVE: The market has a BEARISH bias. Favor short positions but be selective.")
            perspective.append("")
            perspective.append("STRATEGY: Sell rallies to EMA 9 or EMA 27. Avoid selling at lows.")
        elif bias in ['NEUTRAL_BULL', 'NEUTRAL_BEAR']:
            perspective.append("PERSPECTIVE: The market is in TRANSITION. A new trend may be forming.")
            perspective.append("")
            perspective.append("STRATEGY: Wait for confirmation. Trade small if you must trade.")
        else:
            perspective.append("PERSPECTIVE: The market is CHOPPY with no clear direction.")
            perspective.append("")
            perspective.append("STRATEGY: AVOID trading or use very tight risk management. This is not a good trading environment.")

        # Add specific actions from conditions
        perspective.append("")
        perspective.append("CURRENT ACTIONS:")

        entry_conditions = [c for c in conditions if c['type'] == 'ENTRY']
        if entry_conditions:
            for c in entry_conditions:
                perspective.append(f"  - {c['action']}")
        else:
            perspective.append("  - No immediate entry signal. Wait for pullback.")

        return "\n".join(perspective)

    def update_bias_display(self, analysis: dict):
        """Update the main bias display"""
        bias = analysis['bias']
        strength = analysis['bias_strength']

        bias_text = {
            'STRONG_BULL': 'STRONG BUY BIAS',
            'BULL': 'BUY BIAS',
            'NEUTRAL_BULL': 'CAUTIOUS BUY',
            'NEUTRAL': 'NEUTRAL',
            'NEUTRAL_BEAR': 'CAUTIOUS SELL',
            'BEAR': 'SELL BIAS',
            'STRONG_BEAR': 'STRONG SELL BIAS',
        }

        bias_colors = {
            'STRONG_BULL': ('#10B981', '#064E3B'),
            'BULL': ('#34D399', '#065F46'),
            'NEUTRAL_BULL': ('#FCD34D', '#78350F'),
            'NEUTRAL': ('#94A3B8', '#334155'),
            'NEUTRAL_BEAR': ('#FCD34D', '#78350F'),
            'BEAR': ('#F87171', '#7F1D1D'),
            'STRONG_BEAR': ('#EF4444', '#7F1D1D'),
        }

        text_color, border_color = bias_colors.get(bias, ('#94A3B8', '#334155'))

        self.bias_label.setText(bias_text.get(bias, 'ANALYZING...'))
        self.bias_label.setStyleSheet(f"color: {text_color};")

        self.bias_detail.setText(f"Confidence: {strength}% | Price: {analysis['price']:.5f}")

        self.bias_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1E293B;
                border: 3px solid {text_color};
                border-radius: 10px;
            }}
        """)

    def update_conditions_display(self, analysis: dict):
        """Update the conditions display"""
        # Clear existing conditions
        while self.conditions_layout.count():
            item = self.conditions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add each condition as a card
        for condition in analysis['conditions']:
            card = self.create_condition_card(condition)
            self.conditions_layout.addWidget(card)

        self.conditions_layout.addStretch()

    def create_condition_card(self, condition: dict) -> QFrame:
        """Create a condition card widget"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1E293B;
                border-left: 4px solid {condition['color']};
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header with icon and title
        header = QHBoxLayout()

        icon_label = QLabel(condition['icon'])
        icon_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        icon_label.setStyleSheet(f"""
            color: {condition['color']};
            background-color: {condition['color']}33;
            border-radius: 12px;
            padding: 2px 8px;
        """)
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(icon_label)

        title = QLabel(condition['title'])
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {condition['color']};")
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        # Description
        desc = QLabel(condition['description'])
        desc.setFont(QFont("Arial", 9))
        desc.setStyleSheet("color: #CBD5E1;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Action
        action = QLabel(f"ACTION: {condition['action']}")
        action.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        action.setStyleSheet("color: #F8FAFC; background-color: #334155; padding: 4px; border-radius: 4px;")
        action.setWordWrap(True)
        layout.addWidget(action)

        return card

    def update_perspective_display(self, analysis: dict):
        """Update the perspective text display"""
        self.perspective_text.setText(analysis['perspective'])
