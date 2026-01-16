//+------------------------------------------------------------------+
//| InstitutionalTradingRobot_v3_Trading.mqh                         |
//| Trading Logic Functions                                          |
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
    int bars_since = Bars(_Symbol, g_PreferredTimeframe, active_pattern.detected_time, TimeCurrent()) - 1;

    if(bars_since > g_PatternExpiryBars)
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
//| CHECK FOR DUPLICATE TRADES                                        |
//+------------------------------------------------------------------+
bool IsDuplicateTrade(bool is_buy, string pattern_name)
{
    if(!EnableDuplicateDetection) return false;

    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return false;
    double atr = atr_buffer[0];

    double current_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);

    // Check existing positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() != _Symbol || position.Magic() != MagicNumber) continue;

            // FIX #7: Exclude pyramid positions from duplicate check
            string pos_comment = position.Comment();
            if(StringFind(pos_comment, "PYRAMID|") >= 0)
                continue;  // Skip pyramid positions

            bool pos_is_buy = (position.Type() == POSITION_TYPE_BUY);
            double pos_entry = position.PriceOpen();

            // Same direction within 2 ATR range = duplicate
            if(pos_is_buy == is_buy && MathAbs(pos_entry - current_price) < atr * 2.0)
            {
                AddComment("⚠ DUPLICATE TRADE BLOCKED - Similar position exists at " +
                          DoubleToString(pos_entry, _Digits), clrOrange, PRIORITY_IMPORTANT);
                return true;
            }
        }
    }

    // Check pending orders
    for(int i = 0; i < OrdersTotal(); i++)
    {
        ulong ticket = OrderGetTicket(i);
        if(OrderSelect(ticket))
        {
            if(OrderGetString(ORDER_SYMBOL) != _Symbol ||
               OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;

            ENUM_ORDER_TYPE order_type = (ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
            bool order_is_buy = (order_type == ORDER_TYPE_BUY_LIMIT || order_type == ORDER_TYPE_BUY_STOP);
            double order_price = OrderGetDouble(ORDER_PRICE_OPEN);

            // Same direction within 2 ATR range = duplicate
            if(order_is_buy == is_buy && MathAbs(order_price - current_price) < atr * 2.0)
            {
                AddComment("⚠ DUPLICATE ORDER BLOCKED - Pending order exists at " +
                          DoubleToString(order_price, _Digits), clrOrange, PRIORITY_IMPORTANT);
                return true;
            }
        }
    }

    return false;
}

//+------------------------------------------------------------------+
//| PLACE PENDING ORDER                                              |
//+------------------------------------------------------------------+
bool PlacePendingOrder(bool is_buy, double entry_price, double sl, double tp,
                       double lot_size, string comment)
{
    ENUM_ORDER_TYPE order_type;
    double current_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);

    // Determine order type based on entry price vs current price
    if(is_buy)
    {
        if(entry_price > current_price)
            order_type = ORDER_TYPE_BUY_STOP;   // Buy above current price
        else
            order_type = ORDER_TYPE_BUY_LIMIT;  // Buy below current price
    }
    else
    {
        if(entry_price < current_price)
            order_type = ORDER_TYPE_SELL_STOP;  // Sell below current price
        else
            order_type = ORDER_TYPE_SELL_LIMIT; // Sell above current price
    }

    // Check if this order type is enabled
    if((order_type == ORDER_TYPE_BUY_STOP && !UseBuyStop) ||
       (order_type == ORDER_TYPE_SELL_STOP && !UseSellStop) ||
       (order_type == ORDER_TYPE_BUY_LIMIT && !UseBuyLimit) ||
       (order_type == ORDER_TYPE_SELL_LIMIT && !UseSellLimit))
    {
        AddComment("⚠ Order type " + EnumToString(order_type) + " is disabled", clrOrange, PRIORITY_IMPORTANT);
        return false;
    }

    // Calculate expiration time
    datetime expiration = 0;
    if(g_PendingOrderExpiration > 0)
        expiration = TimeCurrent() + g_PendingOrderExpiration * 3600;

    bool success = trade.OrderOpen(_Symbol, order_type, lot_size, 0, entry_price, sl, tp,
                                   ORDER_TIME_GTC, expiration, comment);

    if(success)
    {
        AddComment("✓ PENDING ORDER PLACED: " + EnumToString(order_type), clrLime, PRIORITY_CRITICAL);
        AddComment("  Entry: " + DoubleToString(entry_price, _Digits), clrWhite, PRIORITY_IMPORTANT);
        AddComment("  Expires: " + (expiration > 0 ? TimeToString(expiration) : "Never"), clrYellow, PRIORITY_INFO);
    }
    else
    {
        AddComment("✗ PENDING ORDER FAILED: " + IntegerToString(GetLastError()), clrRed, PRIORITY_CRITICAL);
    }

    return success;
}

//+------------------------------------------------------------------+
//| TIER 1: FIND BEST STRUCTURE ENTRY PRICE                          |
//+------------------------------------------------------------------+
double FindStructureEntryPrice(bool is_buy, double current_price, string &structure_type)
{
    double best_entry = 0;
    double best_distance = 999999;
    structure_type = "NONE";

    // TIER 1: Search for Order Blocks
    for(int i = 0; i < ob_count; i++)
    {
        if(order_blocks[i].invalidated) continue;

        // For BUY: Look for bullish OB below current price (BUY LIMIT entry)
        if(is_buy && order_blocks[i].is_bullish)
        {
            double ob_top = order_blocks[i].top;
            if(ob_top < current_price)
            {
                double distance = current_price - ob_top;
                if(distance < best_distance)
                {
                    best_entry = ob_top;
                    best_distance = distance;
                    structure_type = "OB_BULL";
                }
            }
        }

        // For SELL: Look for bearish OB above current price (SELL LIMIT entry)
        if(!is_buy && !order_blocks[i].is_bullish)
        {
            double ob_bottom = order_blocks[i].bottom;
            if(ob_bottom > current_price)
            {
                double distance = ob_bottom - current_price;
                if(distance < best_distance)
                {
                    best_entry = ob_bottom;
                    best_distance = distance;
                    structure_type = "OB_BEAR";
                }
            }
        }
    }

    // TIER 1: Search for Fair Value Gaps
    for(int i = 0; i < fvg_count; i++)
    {
        if(fvg_zones[i].filled) continue;

        // For BUY: Look for bullish FVG below current price
        if(is_buy && fvg_zones[i].is_bullish)
        {
            double fvg_bottom = fvg_zones[i].bottom;
            if(fvg_bottom < current_price)
            {
                double distance = current_price - fvg_bottom;
                if(distance < best_distance)
                {
                    best_entry = fvg_bottom;
                    best_distance = distance;
                    structure_type = "FVG_BULL";
                }
            }
        }

        // For SELL: Look for bearish FVG above current price
        if(!is_buy && !fvg_zones[i].is_bullish)
        {
            double fvg_top = fvg_zones[i].top;
            if(fvg_top > current_price)
            {
                double distance = fvg_top - current_price;
                if(distance < best_distance)
                {
                    best_entry = fvg_top;
                    best_distance = distance;
                    structure_type = "FVG_BEAR";
                }
            }
        }
    }

    return best_entry;
}

