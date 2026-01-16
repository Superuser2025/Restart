"""
Wyckoff Chart Overlay Tool

Displays Wyckoff LPS/LPSY analysis directly on MT5 charts
Shows:
- LPS/LPSY markers
- Entry trigger lines
- Stop loss lines
- Wyckoff phase annotations
- Volume analysis
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from analysis.wyckoff_analyzer import WyckoffAnalyzer, WyckoffPhase
import time


class WyckoffChartOverlay:
    """
    Overlay Wyckoff analysis on MT5 charts
    """
    
    def __init__(self):
        self.analyzer = WyckoffAnalyzer()
        self.symbols = []
        self.timeframes = {
            'H4': mt5.TIMEFRAME_H4,
            'H1': mt5.TIMEFRAME_H1,
            'M15': mt5.TIMEFRAME_M15
        }
        
    def initialize(self, symbols=None):
        """
        Initialize MT5 connection and set symbols to monitor
        
        Args:
            symbols: List of symbols to monitor (default: ['EURUSD', 'GBPUSD', 'USDJPY'])
        """
        if not mt5.initialize():
            print("MT5 initialization failed")
            return False
            
        if symbols is None:
            self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        else:
            self.symbols = symbols
            
        print(f"Wyckoff Chart Overlay initialized for: {', '.join(self.symbols)}")
        return True
        
    def analyze_and_display(self, symbol, timeframe_name='H4'):
        """
        Analyze symbol and display results
        
        Args:
            symbol: Trading symbol
            timeframe_name: Timeframe to analyze ('H4', 'H1', 'M15')
        """
        if timeframe_name not in self.timeframes:
            print(f"Invalid timeframe: {timeframe_name}")
            return None
            
        timeframe = self.timeframes[timeframe_name]
        
        # Run Wyckoff analysis
        result = self.analyzer.analyze_symbol(symbol, timeframe, bars=100)
        
        if result is None:
            print(f"Analysis failed for {symbol} {timeframe_name}")
            return None
            
        # Display results
        self._display_results(symbol, timeframe_name, result)
        
        # Generate chart data for potential MT5 integration
        chart_data = result.get('chart_data', {})
        
        return result
        
    def _display_results(self, symbol, timeframe, result):
        """Display analysis results in terminal"""
        
        print("\n" + "="*80)
        print(f"  WYCKOFF ANALYSIS: {symbol} ({timeframe})")
        print("="*80)
        
        # Phase
        phase = result['current_phase']
        phase_symbols = {
            'ACCUMULATION': '🟢',
            'MARKUP': '📈',
            'DISTRIBUTION': '🔴',
            'MARKDOWN': '📉',
            'UNKNOWN': '❓'
        }
        phase_symbol = phase_symbols.get(phase.value, '❓')
        print(f"\n{phase_symbol} Market Phase: {phase.value}")
        
        # LPS/LPSY
        lps_lpsy = result.get('lps_lpsy')
        if lps_lpsy:
            lps_type = lps_lpsy['type']
            icon = '🟢' if lps_type == 'LPS' else '🔴'
            strength = lps_lpsy['strength']
            confirmed = "CONFIRMED ✅" if lps_lpsy['confirmed'] else "PENDING ⏳"
            
            print(f"\n{icon} {lps_type} Detected ({strength}) - {confirmed}")
            print(f"   Price: {lps_lpsy['price']:.5f}")
            print(f"   Entry Trigger: {lps_lpsy['entry_trigger']:.5f}")
            print(f"   Stop Loss: {lps_lpsy['stop_loss']:.5f}")
            print(f"   {lps_lpsy['description']}")
        else:
            print("\n⚪ No LPS/LPSY detected")
            
        # Signals
        signals = result['signals']
        if signals['action'] != 'WAIT':
            action_icon = '🟢' if signals['action'] == 'BUY' else '🔴'
            print(f"\n{action_icon} Signal: {signals['action']} ({signals['confidence']})")
            print("   Reasons:")
            for reason in signals['reasons']:
                print(f"   • {reason}")
        else:
            print("\n⏸️ Signal: WAIT - No clear setup")
            
        # Volume Analysis
        volume = result['volume_analysis']
        if volume:
            print(f"\n📊 Volume Analysis:")
            print(f"   {volume.get('effort_result', 'N/A')}")
            print(f"   {volume.get('divergence', 'N/A')}")
            
        # Events
        events = result.get('events', [])
        if events:
            recent_events = events[-5:]  # Last 5 events
            print(f"\n📍 Recent Wyckoff Events:")
            for event in recent_events:
                event_type = event['event'].value
                print(f"   • {event_type} at {event['price']:.5f}")
                
        print("\n" + "="*80 + "\n")
        
    def monitor_continuous(self, refresh_seconds=300):
        """
        Continuously monitor symbols and update analysis
        
        Args:
            refresh_seconds: How often to refresh analysis (default: 300 = 5 minutes)
        """
        print(f"\nStarting continuous monitoring (refresh every {refresh_seconds}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'='*80}")
                print(f"  UPDATE: {timestamp}")
                print(f"{'='*80}")
                
                # Analyze each symbol on each timeframe
                for symbol in self.symbols:
                    for tf_name in ['H4', 'H1', 'M15']:
                        self.analyze_and_display(symbol, tf_name)
                        time.sleep(1)  # Small delay between analyses
                        
                print(f"\nNext update in {refresh_seconds} seconds...")
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            self.shutdown()
            
    def generate_chart_markers(self, symbol, timeframe_name='H4'):
        """
        Generate chart marker data that can be used by MT5 indicators
        
        Returns: Dict with marker data for plotting on charts
        """
        if timeframe_name not in self.timeframes:
            return None
            
        timeframe = self.timeframes[timeframe_name]
        result = self.analyzer.analyze_symbol(symbol, timeframe, bars=100)
        
        if result is None:
            return None
            
        markers = []
        
        # Add LPS/LPSY marker
        lps_lpsy = result.get('lps_lpsy')
        if lps_lpsy:
            markers.append({
                'type': 'lps_lpsy',
                'price': lps_lpsy['price'],
                'entry': lps_lpsy['entry_trigger'],
                'stop': lps_lpsy['stop_loss'],
                'label': lps_lpsy['type'],
                'color': 'green' if lps_lpsy['type'] == 'LPS' else 'red'
            })
            
        # Add event markers
        events = result.get('events', [])
        for event in events[-10:]:  # Last 10 events
            markers.append({
                'type': 'event',
                'price': event['price'],
                'label': event['event'].value,
                'description': event['description']
            })
            
        return {
            'symbol': symbol,
            'timeframe': timeframe_name,
            'phase': result['current_phase'].value,
            'markers': markers,
            'timestamp': datetime.now()
        }
        
    def shutdown(self):
        """Shutdown MT5 connection"""
        mt5.shutdown()
        print("MT5 connection closed")


def main():
    """
    Main entry point for chart overlay tool
    """
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    WYCKOFF CHART OVERLAY TOOL                              ║
║                    LPS/LPSY Analysis for MT5                               ║
╚════════════════════════════════════════════════════════════════════════════╝

This tool analyzes your symbols using Wyckoff methodology and displays:
• Market Phase (Accumulation, Markup, Distribution, Markdown)
• LPS (Last Point of Support) - Bullish entry points
• LPSY (Last Point of Supply) - Bearish entry points
• Volume Spread Analysis
• Entry triggers and stop loss levels

""")
    
    # Get symbols from user
    print("Enter symbols to monitor (comma-separated, e.g., EURUSD,GBPUSD,USDJPY)")
    print("Or press Enter for default (EURUSD, GBPUSD, USDJPY):")
    symbols_input = input().strip()
    
    if symbols_input:
        symbols = [s.strip().upper() for s in symbols_input.split(',')]
    else:
        symbols = None
        
    # Initialize overlay
    overlay = WyckoffChartOverlay()
    
    if not overlay.initialize(symbols):
        print("Failed to initialize. Exiting.")
        return
        
    # Menu
    while True:
        print("\n" + "="*80)
        print("MENU:")
        print("1. Analyze specific symbol once")
        print("2. Analyze all symbols (all timeframes)")
        print("3. Start continuous monitoring (updates every 5 min)")
        print("4. Generate chart markers for MT5 indicator")
        print("5. Exit")
        print("="*80)
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            symbol = input("Enter symbol: ").strip().upper()
            tf = input("Enter timeframe (H4/H1/M15): ").strip().upper()
            overlay.analyze_and_display(symbol, tf)
            
        elif choice == '2':
            for symbol in overlay.symbols:
                for tf in ['H4', 'H1', 'M15']:
                    overlay.analyze_and_display(symbol, tf)
                    time.sleep(0.5)
                    
        elif choice == '3':
            refresh = input("Refresh interval in seconds (default 300): ").strip()
            refresh = int(refresh) if refresh.isdigit() else 300
            overlay.monitor_continuous(refresh)
            
        elif choice == '4':
            symbol = input("Enter symbol: ").strip().upper()
            tf = input("Enter timeframe (H4/H1/M15): ").strip().upper()
            markers = overlay.generate_chart_markers(symbol, tf)
            if markers:
                print("\nChart Markers Generated:")
                print(f"Phase: {markers['phase']}")
                print(f"Markers: {len(markers['markers'])} items")
                print("\nMarker data can be used by MT5 indicators")
                print(f"Data: {markers}")
            else:
                print("Failed to generate markers")
                
        elif choice == '5':
            overlay.shutdown()
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please select 1-5.")


if __name__ == "__main__":
    main()
