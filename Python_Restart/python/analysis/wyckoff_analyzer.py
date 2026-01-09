"""
Wyckoff Method Analyzer
Implements Richard Wyckoff's accumulation/distribution analysis with LPS/LPSY detection
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class WyckoffPhase(Enum):
    """Wyckoff market cycle phases"""
    ACCUMULATION = "ACCUMULATION"
    MARKUP = "MARKUP"
    DISTRIBUTION = "DISTRIBUTION"
    MARKDOWN = "MARKDOWN"
    UNKNOWN = "UNKNOWN"


class WyckoffEvent(Enum):
    """Wyckoff significant events"""
    # Accumulation events
    PS = "PS"  # Preliminary Support
    SC = "SC"  # Selling Climax
    AR = "AR"  # Automatic Rally
    ST = "ST"  # Secondary Test
    SPRING = "SPRING"  # Spring (false breakdown)
    LPS = "LPS"  # Last Point of Support
    
    # Distribution events
    PSY = "PSY"  # Preliminary Supply
    BC = "BC"  # Buying Climax
    AR_DIST = "AR_DIST"  # Automatic Reaction
    ST_DIST = "ST_DIST"  # Secondary Test (Distribution)
    UPTHRUST = "UPTHRUST"  # Upthrust (false breakout)
    LPSY = "LPSY"  # Last Point of Supply
    
    NONE = "NONE"


class WyckoffAnalyzer:
    """
    Comprehensive Wyckoff Method analyzer
    
    Detects:
    - Market phases (Accumulation, Markup, Distribution, Markdown)
    - Wyckoff events (PS, SC, AR, ST, Spring, LPS, PSY, BC, UT, LPSY)
    - Volume patterns and anomalies
    - Entry/exit signals based on LPS/LPSY
    """
    
    def __init__(self):
        self.lookback_bars = 100  # Bars to analyze
        self.volume_ma_period = 20  # Moving average for volume comparison
        
        # Volume thresholds (relative to average)
        self.climax_volume_threshold = 2.0  # 200% of average = climax
        self.low_volume_threshold = 0.6  # 60% of average = low volume
        
        # Price spread thresholds (relative to ATR)
        self.wide_spread_threshold = 1.5  # 150% of ATR = wide spread
        self.narrow_spread_threshold = 0.5  # 50% of ATR = narrow spread
        
        # Phase detection parameters
        self.range_periods = 50  # Bars to define accumulation/distribution range
        self.range_tolerance = 0.02  # 2% tolerance for ranging market
        
    def analyze_symbol(self, symbol: str, timeframe, bars: int = 100) -> Optional[Dict]:
        """
        Perform complete Wyckoff analysis on a symbol
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: MT5 timeframe constant
            bars: Number of bars to analyze
            
        Returns:
            Dictionary with complete Wyckoff analysis or None if error
        """
        if not MT5_AVAILABLE:
            return None
            
        try:
            if not mt5.initialize():
                return None
                
            # Get price and volume data
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            tick_volume = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            
            mt5.shutdown()
            
            if rates is None or len(rates) < self.lookback_bars:
                return None
                
            # Extract data
            highs = rates['high']
            lows = rates['low']
            closes = rates['close']
            opens = rates['open']
            volumes = rates['tick_volume']  # MT5 tick volume
            times = rates['time']
            
            # Calculate technical indicators
            atr = self._calculate_atr(highs, lows, closes, period=14)
            volume_ma = self._calculate_sma(volumes, period=self.volume_ma_period)
            
            # Detect current phase
            current_phase = self._detect_phase(highs, lows, closes, volumes, volume_ma)
            
            # Detect Wyckoff events
            events = self._detect_events(
                highs, lows, closes, opens, volumes, volume_ma, atr, current_phase
            )
            
            # Find LPS/LPSY opportunities
            lps_lpsy = self._find_lps_lpsy(
                highs, lows, closes, opens, volumes, volume_ma, atr, events, current_phase
            )
            
            # Volume analysis
            volume_analysis = self._analyze_volume(volumes, volume_ma, closes)
            
            # Generate trading signals
            signals = self._generate_signals(lps_lpsy, current_phase, volume_analysis)
            
            # Create chart overlay data
            chart_data = self._generate_chart_overlay(
                times, highs, lows, closes, events, lps_lpsy
            )
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now(),
                'current_phase': current_phase,
                'events': events,
                'lps_lpsy': lps_lpsy,
                'volume_analysis': volume_analysis,
                'signals': signals,
                'chart_data': chart_data,
                'current_price': closes[-1],
                'atr': atr[-1]
            }
            
        except Exception as e:
            print(f"Error in Wyckoff analysis: {e}")
            return None
            
    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, 
                       closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range"""
        tr = np.zeros(len(highs))
        tr[0] = highs[0] - lows[0]
        
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr[i] = max(hl, hc, lc)
            
        # Simple moving average of TR
        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        return atr
        
    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        return np.convolve(data, np.ones(period)/period, mode='same')
        
    def _detect_phase(self, highs: np.ndarray, lows: np.ndarray, 
                      closes: np.ndarray, volumes: np.ndarray,
                      volume_ma: np.ndarray) -> WyckoffPhase:
        """
        Detect current Wyckoff phase
        
        Logic:
        - ACCUMULATION: Price ranging with high volume (smart money buying)
        - MARKUP: Price rising with increasing volume
        - DISTRIBUTION: Price ranging at high levels with high volume
        - MARKDOWN: Price falling with increasing volume
        """
        # Analyze last 50 bars
        recent_bars = min(50, len(closes))
        recent_closes = closes[-recent_bars:]
        recent_highs = highs[-recent_bars:]
        recent_lows = lows[-recent_bars:]
        recent_volumes = volumes[-recent_bars:]
        
        # Calculate range metrics
        range_high = np.max(recent_highs)
        range_low = np.min(recent_lows)
        range_size = range_high - range_low
        current_price = closes[-1]
        
        # Price position in range
        if range_size > 0:
            price_position = (current_price - range_low) / range_size
        else:
            price_position = 0.5
            
        # Trend direction
        sma_20 = np.mean(recent_closes[-20:])
        sma_50 = np.mean(recent_closes) if len(recent_closes) >= 50 else sma_20
        
        # Volume trend
        recent_volume_avg = np.mean(recent_volumes)
        older_volume_avg = np.mean(volumes[-100:-50]) if len(volumes) >= 100 else recent_volume_avg
        volume_increasing = recent_volume_avg > older_volume_avg * 1.1
        
        # Price volatility (ranging vs trending)
        price_changes = np.diff(recent_closes)
        volatility = np.std(price_changes)
        
        # Check if ranging (price oscillating within narrow range)
        ranging = range_size < (range_high * self.range_tolerance)
        
        # Phase detection logic
        if ranging and price_position < 0.4 and volume_increasing:
            # Low price range with high volume = Accumulation
            return WyckoffPhase.ACCUMULATION
            
        elif ranging and price_position > 0.6 and volume_increasing:
            # High price range with high volume = Distribution
            return WyckoffPhase.DISTRIBUTION
            
        elif current_price > sma_20 > sma_50 and sma_20 > sma_50 * 1.02:
            # Strong uptrend = Markup
            return WyckoffPhase.MARKUP
            
        elif current_price < sma_20 < sma_50 and sma_20 < sma_50 * 0.98:
            # Strong downtrend = Markdown
            return WyckoffPhase.MARKDOWN
            
        else:
            return WyckoffPhase.UNKNOWN
            
    def _detect_events(self, highs: np.ndarray, lows: np.ndarray,
                       closes: np.ndarray, opens: np.ndarray,
                       volumes: np.ndarray, volume_ma: np.ndarray,
                       atr: np.ndarray, phase: WyckoffPhase) -> List[Dict]:
        """
        Detect Wyckoff events in price history
        
        Returns list of detected events with their bar index and details
        """
        events = []
        
        # Only analyze recent bars for event detection
        lookback = min(self.range_periods, len(closes))
        
        for i in range(lookback, len(closes)):
            bar_range = highs[i] - lows[i]
            relative_volume = volumes[i] / volume_ma[i] if volume_ma[i] > 0 else 1.0
            
            # Detect climax conditions (very high volume + wide spread)
            is_climax = (relative_volume > self.climax_volume_threshold and 
                        bar_range > atr[i] * self.wide_spread_threshold)
            
            # Detect low volume conditions
            is_low_volume = relative_volume < self.low_volume_threshold
            
            # Detect narrow spread
            is_narrow_spread = bar_range < atr[i] * self.narrow_spread_threshold
            
            # ACCUMULATION EVENTS
            if phase == WyckoffPhase.ACCUMULATION:
                
                # Selling Climax (SC): Downward climax at bottom
                if (is_climax and closes[i] < closes[i-1] and 
                    lows[i] == np.min(lows[max(0, i-20):i+1])):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.SC,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Selling Climax detected'
                    })
                    
                # Automatic Rally (AR): Strong bounce after SC
                elif (len(events) > 0 and events[-1]['event'] == WyckoffEvent.SC and
                      i - events[-1]['index'] <= 5 and
                      closes[i] > closes[i-1] and relative_volume > 1.2):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.AR,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Automatic Rally after SC'
                    })
                    
                # Secondary Test (ST): Test of SC low on lower volume
                elif (is_low_volume and is_narrow_spread and
                      abs(lows[i] - np.min(lows[max(0, i-30):i])) < atr[i] * 0.5):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.ST,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Secondary Test on low volume'
                    })
                    
                # Spring: False breakdown below support on low volume
                elif (is_low_volume and 
                      lows[i] < np.min(lows[max(0, i-20):i]) and
                      closes[i] > lows[i] + bar_range * 0.6):  # Close in upper part
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.SPRING,
                        'price': lows[i],
                        'volume': volumes[i],
                        'description': 'Spring - false breakdown'
                    })
                    
            # DISTRIBUTION EVENTS
            elif phase == WyckoffPhase.DISTRIBUTION:
                
                # Buying Climax (BC): Upward climax at top
                if (is_climax and closes[i] > closes[i-1] and
                    highs[i] == np.max(highs[max(0, i-20):i+1])):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.BC,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Buying Climax detected'
                    })
                    
                # Automatic Reaction (AR): Sharp drop after BC
                elif (len(events) > 0 and events[-1]['event'] == WyckoffEvent.BC and
                      i - events[-1]['index'] <= 5 and
                      closes[i] < closes[i-1] and relative_volume > 1.2):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.AR_DIST,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Automatic Reaction after BC'
                    })
                    
                # Secondary Test (ST): Test of BC high on lower volume
                elif (is_low_volume and is_narrow_spread and
                      abs(highs[i] - np.max(highs[max(0, i-30):i])) < atr[i] * 0.5):
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.ST_DIST,
                        'price': closes[i],
                        'volume': volumes[i],
                        'description': 'Secondary Test (Distribution) on low volume'
                    })
                    
                # Upthrust (UT): False breakout above resistance on low volume
                elif (is_low_volume and
                      highs[i] > np.max(highs[max(0, i-20):i]) and
                      closes[i] < highs[i] - bar_range * 0.6):  # Close in lower part
                    events.append({
                        'index': i,
                        'event': WyckoffEvent.UPTHRUST,
                        'price': highs[i],
                        'volume': volumes[i],
                        'description': 'Upthrust - false breakout'
                    })
                    
        return events
        
    def _find_lps_lpsy(self, highs: np.ndarray, lows: np.ndarray,
                       closes: np.ndarray, opens: np.ndarray,
                       volumes: np.ndarray, volume_ma: np.ndarray,
                       atr: np.ndarray, events: List[Dict],
                       phase: WyckoffPhase) -> Optional[Dict]:
        """
        Find Last Point of Support (LPS) or Last Point of Supply (LPSY)
        
        LPS occurs after Spring/ST in Accumulation or early Markup
        LPSY occurs after UT/ST in Distribution or early Markdown
        """
        if len(closes) < 20:
            return None
            
        # Analyze last 20 bars for LPS/LPSY
        recent_bars = 20
        
        # Check for LPS (Bullish)
        if phase in [WyckoffPhase.ACCUMULATION, WyckoffPhase.MARKUP]:
            
            # Must have Spring or ST in recent history
            has_spring = any(e['event'] == WyckoffEvent.SPRING for e in events[-10:]) if len(events) >= 10 else False
            has_st = any(e['event'] == WyckoffEvent.ST for e in events[-10:]) if len(events) >= 10 else False
            
            if not (has_spring or has_st):
                return None
                
            # Look for LPS characteristics in last 10 bars
            for i in range(len(closes) - 10, len(closes)):
                if i < recent_bars:
                    continue
                    
                bar_range = highs[i] - lows[i]
                relative_volume = volumes[i] / volume_ma[i] if volume_ma[i] > 0 else 1.0
                
                # LPS criteria:
                # 1. Low volume (< 80% of average)
                # 2. Narrow spread (< 70% of ATR)
                # 3. Close in upper half of bar
                # 4. Higher low than Spring/ST
                # 5. Pullback to support level
                
                is_low_vol = relative_volume < 0.8
                is_narrow = bar_range < atr[i] * 0.7
                close_upper = closes[i] > lows[i] + bar_range * 0.5
                
                # Check if this is a higher low
                recent_low = np.min(lows[max(0, i-30):i])
                is_higher_low = lows[i] > recent_low
                
                # Check if next bar bounces (confirmation)
                if i < len(closes) - 1:
                    next_bar_up = closes[i+1] > closes[i]
                    volume_increases = volumes[i+1] > volumes[i]
                else:
                    next_bar_up = False
                    volume_increases = False
                    
                if is_low_vol and is_narrow and close_upper and is_higher_low:
                    
                    # Calculate support/resistance flip level
                    sr_flip = np.mean(highs[max(0, i-20):i])
                    
                    return {
                        'type': 'LPS',
                        'index': i,
                        'price': closes[i],
                        'low': lows[i],
                        'high': highs[i],
                        'volume': volumes[i],
                        'relative_volume': relative_volume,
                        'bar_range': bar_range,
                        'confirmed': next_bar_up and volume_increases,
                        'entry_trigger': highs[i],  # Enter above LPS high
                        'stop_loss': lows[i],  # SL below LPS low
                        'support_resistance': sr_flip,
                        'description': 'Last Point of Support detected',
                        'strength': self._calculate_lps_strength(
                            is_low_vol, is_narrow, close_upper, next_bar_up, volume_increases
                        )
                    }
                    
        # Check for LPSY (Bearish)
        elif phase in [WyckoffPhase.DISTRIBUTION, WyckoffPhase.MARKDOWN]:
            
            # Must have Upthrust or ST in recent history
            has_ut = any(e['event'] == WyckoffEvent.UPTHRUST for e in events[-10:]) if len(events) >= 10 else False
            has_st = any(e['event'] == WyckoffEvent.ST_DIST for e in events[-10:]) if len(events) >= 10 else False
            
            if not (has_ut or has_st):
                return None
                
            # Look for LPSY characteristics in last 10 bars
            for i in range(len(closes) - 10, len(closes)):
                if i < recent_bars:
                    continue
                    
                bar_range = highs[i] - lows[i]
                relative_volume = volumes[i] / volume_ma[i] if volume_ma[i] > 0 else 1.0
                
                # LPSY criteria:
                # 1. Low volume
                # 2. Narrow spread
                # 3. Close in lower half of bar
                # 4. Lower high than UT/ST
                # 5. Rally to resistance level
                
                is_low_vol = relative_volume < 0.8
                is_narrow = bar_range < atr[i] * 0.7
                close_lower = closes[i] < highs[i] - bar_range * 0.5
                
                # Check if this is a lower high
                recent_high = np.max(highs[max(0, i-30):i])
                is_lower_high = highs[i] < recent_high
                
                # Check if next bar drops (confirmation)
                if i < len(closes) - 1:
                    next_bar_down = closes[i+1] < closes[i]
                    volume_increases = volumes[i+1] > volumes[i]
                else:
                    next_bar_down = False
                    volume_increases = False
                    
                if is_low_vol and is_narrow and close_lower and is_lower_high:
                    
                    # Calculate resistance/support flip level
                    rs_flip = np.mean(lows[max(0, i-20):i])
                    
                    return {
                        'type': 'LPSY',
                        'index': i,
                        'price': closes[i],
                        'low': lows[i],
                        'high': highs[i],
                        'volume': volumes[i],
                        'relative_volume': relative_volume,
                        'bar_range': bar_range,
                        'confirmed': next_bar_down and volume_increases,
                        'entry_trigger': lows[i],  # Enter below LPSY low
                        'stop_loss': highs[i],  # SL above LPSY high
                        'support_resistance': rs_flip,
                        'description': 'Last Point of Supply detected',
                        'strength': self._calculate_lps_strength(
                            is_low_vol, is_narrow, close_lower, next_bar_down, volume_increases
                        )
                    }
                    
        return None
        
    def _calculate_lps_strength(self, low_vol: bool, narrow: bool,
                                close_position: bool, next_confirm: bool,
                                vol_confirm: bool) -> str:
        """Calculate strength of LPS/LPSY signal"""
        score = sum([low_vol, narrow, close_position, next_confirm, vol_confirm])
        
        if score >= 4:
            return "STRONG"
        elif score >= 3:
            return "MODERATE"
        else:
            return "WEAK"
            
    def _analyze_volume(self, volumes: np.ndarray, volume_ma: np.ndarray,
                       closes: np.ndarray) -> Dict:
        """
        Analyze volume patterns and trends
        
        Returns volume analysis with effort vs result
        """
        if len(volumes) < 20:
            return {}
            
        recent_volumes = volumes[-20:]
        recent_vol_ma = volume_ma[-20:]
        recent_closes = closes[-20:]
        
        # Calculate volume trend
        vol_trend = np.polyfit(range(len(recent_volumes)), recent_volumes, 1)[0]
        volume_increasing = vol_trend > 0
        
        # Calculate price trend
        price_trend = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
        price_rising = price_trend > 0
        
        # Effort vs Result analysis
        avg_rel_volume = np.mean(recent_volumes / recent_vol_ma)
        price_change = abs(recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        
        # High effort (volume) vs low result (price change) = absorption
        if avg_rel_volume > 1.2 and price_change < 0.01:
            effort_result = "HIGH EFFORT, LOW RESULT - Absorption occurring"
            absorption = True
        # Low effort (volume) vs high result (price change) = no resistance
        elif avg_rel_volume < 0.8 and price_change > 0.02:
            effort_result = "LOW EFFORT, HIGH RESULT - No resistance"
            absorption = False
        else:
            effort_result = "Normal effort/result relationship"
            absorption = False
            
        # Volume/price divergence
        if volume_increasing and not price_rising:
            divergence = "BEARISH - Volume increasing but price not rising"
        elif not volume_increasing and price_rising:
            divergence = "WARNING - Price rising on decreasing volume"
        elif volume_increasing and price_rising:
            divergence = "BULLISH - Volume and price both rising"
        else:
            divergence = "NEUTRAL - Both decreasing"
            
        return {
            'volume_trend': 'INCREASING' if volume_increasing else 'DECREASING',
            'price_trend': 'RISING' if price_rising else 'FALLING',
            'avg_relative_volume': avg_rel_volume,
            'effort_result': effort_result,
            'absorption': absorption,
            'divergence': divergence,
            'current_volume_vs_avg': volumes[-1] / volume_ma[-1] if volume_ma[-1] > 0 else 1.0
        }
        
    def _generate_signals(self, lps_lpsy: Optional[Dict], phase: WyckoffPhase,
                         volume_analysis: Dict) -> Dict:
        """
        Generate trading signals based on Wyckoff analysis
        """
        signals = {
            'action': 'WAIT',
            'direction': None,
            'entry_price': None,
            'stop_loss': None,
            'target': None,
            'confidence': 'LOW',
            'reasons': []
        }
        
        if lps_lpsy is None:
            signals['reasons'].append("No LPS/LPSY detected")
            return signals
            
        # LPS Signal (Bullish)
        if lps_lpsy['type'] == 'LPS':
            
            if lps_lpsy['confirmed'] and lps_lpsy['strength'] in ['STRONG', 'MODERATE']:
                signals['action'] = 'BUY'
                signals['direction'] = 'BUY'
                signals['entry_price'] = lps_lpsy['entry_trigger']
                signals['stop_loss'] = lps_lpsy['stop_loss']
                
                # Target: Measured move or next resistance
                range_size = lps_lpsy['high'] - lps_lpsy['low']
                signals['target'] = lps_lpsy['entry_trigger'] + (range_size * 3)
                
                signals['confidence'] = lps_lpsy['strength']
                signals['reasons'].append(f"LPS confirmed with {lps_lpsy['strength']} signal")
                signals['reasons'].append(f"Low volume pullback ({lps_lpsy['relative_volume']:.2f}x avg)")
                
                if phase == WyckoffPhase.ACCUMULATION:
                    signals['reasons'].append("Accumulation phase - smart money buying")
                elif phase == WyckoffPhase.MARKUP:
                    signals['reasons'].append("Markup phase - trend continuation")
                    
            else:
                signals['action'] = 'WAIT'
                signals['reasons'].append("LPS detected but not confirmed yet")
                signals['reasons'].append("Wait for breakout above LPS high with volume")
                
        # LPSY Signal (Bearish)
        elif lps_lpsy['type'] == 'LPSY':
            
            if lps_lpsy['confirmed'] and lps_lpsy['strength'] in ['STRONG', 'MODERATE']:
                signals['action'] = 'SELL'
                signals['direction'] = 'SELL'
                signals['entry_price'] = lps_lpsy['entry_trigger']
                signals['stop_loss'] = lps_lpsy['stop_loss']
                
                # Target: Measured move or next support
                range_size = lps_lpsy['high'] - lps_lpsy['low']
                signals['target'] = lps_lpsy['entry_trigger'] - (range_size * 3)
                
                signals['confidence'] = lps_lpsy['strength']
                signals['reasons'].append(f"LPSY confirmed with {lps_lpsy['strength']} signal")
                signals['reasons'].append(f"Low volume rally ({lps_lpsy['relative_volume']:.2f}x avg)")
                
                if phase == WyckoffPhase.DISTRIBUTION:
                    signals['reasons'].append("Distribution phase - smart money selling")
                elif phase == WyckoffPhase.MARKDOWN:
                    signals['reasons'].append("Markdown phase - trend continuation")
                    
            else:
                signals['action'] = 'WAIT'
                signals['reasons'].append("LPSY detected but not confirmed yet")
                signals['reasons'].append("Wait for breakdown below LPSY low with volume")
                
        return signals
        
    def _generate_chart_overlay(self, times: np.ndarray, highs: np.ndarray,
                               lows: np.ndarray, closes: np.ndarray,
                               events: List[Dict], lps_lpsy: Optional[Dict]) -> Dict:
        """
        Generate data for chart overlay visualization
        
        Returns chart markers, lines, and zones to display
        """
        overlay = {
            'markers': [],
            'lines': [],
            'zones': []
        }
        
        # Add event markers
        for event in events[-20:]:  # Last 20 events
            idx = event['index']
            if idx >= len(times):
                continue
                
            marker = {
                'time': times[idx],
                'price': event['price'],
                'type': event['event'].value,
                'description': event['description'],
                'color': self._get_event_color(event['event']),
                'symbol': self._get_event_symbol(event['event'])
            }
            overlay['markers'].append(marker)
            
        # Add LPS/LPSY marker
        if lps_lpsy:
            idx = lps_lpsy['index']
            if idx < len(times):
                marker = {
                    'time': times[idx],
                    'price': lps_lpsy['price'],
                    'type': lps_lpsy['type'],
                    'description': lps_lpsy['description'],
                    'color': '#00FF00' if lps_lpsy['type'] == 'LPS' else '#FF0000',
                    'symbol': '🔵' if lps_lpsy['type'] == 'LPS' else '🔴',
                    'confirmed': lps_lpsy['confirmed'],
                    'strength': lps_lpsy['strength']
                }
                overlay['markers'].append(marker)
                
                # Add entry trigger line
                line = {
                    'type': 'horizontal',
                    'price': lps_lpsy['entry_trigger'],
                    'color': '#00FF00' if lps_lpsy['type'] == 'LPS' else '#FF0000',
                    'style': 'dashed',
                    'label': f"{lps_lpsy['type']} Entry: {lps_lpsy['entry_trigger']:.5f}"
                }
                overlay['lines'].append(line)
                
                # Add stop loss line
                line = {
                    'type': 'horizontal',
                    'price': lps_lpsy['stop_loss'],
                    'color': '#FF6B6B',
                    'style': 'solid',
                    'label': f"SL: {lps_lpsy['stop_loss']:.5f}"
                }
                overlay['lines'].append(line)
                
        return overlay
        
    def _get_event_color(self, event: WyckoffEvent) -> str:
        """Get color for event marker"""
        colors = {
            WyckoffEvent.SC: '#FF0000',
            WyckoffEvent.BC: '#FF0000',
            WyckoffEvent.AR: '#00FF00',
            WyckoffEvent.AR_DIST: '#FF6B6B',
            WyckoffEvent.SPRING: '#00BFFF',
            WyckoffEvent.UPTHRUST: '#FF69B4',
            WyckoffEvent.ST: '#FFA500',
            WyckoffEvent.ST_DIST: '#FFA500',
            WyckoffEvent.LPS: '#00FF00',
            WyckoffEvent.LPSY: '#FF0000'
        }
        return colors.get(event, '#FFFFFF')
        
    def _get_event_symbol(self, event: WyckoffEvent) -> str:
        """Get symbol for event marker"""
        symbols = {
            WyckoffEvent.SC: '⬇️',
            WyckoffEvent.BC: '⬆️',
            WyckoffEvent.AR: '↗️',
            WyckoffEvent.AR_DIST: '↘️',
            WyckoffEvent.SPRING: '🌱',
            WyckoffEvent.UPTHRUST: '⚡',
            WyckoffEvent.ST: '🔄',
            WyckoffEvent.ST_DIST: '🔄',
            WyckoffEvent.LPS: '🟢',
            WyckoffEvent.LPSY: '🔴'
        }
        return symbols.get(event, '•')
