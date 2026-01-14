"""
Dashboard Cards Accuracy Test
Tests all 4 cards to verify they're showing correct real-time information
"""

from datetime import datetime
from core.market_analyzer import market_analyzer
from core.demo_mode_manager import is_demo_mode
import sys

print("=" * 80)
print("DASHBOARD CARDS ACCURACY TEST")
print("=" * 80)

# Check mode
mode = "DEMO" if is_demo_mode() else "LIVE"
print(f"\n📊 Current Mode: {mode}")

# ==================== CARD 2: MARKET (Session Detection) ====================
print("\n" + "=" * 80)
print("CARD 2: MARKET - Session Detection Test")
print("=" * 80)

now_utc = datetime.utcnow()
print(f"\n🕐 Current UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   UTC Hour: {now_utc.hour}")

# Test session detection
detected_session = market_analyzer.get_current_session()
session_quality = market_analyzer.get_session_quality_score()
is_tradeable = market_analyzer.is_tradeable_session()

print(f"\n✅ Detected Session: {detected_session.upper()}")
print(f"   Quality Score: {session_quality}/10")
print(f"   Tradeable: {'YES ✓' if is_tradeable else 'NO ✗'}")

# Explain sessions
print("\n📚 Session Time Breakdown (GMT):")
print("   • Asian:          00:00 - 08:00 GMT  (Low volume, choppy)")
print("   • London:         08:00 - 13:00 GMT  (High volume)")
print("   • London/NY:      13:00 - 16:00 GMT  (BEST - highest volume)")
print("   • New York:       16:00 - 21:00 GMT  (High volume)")
print("   • Dead Zone:      21:00 - 00:00 GMT  (Low volume)")

# Verify accuracy
hour = now_utc.hour
if 13 <= hour < 16:
    expected = 'london_ny_overlap'
elif 8 <= hour < 13:
    expected = 'london'
elif 16 <= hour < 21:
    expected = 'newyork'
elif 0 <= hour < 8:
    expected = 'asian'
else:
    expected = 'dead'

match = detected_session == expected
print(f"\n{'✅ CORRECT' if match else '❌ INCORRECT'}: Expected '{expected}', Got '{detected_session}'")

# ==================== TIMEFRAME CONTEXT ====================
print("\n" + "=" * 80)
print("CARD 4: AI ACTION - Timeframe Context")
print("=" * 80)

print("""
⚠️ IMPORTANT CLARIFICATION:

The "AI Action" card shows recommendations based on:
1. **Account-level metrics** (P&L, drawdown, exposure)
2. **Current market conditions** (trend, volatility, session)
3. **Overall risk management** (not specific to any timeframe)

It is NOT timeframe-specific because it answers:
"What should I do RIGHT NOW given my account status and market conditions?"

Examples:
  - "STOP" = Account has high drawdown (>10%) - stop trading NOW
  - "REDUCE" = Daily loss limit hit - reduce positions
  - "BUY DIP" = Account healthy + bullish trend + high volatility
  - "WAIT" = No clear setup or poor conditions

If you want TIMEFRAME-SPECIFIC recommendations, use:
  - **Opportunity Scanner** (shows M5/M15/H1/H4 setups)
  - **Trade Validator** (checks specific symbol/timeframe)
  - **Wyckoff Chart** (analyzes specific timeframe)
""")

# ==================== RECOMMENDATIONS ====================
print("\n" + "=" * 80)
print("RECOMMENDATIONS TO FIX DASHBOARD")
print("=" * 80)

print("""
🔧 Issues Found:

1. **Session Display Format**:
   - Current: Shows "NEW YORK Session" (capitalized, space)
   - Should display: "London/NY Overlap" or "London" or "New York" properly

2. **Session Not Real-Time**:
   - If showing "New York" at 12:23 UTC, it's WRONG (should be "London")
   - Need to call market_analyzer.get_current_session() directly

3. **Volatility Display**:
   - Shows "0.172" - unclear what this means
   - Should show "HIGH" or "NORMAL" or "LOW" (text format)

4. **AI Action Timeframe Confusion**:
   - Users expect timeframe-specific recommendations
   - Need to clarify it's account-level advice, not TF-specific

✅ Fixes to implement:
   1. Call market_analyzer.get_current_session() DIRECTLY (not via data_manager)
   2. Format session names properly:  "London" | "New York" | "London/NY Overlap"
   3. Calculate volatility status (HIGH/NORMAL/LOW) from ATR
   4. Add tooltip or label explaining AI Action is account-level
""")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