//+------------------------------------------------------------------+
//| EXECUTE TRADE                                                     |
//+------------------------------------------------------------------+
void ExecuteTrade(double risk_percent, double slippage)
{
    bool is_buy = active_pattern.is_bullish;
    double current_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);
    double entry_price = current_price;  // Initialize at function scope for logging
    int confluence = 0;  // Initialize at function scope for logging
    TradeDecision trade_decision;  // Initialize at function scope for logging confluence factors
    trade_decision.passed_count = 0;
    trade_decision.failed_count = 0;
    trade_decision.confluence_score = 0;

    // ML features at function scope (for both filtering and entry tracking)
    MLFeatureVector ml_features;
    bool ml_features_extracted = false;

    // TIER 2: Time-of-day filtering
    if(UseTimeOfDayFilter)
    {
        MqlDateTime dt;
        TimeToStruct(TimeGMT(), dt);
        int hour = dt.hour;

        if(hour < StartTradingHour || hour >= StopTradingHour)
        {
            AddComment("⏰ Outside trading hours (" + IntegerToString(StartTradingHour) +
                      "-" + IntegerToString(StopTradingHour) + " GMT) - Trade skipped",
                      clrOrange, PRIORITY_IMPORTANT);
            has_active_pattern = false;
            return;
        }
        else
        {
            AddComment("✓ Within trading hours (" + IntegerToString(hour) + ":00 GMT)",
                      clrAqua, PRIORITY_INFO);
        }
    }

    // Check for duplicate
    if(IsDuplicateTrade(is_buy, active_pattern.name))
    {
        has_active_pattern = false;
        return;
    }

    //═══════════════════════════════════════════════════════════════
    // MACHINE LEARNING FILTER (Multi-Symbol File-Based System)
    //═══════════════════════════════════════════════════════════════
    if(g_MLEnabled)
    {
        // Read prediction for current symbol from multi-symbol prediction.json
        if(ml_reader.ReadPrediction(Symbol()))
        {
            // Check if ML approves this trade
            bool ml_approved = ml_reader.ShouldEnterTrade();

            string ml_summary = ml_reader.GetSummary();

            if(!ml_approved)
            {
                AddComment("🤖 ML FILTER: " + ml_summary, clrRed, PRIORITY_CRITICAL);
                AddPriceActionComment("❌ " + ml_summary, clrRed, PRIORITY_CRITICAL, TimeCurrent());
                Print("ML DECISION: Trade rejected for ", Symbol(), " - ", ml_summary);
                has_active_pattern = false;
                return;
            }
            else
            {
                AddComment("🤖 ML APPROVED: " + ml_summary, clrLime, PRIORITY_IMPORTANT);
                AddPriceActionComment("✅ " + ml_summary, clrLime, PRIORITY_IMPORTANT, TimeCurrent());
                Print("ML DECISION: Trade approved for ", Symbol(), " - ", ml_summary);
            }
        }
        else
        {
            AddComment("⚠ ML prediction file not found - proceeding without ML", clrOrange, PRIORITY_INFO);
            Print("WARNING: Could not read ML prediction for ", Symbol(), " - allowing trade (fail-safe mode)");
        }
    }

    // FIX #1: Check if this is a re-entry and apply local parameter adjustments
    bool is_re_entry = false;
    double sl_multiplier = 1.0;
    int confluence_bonus = 0;

    for(int i = 0; i < re_entry_count; i++)
    {
        if(re_entry_patterns[i].re_entry_active)
        {
            is_re_entry = true;
            sl_multiplier = 0.8;  // Tighter SL (80% of normal)
            confluence_bonus = 1;  // Higher confluence requirement

            // Reset flag immediately - only applies to this trade
            re_entry_patterns[i].re_entry_active = false;

            AddComment("→ Applying re-entry parameters: Tighter SL (80%), Higher confluence (+1)",
                      clrAqua, PRIORITY_IMPORTANT);
            break;
        }
    }

    // FIX #9: Calculate spread and factor into entry price
    double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID));
    double spread_adjusted_price = current_price;

    // For BUY: actual entry is at ASK (current_price already is ASK)
    // For SELL: actual entry is at BID (current_price already is BID)
    // But we need to account for spread in SL distance calculation

    // Calculate Stop Loss (with re-entry multiplier if applicable)
    double original_sl_atr = g_StopLossATR;
    if(is_re_entry)
        g_StopLossATR *= sl_multiplier;

    double sl = CalculateStopLoss(is_buy);

    // Reset SL ATR immediately
    g_StopLossATR = original_sl_atr;

    // TIER 1: Dynamic position sizing based on confluence score
    // Always evaluate trade decision for logging confluence factors
    trade_decision = EvaluateTradeDecision();
    confluence = trade_decision.confluence_score + confluence_bonus;  // Apply re-entry bonus

    double adjusted_risk = risk_percent;
    if(UseDynamicPositionSizing)
    {
        // FIX #6: Handle all confluence levels including low ones
        if(confluence >= 9)
        {
            adjusted_risk = 2.0;  // Very high confidence
            AddComment("📊 Dynamic Risk: 2.0% (Confluence: " + IntegerToString(confluence) + ")", clrGreen, PRIORITY_CRITICAL);
        }
        else if(confluence >= 7 && confluence <= 8)
        {
            adjusted_risk = 1.3;  // High confidence
            AddComment("📊 Dynamic Risk: 1.3% (Confluence: " + IntegerToString(confluence) + ")", clrLime, PRIORITY_IMPORTANT);
        }
        else if(confluence >= 5 && confluence <= 6)
        {
            adjusted_risk = 0.8;  // Medium confidence
            AddComment("📊 Dynamic Risk: 0.8% (Confluence: " + IntegerToString(confluence) + ")", clrAqua, PRIORITY_IMPORTANT);
        }
        else if(confluence >= 3 && confluence <= 4)
        {
            adjusted_risk = 0.4;  // Low confidence
            AddComment("📊 Dynamic Risk: 0.4% (Confluence: " + IntegerToString(confluence) + ")", clrYellow, PRIORITY_IMPORTANT);
        }
        else
        {
            // Very low confluence (< 3) - minimal risk or skip
            adjusted_risk = 0.2;  // Very low confidence
            AddComment("📊 Dynamic Risk: 0.2% (Confluence: " + IntegerToString(confluence) + ") - WEAK SIGNAL",
                      clrOrange, PRIORITY_CRITICAL);
            AddComment("⚠ Consider skipping - Confluence below minimum threshold", clrRed, PRIORITY_IMPORTANT);
        }
    }

    // Calculate lot size (factor in spread for actual SL distance)
    double sl_pips = MathAbs(current_price - sl) / _Point;
    double spread_pips = spread / _Point / 10;  // Convert to pips

    // Add spread to SL distance for accurate risk calculation
    sl_pips += spread_pips;

    AddComment("→ Spread: " + DoubleToString(spread_pips, 1) + " pips (factored into risk)",
              clrYellow, PRIORITY_INFO);

    double lot_size = CalculateLotSize(sl_pips, adjusted_risk);

    // Calculate Take Profits
    double tp1, tp2, tp3;
    CalculateTakeProfits(is_buy, current_price, sl, tp1, tp2, tp3);

    string comment = "IGTR3|" + active_pattern.name + "|" + EnumToString(current_regime);

    AddComment("═══ EXECUTING TRADE ═══", clrWhite, PRIORITY_CRITICAL);
    AddComment("Direction: " + (is_buy ? "BUY" : "SELL"), is_buy ? clrLime : clrRed, PRIORITY_CRITICAL);
    AddComment("Stop Loss: " + DoubleToString(sl, _Digits) + " (" +
              DoubleToString(sl_pips / 10, 1) + " pips)", clrRed, PRIORITY_IMPORTANT);
    AddComment("Position Size: " + DoubleToString(lot_size, 2) + " lots", clrYellow, PRIORITY_IMPORTANT);

    bool success = false;

    // Use pending orders if enabled
    if(UsePendingOrders)
    {
        double atr_buffer[];
        ArraySetAsSeries(atr_buffer, true);
        if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) > 0)
        {
            double atr = atr_buffer[0];
            entry_price = 0;  // Reset for pending order calculation
            string structure_type = "";

            // TIER 1: Use smart structure-based placement if enabled
            if(UseSmartPlacement)
            {
                entry_price = FindStructureEntryPrice(is_buy, current_price, structure_type);

                // FIX #5: Validate entry price against broker stops level and spread
                if(entry_price > 0 && MathAbs(entry_price - current_price) <= atr * 3.0)
                {
                    // Check broker minimum distance (SYMBOL_TRADE_STOPS_LEVEL)
                    int stops_level = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
                    double min_distance = stops_level * _Point;

                    // Add spread to minimum distance for safety
                    double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID));
                    min_distance += spread * 2;  // 2× spread for safety margin

                    double entry_distance = MathAbs(entry_price - current_price);

                    if(entry_distance < min_distance)
                    {
                        // Too close to current price - adjust entry
                        if(is_buy)
                            entry_price = (entry_price < current_price) ?
                                        current_price - min_distance :  // LIMIT
                                        current_price + min_distance;   // STOP
                        else
                            entry_price = (entry_price > current_price) ?
                                        current_price + min_distance :  // LIMIT
                                        current_price - min_distance;   // STOP

                        AddComment("🎯 SMART ENTRY (adjusted): " + structure_type + " @ " + DoubleToString(entry_price, _Digits),
                                  clrAqua, PRIORITY_CRITICAL);
                        AddComment("→ Adjusted for broker stops level (" + IntegerToString(stops_level) + " points)",
                                  clrYellow, PRIORITY_INFO);
                    }
                    else
                    {
                        AddComment("🎯 SMART ENTRY at " + structure_type + ": " + DoubleToString(entry_price, _Digits),
                                  clrAqua, PRIORITY_CRITICAL);
                        AddComment("→ Distance: " + DoubleToString(entry_distance / _Point / 10, 1) + " pips",
                                  clrYellow, PRIORITY_IMPORTANT);
                    }
                }
                else
                {
                    // Fallback to ATR-based placement
                    entry_price = 0;
                    structure_type = "ATR_FALLBACK";
                }
            }

            // Fallback to ATR-based placement
            if(entry_price == 0)
            {
                // TIER 2: Volatility-adaptive pending distance
                double pending_multiplier = PendingOrderDistance;

                if(UseVolatilityAdaptive)
                {
                    // Calculate volatility ratio
                    double atr_buffer_long[];
                    ArraySetAsSeries(atr_buffer_long, true);
                    if(CopyBuffer(h_ATR, 0, 0, 20, atr_buffer_long) > 0)
                    {
                        double atr_sum = 0;
                        for(int i = 0; i < 20; i++)
                            atr_sum += atr_buffer_long[i];
                        double atr_avg = atr_sum / 20;
                        double vol_ratio = atr / atr_avg;

                        if(vol_ratio < 0.7)
                        {
                            // Low volatility - tighter distance
                            pending_multiplier = 0.3;
                            AddComment("⚡ Low volatility - Tight pending distance (0.3 × ATR)",
                                      clrAqua, PRIORITY_INFO);
                        }
                        else if(vol_ratio > 1.5)
                        {
                            // High volatility - wider distance
                            pending_multiplier = 0.8;
                            AddComment("⚡ High volatility - Wide pending distance (0.8 × ATR)",
                                      clrOrange, PRIORITY_INFO);
                        }
                        else
                        {
                            // Normal volatility
                            pending_multiplier = 0.5;
                            AddComment("⚡ Normal volatility - Standard distance (0.5 × ATR)",
                                      clrYellow, PRIORITY_INFO);
                        }
                    }
                }

                double pending_distance = atr * pending_multiplier;

                if(is_buy)
                {
                    // For buy: place limit below current price or stop above
                    entry_price = current_price - pending_distance;
                    if(entry_price < current_price)
                        entry_price = current_price - pending_distance;  // BUY LIMIT
                    else
                        entry_price = current_price + pending_distance;  // BUY STOP
                }
                else
                {
                    // For sell: place limit above current price or stop below
                    entry_price = current_price + pending_distance;
                    if(entry_price > current_price)
                        entry_price = current_price + pending_distance;  // SELL LIMIT
                    else
                        entry_price = current_price - pending_distance;  // SELL STOP
                }

                if(structure_type == "ATR_FALLBACK")
                {
                    AddComment("⚠ No structure found - Using volatility-adaptive distance",
                              clrOrange, PRIORITY_IMPORTANT);
                }
            }

            AddComment("Entry (Pending): " + DoubleToString(entry_price, _Digits), clrWhite, PRIORITY_IMPORTANT);
            success = PlacePendingOrder(is_buy, entry_price, sl, tp1, lot_size, comment);
        }
    }
    else
    {
        // Market order execution (only if AllowMarketOrders = true)
        entry_price = current_price + (is_buy ? slippage : -slippage);
        AddComment("Entry (Market): " + DoubleToString(entry_price, _Digits), clrWhite, PRIORITY_IMPORTANT);

        if(is_buy)
            success = trade.Buy(lot_size, _Symbol, 0, sl, tp1, comment);
        else
            success = trade.Sell(lot_size, _Symbol, 0, sl, tp1, comment);
    }

    if(success)
    {
        ulong ticket = trade.ResultOrder();

        // LOG ORDER PLACEMENT TO PRICE ACTION COMMENTARY
        string order_type_text = "";
        if(UsePendingOrders)
        {
            if(is_buy)
                order_type_text = (entry_price > current_price) ? "BUY STOP" : "BUY LIMIT";
            else
                order_type_text = (entry_price < current_price) ? "SELL STOP" : "SELL LIMIT";
        }
        else
        {
            order_type_text = is_buy ? "BUY MARKET" : "SELL MARKET";
        }

        // Add comprehensive order details to Price Action Commentary
        AddPriceActionComment("🎯 ORDER PLACED: " + order_type_text + " #" + IntegerToString(ticket),
                             clrLime, PRIORITY_CRITICAL, TimeCurrent());
        AddPriceActionComment("→ Entry: " + DoubleToString(entry_price, _Digits) +
                             " | SL: " + DoubleToString(sl, _Digits) +
                             " | TP1: " + DoubleToString(tp1, _Digits),
                             clrAqua, PRIORITY_IMPORTANT, TimeCurrent());
        AddPriceActionComment("→ Lot Size: " + DoubleToString(lot_size, 2) +
                             " | Risk: " + DoubleToString(adjusted_risk, 2) + "%" +
                             " | Confluence: " + IntegerToString(confluence),
                             clrYellow, PRIORITY_IMPORTANT, TimeCurrent());
        AddPriceActionComment("→ Pattern: " + active_pattern.name +
                             " | SL Distance: " + DoubleToString(MathAbs(entry_price - sl) / _Point / 10, 1) + " pips",
                             clrAqua, PRIORITY_INFO, TimeCurrent());

        // Log confluence factors (reasons for the trade)
        if(trade_decision.passed_count > 0)
        {
            AddPriceActionComment("→ Trade Conviction - " + IntegerToString(trade_decision.passed_count) + " factors aligned:",
                                 clrGold, PRIORITY_IMPORTANT, TimeCurrent());

            // Log all passed filters
            for(int i = 0; i < trade_decision.passed_count; i++)
            {
                AddPriceActionComment("  ✓ " + trade_decision.passed_filters[i],
                                     clrLightGreen, PRIORITY_INFO, TimeCurrent());
            }
        }

        // Track trade for partial TP management
        if(UsePartialTakeProfit && active_trade_count < 100)
        {
            active_trades[active_trade_count].ticket = ticket;
            active_trades[active_trade_count].entry_price = current_price;
            active_trades[active_trade_count].stop_loss = sl;
            active_trades[active_trade_count].tp1 = tp1;
            active_trades[active_trade_count].tp2 = tp2;
            active_trades[active_trade_count].tp3 = tp3;
            active_trades[active_trade_count].tp1_hit = false;
            active_trades[active_trade_count].tp2_hit = false;
            active_trades[active_trade_count].tp3_hit = false;
            active_trades[active_trade_count].breakeven_moved = false;
            active_trades[active_trade_count].original_lot_size = lot_size;
            active_trades[active_trade_count].open_time = TimeCurrent();
            active_trades[active_trade_count].is_buy = is_buy;
            active_trades[active_trade_count].pattern_name = active_pattern.name;
            active_trades[active_trade_count].pyramid_level = 0;
            active_trades[active_trade_count].re_entry_count = 0;
            active_trades[active_trade_count].best_price_reached = current_price;
            active_trade_count++;
        }

        // ML System: Record trade entry for future labeling
        if(ml_system != NULL && g_MLEnabled && ml_features_extracted)
        {
            ml_system.OnTradeEntry(ml_features, entry_price, sl, is_buy);
        }

        AddComment("✓ ORDER PLACED SUCCESSFULLY", clrLime, PRIORITY_CRITICAL);
        AddComment("ADVICE: Monitor for breakeven move after " + DoubleToString(g_BreakEvenActivationR, 1) + "R", clrAqua, PRIORITY_IMPORTANT);
        has_active_pattern = false;
    }
    else
    {
        AddComment("✗ ORDER FAILED: " + IntegerToString(GetLastError()), clrRed, PRIORITY_CRITICAL);
        AddComment("ADVICE: Check account balance, margin, and broker connection", clrOrange, PRIORITY_CRITICAL);
    }
}

