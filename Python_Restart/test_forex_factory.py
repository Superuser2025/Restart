#!/usr/bin/env python3
"""Test Forex Factory calendar scraping"""

import sys
sys.path.insert(0, '/home/user/Restart/Python_Restart/python')

from widgets.calendar_fetcher import calendar_fetcher

print("=" * 60)
print("TESTING FOREX FACTORY CALENDAR SCRAPER")
print("=" * 60)

# Test fetching events
print("\n📰 Fetching events from calendar sources...")
events = calendar_fetcher.fetch_events(days_ahead=7)

print(f"\n✓ Fetched {len(events)} events")

if events:
    print("\n📅 UPCOMING EVENTS:")
    print("-" * 60)
    for i, event in enumerate(events[:10], 1):  # Show first 10
        print(f"\n{i}. {event.event_name}")
        print(f"   Currency: {event.currency}")
        print(f"   Time: {event.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Impact: {event.impact_level.value}")
        print(f"   Avg Pip Impact: {event.avg_pip_impact}")
        if event.forecast:
            print(f"   Forecast: {event.forecast}")
        if event.previous:
            print(f"   Previous: {event.previous}")
else:
    print("\n⚠️ No events fetched")
    print("\nChecking MT5 availability...")
    print(f"MT5 Available: {calendar_fetcher.mt5_available}")

    print("\nTrying Forex Factory directly...")
    try:
        ff_events = calendar_fetcher._fetch_from_forex_factory(7)
        print(f"Forex Factory returned {len(ff_events)} events")
    except Exception as e:
        print(f"Forex Factory error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
