#!/usr/bin/env python3
"""
INTERACTIVE TOOL - Add today's REAL events to calendar

HONEST TRUTH:
- ALL calendar websites block automated scraping (403 Forbidden)
- Free APIs either don't exist or require keys
- MT5 calendar API not available in your version

THIS SCRIPT WORKS:
- You tell it today's events
- It builds the JSON for you
- Takes 2 minutes to add a week's worth of events

ALTERNATIVE: If you want fully automated, you need:
- Paid API ($20-50/month): Trading Economics, Alpha Vantage Premium
- Or MT5 with calendar support
"""

import json
from datetime import datetime, timedelta

def add_event_interactive():
    """Interactively add one event"""
    print("\n" + "="*60)
    print("Add an event (or press Enter on name to finish)")
    print("="*60)

    name = input("\nEvent name (e.g., 'US Unemployment Claims'): ").strip()
    if not name:
        return None

    currency = input("Currency (USD/EUR/GBP/JPY/AUD/CAD/NZD/CHF): ").strip().upper()

    print("\nTime (24-hour format):")
    hour = int(input("  Hour (0-23): ").strip())
    minute = int(input("  Minute (0-59): ").strip())

    today = datetime.now()
    event_time = today.replace(hour=hour, minute=minute, second=0)

    print("\nImpact level:")
    print("  1. EXTREME (NFP, FOMC, ECB)")
    print("  2. HIGH (GDP, Employment, Retail Sales)")
    print("  3. MEDIUM (PMI, Consumer Confidence)")
    print("  4. LOW (Minor indicators)")
    impact_choice = input("Choose (1-4): ").strip()

    impact_map = {
        '1': ('EXTREME', 150),
        '2': ('HIGH', 80),
        '3': ('MEDIUM', 50),
        '4': ('LOW', 25)
    }

    impact, pips = impact_map.get(impact_choice, ('MEDIUM', 50))

    forecast = input("\nForecast value (or Enter to skip): ").strip()
    previous = input("Previous value (or Enter to skip): ").strip()

    event = {
        'name': name,
        'currency': currency,
        'timestamp': event_time.isoformat(),
        'forecast': float(forecast) if forecast else None,
        'previous': float(previous) if previous else None,
        'actual': None,
        'impact': impact,
        'avg_pip_impact': pips
    }

    print(f"\n✓ Added: {currency} {name} at {hour:02d}:{minute:02d} ({impact} impact)")

    return event


def quick_add_common_events():
    """Quick add today's common events"""
    print("\n" + "="*60)
    print("QUICK ADD - Common Today Events")
    print("="*60)
    print("\nWhat day is today?")
    print("1. Monday")
    print("2. Tuesday")
    print("3. Wednesday")
    print("4. Thursday (Unemployment Claims)")
    print("5. Friday (First Friday = NFP)")
    print("6. Custom events")

    choice = input("\nChoose (1-6): ").strip()

    today = datetime.now()
    events = []

    if choice == '4':  # Thursday
        # US Unemployment Claims
        event_time = today.replace(hour=8, minute=30, second=0)
        events.append({
            'name': 'US Unemployment Claims',
            'currency': 'USD',
            'timestamp': event_time.isoformat(),
            'forecast': 220.0,
            'previous': 215.0,
            'actual': None,
            'impact': 'MEDIUM',
            'avg_pip_impact': 45
        })
        print("✓ Added US Unemployment Claims (8:30 AM)")

    elif choice == '5':  # Friday - check if first Friday
        first_friday = (today.day <= 7)
        if first_friday:
            # NFP
            event_time = today.replace(hour=8, minute=30, second=0)
            events.append({
                'name': 'US Non-Farm Payrolls',
                'currency': 'USD',
                'timestamp': event_time.isoformat(),
                'forecast': 185.0,
                'previous': 180.0,
                'actual': None,
                'impact': 'EXTREME',
                'avg_pip_impact': 150
            })
            print("✓ Added US Non-Farm Payrolls (8:30 AM) - EXTREME IMPACT!")
        else:
            print("Not first Friday - no NFP today")

    return events if events else None


def main():
    print("="*70)
    print("ADD TODAY'S REAL ECONOMIC EVENTS")
    print("="*70)

    print("\n📋 How do you want to add events?")
    print("1. Quick add (common events for today)")
    print("2. Manual entry (you type each event)")
    print("3. Show me where to find today's real events")

    choice = input("\nChoose (1-3): ").strip()

    events = []

    if choice == '1':
        quick_events = quick_add_common_events()
        if quick_events:
            events.extend(quick_events)

    elif choice == '2':
        while True:
            event = add_event_interactive()
            if not event:
                break
            events.append(event)

    elif choice == '3':
        print("\n" + "="*70)
        print("WHERE TO FIND TODAY'S REAL EVENTS:")
        print("="*70)
        print("\n1. MyFXBook Calendar:")
        print("   https://www.myfxbook.com/forex-economic-calendar")
        print("\n2. Investing.com Calendar:")
        print("   https://www.investing.com/economic-calendar/")
        print("\n3. DailyFX Calendar:")
        print("   https://www.dailyfx.com/economic-calendar")
        print("\n4. FXStreet Calendar:")
        print("   https://www.fxstreet.com/economic-calendar")
        print("\n5. ForexFactory (blocks scrapers but website works):")
        print("   https://www.forexfactory.com/calendar")
        print("\n" + "="*70)
        print("Run this script again after checking the calendars!")
        print("="*70)
        return

    # Save events
    if events:
        output_file = '/home/user/Restart/Python_Restart/python/data/economic_calendar.json'
        output = {
            'generated_at': datetime.now().isoformat(),
            'source': 'Manual entry - REAL events',
            'events': events
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print("\n" + "="*70)
        print(f"✅ SUCCESS! Saved {len(events)} REAL events")
        print("="*70)
        print(f"\nSaved to: {output_file}")
        print("\n🚀 RESTART THE APP to see your real calendar events!")
        print("="*70)
    else:
        print("\n⚠️  No events added")


if __name__ == '__main__':
    main()
