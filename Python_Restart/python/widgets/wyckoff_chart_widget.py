"""
Wyckoff Chart Widget
Displays candlestick charts with Wyckoff LPS/LPSY overlays
"""

import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from core.verbose_mode_manager import vprint

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class WyckoffChartWidget(QWidget):
    """
    Widget for displaying Wyckoff analysis on candlestick charts
    """
    
    def __init__(self):
        super().__init__()
        self.current_symbol = "EURUSD"
        self.current_timeframe = "H4"
        self.wyckoff_data = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # === TITLE & CONTROLS ===
        controls_layout = QHBoxLayout()
        
        title_label = QLabel("📊 WYCKOFF CHART ANALYSIS")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        controls_layout.addWidget(title_label)
        
        controls_layout.addStretch()
        
        # Timeframe selector
        tf_label = QLabel("Timeframe:")
        controls_layout.addWidget(tf_label)
        
        self.tf_combo = QComboBox()
        self.tf_combo.addItems(["M15", "H1", "H4", "D1"])
        self.tf_combo.setCurrentText("H4")
        self.tf_combo.currentTextChanged.connect(self.on_timeframe_changed)
        controls_layout.addWidget(self.tf_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh Chart")
        self.refresh_btn.clicked.connect(self.refresh_chart)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)

        # === MATPLOTLIB CHART ===
        # Larger figure size to match main chart height for easy comparison
        self.figure = Figure(figsize=(14, 12), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(600)  # Ensure minimum height for visibility
        layout.addWidget(self.canvas)
        
        # Initial empty chart
        self.show_empty_chart()
        
    def show_empty_chart(self):
        """Show empty chart with instructions"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')

        # Main instruction
        ax.text(0.5, 0.6, '📊 Wyckoff Chart Analysis',
                ha='center', va='center', fontsize=18, color='#64B5F6', weight='bold',
                transform=ax.transAxes)

        # Step-by-step instructions
        instructions = [
            '1. Go to the "🎯 Trade Check" tab',
            '2. Check "🔵 Enable Wyckoff LPS/LPSY Analysis"',
            '3. Enter a trade (e.g., "BUY EURUSD")',
            '4. Click "✓ Check Trade"',
            '',
            'The chart will automatically populate with:',
            '• Candlestick price data',
            '• LPS/LPSY markers (entry points)',
            '• Entry trigger lines',
            '• Stop loss lines',
            '• Wyckoff events (SC, Spring, BC, UT, etc.)',
            '• Phase annotations'
        ]

        y_pos = 0.45
        for instruction in instructions:
            color = '#aaa' if instruction else '#666'
            fontsize = 11 if instruction.startswith('•') else 12
            weight = 'bold' if instruction.startswith(('1.', '2.', '3.', '4.')) else 'normal'
            ax.text(0.5, y_pos, instruction,
                    ha='center', va='center', fontsize=fontsize, color=color,
                    weight=weight, transform=ax.transAxes)
            y_pos -= 0.035

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        self.canvas.draw()
        
    def on_timeframe_changed(self, timeframe):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        if self.wyckoff_data and self.current_symbol:
            self.plot_wyckoff_chart(self.current_symbol, self.wyckoff_data)
            
    def refresh_chart(self):
        """Refresh the chart"""
        if self.wyckoff_data and self.current_symbol:
            self.plot_wyckoff_chart(self.current_symbol, self.wyckoff_data)
            
    def update_chart(self, symbol, wyckoff_data, main_chart_timeframe=None):
        """
        Update chart with Wyckoff analysis data

        Args:
            symbol: Trading symbol
            wyckoff_data: Dict containing Wyckoff analysis for multiple timeframes
            main_chart_timeframe: Timeframe from main chart (e.g., "H4", "H1")
        """
        self.current_symbol = symbol
        self.wyckoff_data = wyckoff_data

        # Sync with main chart's timeframe if provided
        if main_chart_timeframe:
            # Map main chart timeframes to our timeframe format
            tf_map = {
                'M15': 'M15',
                'M30': 'M15',  # Fallback to M15 if M30
                'H1': 'H1',
                'H4': 'H4',
                'D1': 'D1',
                'W1': 'D1'  # Fallback to D1 if W1
            }
            mapped_tf = tf_map.get(main_chart_timeframe, 'H4')
            self.current_timeframe = mapped_tf
            self.tf_combo.setCurrentText(mapped_tf)
            vprint(f"[Wyckoff Chart] Synced to main chart timeframe: {main_chart_timeframe} -> {mapped_tf}")

        self.plot_wyckoff_chart(symbol, wyckoff_data)
        
    def plot_wyckoff_chart(self, symbol, wyckoff_data):
        """
        Plot candlestick chart with Wyckoff overlays
        
        Args:
            symbol: Trading symbol
            wyckoff_data: Dict with Wyckoff analysis (contains H4, H1, M15 data)
        """
        if not MT5_AVAILABLE:
            self.show_error("MT5 not available")
            return
            
        # Get data for selected timeframe
        tf_map = {
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        timeframe = tf_map.get(self.current_timeframe, mt5.TIMEFRAME_H4)
        
        # Get price data
        if not mt5.initialize():
            self.show_error("Failed to initialize MT5")
            return
            
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        mt5.shutdown()
        
        if rates is None or len(rates) == 0:
            self.show_error(f"No data for {symbol}")
            return
            
        # Get Wyckoff data for this timeframe
        tf_wyckoff = wyckoff_data.get(self.current_timeframe, {})
        
        # Clear figure and create subplots
        self.figure.clear()

        # Create 2 subplots: price chart and volume
        # Height ratio [4, 1] gives more space to price chart for better visibility
        gs = self.figure.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.08)
        ax_price = self.figure.add_subplot(gs[0])
        ax_volume = self.figure.add_subplot(gs[1], sharex=ax_price)
        
        # Convert timestamps to datetime
        times = [datetime.fromtimestamp(r['time']) for r in rates]
        
        # Plot candlesticks
        self._plot_candlesticks(ax_price, times, rates)
        
        # Plot volume
        self._plot_volume(ax_volume, times, rates)
        
        # Overlay Wyckoff analysis
        if tf_wyckoff:
            self._overlay_wyckoff(ax_price, times, rates, tf_wyckoff)
            
        # Style the chart
        self._style_chart(ax_price, ax_volume, symbol)
        
        self.canvas.draw()
        
    def _plot_candlesticks(self, ax, times, rates):
        """Plot candlestick chart"""
        # Prepare data
        opens = rates['open']
        highs = rates['high']
        lows = rates['low']
        closes = rates['close']
        
        # Calculate candle colors
        colors = ['#00ff00' if c >= o else '#ff0000' for c, o in zip(closes, opens)]
        
        # Plot candles
        width = 0.6
        for i, (t, o, h, l, c, color) in enumerate(zip(times, opens, highs, lows, closes, colors)):
            # Wick (high-low line)
            ax.plot([t, t], [l, h], color='#666', linewidth=1, zorder=1)
            
            # Body (open-close rectangle)
            height = abs(c - o)
            bottom = min(o, c)
            rect = Rectangle((mdates.date2num(t) - width/2, bottom), width, height,
                           facecolor=color, edgecolor=color, alpha=0.8, zorder=2)
            ax.add_patch(rect)
            
    def _plot_volume(self, ax, times, rates):
        """Plot volume bars"""
        volumes = rates['tick_volume']
        colors = ['#00ff00' if c >= o else '#ff0000' 
                 for c, o in zip(rates['close'], rates['open'])]
        
        ax.bar(times, volumes, color=colors, alpha=0.5, width=0.8)
        ax.set_ylabel('Volume', color='#888', fontsize=10)
        ax.tick_params(colors='#888')
        
    def _overlay_wyckoff(self, ax, times, rates, wyckoff_data):
        """
        Overlay Wyckoff analysis on chart
        
        Args:
            ax: Matplotlib axis
            times: List of datetime objects
            rates: MT5 rates data
            wyckoff_data: Wyckoff analysis for this timeframe
        """
        # Get LPS/LPSY if detected
        lps_lpsy = wyckoff_data.get('lps_lpsy')
        if lps_lpsy:
            lps_index = lps_lpsy['index']
            if lps_index < len(times):
                lps_time = times[lps_index]
                lps_price = lps_lpsy['price']
                lps_type = lps_lpsy['type']
                
                # Plot LPS/LPSY marker
                if lps_type == 'LPS':
                    marker_color = '#00ff00'
                    marker = '^'  # Up arrow
                    label = 'LPS'
                else:
                    marker_color = '#ff0000'
                    marker = 'v'  # Down arrow
                    label = 'LPSY'
                    
                ax.scatter(lps_time, lps_price, s=200, c=marker_color, 
                          marker=marker, zorder=10, edgecolors='white', linewidths=2)
                ax.text(lps_time, lps_price, f'  {label}', 
                       fontsize=12, color=marker_color, fontweight='bold',
                       verticalalignment='center')
                
                # Plot entry trigger line
                entry_price = lps_lpsy['entry_trigger']
                ax.axhline(y=entry_price, color=marker_color, linestyle='--', 
                          linewidth=2, alpha=0.7, label=f'{label} Entry: {entry_price:.5f}')
                
                # Plot stop loss line
                stop_price = lps_lpsy['stop_loss']
                ax.axhline(y=stop_price, color='#ff6b6b', linestyle='-', 
                          linewidth=2, alpha=0.7, label=f'Stop Loss: {stop_price:.5f}')
                
        # Plot Wyckoff events
        events = wyckoff_data.get('events', [])
        for event in events[-10:]:  # Last 10 events
            event_index = event['index']
            if event_index < len(times):
                event_time = times[event_index]
                event_price = event['price']
                event_type = event['event'].value
                
                # Event marker colors
                event_colors = {
                    'SC': '#ff0000',
                    'BC': '#ff0000',
                    'AR': '#00ff00',
                    'AR_DIST': '#ff6b6b',
                    'SPRING': '#00bfff',
                    'UPTHRUST': '#ff69b4',
                    'ST': '#ffa500',
                    'ST_DIST': '#ffa500'
                }
                
                event_color = event_colors.get(event_type, '#ffffff')
                
                # Plot event marker
                ax.scatter(event_time, event_price, s=100, c=event_color,
                          marker='o', zorder=9, edgecolors='white', linewidths=1,
                          alpha=0.8)
                ax.text(event_time, event_price, f' {event_type}',
                       fontsize=9, color=event_color, fontweight='bold',
                       verticalalignment='bottom')
                       
        # Add phase annotation
        phase = wyckoff_data.get('current_phase')
        if phase:
            phase_text = f"Phase: {phase.value}"
            phase_colors = {
                'ACCUMULATION': '#00ff00',
                'MARKUP': '#4CAF50',
                'DISTRIBUTION': '#ff0000',
                'MARKDOWN': '#F44336',
                'UNKNOWN': '#888888'
            }
            phase_color = phase_colors.get(phase.value, '#888888')
            
            ax.text(0.02, 0.98, phase_text, transform=ax.transAxes,
                   fontsize=14, fontweight='bold', color=phase_color,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='#2a2a2a', alpha=0.8))
                   
        # Add legend
        ax.legend(loc='upper right', facecolor='#2a2a2a', edgecolor='#666',
                 labelcolor='#fff', fontsize=10)
                 
    def _style_chart(self, ax_price, ax_volume, symbol):
        """Apply styling to charts"""
        # Price chart styling
        ax_price.set_facecolor('#1e1e1e')
        ax_price.grid(True, alpha=0.2, color='#444', linestyle='--')
        ax_price.set_ylabel('Price', color='#888', fontsize=12, fontweight='bold')
        ax_price.tick_params(colors='#888', labelsize=10)
        ax_price.set_title(f'{symbol} - {self.current_timeframe} with Wyckoff Analysis',
                          color='#fff', fontsize=16, fontweight='bold', pad=20)
        
        # Remove x-axis labels from price chart (shared with volume)
        ax_price.tick_params(labelbottom=False)
        
        # Volume chart styling
        ax_volume.set_facecolor('#1e1e1e')
        ax_volume.grid(True, alpha=0.2, color='#444', linestyle='--')
        ax_volume.tick_params(colors='#888', labelsize=10)
        ax_volume.set_xlabel('Date/Time', color='#888', fontsize=12, fontweight='bold')
        
        # Format x-axis dates
        ax_volume.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax_volume.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax_volume.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Set background color
        self.figure.patch.set_facecolor('#1e1e1e')
        
        # Adjust layout
        self.figure.tight_layout()
        
    def show_error(self, message):
        """Show error message on chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        ax.text(0.5, 0.5, f'Error: {message}',
                ha='center', va='center', fontsize=14, color='#ff0000',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
