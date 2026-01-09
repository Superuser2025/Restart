"""
AppleTrader Pro - Institutional Order Flow Widget
PyQt6 widget for displaying detected institutional orders
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGroupBox, QListWidget, QListWidgetItem,
                            QPushButton, QTextEdit, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import Dict, List
import pandas as pd

from widgets.order_flow_detector import order_flow_detector, InstitutionalOrder
from core.ai_assist_base import AIAssistMixin
from core.verbose_mode_manager import vprint
from core.demo_mode_manager import demo_mode_manager, is_demo_mode, get_demo_data
from core.verbose_mode_manager import vprint


class OrderFlowListItem(QWidget):
    """Custom widget for a single institutional order"""

    def __init__(self, order: InstitutionalOrder, parent=None):
        super().__init__(parent)
        self.order = order
        self.init_ui()

    def init_ui(self):
        """Initialize the list item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Direction emoji
        if self.order.direction == 'BUY':
            emoji = '🟢'
            color = '#00ff00'
        elif self.order.direction == 'SELL':
            emoji = '🔴'
            color = '#ff0000'
        else:
            emoji = '🟡'
            color = '#ffaa00'

        emoji_label = QLabel(emoji)
        emoji_label.setFont(QFont("Arial", 14))
        emoji_label.setFixedWidth(30)
        layout.addWidget(emoji_label)

        # Order details
        details_layout = QVBoxLayout()

        # Price and direction
        price_text = f"{self.order.direction}: {self.order.price:.5f}"
        price_label = QLabel(price_text)
        price_label.setFont(QFont("Courier", 10, QFont.Weight.Bold))
        price_label.setStyleSheet(f"color: {color};")
        details_layout.addWidget(price_label)

        # Size and type
        size_mb = self.order.estimated_size_usd / 1e6
        info_text = (f"{size_mb:.0f}M USD - {self.order.order_type.upper()} - "
                    f"{self.order.volume_multiplier:.1f}× volume")
        info_label = QLabel(info_text)
        info_label.setFont(QFont("Courier", 8))
        details_layout.addWidget(info_label)

        layout.addLayout(details_layout, 1)

        # Confidence
        confidence_label = QLabel(f"{self.order.confidence:.0f}%")
        confidence_label.setFont(QFont("Courier", 9))
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        confidence_label.setFixedWidth(50)
        layout.addWidget(confidence_label)

        # Time
        time_str = self.order.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Courier", 8))
        time_label.setStyleSheet("color: #888;")
        time_label.setFixedWidth(50)
        layout.addWidget(time_label)