//+------------------------------------------------------------------+
//| TIER 2: FIND ADVANCED SL AT STRUCTURE BOUNDARIES                 |
//+------------------------------------------------------------------+
double FindAdvancedStopLoss(bool is_buy, double entry_price, string &sl_type)
{
    double best_sl = 0;
    sl_type = "NONE";

    // TIER 2: Look for Order Block invalidation points
    for(int i = 0; i < ob_count; i++)
    {
        if(order_blocks[i].invalidated) continue;

        if(is_buy && order_blocks[i].is_bullish)
        {
            // For BUY: SL below bullish OB
            double ob_invalidation = order_blocks[i].bottom - 5 * _Point;
            if(ob_invalidation < entry_price && (best_sl == 0 || ob_invalidation > best_sl))
            {
                best_sl = ob_invalidation;
                sl_type = "OB_INVALIDATION";
            }
        }
        else if(!is_buy && !order_blocks[i].is_bullish)
        {
            // For SELL: SL above bearish OB
            double ob_invalidation = order_blocks[i].top + 5 * _Point;
            if(ob_invalidation > entry_price && (best_sl == 0 || ob_invalidation < best_sl))
            {
                best_sl = ob_invalidation;
                sl_type = "OB_INVALIDATION";
            }
        }
    }

    // TIER 2: Look for FVG boundaries
    for(int i = 0; i < fvg_count; i++)
    {
        if(fvg_zones[i].filled) continue;

        if(is_buy && fvg_zones[i].is_bullish)
        {
            // For BUY: SL below bullish FVG
            double fvg_invalidation = fvg_zones[i].bottom - 5 * _Point;
            if(fvg_invalidation < entry_price && (best_sl == 0 || fvg_invalidation > best_sl))
            {
                best_sl = fvg_invalidation;
                sl_type = "FVG_BOUNDARY";
            }
        }
        else if(!is_buy && !fvg_zones[i].is_bullish)
        {
            // For SELL: SL above bearish FVG
            double fvg_invalidation = fvg_zones[i].top + 5 * _Point;
            if(fvg_invalidation > entry_price && (best_sl == 0 || fvg_invalidation < best_sl))
            {
                best_sl = fvg_invalidation;
                sl_type = "FVG_BOUNDARY";
            }
        }
    }

    // TIER 2: Look for liquidity sweep levels
    for(int i = 0; i < liquidity_count; i++)
    {
        if(is_buy && !liquidity_zones[i].is_high)
        {
            // For BUY: SL below liquidity low
            double liq_sl = liquidity_zones[i].price - 10 * _Point;
            if(liq_sl < entry_price && (best_sl == 0 || liq_sl > best_sl))
            {
                best_sl = liq_sl;
                sl_type = "LIQ_SWEEP";
            }
        }
        else if(!is_buy && liquidity_zones[i].is_high)
        {
            // For SELL: SL above liquidity high
            double liq_sl = liquidity_zones[i].price + 10 * _Point;
            if(liq_sl > entry_price && (best_sl == 0 || liq_sl < best_sl))
            {
                best_sl = liq_sl;
                sl_type = "LIQ_SWEEP";
            }
        }
    }

    return best_sl;
}

