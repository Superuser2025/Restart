//+------------------------------------------------------------------+
//| InstitutionalTradingRobot_v3_Visual.mqh                          |
//| Visualization Functions - Dashboard & Commentary                 |
//+------------------------------------------------------------------+

// Forward declarations
void CreateLabel(string name, int x, int y, string text, color clr, int font_size = 11);

//+------------------------------------------------------------------+
//| UPDATE DASHBOARD DATA                                            |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
    dashboard.regime = current_regime;
    dashboard.bias = current_bias;
    dashboard.session = current_session;
    dashboard.volatility = current_volatility;
    dashboard.daily_pnl = account.Balance() - daily_start_balance;
    dashboard.open_trades = PositionsTotal();
    dashboard.current_risk = dynamic_risk_percent;

    if(has_active_pattern)
    {
        dashboard.last_pattern = active_pattern.name;
        dashboard.confluence_score = last_decision.confluence_score;
    }
    else
    {
        dashboard.last_pattern = "None";
        dashboard.confluence_score = 0;
    }

    // Calculate win rate (simplified)
    dashboard.win_rate = 0.0;
    int total_wins = 0;
    int total_trades = 0;
    for(int i = 0; i < performance_count; i++)
    {
        total_trades += pattern_performance[i].total_trades;
        total_wins += pattern_performance[i].winning_trades;
    }
    if(total_trades > 0)
        dashboard.win_rate = (double)total_wins / total_trades;
}

