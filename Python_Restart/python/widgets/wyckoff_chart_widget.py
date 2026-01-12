"""
Wyckoff Chart Widget
Displays candlestick charts with Wyckoff LPS/LPSY overlays
"""

import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTextEdit, QSplitter)
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
        layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins for more chart space
        layout.setSpacing(5)
        
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

        # === SPLITTER: CHART + EDUCATIONAL TEXT ===
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === MATPLOTLIB CHART ===
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(18, 8), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(400)
        chart_layout.addWidget(self.canvas)

        splitter.addWidget(chart_widget)

        # === EDUCATIONAL TEXT PANEL ===
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMinimumHeight(200)
        self.analysis_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ddd;
                border: 2px solid #444;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        splitter.addWidget(self.analysis_text)

        # Set initial sizes (60% chart, 40% text)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter, stretch=1)

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

        # Generate real-time educational analysis with actual numbers
        if tf_wyckoff:
            self._update_educational_analysis(symbol, rates, tf_wyckoff)
        
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
        vprint(f"[Wyckoff Chart] _overlay_wyckoff called with data: {wyckoff_data.keys() if wyckoff_data else 'None'}")

        # Get LPS/LPSY if detected
        lps_lpsy = wyckoff_data.get('lps_lpsy')
        vprint(f"[Wyckoff Chart] LPS/LPSY data: {lps_lpsy}")

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
                
        # Plot Wyckoff events with educational annotations
        events = wyckoff_data.get('events', [])
        event_explanations = self._get_event_explanations()

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

                # Add event label with educational tooltip
                event_label = f' {event_type}'
                if event_type in event_explanations:
                    event_label += f'\n{event_explanations[event_type]}'

                ax.text(event_time, event_price, event_label,
                       fontsize=8, color=event_color, fontweight='bold',
                       verticalalignment='bottom', linespacing=1.2,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e1e1e',
                                alpha=0.7, edgecolor=event_color, linewidth=1))
                       
        # Add clean phase label at top-left (minimal, no explanations)
        phase = wyckoff_data.get('current_phase')
        vprint(f"[Wyckoff Chart] Phase data: {phase}")

        if phase:
            phase_text = f"Phase: {phase.value}"
            vprint(f"[Wyckoff Chart] Adding phase label: {phase_text}")
            phase_colors = {
                'ACCUMULATION': '#00ff00',
                'MARKUP': '#4CAF50',
                'DISTRIBUTION': '#ff0000',
                'MARKDOWN': '#F44336',
                'UNKNOWN': '#888888'
            }
            phase_color = phase_colors.get(phase.value, '#888888')

            # Simple phase label only - all explanations in text panel below
            ax.text(0.02, 0.98, phase_text, transform=ax.transAxes,
                   fontsize=12, fontweight='bold', color=phase_color,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='#2a2a2a', alpha=0.9, pad=0.6))

        # Add LPS/LPSY label if present (minimal - details in text panel below)
        if lps_lpsy:
            lps_type = lps_lpsy['type']
            strength = lps_lpsy.get('strength', 'MODERATE')
            confirmed = lps_lpsy.get('confirmed', False)

            lps_color = '#00FF00' if lps_type == 'LPS' else '#FF0000'
            status = "✅" if confirmed else "⏳"

            # Simple label at top-right - full analysis in text panel below
            signal_label = f"{lps_type} {strength} {status}"
            ax.text(0.98, 0.98, signal_label, transform=ax.transAxes,
                   fontsize=11, fontweight='bold', color=lps_color,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='#2a2a2a', alpha=0.9, pad=0.6))

        # Add legend for entry/stop lines - positioned to avoid overlap
        ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.90),
                 facecolor='#2a2a2a', edgecolor='#666',
                 labelcolor='#fff', fontsize=9, framealpha=0.9)
                 
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

    def _update_educational_analysis(self, symbol: str, rates, wyckoff_data: dict):
        """
        Generate educational analysis with REAL numbers from current market data
        """
        # Calculate real market statistics
        current_price = rates[-1]['close']
        high_price = np.max(rates[-20:]['high'])
        low_price = np.min(rates[-20:]['low'])
        price_range = high_price - low_price

        # Volume statistics
        volumes = rates['tick_volume']
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        high_volume_bars = np.sum(volumes[-20:] > avg_volume * 1.5)

        # Recent price action (last 5 bars)
        recent_bars = rates[-5:]
        recent_spread = np.mean([r['high'] - r['low'] for r in recent_bars])

        # Get phase
        phase = wyckoff_data.get('current_phase')
        phase_name = phase.value if phase else 'UNKNOWN'

        # Get LPS/LPSY if present
        lps_lpsy = wyckoff_data.get('lps_lpsy')

        # Get volume analysis
        volume_analysis = wyckoff_data.get('volume_analysis', {})
        effort_result = volume_analysis.get('effort_result', 'N/A')

        # Build HTML with REAL DATA
        html = f"""
        <div style='font-family: Arial, sans-serif;'>
            <h2 style='color: #FFD700; margin-bottom: 15px; border-bottom: 2px solid #FFD700; padding-bottom: 10px;'>
                📊 REAL-TIME WYCKOFF ANALYSIS: {symbol} {self.current_timeframe}
            </h2>

            <div style='background-color: rgba(0, 191, 255, 0.1); padding: 15px; border-left: 4px solid #00BFFF; margin-bottom: 20px;'>
                <h3 style='color: #00BFFF; margin-top: 0;'>🎯 CURRENT MARKET STATE</h3>
                <p><strong>Price:</strong> {current_price:.5f}</p>
                <p><strong>20-Bar Range:</strong> {low_price:.5f} to {high_price:.5f} ({price_range:.5f} points)</p>
                <p><strong>Current Volume:</strong> {current_volume:,.0f} (Avg: {avg_volume:,.0f})</p>
                <p><strong>High Volume Bars (last 20):</strong> {high_volume_bars} bars above 1.5x average</p>
                <p><strong>Recent Bar Spread (avg last 5):</strong> {recent_spread:.5f} points</p>
                <p><strong>Wyckoff Phase:</strong> <span style='color: {"#00FF00" if phase_name == "ACCUMULATION" else "#FF0000" if phase_name == "DISTRIBUTION" else "#FFD700"}; font-weight: bold;'>{phase_name}</span></p>
            </div>
        """

        # Phase-specific analysis with REAL context
        if phase_name == 'ACCUMULATION':
            html += f"""
            <div style='background-color: rgba(0, 255, 0, 0.05); padding: 15px; border-left: 4px solid #00FF00; margin-bottom: 20px;'>
                <h3 style='color: #00FF00; margin-top: 0;'>🎭 ACCUMULATION IN PROGRESS</h3>
                <p><strong>What's Happening RIGHT NOW:</strong></p>
                <p>Price is ranging between {low_price:.5f} and {high_price:.5f}. Institutions are absorbing supply at these levels.
                The {high_volume_bars} high-volume bars we've seen indicate heavy absorption activity - institutions are buying what retail is selling.</p>

                <p><strong>Volume Evidence:</strong></p>
                <p>Current volume ({current_volume:,.0f}) vs Average ({avg_volume:,.0f}):
                {"Volume is ELEVATED - institutions actively accumulating" if current_volume > avg_volume * 1.2 else "Volume normal - quiet accumulation phase"}</p>

                <p><strong>What To Watch:</strong></p>
                <p>• If price holds above {low_price:.5f} on declining volume = sellers exhausting (bullish)</p>
                <p>• Look for Spring below {low_price:.5f} that quickly reverses = trap for sellers</p>
                <p>• LPS will likely form near {low_price + (price_range * 0.3):.5f} (30% of range)</p>

                <p><strong>Trade Plan:</strong></p>
                <p>• Entry Zone: {low_price:.5f} - {low_price + (price_range * 0.2):.5f}</p>
                <p>• Stop: Below {low_price - (recent_spread * 1.5):.5f}</p>
                <p>• Target: {high_price:.5f} (top of range), then {high_price + price_range:.5f} (markup)</p>
            </div>
            """

        elif phase_name == 'DISTRIBUTION':
            html += f"""
            <div style='background-color: rgba(255, 0, 0, 0.05); padding: 15px; border-left: 4px solid #FF0000; margin-bottom: 20px;'>
                <h3 style='color: #FF0000; margin-top: 0;'>⚠️ DISTRIBUTION IN PROGRESS</h3>
                <p><strong>What's Happening RIGHT NOW:</strong></p>
                <p>Price is capped between {low_price:.5f} and {high_price:.5f}. Institutions are offloading positions at these levels.
                The {high_volume_bars} high-volume bars indicate heavy distribution - institutions are selling into retail buying.</p>

                <p><strong>Volume Evidence:</strong></p>
                <p>Current volume ({current_volume:,.0f}) vs Average ({avg_volume:,.0f}):
                {"Volume ELEVATED at resistance - institutional selling" if current_volume > avg_volume * 1.2 else "Volume declining - buyers exhausting"}</p>

                <p><strong>WARNING SIGNS:</strong></p>
                <p>• Price failing at {high_price:.5f} repeatedly = supply ceiling</p>
                <p>• Watch for Upthrust above {high_price:.5f} that reverses = trap for buyers</p>
                <p>• LPSY will likely form near {high_price - (price_range * 0.3):.5f} (30% below top)</p>

                <p><strong>Trade Plan:</strong></p>
                <p>• EXIT ALL LONGS IMMEDIATELY</p>
                <p>• Short Entry Zone: {high_price - (price_range * 0.2):.5f} - {high_price:.5f}</p>
                <p>• Stop: Above {high_price + (recent_spread * 1.5):.5f}</p>
                <p>• Target: {low_price:.5f} (bottom of range), then {low_price - price_range:.5f} (markdown)</p>
            </div>
            """

        elif phase_name == 'MARKUP':
            html += f"""
            <div style='background-color: rgba(76, 175, 80, 0.1); padding: 15px; border-left: 4px solid #4CAF50; margin-bottom: 20px;'>
                <h3 style='color: #4CAF50; margin-top: 0;'>📈 MARKUP PHASE ACTIVE</h3>
                <p><strong>Trend Strength:</strong></p>
                <p>Price advanced from {low_price:.5f} to {high_price:.5f} (+{price_range:.5f} points). Uptrend is {"STRONG" if price_range > recent_spread * 20 else "MODERATE"}.</p>

                <p><strong>Volume Confirmation:</strong></p>
                <p>{"Volume increasing on rallies - healthy trend" if high_volume_bars > 5 else "Volume declining - watch for distribution starting"}</p>

                <p><strong>Support Levels:</strong></p>
                <p>• Key support: {high_price - (price_range * 0.382):.5f} (38.2% retracement)</p>
                <p>• Major support: {high_price - (price_range * 0.618):.5f} (61.8% retracement)</p>

                <p><strong>Strategy:</strong></p>
                <p>• Trail stops below recent swing lows</p>
                <p>• Take partial profits at resistance levels</p>
                <p>• Watch for distribution signs near {high_price:.5f}</p>
            </div>
            """

        elif phase_name == 'MARKDOWN':
            html += f"""
            <div style='background-color: rgba(244, 67, 54, 0.1); padding: 15px; border-left: 4px solid #F44336; margin-bottom: 20px;'>
                <h3 style='color: #F44336; margin-top: 0;'>📉 MARKDOWN PHASE ACTIVE</h3>
                <p><strong>Trend Strength:</strong></p>
                <p>Price declined from {high_price:.5f} to {low_price:.5f} (-{price_range:.5f} points). Downtrend is {"STRONG" if price_range > recent_spread * 20 else "MODERATE"}.</p>

                <p><strong>Volume Confirmation:</strong></p>
                <p>{"Volume increasing on declines - healthy downtrend" if high_volume_bars > 5 else "Volume declining - watch for accumulation starting"}</p>

                <p><strong>Resistance Levels:</strong></p>
                <p>• Key resistance: {low_price + (price_range * 0.382):.5f} (38.2% retracement)</p>
                <p>• Major resistance: {low_price + (price_range * 0.618):.5f} (61.8% retracement)</p>

                <p><strong>Strategy:</strong></p>
                <p>• Trail stops on shorts above recent swing highs</p>
                <p>• Take profits at support levels</p>
                <p>• Watch for accumulation signs near {low_price:.5f}</p>
            </div>
            """

        # LPS/LPSY Analysis with REAL PRICES
        if lps_lpsy:
            lps_type = lps_lpsy['type']
            lps_price = lps_lpsy['price']
            entry_trigger = lps_lpsy['entry_trigger']
            stop_loss = lps_lpsy['stop_loss']
            confirmed = lps_lpsy.get('confirmed', False)
            strength = lps_lpsy.get('strength', 'MODERATE')

            risk = abs(entry_trigger - stop_loss)
            reward = abs(entry_trigger - (high_price if lps_type == 'LPS' else low_price))
            rr_ratio = reward / risk if risk > 0 else 0

            html += f"""
            <div style='background-color: rgba(135, 206, 250, 0.1); padding: 15px; border: 2px solid #87CEEB; border-radius: 8px; margin-bottom: 20px;'>
                <h3 style='color: #87CEEB; margin-top: 0;'>🎯 {lps_type} SIGNAL DETECTED</h3>

                <p><strong>Signal Quality:</strong> <span style='color: {"#00FF00" if strength == "STRONG" else "#FFD700" if strength == "MODERATE" else "#FF6B6B"};'>{strength}</span>
                {"✅ CONFIRMED" if confirmed else "⏳ PENDING"}</p>

                <p><strong>Price Levels:</strong></p>
                <p>• {lps_type} formed at: {lps_price:.5f}</p>
                <p>• Entry trigger: {entry_trigger:.5f}</p>
                <p>• Stop loss: {stop_loss:.5f}</p>
                <p>• Initial target: {(high_price if lps_type == 'LPS' else low_price):.5f}</p>

                <p><strong>Risk/Reward:</strong></p>
                <p>• Risk: {risk:.5f} points</p>
                <p>• Potential Reward: {reward:.5f} points</p>
                <p>• R:R Ratio: 1:{rr_ratio:.1f} {"✅ Excellent" if rr_ratio > 2 else "⚠️ Moderate" if rr_ratio > 1 else "❌ Poor"}</p>

                <p><strong>Action Plan:</strong></p>
                <p>{"✅ This is a HIGH PROBABILITY setup. Consider entering with full position size." if strength == "STRONG" and confirmed else
                   "⏳ Wait for confirmation or use reduced position size (50%)." if not confirmed else
                   "⚠️ Weak signal - consider passing or using minimal size (25%)."}</p>
            </div>
            """

        # Volume Analysis with REAL NUMBERS
        if volume_analysis:
            html += f"""
            <div style='background-color: rgba(138, 43, 226, 0.1); padding: 15px; border-left: 4px solid #8A2BE2; margin-bottom: 20px;'>
                <h3 style='color: #8A2BE2; margin-top: 0;'>📊 VOLUME ANALYSIS (Real Data)</h3>

                <p><strong>Current Pattern:</strong> {effort_result}</p>

                <p><strong>What The Numbers Tell Us:</strong></p>
                <p>Average volume (20 bars): {avg_volume:,.0f}</p>
                <p>Current bar volume: {current_volume:,.0f} ({((current_volume/avg_volume - 1) * 100):.1f}% {"above" if current_volume > avg_volume else "below"} average)</p>
                <p>High volume bars: {high_volume_bars}/20 ({"Elevated activity" if high_volume_bars > 5 else "Normal activity"})</p>

                <p><strong>Recent spread (last 5 bars):</strong> {recent_spread:.5f} points average</p>
                <p>{"WIDE spreads indicate momentum" if recent_spread > price_range * 0.05 else "NARROW spreads indicate ranging/absorption"}</p>

                <p><strong>Interpretation:</strong></p>
                {"<p style='color: #00FF00;'>High volume + narrow spreads = ABSORPTION active. One side aggressively defending this level.</p>" if "high volume" in effort_result.lower() and "narrow" in effort_result.lower() else
                 "<p style='color: #FFD700;'>High volume + wide spreads = MOMENTUM. Strong directional move in progress.</p>" if "high volume" in effort_result.lower() and "wide" in effort_result.lower() else
                 "<p style='color: #87CEEB;'>Low volume + wide spreads = NO RESISTANCE. Price moving easily in current direction.</p>" if "low volume" in effort_result.lower() and "wide" in effort_result.lower() else
                 "<p style='color: #888;'>Low volume + narrow spreads = APATHY. No institutional interest currently.</p>"}
            </div>
            """

        html += """
        </div>
        """

        self.analysis_text.setHtml(html)

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

    def _get_event_explanations(self) -> dict:
        """
        Get educational explanations for Wyckoff events
        Returns brief tooltips for each event type
        """
        return {
            'SC': '(Selling Climax)\nPanic selling exhausts',
            'BC': '(Buying Climax)\nPanic buying exhausts',
            'AR': '(Automatic Rally)\nStrong bounce up',
            'AR_DIST': '(Auto Reaction)\nInitial decline',
            'SPRING': '(Spring)\nFalse breakdown trap',
            'UPTHRUST': '(Upthrust)\nFalse breakout trap',
            'ST': '(Secondary Test)\nRetesting lows',
            'ST_DIST': '(Secondary Test)\nRetesting highs'
        }

    def _get_phase_guidance(self, phase: str) -> dict:
        """
        Get educational guidance for Wyckoff phase
        Returns short description and actionable guidance
        """
        phase_guides = {
            'ACCUMULATION': {
                'short_description': 'Smart money is buying',
                'action': 'Look for LPS (green arrows) to enter LONG. Avoid selling.'
            },
            'MARKUP': {
                'short_description': 'Uptrend in progress',
                'action': 'Trail stops on longs. Enter on pullbacks to support.'
            },
            'DISTRIBUTION': {
                'short_description': 'Smart money is selling',
                'action': 'Look for LPSY (red arrows) to enter SHORT. Exit all longs.'
            },
            'MARKDOWN': {
                'short_description': 'Downtrend in progress',
                'action': 'Trail stops on shorts. Enter on rallies to resistance.'
            },
            'UNKNOWN': {
                'short_description': 'Market structure unclear',
                'action': 'Wait for clarity. Reduce position sizes or stay flat.'
            }
        }
        return phase_guides.get(phase, phase_guides['UNKNOWN'])

    def _get_signal_guidance(self, signal_type: str, strength: str, confirmed: bool) -> str:
        """
        Get educational guidance for LPS/LPSY signal
        Returns concise actionable guidance
        """
        if signal_type == 'LPS':
            if strength == 'STRONG' and confirmed:
                return "✅ HIGH PROBABILITY long entry\nEnter near green line\nStop below LPS marker"
            elif strength == 'STRONG':
                return "⏳ STRONG signal, not confirmed\nWait for follow-through\nThen enter long"
            elif strength == 'MODERATE' and confirmed:
                return "✅ GOOD long opportunity\nEnter with reduced size\nStop below LPS marker"
            elif strength == 'MODERATE':
                return "⏳ MODERATE signal pending\nWait for confirmation\nOr use small position"
            else:  # WEAK
                return "⚠️ WEAK signal - Low confidence\nWait for better setup\nOr skip this one"
        else:  # LPSY
            if strength == 'STRONG' and confirmed:
                return "✅ HIGH PROBABILITY short entry\nEnter near red line\nStop above LPSY marker"
            elif strength == 'STRONG':
                return "⏳ STRONG signal, not confirmed\nWait for follow-through\nThen enter short"
            elif strength == 'MODERATE' and confirmed:
                return "✅ GOOD short opportunity\nEnter with reduced size\nStop above LPSY marker"
            elif strength == 'MODERATE':
                return "⏳ MODERATE signal pending\nWait for confirmation\nOr use small position"
            else:  # WEAK
                return "⚠️ WEAK signal - Low confidence\nWait for better setup\nOr skip this one"