//+------------------------------------------------------------------+
//| CALCULATE STOP LOSS                                              |
//+------------------------------------------------------------------+
double CalculateStopLoss(bool is_buy)
{
    double entry_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);
    double sl_price = 0;

    // TIER 2: Use advanced structure-based SL if enabled
    if(UseAdvancedSL)
    {
        string sl_type = "";
        sl_price = FindAdvancedStopLoss(is_buy, entry_price, sl_type);

        // FIX #4: Validate maximum SL distance (3× normal ATR SL)
        if(sl_price > 0)
        {
            double sl_distance = MathAbs(entry_price - sl_price);
            double atr_buffer_check[];
            ArraySetAsSeries(atr_buffer_check, true);
            if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer_check) > 0)
            {
                double atr = atr_buffer_check[0];
                double max_sl_distance = atr * g_StopLossATR * 3.0;  // 3× normal SL

                if(sl_distance > max_sl_distance)
                {
                    AddComment("⚠ Advanced SL too wide (" + DoubleToString(sl_distance / atr, 2) +
                              " ATR) - Using capped distance", clrOrange, PRIORITY_IMPORTANT);
                    // Use max allowed distance instead
                    sl_price = is_buy ? entry_price - max_sl_distance : entry_price + max_sl_distance;
                }
            }

            AddComment("🛡 Advanced SL: " + sl_type + " @ " + DoubleToString(sl_price, _Digits),
                      clrAqua, PRIORITY_IMPORTANT);
            return NormalizeDouble(sl_price, _Digits);
        }
    }

    // Use custom SL if enabled
    if(UseCustomSL)
    {
        double sl_distance = CustomSLPips * _Point * 10;
        sl_price = is_buy ? entry_price - sl_distance : entry_price + sl_distance;
        return NormalizeDouble(sl_price, _Digits);
    }

    // Use ATR-based SL
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0)
        return 0;

    double atr = atr_buffer[0];
    double sl_distance = atr * g_StopLossATR;

    if(UseSwingStopLoss)
    {
        // Use swing high/low for SL
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
    }
    else
    {
        // Pure ATR-based SL
        sl_price = is_buy ? entry_price - sl_distance : entry_price + sl_distance;
    }

    return NormalizeDouble(sl_price, _Digits);
}