//+------------------------------------------------------------------+
//| DRAW DASHBOARD                                                    |
//+------------------------------------------------------------------+
void DrawDashboard()
{
    if(!g_ShowDashboard)
    {
        // Hide dashboard
        string bg_name = prefix + "Dashboard_BG";
        ObjectDelete(0, bg_name);
        // Delete all dashboard labels too
        for(int i = 0; i < 100; i++)
        {
            ObjectDelete(0, prefix + "D_" + IntegerToString(i));
        }
        return;
    }

    // Dashboard (Market Status) positioned under Real-Time Analysis
    int x = 320;   // Aligned with Real-Time Analysis
    int y = 880;   // Below Real-Time Analysis (which ends around y=870)
    int width = 400;
    int line_height = 22;  // BIGGER line height

    // Background box
    string bg_name = prefix + "Dashboard_BG";
    if(ObjectFind(0, bg_name) < 0)
    {
        ObjectCreate(0, bg_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, bg_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, bg_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, bg_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, bg_name, OBJPROP_YSIZE, 480);
        ObjectSetInteger(0, bg_name, OBJPROP_BGCOLOR, ColorBackground);
        ObjectSetInteger(0, bg_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, bg_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, bg_name, OBJPROP_BACK, true);
    }

    // Title
    CreateLabel("Title", x+10, y+10,
               "═══ MARKET STATUS ═══",
               clrWhite, 13);

    int row = 0;

    // Market Context Section
    row++;
    CreateLabel("Header1", x+10, y+40+row*line_height,
               "── MARKET CONTEXT ──", clrAqua, 12);
    row++;

    string regime_text = "Regime: ";
    color regime_color = clrWhite;
    switch(current_regime)
    {
        case REGIME_TREND:
            regime_text += "TRENDING";
            regime_color = clrLime;
            break;
        case REGIME_RANGE:
            regime_text += "RANGING";
            regime_color = clrYellow;
            break;
        case REGIME_TRANSITION:
            regime_text += "CHOPPY";
            regime_color = clrOrange;
            break;
    }
    CreateLabel("Regime", x+10, y+40+row*line_height, regime_text, regime_color, FontSize);
    row++;

    string bias_text = "Bias: ";
    color bias_color = clrWhite;
    switch(current_bias)
    {
        case BIAS_BULLISH:
            bias_text += "BULLISH";
            bias_color = clrLime;
            break;
        case BIAS_BEARISH:
            bias_text += "BEARISH";
            bias_color = clrRed;
            break;
        case BIAS_NEUTRAL:
            bias_text += "NEUTRAL";
            bias_color = clrGray;
            break;
    }
    CreateLabel("Bias", x+10, y+40+row*line_height, bias_text, bias_color, FontSize);
    row++;

    CreateLabel("Session", x+10, y+40+row*line_height,
               "Session: " + session_data.session_name,
               session_data.is_tradeable ? clrLime : clrGray, FontSize);
    row++;

    string vol_text = "Volatility: ";
    switch(current_volatility)
    {
        case VOL_LOW:
            vol_text += "LOW";
            break;
        case VOL_NORMAL:
            vol_text += "NORMAL";
            break;
        case VOL_HIGH:
            vol_text += "HIGH";
            break;
    }
    CreateLabel("Volatility", x+10, y+40+row*line_height, vol_text, clrYellow, FontSize);
    row++;

    CreateLabel("Structure", x+10, y+40+row*line_height,
               "Structure: " + market_structure.structure, clrWhite, FontSize);
    row++;

    // Filters Section
    row++;
    CreateLabel("Header2", x+10, y+40+row*line_height,
               "── FILTER STATUS ──", clrAqua, 12);
    row++;

    CreateLabel("Volume", x+10, y+40+row*line_height,
               "Volume: " + (dashboard.volume_ok ? "✓ OK" : "✗ Weak"),
               dashboard.volume_ok ? clrLime : clrRed, FontSize);
    row++;

    CreateLabel("Spread", x+10, y+40+row*line_height,
               "Spread: " + (dashboard.spread_ok ? "✓ OK" : "✗ Wide"),
               dashboard.spread_ok ? clrLime : clrRed, FontSize);
    row++;

    CreateLabel("SessionF", x+10, y+40+row*line_height,
               "Session: " + (dashboard.session_ok ? "✓ Active" : "✗ Closed"),
               dashboard.session_ok ? clrLime : clrGray, FontSize);
    row++;

    CreateLabel("News", x+10, y+40+row*line_height,
               "News: " + (dashboard.news_ok ? "✓ Clear" : "⚠ Event"),
               dashboard.news_ok ? clrLime : clrRed, FontSize);
    row++;

    CreateLabel("MTF", x+10, y+40+row*line_height,
               "MTF: " + (dashboard.mtf_ok ? "✓ Aligned" : "✗ Conflict"),
               dashboard.mtf_ok ? clrLime : clrOrange, FontSize);
    row++;

    CreateLabel("Correlation", x+10, y+40+row*line_height,
               "Correlation: " + (dashboard.correlation_ok ? "✓ OK" : "✗ High"),
               dashboard.correlation_ok ? clrLime : clrRed, FontSize);
    row++;

    // Risk Section
    row++;
    CreateLabel("Header3", x+10, y+40+row*line_height,
               "── RISK METRICS ──", clrAqua, 12);
    row++;

    CreateLabel("Risk", x+10, y+40+row*line_height,
               "Current Risk: " + DoubleToString(dashboard.current_risk, 2) + "%",
               clrYellow, FontSize);
    row++;

    CreateLabel("Positions", x+10, y+40+row*line_height,
               "Open Positions: " + IntegerToString(dashboard.open_trades) + "/" +
               IntegerToString(MaxOpenTrades), clrAqua, FontSize);
    row++;

    CreateLabel("Balance", x+10, y+40+row*line_height,
               "Balance: " + DoubleToString(account.Balance(), 2) + " " +
               AccountInfoString(ACCOUNT_CURRENCY), clrWhite, FontSize);
    row++;

    string pnl_text = "Daily P/L: " + DoubleToString(dashboard.daily_pnl, 2) + " " +
                     AccountInfoString(ACCOUNT_CURRENCY);
    CreateLabel("DailyPNL", x+10, y+40+row*line_height, pnl_text,
               dashboard.daily_pnl >= 0 ? clrLime : clrRed, FontSize);
    row++;

    // Pattern Section
    if(has_active_pattern)
    {
        row++;
        CreateLabel("Header4", x+10, y+40+row*line_height,
                   "── ACTIVE PATTERN ──", clrAqua, 12);
        row++;

        CreateLabel("Pattern", x+10, y+40+row*line_height,
                   "(H4) " + active_pattern.name + " [" + IntegerToString(active_pattern.strength) + "★]",
                   active_pattern.is_bullish ? clrLime : clrRed, FontSize);
        row++;

        CreateLabel("Confluence", x+10, y+40+row*line_height,
                   "Confluence: " + IntegerToString(dashboard.confluence_score) + "/" +
                   IntegerToString(dynamic_confluence_required),
                   dashboard.confluence_score >= dynamic_confluence_required ? clrLime : clrOrange,
                   FontSize);
        row++;

        // Show H1 pattern if different from H4
        if(has_active_pattern_h1 && active_pattern_h1.name != active_pattern.name)
        {
            CreateLabel("PatternH1", x+10, y+40+row*line_height,
                       "(H1) " + active_pattern_h1.name + " [" + IntegerToString(active_pattern_h1.strength) + "★]",
                       active_pattern_h1.is_bullish ? clrLime : clrRed, FontSize);
            row++;
        }

        // Show M15 pattern if different from H4
        if(has_active_pattern_m15 && active_pattern_m15.name != active_pattern.name)
        {
            CreateLabel("PatternM15", x+10, y+40+row*line_height,
                       "(M15) " + active_pattern_m15.name + " [" + IntegerToString(active_pattern_m15.strength) + "★]",
                       active_pattern_m15.is_bullish ? clrLime : clrRed, FontSize);
            row++;
        }
    }
    else
    {
        // No H4 pattern, but show H1 and M15 if they exist
        if(has_active_pattern_h1 || has_active_pattern_m15)
        {
            row++;
            CreateLabel("Header4", x+10, y+40+row*line_height,
                       "── ACTIVE PATTERN ──", clrAqua, 12);
            row++;

            if(has_active_pattern_h1)
            {
                CreateLabel("PatternH1Only", x+10, y+40+row*line_height,
                           "(H1) " + active_pattern_h1.name + " [" + IntegerToString(active_pattern_h1.strength) + "★]",
                           active_pattern_h1.is_bullish ? clrLime : clrRed, FontSize);
                row++;
            }

            if(has_active_pattern_m15)
            {
                CreateLabel("PatternM15Only", x+10, y+40+row*line_height,
                           "(M15) " + active_pattern_m15.name + " [" + IntegerToString(active_pattern_m15.strength) + "★]",
                           active_pattern_m15.is_bullish ? clrLime : clrRed, FontSize);
                row++;
            }
        }
    }

    // Performance Section
    if(performance_count > 0)
    {
        row++;
        CreateLabel("Header5", x+10, y+40+row*line_height,
                   "── PERFORMANCE ──", clrAqua, 12);
        row++;

        CreateLabel("WinRate", x+10, y+40+row*line_height,
                   "Win Rate: " + DoubleToString(dashboard.win_rate * 100, 1) + "%",
                   dashboard.win_rate >= 0.5 ? clrLime : clrRed, FontSize);
        row++;
    }

    // Mode Indicator - now shown via button, can skip or make smaller
    row++;
    if(!g_EnableTrading)
    {
        CreateLabel("Mode", x+10, y+40+row*line_height,
                   "⚠ INDICATOR MODE ⚠", clrOrange, 13);
    }
    else
    {
        CreateLabel("Mode", x+10, y+40+row*line_height,
                   "✓ TRADING ACTIVE", clrLime, 13);
    }
}

