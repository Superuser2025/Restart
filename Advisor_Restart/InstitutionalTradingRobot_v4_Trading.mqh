//+------------------------------------------------------------------+
//| InstitutionalTradingRobot_v4_Trading.mqh                         |
//| Trading Logic Functions + Python ML Export                       |
//+------------------------------------------------------------------+

// Include pattern detection module
#include "CandlestickPatterns.mqh"

//+------------------------------------------------------------------+
//| SCAN FOR CANDLESTICK PATTERNS                                    |
//+------------------------------------------------------------------+
void ScanForCandlestickPatterns()
{
    PatternInfo pattern;
    bool found = false;

    double o[], h[], l[], c[];
    ArraySetAsSeries(o, true);
    ArraySetAsSeries(h, true);
    ArraySetAsSeries(l, true);
    ArraySetAsSeries(c, true);

    if(CopyOpen(_Symbol, PreferredTimeframe, 0, 5, o) <= 0) return;
    if(CopyHigh(_Symbol, PreferredTimeframe, 0, 5, h) <= 0) return;
    if(CopyLow(_Symbol, PreferredTimeframe, 0, 5, l) <= 0) return;
    if(CopyClose(_Symbol, PreferredTimeframe, 0, 5, c) <= 0) return;

    // Check all patterns (from CandlestickPatterns.mqh)
    if(!found) found = DetectHammer(1, o, h, l, c, pattern);
    if(!found) found = DetectShootingStar(1, o, h, l, c, pattern);
    if(!found) found = DetectEngulfing(1, o, h, l, c, pattern);
    if(!found) found = DetectMorningStar(1, o, h, l, c, pattern);
    if(!found) found = DetectEveningStar(1, o, h, l, c, pattern);
    if(!found) found = DetectThreeWhiteSoldiers(1, o, h, l, c, pattern);
    if(!found) found = DetectThreeBlackCrows(1, o, h, l, c, pattern);
    if(!found) found = DetectDoji(1, o, h, l, c, pattern);
    if(!found) found = DetectMarubozu(1, o, h, l, c, pattern);
    if(!found) found = DetectHarami(1, o, h, l, c, pattern);

    if(found && pattern.strength >= 2)
    {
        active_pattern = pattern;
        active_pattern.detected_time = TimeCurrent();
        active_pattern.bar_index = 1;
        has_active_pattern = true;

        // FIX #19: Apply Regime-Specific Strategy
        if(g_UseRegimeStrategy)
            ApplyRegimeStrategy();
    }
    else
    {
        has_active_pattern = false;
    }
}

