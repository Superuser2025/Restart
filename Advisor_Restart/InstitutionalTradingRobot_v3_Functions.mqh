//+------------------------------------------------------------------+
//| InstitutionalTradingRobot_v3_Functions.mqh                       |
//| Supporting Functions for Institutional Trading Robot v3.0        |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| FIX #2: SPREAD ANALYSIS                                          |
//+------------------------------------------------------------------+
void AnalyzeSpread()
{
    long spread_points = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
    double spread_pips = spread_points * _Point / 10.0;

    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0)
    {
        spread_data.acceptable = false;
        return;
    }

    double atr = atr_buffer[0];
    double max_spread = atr * MaxSpreadPercent;
    double max_spread_pips = max_spread / _Point / 10.0;

    spread_data.current_pips = spread_pips;
    spread_data.max_allowed_pips = max_spread_pips;
    spread_data.acceptable = (spread_pips <= max_spread_pips);
}

//+------------------------------------------------------------------+
//| FIX #6: SESSION ANALYSIS                                         |
//+------------------------------------------------------------------+
void AnalyzeSession()
{
    MqlDateTime dt;
    TimeToStruct(TimeGMT(), dt);
    int hour = dt.hour;

    if(hour >= 0 && hour < 8)
    {
        current_session = SESSION_ASIAN;
        session_data.current_session = SESSION_ASIAN;
        session_data.session_name = "Asian";
        session_data.expected_volatility = 0.5;
        session_data.is_tradeable = TradeAsianSession;
    }
    else if(hour >= 8 && hour < 13)
    {
        current_session = SESSION_LONDON;
        session_data.current_session = SESSION_LONDON;
        session_data.session_name = "London";
        session_data.expected_volatility = 1.2;
        session_data.is_tradeable = TradeLondonSession;
    }
    else if(hour >= 13 && hour < 16)
    {
        current_session = SESSION_OVERLAP;
        session_data.current_session = SESSION_OVERLAP;
        session_data.session_name = "London-NY Overlap";
        session_data.expected_volatility = 1.5;
        session_data.is_tradeable = (TradeLondonSession && TradeNYSession);
    }
    else if(hour >= 16 && hour < 21)
    {
        current_session = SESSION_NY;
        session_data.current_session = SESSION_NY;
        session_data.session_name = "New York";
        session_data.expected_volatility = 1.1;
        session_data.is_tradeable = TradeNYSession;
    }
    else
    {
        current_session = SESSION_CLOSED;
        session_data.current_session = SESSION_CLOSED;
        session_data.session_name = "After Hours";
        session_data.expected_volatility = 0.3;
        session_data.is_tradeable = false;
    }
}

