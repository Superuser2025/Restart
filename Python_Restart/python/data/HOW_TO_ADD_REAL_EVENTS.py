#!/usr/bin/env python3
"""
Economic Calendar - Add Real Events

This script helps you add REAL economic events to your calendar.

IMPORTANT: The news widget will NOT show fake sample data in live mode.
You must add real events manually to see news.

STEP 1: Get today's real events
-----------------------------------
Visit these websites to see what economic events are happening TODAY:

1. Forex Factory Calendar:
   https://www.forexfactory.com/calendar

2. Investing.com Calendar:
   https://www.investing.com/economic-calendar/

3. DailyFX Calendar:
   https://www.dailyfx.com/economic-calendar

4. FXStreet Calendar:
   https://www.fxstreet.com/economic-calendar


STEP 2: Add events to JSON file
-----------------------------------
Edit this file:
   /home/user/Restart/Python_Restart/python/data/economic_calendar.json

Format (copy the template):
{
  "events": [
    {
      "name": "US Non-Farm Payrolls",
      "currency": "USD",
      "timestamp": "2025-01-03T08:30:00",
      "forecast": 185.0,
      "previous": 180.0,
      "actual": null,
      "impact": "EXTREME",
      "avg_pip_impact": 150
    }
  ]
}

STEP 3: Convert times to ISO format
-----------------------------------
If event is at 8:30 AM today, format as:
   "2025-12-19T08:30:00"  (YYYY-MM-DDTHH:MM:SS)

If event is at 2:00 PM today:
   "2025-12-19T14:00:00"


EXAMPLE: Today's Events (December 19, 2025)
-----------------------------------
Check the calendar websites above to see what's actually scheduled for today.

Common weekly events:
- Monday: Nothing major
- Tuesday: Nothing major
- Wednesday: FOMC (if scheduled), PMI data
- Thursday: Unemployment Claims (USD), ECB (if scheduled)
- Friday: NFP (first Friday of month)


QUICK REFERENCE: Impact Levels
-----------------------------------
EXTREME (150+ pips):
  - US Non-Farm Payrolls (NFP)
  - FOMC Interest Rate Decision
  - ECB Interest Rate Decision
  - US CPI (inflation)

HIGH (80-150 pips):
  - GDP releases
  - Retail Sales
  - Employment data

MEDIUM (40-80 pips):
  - PMI data
  - Consumer Confidence
  - Trade Balance

LOW (< 40 pips):
  - Minor indicators


AUTOMATED SOLUTION (Future):
-----------------------------------
To automate this, you would need:
1. Paid API service (Trading Economics, Alpha Vantage)
2. Web scraping with anti-detection (unreliable)
3. MT5 calendar API (your version doesn't support it)

For now: Manual entry is most reliable for accurate data.
"""

print(__doc__)

print("\n" + "=" * 70)
print("CHECKING CALENDAR FILE STATUS")
print("=" * 70)

import os
calendar_file = "/home/user/Restart/Python_Restart/python/data/economic_calendar.json"

if os.path.exists(calendar_file):
    print(f"✓ Calendar file exists: {calendar_file}")
    import json
    with open(calendar_file, 'r') as f:
        data = json.load(f)
    print(f"✓ Contains {len(data.get('events', []))} events")
else:
    print(f"❌ Calendar file NOT found: {calendar_file}")
    print("\nTo create it:")
    print(f"  cp {calendar_file}.template {calendar_file}")
    print(f"  nano {calendar_file}")
