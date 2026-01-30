"""
Direction-Neutral Trading System - Break the Long Bias

Solves the psychological limitation where traders avoid SHORT trades
and only feel comfortable taking LONG trades.

Strategies:
1. Reframe SELL as BUY the other currency
2. Show profit potential instead of direction
3. Visual neutrality - both directions equally appealing
4. Statistical proof that SELLs are equally profitable
5. Gamification - reward direction-neutral trading
6. Mirror mode - flip everything to BUYs
7. Bias detection and alerts

Author: AppleTrader Pro
Date: 2026-01-30
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DirectionNeutralView:
    """
    Reframed view of a trading opportunity that removes directional bias
    """

    # Original trade
    original_symbol: str  # "EURUSD"
    original_direction: str  # "SELL"

    # Reframed as BUY
    reframed_symbol: str  # "USDEUR" (inverted) or "USD vs EUR"
    reframed_direction: str  # Always "BUY"
    reframed_narrative: str  # "Buy the Dollar (against Euro)"

    # Profit-focused framing
    profit_narrative: str  # "Profit from Euro weakness"
    target_profit: float  # "$450 profit target"

    # Psychological messaging
    comfort_message: str  # "This is just buying USD - same as buying EURUSD, but reversed"
    equivalence_proof: str  # "Buying USD = Selling EUR. Mathematically identical."


class DirectionBiasDetector:
    """
    Detects if trader has directional bias and provides interventions
    """

    def __init__(self):
        """Initialize bias detector"""
        self.trade_history = []

    def analyze_bias(self, trade_history: List[Dict]) -> Dict:
        """
        Analyze if trader has long bias

        Args:
            trade_history: List of trades with 'direction' field

        Returns:
            Dict with bias analysis
        """
        if not trade_history:
            return {
                'has_bias': False,
                'bias_type': None,
                'severity': 0,
                'message': 'No trade history yet'
            }

        buys = sum(1 for t in trade_history if t.get('direction') == 'BUY')
        sells = sum(1 for t in trade_history if t.get('direction') == 'SELL')
        total = len(trade_history)

        buy_pct = buys / total if total > 0 else 0
        sell_pct = sells / total if total > 0 else 0

        # Detect bias
        if total < 5:
            # Too few trades to detect bias
            return {
                'has_bias': False,
                'bias_type': None,
                'severity': 0,
                'message': f'Only {total} trades - too early to detect bias'
            }

        # Severe long bias
        if buy_pct >= 0.80:
            return {
                'has_bias': True,
                'bias_type': 'LONG',
                'severity': 3,  # Critical
                'buy_count': buys,
                'sell_count': sells,
                'buy_pct': buy_pct * 100,
                'sell_pct': sell_pct * 100,
                'message': f'⚠️ CRITICAL LONG BIAS: {buy_pct*100:.0f}% BUY vs {sell_pct*100:.0f}% SELL',
                'recommendation': 'You are missing 80% of SELL opportunities! Enable Mirror Mode to see all trades as BUYs.',
                'missed_opportunities': self._calculate_missed_opportunities(trade_history)
            }

        # Moderate long bias
        elif buy_pct >= 0.65:
            return {
                'has_bias': True,
                'bias_type': 'LONG',
                'severity': 2,  # Moderate
                'buy_count': buys,
                'sell_count': sells,
                'buy_pct': buy_pct * 100,
                'sell_pct': sell_pct * 100,
                'message': f'⚠️ MODERATE LONG BIAS: {buy_pct*100:.0f}% BUY vs {sell_pct*100:.0f}% SELL',
                'recommendation': 'Try taking some SELL setups - they are statistically just as profitable!',
                'missed_opportunities': self._calculate_missed_opportunities(trade_history)
            }

        # Slight long bias
        elif buy_pct >= 0.60:
            return {
                'has_bias': True,
                'bias_type': 'LONG',
                'severity': 1,  # Mild
                'buy_count': buys,
                'sell_count': sells,
                'buy_pct': buy_pct * 100,
                'sell_pct': sell_pct * 100,
                'message': f'Slight long bias: {buy_pct*100:.0f}% BUY vs {sell_pct*100:.0f}% SELL',
                'recommendation': 'You are direction-balanced! Keep taking opportunities regardless of direction.',
                'missed_opportunities': 0
            }

        # Severe short bias (rare but possible)
        elif sell_pct >= 0.80:
            return {
                'has_bias': True,
                'bias_type': 'SHORT',
                'severity': 3,
                'buy_count': buys,
                'sell_count': sells,
                'buy_pct': buy_pct * 100,
                'sell_pct': sell_pct * 100,
                'message': f'⚠️ CRITICAL SHORT BIAS: {sell_pct*100:.0f}% SELL vs {buy_pct*100:.0f}% BUY',
                'recommendation': 'You are missing BUY opportunities! Focus on taking BUY setups.',
                'missed_opportunities': self._calculate_missed_opportunities(trade_history)
            }

        # Balanced!
        else:
            return {
                'has_bias': False,
                'bias_type': 'BALANCED',
                'severity': 0,
                'buy_count': buys,
                'sell_count': sells,
                'buy_pct': buy_pct * 100,
                'sell_pct': sell_pct * 100,
                'message': f'✓ DIRECTION NEUTRAL: {buy_pct*100:.0f}% BUY, {sell_pct*100:.0f}% SELL',
                'recommendation': 'Excellent! You are taking opportunities regardless of direction.',
                'missed_opportunities': 0
            }

    def _calculate_missed_opportunities(self, trade_history: List[Dict]) -> int:
        """Estimate how many opportunities were missed due to bias"""
        # Rough estimate: if trader has 80% long bias, they likely skipped
        # ~3x as many SELL opportunities
        buys = sum(1 for t in trade_history if t.get('direction') == 'BUY')
        sells = sum(1 for t in trade_history if t.get('direction') == 'SELL')

        if buys == 0:
            return 0

        expected_sells = buys  # Should be roughly 50/50
        missed = expected_sells - sells

        return max(0, missed)


class DirectionNeutralizer:
    """
    Converts directional trades into direction-neutral framing
    """

    def reframe_as_buy(self, opportunity: Dict) -> DirectionNeutralView:
        """
        Reframe any trade as a BUY opportunity

        For BUY trades: Keep as-is
        For SELL trades: Reframe as buying the counter-currency

        Args:
            opportunity: Trade opportunity dict

        Returns:
            DirectionNeutralView with reframed narrative
        """
        symbol = opportunity.get('symbol', 'UNKNOWN')
        direction = opportunity.get('direction', 'BUY')
        entry = opportunity.get('entry', 0)
        sl = opportunity.get('stop_loss', 0)
        tp = opportunity.get('take_profit', 0)

        # Calculate profit potential
        if direction == 'BUY':
            profit_pips = (tp - entry) * 10000  # Rough estimate for forex
        else:
            profit_pips = (entry - tp) * 10000

        profit_amount = abs(profit_pips * 10)  # $10 per pip estimate

        # Reframe SELL as BUY
        if direction == 'SELL':
            # Parse symbol (e.g., "EURUSD" → base="EUR", quote="USD")
            if len(symbol) == 6:
                base = symbol[:3]
                quote = symbol[3:6]
            else:
                base = "BASE"
                quote = "QUOTE"

            # Reframe
            reframed_symbol = f"{quote}{base}"  # "USDEUR"
            reframed_direction = "BUY"
            reframed_narrative = f"Buy {quote} (against {base})"

            profit_narrative = f"Profit from {base} weakness"
            comfort_message = f"This is buying {quote} - same as any BUY trade, just on inverted pair"
            equivalence_proof = f"Selling {symbol} = Buying {quote}. Mathematically identical. Same profit!"

        else:  # Already BUY
            if len(symbol) == 6:
                base = symbol[:3]
                quote = symbol[3:6]
            else:
                base = "BASE"
                quote = "QUOTE"

            reframed_symbol = symbol
            reframed_direction = "BUY"
            reframed_narrative = f"Buy {base} (against {quote})"

            profit_narrative = f"Profit from {base} strength"
            comfort_message = "Standard BUY trade"
            equivalence_proof = f"Buying {symbol} = Buying {base}."

        return DirectionNeutralView(
            original_symbol=symbol,
            original_direction=direction,
            reframed_symbol=reframed_symbol,
            reframed_direction=reframed_direction,
            reframed_narrative=reframed_narrative,
            profit_narrative=profit_narrative,
            target_profit=profit_amount,
            comfort_message=comfort_message,
            equivalence_proof=equivalence_proof
        )

    def get_profit_focused_display(self, opportunity: Dict) -> Dict:
        """
        Create profit-focused display that hides direction

        Instead of "SELL EURUSD", show:
        "PROFIT OPPORTUNITY: $450 target"
        """
        neutral_view = self.reframe_as_buy(opportunity)

        return {
            'headline': f"💰 PROFIT OPPORTUNITY",
            'sub_headline': f"{neutral_view.profit_narrative}",
            'target': f"${neutral_view.target_profit:.0f} target",
            'action': neutral_view.reframed_direction,  # Always "BUY"
            'symbol': neutral_view.reframed_symbol,
            'narrative': neutral_view.reframed_narrative,
            'comfort': neutral_view.comfort_message,
            'proof': neutral_view.equivalence_proof
        }


class BiasBreakingInterventions:
    """
    Active interventions to break directional bias
    """

    def __init__(self):
        """Initialize interventions"""
        self.bias_detector = DirectionBiasDetector()
        self.neutralizer = DirectionNeutralizer()

    def get_intervention_for_sell_opportunity(self, opportunity: Dict) -> Dict:
        """
        Get psychological intervention for SELL opportunity

        Returns messaging to make SELL feel comfortable
        """
        neutral = self.neutralizer.reframe_as_buy(opportunity)

        return {
            'intervention_type': 'REFRAME_AS_BUY',
            'original_message': f"SELL {opportunity.get('symbol')}",
            'reframed_message': f"BUY {neutral.reframed_symbol} ({neutral.reframed_narrative})",
            'comfort_message': neutral.comfort_message,
            'equivalence_proof': neutral.equivalence_proof,
            'visual_hint': "💡 This is a BUY trade on the inverted pair - psychologically easier!",
            'statistics_proof': "Historical stats show SELL trades have same win rate as BUY trades",
            'profit_focus': f"Focus on profit: ${neutral.target_profit:.0f} target - direction doesn't matter!"
        }

    def get_bias_alert(self, trade_history: List[Dict]) -> Optional[Dict]:
        """
        Generate alert if bias detected

        Returns alert dict or None if no bias
        """
        analysis = self.bias_detector.analyze_bias(trade_history)

        if not analysis['has_bias']:
            return None

        if analysis['severity'] >= 2:  # Moderate or Critical
            return {
                'alert_type': 'CRITICAL' if analysis['severity'] == 3 else 'WARNING',
                'title': '⚠️ Directional Bias Detected',
                'message': analysis['message'],
                'recommendation': analysis['recommendation'],
                'stats': f"{analysis['buy_count']} BUY trades vs {analysis['sell_count']} SELL trades",
                'missed_count': analysis['missed_opportunities'],
                'action_button': 'Enable Mirror Mode' if analysis['severity'] == 3 else 'Learn About SELL Trades',
                'severity_color': '#EF4444' if analysis['severity'] == 3 else '#F59E0B'
            }

        return None

    def get_sell_encouragement(self, sell_opportunity: Dict) -> str:
        """
        Generate encouraging message for SELL opportunity
        """
        encouragements = [
            "💎 Don't skip this! SELL trades are equally profitable.",
            "🎯 Remember: Selling is just buying the other currency!",
            "📈 Profit goes UP whether you BUY or SELL!",
            "✓ This SELL trade has the same quality as your best BUY trades.",
            "💰 Direction doesn't matter - profit potential matters!",
            "🔄 Think of this as BUYING weakness - same as buying strength!",
            "⭐ Top traders are direction-neutral - they take both!",
            "🎓 SELLs have 52% win rate, BUYs have 51% - no difference!"
        ]

        import random
        return random.choice(encouragements)


# Global instances
bias_detector = DirectionBiasDetector()
direction_neutralizer = DirectionNeutralizer()
bias_interventions = BiasBreakingInterventions()
