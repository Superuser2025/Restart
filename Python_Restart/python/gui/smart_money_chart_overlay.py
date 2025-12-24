"""
Smart Money Chart Overlay Manager
Connects smart money detectors to the chart overlay system for visualization
"""

from typing import List, Dict, Optional
from analysis.order_block_detector import order_block_detector
from analysis.liquidity_sweep_detector import liquidity_sweep_detector
from analysis.fair_value_gap_detector import fair_value_gap_detector
from analysis.market_structure_detector import market_structure_detector


class SmartMoneyChartOverlay:
    """
    Manages smart money overlays on the chart.

    Converts detector output into chart zones and markers:
    - Order Blocks → Green/Red rectangles
    - FVG Zones → Yellow/Magenta shaded areas
    - Liquidity Sweeps → Orange dotted lines
    - BOS/CHoCH → Arrows/labels
    """

    def __init__(self):
        self.enabled_overlays = {
            'Order Blocks': True,
            'FVG Zones': True,
            'Liquidity Lines': True,
            'Structure Markers': True
        }

    def generate_zones_from_detectors(
        self,
        candles: List[Dict],
        symbol: str,
        chart_overlay_system
    ):
        """
        Generate chart zones from smart money detectors.

        Args:
            candles: List of candle data
            symbol: Trading symbol
            chart_overlay_system: ChartOverlaySystem instance
        """
        # Clear existing smart money zones
        chart_overlay_system.clear_zones()

        if not candles or len(candles) < 10:
            print(f"[SmartMoneyOverlay] ERROR: Not enough candles ({len(candles) if candles else 0})")
            return

        print(f"\n[SmartMoneyOverlay] ═══ DETECTION START for {symbol} ═══")
        print(f"[SmartMoneyOverlay] → Analyzing {len(candles)} candles")

        # ============================================================
        # ORDER BLOCKS → Green/Red Rectangles
        # ============================================================
        if self.enabled_overlays['Order Blocks']:
            print(f"\n[SmartMoneyOverlay] --- ORDER BLOCK DETECTION ---")
            order_blocks = order_block_detector.detect_order_blocks(
                candles, symbol, lookback=150, min_impulse_pips=8  # RELAXED: was 50 lookback, 15 pips
            )
            print(f"[SmartMoneyOverlay] Total OBs detected: {len(order_blocks)}")

            # Show ALL OBs, not just valid ones (for debugging)
            valid_obs = [ob for ob in order_blocks if ob['valid'] and not ob['mitigated']]
            mitigated_obs = [ob for ob in order_blocks if ob['mitigated']]
            invalid_obs = [ob for ob in order_blocks if not ob['valid']]

            print(f"[SmartMoneyOverlay]   → Valid (unmitigated): {len(valid_obs)}")
            print(f"[SmartMoneyOverlay]   → Mitigated: {len(mitigated_obs)}")
            print(f"[SmartMoneyOverlay]   → Invalid: {len(invalid_obs)}")

            # Show top 10 valid OBs, or fallback to ANY OBs if none valid
            display_obs = valid_obs[:10] if valid_obs else order_blocks[:10]
            print(f"[SmartMoneyOverlay]   → Displaying: {len(display_obs)} OBs")

            for ob in display_obs:
                if ob['type'] == 'demand':
                    # Bullish OB → Green
                    color = "#00ff00"
                    name = "Bullish OB"
                else:
                    # Bearish OB → Red
                    color = "#ff0000"
                    name = "Bearish OB"

                chart_overlay_system.add_zone(
                    name=name,
                    color=color,
                    top=ob['price_high'],
                    bottom=ob['price_low'],
                    zone_type="Order Block"
                )

        # ============================================================
        # FAIR VALUE GAPS → Yellow/Magenta Shaded Areas
        # ============================================================
        if self.enabled_overlays['FVG Zones']:
            print(f"\n[SmartMoneyOverlay] --- FVG DETECTION ---")
            fvgs = fair_value_gap_detector.detect_fair_value_gaps(
                candles, symbol, lookback=150, min_gap_pips=3  # RELAXED: was 50 lookback, 5 pips
            )
            print(f"[SmartMoneyOverlay] Total FVGs detected: {len(fvgs)}")

            # Show ALL FVGs with their fill status
            unfilled = [fvg for fvg in fvgs if not fvg['filled']]
            partial = [fvg for fvg in fvgs if fvg['filled'] and fvg['fill_percentage'] < 50]
            filled = [fvg for fvg in fvgs if fvg['fill_percentage'] >= 50]

            print(f"[SmartMoneyOverlay]   → Unfilled: {len(unfilled)}")
            print(f"[SmartMoneyOverlay]   → Partially filled (<50%): {len(partial)}")
            print(f"[SmartMoneyOverlay]   → Filled (>=50%): {len(filled)}")

            # Show top 10 unfilled, or fallback to ANY FVGs
            display_fvgs = unfilled[:10] if unfilled else (partial[:5] if partial else fvgs[:5])
            print(f"[SmartMoneyOverlay]   → Displaying: {len(display_fvgs)} FVGs")

            for fvg in display_fvgs:
                if fvg['type'] == 'bullish':
                    # Bullish FVG → Cyan/Yellow
                    color = "#ffff00"  # Yellow
                    name = "FVG Up"
                else:
                    # Bearish FVG → Magenta
                    color = "#ff00ff"  # Magenta
                    name = "FVG Down"

                chart_overlay_system.add_zone(
                    name=name,
                    color=color,
                    top=fvg['top'],
                    bottom=fvg['bottom'],
                    zone_type="FVG"
                )

        # ============================================================
        # LIQUIDITY SWEEPS → Orange Horizontal Lines
        # ============================================================
        if self.enabled_overlays['Liquidity Lines']:
            print(f"\n[SmartMoneyOverlay] --- LIQUIDITY SWEEP DETECTION ---")
            sweeps = liquidity_sweep_detector.detect_liquidity_sweeps(
                candles, symbol, lookback=150, tolerance_pips=5  # RELAXED: was 50 lookback, 3 pips
            )
            print(f"[SmartMoneyOverlay] Total Sweeps detected: {len(sweeps)}")
            print(f"[SmartMoneyOverlay]   → Displaying: {min(len(sweeps), 5)} sweeps")

            # Show top 5 recent sweeps (was 3)
            for sweep in sweeps[:5]:
                # Liquidity sweep level → Orange line (thin zone)
                color = "#ff8800"  # Orange
                name = f"Liquidity ({sweep['type'].upper()})"

                # Create thin zone (1 pip height)
                pip = 0.0001
                chart_overlay_system.add_zone(
                    name=name,
                    color=color,
                    top=sweep['level'] + pip,
                    bottom=sweep['level'] - pip,
                    zone_type="Liquidity"
                )

        # ============================================================
        # MARKET STRUCTURE (BOS/CHoCH) → Labels/Arrows
        # ============================================================
        if self.enabled_overlays['Structure Markers']:
            structure_events, current_trend = market_structure_detector.detect_structure_shifts(
                candles, symbol, lookback=150  # RELAXED: was 50 lookback
            )

            # Show top 5 recent structure events (was 3)
            for event in structure_events[:5]:
                # Determine color based on direction
                if event['direction'] == 'bullish':
                    color = "#00ff88"  # Green
                    name = f"BOS/CHoCH ↑" if event['type'] == 'BOS' else f"CHoCH ↑"
                else:
                    color = "#ff4444"  # Red
                    name = f"BOS/CHoCH ↓" if event['type'] == 'BOS' else f"CHoCH ↓"

                # Create small marker zone at structure event price
                pip = 0.0002
                chart_overlay_system.add_zone(
                    name=name,
                    color=color,
                    top=event['price'] + pip,
                    bottom=event['price'] - pip,
                    zone_type="Structure"
                )

        # Trigger chart redraw
        chart_overlay_system.update()

        # Log detection results for debugging
        print(f"\n[SmartMoneyOverlay] Zone Detection Summary for {symbol}:")
        print(f"  → Total zones rendered: {len(chart_overlay_system.zones)}")
        zone_types = {}
        for zone in chart_overlay_system.zones:
            zone_types[zone.zone_type] = zone_types.get(zone.zone_type, 0) + 1
        for ztype, count in zone_types.items():
            print(f"  → {ztype}: {count} zones")

    def toggle_overlay(self, overlay_name: str, enabled: bool):
        """Toggle specific overlay type"""
        if overlay_name in self.enabled_overlays:
            self.enabled_overlays[overlay_name] = enabled

    def get_overlay_status(self) -> Dict[str, bool]:
        """Get current overlay enable/disable status"""
        return self.enabled_overlays.copy()


# Global instance
smart_money_chart_overlay = SmartMoneyChartOverlay()
