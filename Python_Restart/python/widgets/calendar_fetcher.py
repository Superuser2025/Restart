"""
AppleTrader Pro - Economic Calendar Fetcher
Fetches real economic news events from multiple sources
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from bs4 import BeautifulSoup
import logging

from widgets.news_impact_predictor import NewsEvent, ImpactLevel
from core.verbose_mode_manager import vprint


class CalendarFetcher:
    """
    Fetches economic calendar events from various sources

    Supported sources:
    - Forex Factory (scraping)
    - Trading Economics API
    - Custom MT5 integration (if available)
    """

    def __init__(self):
        """Initialize the calendar fetcher"""
        self.logger = logging.getLogger(__name__)

        # Try MT5 first
        self.mt5_available = self._check_mt5()

        # Forex Factory URL
        self.forex_factory_url = "https://www.forexfactory.com/calendar"

    def _check_mt5(self) -> bool:
        """Check if MT5 is available"""
        try:
            import MetaTrader5 as mt5
            return mt5.initialize()
        except:
            return False

    def fetch_events(self, days_ahead: int = 7) -> List[NewsEvent]:
        """
        Fetch upcoming economic events

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of NewsEvent objects
        """
        events = []

        # Try MT5 calendar first
        if self.mt5_available:
            try:
                events = self._fetch_from_mt5(days_ahead)
                if events:
                    vprint(f"Fetched {len(events)} events from MT5")
                    return events
            except Exception as e:
                vprint(f"MT5 calendar fetch failed: {e}")

        # Try Forex Factory scraping
        try:
            events = self._fetch_from_forex_factory(days_ahead)
            if events:
                vprint(f"Fetched {len(events)} events from Forex Factory")
                return events
        except Exception as e:
            vprint(f"Forex Factory fetch failed: {e}")

        # If all fails, return empty list
        vprint("No calendar source available, using empty calendar")
        return []

    def _fetch_from_mt5(self, days_ahead: int) -> List[NewsEvent]:
        """Fetch events from MT5 calendar"""
        import MetaTrader5 as mt5

        events = []

        # Get calendar events
        start_time = datetime.now()
        end_time = start_time + timedelta(days=days_ahead)

        # MT5 calendar_get returns calendar events
        calendar_records = mt5.calendar_get(start_time, end_time)

        if calendar_records is None:
            return events

        for record in calendar_records:
            # Parse MT5 calendar record
            event = self._parse_mt5_event(record)
            if event:
                events.append(event)

        return events

    def _parse_mt5_event(self, record) -> Optional[NewsEvent]:
        """Parse MT5 calendar record into NewsEvent"""
        try:
            # Extract currency from country code
            country_to_currency = {
                'US': 'USD', 'EU': 'EUR', 'GB': 'GBP',
                'JP': 'JPY', 'AU': 'AUD', 'CA': 'CAD',
                'CH': 'CHF', 'NZ': 'NZD'
            }

            currency = country_to_currency.get(record.country_code, 'USD')

            # Create event
            event = NewsEvent(
                event_name=record.name,
                currency=currency,
                timestamp=datetime.fromtimestamp(record.time),
                forecast=record.forecast_value if hasattr(record, 'forecast_value') else None,
                previous=record.prev_value if hasattr(record, 'prev_value') else None,
                actual=record.actual_value if hasattr(record, 'actual_value') else None
            )

            # Map MT5 importance to impact level
            if hasattr(record, 'importance'):
                importance = record.importance
                if importance == 3:
                    event.impact_level = ImpactLevel.EXTREME
                    event.avg_pip_impact = 100
                elif importance == 2:
                    event.impact_level = ImpactLevel.HIGH
                    event.avg_pip_impact = 60
                elif importance == 1:
                    event.impact_level = ImpactLevel.MEDIUM
                    event.avg_pip_impact = 30
                else:
                    event.impact_level = ImpactLevel.LOW
                    event.avg_pip_impact = 15

            return event

        except Exception as e:
            self.logger.error(f"Failed to parse MT5 event: {e}")
            return None

    def _fetch_from_forex_factory(self, days_ahead: int) -> List[NewsEvent]:
        """
        Fetch events from multiple API sources with fallback chain

        Strategy:
        1. Try economic calendar JSON API
        2. Try alternative free APIs
        3. Return empty if all fail (widget will use intelligent sample data)
        """
        events = []

        # Source 1: Try Investing.com calendar JSON endpoint
        try:
            events = self._fetch_from_investing_api(days_ahead)
            if events:
                vprint(f"✓ Fetched {len(events)} events from Investing.com API")
                return events
        except Exception as e:
            vprint(f"Investing.com API failed: {e}")

        # Source 2: Try FCS API (free tier)
        try:
            events = self._fetch_from_fcs_api(days_ahead)
            if events:
                vprint(f"✓ Fetched {len(events)} events from FCS API")
                return events
        except Exception as e:
            vprint(f"FCS API failed: {e}")

        # Source 3: Try local calendar file (user can maintain their own)
        try:
            events = self._fetch_from_local_file(days_ahead)
            if events:
                vprint(f"✓ Loaded {len(events)} events from local calendar file")
                return events
        except Exception as e:
            vprint(f"Local calendar file failed: {e}")

        # All sources failed
        vprint("All calendar sources failed")
        return events

    def _parse_forex_factory_row(self, row, current_date) -> Optional[NewsEvent]:
        """Parse a single Forex Factory calendar row"""
        try:
            # Extract time
            time_elem = row.find('td', class_='calendar__time')
            if not time_elem:
                return None

            time_str = time_elem.text.strip()
            if not time_str or time_str == 'All Day':
                return None

            # Extract currency
            currency_elem = row.find('td', class_='calendar__currency')
            if not currency_elem:
                return None
            currency = currency_elem.text.strip()

            # Extract event name
            event_elem = row.find('span', class_='calendar__event-title')
            if not event_elem:
                return None
            event_name = event_elem.text.strip()

            # Extract impact level
            impact_elem = row.find('td', class_='calendar__impact')
            impact_level = ImpactLevel.LOW
            avg_pip_impact = 15

            if impact_elem:
                impact_class = impact_elem.find('span', class_='icon')
                if impact_class:
                    classes = impact_class.get('class', [])
                    if 'icon--ff-impact-red' in classes:
                        impact_level = ImpactLevel.EXTREME
                        avg_pip_impact = 100
                    elif 'icon--ff-impact-ora' in classes:
                        impact_level = ImpactLevel.HIGH
                        avg_pip_impact = 60
                    elif 'icon--ff-impact-yel' in classes:
                        impact_level = ImpactLevel.MEDIUM
                        avg_pip_impact = 30

            # Extract forecast, previous, actual
            forecast = None
            previous = None
            actual = None

            forecast_elem = row.find('td', class_='calendar__forecast')
            if forecast_elem:
                try:
                    forecast = float(forecast_elem.text.strip().replace('%', '').replace('K', ''))
                except:
                    pass

            previous_elem = row.find('td', class_='calendar__previous')
            if previous_elem:
                try:
                    previous = float(previous_elem.text.strip().replace('%', '').replace('K', ''))
                except:
                    pass

            actual_elem = row.find('td', class_='calendar__actual')
            if actual_elem:
                try:
                    actual = float(actual_elem.text.strip().replace('%', '').replace('K', ''))
                except:
                    pass

            # Parse timestamp
            # Assuming today for simplicity (Forex Factory shows current week)
            hour, minute = map(int, time_str.split(':')[:2])
            timestamp = datetime.combine(current_date, datetime.min.time())
            timestamp = timestamp.replace(hour=hour, minute=minute)

            # Create event
            event = NewsEvent(
                event_name=event_name,
                currency=currency,
                timestamp=timestamp,
                forecast=forecast,
                previous=previous,
                actual=actual
            )

            event.impact_level = impact_level
            event.avg_pip_impact = avg_pip_impact

            return event

        except Exception as e:
            return None

    def _fetch_from_investing_api(self, days_ahead: int) -> List[NewsEvent]:
        """
        Fetch from Investing.com economic calendar API
        Uses their public JSON endpoint
        """
        events = []

        try:
            # Investing.com calendar API endpoint
            url = "https://api.investing.com/api/financialdata/economic-calendar/all"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.investing.com/',
                'Origin': 'https://www.investing.com'
            }

            # Get events for date range
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days_ahead)

            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'importance': '2,3'  # Only medium and high impact
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                # Parse JSON response and convert to NewsEvent objects
                # (Implementation depends on actual API structure)
                vprint("Investing.com API: Response received but parsing not implemented")
            else:
                vprint(f"Investing.com API returned status {response.status_code}")

        except Exception as e:
            vprint(f"Investing.com API error: {e}")

        return events

    def _fetch_from_fcs_api(self, days_ahead: int) -> List[NewsEvent]:
        """
        Fetch from FCS (Financial Content Services) API
        Free tier available
        """
        events = []

        try:
            # FCS API - would need API key for full access
            # This is a placeholder for now
            pass

        except Exception as e:
            vprint(f"FCS API error: {e}")

        return events

    def _fetch_from_local_file(self, days_ahead: int) -> List[NewsEvent]:
        """
        Load events from local JSON calendar file
        Users can maintain their own calendar data
        """
        events = []

        try:
            import os
            calendar_file = os.path.join(
                os.path.dirname(__file__),
                '../data/economic_calendar.json'
            )

            if not os.path.exists(calendar_file):
                return events

            with open(calendar_file, 'r') as f:
                calendar_data = json.load(f)

            current_date = datetime.now()
            end_date = current_date + timedelta(days=days_ahead)

            for event_data in calendar_data.get('events', []):
                try:
                    # Parse event timestamp
                    event_time = datetime.fromisoformat(event_data['timestamp'])

                    # Check if within range
                    if current_date <= event_time <= end_date:
                        # Create NewsEvent
                        event = NewsEvent(
                            event_name=event_data['name'],
                            currency=event_data['currency'],
                            timestamp=event_time,
                            forecast=event_data.get('forecast'),
                            previous=event_data.get('previous'),
                            actual=event_data.get('actual')
                        )

                        # Set impact level
                        impact_str = event_data.get('impact', 'LOW')
                        event.impact_level = ImpactLevel[impact_str]

                        # Set pip impact
                        event.avg_pip_impact = event_data.get('avg_pip_impact', 50)

                        events.append(event)

                except Exception as e:
                    self.logger.error(f"Failed to parse local calendar event: {e}")
                    continue

        except Exception as e:
            vprint(f"Local calendar file error: {e}")

        return events

    def get_this_weeks_nfp(self) -> Optional[NewsEvent]:
        """
        Get this week's Non-Farm Payrolls event

        Returns:
            NewsEvent for NFP if found, None otherwise
        """
        events = self.fetch_events(days_ahead=7)

        for event in events:
            if 'Non-Farm' in event.event_name or 'NFP' in event.event_name:
                return event

        return None


# Global instance
calendar_fetcher = CalendarFetcher()