//+------------------------------------------------------------------+
//| TIER 1: FIND STRUCTURE-BASED TAKE PROFITS                        |
//+------------------------------------------------------------------+
void FindStructureBasedTPs(bool is_buy, double entry, double sl, double &tp1, double &tp2, double &tp3)
{
    tp1 = 0;
    tp2 = 0;
    tp3 = 0;

    int targets_found = 0;
    double targets[10];
    string target_types[10];

    // Search for Order Blocks in trade direction
    for(int i = 0; i < ob_count && targets_found < 10; i++)
    {
        if(order_blocks[i].invalidated) continue;

        if(is_buy)
        {
            // For BUY: Look for bearish OB above entry (resistance)
            if(!order_blocks[i].is_bullish && order_blocks[i].bottom > entry)
            {
                targets[targets_found] = order_blocks[i].bottom;
                target_types[targets_found] = "OB_RESIST";
                targets_found++;
            }
        }
        else
        {
            // For SELL: Look for bullish OB below entry (support)
            if(order_blocks[i].is_bullish && order_blocks[i].top < entry)
            {
                targets[targets_found] = order_blocks[i].top;
                target_types[targets_found] = "OB_SUPPORT";
                targets_found++;
            }
        }
    }

    // Search for unfilled FVGs
    for(int i = 0; i < fvg_count && targets_found < 10; i++)
    {
        if(fvg_zones[i].filled) continue;

        if(is_buy)
        {
            // For BUY: Look for bearish FVG above entry
            if(!fvg_zones[i].is_bullish && fvg_zones[i].bottom > entry)
            {
                targets[targets_found] = fvg_zones[i].bottom;
                target_types[targets_found] = "FVG_FILL";
                targets_found++;
            }
        }
        else
        {
            // For SELL: Look for bullish FVG below entry
            if(fvg_zones[i].is_bullish && fvg_zones[i].top < entry)
            {
                targets[targets_found] = fvg_zones[i].top;
                target_types[targets_found] = "FVG_FILL";
                targets_found++;
            }
        }
    }

    // Search for liquidity zones
    for(int i = 0; i < liquidity_count && targets_found < 10; i++)
    {
        if(liquidity_zones[i].swept) continue;

        if(is_buy && liquidity_zones[i].is_high && liquidity_zones[i].price > entry)
        {
            targets[targets_found] = liquidity_zones[i].price;
            target_types[targets_found] = "LIQ_HIGH";
            targets_found++;
        }
        else if(!is_buy && !liquidity_zones[i].is_high && liquidity_zones[i].price < entry)
        {
            targets[targets_found] = liquidity_zones[i].price;
            target_types[targets_found] = "LIQ_LOW";
            targets_found++;
        }
    }

    // Sort targets by distance from entry
    for(int i = 0; i < targets_found - 1; i++)
    {
        for(int j = i + 1; j < targets_found; j++)
        {
            double dist_i = MathAbs(targets[i] - entry);
            double dist_j = MathAbs(targets[j] - entry);

            if(dist_j < dist_i)
            {
                // Swap
                double temp_price = targets[i];
                string temp_type = target_types[i];
                targets[i] = targets[j];
                target_types[i] = target_types[j];
                targets[j] = temp_price;
                target_types[j] = temp_type;
            }
        }
    }

    // FIX #3: Assign first 3 targets as TPs with minimum R:R validation
    // Minimum requirements: TP1 >= 1.5R, TP2 >= 2.5R, TP3 >= 4.0R
    double sl_distance = MathAbs(entry - sl);
    if(sl_distance == 0) return;  // Safety check

    double min_tp1_distance = sl_distance * 1.5;
    double min_tp2_distance = sl_distance * 2.5;
    double min_tp3_distance = sl_distance * 4.0;

    if(targets_found >= 1)
    {
        double tp1_distance = MathAbs(targets[0] - entry);
        if(tp1_distance >= min_tp1_distance)
        {
            tp1 = targets[0];
            AddComment("TP1: " + target_types[0] + " @ " + DoubleToString(tp1, _Digits) +
                      " (" + DoubleToString(tp1_distance / sl_distance, 2) + "R)",
                      clrLime, PRIORITY_IMPORTANT);
        }
        else
        {
            AddComment("⚠ " + target_types[0] + " too close (" +
                      DoubleToString(tp1_distance / sl_distance, 2) + "R < 1.5R minimum)",
                      clrOrange, PRIORITY_INFO);
        }
    }
    if(targets_found >= 2)
    {
        double tp2_distance = MathAbs(targets[1] - entry);
        if(tp2_distance >= min_tp2_distance)
        {
            tp2 = targets[1];
            AddComment("TP2: " + target_types[1] + " @ " + DoubleToString(tp2, _Digits) +
                      " (" + DoubleToString(tp2_distance / sl_distance, 2) + "R)",
                      clrLime, PRIORITY_IMPORTANT);
        }
    }
    if(targets_found >= 3)
    {
        double tp3_distance = MathAbs(targets[2] - entry);
        if(tp3_distance >= min_tp3_distance && tp3_distance <= sl_distance * 10.0)  // Max 10R
        {
            tp3 = targets[2];
            AddComment("TP3: " + target_types[2] + " @ " + DoubleToString(tp3, _Digits) +
                      " (" + DoubleToString(tp3_distance / sl_distance, 2) + "R)",
                      clrLime, PRIORITY_IMPORTANT);
        }
        else if(tp3_distance > sl_distance * 10.0)
        {
            AddComment("⚠ " + target_types[2] + " too far (" +
                      DoubleToString(tp3_distance / sl_distance, 2) + "R > 10R maximum)",
                      clrOrange, PRIORITY_INFO);
        }
    }
}