//+------------------------------------------------------------------+
//| DRAW COMMENTARY                                                   |
//+------------------------------------------------------------------+
void DrawCommentary()
{
    int x = Dashboard_X;
    int y = Dashboard_Y + 500;
    int width = 600;
    int line_height = 16;
    int max_lines = 25;

    // Background box
    string box_name = prefix + "Commentary_Box";
    if(ObjectFind(0, box_name) < 0)
    {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, box_name, OBJPROP_YSIZE, max_lines * line_height);
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'30,30,40');
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
    }

    // Draw commentary lines
    int start_index = MathMax(0, commentary_count - max_lines);

    for(int i = start_index; i < commentary_count; i++)
    {
        string label_name = prefix + "Comment_" + IntegerToString(i);

        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Consolas");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 8);
        }

        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 5);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y + 5 + (i - start_index) * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT, commentary_buffer[i].text);
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, commentary_buffer[i].text_color);
    }
}

//+------------------------------------------------------------------+
//| CREATE DASHBOARD LABEL                                           |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int font_size = 11)
{
    string label_name = prefix + "DB_" + name;

    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");  // More readable
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, font_size);
    }

    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y);
    ObjectSetString(0, label_name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| DRAW LIQUIDITY ZONES                                             |
//+------------------------------------------------------------------+
void DrawLiquidityZones()
{
    if(!g_ShowLiquidityZones)
    {
        // Hide all liquidity zones
        for(int i = 0; i < liquidity_count; i++)
        {
            string name = prefix + "LIQ_" + IntegerToString(i);
            ObjectDelete(0, name);
        }
        return;
    }

    for(int i = 0; i < liquidity_count; i++)
    {
        string name = prefix + "LIQ_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            ObjectCreate(0, name, OBJ_HLINE, 0, 0, liquidity_zones[i].price);
            ObjectSetInteger(0, name, OBJPROP_COLOR,
                           liquidity_zones[i].is_high ? clrRed : clrBlue);
            ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);
            ObjectSetInteger(0, name, OBJPROP_WIDTH,
                           liquidity_zones[i].swept ? 2 : 1);
            ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
        }
    }
}