//+------------------------------------------------------------------+
//| SCAN FOR PATTERNS ON SPECIFIC TIMEFRAME (Multi-TF Support)      |
//+------------------------------------------------------------------+
bool ScanPatternOnTimeframe(ENUM_TIMEFRAMES timeframe, PatternInfo &pattern_out)
{
    PatternInfo pattern;
    bool found = false;

    double o[], h[], l[], c[];
    ArraySetAsSeries(o, true);
    ArraySetAsSeries(h, true);
    ArraySetAsSeries(l, true);
    ArraySetAsSeries(c, true);

    if(CopyOpen(_Symbol, timeframe, 0, 5, o) <= 0) return false;
    if(CopyHigh(_Symbol, timeframe, 0, 5, h) <= 0) return false;
    if(CopyLow(_Symbol, timeframe, 0, 5, l) <= 0) return false;
    if(CopyClose(_Symbol, timeframe, 0, 5, c) <= 0) return false;

    // Check all patterns (from CandlestickPatterns.mqh)
    if(!found) found = DetectHammer(1, o, h, l, c, pattern);
    if(!found) found = DetectShootingStar(1, o, h, l, c, pattern);
    if(!found) found = DetectEngulfing(1, o, h, l, c, pattern);
    if(!found) found = DetectMorningStar(1, o, h, l, c, pattern);
    if(!found) found = DetectEveningStar(1, o, h, l, c, pattern);
    if(!found) found = DetectThreeWhiteSoldiers(1, o, h, l, c, pattern);
    if(!found) found = DetectThreeBlackCrows(1, o, h, l, c, pattern);
    if(!found) found = DetectDoji(1, o, h, l, c, pattern);
    if(!found) found = DetectMarubozu(1, o, h, l, c, pattern);
    if(!found) found = DetectHarami(1, o, h, l, c, pattern);

    if(found && pattern.strength >= 2)
    {
        pattern_out = pattern;
        pattern_out.detected_time = TimeCurrent();
        pattern_out.bar_index = 1;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| SCAN LOWER TIMEFRAMES (H1 and M15)                              |
//+------------------------------------------------------------------+
void ScanLowerTimeframes()
{
    // Scan H1
    has_active_pattern_h1 = ScanPatternOnTimeframe(PERIOD_H1, active_pattern_h1);

    // Scan M15
    has_active_pattern_m15 = ScanPatternOnTimeframe(PERIOD_M15, active_pattern_m15);
}

//+------------------------------------------------------------------+
//| FIX #11: PATTERN VALIDITY CHECK                                  |
//+------------------------------------------------------------------+
bool IsPatternValid()
{
    int bars_since = Bars(_Symbol, PreferredTimeframe, active_pattern.detected_time, TimeCurrent()) - 1;

    if(bars_since > PatternExpiryBars)
        return false;

    return true;
}

//+------------------------------------------------------------------+
//| FIX #19: REGIME-SPECIFIC STRATEGY                                |
//+------------------------------------------------------------------+
void ApplyRegimeStrategy()
{
    if(!g_UseRegimeStrategy) return;

    switch(current_regime)
    {
        case REGIME_TREND:
            // Trend following - only trade with the trend
            dynamic_confluence_required = 3;
            dynamic_tp1 = TP1_RiskReward;

            if((current_bias == BIAS_BULLISH && !active_pattern.is_bullish) ||
               (current_bias == BIAS_BEARISH && active_pattern.is_bullish))
            {
                AddComment("⚠ Counter-trend setup REJECTED in trending market", clrOrange, PRIORITY_IMPORTANT);
                has_active_pattern = false;
            }
            break;

        case REGIME_RANGE:
            // Mean reversion - trade extremes
            dynamic_confluence_required = 4;
            dynamic_tp1 = 1.5;  // Smaller targets

            if(current_bias == BIAS_NEUTRAL)
            {
                AddComment("⚠ Middle of range - Waiting for extremes", clrYellow, PRIORITY_INFO);
                has_active_pattern = false;
            }
            break;

        case REGIME_TRANSITION:
            // Very selective
            dynamic_confluence_required = 5;
            AddComment("⚠ Choppy market - Only high-conviction setups", clrOrange, PRIORITY_IMPORTANT);
            break;
    }
}

//+------------------------------------------------------------------+
//| EVALUATE TRADE DECISION WITH CONFLUENCE                          |
//+------------------------------------------------------------------+
TradeDecision EvaluateTradeDecision()
{
    TradeDecision decision;
    decision.confluence_score = 0;
    decision.passed_count = 0;
    decision.failed_count = 0;

    // 1. Market Regime
    if(current_regime != REGIME_TRANSITION)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Regime: " + EnumToString(current_regime);
    }
    else
    {
        decision.failed_filters[decision.failed_count++] = "Regime: Choppy/Uncertain";
    }

    // 2. Bias Alignment
    if((current_bias == BIAS_BULLISH && active_pattern.is_bullish) ||
       (current_bias == BIAS_BEARISH && !active_pattern.is_bullish))
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Bias: Aligned";
    }
    else if(current_bias == BIAS_NEUTRAL)
    {
        decision.failed_filters[decision.failed_count++] = "Bias: Neutral";
    }
    else
    {
        decision.failed_filters[decision.failed_count++] = "Bias: Counter-trend";
    }

    // 3. Volume (FIX #1)
    if(g_UseVolumeFilter && volume_data.above_threshold)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Volume: Above Threshold";
    }
    else if(g_UseVolumeFilter)
    {
        decision.failed_filters[decision.failed_count++] = "Volume: Below Threshold";
    }

    // 4. Spread (FIX #2)
    if(g_UseSpreadFilter && spread_data.acceptable)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Spread: Acceptable";
    }
    else if(g_UseSpreadFilter)
    {
        decision.failed_filters[decision.failed_count++] = "Spread: Too Wide";
    }

    // 5. Session (FIX #6)
    if(g_UseSessionFilter && session_data.is_tradeable)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Session: Active";
    }
    else if(g_UseSessionFilter)
    {
        decision.failed_filters[decision.failed_count++] = "Session: Not Tradeable";
    }

    // 6. News (FIX #8)
    bool news_clear = (news_count == 0);
    if(g_UseNewsFilter && news_clear)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "News: Clear";
    }
    else if(g_UseNewsFilter)
    {
        decision.failed_filters[decision.failed_count++] = "News: High Impact Near";
    }

    // 7. MTF (FIX #5)
    if(g_UseMTFConfirmation && dashboard.mtf_ok)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "MTF: Aligned";
    }
    else if(g_UseMTFConfirmation)
    {
        decision.failed_filters[decision.failed_count++] = "MTF: Conflicting";
    }

    // 8. Correlation (FIX #7)
    if(g_UseCorrelationFilter && dashboard.correlation_ok)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Correlation: OK";
    }
    else if(g_UseCorrelationFilter)
    {
        decision.failed_filters[decision.failed_count++] = "Correlation: Overexposed";
    }

    // 9. Pattern Strength
    if(active_pattern.strength >= 4)
    {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Pattern: High Strength";
    }
    else
    {
        decision.failed_filters[decision.failed_count++] = "Pattern: Moderate Strength";
    }

    // 10. Historical Performance (FIX #17)
    if(g_UsePatternTracking)
    {
        bool historically_profitable = CheckPatternHistory();
        if(historically_profitable)
        {
            decision.confluence_score++;
            decision.passed_filters[decision.passed_count++] = "History: Profitable";
        }
        else
        {
            decision.failed_filters[decision.failed_count++] = "History: Unprofitable";
        }
    }

    // Make Final Decision
    if(decision.confluence_score >= dynamic_confluence_required)
    {
        decision.decision = DECISION_ENTER;
        decision.primary_reason = "Confluence Met";
        decision.explanation = IntegerToString(decision.confluence_score) + " factors aligned";
        decision.advice = "High probability setup - Execute with confidence";
    }
    else if(decision.confluence_score == dynamic_confluence_required - 1)
    {
        decision.decision = DECISION_WAIT;
        decision.primary_reason = "Near Threshold";
        decision.explanation = "Need 1 more confirmation";
        decision.advice = "Wait for next bar or additional factor";
    }
    else
    {
        decision.decision = DECISION_SKIP;
        decision.primary_reason = "Insufficient Confluence";
        decision.explanation = "Only " + IntegerToString(decision.confluence_score) +
                             " factors, need " + IntegerToString(dynamic_confluence_required);
        decision.advice = "Setup quality below standard - Wait for better opportunity";
    }

    return decision;
}

