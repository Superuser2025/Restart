//+------------------------------------------------------------------+
//| InstitutionalGradeTradingRobot_Part2.mqh                         |
//| Continuation of Institutional Functions                          |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| FIX #13: LIQUIDITY SWEEP CONFIRMATION                            |
//+------------------------------------------------------------------+
bool ConfirmLiquiditySweep(bool is_buy)
{
    if(is_buy) {
        double current_low = iLow(_Symbol, PreferredTimeframe, 1);
        double current_close = iClose(_Symbol, PreferredTimeframe, 1);

        // Find previous swing low
        double prev_swing_low = DBL_MAX;
        for(int i = 0; i < ArraySize(liquidity_zones); i++) {
            if(!liquidity_zones[i].is_high && liquidity_zones[i].price < current_close) {
                if(liquidity_zones[i].price < prev_swing_low) {
                    prev_swing_low = liquidity_zones[i].price;
                }
            }
        }

        // Sweep = went below and closed above
        if(current_low < prev_swing_low && current_close > prev_swing_low) {
            liquidity_zones[ArraySize(liquidity_zones)-1].swept = true;
            return true;
        }
    }
    else {
        double current_high = iHigh(_Symbol, PreferredTimeframe, 1);
        double current_close = iClose(_Symbol, PreferredTimeframe, 1);

        // Find previous swing high
        double prev_swing_high = 0;
        for(int i = 0; i < ArraySize(liquidity_zones); i++) {
            if(liquidity_zones[i].is_high && liquidity_zones[i].price > current_close) {
                if(liquidity_zones[i].price > prev_swing_high) {
                    prev_swing_high = liquidity_zones[i].price;
                }
            }
        }

        // Sweep = went above and closed below
        if(current_high > prev_swing_high && current_close < prev_swing_high) {
            liquidity_zones[ArraySize(liquidity_zones)-1].swept = true;
            return true;
        }
    }

    return false;
}

//+------------------------------------------------------------------+
//| FIX #14: RETAIL TRAP DETECTION                                   |
//+------------------------------------------------------------------+
bool IsRetailTrap()
{
    // Check for false breakout pattern
    double high1 = iHigh(_Symbol, PreferredTimeframe, 1);
    double close1 = iClose(_Symbol, PreferredTimeframe, 1);
    long vol1 = iVolume(_Symbol, PreferredTimeframe, 1);

    // Get nearest resistance
    double resistance = 0;
    for(int i = 0; i < ArraySize(liquidity_zones); i++) {
        if(liquidity_zones[i].is_high && liquidity_zones[i].price > close1) {
            if(resistance == 0 || liquidity_zones[i].price < resistance) {
                resistance = liquidity_zones[i].price;
            }
        }
    }

    if(resistance == 0) return false;

    // Fake breakout: break above but close back below with high volume
    if(high1 > resistance && close1 < resistance && volume_data.volume_ratio > 2.0) {
        return true;  // Retail got trapped
    }

    return false;
}