//+------------------------------------------------------------------+
//| DRAW FAIR VALUE GAPS                                             |
//+------------------------------------------------------------------+
void DrawFVGZones()
{
    if(!g_ShowFVGZones)
    {
        // Hide all FVG zones
        for(int i = 0; i < fvg_count; i++)
        {
            string name = prefix + "FVG_" + IntegerToString(i);
            ObjectDelete(0, name);
        }
        return;
    }

    for(int i = 0; i < fvg_count; i++)
    {
        if(fvg_zones[i].filled) continue;

        string name = prefix + "FVG_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            datetime time_now = TimeCurrent();
            datetime time_end = time_now + PeriodSeconds(g_PreferredTimeframe) * 50;

            ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                        fvg_zones[i].time, fvg_zones[i].top,
                        time_end, fvg_zones[i].bottom);

            ObjectSetInteger(0, name, OBJPROP_COLOR,
                           fvg_zones[i].is_bullish ? clrLightGreen : clrLightPink);
            ObjectSetInteger(0, name, OBJPROP_BACK, true);
            ObjectSetInteger(0, name, OBJPROP_FILL, true);
            ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
        }
    }
}

//+------------------------------------------------------------------+
//| DRAW ORDER BLOCKS                                                |
//+------------------------------------------------------------------+
void DrawOrderBlocks()
{
    if(!g_ShowOrderBlocks)
    {
        // Hide all order blocks
        for(int i = 0; i < ob_count; i++)
        {
            string name = prefix + "OB_" + IntegerToString(i);
            ObjectDelete(0, name);
        }
        return;
    }

    for(int i = 0; i < ob_count; i++)
    {
        if(order_blocks[i].invalidated) continue;

        string name = prefix + "OB_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            datetime time_now = TimeCurrent();
            datetime time_end = time_now + PeriodSeconds(g_PreferredTimeframe) * 50;

            ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                        order_blocks[i].time, order_blocks[i].top,
                        time_end, order_blocks[i].bottom);

            ObjectSetInteger(0, name, OBJPROP_COLOR,
                           order_blocks[i].is_bullish ? C'0,100,0' : clrCrimson);
            ObjectSetInteger(0, name, OBJPROP_BACK, true);
            ObjectSetInteger(0, name, OBJPROP_FILL, true);
            ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
        }
    }
}

//+------------------------------------------------------------------+
//| DRAW PATTERN BOX                                                 |
//+------------------------------------------------------------------+
void DrawPatternBox(PatternInfo &p)
{
    datetime time = iTime(_Symbol, g_PreferredTimeframe, p.bar_index);
    string name = prefix + "BOX_" + TimeToString(time);

    if(!g_ShowPatternBoxes)
    {
        ObjectDelete(0, name);
        return;
    }

    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);
    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return;

    double atr = atr_buffer[0];
    double top = p.price + atr;
    double bottom = p.price - atr;
    datetime time_end = time + PeriodSeconds(g_PreferredTimeframe);

    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_RECTANGLE, 0, time, top, time_end, bottom);
        ObjectSetInteger(0, name, OBJPROP_COLOR,
                       p.is_bullish ? clrLime : clrRed);
        ObjectSetInteger(0, name, OBJPROP_BACK, false);
        ObjectSetInteger(0, name, OBJPROP_FILL, false);
        ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
        ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
    }
}

//+------------------------------------------------------------------+
//| DRAW PATTERN LABEL                                               |
//+------------------------------------------------------------------+
void DrawPatternLabel(PatternInfo &p)
{
    datetime time = iTime(_Symbol, g_PreferredTimeframe, p.bar_index);
    string name = prefix + "LABEL_" + TimeToString(time);

    if(!g_ShowPatternLabels)
    {
        ObjectDelete(0, name);
        return;
    }

    double price = p.is_bullish ?
                  iLow(_Symbol, g_PreferredTimeframe, p.bar_index) - 10 * _Point :
                  iHigh(_Symbol, g_PreferredTimeframe, p.bar_index) + 10 * _Point;

    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_TEXT, 0, time, price);
        ObjectSetString(0, name, OBJPROP_TEXT, p.name + " [" + IntegerToString(p.strength) + "★]");
        ObjectSetInteger(0, name, OBJPROP_COLOR,
                       p.is_bullish ? clrLime : clrRed);
        ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
    }
}

//+------------------------------------------------------------------+