//+------------------------------------------------------------------+
//| FIX #17: CHECK PATTERN HISTORICAL PERFORMANCE                    |
//+------------------------------------------------------------------+
bool CheckPatternHistory()
{
    for(int i = 0; i < performance_count; i++)
    {
        if(pattern_performance[i].pattern_name == active_pattern.name &&
           pattern_performance[i].regime == current_regime)
        {
            // Need at least 30 trades for statistical significance
            if(pattern_performance[i].total_trades < 30)
                return true;

            // Check if profitable
            if(pattern_performance[i].win_rate >= 0.5)
            {
                AddComment("Historical Win Rate: " + DoubleToString(pattern_performance[i].win_rate * 100, 0) +
                          "%", clrLime, PRIORITY_INFO);
                return true;
            }
            else
            {
                AddComment("Historical Win Rate: " + DoubleToString(pattern_performance[i].win_rate * 100, 0) +
                          "% (Poor)", clrRed, PRIORITY_IMPORTANT);
                return false;
            }
        }
    }

    return true;  // No data, allow trade
}

//+------------------------------------------------------------------+
//| FIX #3: CALCULATE EXPECTED SLIPPAGE                              |
//+------------------------------------------------------------------+
double CalculateExpectedSlippage()
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0)
        return 0.0001;

    return atr_buffer[0] * ExpectedSlippagePercent;
}