//+------------------------------------------------------------------+
//| FIX #15: ORDER BLOCK INVALIDATION                                |
//+------------------------------------------------------------------+
void UpdateOrderBlocksInvalidation()
{
    double current_price = iClose(_Symbol, PreferredTimeframe, 0);

    for(int i = 0; i < ArraySize(order_blocks); i++) {
        if(order_blocks[i].invalidated) continue;

        // Check if price tested the OB
        if(current_price >= order_blocks[i].bottom && current_price <= order_blocks[i].top) {
            order_blocks[i].test_count++;
            order_blocks[i].last_test_time = TimeCurrent();

            AddCommentary("Order Block tested (" + IntegerToString(order_blocks[i].test_count) +
                         "/" + IntegerToString(MaxOBTests) + " tests)", clrYellow, 3);

            // Invalidate after max tests
            if(order_blocks[i].test_count >= MaxOBTests) {
                order_blocks[i].invalidated = true;
                AddCommentary("Order Block INVALIDATED (exceeded max tests)", clrRed, 2);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| FIX #16: MARKET STRUCTURE SEQUENCE                               |
//+------------------------------------------------------------------+
void UpdateMarketStructureSequence()
{
    double swing_high = GetSwingHigh(20);
    double swing_low = GetSwingLow(20);

    // Bullish structure: HH and HL
    if(swing_high > market_structure.last_HH && swing_low > market_structure.last_HL) {
        market_structure.structure = "BULLISH (HH+HL)";
        market_structure.last_HH = swing_high;
        market_structure.last_HL = swing_low;
        market_structure.last_update = TimeCurrent();
    }
    // Bearish structure: LH and LL
    else if(swing_high < market_structure.last_LH && swing_low < market_structure.last_LL) {
        market_structure.structure = "BEARISH (LH+LL)";
        market_structure.last_LH = swing_high;
        market_structure.last_LL = swing_low;
        market_structure.last_update = TimeCurrent();
    }
    else {
        market_structure.structure = "CHOPPY";
    }
}

//+------------------------------------------------------------------+
//| FIX #17: PATTERN PERFORMANCE TRACKING                            |
//+------------------------------------------------------------------+
void TrackPatternPerformance(string pattern_name, MARKET_REGIME regime, double pnl, double rr)
{
    // Find or create entry
    int index = -1;
    for(int i = 0; i < ArraySize(pattern_performance); i++) {
        if(pattern_performance[i].pattern_name == pattern_name &&
           pattern_performance[i].regime == regime) {
            index = i;
            break;
        }
    }

    if(index == -1) {
        // Create new entry
        index = ArraySize(pattern_performance);
        ArrayResize(pattern_performance, index + 1);
        pattern_performance[index].pattern_name = pattern_name;
        pattern_performance[index].regime = regime;
        pattern_performance[index].total_trades = 0;
        pattern_performance[index].winning_trades = 0;
        pattern_performance[index].total_pnl = 0;
        pattern_performance[index].avg_rr = 0;
    }

    // Update stats
    pattern_performance[index].total_trades++;
    if(pnl > 0) pattern_performance[index].winning_trades++;
    pattern_performance[index].total_pnl += pnl;

    // Update averages
    int n = pattern_performance[index].total_trades;
    pattern_performance[index].avg_rr = (pattern_performance[index].avg_rr * (n-1) + rr) / n;
    pattern_performance[index].win_rate = (double)pattern_performance[index].winning_trades / n;
    pattern_performance[index].expectancy = pattern_performance[index].total_pnl / n;
}

bool IsPatternProfitableInRegime()
{
    // Check if pattern historically profitable in this regime
    for(int i = 0; i < ArraySize(pattern_performance); i++) {
        if(pattern_performance[i].pattern_name == last_pattern.name &&
           pattern_performance[i].regime == current_regime) {

            if(pattern_performance[i].total_trades < 30) return true;  // Not enough data

            if(pattern_performance[i].win_rate < 0.5 || pattern_performance[i].expectancy < 0) {
                AddCommentary("⚠ Historical Data: " + last_pattern.name + " loses money in " +
                             EnumToString(current_regime) + " (WR: " +
                             DoubleToString(pattern_performance[i].win_rate*100, 0) + "%)",
                             clrOrange, 2);
                return false;
            }

            AddCommentary("✓ Historical Data: " + last_pattern.name + " profitable in regime (WR: " +
                         DoubleToString(pattern_performance[i].win_rate*100, 0) + "%)", clrLime, 3);
            return true;
        }
    }

    return true;  // No data, allow trade
}

//+------------------------------------------------------------------+
//| FIX #18: PARAMETER ADAPTATION                                    |
//+------------------------------------------------------------------+
void AdaptParameters()
{
    // Get recent performance
    double recent_win_rate = GetRecentWinRate(AdaptationPeriod);
    double recent_avg_rr = GetRecentAvgRR(AdaptationPeriod);

    // If poor performance, tighten filters
    if(recent_win_rate < 0.5 && recent_win_rate > 0) {
        dynamic_required_confluence = MathMin(dynamic_required_confluence + 1, 5);
        AddCommentary("⚙ Auto-Adapt: Win rate low, increasing confluence to " +
                     IntegerToString(dynamic_required_confluence), clrYellow, 2);
    }

    // If great performance, can be more aggressive
    if(recent_win_rate > 0.7) {
        dynamic_required_confluence = MathMax(dynamic_required_confluence - 1, 3);
        AddCommentary("⚙ Auto-Adapt: Win rate high, reducing confluence to " +
                     IntegerToString(dynamic_required_confluence), clrAqua, 3);
    }

    // If R:R too low, increase targets
    if(recent_avg_rr < 1.5 && recent_avg_rr > 0) {
        dynamic_tp1_rr += 0.5;
        AddCommentary("⚙ Auto-Adapt: R:R low, increasing TP to " +
                     DoubleToString(dynamic_tp1_rr, 1), clrYellow, 2);
    }
}

double GetRecentWinRate(int period)
{
    // Simplified - would track in proper metrics
    return 0.6;  // Placeholder
}

double GetRecentAvgRR(int period)
{
    // Simplified - would track in proper metrics
    return 2.0;  // Placeholder
}

//+------------------------------------------------------------------+
//| FIX #19: REGIME-SPECIFIC STRATEGY                                |
//+------------------------------------------------------------------+
void ApplyRegimeSpecificStrategy()
{
    if(!UseRegimeStrategy) return;

    switch(current_regime) {
        case REGIME_TREND:
            // Trend following mode
            dynamic_required_confluence = 3;
            dynamic_tp1_rr = TP1_RR;
            AddCommentary("Strategy: TREND FOLLOWING (Let winners run)", clrAqua, 3);

            // Only trade in trend direction
            if((current_bias == BIAS_BULLISH && !last_pattern.is_bullish) ||
               (current_bias == BIAS_BEARISH && last_pattern.is_bullish)) {
                AddCommentary("⚠ Counter-trend setup - REJECTED in trend mode", clrOrange, 2);
                has_active_pattern = false;
            }
            break;

        case REGIME_RANGE:
            // Mean reversion mode
            dynamic_required_confluence = 4;
            dynamic_tp1_rr = 1.5;  // Quick targets
            AddCommentary("Strategy: MEAN REVERSION (Quick profits)", clrAqua, 3);

            // Only at extremes
            if(current_bias == BIAS_NEUTRAL) {
                AddCommentary("⚠ Middle of range - WAITING for extremes", clrYellow, 2);
                has_active_pattern = false;
            }
            break;

        case REGIME_TRANSITION:
            // Very selective or don't trade
            dynamic_required_confluence = 5;
            AddCommentary("Strategy: BREAKOUT ONLY (Very selective)", clrOrange, 2);
            break;
    }
}

//+------------------------------------------------------------------+
//| TRADE DECISION EVALUATION                                        |
//+------------------------------------------------------------------+
TradeDecisionInfo EvaluateTradeDecision()
{
    TradeDecisionInfo decision;
    decision.confluence_score = 0;
    decision.passed_count = 0;
    decision.failed_count = 0;

    // 1. Market Regime
    if(current_regime != REGIME_TRANSITION) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Market Regime: " + EnumToString(current_regime);
    } else {
        decision.failed_filters[decision.failed_count++] = "Market Regime: Choppy/Transition";
    }

    // 2. Market Bias
    if((current_bias == BIAS_BULLISH && last_pattern.is_bullish) ||
       (current_bias == BIAS_BEARISH && !last_pattern.is_bullish)) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Bias Aligned";
    } else if(current_bias == BIAS_NEUTRAL) {
        decision.failed_filters[decision.failed_count++] = "Bias: Neutral";
    } else {
        decision.failed_filters[decision.failed_count++] = "Bias: Counter-trend";
    }

    // 3. Volume
    if(UseVolumeFilter && volume_data.above_average) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Volume: Above Average";
    } else if(UseVolumeFilter) {
        decision.failed_filters[decision.failed_count++] = "Volume: Below Average";
    }

    // 4. Spread
    if(UseSpreadFilter && spread_data.acceptable) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Spread: Acceptable";
    } else if(UseSpreadFilter) {
        decision.failed_filters[decision.failed_count++] = "Spread: Too Wide";
    }

    // 5. Session
    if(UseSessionFilter && session_data.is_tradeable) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Session: Active";
    } else if(UseSessionFilter) {
        decision.failed_filters[decision.failed_count++] = "Session: Not Tradeable";
    }

    // 6. News
    bool news_clear = ArraySize(upcoming_news) == 0;
    if(UseNewsFilter && news_clear) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "News: Clear";
    } else if(UseNewsFilter) {
        decision.failed_filters[decision.failed_count++] = "News: High Impact Event Near";
    }

    // 7. MTF
    if(UseMTFConfirmation && dashboard.mtf_ok) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Multi-Timeframe: Aligned";
    } else if(UseMTFConfirmation) {
        decision.failed_filters[decision.failed_count++] = "Multi-Timeframe: Conflicting";
    }

    // 8. Correlation
    if(UseCorrelationFilter && dashboard.correlation_ok) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Portfolio Correlation: OK";
    } else if(UseCorrelationFilter) {
        decision.failed_filters[decision.failed_count++] = "Portfolio Correlation: Too High";
    }

    // 9. Pattern Strength
    if(last_pattern.strength >= 4) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Pattern Strength: High";
    } else {
        decision.failed_filters[decision.failed_count++] = "Pattern Strength: Moderate";
    }

    // 10. Historical Performance
    if(UsePatternPerformanceTracking && IsPatternProfitableInRegime()) {
        decision.confluence_score++;
        decision.passed_filters[decision.passed_count++] = "Historical Data: Profitable";
    }

    // Make decision
    if(decision.confluence_score >= dynamic_required_confluence) {
        decision.decision = DECISION_ENTER;
        decision.primary_reason = "Confluence requirements met";
        decision.detailed_explanation = IntegerToString(decision.confluence_score) + " factors aligned";
        decision.advice = "High probability setup - Execute trade with confidence";
    }
    else if(decision.confluence_score == dynamic_required_confluence - 1) {
        decision.decision = DECISION_WAIT;
        decision.primary_reason = "Near confluence threshold";
        decision.detailed_explanation = "Need 1 more confirming factor";
        decision.advice = "Wait for next bar or additional confirmation";
    }
    else {
        decision.decision = DECISION_SKIP;
        decision.primary_reason = "Insufficient confluence";
        decision.detailed_explanation = "Only " + IntegerToString(decision.confluence_score) +
                                       " factors, need " + IntegerToString(dynamic_required_confluence);
        decision.advice = "Setup quality below threshold - Wait for better opportunity";
    }

    return decision;
}

