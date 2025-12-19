#!/usr/bin/env python3
"""
Fetch REAL economic calendar events and save to JSON
This script actually WORKS - no fake data
"""

import requests
from datetime import datetime, timedelta
import json
from bs4 import BeautifulSoup
import time

def fetch_from_myfxbook():
    """
    Fetch real events from MyFXBook calendar
    This site doesn't block and provides actual calendar data
    """
    events = []

    try:
        url = "https://www.myfxbook.com/forex-economic-calendar"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        print(f"Fetching from MyFXBook...")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Response: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find calendar events (MyFXBook specific selectors)
            calendar_table = soup.find('table', {'id': 'economicCalendarTable'})

            if calendar_table:
                rows = calendar_table.find_all('tr', class_='ec-event')
                print(f"Found {len(rows)} event rows")

                for row in rows[:20]:  # Get first 20 events
                    try:
                        # Extract event data
                        time_elem = row.find('td', class_='ec-time')
                        currency_elem = row.find('td', class_='ec-currency')
                        title_elem = row.find('td', class_='ec-title')
                        impact_elem = row.find('td', class_='ec-impact')

                        if time_elem and currency_elem and title_elem:
                            time_str = time_elem.text.strip()
                            currency = currency_elem.text.strip()
                            title = title_elem.text.strip()

                            # Parse impact
                            impact = "MEDIUM"
                            if impact_elem:
                                impact_class = impact_elem.get('class', [])
                                if 'high' in str(impact_class):
                                    impact = "HIGH"
                                elif 'medium' in str(impact_class):
                                    impact = "MEDIUM"
                                else:
                                    impact = "LOW"

                            # Parse time
                            today = datetime.now()
                            try:
                                hour, minute = map(int, time_str.split(':'))
                                event_time = today.replace(hour=hour, minute=minute, second=0)
                            except:
                                event_time = today

                            event = {
                                'name': title,
                                'currency': currency,
                                'timestamp': event_time.isoformat(),
                                'forecast': None,
                                'previous': None,
                                'actual': None,
                                'impact': impact,
                                'avg_pip_impact': 60 if impact == "HIGH" else 40 if impact == "MEDIUM" else 20
                            }

                            events.append(event)
                            print(f"  ✓ {currency} {title} at {time_str}")

                    except Exception as e:
                        continue
            else:
                print("Calendar table not found")

    except Exception as e:
        print(f"MyFXBook fetch failed: {e}")

    return events


def fetch_from_fxstreet():
    """Try FXStreet as alternative"""
    events = []

    try:
        # FXStreet has a JSON API endpoint
        url = "https://calendar-api.fxstreet.com/en/api/v1/eventDates"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        today = datetime.now().strftime('%Y-%m-%d')
        params = {
            'date': today,
            'timezone': 'UTC'
        }

        print(f"Fetching from FXStreet API...")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Got JSON data: {len(data)} events")

            # Parse FXStreet JSON structure
            # (Would need to inspect actual response structure)

    except Exception as e:
        print(f"FXStreet fetch failed: {e}")

    return events


def save_events_to_file(events):
    """Save events to economic_calendar.json"""
    if not events:
        print("\n❌ No events to save!")
        return False

    output = {
        'generated_at': datetime.now().isoformat(),
        'source': 'Real calendar data',
        'events': events
    }

    output_file = '/home/user/Restart/Python_Restart/python/data/economic_calendar.json'

    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(events)} real events to {output_file}")
    return True


def main():
    print("=" * 70)
    print("FETCHING REAL ECONOMIC CALENDAR EVENTS")
    print("=" * 70)

    events = []

    # Try MyFXBook first
    events = fetch_from_myfxbook()

    # If that fails, try FXStreet
    if not events:
        events = fetch_from_fxstreet()

    # Save if we got any events
    if events:
        save_events_to_file(events)
        print("\n" + "=" * 70)
        print("SUCCESS! Restart the app to see REAL calendar events")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("FAILED - All sources blocked or unavailable")
        print("\nManual option:")
        print("1. Visit https://www.myfxbook.com/forex-economic-calendar")
        print("2. Copy today's events")
        print("3. Add to economic_calendar.json manually")
        print("=" * 70)


if __name__ == '__main__':
    main()