//+------------------------------------------------------------------+
//| FIX #10: CALCULATE DYNAMIC RISK                                  |
//+------------------------------------------------------------------+
double CalculateDynamicRisk()
{
    double base_risk = BaseRiskPercent;

    // Track peak balance
    if(account.Balance() > peak_balance)
        peak_balance = account.Balance();

    // Calculate drawdown
    double drawdown = 0;
    if(peak_balance > 0)
        drawdown = (peak_balance - account.Balance()) / peak_balance;

    // Reduce risk during drawdown
    if(drawdown > 0.05)
    {
        base_risk *= (1.0 - drawdown);
        AddComment("Risk Reduced: Drawdown " + DoubleToString(drawdown * 100, 1) +
                  "% → " + DoubleToString(base_risk, 2) + "%", clrOrange, PRIORITY_IMPORTANT);
    }

    // Reduce risk after consecutive losses
    if(consecutive_losses >= 2)
    {
        base_risk *= 0.5;
        AddComment("Risk Reduced: " + IntegerToString(consecutive_losses) +
                  " losses → " + DoubleToString(base_risk, 2) + "%", clrOrange, PRIORITY_IMPORTANT);
    }

    // Adjust for volatility
    if(current_volatility == VOL_HIGH)
        base_risk *= 0.5;

    return MathMax(base_risk, 0.1);  // Minimum 0.1%
}

//+------------------------------------------------------------------+
//| V4 NEW: EXPORT TRADE DATA FOR PYTHON ML ANALYSIS                |
//+------------------------------------------------------------------+
void ExportTradeToPython(string direction, double entry, double sl, double tp,
                         double lot_size, double risk_percent, int confluence_score)
{
    if(!EnablePythonFileExport) return;

    // Create folder if it doesn't exist
    string folder_path = PythonDataFolder + "\\";

    // Build filename with symbol and date
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    string date_str = StringFormat("%04d%02d%02d", dt.year, dt.mon, dt.day);
    string filename = folder_path + _Symbol + "_trades_" + date_str + ".csv";

    // Check if file exists to determine if we need to write header
    bool file_exists = false;
    int check_handle = FileOpen(filename, FILE_READ | FILE_CSV | FILE_ANSI, ',');
    if(check_handle != INVALID_HANDLE)
    {
        file_exists = true;
        FileClose(check_handle);
    }

    // Open file for append
    int handle = FileOpen(filename, FILE_WRITE | FILE_READ | FILE_CSV | FILE_ANSI, ',');
    if(handle == INVALID_HANDLE)
    {
        Print("ERROR: Failed to open Python export file: ", filename, " Error: ", GetLastError());
        return;
    }

    // Move to end of file
    FileSeek(handle, 0, SEEK_END);

    // Write header if new file
    if(!file_exists)
    {
        FileWrite(handle, "Timestamp", "Symbol", "Timeframe", "Direction", "Pattern",
                 "PatternStrength", "Entry", "StopLoss", "TakeProfit", "LotSize",
                 "RiskPercent", "ConfluenceScore", "Regime", "Bias", "Volatility",
                 "Session", "VolumeOK", "SpreadOK", "MTF_OK", "AggressionLevel");
    }

    // Write trade data
    FileWrite(handle,
             TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES),
             _Symbol,
             EnumToString(PreferredTimeframe),
             direction,
             active_pattern.name,
             IntegerToString(active_pattern.strength),
             DoubleToString(entry, _Digits),
             DoubleToString(sl, _Digits),
             DoubleToString(tp, _Digits),
             DoubleToString(lot_size, 2),
             DoubleToString(risk_percent, 2),
             IntegerToString(confluence_score),
             EnumToString(current_regime),
             EnumToString(current_bias),
             EnumToString(current_volatility),
             session_data.session_name,
             dashboard.volume_ok ? "1" : "0",
             dashboard.spread_ok ? "1" : "0",
             dashboard.mtf_ok ? "1" : "0",
             IntegerToString(AggressionLevel));

    FileClose(handle);

    Print("✓ Trade data exported to Python ML: ", filename);
}

