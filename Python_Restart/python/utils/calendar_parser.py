#!/usr/bin/env python3
"""
Economic Calendar Parser - Convert pasted calendar data to JSON

Parses the format from Investing.com or similar calendar sites
"""

from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Optional
from html.parser import HTMLParser


class TableExtractor(HTMLParser):
    """Extract data from HTML tables"""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.current_data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif tag in ['td', 'th']:
            self.in_cell = True
            self.current_data = []

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False
            self.current_row = []
        elif tag in ['td', 'th']:
            if self.in_cell:
                cell_text = ''.join(self.current_data).strip()
                self.current_row.append(cell_text)
            self.in_cell = False
            self.current_data = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_data.append(data)


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
        self.current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        print(f"\n🔍 Analyzing calendar data ({len(text)} chars)...")

        # Check if it's HTML
        if '<table' in text.lower() or '<tr' in text.lower():
            print("📊 Detected HTML table - using HTML parser...")
            return self._parse_html_table(text)
        else:
            print("📝 No HTML detected - using text parser...")
            return self._parse_text(text)

    def _parse_html_table(self, html: str) -> List[Dict]:
        """Parse HTML table format"""
        # Extract table data
        extractor = TableExtractor()
        extractor.feed(html)

        print(f"📋 Extracted {len(extractor.rows)} rows from HTML")

        # Show first 5 rows for debugging
        print("\n📊 SHOWING FIRST 5 ROWS:")
        for i, row in enumerate(extractor.rows[:5]):
            print(f"  Row {i}: {len(row)} cells")
            for j, cell in enumerate(row):
                print(f"    Cell {j}: '{cell[:50]}'")
        print()

        # Process each row
        for i, row in enumerate(extractor.rows):
            if len(row) < 3:
                print(f"  ⊘ Row {i}: Only {len(row)} cells - skipping")
                continue

            # Try to parse as event - Investing.com format: [Time, Currency, Event, Actual, Forecast, Previous]
            event = self._parse_table_row(row, i)
            if event:
                self.events.append(event)
                print(f"  ✓ Event {len(self.events)}: {event['currency']} {event['name'][:40]}")
            else:
                if i < 10:  # Show why first 10 failed
                    print(f"  ⊘ Row {i}: Failed to parse - {row[:3]}")

        print(f"\n✅ Parsed {len(self.events)} events from HTML table")
        return self.events

    def _parse_table_row(self, cells: List[str], row_num: int = 0) -> Optional[Dict]:
        """Parse a table row into an event"""
        try:
            # Investing.com table format variations:
            # [Time, Currency/Flag, Event, Actual, Forecast, Previous]
            # OR: [Date, Time, Currency, Event, Impact, Actual, Forecast, Previous]

            # Find time (contains : or AM/PM)
            time_idx = -1
            for i, cell in enumerate(cells):
                if ':' in cell or 'AM' in cell.upper() or 'PM' in cell.upper():
                    time_idx = i
                    break

            if time_idx == -1:
                print(f"    Row {row_num}: No time found in cells: {[c[:20] for c in cells[:5]]}")
                return None

            # Find currency/country code (2-3 letter codes)
            currency_idx = -1
            for i in range(time_idx + 1, min(time_idx + 3, len(cells))):
                cell = cells[i].strip().upper()
                if len(cell) == 2 or len(cell) == 3:
                    if cell in self.COUNTRY_TO_CURRENCY or cell in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'NZD', 'CHF']:
                        currency_idx = i
                        break

            if currency_idx == -1:
                return None

            # Event name is next after currency
            event_idx = currency_idx + 1
            if event_idx >= len(cells):
                return None

            time_str = cells[time_idx].strip()
            country = cells[currency_idx].strip().upper()
            event_name = cells[event_idx].strip()

            if not event_name:
                return None

            # Parse time
            event_time = self._parse_time(time_str)
            if not event_time:
                return None

            # Use current or next date
            timestamp = self.current_date.replace(
                hour=event_time.hour,
                minute=event_time.minute
            )

            # If time is in the past, assume it's tomorrow
            if timestamp < datetime.now():
                timestamp += timedelta(days=1)

            # Get forecast and previous values
            actual = None
            forecast = None
            previous = None

            # Try to find numeric values in remaining cells
            for i in range(event_idx + 1, len(cells)):
                val = self._parse_numeric(cells[i])
                if val is not None:
                    if actual is None:
                        actual = val
                    elif forecast is None:
                        forecast = val
                    elif previous is None:
                        previous = val
                        break

            # Determine impact level
            impact, pips = self._determine_impact(event_name, country)

            # Get currency
            if country in self.COUNTRY_TO_CURRENCY:
                currency = self.COUNTRY_TO_CURRENCY[country]
            else:
                currency = country if len(country) == 3 else 'USD'

            # Only include major currencies
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'NZD', 'CHF']
            if currency not in major_currencies:
                return None

            return {
                'name': event_name,
                'currency': currency,
                'timestamp': timestamp.isoformat(),
                'forecast': forecast,
                'previous': previous,
                'actual': actual,
                'impact': impact,
                'avg_pip_impact': pips
            }

        except Exception as e:
            print(f"  ⊗ Error parsing row: {e}")
            return None

    def _parse_numeric(self, text: str) -> Optional[float]:
        """Parse numeric value from text"""
        if not text or text.strip() in ['', '-', 'N/A', 'n/a']:
            return None
        try:
            # Remove % and other symbols
            cleaned = re.sub(r'[%KMB]', '', text.strip())
            cleaned = re.sub(r'[^\d.-]', '', cleaned)
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None

    def _parse_text(self, text: str) -> List[Dict]:
        """Parse text format (Investing.com copy/paste)"""
        lines = text.strip().split('\n')

        print(f"📝 Parsing {len(lines)} lines of text data...")
        parsed_count = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if it's a date header: "Thursday, January 1, 2026"
            if self._is_date_header_investing(line):
                self.current_date = self._parse_date_header_investing(line)
                if self.current_date:
                    print(f"📅 Found date: {self.current_date.strftime('%Y-%m-%d')}")
                continue

            # Skip holiday lines
            if 'Holiday' in line or 'All Day' in line:
                continue

            # Try to parse as event (Investing.com format)
            event = self._parse_investing_line(line)
            if event:
                self.events.append(event)
                parsed_count += 1
                print(f"  ✓ Event {parsed_count}: {event['currency']} {event['name'][:40]}...")

        print(f"\n✅ Parsed {parsed_count} events from text")
        return self.events

    def _is_date_header_investing(self, line: str) -> bool:
        """Check if line is Investing.com date header: 'Thursday, January 1, 2026'"""
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Must have a day name and month name
        has_day = any(day in line for day in days)
        has_month = any(month in line for month in months)
        has_year = any(year in line for year in ['2025', '2026', '2027', '2028'])

        return has_day and has_month and has_year

    def _parse_date_header_investing(self, line: str) -> Optional[datetime]:
        """Parse Investing.com date header: 'Thursday, January 1, 2026'"""
        try:
            # Remove day of week: "Thursday, January 1, 2026" -> "January 1, 2026"
            parts = line.split(',', 1)
            if len(parts) == 2:
                date_str = parts[1].strip()
                # Parse "January 1, 2026"
                return datetime.strptime(date_str, "%B %d, %Y")
        except:
            pass
        return None

    def _parse_investing_line(self, line: str) -> Optional[Dict]:
        """Parse Investing.com event line: '08:45  USD  S&P Global Manufacturing PMI (Dec)  51.8'"""
        if not self.current_date:
            return None

        # Split by tabs
        parts = [p.strip() for p in line.split('\t') if p.strip()]

        if len(parts) < 3:
            return None

        try:
            # First part should be time: "08:45" or "01:00"
            time_str = parts[0]
            if not re.match(r'\d{1,2}:\d{2}', time_str):
                return None

            # Second part should be 3-letter currency code: USD, EUR, GBP, etc.
            currency = parts[1].strip().upper()
            if len(currency) != 3:
                return None

            # Only major currencies
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'NZD', 'CHF', 'RUB', 'BRL', 'INR', 'HKD', 'SGD']
            if currency not in major_currencies:
                return None

            # Find event name (first non-empty text after currency)
            event_name = None
            event_idx = -1
            for i in range(2, len(parts)):
                if parts[i] and not self._is_numeric_value(parts[i]):
                    event_name = parts[i]
                    event_idx = i
                    break

            if not event_name:
                return None

            # Parse time (24-hour format)
            hour, minute = map(int, time_str.split(':'))
            timestamp = self.current_date.replace(hour=hour, minute=minute)

            # If time is in the past, assume it's for next occurrence
            if timestamp < datetime.now():
                # Check if it's more than 12 hours in the past, then add a day
                if (datetime.now() - timestamp).total_seconds() > 43200:
                    timestamp += timedelta(days=1)

            # Get numeric values (actual, forecast, previous)
            actual = None
            forecast = None
            previous = None

            numeric_values = []
            for i in range(event_idx + 1, len(parts)):
                val = self._parse_numeric(parts[i])
                if val is not None:
                    numeric_values.append(val)

            # Assign values: last value is usually Previous, second-to-last is Forecast
            if len(numeric_values) >= 1:
                previous = numeric_values[-1]
            if len(numeric_values) >= 2:
                forecast = numeric_values[-2]
            if len(numeric_values) >= 3:
                actual = numeric_values[-3]

            # Determine impact level
            impact, pips = self._determine_impact(event_name, currency)

            return {
                'name': event_name,
                'currency': currency,
                'timestamp': timestamp.isoformat(),
                'forecast': forecast,
                'previous': previous,
                'actual': actual,
                'impact': impact,
                'avg_pip_impact': pips
            }

        except Exception as e:
            print(f"  ⊗ Error parsing line: {e} - {line[:60]}")
            return None

    def _is_numeric_value(self, text: str) -> bool:
        """Check if text looks like a numeric value"""
        if not text:
            return False
        # Check for numbers, %, -, decimals, K, M, B suffixes
        return bool(re.search(r'[\d.%KMB-]', text))

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and convert table structure to text"""
        # If it's HTML table, convert to tab-delimited format
        if '<table' in text.lower() or '<tr' in text.lower():
            print("📊 Detected HTML table - converting to tab-delimited format...")

            # Replace table row endings with newlines
            text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)

            # Replace table cell endings with tabs
            text = re.sub(r'</td>', '\t', text, flags=re.IGNORECASE)
            text = re.sub(r'</th>', '\t', text, flags=re.IGNORECASE)

            # Remove all remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)
        else:
            # Just remove HTML tags
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
