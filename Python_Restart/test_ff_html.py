#!/usr/bin/env python3
"""Debug Forex Factory HTML structure"""

import requests
from bs4 import BeautifulSoup

print("=" * 80)
print("FOREX FACTORY HTML STRUCTURE TEST")
print("=" * 80)

url = "https://www.forexfactory.com/calendar"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print(f"\n📡 Fetching: {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"\n✓ Response Code: {response.status_code}")
    print(f"✓ Content Length: {len(response.content)} bytes")

    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # Try different selectors
    print("\n" + "=" * 80)
    print("TESTING DIFFERENT SELECTORS")
    print("=" * 80)

    # Original selector
    calendar_rows = soup.find_all('tr', class_='calendar__row')
    print(f"\n1. tr.calendar__row: {len(calendar_rows)} found")

    # Alternative selectors
    all_trs = soup.find_all('tr')
    print(f"2. All <tr> tags: {len(all_trs)} found")

    # Check for table
    tables = soup.find_all('table')
    print(f"3. All <table> tags: {len(tables)} found")

    # Check for calendar div
    calendar_divs = soup.find_all('div', class_='calendar')
    print(f"4. div.calendar: {len(calendar_divs)} found")

    # Check page title
    title = soup.find('title')
    print(f"\n📄 Page Title: {title.text if title else 'N/A'}")

    # Save a sample of the HTML for inspection
    html_sample = str(soup)[:5000]  # First 5000 chars
    print(f"\n📝 HTML Sample (first 5000 chars):")
    print("-" * 80)
    print(html_sample)
    print("-" * 80)

    # Check if we got redirected or blocked
    if 'cloudflare' in html_sample.lower() or 'captcha' in html_sample.lower():
        print("\n⚠️ WARNING: Page appears to be protected by Cloudflare/CAPTCHA")

    # Look for calendar-specific elements
    calendar_table = soup.find('table', class_='calendar__table')
    if calendar_table:
        print(f"\n✓ Found calendar__table!")
        rows = calendar_table.find_all('tr')
        print(f"  Rows in table: {len(rows)}")
    else:
        print(f"\n❌ No calendar__table found")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
