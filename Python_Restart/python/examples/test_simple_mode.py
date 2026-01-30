#!/usr/bin/env python3
"""
Test Simple Mode - Demo of Trade Decision Assistant

Shows how complex statistics get translated into simple decisions.

Run: python examples/test_simple_mode.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock vprint if PyQt6 not available
try:
    from core.trade_decision_assistant import trade_decision_assistant
except ModuleNotFoundError:
    print("Note: Running in standalone mode (PyQt6 not available)")
    print("This is just a demo - in the actual app, full functionality is available.")
    print()

    # Minimal mock for demo purposes
    class MockDecisionAssistant:
        def analyze_opportunity(self, opp):
            class MockDecision:
                action = "TAKE"
                action_color = "#10B981"
                action_icon = "✓"
                quality_score = 8
                quality_stars = "★★★★★★★★☆☆"
                quality_description = "Excellent"
                headline = "Strong setup example"
                explanation = "Mock explanation"
                recommendation = "Mock recommendation"
                confidence = "High"
                confidence_percent = 80
                confidence_icon = "🟢🟢🟢"
                confidence_explanation = "Mock confidence"
                risk_amount_conservative = 1.6
                risk_amount_balanced = 3.2
                risk_amount_aggressive = 6.4
                risk_recommendation = "Balanced"
                risk_explanation = "Mock risk explanation"
                projection_100_trades = "Mock projection"
                projection_explanation = "Mock explanation"
                projection_warning = None
                vs_portfolio = None
                vs_other_opportunities = None
                historical_summary = "Mock history"
                recent_trend = None
                warnings = []
                alerts = []
            return MockDecision()

        def format_for_ui(self, decision):
            return "DEMO MODE - Install full system for actual analysis"

    trade_decision_assistant = MockDecisionAssistant()


def main():
    """Demo the Trade Decision Assistant"""

    print("=" * 80)
    print("  TRADE DECISION ASSISTANT - MAKING STATISTICS SIMPLE")
    print("=" * 80)
    print()

    # Example 1: STRONG TRADE (High quality, lots of data)
    print("Example 1: STRONG TRADE")
    print("-" * 80)

    strong_trade = {
        'symbol': 'EURUSD',
        'timeframe': 'H1',
        'direction': 'BUY',
        'entry': 1.1234,
        'stop_loss': 1.1200,
        'take_profit': 1.1300,
        'risk_reward': 2.1,
        'quality_score': 85,
        # Statistical enhancements (from our system)
        'statistical_win_prob': 0.653,
        'statistical_ev': 0.52,
        'statistical_sample_size': 47,
        'statistical_confidence': 'High',
        'statistical_ci_lower': 0.58,
        'statistical_ci_upper': 0.72,
        'statistical_kelly_half': 0.032,
        'statistical_kelly_quarter': 0.016,
    }

    decision = trade_decision_assistant.analyze_opportunity(strong_trade)
    print(trade_decision_assistant.format_for_ui(decision))
    print()

    # Example 2: MARGINAL TRADE (Positive but limited data)
    print("\n" + "=" * 80)
    print("Example 2: MARGINAL TRADE (Limited Data)")
    print("-" * 80)

    marginal_trade = {
        'symbol': 'GBPJPY',
        'timeframe': 'M15',
        'direction': 'SELL',
        'entry': 197.50,
        'stop_loss': 197.80,
        'take_profit': 196.90,
        'risk_reward': 2.0,
        'quality_score': 65,
        'statistical_win_prob': 0.571,  # 4W / 3L
        'statistical_ev': 0.14,
        'statistical_sample_size': 7,  # Limited data!
        'statistical_confidence': 'Low',
        'statistical_ci_lower': 0.32,
        'statistical_ci_upper': 0.78,
        'statistical_kelly_half': 0.014,
        'statistical_kelly_quarter': 0.007,
    }

    decision = trade_decision_assistant.analyze_opportunity(marginal_trade)
    print(trade_decision_assistant.format_for_ui(decision))
    print()

    # Example 3: LOSING TRADE (Negative EV)
    print("\n" + "=" * 80)
    print("Example 3: LOSING TRADE (Negative EV)")
    print("-" * 80)

    losing_trade = {
        'symbol': 'AUDUSD',
        'timeframe': 'H4',
        'direction': 'BUY',
        'entry': 0.6850,
        'stop_loss': 0.6820,
        'take_profit': 0.6900,
        'risk_reward': 1.7,
        'quality_score': 45,
        'statistical_win_prob': 0.42,  # Below 50%!
        'statistical_ev': -0.24,  # Negative!
        'statistical_sample_size': 24,
        'statistical_confidence': 'Medium',
        'statistical_ci_lower': 0.28,
        'statistical_ci_upper': 0.56,
        'statistical_kelly_half': 0.0,
        'statistical_kelly_quarter': 0.0,
    }

    decision = trade_decision_assistant.analyze_opportunity(losing_trade)
    print(trade_decision_assistant.format_for_ui(decision))
    print()

    # Example 4: NEW PATTERN (No historical data)
    print("\n" + "=" * 80)
    print("Example 4: NEW PATTERN (Learning Phase)")
    print("-" * 80)

    new_pattern = {
        'symbol': 'USDJPY',
        'timeframe': 'D1',
        'direction': 'SELL',
        'entry': 149.50,
        'stop_loss': 150.20,
        'take_profit': 147.80,
        'risk_reward': 2.4,
        'quality_score': 70,
        'statistical_win_prob': 0.50,  # Default (no data)
        'statistical_ev': 0.0,
        'statistical_sample_size': 0,  # No trades yet!
        'statistical_confidence': 'No data',
        'statistical_ci_lower': 0.40,
        'statistical_ci_upper': 0.60,
        'statistical_kelly_half': 0.02,
        'statistical_kelly_quarter': 0.01,
    }

    decision = trade_decision_assistant.analyze_opportunity(new_pattern)
    print(trade_decision_assistant.format_for_ui(decision))
    print()

    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print()
    print("As you can see, the Trade Decision Assistant:")
    print()
    print("✓ Converts complex stats into YES/NO/MAYBE decisions")
    print("✓ Shows quality scores (1-10) anyone can understand")
    print("✓ Explains WHY in plain English")
    print("✓ Gives exact risk percentages")
    print("✓ Projects long-term results ('100 trades like this...')")
    print("✓ Flags warnings and highlights strengths")
    print("✓ Shows confidence levels")
    print()
    print("No math degree needed - just clear, actionable guidance!")
    print()


if __name__ == '__main__':
    main()