//+------------------------------------------------------------------+
//| FIX #8: ECONOMIC CALENDAR CHECK                                  |
//+------------------------------------------------------------------+
void CheckEconomicCalendar()
{
    news_count = 0;

    MqlCalendarValue values[];
    datetime from = TimeCurrent();
    datetime to = TimeCurrent() + NewsAvoidMinutes * 60;

    if(CalendarValueHistory(values, from, to) > 0)
    {
        for(int i = 0; i < ArraySize(values); i++)
        {
            MqlCalendarEvent event;
            if(CalendarEventById(values[i].event_id, event))
            {
                if(event.importance == CALENDAR_IMPORTANCE_HIGH)
                {
                    if(news_count < 20)
                    {
                        upcoming_news[news_count].event_time = values[i].time;
                        upcoming_news[news_count].event_name = event.name;
                        upcoming_news[news_count].importance = event.importance;
                        upcoming_news[news_count].is_near = true;

                        MqlCalendarCountry country;
                        CalendarCountryById(event.country_id, country);
                        upcoming_news[news_count].currency = country.currency;

                        news_count++;
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| FIX #9: VOLATILITY REGIME ANALYSIS                               |
//+------------------------------------------------------------------+
void AnalyzeVolatilityRegime()
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 100, atr_buffer) <= 0) return;

    double atr_current = atr_buffer[0];
    double atr_sum = 0;
    for(int i = 0; i < 100; i++)
        atr_sum += atr_buffer[i];
    double atr_avg = atr_sum / 100;

    double ratio = atr_current / atr_avg;

    volatility_data.atr_current = atr_current;
    volatility_data.atr_average = atr_avg;
    volatility_data.ratio = ratio;

    if(ratio < 0.7)
        current_volatility = VOL_LOW;
    else if(ratio > 1.5)
        current_volatility = VOL_HIGH;
    else
        current_volatility = VOL_NORMAL;

    volatility_data.regime = current_volatility;
}

//+------------------------------------------------------------------+
//| DETECT MARKET REGIME                                             |
//+------------------------------------------------------------------+
void DetectMarketRegime()
{
    double ema_buffer[];
    double atr_buffer[];
    ArraySetAsSeries(ema_buffer, true);
    ArraySetAsSeries(atr_buffer, true);

    if(CopyBuffer(h_EMA_200, 0, 0, 50, ema_buffer) <= 0) return;
    if(CopyBuffer(h_ATR, 0, 0, 20, atr_buffer) <= 0) return;

    // Calculate EMA slope
    double ema_slope = (ema_buffer[0] - ema_buffer[10]) / 10;

    // Calculate ATR ratio
    double atr_sum = 0;
    for(int i = 0; i < 10; i++)
        atr_sum += atr_buffer[i];
    double atr_avg = atr_sum / 10;
    double atr_ratio = atr_buffer[0] / atr_avg;

    // Detect regime
    if(MathAbs(ema_slope) > 0.0001 && atr_ratio > 0.8)
        current_regime = REGIME_TREND;
    else if(MathAbs(ema_slope) < 0.00005 && atr_ratio < 1.1)
        current_regime = REGIME_RANGE;
    else
        current_regime = REGIME_TRANSITION;
}

//+------------------------------------------------------------------+
//| DETERMINE MARKET BIAS                                            |
//+------------------------------------------------------------------+
void DetermineBias()
{
    double ema_buffer[];
    ArraySetAsSeries(ema_buffer, true);
    if(CopyBuffer(h_EMA_200, 0, 0, 3, ema_buffer) <= 0) return;

    double close_price = iClose(_Symbol, PreferredTimeframe, 1);

    if(current_regime == REGIME_TREND)
    {
        if(close_price > ema_buffer[0])
            current_bias = BIAS_BULLISH;
        else
            current_bias = BIAS_BEARISH;
    }
    else if(current_regime == REGIME_RANGE)
    {
        double range_high = GetRangeHigh(50);
        double range_low = GetRangeLow(50);
        double range_size = range_high - range_low;

        if(close_price < range_low + range_size * 0.2)
            current_bias = BIAS_BULLISH;
        else if(close_price > range_high - range_size * 0.2)
            current_bias = BIAS_BEARISH;
        else
            current_bias = BIAS_NEUTRAL;
    }
    else
    {
        current_bias = BIAS_NEUTRAL;
    }
}

//+------------------------------------------------------------------+
//| FIX #16: UPDATE MARKET STRUCTURE                                 |
//+------------------------------------------------------------------+
void UpdateMarketStructure()
{
    double swing_high = GetSwingHigh(20);
    double swing_low = GetSwingLow(20);

    // Bullish structure: Higher Highs and Higher Lows
    if(swing_high > market_structure.last_HH && swing_low > market_structure.last_HL)
    {
        market_structure.structure = "BULLISH (HH+HL)";
        market_structure.last_HH = swing_high;
        market_structure.last_HL = swing_low;
        market_structure.last_update = TimeCurrent();
    }
    // Bearish structure: Lower Highs and Lower Lows
    else if(swing_high < market_structure.last_LH && swing_low < market_structure.last_LL)
    {
        market_structure.structure = "BEARISH (LH+LL)";
        market_structure.last_LH = swing_high;
        market_structure.last_LL = swing_low;
        market_structure.last_update = TimeCurrent();
    }
    else
    {
        market_structure.structure = "CHOPPY";
    }
}

//+------------------------------------------------------------------+
//| MAP LIQUIDITY ZONES                                              |
//+------------------------------------------------------------------+
void MapLiquidityZones()
{
    liquidity_count = 0;
    int lookback = 20;

    for(int i = lookback; i < 100 && liquidity_count < 100; i++)
    {
        double high = iHigh(_Symbol, PreferredTimeframe, i);
        double low = iLow(_Symbol, PreferredTimeframe, i);
        datetime time = iTime(_Symbol, PreferredTimeframe, i);

        // Check for swing high
        bool is_swing_high = true;
        for(int j = 1; j <= lookback; j++)
        {
            if(i-j < 0 || i+j >= Bars(_Symbol, PreferredTimeframe))
            {
                is_swing_high = false;
                break;
            }
            if(iHigh(_Symbol, PreferredTimeframe, i-j) >= high ||
               iHigh(_Symbol, PreferredTimeframe, i+j) >= high)
            {
                is_swing_high = false;
                break;
            }
        }

        if(is_swing_high)
        {
            liquidity_zones[liquidity_count].price = high;
            liquidity_zones[liquidity_count].is_high = true;
            liquidity_zones[liquidity_count].time = time;
            liquidity_zones[liquidity_count].touch_count = 0;
            liquidity_zones[liquidity_count].swept = false;
            liquidity_count++;
        }

        // Check for swing low
        bool is_swing_low = true;
        for(int j = 1; j <= lookback; j++)
        {
            if(i-j < 0 || i+j >= Bars(_Symbol, PreferredTimeframe))
            {
                is_swing_low = false;
                break;
            }
            if(iLow(_Symbol, PreferredTimeframe, i-j) <= low ||
               iLow(_Symbol, PreferredTimeframe, i+j) <= low)
            {
                is_swing_low = false;
                break;
            }
        }

        if(is_swing_low && liquidity_count < 100)
        {
            liquidity_zones[liquidity_count].price = low;
            liquidity_zones[liquidity_count].is_high = false;
            liquidity_zones[liquidity_count].time = time;
            liquidity_zones[liquidity_count].touch_count = 0;
            liquidity_zones[liquidity_count].swept = false;
            liquidity_count++;
        }
    }
}

//+------------------------------------------------------------------+
//| DETECT FAIR VALUE GAPS                                           |
//+------------------------------------------------------------------+
void DetectFairValueGaps()
{
    fvg_count = 0;
    double min_gap = 5 * _Point * 10;

    for(int i = 1; i < 50 && fvg_count < 50; i++)
    {
        double high1 = iHigh(_Symbol, PreferredTimeframe, i+1);
        double low1 = iLow(_Symbol, PreferredTimeframe, i+1);
        double high3 = iHigh(_Symbol, PreferredTimeframe, i-1);
        double low3 = iLow(_Symbol, PreferredTimeframe, i-1);

        // Bullish FVG
        if(low3 > high1 && (low3 - high1) >= min_gap)
        {
            fvg_zones[fvg_count].top = low3;
            fvg_zones[fvg_count].bottom = high1;
            fvg_zones[fvg_count].time = iTime(_Symbol, PreferredTimeframe, i);
            fvg_zones[fvg_count].is_bullish = true;
            fvg_zones[fvg_count].filled = false;
            fvg_zones[fvg_count].fill_percentage = 0;
            fvg_zones[fvg_count].visit_count = 0;
            fvg_zones[fvg_count].first_visit_time = 0;
            fvg_zones[fvg_count].last_visit_time = 0;
            fvg_zones[fvg_count].ever_visited = false;
            fvg_count++;
        }

        // Bearish FVG
        if(high3 < low1 && (low1 - high3) >= min_gap && fvg_count < 50)
        {
            fvg_zones[fvg_count].top = low1;
            fvg_zones[fvg_count].bottom = high3;
            fvg_zones[fvg_count].time = iTime(_Symbol, PreferredTimeframe, i);
            fvg_zones[fvg_count].is_bullish = false;
            fvg_zones[fvg_count].filled = false;
            fvg_zones[fvg_count].fill_percentage = 0;
            fvg_zones[fvg_count].visit_count = 0;
            fvg_zones[fvg_count].first_visit_time = 0;
            fvg_zones[fvg_count].last_visit_time = 0;
            fvg_zones[fvg_count].ever_visited = false;
            fvg_count++;
        }
    }
}

//+------------------------------------------------------------------+
//| DETECT ORDER BLOCKS                                              |
//+------------------------------------------------------------------+
void DetectOrderBlocks()
{
    ob_count = 0;

    for(int i = 2; i < 100 && ob_count < 50; i++)
    {
        double close_prev = iClose(_Symbol, PreferredTimeframe, i);
        double open_prev = iOpen(_Symbol, PreferredTimeframe, i);
        double close_curr = iClose(_Symbol, PreferredTimeframe, i-1);

        // Bullish Order Block
        if(close_prev < open_prev && close_curr > close_prev)
        {
            order_blocks[ob_count].top = MathMax(open_prev, close_prev);
            order_blocks[ob_count].bottom = MathMin(open_prev, close_prev);
            order_blocks[ob_count].time = iTime(_Symbol, PreferredTimeframe, i);
            order_blocks[ob_count].is_bullish = true;
            order_blocks[ob_count].test_count = 0;
            order_blocks[ob_count].invalidated = false;
            order_blocks[ob_count].visit_count = 0;
            order_blocks[ob_count].first_visit_time = 0;
            order_blocks[ob_count].ever_visited = false;
            ob_count++;
        }

        // Bearish Order Block
        if(close_prev > open_prev && close_curr < close_prev && ob_count < 50)
        {
            order_blocks[ob_count].top = MathMax(open_prev, close_prev);
            order_blocks[ob_count].bottom = MathMin(open_prev, close_prev);
            order_blocks[ob_count].time = iTime(_Symbol, PreferredTimeframe, i);
            order_blocks[ob_count].is_bullish = false;
            order_blocks[ob_count].test_count = 0;
            order_blocks[ob_count].invalidated = false;
            order_blocks[ob_count].visit_count = 0;
            order_blocks[ob_count].first_visit_time = 0;
            order_blocks[ob_count].ever_visited = false;
            ob_count++;
        }
    }

    // FIX #15: Update Order Block Invalidation
    if(g_UseOrderBlockInvalidation)
        UpdateOrderBlockInvalidation();
}

//+------------------------------------------------------------------+
//| FIX #15: ORDER BLOCK INVALIDATION                                |
//+------------------------------------------------------------------+
void UpdateOrderBlockInvalidation()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);

    for(int i = 0; i < ob_count; i++)
    {
        if(order_blocks[i].invalidated) continue;

        // Check if price is testing the OB
        if(current_price >= order_blocks[i].bottom && current_price <= order_blocks[i].top)
        {
            order_blocks[i].test_count++;
            order_blocks[i].last_test_time = TimeCurrent();

            if(order_blocks[i].test_count >= MaxOBTests)
            {
                order_blocks[i].invalidated = true;
                AddComment("Order Block INVALIDATED (max tests reached)", clrRed, PRIORITY_IMPORTANT);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| FIX #1: VOLUME ANALYSIS                                          |
//+------------------------------------------------------------------+
void AnalyzeVolume()
{
    long current_vol = iVolume(_Symbol, PreferredTimeframe, 1);

    double vol_ma_buffer[];
    ArraySetAsSeries(vol_ma_buffer, true);
    if(CopyBuffer(h_Volume_MA, 0, 0, 20, vol_ma_buffer) <= 0)
    {
        volume_data.above_threshold = false;
        return;
    }

    double avg_vol = vol_ma_buffer[0];

    volume_data.current_volume = (double)current_vol;
    volume_data.average_volume = avg_vol;
    volume_data.volume_ratio = current_vol / avg_vol;
    volume_data.above_threshold = (volume_data.volume_ratio >= MinVolumeMultiplier);
    volume_data.spike_detected = (volume_data.volume_ratio >= 2.0);
}

//+------------------------------------------------------------------+
//| FIX #5: MULTI-TIMEFRAME CONFIRMATION                             |
//+------------------------------------------------------------------+
bool CheckMultiTimeframeAlignment()
{
    double ema_higher_buffer[];
    ArraySetAsSeries(ema_higher_buffer, true);
    if(CopyBuffer(h_EMA_Higher, 0, 0, 1, ema_higher_buffer) <= 0)
        return false;

    ENUM_TIMEFRAMES higher_tf = GetHigherTimeframe(PreferredTimeframe);
    double price_higher = iClose(_Symbol, higher_tf, 0);

    bool higher_bullish = (price_higher > ema_higher_buffer[0]);
    bool higher_bearish = (price_higher < ema_higher_buffer[0]);

    // Check alignment with pattern direction
    if(active_pattern.is_bullish && higher_bearish) return false;
    if(!active_pattern.is_bullish && higher_bullish) return false;

    return true;
}

//+------------------------------------------------------------------+
//| FIX #7: PORTFOLIO CORRELATION CHECK                              |
//+------------------------------------------------------------------+
bool CheckPortfolioCorrelation()
{
    string base_currency = StringSubstr(_Symbol, 0, 3);
    string quote_currency = StringSubstr(_Symbol, 3, 3);

    double net_exposure = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Magic() != MagicNumber) continue;

            string pos_symbol = position.Symbol();
            string pos_base = StringSubstr(pos_symbol, 0, 3);
            string pos_quote = StringSubstr(pos_symbol, 3, 3);

            double lots = position.Volume();
            int direction = (position.Type() == POSITION_TYPE_BUY) ? 1 : -1;

            // Check correlation
            if(pos_base == base_currency || pos_quote == quote_currency ||
               pos_base == quote_currency || pos_quote == base_currency)
            {
                net_exposure += lots * direction;
            }
        }
    }

    // Reject if over-exposed
    if(MathAbs(net_exposure) > MaxCorrelationExposure * 10)
        return false;

    return true;
}

//+------------------------------------------------------------------+
//| FIX #13: LIQUIDITY SWEEP DETECTION                               |
//+------------------------------------------------------------------+
bool CheckLiquiditySweep(bool is_buy_pattern)
{
    double current_high = iHigh(_Symbol, PreferredTimeframe, 1);
    double current_low = iLow(_Symbol, PreferredTimeframe, 1);
    double current_close = iClose(_Symbol, PreferredTimeframe, 1);

    if(is_buy_pattern)
    {
        // Look for sweep below previous low
        for(int i = 0; i < liquidity_count; i++)
        {
            if(!liquidity_zones[i].is_high)
            {
                double prev_low = liquidity_zones[i].price;
                // Sweep = went below then closed above
                if(current_low < prev_low && current_close > prev_low)
                {
                    liquidity_zones[i].swept = true;
                    return true;
                }
            }
        }
    }
    else
    {
        // Look for sweep above previous high
        for(int i = 0; i < liquidity_count; i++)
        {
            if(liquidity_zones[i].is_high)
            {
                double prev_high = liquidity_zones[i].price;
                // Sweep = went above then closed below
                if(current_high > prev_high && current_close < prev_high)
                {
                    liquidity_zones[i].swept = true;
                    return true;
                }
            }
        }
    }

    return false;
}

//+------------------------------------------------------------------+
//| FIX #14: RETAIL TRAP DETECTION                                   |
//+------------------------------------------------------------------+
bool DetectRetailTrap()
{
    double high1 = iHigh(_Symbol, PreferredTimeframe, 1);
    double close1 = iClose(_Symbol, PreferredTimeframe, 1);

    // Find nearest resistance
    double resistance = 0;
    for(int i = 0; i < liquidity_count; i++)
    {
        if(liquidity_zones[i].is_high && liquidity_zones[i].price > close1)
        {
            if(resistance == 0 || liquidity_zones[i].price < resistance)
                resistance = liquidity_zones[i].price;
        }
    }

    if(resistance == 0) return false;

    // Fake breakout: breaks above but closes below with high volume
    if(high1 > resistance && close1 < resistance && volume_data.volume_ratio > 2.0)
        return true;

    return false;
}

//+------------------------------------------------------------------+
//| HELPER FUNCTIONS                                                  |
//+------------------------------------------------------------------+
double GetSwingHigh(int lookback)
{
    double high = 0;
    for(int i = 1; i <= lookback; i++)
    {
        double h = iHigh(_Symbol, PreferredTimeframe, i);
        if(h > high) high = h;
    }
    return high;
}

double GetSwingLow(int lookback)
{
    double low = DBL_MAX;
    for(int i = 1; i <= lookback; i++)
    {
        double l = iLow(_Symbol, PreferredTimeframe, i);
        if(l < low) low = l;
    }
    return low;
}

double GetRangeHigh(int lookback)
{
    double high = 0;
    for(int i = 1; i < lookback; i++)
    {
        double h = iHigh(_Symbol, PreferredTimeframe, i);
        if(h > high) high = h;
    }
    return high;
}

double GetRangeLow(int lookback)
{
    double low = DBL_MAX;
    for(int i = 1; i < lookback; i++)
    {
        double l = iLow(_Symbol, PreferredTimeframe, i);
        if(l < low) low = l;
    }
    return low;
}

//+------------------------------------------------------------------+
//| COMPREHENSIVE PRICE ACTION COMMENTARY MODULE                      |
//| Educational real-time analysis and explanations                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Analyze Candlestick Patterns - Identify key reversal patterns    |
//+------------------------------------------------------------------+
void AnalyzeCandlestickPatterns()
{
    double open0 = iOpen(_Symbol, PreferredTimeframe, 1);
    double high0 = iHigh(_Symbol, PreferredTimeframe, 1);
    double low0 = iLow(_Symbol, PreferredTimeframe, 1);
    double close0 = iClose(_Symbol, PreferredTimeframe, 1);
    double body0 = MathAbs(close0 - open0);
    double range0 = high0 - low0;

    double open1 = iOpen(_Symbol, PreferredTimeframe, 2);
    double close1 = iClose(_Symbol, PreferredTimeframe, 2);
    double body1 = MathAbs(close1 - open1);

    if(range0 < _Point) return;  // Avoid division by zero

    // Pin Bar / Hammer / Shooting Star
    double upper_wick = high0 - MathMax(open0, close0);
    double lower_wick = MathMin(open0, close0) - low0;
    double body_ratio = body0 / range0;

    if(body_ratio < 0.3)  // Small body
    {
        if(lower_wick > body0 * 2 && upper_wick < body0)  // Long lower wick
        {
            AddPriceActionComment("🕯️ BULLISH PIN BAR detected at " + DoubleToString(low0, _Digits), clrLime, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Strong rejection of lower prices - Buyers stepping in", clrYellow, PRIORITY_IMPORTANT);
        }
        else if(upper_wick > body0 * 2 && lower_wick < body0)  // Long upper wick
        {
            AddPriceActionComment("🕯️ BEARISH PIN BAR detected at " + DoubleToString(high0, _Digits), clrRed, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Strong rejection of higher prices - Sellers stepping in", clrYellow, PRIORITY_IMPORTANT);
        }
    }

    // Engulfing Patterns
    if(body0 > body1 * 1.5 && body1 > 0)
    {
        bool bullish_engulf = (close1 < open1) && (close0 > open0) && (close0 > open1) && (open0 < close1);
        bool bearish_engulf = (close1 > open1) && (close0 < open0) && (close0 < open1) && (open0 > close1);

        if(bullish_engulf)
        {
            AddPriceActionComment("🟢 BULLISH ENGULFING pattern formed", clrLime, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Buyers overwhelmed sellers - Potential reversal/continuation", clrYellow, PRIORITY_IMPORTANT);
        }
        else if(bearish_engulf)
        {
            AddPriceActionComment("🔴 BEARISH ENGULFING pattern formed", clrRed, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Sellers overwhelmed buyers - Potential reversal/continuation", clrYellow, PRIORITY_IMPORTANT);
        }
    }

    // Doji / Indecision Candles
    if(body_ratio < 0.1)
    {
        AddPriceActionComment("⚖️ DOJI candle - Market indecision", clrOrange, PRIORITY_IMPORTANT);
        AddPriceActionComment("→ Bulls and bears in equilibrium - Awaiting breakout direction", clrYellow, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| Analyze Trend Strength - Evaluate current trend momentum         |
//+------------------------------------------------------------------+
void AnalyzeTrendStrength()
{
    double ema_buffer[];
    ArraySetAsSeries(ema_buffer, true);
    if(CopyBuffer(h_EMA_200, 0, 0, 3, ema_buffer) <= 0) return;

    double current_price = iClose(_Symbol, PreferredTimeframe, 0);
    double price_distance = ((current_price - ema_buffer[0]) / ema_buffer[0]) * 100.0;

    // EMA Slope (trend strength indicator)
    double ema_slope = ema_buffer[0] - ema_buffer[2];

    if(MathAbs(price_distance) > 5.0)
    {
        if(price_distance > 0)
        {
            AddPriceActionComment("📊 STRONG BULLISH TREND - Price " + DoubleToString(MathAbs(price_distance), 1) + "% above EMA200", clrLime, PRIORITY_IMPORTANT);
            AddPriceActionComment("→ Extended move - Watch for potential pullback/consolidation", clrYellow, PRIORITY_INFO);
        }
        else
        {
            AddPriceActionComment("📊 STRONG BEARISH TREND - Price " + DoubleToString(MathAbs(price_distance), 1) + "% below EMA200", clrRed, PRIORITY_IMPORTANT);
            AddPriceActionComment("→ Extended move - Watch for potential pullback/consolidation", clrYellow, PRIORITY_INFO);
        }
    }
    else if(MathAbs(price_distance) < 1.0)
    {
        AddPriceActionComment("🎯 Price AT EMA200 - Key decision zone", clrOrange, PRIORITY_IMPORTANT);
        AddPriceActionComment("→ Major support/resistance test - Breakout or bounce likely", clrYellow, PRIORITY_IMPORTANT);
    }
}

//+------------------------------------------------------------------+
//| Analyze Momentum - Detect acceleration and deceleration          |
//+------------------------------------------------------------------+
void AnalyzeMomentum()
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 5, atr_buffer) <= 0) return;

    // Compare recent candle ranges to ATR
    double current_range = iHigh(_Symbol, PreferredTimeframe, 1) - iLow(_Symbol, PreferredTimeframe, 1);
    double avg_atr = (atr_buffer[0] + atr_buffer[1] + atr_buffer[2]) / 3.0;

    if(current_range > avg_atr * 1.5)
    {
        bool bullish = iClose(_Symbol, PreferredTimeframe, 1) > iOpen(_Symbol, PreferredTimeframe, 1);
        if(bullish)
        {
            AddPriceActionComment("⚡ MOMENTUM SURGE - Bullish acceleration detected", clrLime, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Strong buying pressure - Trend may be accelerating", clrYellow, PRIORITY_IMPORTANT);
        }
        else
        {
            AddPriceActionComment("⚡ MOMENTUM SURGE - Bearish acceleration detected", clrRed, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Strong selling pressure - Trend may be accelerating", clrYellow, PRIORITY_IMPORTANT);
        }
    }
    else if(current_range < avg_atr * 0.5)
    {
        AddPriceActionComment("🐌 MOMENTUM SLOWING - Reduced volatility", clrGray, PRIORITY_INFO);
        AddPriceActionComment("→ Market consolidating - Potential breakout setup forming", clrOrange, PRIORITY_INFO);
    }

    // Check if ATR is expanding (volatility increasing)
    if(atr_buffer[0] > atr_buffer[4] * 1.3)
    {
        AddPriceActionComment("📈 VOLATILITY EXPANDING - ATR increasing", clrOrange, PRIORITY_IMPORTANT);
        AddPriceActionComment("→ Larger moves expected - Adjust position sizing", clrYellow, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| Detect Consolidation Zones - Identify ranging markets            |
//+------------------------------------------------------------------+
void DetectConsolidation()
{
    // Calculate range of last 10 bars
    double highest = iHigh(_Symbol, PreferredTimeframe, iHighest(_Symbol, PreferredTimeframe, MODE_HIGH, 10, 1));
    double lowest = iLow(_Symbol, PreferredTimeframe, iLowest(_Symbol, PreferredTimeframe, MODE_LOW, 10, 1));
    double range = highest - lowest;

    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return;

    double expected_range = atr_buffer[0] * 10;  // Expected range for 10 bars

    if(range < expected_range * 0.6)
    {
        AddPriceActionComment("📦 CONSOLIDATION ZONE detected - Tight range", clrCyan, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Compression phase - Breakout likely imminent", clrYellow, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Range: " + DoubleToString(lowest, _Digits) + " - " + DoubleToString(highest, _Digits), clrAqua, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| Detect Breakouts - Identify when price breaks key levels         |
//+------------------------------------------------------------------+
void DetectBreakouts()
{
    double current_high = iHigh(_Symbol, PreferredTimeframe, 1);
    double current_low = iLow(_Symbol, PreferredTimeframe, 1);
    double current_close = iClose(_Symbol, PreferredTimeframe, 1);

    // Get recent swing high/low (last 20 bars)
    double swing_high = iHigh(_Symbol, PreferredTimeframe, iHighest(_Symbol, PreferredTimeframe, MODE_HIGH, 20, 2));
    double swing_low = iLow(_Symbol, PreferredTimeframe, iLowest(_Symbol, PreferredTimeframe, MODE_LOW, 20, 2));

    // Check for breakout above swing high
    if(current_high > swing_high && current_close > swing_high)
    {
        AddPriceActionComment("🚀 BULLISH BREAKOUT - Price broke above swing high at " + DoubleToString(swing_high, _Digits), clrLime, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Resistance turned support - Look for continuation", clrYellow, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Watch for retest of breakout level", clrAqua, PRIORITY_IMPORTANT);
    }

    // Check for breakdown below swing low
    if(current_low < swing_low && current_close < swing_low)
    {
        AddPriceActionComment("🔻 BEARISH BREAKDOWN - Price broke below swing low at " + DoubleToString(swing_low, _Digits), clrRed, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Support turned resistance - Look for continuation", clrYellow, PRIORITY_CRITICAL);
        AddPriceActionComment("→ Watch for retest of breakdown level", clrAqua, PRIORITY_IMPORTANT);
    }
}

//+------------------------------------------------------------------+
//| Analyze Support/Resistance Tests - Track key level interactions  |
//+------------------------------------------------------------------+
void AnalyzeSupportResistanceTests()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);
    double current_high = iHigh(_Symbol, PreferredTimeframe, 1);
    double current_low = iLow(_Symbol, PreferredTimeframe, 1);

    double ema_buffer[];
    ArraySetAsSeries(ema_buffer, true);
    if(CopyBuffer(h_EMA_200, 0, 0, 1, ema_buffer) <= 0) return;
    double ema200 = ema_buffer[0];

    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return;
    double atr = atr_buffer[0];

    // Check if price is testing EMA200
    double distance_to_ema = MathAbs(current_price - ema200);
    if(distance_to_ema < atr * 0.5)
    {
        if(current_price > ema200)
        {
            AddPriceActionComment("🎯 Testing EMA200 SUPPORT at " + DoubleToString(ema200, _Digits), clrCyan, PRIORITY_IMPORTANT);
            AddPriceActionComment("→ Key dynamic support - Watch for bounce or break", clrYellow, PRIORITY_IMPORTANT);
        }
        else
        {
            AddPriceActionComment("🎯 Testing EMA200 RESISTANCE at " + DoubleToString(ema200, _Digits), clrOrange, PRIORITY_IMPORTANT);
            AddPriceActionComment("→ Key dynamic resistance - Watch for rejection or break", clrYellow, PRIORITY_IMPORTANT);
        }
    }
}

//+------------------------------------------------------------------+
//| Analyze FVG Fills - Track and explain Fair Value Gap fills       |
//+------------------------------------------------------------------+
void AnalyzeFVGFills()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);
    double current_high = iHigh(_Symbol, PreferredTimeframe, 0);
    double current_low = iLow(_Symbol, PreferredTimeframe, 0);
    double prev_close = iClose(_Symbol, PreferredTimeframe, 1);

    for(int i = 0; i < fvg_count; i++)
    {
        if(fvg_zones[i].filled) continue;

        // Check if price is interacting with FVG
        bool price_in_fvg = (current_high >= fvg_zones[i].bottom && current_low <= fvg_zones[i].top);
        bool prev_in_fvg = (prev_close >= fvg_zones[i].bottom && prev_close <= fvg_zones[i].top);

        // Detect entry direction
        bool entering_from_top = !prev_in_fvg && price_in_fvg && prev_close > fvg_zones[i].top;
        bool entering_from_bottom = !prev_in_fvg && price_in_fvg && prev_close < fvg_zones[i].bottom;

        if(price_in_fvg)
        {
            // Track visits - update visit tracking
            if(!prev_in_fvg)  // Just entered
            {
                fvg_zones[i].visit_count++;
                if(!fvg_zones[i].ever_visited)
                {
                    fvg_zones[i].ever_visited = true;
                    fvg_zones[i].first_visit_time = TimeCurrent();
                }
                fvg_zones[i].last_visit_time = TimeCurrent();
            }

            // Calculate fill percentage
            double gap_size = fvg_zones[i].top - fvg_zones[i].bottom;
            double filled_amount = 0;

            if(fvg_zones[i].is_bullish)
            {
                // Bullish FVG fills from bottom up
                if(current_low <= fvg_zones[i].bottom)
                    filled_amount = MathMin(current_high, fvg_zones[i].top) - fvg_zones[i].bottom;
                else
                    filled_amount = MathMin(current_high, fvg_zones[i].top) - current_low;
            }
            else
            {
                // Bearish FVG fills from top down
                if(current_high >= fvg_zones[i].top)
                    filled_amount = fvg_zones[i].top - MathMax(current_low, fvg_zones[i].bottom);
                else
                    filled_amount = current_high - MathMax(current_low, fvg_zones[i].bottom);
            }

            double fill_percentage = (filled_amount / gap_size) * 100.0;
            fvg_zones[i].fill_percentage = fill_percentage;

            // Generate commentary based on fill level
            string fvg_type = fvg_zones[i].is_bullish ? "BULLISH" : "BEARISH";
            string gap_range = DoubleToString(fvg_zones[i].bottom, _Digits) + " - " + DoubleToString(fvg_zones[i].top, _Digits);

            // Determine if heading there or revisiting
            bool is_heading = (fvg_zones[i].visit_count == 1);  // First visit = heading there
            bool is_revisiting = (fvg_zones[i].visit_count > 1);  // Multiple visits = revisiting
            string visit_context = is_heading ? " - HEADING to FVG (1st approach)" : " - REVISITING FVG (visit #" + IntegerToString(fvg_zones[i].visit_count) + ")";

            // Add direction context
            string direction_text = "";
            if(entering_from_top)
            {
                direction_text = " from ABOVE";
                if(fvg_zones[i].is_bullish)
                {
                    if(is_heading)
                        AddPriceActionComment("→ Price HEADING to bullish FVG from above (1st approach) - Less ideal, watch for reversal",
                                             clrOrange, PRIORITY_INFO, fvg_zones[i].time);
                    else
                        AddPriceActionComment("→ Price REVISITING bullish FVG from above (visit #" + IntegerToString(fvg_zones[i].visit_count) + ") - Weakening zone",
                                             clrOrange, PRIORITY_INFO, fvg_zones[i].time);
                }
                else
                {
                    if(is_heading)
                        AddPriceActionComment("→ Price HEADING to bearish FVG from above (1st approach) - IDEAL direction for shorts",
                                             clrRed, PRIORITY_INFO, fvg_zones[i].time);
                    else
                        AddPriceActionComment("→ Price REVISITING bearish FVG from above (visit #" + IntegerToString(fvg_zones[i].visit_count) + ") - Still valid",
                                             clrRed, PRIORITY_INFO, fvg_zones[i].time);
                }
            }
            else if(entering_from_bottom)
            {
                direction_text = " from BELOW";
                if(fvg_zones[i].is_bullish)
                {
                    if(is_heading)
                        AddPriceActionComment("→ Price HEADING to bullish FVG from below (1st approach) - IDEAL direction for longs",
                                             clrLime, PRIORITY_INFO, fvg_zones[i].time);
                    else
                        AddPriceActionComment("→ Price REVISITING bullish FVG from below (visit #" + IntegerToString(fvg_zones[i].visit_count) + ") - Still valid",
                                             clrLime, PRIORITY_INFO, fvg_zones[i].time);
                }
                else
                {
                    if(is_heading)
                        AddPriceActionComment("→ Price HEADING to bearish FVG from below (1st approach) - Less ideal, watch for reversal",
                                             clrOrange, PRIORITY_INFO, fvg_zones[i].time);
                    else
                        AddPriceActionComment("→ Price REVISITING bearish FVG from below (visit #" + IntegerToString(fvg_zones[i].visit_count) + ") - Weakening zone",
                                             clrOrange, PRIORITY_INFO, fvg_zones[i].time);
                }
            }

            if(fill_percentage >= 90)
            {
                fvg_zones[i].filled = true;
                AddPriceActionComment("✓ " + fvg_type + " FVG FULLY FILLED" + direction_text + " (" + gap_range + ")",
                                     fvg_zones[i].is_bullish ? clrLime : clrRed, PRIORITY_IMPORTANT, fvg_zones[i].time);
                AddPriceActionComment("→ Imbalance corrected - Watch for continuation or reversal",
                                     clrYellow, PRIORITY_INFO);
            }
            else if(fill_percentage >= 50)
            {
                AddPriceActionComment("⚡ " + fvg_type + " FVG " + DoubleToString(fill_percentage, 0) + "% FILLED" + direction_text + " (" + gap_range + ")",
                                     clrOrange, PRIORITY_IMPORTANT, fvg_zones[i].time);
                AddPriceActionComment("→ Partial fill - Price in the GAP zone, looking for reaction",
                                     clrYellow, PRIORITY_INFO);
            }
            else if(fill_percentage > 0 && !prev_in_fvg)
            {
                AddPriceActionComment("→ " + fvg_type + " FVG touched" + direction_text + " (" + DoubleToString(fill_percentage, 0) + "% filled)",
                                     clrCyan, PRIORITY_INFO, fvg_zones[i].time);
                AddPriceActionComment("→ Price entering the imbalance zone - Early reaction point",
                                     clrYellow, PRIORITY_INFO);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Analyze Order Block Interactions - Track price behavior at OBs   |
//+------------------------------------------------------------------+
void AnalyzeOrderBlockInteractions()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);
    double current_high = iHigh(_Symbol, PreferredTimeframe, 0);
    double current_low = iLow(_Symbol, PreferredTimeframe, 0);
    double prev_close = iClose(_Symbol, PreferredTimeframe, 1);

    for(int i = 0; i < ob_count; i++)
    {
        if(order_blocks[i].invalidated) continue;

        bool price_in_ob = (current_low <= order_blocks[i].top && current_high >= order_blocks[i].bottom);
        bool prev_in_ob = (prev_close >= order_blocks[i].bottom && prev_close <= order_blocks[i].top);

        string ob_type = order_blocks[i].is_bullish ? "BULLISH" : "BEARISH";
        string ob_range = DoubleToString(order_blocks[i].bottom, _Digits) + " - " + DoubleToString(order_blocks[i].top, _Digits);

        // Price entering OB
        if(price_in_ob && !prev_in_ob)
        {
            // Track visits - update visit tracking
            order_blocks[i].visit_count++;
            if(!order_blocks[i].ever_visited)
            {
                order_blocks[i].ever_visited = true;
                order_blocks[i].first_visit_time = TimeCurrent();
            }

            // Determine if price is entering from top or bottom
            bool entering_from_top = prev_close > order_blocks[i].top;
            bool entering_from_bottom = prev_close < order_blocks[i].bottom;
            string entry_direction = "";

            // Determine if heading there or revisiting
            bool is_heading = (order_blocks[i].visit_count == 1);  // First visit = heading there
            bool is_revisiting = (order_blocks[i].visit_count > 1);  // Multiple visits = revisiting

            string visit_status = is_heading ? "HEADING to" : "REVISITING";
            string visit_detail = is_heading ? " (1st approach)" : " (visit #" + IntegerToString(order_blocks[i].visit_count) + ")";

            if(entering_from_top)
                entry_direction = " from ABOVE";
            else if(entering_from_bottom)
                entry_direction = " from BELOW";

            AddPriceActionComment("🎯 Price " + visit_status + " " + ob_type + " ORDER BLOCK" + entry_direction + visit_detail + " (" + ob_range + ")",
                                 order_blocks[i].is_bullish ? clrLime : clrRed, PRIORITY_CRITICAL, order_blocks[i].time);

            // Add context about the entry direction and visit status
            if(order_blocks[i].is_bullish && entering_from_bottom)
            {
                if(is_heading)
                    AddPriceActionComment("→ Price HEADING to bullish OB from below (1st time) - IDEAL setup for longs",
                                         clrLime, PRIORITY_IMPORTANT, order_blocks[i].time);
                else
                    AddPriceActionComment("→ Price REVISITING bullish OB from below - Zone still holding, good for longs",
                                         clrLime, PRIORITY_IMPORTANT, order_blocks[i].time);
            }
            else if(order_blocks[i].is_bullish && entering_from_top)
            {
                if(is_heading)
                    AddPriceActionComment("→ Price HEADING to bullish OB from above (1st time) - Possible retest or reversal",
                                         clrYellow, PRIORITY_IMPORTANT, order_blocks[i].time);
                else
                    AddPriceActionComment("→ Price REVISITING bullish OB from above - Re-test in progress, zone weakening",
                                         clrOrange, PRIORITY_IMPORTANT, order_blocks[i].time);
            }
            else if(!order_blocks[i].is_bullish && entering_from_top)
            {
                if(is_heading)
                    AddPriceActionComment("→ Price HEADING to bearish OB from above (1st time) - IDEAL setup for shorts",
                                         clrRed, PRIORITY_IMPORTANT, order_blocks[i].time);
                else
                    AddPriceActionComment("→ Price REVISITING bearish OB from above - Zone still holding, good for shorts",
                                         clrRed, PRIORITY_IMPORTANT, order_blocks[i].time);
            }
            else if(!order_blocks[i].is_bullish && entering_from_bottom)
            {
                if(is_heading)
                    AddPriceActionComment("→ Price HEADING to bearish OB from below (1st time) - Possible retest or reversal",
                                         clrYellow, PRIORITY_IMPORTANT, order_blocks[i].time);
                else
                    AddPriceActionComment("→ Price REVISITING bearish OB from below - Re-test in progress, zone weakening",
                                         clrOrange, PRIORITY_IMPORTANT, order_blocks[i].time);
            }

            AddPriceActionComment("→ Test #" + IntegerToString(order_blocks[i].test_count + 1) +
                                 " - Institutional demand/supply zone " + (is_heading ? "activated for first time" : "still active"),
                                 clrCyan, PRIORITY_IMPORTANT);

            if(order_blocks[i].test_count >= MaxOBTests - 1)
            {
                AddPriceActionComment("⚠ WARNING: Final test of this OB - Next break invalidates it",
                                     clrOrange, PRIORITY_IMPORTANT);
            }
        }

        // Price rejecting from OB
        if(prev_in_ob && !price_in_ob)
        {
            bool rejection = (order_blocks[i].is_bullish && current_price > prev_close) ||
                           (!order_blocks[i].is_bullish && current_price < prev_close);

            if(rejection)
            {
                AddPriceActionComment("✓ STRONG REJECTION from " + ob_type + " ORDER BLOCK!",
                                     clrLime, PRIORITY_CRITICAL);
                AddPriceActionComment("→ Institutional orders triggered - Continuation likely",
                                     clrYellow, PRIORITY_IMPORTANT);
            }
            else
            {
                AddPriceActionComment("⛔ " + ob_type + " ORDER BLOCK BREACHED - Invalidated",
                                     clrRed, PRIORITY_CRITICAL);
                AddPriceActionComment("→ Liquidity absorbed - Look for new zones",
                                     clrOrange, PRIORITY_IMPORTANT);
            }
        }

        // Price inside OB
        if(price_in_ob && prev_in_ob)
        {
            AddPriceActionComment("📍 Price INSIDE " + ob_type + " ORDER BLOCK - Decision zone",
                                 clrCyan, PRIORITY_INFO, order_blocks[i].time);

            if(order_blocks[i].is_bullish && current_price > prev_close)
            {
                AddPriceActionComment("→ Bullish candle forming in demand zone - Positive sign",
                                     clrLime, PRIORITY_INFO);
            }
            else if(!order_blocks[i].is_bullish && current_price < prev_close)
            {
                AddPriceActionComment("→ Bearish candle forming in supply zone - Positive sign",
                                     clrRed, PRIORITY_INFO);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Analyze Liquidity Sweeps - Detailed sweep commentary             |
//+------------------------------------------------------------------+
void AnalyzeLiquiditySweepsDetailed()
{
    double current_high = iHigh(_Symbol, PreferredTimeframe, 1);
    double current_low = iLow(_Symbol, PreferredTimeframe, 1);
    double current_close = iClose(_Symbol, PreferredTimeframe, 1);
    double prev_high = iHigh(_Symbol, PreferredTimeframe, 2);
    double prev_low = iLow(_Symbol, PreferredTimeframe, 2);

    for(int i = 0; i < liquidity_count; i++)
    {
        if(liquidity_zones[i].swept) continue;

        // Check for liquidity sweep
        if(liquidity_zones[i].is_high)
        {
            // Sellside liquidity (above high)
            if(current_high > liquidity_zones[i].price && current_close < liquidity_zones[i].price)
            {
                liquidity_zones[i].swept = true;
                AddPriceActionComment("💥 SELL-SIDE LIQUIDITY SWEPT at " + DoubleToString(liquidity_zones[i].price, _Digits),
                                     clrOrange, PRIORITY_CRITICAL);
                AddPriceActionComment("→ Stop losses triggered above high - Smart money trapping retail longs",
                                     clrYellow, PRIORITY_IMPORTANT);
                AddPriceActionComment("→ Look for bearish continuation after liquidity grab",
                                     clrAqua, PRIORITY_IMPORTANT);
            }
        }
        else
        {
            // Buyside liquidity (below low)
            if(current_low < liquidity_zones[i].price && current_close > liquidity_zones[i].price)
            {
                liquidity_zones[i].swept = true;
                AddPriceActionComment("💥 BUY-SIDE LIQUIDITY SWEPT at " + DoubleToString(liquidity_zones[i].price, _Digits),
                                     clrDodgerBlue, PRIORITY_CRITICAL);
                AddPriceActionComment("→ Stop losses triggered below low - Smart money trapping retail shorts",
                                     clrYellow, PRIORITY_IMPORTANT);
                AddPriceActionComment("→ Look for bullish continuation after liquidity grab",
                                     clrAqua, PRIORITY_IMPORTANT);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Detect Break of Structure (BOS) and Change of Character (CHoCH)  |
//+------------------------------------------------------------------+
void DetectMarketStructureBreaks()
{
    static double last_structure_high = 0;
    static double last_structure_low = 0;
    static string last_structure_type = "";

    double current_close = iClose(_Symbol, PreferredTimeframe, 1);
    double swing_high = GetSwingHigh(10);
    double swing_low = GetSwingLow(10);

    // Break of Structure (BOS) - Continuation pattern
    if(market_structure.structure == "BULLISH (HH+HL)")
    {
        if(last_structure_type != "BULLISH")
        {
            AddPriceActionComment("📈 BULLISH MARKET STRUCTURE confirmed (Higher Highs + Higher Lows)",
                                 clrLime, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Uptrend intact - Look for pullbacks to enter longs",
                                 clrAqua, PRIORITY_IMPORTANT);
            last_structure_type = "BULLISH";
        }

        // Check for BOS (new higher high)
        if(swing_high > last_structure_high && last_structure_high > 0)
        {
            AddPriceActionComment("🚀 BREAK OF STRUCTURE (BOS) - New Higher High at " + DoubleToString(swing_high, _Digits),
                                 clrLime, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Bullish continuation confirmed - Momentum accelerating",
                                 clrYellow, PRIORITY_IMPORTANT);
        }
        last_structure_high = swing_high;
    }
    else if(market_structure.structure == "BEARISH (LH+LL)")
    {
        if(last_structure_type != "BEARISH")
        {
            AddPriceActionComment("📉 BEARISH MARKET STRUCTURE confirmed (Lower Highs + Lower Lows)",
                                 clrRed, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Downtrend intact - Look for pullbacks to enter shorts",
                                 clrAqua, PRIORITY_IMPORTANT);
            last_structure_type = "BEARISH";
        }

        // Check for BOS (new lower low)
        if(swing_low < last_structure_low || last_structure_low == 0)
        {
            AddPriceActionComment("🔻 BREAK OF STRUCTURE (BOS) - New Lower Low at " + DoubleToString(swing_low, _Digits),
                                 clrRed, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Bearish continuation confirmed - Momentum accelerating",
                                 clrYellow, PRIORITY_IMPORTANT);
        }
        last_structure_low = swing_low;
    }
    else if(market_structure.structure == "CHOPPY")
    {
        // Check for Change of Character (CHoCH) - Potential reversal
        if(last_structure_type == "BULLISH" && swing_low < last_structure_low)
        {
            AddPriceActionComment("⚠ CHANGE OF CHARACTER (CHoCH) - Lower Low detected",
                                 clrOrange, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Bullish structure broken - Potential trend reversal forming",
                                 clrYellow, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Wait for confirmation before entering shorts",
                                 clrCyan, PRIORITY_IMPORTANT);
            last_structure_type = "CHOPPY";
        }
        else if(last_structure_type == "BEARISH" && swing_high > last_structure_high)
        {
            AddPriceActionComment("⚠ CHANGE OF CHARACTER (CHoCH) - Higher High detected",
                                 clrOrange, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Bearish structure broken - Potential trend reversal forming",
                                 clrYellow, PRIORITY_CRITICAL);
            AddPriceActionComment("→ Wait for confirmation before entering longs",
                                 clrCyan, PRIORITY_IMPORTANT);
            last_structure_type = "CHOPPY";
        }
    }
}

//+------------------------------------------------------------------+
//| Analyze Real-Time Price Position - Where is price relative to key levels |
//+------------------------------------------------------------------+
void AnalyzePricePosition()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return;
    double atr = atr_buffer[0];

    // Find nearest liquidity zones
    double nearest_resistance = 0;
    double nearest_support = 0;
    double min_resistance_distance = DBL_MAX;
    double min_support_distance = DBL_MAX;

    for(int i = 0; i < liquidity_count; i++)
    {
        if(liquidity_zones[i].is_high && liquidity_zones[i].price > current_price)
        {
            double distance = liquidity_zones[i].price - current_price;
            if(distance < min_resistance_distance)
            {
                min_resistance_distance = distance;
                nearest_resistance = liquidity_zones[i].price;
            }
        }
        else if(!liquidity_zones[i].is_high && liquidity_zones[i].price < current_price)
        {
            double distance = current_price - liquidity_zones[i].price;
            if(distance < min_support_distance)
            {
                min_support_distance = distance;
                nearest_support = liquidity_zones[i].price;
            }
        }
    }

    // Position commentary
    if(nearest_resistance > 0 && nearest_support > 0)
    {
        double range_size = nearest_resistance - nearest_support;
        double position_pct = ((current_price - nearest_support) / range_size) * 100.0;

        string position_desc = "";
        color position_color = clrWhite;

        if(position_pct < 20)
        {
            position_desc = "LOWER RANGE";
            position_color = clrLime;
            AddPriceActionComment("📍 Price at " + position_desc + " (" + DoubleToString(position_pct, 0) + "% of range)",
                                 position_color, PRIORITY_INFO);
            AddPriceActionComment("→ Near support at " + DoubleToString(nearest_support, _Digits) + " - Watch for bounce",
                                 clrCyan, PRIORITY_INFO);
        }
        else if(position_pct > 80)
        {
            position_desc = "UPPER RANGE";
            position_color = clrRed;
            AddPriceActionComment("📍 Price at " + position_desc + " (" + DoubleToString(position_pct, 0) + "% of range)",
                                 position_color, PRIORITY_INFO);
            AddPriceActionComment("→ Near resistance at " + DoubleToString(nearest_resistance, _Digits) + " - Watch for rejection",
                                 clrCyan, PRIORITY_INFO);
        }
        else
        {
            position_desc = "MID-RANGE";
            position_color = clrYellow;
            AddPriceActionComment("📍 Price in " + position_desc + " (" + DoubleToString(position_pct, 0) + "% between levels)",
                                 position_color, PRIORITY_INFO);
            AddPriceActionComment("→ Between " + DoubleToString(nearest_support, _Digits) + " support and " +
                                 DoubleToString(nearest_resistance, _Digits) + " resistance",
                                 clrCyan, PRIORITY_INFO);
        }
    }

    // Volume context
    if(volume_data.volume_ratio > 2.0)
    {
        AddPriceActionComment("🔊 VOLUME SPIKE (" + DoubleToString(volume_data.volume_ratio, 1) + "x average)",
                             clrOrange, PRIORITY_IMPORTANT);
        AddPriceActionComment("→ High institutional activity - Significant move likely incoming",
                             clrYellow, PRIORITY_INFO);
    }
    else if(volume_data.volume_ratio < 0.5)
    {
        AddPriceActionComment("🔇 Low volume (" + DoubleToString(volume_data.volume_ratio, 1) + "x average)",
                             clrGray, PRIORITY_INFO);
        AddPriceActionComment("→ Lack of conviction - Moves may be unreliable",
                             clrOrange, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| Master Price Action Analysis - Call all analysis functions       |
//+------------------------------------------------------------------+
void PerformPriceActionAnalysis()
{
    // Clear previous commentary
    pa_commentary_count = 0;

    // Note: Server Time and Local Time are displayed as persistent headers in the GUI
    // No need to add them as commentary messages

    // Core price action analysis
    AnalyzePricePosition();
    AnalyzeCandlestickPatterns();
    AnalyzeTrendStrength();
    AnalyzeMomentum();
    AnalyzeSupportResistanceTests();
    DetectConsolidation();
    DetectBreakouts();

    // Smart money concepts
    AnalyzeFVGFills();
    AnalyzeOrderBlockInteractions();
    AnalyzeLiquiditySweepsDetailed();
    DetectMarketStructureBreaks();

    // Session context
    AddPriceActionComment("", clrWhite, PRIORITY_INFO);  // Spacing
    AddPriceActionComment("──── TRADING CONTEXT ────", clrAqua, PRIORITY_INFO);
    AddPriceActionComment("Session: " + session_data.session_name + (session_data.is_tradeable ? " (Active)" : " (Closed)"),
                         session_data.is_tradeable ? clrLime : clrGray, PRIORITY_INFO);

    string vol_text = "Volatility: ";
    switch(current_volatility)
    {
        case VOL_LOW: vol_text += "LOW (Compression - Breakout pending)"; break;
        case VOL_NORMAL: vol_text += "NORMAL"; break;
        case VOL_HIGH: vol_text += "HIGH (Expansion - Be cautious)"; break;
    }
    AddPriceActionComment(vol_text, clrCyan, PRIORITY_INFO);
}

//+------------------------------------------------------------------+