//+------------------------------------------------------------------+
//| CALCULATE TAKE PROFITS                                           |
//+------------------------------------------------------------------+
void CalculateTakeProfits(bool is_buy, double entry, double sl,
                         double &tp1, double &tp2, double &tp3)
{
    // TIER 1: Use structure-based TPs if enabled
    if(UseStructureBasedTP)
    {
        FindStructureBasedTPs(is_buy, entry, sl, tp1, tp2, tp3);

        // Fallback to R:R if not enough structure found
        double sl_distance = MathAbs(entry - sl);

        if(tp1 == 0)
            tp1 = entry + (is_buy ? 1 : -1) * sl_distance * dynamic_tp1;
        if(tp2 == 0)
            tp2 = entry + (is_buy ? 1 : -1) * sl_distance * TP2_RiskReward;
        if(tp3 == 0)
            tp3 = entry + (is_buy ? 1 : -1) * sl_distance * TP3_RiskReward;

        tp1 = NormalizeDouble(tp1, _Digits);
        tp2 = NormalizeDouble(tp2, _Digits);
        tp3 = NormalizeDouble(tp3, _Digits);
        return;
    }

    // Use custom TP if enabled
    if(UseCustomTP)
    {
        double tp1_distance = CustomTP1Pips * _Point * 10;
        double tp2_distance = CustomTP2Pips * _Point * 10;
        double tp3_distance = CustomTP3Pips * _Point * 10;

        tp1 = entry + (is_buy ? tp1_distance : -tp1_distance);
        tp2 = entry + (is_buy ? tp2_distance : -tp2_distance);
        tp3 = entry + (is_buy ? tp3_distance : -tp3_distance);
    }
    else
    {
        // Use risk-reward ratio
        double sl_distance = MathAbs(entry - sl);

        tp1 = entry + (is_buy ? 1 : -1) * sl_distance * dynamic_tp1;
        tp2 = entry + (is_buy ? 1 : -1) * sl_distance * TP2_RiskReward;
        tp3 = entry + (is_buy ? 1 : -1) * sl_distance * TP3_RiskReward;
    }

    tp1 = NormalizeDouble(tp1, _Digits);
    tp2 = NormalizeDouble(tp2, _Digits);
    tp3 = NormalizeDouble(tp3, _Digits);
}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE                                               |
//+------------------------------------------------------------------+
double CalculateLotSize(double stop_loss_pips, double risk_percent)
{
    double capital_risk = account.Balance() * (risk_percent / 100.0);
    double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    double sl_in_price = stop_loss_pips * point;
    double risk_per_lot = (sl_in_price / tick_size) * tick_value;

    double lot_size = capital_risk / risk_per_lot;
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    lot_size = MathFloor(lot_size / lot_step) * lot_step;

    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

    if(lot_size < MinLotSize) lot_size = MinLotSize;
    if(lot_size < min_lot) lot_size = min_lot;
    if(lot_size > max_lot) lot_size = max_lot;

    // Apply max lot per trade limit
    if(lot_size > MaxLotPerTrade)
    {
        AddComment("⚠ Lot size capped at " + DoubleToString(MaxLotPerTrade, 2) + " (Max per trade)",
                  clrOrange, PRIORITY_IMPORTANT);
        lot_size = MaxLotPerTrade;
    }

    // Check max lots per symbol
    double current_symbol_lots = GetSymbolTotalLots();
    if(current_symbol_lots + lot_size > MaxLotsPerSymbol)
    {
        double available = MaxLotsPerSymbol - current_symbol_lots;
        if(available >= min_lot)
        {
            lot_size = MathFloor(available / lot_step) * lot_step;
            AddComment("⚠ Lot size reduced to " + DoubleToString(lot_size, 2) +
                      " (Symbol max: " + DoubleToString(MaxLotsPerSymbol, 2) + ")",
                      clrOrange, PRIORITY_IMPORTANT);
        }
        else
        {
            AddComment("⛔ MAX LOTS FOR SYMBOL REACHED (" + DoubleToString(MaxLotsPerSymbol, 2) + ")",
                      clrRed, PRIORITY_CRITICAL);
            return 0;
        }
    }

    return lot_size;
}