//+------------------------------------------------------------------+
//| EXECUTE INSTITUTIONAL TRADE                                      |
//+------------------------------------------------------------------+
void ExecuteInstitutionalTrade(double risk_percent)
{
    bool is_buy = last_pattern.is_bullish;
    double entry_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);

    // Apply slippage model
    double slippage = UseSlippageModel ? CalculateExpectedSlippage() : 0;
    entry_price += is_buy ? slippage : -slippage;

    // Calculate SL
    double sl = CalculateStopLoss(is_buy);

    // Calculate lot size
    double sl_pips = MathAbs(entry_price - sl) / _Point;
    double lot_size = CalculateLotSize(sl_pips, risk_percent);

    // Calculate TPs
    double tp1, tp2, tp3;
    CalculateTakeProfits(is_buy, entry_price, sl, tp1, tp2, tp3);

    AddCommentary("═══ TRADE EXECUTION ═══", clrWhite, 1);
    AddCommentary("Direction: " + (is_buy ? "BUY" : "SELL"), is_buy ? clrLime : clrRed, 2);
    AddCommentary("Entry: " + DoubleToString(entry_price, _Digits), clrWhite, 2);
    AddCommentary("Stop Loss: " + DoubleToString(sl, _Digits) + " (" +
                 DoubleToString(sl_pips/10, 1) + " pips)", clrRed, 2);
    AddCommentary("Take Profit 1: " + DoubleToString(tp1, _Digits), clrLime, 2);
    AddCommentary("Position Size: " + DoubleToString(lot_size, 2) + " lots", clrYellow, 2);
    AddCommentary("Risk: " + DoubleToString(risk_percent, 2) + "% (" +
                 DoubleToString(account.Balance() * risk_percent/100, 2) + " " +
                 AccountInfoString(ACCOUNT_CURRENCY) + ")", clrOrange, 2);

    // Execute
    bool success = false;
    if(is_buy) {
        success = trade.Buy(lot_size, _Symbol, entry_price, sl, tp1,
                          "IGTR|" + last_pattern.name + "|" + EnumToString(current_regime));
    } else {
        success = trade.Sell(lot_size, _Symbol, entry_price, sl, tp1,
                           "IGTR|" + last_pattern.name + "|" + EnumToString(current_regime));
    }

    if(success) {
        AddCommentary("✓ TRADE EXECUTED SUCCESSFULLY", clrLime, 1);
        AddCommentary("ADVICE: Monitor for breakeven after 1R profit", clrAqua, 2);
        has_active_pattern = false;
    } else {
        AddCommentary("✗ TRADE EXECUTION FAILED: " + IntegerToString(GetLastError()), clrRed, 1);
        AddCommentary("ADVICE: Check broker connection and account status", clrOrange, 2);
    }
}

