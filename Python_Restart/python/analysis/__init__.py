"""
Smart Money Analysis Module

Professional institutional trading concepts:
- Order Blocks: Where smart money entered positions
- Liquidity Sweeps: Stop hunts before reversals
- Fair Value Gaps: Price imbalances that attract price back
- Market Structure: BOS (continuation) vs CHoCH (reversal)

Usage:
    from analysis.order_block_detector import order_block_detector
    from analysis.liquidity_sweep_detector import liquidity_sweep_detector
    from analysis.fair_value_gap_detector import fair_value_gap_detector
    from analysis.market_structure_detector import market_structure_detector

    # Detect order blocks
    obs = order_block_detector.detect_order_blocks(candles, symbol)

    # Check for recent liquidity sweep
    has_sweep = liquidity_sweep_detector.has_recent_sweep(candles, symbol)

    # Find unfilled FVGs
    fvgs = fair_value_gap_detector.get_unfilled_fvgs(symbol)

    # Check market structure
    aligned = market_structure_detector.check_structure_aligned(candles, 'BUY', symbol)
"""

from .order_block_detector import order_block_detector
from .liquidity_sweep_detector import liquidity_sweep_detector
from .fair_value_gap_detector import fair_value_gap_detector
from .market_structure_detector import market_structure_detector

__all__ = [
    'order_block_detector',
    'liquidity_sweep_detector',
    'fair_value_gap_detector',
    'market_structure_detector'
]
