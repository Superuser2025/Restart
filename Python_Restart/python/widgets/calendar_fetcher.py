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
                    self.logger.info(f"Fetched {len(events)} events from MT5")
                    return events
            except Exception as e:
                self.logger.warning(f"MT5 calendar fetch failed: {e}")

        # Try Forex Factory scraping
        try:
            events = self._fetch_from_forex_factory(days_ahead)
            if events:
                self.logger.info(f"Fetched {len(events)} events from Forex Factory")
                return events
        except Exception as e:
            self.logger.warning(f"Forex Factory fetch failed: {e}")

        # If all fails, return empty list
        self.logger.warning("No calendar source available, using empty calendar")
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
        Fetch events from Forex Factory via web scraping

        Note: This is a simplified implementation. For production,
        consider using a proper API or more robust scraping.
        """
        events = []

        try:
            # Build URL with date range
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Get current week's calendar
            response = requests.get(
                self.forex_factory_url,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                return events

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find calendar table
            calendar_rows = soup.find_all('tr', class_='calendar__row')

            current_date = datetime.now().date()

            for row in calendar_rows:
                try:
                    event = self._parse_forex_factory_row(row, current_date)
                    if event:
                        # Only include events within days_ahead
                        days_until = (event.timestamp.date() - current_date).days
                        if 0 <= days_until <= days_ahead:
                            events.append(event)
                except Exception as e:
                    continue

        except Exception as e:
            self.logger.error(f"Forex Factory scraping failed: {e}")

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
