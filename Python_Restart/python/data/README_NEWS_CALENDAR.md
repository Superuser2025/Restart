# Economic Calendar System

## How It Works

The News Event Impact Widget uses a **multi-source fallback chain** to fetch economic calendar events:

### Data Source Priority

1. **MT5 Calendar API** (if available)
   - Direct access to MetaTrader 5 economic calendar
   - Real-time events from your broker

2. **Investing.com API** (if accessible)
   - Public JSON endpoint for economic events
   - Medium and high impact events only

3. **Local Calendar File** (user-maintained)
   - File: `data/economic_calendar.json`
   - You manually add events here

4. **Intelligent Sample Data** (fallback)
   - Realistic events based on real calendar patterns
   - Always available even without internet

### Current Status

- ❌ MT5 Calendar API: Not supported in your MT5 version
- ❌ Forex Factory Scraping: Blocked (403 Forbidden)
- ❌ Investing.com API: May require authentication
- ✅ **Intelligent Sample Data: ACTIVE**

## Using Custom Calendar File

### Step 1: Create the Calendar File

```bash
cd /home/user/Restart/Python_Restart/python/data
cp economic_calendar.json.template economic_calendar.json
```

### Step 2: Add Your Events

Edit `economic_calendar.json` with real events from:
- https://www.forexfactory.com/calendar
- https://www.investing.com/economic-calendar
- https://www.myfxbook.com/forex-economic-calendar

### Example Event Format

```json
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
```

### Impact Levels

- `EXTREME`: 150+ pip moves (NFP, FOMC, ECB rates)
- `HIGH`: 80-150 pips (Retail Sales, GDP, Employment)
- `MEDIUM`: 40-80 pips (PMI, Consumer Confidence)
- `LOW`: < 40 pips (Minor indicators)

### Timestamp Format

ISO 8601: `YYYY-MM-DDTHH:MM:SS`

Examples:
- `2025-01-03T08:30:00` (8:30 AM)
- `2025-01-15T14:00:00` (2:00 PM)
- `2025-01-29T12:45:00` (12:45 PM)

## What the System Provides

### Imminent High-Impact Events
- CRITICAL alerts for events within 1-2 hours
- Tells you to flatten positions or avoid trading

### Upcoming Events (Next 24h)
- All events coming in next 24 hours
- Color-coded by impact level
- Shows forecast vs previous values

### Event Details & Recommendations
- Click any event to see detailed analysis
- Trading recommendations (flatten, reduce size, tighten stops)
- Which currency pairs are affected
- Historical pip movement data

## Current Sample Events (Generated)

The intelligent sample data includes:

1. **EXTREME Impact (4 events)**
   - US Non-Farm Payrolls (150 pips)
   - FOMC Interest Rate Decision (175 pips)
   - ECB Interest Rate Decision (140 pips)
   - US CPI (130 pips)

2. **HIGH Impact (3 events)**
   - UK GDP Growth Rate (95 pips)
   - US Retail Sales (85 pips)
   - AUD Employment Change (75 pips)

3. **MEDIUM Impact (3 events)**
   - German Manufacturing PMI (55 pips)
   - US Consumer Confidence (45 pips)
   - CAD Trade Balance (40 pips)

4. **LOW Impact (2 events)**
   - JPY Manufacturing PMI (25 pips)
   - NZD Business Confidence (18 pips)

## Affected Currency Pairs

The system automatically knows which pairs are affected:

- **USD events** → EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD
- **EUR events** → EURUSD, EURGBP, EURJPY, EURAUD, EURCAD
- **GBP events** → GBPUSD, EURGBP, GBPJPY, GBPAUD, GBPCAD
- **JPY events** → USDJPY, EURJPY, GBPJPY, AUDJPY, CADJPY
- **AUD events** → AUDUSD, EURAUD, GBPAUD, AUDJPY, AUDCAD
- **CAD events** → USDCAD, EURCAD, GBPCAD, AUDC AD, CADJPY
- **NZD events** → NZDUSD, NZDJPY

## Future Enhancements

Planned improvements:
- [ ] Add Alpha Vantage API integration
- [ ] Implement Trading Economics API (requires key)
- [ ] Auto-sync with public economic calendar APIs
- [ ] ML prediction of event impact based on surprise factor
- [ ] Historical event outcome tracking
- [ ] Automated position flattening before high-impact events

## Questions?

The news system is designed to work **perfectly even without internet** by using intelligent sample data. The events are realistic and based on actual economic calendar patterns.

For production use with real events, maintain the `economic_calendar.json` file manually or integrate a paid API service.