//+------------------------------------------------------------------+
//| EXECUTE TRADE                                                     |
//+------------------------------------------------------------------+
void ExecuteTrade(double risk_percent, double slippage)
{
    bool is_buy = active_pattern.is_bullish;
    double entry_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);

    // Apply slippage
    entry_price += is_buy ? slippage : -slippage;

    // Calculate Stop Loss
    double sl = CalculateStopLoss(is_buy);

    // Calculate lot size
    double sl_pips = MathAbs(entry_price - sl) / _Point;
    double lot_size = CalculateLotSize(sl_pips, risk_percent);

    // Calculate Take Profits
    double tp1, tp2, tp3;
    CalculateTakeProfits(is_buy, entry_price, sl, tp1, tp2, tp3);

    AddComment("═══ EXECUTING TRADE ═══", clrWhite, PRIORITY_CRITICAL);
    AddComment("Direction: " + (is_buy ? "BUY" : "SELL"), is_buy ? clrLime : clrRed, PRIORITY_CRITICAL);
    AddComment("Entry: " + DoubleToString(entry_price, _Digits), clrWhite, PRIORITY_IMPORTANT);
    AddComment("Stop Loss: " + DoubleToString(sl, _Digits) + " (" +
              DoubleToString(sl_pips / 10, 1) + " pips)", clrRed, PRIORITY_IMPORTANT);
    AddComment("Take Profit: " + DoubleToString(tp1, _Digits), clrLime, PRIORITY_IMPORTANT);
    AddComment("Position Size: " + DoubleToString(lot_size, 2) + " lots", clrYellow, PRIORITY_IMPORTANT);

    // Execute order
    bool success = false;
    string comment = "IGTR4|" + active_pattern.name + "|" + EnumToString(current_regime) + "|L" + IntegerToString(AggressionLevel);

    if(is_buy)
        success = trade.Buy(lot_size, _Symbol, entry_price, sl, tp1, comment);
    else
        success = trade.Sell(lot_size, _Symbol, entry_price, sl, tp1, comment);

    if(success)
    {
        AddComment("✓ TRADE EXECUTED SUCCESSFULLY", clrLime, PRIORITY_CRITICAL);
        AddComment("ADVICE: Monitor for breakeven move after 1R", clrAqua, PRIORITY_IMPORTANT);

        // V4 NEW: Export trade data for Python ML analysis
        ExportTradeToPython(is_buy ? "BUY" : "SELL", entry_price, sl, tp1, lot_size, risk_percent, last_decision.confluence_score);

        has_active_pattern = false;
    }
    else
    {
        AddComment("✗ TRADE FAILED: " + IntegerToString(GetLastError()), clrRed, PRIORITY_CRITICAL);
        AddComment("ADVICE: Check account balance, margin, and broker connection", clrOrange, PRIORITY_CRITICAL);
    }
}

//+------------------------------------------------------------------+
//| CALCULATE STOP LOSS                                              |
//+------------------------------------------------------------------+
double CalculateStopLoss(bool is_buy)
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0)
        return 0;

    double atr = atr_buffer[0];
    double sl_distance = atr * StopLossATR;
    double entry_price = active_pattern.price;

    double sl_price;
    if(is_buy)
    {
        double swing_low = GetSwingLow(20);
        double atr_sl = entry_price - sl_distance;
        sl_price = MathMin(swing_low - 5 * _Point, atr_sl);
    }
    else
    {
        double swing_high = GetSwingHigh(20);
        double atr_sl = entry_price + sl_distance;
        sl_price = MathMax(swing_high + 5 * _Point, atr_sl);
    }

    return NormalizeDouble(sl_price, _Digits);
}