class InstitutionalOrderFlowWidget(AIAssistMixin, QWidget):
    """
    Institutional Order Flow Display Widget

    Shows:
    - Recent institutional orders detected
    - Order type (absorption, sweep, accumulation)
    - Estimated size in USD
    - Confidence level
    - Order clusters (multiple orders at same level)
    """

    order_detected = pyqtSignal(dict)  # Emits when new order detected

    def __init__(self, parent=None):
        super().__init__(parent)

        # CRITICAL: Initialize current_symbol to default value
        self.current_symbol = "EURUSD"
        self.current_orders = []  # Store orders for AI analysis

        self.using_real_data = False  # Track if we're using real or demo data
        self.init_ui()
        self.setup_ai_assist("order_flow")

        # Auto-refresh every 3 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_data)
        self.refresh_timer.start(3000)

        # Initial update
        self.update_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("💼 Institutional Order Flow")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # AI checkbox placeholder
        self.ai_checkbox_placeholder = header_layout

        # Scan button
        self.scan_btn = QPushButton("🔍 Scan")
        self.scan_btn.clicked.connect(self.on_scan_requested)
        self.scan_btn.setMaximumWidth(80)
        header_layout.addWidget(self.scan_btn)

        layout.addLayout(header_layout)

        # === SUMMARY ===
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

        # Buy orders
        buy_col = QVBoxLayout()
        buy_col.addWidget(QLabel("🟢 BUY"))
        self.buy_count_label = QLabel("0")
        self.buy_count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.buy_count_label.setStyleSheet("color: #00ff00; border: none;")
        buy_col.addWidget(self.buy_count_label)
        summary_layout.addLayout(buy_col)

        # Sell orders
        sell_col = QVBoxLayout()
        sell_col.addWidget(QLabel("🔴 SELL"))
        self.sell_count_label = QLabel("0")
        self.sell_count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.sell_count_label.setStyleSheet("color: #ff0000; border: none;")
        sell_col.addWidget(self.sell_count_label)
        summary_layout.addLayout(sell_col)

        # Total
        total_col = QVBoxLayout()
        total_col.addWidget(QLabel("Total"))
        self.total_count_label = QLabel("0")
        self.total_count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.total_count_label.setStyleSheet("color: #00aaff; border: none;")
        total_col.addWidget(self.total_count_label)
        summary_layout.addLayout(total_col)

        layout.addWidget(summary_frame)

        # === RECENT ORDERS ===
        orders_group = QGroupBox("🔔 Recent Orders (Last 24h)")
        orders_layout = QVBoxLayout()

        self.orders_list = QListWidget()
        self.orders_list.setMinimumHeight(250)
        self.orders_list.setFont(QFont("Courier", 9))
        orders_layout.addWidget(self.orders_list)

        orders_group.setLayout(orders_layout)
        layout.addWidget(orders_group)

        # === ORDER CLUSTERS ===
        clusters_group = QGroupBox("📍 Order Clusters")
        clusters_layout = QVBoxLayout()

        self.clusters_text = QTextEdit()
        self.clusters_text.setReadOnly(True)
        self.clusters_text.setMaximumHeight(120)
        self.clusters_text.setFont(QFont("Courier", 9))
        clusters_layout.addWidget(self.clusters_text)

        clusters_group.setLayout(clusters_layout)
        layout.addWidget(clusters_group)

        # AI suggestion frame placeholder
        self.ai_suggestion_placeholder = layout

        # === STATUS ===
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Arial", 8))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Apply dark theme
        self.apply_dark_theme()

    def update_from_live_data(self):
        """Update with live data from data_manager"""
        from core.data_manager import data_manager

        vvprint("🔴 [Order Flow] LIVE MODE - Attempting to fetch real order flow data")

        # Get real candle data to analyze for institutional activity
        candles = data_manager.get_candles()

        if not candles or len(candles) < 20:
            vprint("    ⚠️ Not enough candle data for order flow analysis")
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Live: Waiting for data...")
            return

        # Analyze candles for institutional order flow patterns
        # Look for volume spikes, large candles, liquidity sweeps
        self.analyze_real_order_flow(candles)

        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Live: {self.current_symbol} - {len(self.current_orders)} orders detected")

    def analyze_real_order_flow(self, candles):
        """Analyze real candle data for institutional order flow"""
        vvprint(f"    → Analyzing {len(candles)} REAL candles for order flow patterns")

        # Clear old orders
        self.current_orders = []

        # Analyze last 50 candles for institutional activity
        recent_candles = candles[-50:] if len(candles) >= 50 else candles

        for i, candle in enumerate(recent_candles):
            # Look for large volume moves (proxy for institutional activity)
            candle_range = candle['high'] - candle['low']

            # Calculate average range
            avg_range = sum([c['high'] - c['low'] for c in recent_candles]) / len(recent_candles)

            # If this candle is significantly larger, it might be institutional
            if candle_range > avg_range * 1.5:
                order = {
                    'type': 'BUY' if candle['close'] > candle['open'] else 'SELL',
                    'price': candle['close'],
                    'volume': candle_range,  # Using range as proxy for volume
                    'timestamp': candle.get('time', ''),
                    'confidence': min(95, (candle_range / avg_range) * 30)
                }
                self.current_orders.append(order)

        vvprint(f"    ✓ Found {len(self.current_orders)} potential institutional orders from REAL data")

        # Update display
        self.refresh_display()

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
        """)

    def set_symbol(self, symbol: str):
        """Set the current symbol to monitor"""
        if symbol != self.current_symbol:
            self.current_symbol = symbol
            # Immediate refresh with new symbol
            self.refresh_display()

    def refresh_display(self):
        """Refresh the display with current data"""
        if not self.current_symbol:
            return

        # Get recent orders
        recent_orders = order_flow_detector.get_recent_orders(
            self.current_symbol, hours=24
        )

        # Store for AI analysis
        self.current_orders = recent_orders

        # Update summary counts
        buy_count = sum(1 for o in recent_orders if o.direction == 'BUY')
        sell_count = sum(1 for o in recent_orders if o.direction == 'SELL')
        total_count = len(recent_orders)

        self.buy_count_label.setText(str(buy_count))
        self.sell_count_label.setText(str(sell_count))
        self.total_count_label.setText(str(total_count))

        # Update orders list
        self.orders_list.clear()

        for order in recent_orders[:20]:  # Show top 20
            # Create custom widget
            item_widget = OrderFlowListItem(order)

            # Create list item
            list_item = QListWidgetItem(self.orders_list)
            list_item.setSizeHint(item_widget.sizeHint())

            # Add widget
            self.orders_list.addItem(list_item)
            self.orders_list.setItemWidget(list_item, item_widget)

        # Update clusters
        clusters = order_flow_detector.get_order_clusters(
            self.current_symbol, price_tolerance_pips=10
        )

        if clusters:
            cluster_lines = []
            for i, cluster in enumerate(clusters[:5], 1):
                direction_emoji = {'BUY': '🟢', 'SELL': '🔴', 'NEUTRAL': '🟡'}[cluster['direction']]
                cluster_lines.append(
                    f"{i}. {cluster['price']:.5f} {direction_emoji} "
                    f"({cluster['order_count']} orders, "
                    f"{cluster['total_volume_multiplier']:.1f}× volume)"
                )

            self.clusters_text.setPlainText('\n'.join(cluster_lines))
        else:
            self.clusters_text.setPlainText("No order clusters detected")

        # Update status
        stats = order_flow_detector.get_summary_stats()
        if stats.get('last_scan'):
            time_str = stats['last_scan'].strftime("%H:%M:%S")
            self.status_label.setText(
                f"Last scan: {time_str} | "
                f"{stats['total_orders']} total orders in history"
            )
        else:
            self.status_label.setText(
                f"{stats.get('total_orders', 0)} total orders in history"
            )

        # Update AI if enabled
        if self.ai_enabled and self.current_orders:
            self.update_ai_suggestions()

    def on_scan_requested(self):
        """Handle scan request"""
        self.status_label.setText("Scanning...")
        # Actual scanning done by parent/controller

    def scan_and_update(self, symbol: str, df: pd.DataFrame, lookback: int = 50):
        """
        Convenience method to scan and update in one call

        Args:
            symbol: Symbol to scan
            df: DataFrame with OHLC and volume data
            lookback: Number of candles to analyze
        """
        self.current_symbol = symbol

        # Mark that we're using real data now
        if not self.using_real_data:
            self.using_real_data = True
            # Clear demo data from detector
            order_flow_detector.order_history.clear()
            vprint("[Order Flow] Switched from demo data to REAL MT5 data")

        # Run scan on real data
        detected_orders = order_flow_detector.scan_for_orders(
            symbol, df, lookback
        )

        vvprint(f"[Order Flow] Detected {len(detected_orders)} institutional orders in real data")

        # Emit signals for new orders
        for order in detected_orders:
            self.order_detected.emit(order.to_dict())

        # Update display
        self.refresh_display()

    def clear_display(self):
        """Clear all displays"""
        self.buy_count_label.setText("0")
        self.sell_count_label.setText("0")
        self.total_count_label.setText("0")
        self.orders_list.clear()
        self.clusters_text.setPlainText("No data")
        self.status_label.setText("Status: Waiting for data")

    def get_chart_overlays(self, hours: int = 4) -> List[Dict]:
        """Get overlays for chart"""
        if not self.current_symbol:
            return []

        return order_flow_detector.get_chart_overlays(self.current_symbol, hours)

    def load_sample_data(self):
        """Load sample institutional order flow data"""
        from datetime import datetime, timedelta

        # Create sample orders using correct constructor signature
        # InstitutionalOrder(symbol, timestamp, price, direction, volume_multiplier, pip_move, order_type, confidence)
        sample_orders = [
            InstitutionalOrder(
                symbol='GBPUSD',
                timestamp=datetime.now() - timedelta(minutes=5),
                price=1.31850,
                direction='BUY',
                volume_multiplier=2.5,
                pip_move=28.0,
                order_type='absorption',
                confidence=92
            ),
            InstitutionalOrder(
                symbol='GBPUSD',
                timestamp=datetime.now() - timedelta(minutes=8),
                price=1.31855,  # Close to first order - will form cluster
                direction='BUY',
                volume_multiplier=3.2,
                pip_move=32.0,
                order_type='accumulation',
                confidence=90
            ),
            InstitutionalOrder(
                symbol='GBPUSD',
                timestamp=datetime.now() - timedelta(minutes=12),
                price=1.32120,
                direction='SELL',
                volume_multiplier=1.8,
                pip_move=22.0,
                order_type='sweep',
                confidence=88
            ),
            InstitutionalOrder(
                symbol='GBPUSD',
                timestamp=datetime.now() - timedelta(minutes=15),
                price=1.32118,  # Close to previous SELL - will form cluster
                direction='SELL',
                volume_multiplier=2.1,
                pip_move=24.0,
                order_type='absorption',
                confidence=87
            ),
            InstitutionalOrder(
                symbol='GBPUSD',
                timestamp=datetime.now() - timedelta(minutes=18),
                price=1.31750,
                direction='BUY',
                volume_multiplier=3.5,
                pip_move=35.0,
                order_type='accumulation',
                confidence=95
            ),
            InstitutionalOrder(
                symbol='EURUSD',
                timestamp=datetime.now() - timedelta(minutes=25),
                price=1.16125,
                direction='SELL',
                volume_multiplier=2.2,
                pip_move=25.0,
                order_type='absorption',
                confidence=85
            ),
            InstitutionalOrder(
                symbol='EURUSD',
                timestamp=datetime.now() - timedelta(minutes=28),
                price=1.16122,  # Close to previous EURUSD - will form cluster
                direction='SELL',
                volume_multiplier=2.8,
                pip_move=30.0,
                order_type='sweep',
                confidence=89
            )
        ]

        # Add sample orders to the detector's order history
        order_flow_detector.order_history.extend(sample_orders)
        self.current_symbol = 'GBPUSD'

        # Refresh display
        self.refresh_display()

    def update_data(self):
        """Update widget with data based on current mode (demo/live)"""
        if is_demo_mode():
            # Load sample order flow data
            self.load_sample_data()
        else:
            # Get live data
            self.update_from_live_data()

        # Update AI if enabled
        if self.ai_enabled and self.current_orders:
            self.update_ai_suggestions()

    def on_mode_changed(self, is_demo: bool):
        """Handle demo/live mode changes"""
        mode_text = "DEMO" if is_demo else "LIVE"
        vprint(f"Order Flow widget switching to {mode_text} mode")
        self.update_data()

    def analyze_with_ai(self, prediction, widget_data):
        """
        Advanced AI analysis for institutional order flow

        Analyzes:
        - Order clustering and concentration
        - Directional bias (smart money direction)
        - Order type significance
        - Volume magnitude assessment
        - Liquidity sweep patterns
        """
        from core.ml_integration import create_ai_suggestion
        from datetime import datetime, timedelta

        if not self.current_orders:
            return create_ai_suggestion(
                widget_type="order_flow",
                text="No institutional orders detected yet",
                confidence=0.0
            )

        # Analyze recent orders (last hour)
        now = datetime.now()
        recent_orders = [o for o in self.current_orders
                        if now - o.timestamp <= timedelta(hours=1)]

        if not recent_orders:
            return create_ai_suggestion(
                widget_type="order_flow",
                text="No recent institutional activity - Market quiet",
                confidence=0.75,
                emoji="💤",
                color="gray"
            )

        # Analyze directional bias
        buy_orders = [o for o in recent_orders if o.direction == 'BUY']
        sell_orders = [o for o in recent_orders if o.direction == 'SELL']

        # Calculate total institutional volume
        total_buy_volume = sum(o.estimated_size_usd for o in buy_orders)
        total_sell_volume = sum(o.estimated_size_usd for o in sell_orders)

        # Analyze order types
        sweeps = [o for o in recent_orders if o.order_type == 'sweep']
        absorptions = [o for o in recent_orders if o.order_type == 'absorption']
        accumulations = [o for o in recent_orders if o.order_type == 'accumulation']

        # Get average confidence
        avg_confidence = sum(o.confidence for o in recent_orders) / len(recent_orders)

        # CRITICAL: Strong directional bias with high-value sweeps
        if sweeps and len(sweeps) >= 2:
            sweep_direction = 'BUY' if len([s for s in sweeps if s.direction == 'BUY']) > len([s for s in sweeps if s.direction == 'SELL']) else 'SELL'
            sweep_volume = sum(o.estimated_size_usd for o in sweeps)

            if sweep_volume > 50_000_000:  # >$50M in sweeps
                emoji = "🔥" if sweep_direction == 'BUY' else "❄️"
                color = "green" if sweep_direction == 'BUY' else "red"
                return create_ai_suggestion(
                    widget_type="order_flow",
                    text=f"{emoji} STRONG {sweep_direction} SIGNAL: {len(sweeps)} liquidity sweeps detected (${sweep_volume/1e6:.0f}M). Smart money is aggressively {sweep_direction}ING! High probability move incoming!",
                    confidence=0.93,
                    emoji=emoji,
                    color=color
                )

        # STRONG: Clear directional imbalance
        if total_buy_volume > total_sell_volume * 2:
            return create_ai_suggestion(
                widget_type="order_flow",
                text=f"📈 STRONG BUY FLOW: ${total_buy_volume/1e6:.0f}M BUY vs ${total_sell_volume/1e6:.0f}M SELL ({len(buy_orders)} vs {len(sell_orders)} orders). Institutions accumulating! Avg confidence: {avg_confidence:.0f}%",
                confidence=0.88,
                emoji="📈",
                color="green"
            )
        elif total_sell_volume > total_buy_volume * 2:
            return create_ai_suggestion(
                widget_type="order_flow",
                text=f"📉 STRONG SELL FLOW: ${total_sell_volume/1e6:.0f}M SELL vs ${total_buy_volume/1e6:.0f}M BUY ({len(sell_orders)} vs {len(buy_orders)} orders). Institutions distributing! Avg confidence: {avg_confidence:.0f}%",
                confidence=0.88,
                emoji="📉",
                color="red"
            )

        # MODERATE: Absorption detected (potential reversal)
        if len(absorptions) >= 2:
            absorption_direction = 'BUY' if len([a for a in absorptions if a.direction == 'BUY']) > len([a for a in absorptions if a.direction == 'SELL']) else 'SELL'
            return create_ai_suggestion(
                widget_type="order_flow",
                text=f"⚠️ ABSORPTION DETECTED: {len(absorptions)} {absorption_direction} absorptions - Institutions stopping {('sellers' if absorption_direction == 'BUY' else 'buyers')}. Possible reversal zone!",
                confidence=0.82,
                emoji="⚠️",
                color="yellow"
            )

        # GOOD: Accumulation pattern
        if len(accumulations) >= 2:
            accum_direction = 'BUY' if len([a for a in accumulations if a.direction == 'BUY']) > len([a for a in accumulations if a.direction == 'SELL']) else 'SELL'
            accum_volume = sum(o.estimated_size_usd for o in accumulations)
            return create_ai_suggestion(
                widget_type="order_flow",
                text=f"📊 ACCUMULATION: {len(accumulations)} {accum_direction} accumulation orders (${accum_volume/1e6:.0f}M). Smart money building {accum_direction} position slowly.",
                confidence=0.78,
                emoji="📊",
                color="green" if accum_direction == 'BUY' else "red"
            )

        # BALANCED: Mixed signals
        if abs(len(buy_orders) - len(sell_orders)) <= 1:
            return create_ai_suggestion(
                widget_type="order_flow",
                text=f"⚖️ BALANCED FLOW: {len(buy_orders)} BUY vs {len(sell_orders)} SELL (${total_buy_volume/1e6:.0f}M vs ${total_sell_volume/1e6:.0f}M). No clear institutional bias. Wait for direction.",
                confidence=0.70,
                emoji="⚖️",
                color="yellow"
            )

        # WEAK: Some activity but unclear
        return create_ai_suggestion(
            widget_type="order_flow",
            text=f"📋 {len(recent_orders)} institutional orders detected. Total: ${(total_buy_volume + total_sell_volume)/1e6:.0f}M. Avg confidence: {avg_confidence:.0f}%. Monitor for clearer pattern.",
            confidence=0.68,
            emoji="📋",
            color="blue"
        )