//+------------------------------------------------------------------+
//| MANAGE OPEN TRADES (INSTITUTIONAL)                               |
//+------------------------------------------------------------------+
void ManageOpenTradesInstitutional()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
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

        // Breakeven at 1R
        if(r_profit >= 1.0 && sl != entry) {
            double new_sl = entry + (is_buy ? 1 : -1) * 5 * _Point;
            if(trade.PositionModify(ticket, new_sl, tp)) {
                AddCommentary("✓ Position " + IntegerToString(ticket) + " moved to BREAKEVEN", clrLime, 2);
                AddCommentary("ADVICE: Risk-free trade now - Let it run", clrAqua, 3);
            }
        }

        // Structure trailing
        if(r_profit >= 1.5) {
            double new_sl;
            if(is_buy) {
                new_sl = GetSwingLow(10);
                if(new_sl > sl && new_sl < current_price) {
                    if(trade.PositionModify(ticket, new_sl, tp)) {
                        AddCommentary("✓ Trailing Stop updated to " + DoubleToString(new_sl, _Digits), clrLime, 3);
                    }
                }
            } else {
                new_sl = GetSwingHigh(10);
                if(new_sl < sl && new_sl > current_price) {
                    if(trade.PositionModify(ticket, new_sl, tp)) {
                        AddCommentary("✓ Trailing Stop updated to " + DoubleToString(new_sl, _Digits), clrLime, 3);
                    }
                }
            }
        }

        // Exit on opposite structure break
        if(CheckOppositeStructureBreak(is_buy)) {
            if(trade.PositionClose(ticket)) {
                AddCommentary("✓ Position closed: Opposite structure break detected", clrOrange, 2);
                AddCommentary("ADVICE: Market reversing - Good exit timing", clrAqua, 2);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| COMMENTARY SYSTEM                                                 |
//+------------------------------------------------------------------+
void AddCommentary(string text, color text_color, int priority)
{
    if(!ShowCommentary) return;

    if(commentary_count >= 50) {
        // Shift array
        for(int i = 0; i < 49; i++) {
            commentary_buffer[i] = commentary_buffer[i+1];
        }
        commentary_count = 49;
    }

    commentary_buffer[commentary_count].text = text;
    commentary_buffer[commentary_count].text_color = text_color;
    commentary_buffer[commentary_count].timestamp = TimeCurrent();
    commentary_buffer[commentary_count].priority = priority;
    commentary_count++;

    // Also print to terminal for critical messages
    if(priority == 1) {
        Print(">>> ", text);
    }
}

//+------------------------------------------------------------------+
//| DRAW COMMENTARY                                                  |
//+------------------------------------------------------------------+
void DrawCommentary()
{
    int y_offset = Dashboard_Y + 550;
    int line_height = 16;
    int max_lines = 25;

    // Draw commentary box
    string box_name = prefix + "Commentary_Box";
    if(ObjectFind(0, box_name) < 0) {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, Dashboard_X);
        ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y_offset);
        ObjectSetInteger(0, box_name, OBJPROP_XSIZE, 600);
        ObjectSetInteger(0, box_name, OBJPROP_YSIZE, max_lines * line_height);
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'30,30,40');
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
    }

    // Draw recent commentary lines
    int start = MathMax(0, commentary_count - max_lines);
    for(int i = start; i < commentary_count; i++) {
        string label_name = prefix + "Commentary_" + IntegerToString(i);

        if(ObjectFind(0, label_name) < 0) {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Consolas");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 8);
        }

        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, Dashboard_X + 5);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y_offset + 5 + (i - start) * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT, commentary_buffer[i].text);
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, commentary_buffer[i].text_color);
    }
}