//+------------------------------------------------------------------+
//| CALCULATE TAKE PROFITS                                           |
//+------------------------------------------------------------------+
void CalculateTakeProfits(bool is_buy, double entry, double sl,
                         double &tp1, double &tp2, double &tp3)
{
    double sl_distance = MathAbs(entry - sl);

    tp1 = entry + (is_buy ? 1 : -1) * sl_distance * dynamic_tp1;
    tp2 = entry + (is_buy ? 1 : -1) * sl_distance * TP2_RiskReward;
    tp3 = entry + (is_buy ? 1 : -1) * sl_distance * TP3_RiskReward;

    tp1 = NormalizeDouble(tp1, _Digits);
    tp2 = NormalizeDouble(tp2, _Digits);
    tp3 = NormalizeDouble(tp3, _Digits);
}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE - DUAL MODE SYSTEM                            |
//+------------------------------------------------------------------+
double CalculateLotSize(double stop_loss_pips, double risk_percent)
{
    double lot_size = 0.0;
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    double broker_min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double broker_max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

    // MODE 1: LOT_SIZE_RANGE - Fixed lot range with min/max bounds
    if(PositionSizingMode == LOT_SIZE_RANGE)
    {
        // Use the minimum lot size as base, can be scaled up to maximum
        // For now, start with minimum and can be adjusted based on confluence/conditions
        lot_size = MinLotSize;

        // Round to lot step
        lot_size = MathFloor(lot_size / lot_step) * lot_step;

        // Enforce user-defined range
        if(lot_size < MinLotSize) lot_size = MinLotSize;
        if(lot_size > MaxLotSize) lot_size = MaxLotSize;

        // Enforce broker limits
        if(lot_size < broker_min_lot) lot_size = broker_min_lot;
        if(lot_size > broker_max_lot) lot_size = broker_max_lot;
    }
    // MODE 2: RISK_PERCENTAGE - Dynamic risk-based calculation
    else if(PositionSizingMode == RISK_PERCENTAGE)
    {
        double capital_risk = account.Balance() * (risk_percent / 100.0);
        double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
        double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
        double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

        double sl_in_price = stop_loss_pips * point;
        double risk_per_lot = (sl_in_price / tick_size) * tick_value;

        lot_size = capital_risk / risk_per_lot;
        lot_size = MathFloor(lot_size / lot_step) * lot_step;

        // Enforce broker limits
        if(lot_size < broker_min_lot) lot_size = broker_min_lot;
        if(lot_size > broker_max_lot) lot_size = broker_max_lot;
    }

    return lot_size;
}

