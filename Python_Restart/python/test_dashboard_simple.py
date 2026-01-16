"""Simple dashboard accuracy test without dependencies"""

from datetime import datetime, time

print("=" * 80)
print("DASHBOARD ACCURACY DIAGNOSTIC")
print("=" * 80)

# Get current UTC time
now_utc = datetime.utcnow()
current_time = now_utc.time()
hour = now_utc.hour

print(f"\n🕐 Current UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Current Hour (UTC): {hour}")

# Session detection logic (from market_analyzer.py)
if 13 <= hour < 16:
    session = 'London/NY Overlap'
    quality = 10
    tradeable = True
    description = "BEST trading hours - highest volume and liquidity"
elif 8 <= hour < 13:
    session = 'London'
    quality = 8
    tradeable = True
    description = "High volume, trending moves"
elif 16 <= hour < 21:
    session = 'New York'
    quality = 7
    tradeable = True
    description = "High volume, trending moves"
elif 0 <= hour < 8:
    session = 'Asian'
    quality = 3
    tradeable = False
    description = "Low volume, choppy - avoid trading"
else:
    session = 'Dead Zone'
    quality = 0
    tradeable = False
    description = "Very low volume - avoid trading"

print(f"\n✅ CORRECT Session: {session}")
print(f"   Quality: {quality}/10")
print(f"   Tradeable: {'YES' if tradeable else 'NO'}")
print(f"   Note: {description}")

print("\n" + "=" * 80)
print("WHAT YOUR DASHBOARD SHOULD SHOW")
print("=" * 80)

print(f"\n📊 Card 2 (Market) should display:")
print(f"   Main value: BULLISH (or BEARISH/NEUTRAL)")
print(f"   Subtitle: HIGH Vol | {session} Session")
print(f"            ^^^                ^^^")
print(f"   Not '0.172' -     Proper session name!")
print(f"   Should be text!")

print("\n" + "=" * 80)
print("ISSUES IDENTIFIED")
print("=" * 80)

print("""
❌ Problem 1: Session shows "New York" but it's actually "{}"
   Cause: data_manager may have stale data or wrong calculation
   Fix: Call market_analyzer.get_current_session() DIRECTLY

❌ Problem 2: Volatility shows "0.172" (a number)
   Cause: Displaying raw ATR value instead of status
   Fix: Calculate if ATR > 1.5x average → "HIGH", else "NORMAL"

❌ Problem 3: AI Action timeframe unclear
   Cause: Users think it's symbol/timeframe specific
   Fix: Add label: "AI Action (Account-Level)"

✅ Card 1 (Account): Appears correct if showing real MT5 balance
✅ Card 3 (Risk): Appears correct if showing real drawdown %
""".format(session))

print("\n" + "=" * 80)
print("SESSION TIME REFERENCE (GMT)")
print("=" * 80)
print("""
Asian:         00:00 - 08:00 GMT  (Quality: 3/10)
London:        08:00 - 13:00 GMT  (Quality: 8/10)  ← Current!
London/NY:     13:00 - 16:00 GMT  (Quality: 10/10) ← BEST
New York:      16:00 - 21:00 GMT  (Quality: 7/10)
Dead Zone:     21:00 - 00:00 GMT  (Quality: 0/10)
""")

print("\n" + "=" * 80)
print("AI ACTION CARD CLARIFICATION")
print("=" * 80)
print("""
The AI Action card is NOT timeframe-specific!

It analyzes:
  • Your account health (balance, P&L, drawdown)
  • Overall market conditions (trend, volatility)
  • Risk management state

Examples:
  • "STOP" = Account drawdown > 10% → stop all trading
  • "REDUCE" = Daily loss > $100 → reduce position sizes
  • "BUY DIP" = Bullish trend + high vol → look for longs
  • "WAIT" = No clear conditions → stay flat

For timeframe-specific signals, use:
  • Opportunity Scanner (shows M5/M15/H1/H4 setups)
  • Trade Validator (validates specific trade ideas)
  • Wyckoff Chart (analyzes price action on chosen TF)
""")

print("=" * 80)