//+------------------------------------------------------------------+
//| GET TOTAL LOTS FOR CURRENT SYMBOL                                |
//+------------------------------------------------------------------+
double GetSymbolTotalLots()
{
    double total_lots = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == MagicNumber)
                total_lots += position.Volume();
        }
    }

    return total_lots;
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

    // Check max open trades
    if(PositionsTotal() >= MaxOpenTrades)
    {
        AddComment("⛔ MAX POSITIONS REACHED: " + IntegerToString(PositionsTotal()), clrRed, PRIORITY_CRITICAL);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| TIER 3: CHECK FOR RE-ENTRY OPPORTUNITIES                         |
//+------------------------------------------------------------------+
void CheckReEntryOpportunities()
{
    if(!UseReEntry) return;

    // Check all tracked re-entry patterns
    for(int i = 0; i < re_entry_count; i++)
    {
        // Skip if max re-entries reached
        if(re_entry_patterns[i].attempts >= MaxReEntries)
            continue;

        // FIX #8: Use time-based delay (1 hour) instead of bars
        int seconds_since = (int)(TimeCurrent() - re_entry_patterns[i].stop_out_time);
        if(seconds_since < 3600)  // Less than 1 hour
            continue;

        // Check if pattern is still valid (market structure intact)
        bool structure_intact = false;
        if(re_entry_patterns[i].is_bullish && current_bias == BIAS_BULLISH)
            structure_intact = true;
        if(!re_entry_patterns[i].is_bullish && current_bias == BIAS_BEARISH)
            structure_intact = true;

        // Check if we're still in same regime
        if(current_regime == REGIME_TRANSITION)
            structure_intact = false;

        if(structure_intact && has_active_pattern &&
           active_pattern.name == re_entry_patterns[i].pattern_name &&
           active_pattern.is_bullish == re_entry_patterns[i].is_bullish)
        {
            // Attempt re-entry with refined parameters
            re_entry_patterns[i].attempts++;

            AddComment("🔄 RE-ENTRY OPPORTUNITY: " + re_entry_patterns[i].pattern_name +
                      " (Attempt " + IntegerToString(re_entry_patterns[i].attempts) + "/" +
                      IntegerToString(MaxReEntries) + ")",
                      clrAqua, PRIORITY_CRITICAL);
            AddComment("→ Structure intact, pattern reconfirmed (1+ hour since stop-out)", clrYellow, PRIORITY_IMPORTANT);

            // FIX #1: Store original values and flag that we're in re-entry mode
            // These will be applied in ExecuteTrade and reset immediately after
            re_entry_patterns[i].re_entry_active = true;

            // Trade will be executed by normal flow with re-entry flag set
            break;
        }
    }

    // Clean up old re-entry patterns (older than 24 hours)
    for(int i = re_entry_count - 1; i >= 0; i--)
    {
        int seconds_since = (int)(TimeCurrent() - re_entry_patterns[i].stop_out_time);
        if(seconds_since > 86400)  // 24 hours
        {
            // Remove from array
            for(int j = i; j < re_entry_count - 1; j++)
                re_entry_patterns[j] = re_entry_patterns[j+1];
            re_entry_count--;
        }
    }
}

//+------------------------------------------------------------------+
//| TIER 3: TRACK STOPPED-OUT TRADE FOR RE-ENTRY                     |
//+------------------------------------------------------------------+
void TrackStoppedOutTrade(string pattern_name, bool is_bullish, double entry_price)
{
    if(!UseReEntry) return;
    if(re_entry_count >= 50) return;  // Max 50 re-entry patterns tracked

    // Check if this pattern is already tracked
    for(int i = 0; i < re_entry_count; i++)
    {
        if(re_entry_patterns[i].pattern_name == pattern_name &&
           re_entry_patterns[i].is_bullish == is_bullish &&
           TimeCurrent() - re_entry_patterns[i].stop_out_time < 3600)  // Within 1 hour
        {
            // Already tracking, don't add duplicate
            return;
        }
    }

    // Add new re-entry pattern
    re_entry_patterns[re_entry_count].pattern_name = pattern_name;
    re_entry_patterns[re_entry_count].is_bullish = is_bullish;
    re_entry_patterns[re_entry_count].stop_out_time = TimeCurrent();
    re_entry_patterns[re_entry_count].attempts = 0;
    re_entry_patterns[re_entry_count].original_entry = entry_price;
    re_entry_patterns[re_entry_count].re_entry_active = false;
    re_entry_count++;

    AddComment("📝 Stopped-out trade tracked for re-entry: " + pattern_name, clrOrange, PRIORITY_INFO);
}

//+------------------------------------------------------------------+
//| MANAGE OPEN TRADES (Enhanced with Partial TP & Trailing)        |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
    // TIER 3: Check for re-entry opportunities first
    CheckReEntryOpportunities();

    // First, manage partial take profits for tracked trades
    if(UsePartialTakeProfit)
    {
        for(int i = active_trade_count - 1; i >= 0; i--)
        {
            // Check if position still exists
            if(!position.SelectByTicket(active_trades[i].ticket))
            {
                // TIER 3: Check if position was stopped out (closed at loss)
                // If it was stopped out, track for potential re-entry
                if(UseReEntry)
                {
                    // Assume stopped out if position no longer exists and no TP3 was hit
                    if(!active_trades[i].tp3_hit && !active_trades[i].tp2_hit)
                    {
                        TrackStoppedOutTrade(active_trades[i].pattern_name,
                                           active_trades[i].is_buy,
                                           active_trades[i].entry_price);
                    }
                }

                // Position closed, remove from tracking
                for(int j = i; j < active_trade_count - 1; j++)
                    active_trades[j] = active_trades[j+1];
                active_trade_count--;
                continue;
            }

            ulong ticket = active_trades[i].ticket;
            double entry = active_trades[i].entry_price;
            double sl = active_trades[i].stop_loss;
            bool is_buy = active_trades[i].is_buy;

            double current_price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_BID) :
                                            SymbolInfoDouble(_Symbol, SYMBOL_ASK);

            double sl_distance = MathAbs(entry - sl);
            double current_profit = is_buy ? (current_price - entry) : (entry - current_price);
            double r_profit = sl_distance > 0 ? current_profit / sl_distance : 0;

            // Check TP1
            if(!active_trades[i].tp1_hit && ((is_buy && current_price >= active_trades[i].tp1) ||
                                             (!is_buy && current_price <= active_trades[i].tp1)))
            {
                double current_volume = position.Volume();
                double close_volume = current_volume * (TP1_ClosePercent / 100.0);
                close_volume = NormalizeDouble(close_volume, 2);

                if(close_volume >= 0.01 && trade.PositionClosePartial(ticket, close_volume))
                {
                    active_trades[i].tp1_hit = true;
                    AddComment("✓ TP1 HIT - Closed " + DoubleToString(TP1_ClosePercent, 0) + "% at " +
                              DoubleToString(active_trades[i].tp1, _Digits), clrLime, PRIORITY_CRITICAL);
                    AddComment("ADVICE: Partial profit secured - Let rest run", clrAqua, PRIORITY_IMPORTANT);
                }
            }

            // Check TP2
            if(active_trades[i].tp1_hit && !active_trades[i].tp2_hit &&
               ((is_buy && current_price >= active_trades[i].tp2) ||
                (!is_buy && current_price <= active_trades[i].tp2)))
            {
                double current_volume = position.Volume();
                double close_volume = current_volume * (TP2_ClosePercent / (100.0 - TP1_ClosePercent) * 100.0);
                close_volume = NormalizeDouble(close_volume, 2);

                if(close_volume >= 0.01 && trade.PositionClosePartial(ticket, close_volume))
                {
                    active_trades[i].tp2_hit = true;
                    AddComment("✓ TP2 HIT - Closed additional " + DoubleToString(TP2_ClosePercent, 0) + "% at " +
                              DoubleToString(active_trades[i].tp2, _Digits), clrLime, PRIORITY_CRITICAL);
                }
            }

            // Check TP3 - Close remaining position
            if(active_trades[i].tp2_hit && !active_trades[i].tp3_hit &&
               ((is_buy && current_price >= active_trades[i].tp3) ||
                (!is_buy && current_price <= active_trades[i].tp3)))
            {
                if(trade.PositionClose(ticket))
                {
                    active_trades[i].tp3_hit = true;
                    AddComment("✓ TP3 HIT - Final " + DoubleToString(TP3_ClosePercent, 0) + "% closed at " +
                              DoubleToString(active_trades[i].tp3, _Digits), clrLime, PRIORITY_CRITICAL);
                    AddComment("ADVICE: Full target reached - Excellent trade!", clrGreen, PRIORITY_IMPORTANT);

                    // Remove from tracking
                    for(int j = i; j < active_trade_count - 1; j++)
                        active_trades[j] = active_trades[j+1];
                    active_trade_count--;
                }
            }
        }
    }

    // Now manage all open positions for trailing stops, breakeven, and pyramiding
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
        if(sl_distance <= 0) continue;

        double current_profit = is_buy ? (current_price - entry) : (entry - current_price);
        double r_profit = current_profit / sl_distance;

        // TIER 3: Pyramiding - Add to winners
        if(UsePyramiding && r_profit >= g_PyramidAddAtR)
        {
            // Find tracked trade
            int tracked_index = -1;
            for(int j = 0; j < active_trade_count; j++)
            {
                if(active_trades[j].ticket == ticket)
                {
                    tracked_index = j;
                    break;
                }
            }

            // Check if we can add another pyramid level
            if(tracked_index >= 0 && active_trades[tracked_index].pyramid_level < MaxPyramidLevels)
            {
                // Update best price reached
                if(is_buy && current_price > active_trades[tracked_index].best_price_reached)
                {
                    active_trades[tracked_index].best_price_reached = current_price;
                }
                else if(!is_buy && current_price < active_trades[tracked_index].best_price_reached)
                {
                    active_trades[tracked_index].best_price_reached = current_price;
                }

                // Only pyramid if price hasn't retraced
                double retrace_threshold = sl_distance * 0.3;  // Allow 30% retrace
                bool can_pyramid = false;

                if(is_buy)
                {
                    can_pyramid = (active_trades[tracked_index].best_price_reached - current_price) < retrace_threshold;
                }
                else
                {
                    can_pyramid = (current_price - active_trades[tracked_index].best_price_reached) < retrace_threshold;
                }

                if(can_pyramid)
                {
                    // Add pyramid position with reduced size (50% of original)
                    double pyramid_lot = active_trades[tracked_index].original_lot_size * 0.5;
                    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
                    pyramid_lot = MathMax(pyramid_lot, min_lot);

                    // Check if adding this would exceed symbol max lots
                    double current_symbol_lots = GetSymbolTotalLots();
                    if(current_symbol_lots + pyramid_lot <= MaxLotsPerSymbol)
                    {
                        bool pyramid_success = false;
                        if(is_buy)
                            pyramid_success = trade.Buy(pyramid_lot, _Symbol, 0, sl, tp, "PYRAMID|" + IntegerToString(ticket));
                        else
                            pyramid_success = trade.Sell(pyramid_lot, _Symbol, 0, sl, tp, "PYRAMID|" + IntegerToString(ticket));

                        if(pyramid_success)
                        {
                            active_trades[tracked_index].pyramid_level++;

                            // FIX #2: Track pyramid position in active_trades array
                            if(active_trade_count < 100)
                            {
                                ulong pyramid_ticket = trade.ResultOrder();

                                active_trades[active_trade_count].ticket = pyramid_ticket;
                                active_trades[active_trade_count].entry_price = current_price;
                                active_trades[active_trade_count].stop_loss = sl;
                                active_trades[active_trade_count].tp1 = tp;
                                active_trades[active_trade_count].tp2 = 0;  // Pyramid shares same TP as base
                                active_trades[active_trade_count].tp3 = 0;
                                active_trades[active_trade_count].tp1_hit = false;
                                active_trades[active_trade_count].tp2_hit = false;
                                active_trades[active_trade_count].tp3_hit = false;
                                active_trades[active_trade_count].breakeven_moved = false;
                                active_trades[active_trade_count].original_lot_size = pyramid_lot;
                                active_trades[active_trade_count].open_time = TimeCurrent();
                                active_trades[active_trade_count].is_buy = is_buy;
                                active_trades[active_trade_count].pattern_name = active_trades[tracked_index].pattern_name + "_PYRAMID";
                                active_trades[active_trade_count].pyramid_level = active_trades[tracked_index].pyramid_level;
                                active_trades[active_trade_count].re_entry_count = 0;
                                active_trades[active_trade_count].best_price_reached = current_price;
                                active_trade_count++;
                            }

                            AddComment("🔺 PYRAMID ADDED at " + DoubleToString(r_profit, 2) + "R - Level " +
                                      IntegerToString(active_trades[tracked_index].pyramid_level),
                                      clrGold, PRIORITY_CRITICAL);
                            AddComment("→ Added " + DoubleToString(pyramid_lot, 2) + " lots to winning position",
                                      clrYellow, PRIORITY_IMPORTANT);
                        }
                    }
                    else
                    {
                        AddComment("⚠ Cannot pyramid - Max symbol lots reached", clrOrange, PRIORITY_INFO);
                    }
                }
            }
        }

        // Move to breakeven
        if(MoveToBreakEven && r_profit >= g_BreakEvenActivationR)
        {
            // Check if not already at breakeven
            bool at_breakeven = (is_buy && sl >= entry) || (!is_buy && sl <= entry);

            if(!at_breakeven)
            {
                double new_sl = entry + (is_buy ? 1 : -1) * 5 * _Point;  // Slightly above/below entry
                if(trade.PositionModify(ticket, new_sl, tp))
                {
                    AddComment("✓ Position moved to BREAKEVEN at " + DoubleToString(r_profit, 2) + "R",
                              clrLime, PRIORITY_IMPORTANT);
                    AddComment("ADVICE: Risk-free trade - Let it run", clrAqua, PRIORITY_INFO);

                    // Mark as breakeven moved in tracking
                    for(int j = 0; j < active_trade_count; j++)
                    {
                        if(active_trades[j].ticket == ticket)
                        {
                            active_trades[j].breakeven_moved = true;
                            break;
                        }
                    }
                }
            }
        }

        // Trailing stop
        if(UseTrailingStop && r_profit >= g_TrailingStopActivationR)
        {
            double new_sl = 0;

            if(UseStructureTrailing)
            {
                // Trail to swing highs/lows
                if(is_buy)
                {
                    new_sl = GetSwingLow(10);
                    if(new_sl > sl && new_sl < current_price)
                    {
                        if(trade.PositionModify(ticket, new_sl, tp))
                            AddComment("✓ Trailing stop updated to swing low: " + DoubleToString(new_sl, _Digits),
                                      clrLime, PRIORITY_INFO);
                    }
                }
                else
                {
                    new_sl = GetSwingHigh(10);
                    if(new_sl < sl && new_sl > current_price)
                    {
                        if(trade.PositionModify(ticket, new_sl, tp))
                            AddComment("✓ Trailing stop updated to swing high: " + DoubleToString(new_sl, _Digits),
                                      clrLime, PRIORITY_INFO);
                    }
                }
            }
            else
            {
                // ATR-based trailing
                double atr_buffer[];
                ArraySetAsSeries(atr_buffer, true);
                if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) > 0)
                {
                    double atr = atr_buffer[0];
                    double trail_distance = atr * TrailingStopDistanceATR;

                    if(is_buy)
                    {
                        new_sl = current_price - trail_distance;
                        if(new_sl > sl)
                        {
                            if(trade.PositionModify(ticket, new_sl, tp))
                                AddComment("✓ ATR trailing stop updated: " + DoubleToString(new_sl, _Digits),
                                          clrLime, PRIORITY_INFO);
                        }
                    }
                    else
                    {
                        new_sl = current_price + trail_distance;
                        if(new_sl < sl)
                        {
                            if(trade.PositionModify(ticket, new_sl, tp))
                                AddComment("✓ ATR trailing stop updated: " + DoubleToString(new_sl, _Digits),
                                          clrLime, PRIORITY_INFO);
                        }
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| CHECK ACCOUNT-LEVEL PROFIT TARGET                                |
//+------------------------------------------------------------------+
bool CheckAccountProfitTarget()
{
    if(!UseAccountProfitTarget) return false;

    double total_profit = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Magic() == MagicNumber)
                total_profit += position.Profit() + position.Swap() + position.Commission();
        }
    }

    if(total_profit >= AccountProfitTarget)
    {
        AddComment("🎯 ACCOUNT PROFIT TARGET REACHED: $" + DoubleToString(total_profit, 2),
                  clrLime, PRIORITY_CRITICAL);
        AddComment("→ Closing all positions to lock in profit", clrYellow, PRIORITY_CRITICAL);

        // Close all positions
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(position.SelectByIndex(i))
            {
                if(position.Magic() == MagicNumber)
                    trade.PositionClose(position.Ticket());
            }
        }

        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| CHECK SYMBOL-LEVEL PROFIT TARGET                                 |
//+------------------------------------------------------------------+
bool CheckSymbolProfitTarget()
{
    if(!UseSymbolProfitTarget) return false;

    double symbol_profit = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == MagicNumber)
                symbol_profit += position.Profit() + position.Swap() + position.Commission();
        }
    }

    if(symbol_profit >= SymbolProfitTarget)
    {
        AddComment("🎯 SYMBOL PROFIT TARGET REACHED: $" + DoubleToString(symbol_profit, 2),
                  clrLime, PRIORITY_CRITICAL);
        AddComment("→ Closing all " + _Symbol + " positions", clrYellow, PRIORITY_CRITICAL);

        // Close symbol positions
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            if(position.SelectByIndex(i))
            {
                if(position.Symbol() == _Symbol && position.Magic() == MagicNumber)
                    trade.PositionClose(position.Ticket());
            }
        }

        return true;
    }

    return false;
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
    int handle = FileOpen("IGTR3_PatternPerformance.csv", FILE_READ | FILE_CSV | FILE_ANSI, ',');
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
    int handle = FileOpen("IGTR3_PatternPerformance.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
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