//+------------------------------------------------------------------+
//| CHECK RISK LIMITS                                                |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
    // Check daily reset
    MqlDateTime dt_current, dt_last;
    TimeToStruct(TimeCurrent(), dt_current);
    TimeToStruct(last_daily_reset, dt_last);

    if(dt_current.day != dt_last.day)
    {
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
    }

    // Check weekly reset
    if(dt_current.day_of_week < dt_last.day_of_week ||
       dt_current.day - dt_last.day >= 7)
    {
        weekly_start_balance = account.Balance();
        last_weekly_reset = TimeCurrent();
    }

    // Check daily loss limit
    double daily_loss = ((daily_start_balance - account.Balance()) / daily_start_balance) * 100.0;
    if(daily_loss >= DailyLossLimit)
    {
        AddComment("⛔ DAILY LOSS LIMIT REACHED: " + DoubleToString(daily_loss, 1) + "%", clrRed, PRIORITY_CRITICAL);
        return false;
    }

    // Check weekly loss limit
    double weekly_loss = ((weekly_start_balance - account.Balance()) / weekly_start_balance) * 100.0;
    if(weekly_loss >= WeeklyLossLimit)
    {
        AddComment("⛔ WEEKLY LOSS LIMIT REACHED: " + DoubleToString(weekly_loss, 1) + "%", clrRed, PRIORITY_CRITICAL);
        return false;
    }

    // V4: Check max open trades from aggression level
    if(PositionsTotal() >= active_aggression.max_trades)
    {
        AddComment("⛔ MAX POSITIONS REACHED: " + IntegerToString(PositionsTotal()) +
                  " (Level " + IntegerToString(AggressionLevel) + " limit: " +
                  IntegerToString(active_aggression.max_trades) + ")", clrRed, PRIORITY_CRITICAL);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| MANAGE OPEN TRADES                                               |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!position.SelectByIndex(i)) continue;
        if(position.Symbol() != _Symbol || position.Magic() != MagicNumber) continue;

        ulong ticket = position.Ticket();
        double entry = position.PriceOpen();
        double sl = position.StopLoss();
        double tp = position.TakeProfit();
        bool is_buy = (position.Type() == POSITION_TYPE_BUY);

        double current_price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_BID) :
                                        SymbolInfoDouble(_Symbol, SYMBOL_ASK);

        // Calculate R profit
        double sl_distance = MathAbs(entry - sl);
        double current_profit = is_buy ? (current_price - entry) : (entry - current_price);
        double r_profit = current_profit / sl_distance;

        // Move to breakeven at 1R
        if(r_profit >= 1.0 && sl != entry)
        {
            double new_sl = entry + (is_buy ? 1 : -1) * 5 * _Point;
            if(trade.PositionModify(ticket, new_sl, tp))
            {
                AddComment("✓ Position moved to BREAKEVEN", clrLime, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Risk-free trade - Let it run", clrAqua, PRIORITY_INFO);
            }
        }

        // Trailing stop using structure
        if(r_profit >= 1.5)
        {
            double new_sl;
            if(is_buy)
            {
                new_sl = GetSwingLow(10);
                if(new_sl > sl && new_sl < current_price)
                {
                    if(trade.PositionModify(ticket, new_sl, tp))
                        AddComment("✓ Trailing stop updated", clrLime, PRIORITY_INFO);
                }
            }
            else
            {
                new_sl = GetSwingHigh(10);
                if(new_sl < sl && new_sl > current_price)
                {
                    if(trade.PositionModify(ticket, new_sl, tp))
                        AddComment("✓ Trailing stop updated", clrLime, PRIORITY_INFO);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| FIX #18: PARAMETER ADAPTATION                                    |
//+------------------------------------------------------------------+
void AdaptParameters()
{
    if(!UseParameterAdaptation) return;

    // Simple adaptation based on recent performance
    // In production, use more sophisticated metrics

    if(consecutive_losses >= 3)
    {
        dynamic_confluence_required = MathMin(dynamic_confluence_required + 1, 5);
        AddComment("⚙ Adapting: Increased confluence to " +
                  IntegerToString(dynamic_confluence_required), clrYellow, PRIORITY_INFO);
    }

    if(consecutive_wins >= 5)
    {
        dynamic_confluence_required = MathMax(dynamic_confluence_required - 1, 3);
        AddComment("⚙ Adapting: Reduced confluence to " +
                  IntegerToString(dynamic_confluence_required), clrAqua, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| LOAD PATTERN PERFORMANCE                                         |
//+------------------------------------------------------------------+
void LoadPatternPerformance()
{
    int handle = FileOpen("IGTR4_PatternPerformance_L" + IntegerToString(AggressionLevel) + ".csv", FILE_READ | FILE_CSV | FILE_ANSI, ',');
    if(handle != INVALID_HANDLE)
    {
        performance_count = 0;

        // Skip header line if exists
        string line = FileReadString(handle);

        while(!FileIsEnding(handle) && performance_count < 100)
        {
            pattern_performance[performance_count].pattern_name = FileReadString(handle);
            pattern_performance[performance_count].regime = (MARKET_REGIME)FileReadInteger(handle);
            pattern_performance[performance_count].total_trades = FileReadInteger(handle);
            pattern_performance[performance_count].winning_trades = FileReadInteger(handle);
            pattern_performance[performance_count].total_pnl = FileReadDouble(handle);
            pattern_performance[performance_count].avg_rr = FileReadDouble(handle);
            pattern_performance[performance_count].win_rate = FileReadDouble(handle);

            performance_count++;
        }

        FileClose(handle);
        AddComment("✓ Loaded " + IntegerToString(performance_count) + " performance records", clrAqua, PRIORITY_INFO);
    }
}

//+------------------------------------------------------------------+
//| SAVE PATTERN PERFORMANCE                                         |
//+------------------------------------------------------------------+
void SavePatternPerformance()
{
    int handle = FileOpen("IGTR4_PatternPerformance_L" + IntegerToString(AggressionLevel) + ".csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
    if(handle != INVALID_HANDLE)
    {
        // Write header
        FileWrite(handle, "PatternName", "Regime", "TotalTrades", "WinningTrades", "TotalPnL", "AvgRR", "WinRate");

        // Write data
        for(int i = 0; i < performance_count; i++)
        {
            FileWrite(handle,
                     pattern_performance[i].pattern_name,
                     (int)pattern_performance[i].regime,
                     pattern_performance[i].total_trades,
                     pattern_performance[i].winning_trades,
                     pattern_performance[i].total_pnl,
                     pattern_performance[i].avg_rr,
                     pattern_performance[i].win_rate);
        }

        FileClose(handle);
    }
}

//+------------------------------------------------------------------+