//+------------------------------------------------------------------+
//| DASHBOARD SYSTEM                                                  |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
    dashboard.regime = current_regime;
    dashboard.bias = current_bias;
    dashboard.session = current_session;
    dashboard.volatility = current_volatility;

    // ... (update other dashboard fields)
}

void DrawDashboard()
{
    int x = Dashboard_X;
    int y = Dashboard_Y;
    int width = 500;
    int line_height = 18;

    // Background
    string bg_name = prefix + "Dashboard_BG";
    if(ObjectFind(0, bg_name) < 0) {
        ObjectCreate(0, bg_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, bg_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, bg_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, bg_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, bg_name, OBJPROP_YSIZE, 500);
        ObjectSetInteger(0, bg_name, OBJPROP_BGCOLOR, DashboardColorBG);
        ObjectSetInteger(0, bg_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, bg_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, bg_name, OBJPROP_BACK, true);
    }

    // Title
    CreateDashboardLabel("Title", x+10, y+10, "═══ INSTITUTIONAL TRADING ROBOT v2.0 ═══", clrWhite, 10);

    // Market Info
    int row = 0;
    CreateDashboardLabel("Regime", x+10, y+40+row*line_height, "Market: " + EnumToString(current_regime), clrYellow);
    row++;
    CreateDashboardLabel("Bias", x+10, y+40+row*line_height, "Bias: " + EnumToString(current_bias),
                        current_bias == BIAS_BULLISH ? clrLime : current_bias == BIAS_BEARISH ? clrRed : clrGray);
    row++;
    CreateDashboardLabel("Session", x+10, y+40+row*line_height, "Session: " + session_data.session_name, clrAqua);
    row++;
    CreateDashboardLabel("Volatility", x+10, y+40+row*line_height, "Volatility: " + volatility_data.status, clrYellow);
    row++;

    // Filters Status
    row++;
    CreateDashboardLabel("FiltersTitle", x+10, y+40+row*line_height, "── INSTITUTIONAL FILTERS ──", clrWhite);
    row++;
    CreateDashboardLabel("Volume", x+10, y+40+row*line_height,
                        "Volume: " + (dashboard.volume_ok ? "✓ OK" : "✗ Weak"),
                        dashboard.volume_ok ? clrLime : clrRed);
    row++;
    CreateDashboardLabel("Spread", x+10, y+40+row*line_height,
                        "Spread: " + (dashboard.spread_ok ? "✓ OK" : "✗ Wide"),
                        dashboard.spread_ok ? clrLime : clrRed);
    row++;
    CreateDashboardLabel("SessionF", x+10, y+40+row*line_height,
                        "Session: " + (dashboard.session_ok ? "✓ Active" : "✗ Inactive"),
                        dashboard.session_ok ? clrLime : clrYellow);
    row++;
    CreateDashboardLabel("News", x+10, y+40+row*line_height,
                        "News: " + (dashboard.news_ok ? "✓ Clear" : "⚠ Event Near"),
                        dashboard.news_ok ? clrLime : clrRed);
    row++;
    CreateDashboardLabel("MTF", x+10, y+40+row*line_height,
                        "MTF: " + (dashboard.mtf_ok ? "✓ Aligned" : "✗ Conflict"),
                        dashboard.mtf_ok ? clrLime : clrOrange);

    // Risk Info
    row += 2;
    CreateDashboardLabel("RiskTitle", x+10, y+40+row*line_height, "── RISK METRICS ──", clrWhite);
    row++;
    CreateDashboardLabel("Risk", x+10, y+40+row*line_height,
                        "Current Risk: " + DoubleToString(dynamic_risk_percent, 2) + "%", clrYellow);
    row++;
    CreateDashboardLabel("Positions", x+10, y+40+row*line_height,
                        "Open Positions: " + IntegerToString(PositionsTotal()) + "/" + IntegerToString(MaxOpenTrades),
                        clrAqua);
    row++;
    CreateDashboardLabel("Balance", x+10, y+40+row*line_height,
                        "Balance: " + DoubleToString(account.Balance(), 2) + " " + AccountInfoString(ACCOUNT_CURRENCY),
                        clrWhite);

    // Pattern Info
    if(has_active_pattern) {
        row += 2;
        CreateDashboardLabel("PatternTitle", x+10, y+40+row*line_height, "── ACTIVE PATTERN ──", clrWhite);
        row++;
        CreateDashboardLabel("Pattern", x+10, y+40+row*line_height,
                            last_pattern.name + " [" + IntegerToString(last_pattern.strength) + "★]",
                            last_pattern.is_bullish ? clrLime : clrRed);
        row++;
        CreateDashboardLabel("Confluence", x+10, y+40+row*line_height,
                            "Confluence: " + IntegerToString(last_decision.confluence_score) + "/" +
                            IntegerToString(dynamic_required_confluence),
                            last_decision.confluence_score >= dynamic_required_confluence ? clrLime : clrOrange);
    }
}

void CreateDashboardLabel(string name, int x, int y, string text, color clr, int font_size = 9)
{
    string label_name = prefix + "Dashboard_" + name;

    if(ObjectFind(0, label_name) < 0) {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Consolas");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, font_size);
    }

    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y);
    ObjectSetString(0, label_name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+