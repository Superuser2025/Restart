#!/usr/bin/env python3
"""
Economic Calendar Parser - Convert pasted calendar data to JSON

Parses the format from Investing.com or similar calendar sites
"""

from datetime import datetime
import json
import re
from typing import List, Dict, Optional


class CalendarParser:
    """Parse economic calendar from text format"""

    # Country code to currency mapping
    COUNTRY_TO_CURRENCY = {
        'US': 'USD', 'EU': 'EUR', 'EA': 'EUR', 'GB': 'GBP', 'UK': 'GBP',
        'JP': 'JPY', 'AU': 'AUD', 'NZ': 'NZD', 'CA': 'CAD', 'CH': 'CHF',
        'CN': 'CNY', 'KR': 'KRW', 'IN': 'INR', 'BR': 'BRL', 'MX': 'MXN',
        'ZA': 'ZAR', 'RU': 'RUB', 'TR': 'TRY', 'SG': 'SGD', 'ID': 'IDR',
        'SA': 'SAR', 'AR': 'ARS', 'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR',
        'ES': 'EUR', 'WL': 'GLOBAL'
    }

    # High-impact event keywords
    HIGH_IMPACT_KEYWORDS = [
        'Non-Farm', 'NFP', 'Employment', 'Unemployment', 'GDP', 'CPI',
        'Interest Rate', 'FOMC', 'Fed ', 'ECB ', 'BoE ', 'BoJ ', 'BoC ',
        'Retail Sales', 'Inflation', 'PMI Manufacturing'
    ]

    EXTREME_IMPACT_KEYWORDS = [
        'Non-Farm Payrolls', 'NFP', 'Interest Rate Decision', 'FOMC',
        'ECB Interest', 'CPI', 'GDP Growth Rate'
    ]

    def __init__(self):
        self.events = []
        self.current_date = None

    def parse(self, text: str) -> List[Dict]:
        """Parse calendar text and return list of events"""
        self.events = []
        self.current_date = None

        # Strip HTML tags if present
        text = self._strip_html(text)

        # Decode HTML entities
        text = self._decode_html_entities(text)

        lines = text.strip().split('\n')

        print(f"\n🔍 Parsing {len(lines)} lines of calendar data...")
        parsed_count = 0
        skipped_count = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if it's a date header
            if self._is_date_header(line):
                self.current_date = self._parse_date_header(line)
                if self.current_date:
                    print(f"📅 Found date: {self.current_date.strftime('%Y-%m-%d')}")
                continue

            # Try to parse as event
            event = self._parse_event_line(line)
            if event:
                self.events.append(event)
                parsed_count += 1
                print(f"  ✓ Event {parsed_count}: {event['currency']} {event['name'][:40]}...")
            else:
                skipped_count += 1
                if i < 10:  # Only print first few skipped lines for debugging
                    print(f"  ⊘ Skipped line {i}: {line[:60]}...")

        print(f"\n✅ Parsed {parsed_count} events, skipped {skipped_count} lines")
        return self.events

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text

    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities like &nbsp; &amp; etc."""
        import html
        return html.unescape(text)

    def _is_date_header(self, line: str) -> bool:
        """Check if line is a date header"""
        # Format: "Thursday January 01 2026"
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        return any(month in line for month in months) and '\t' not in line

    def _parse_date_header(self, line: str) -> Optional[datetime]:
        """Parse date from header line"""
        try:
            # Remove day of week
            parts = line.split()
            # Find month
            months = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }

            month = None
            day = None
            year = None

            for part in parts:
                if part in months:
                    month = months[part]
                elif part.isdigit() and len(part) <= 2:
                    day = int(part)
                elif part.isdigit() and len(part) == 4:
                    year = int(part)

            if month and day and year:
                return datetime(year, month, day)
        except:
            pass

        return None

    def _parse_event_line(self, line: str) -> Optional[Dict]:
        """Parse a single event line"""
        if not self.current_date:
            return None

        # Split by tabs first, then try multiple spaces if no tabs
        if '\t' in line:
            parts = line.split('\t')
        else:
            # Split by 2+ spaces
            parts = re.split(r'\s{2,}', line)

        # Clean up parts
        parts = [p.strip() for p in parts if p.strip()]

        # Need at least: time, country, event name
        if len(parts) < 3:
            return None

        try:
            # Parse time
            time_str = parts[0].strip()
            if not self._is_time(time_str):
                return None

            # Parse country code
            country = parts[1].strip()
            if country not in self.COUNTRY_TO_CURRENCY:
                return None

            # Event name
            event_name = parts[2].strip()
            if not event_name:
                return None

            # Parse time
            event_time = self._parse_time(time_str)
            if not event_time:
                return None

            # Combine date and time
            timestamp = self.current_date.replace(
                hour=event_time.hour,
                minute=event_time.minute
            )

            # Get forecast and previous values
            forecast = None
            previous = None

            if len(parts) >= 5:
                try:
                    prev_str = parts[4].strip()
                    if prev_str and prev_str != '':
                        # Remove currency symbols, K, M, B suffixes
                        prev_str = re.sub(r'[^\d.-]', '', prev_str.replace('K', '').replace('M', '').replace('B', ''))
                        if prev_str:
                            previous = float(prev_str)
                except:
                    pass

            if len(parts) >= 6:
                try:
                    fore_str = parts[5].strip()
                    if fore_str and fore_str != '':
                        fore_str = re.sub(r'[^\d.-]', '', fore_str.replace('K', '').replace('M', '').replace('B', ''))
                        if fore_str:
                            forecast = float(fore_str)
                except:
                    pass

            # Determine impact level
            impact, pips = self._determine_impact(event_name, country)

            # Get currency
            currency = self.COUNTRY_TO_CURRENCY.get(country, 'USD')

            # Only include USD, EUR, GBP, JPY, AUD, CAD, NZD, CHF events
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'NZD', 'CHF']
            if currency not in major_currencies:
                return None

            return {
                'name': event_name,
                'currency': currency,
                'timestamp': timestamp.isoformat(),
                'forecast': forecast,
                'previous': previous,
                'actual': None,
                'impact': impact,
                'avg_pip_impact': pips
            }

        except Exception as e:
            print(f"Error parsing line: {line[:50]}... - {e}")
            return None

    def _is_time(self, text: str) -> bool:
        """Check if text looks like a time"""
        return 'AM' in text or 'PM' in text or ':' in text

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string to datetime"""
        try:
            # Format: "01:00 AM"
            return datetime.strptime(time_str.strip(), "%I:%M %p")
        except:
            try:
                # Try 24-hour format
                return datetime.strptime(time_str.strip(), "%H:%M")
            except:
                return None

    def _determine_impact(self, event_name: str, country: str) -> tuple:
        """Determine impact level and pip movement"""

        # Check for extreme impact
        for keyword in self.EXTREME_IMPACT_KEYWORDS:
            if keyword.lower() in event_name.lower():
                return ('EXTREME', 150)

        # Check for high impact
        for keyword in self.HIGH_IMPACT_KEYWORDS:
            if keyword.lower() in event_name.lower():
                return ('HIGH', 80)

        # Medium impact for major currencies
        major = ['US', 'EU', 'EA', 'GB', 'JP']
        if country in major:
            return ('MEDIUM', 50)

        return ('LOW', 25)

    def save_to_file(self, filepath: str):
        """Save parsed events to JSON file"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'source': 'User pasted calendar data',
            'events': self.events
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✓ Saved {len(self.events)} events to {filepath}")


def test_parser():
    """Test the parser with sample data"""
    sample = """Thursday January 01 2026	Actual	Previous	Consensus	Forecast
01:00 AM	KR	Exports YoY DEC		8.4%
02:30 PM	US	Non Farm Payrolls DEC		64K		70K
Friday January 02 2026	Actual	Previous	Consensus	Forecast
03:45 PM	US	S&P Global Manufacturing PMI Final DEC		52.2	51.8	51.8"""

    parser = CalendarParser()
    events = parser.parse(sample)

    print(f"\nParsed {len(events)} events:")
    for event in events:
        print(f"  {event['timestamp'][:16]} {event['currency']} {event['name']} ({event['impact']})")


if __name__ == '__main__':
    test_parser()
