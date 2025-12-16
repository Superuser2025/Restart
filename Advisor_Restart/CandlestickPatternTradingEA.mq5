//+------------------------------------------------------------------+
//|                                  CandlestickPatternTradingEA.mq5 |
//|                                      Copyright 2025, Pankhuri    |
//|                         Professional Institutional Trading EA     |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Pankhuri"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                   |
//+------------------------------------------------------------------+
input group "===== GENERAL SETTINGS ====="
input bool     EnableTrading = true;                    // Enable Auto Trading
input bool     IndicatorMode = false;                   // Indicator Mode (Show Patterns Only)
input double   MinLotSize = 0.01;                       // Minimum Lot Size
input int      MagicNumber = 888777;                    // Magic Number

input group "===== PHASE 1: MARKET REGIME ====="
input int      EMA_Period = 200;                        // EMA Period for Trend Detection
input int      ATR_Period = 14;                         // ATR Period
input double   ATR_Expansion_Threshold = 1.3;           // ATR Expansion Threshold
input double   EMA_Slope_Threshold = 0.0001;            // EMA Slope Threshold

input group "===== PHASE 2: LIQUIDITY & LEVELS ====="
input int      SwingLookback = 20;                      // Swing High/Low Lookback
input int      FVG_MinPips = 5;                         // Minimum FVG Size (pips)
input int      OrderBlock_Lookback = 10;                // Order Block Lookback
input bool     ShowLiquidityLevels = true;              // Show Liquidity Levels on Chart

input group "===== PHASE 3: ENTRY CONFLUENCE ====="
input int      RequiredConfluence = 3;                  // Required Confluence Factors (3-5)
input bool     DetectSingleCandles = true;              // Detect Single Candle Patterns
input bool     DetectDoubleCandles = true;              // Detect Two Candle Patterns
input bool     DetectTripleCandles = true;              // Detect Three Candle Patterns
input int      MinPatternStrength = 2;                  // Minimum Pattern Strength (1-5)

input group "===== PHASE 4: RISK MANAGEMENT ====="
input double   RiskPerTrade = 0.5;                      // Risk Per Trade (%)
input int      MaxOpenTrades = 3;                       // Maximum Open Trades
input double   DailyLossLimit = 2.0;                    // Daily Loss Limit (%)
input double   WeeklyLossLimit = 5.0;                   // Weekly Loss Limit (%)
input double   StopLossATR = 2.0;                       // Stop Loss Distance (ATR)

input group "===== PHASE 4: TAKE PROFIT MODEL ====="
enum TP_MODEL { TP_LIQUIDITY, TP_RR_PARTIAL, TP_IMBALANCE };
input TP_MODEL TPModel = TP_RR_PARTIAL;                 // Take Profit Model
input double   TP1_RR = 2.0;                            // TP1 Risk:Reward Ratio
input double   TP2_RR = 3.0;                            // TP2 Risk:Reward Ratio
input double   TP3_RR = 5.0;                            // TP3 Risk:Reward Ratio
input double   PartialClosePercent = 50.0;              // Partial Close at TP1 (%)

input group "===== PHASE 5: TRADE MANAGEMENT ====="
input bool     UseBreakeven = true;                     // Use Breakeven
input double   BreakevenAtRR = 1.0;                     // Move to BE at R:R
input bool     UseTrailing = true;                      // Use Structure Trailing
input int      TrailingSwingBars = 10;                  // Trailing Swing Lookback

input group "===== VISUAL SETTINGS ====="
input bool     ShowPatternBoxes = true;                 // Show Pattern Boxes
input bool     ShowPatternLabels = true;                // Show Pattern Names
input bool     ShowSignalLabels = true;                 // Show BUY/SELL Signals
input color    BuyColor = clrLime;                      // Buy Signal Color
input color    SellColor = clrRed;                      // Sell Signal Color
input int      LabelFontSize = 9;                       // Label Font Size

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  position;
CAccountInfo   account;

string prefix = "CPTEA_";

// Indicator handles
int h_EMA;
int h_ATR;

// Market regime
enum MARKET_REGIME { TREND, RANGE, TRANSITION };
MARKET_REGIME current_regime = TREND;
int current_bias = 0;  // 1 = BUY, -1 = SELL, 0 = NEUTRAL

// Liquidity structures
struct LiquidityZone {
    double price;
    int priority;
    datetime time;
    bool is_high;
};

struct FairValueGap {
    double top;
    double bottom;
    datetime time;
    bool is_bullish;
    bool filled;
};

struct OrderBlock {
    double top;
    double bottom;
    datetime time;
    bool is_bullish;
    bool tested;
};

LiquidityZone liquidity_zones[];
FairValueGap fvg_zones[];
OrderBlock order_blocks[];

// Pattern structure
struct PatternInfo {
    string name;
    string signal;
    int strength;
    datetime time;
    double price;
    bool is_bullish;
    int bar_index;
};

PatternInfo last_pattern;
bool has_active_pattern = false;

// Risk management
double daily_start_balance;
double weekly_start_balance;
datetime last_daily_reset;
datetime last_weekly_reset;
int consecutive_losses = 0;
int consecutive_wins = 0;
double current_risk_multiplier = 1.0;

// Metrics tracking
struct TradeMetrics {
    int total_trades;
    int winning_trades;
    int losing_trades;
    double total_profit;
    double total_loss;
    double largest_win;
    double largest_loss;
    int max_consecutive_wins;
    int max_consecutive_losses;
    double expectancy;
};

TradeMetrics metrics;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("========================================");
    Print("  CANDLESTICK PATTERN TRADING EA v1.0  ");
    Print("  Institutional Trading System          ");
    Print("========================================");

    // Initialize trade object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);

    // Initialize indicators
    h_EMA = iMA(_Symbol, PERIOD_CURRENT, EMA_Period, 0, MODE_EMA, PRICE_CLOSE);
    h_ATR = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);

    if(h_EMA == INVALID_HANDLE || h_ATR == INVALID_HANDLE)
    {
        Print("ERROR: Failed to initialize indicators!");
        return INIT_FAILED;
    }

    // Initialize risk management
    daily_start_balance = account.Balance();
    weekly_start_balance = account.Balance();
    last_daily_reset = TimeCurrent();
    last_weekly_reset = TimeCurrent();

    // Initialize metrics
    ZeroMemory(metrics);
    LoadMetricsFromFile();

    Print("✓ Indicators initialized");
    Print("✓ Risk management configured");
    Print("✓ Pattern detection enabled");

    if(IndicatorMode)
        Print("⚠ INDICATOR MODE - Trading Disabled");
    else
        Print("✓ Auto Trading Enabled");

    Print("Ready to scan for patterns!");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(h_EMA != INVALID_HANDLE) IndicatorRelease(h_EMA);
    if(h_ATR != INVALID_HANDLE) IndicatorRelease(h_ATR);

    // Save metrics
    SaveMetricsToFile();

    // Delete all objects
    ObjectsDeleteAll(0, prefix);

    Print("CandlestickPatternTradingEA - Stopped");
    PrintMetricsSummary();
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check for new bar
    static datetime last_bar_time = 0;
    datetime current_bar_time = iTime(_Symbol, PERIOD_CURRENT, 0);

    if(current_bar_time == last_bar_time)
        return;

    last_bar_time = current_bar_time;

    // ============================================================
    // PHASE 1: MARKET REGIME DETECTION
    // ============================================================
    DetectMarketRegime();
    DetermineBias();

    // ============================================================
    // PHASE 2: LIQUIDITY & LEVELS MAPPING
    // ============================================================
    MapLiquidityLevels();
    DetectFairValueGaps();
    DetectOrderBlocks();

    if(ShowLiquidityLevels || IndicatorMode)
    {
        DrawLiquidityLevels();
        DrawFVGZones();
        DrawOrderBlocks();
    }

    // ============================================================
    // PHASE 3: PATTERN DETECTION & ENTRY
    // ============================================================
    ScanForPatterns();

    // ============================================================
    // PHASE 4 & 5: RISK MANAGEMENT & TRADE MANAGEMENT
    // ============================================================
    if(!IndicatorMode && EnableTrading)
    {
        CheckRiskLimits();
        ManageOpenTrades();

        // Check for entry
        if(has_active_pattern && EvaluateConfluence())
        {
            ExecuteTrade();
        }
    }

    // ============================================================
    // PHASE 6: METRICS UPDATE
    // ============================================================
    UpdateMetrics();
}

//+------------------------------------------------------------------+
//| PHASE 1 - TASK 1: Identify Market Regime                        |
//+------------------------------------------------------------------+
void DetectMarketRegime()
{
    double ema_buffer[];
    double atr_buffer[];
    ArraySetAsSeries(ema_buffer, true);
    ArraySetAsSeries(atr_buffer, true);

    if(CopyBuffer(h_EMA, 0, 0, 50, ema_buffer) <= 0) return;
    if(CopyBuffer(h_ATR, 0, 0, 20, atr_buffer) <= 0) return;

    // Calculate EMA slope
    double ema_slope = (ema_buffer[0] - ema_buffer[10]) / 10;

    // Calculate ATR expansion/contraction
    double avg_atr = 0;
    for(int i = 0; i < 10; i++)
        avg_atr += atr_buffer[i];
    avg_atr /= 10;

    double atr_ratio = atr_buffer[0] / avg_atr;

    // Detect market structure
    bool bos_detected = DetectBreakOfStructure();

    // Classify regime
    if(MathAbs(ema_slope) > EMA_Slope_Threshold && !bos_detected)
    {
        current_regime = TREND;
    }
    else if(MathAbs(ema_slope) < EMA_Slope_Threshold * 0.5 && atr_ratio < 1.1)
    {
        current_regime = RANGE;
    }
    else
    {
        current_regime = TRANSITION;
    }
}

//+------------------------------------------------------------------+
//| PHASE 1 - TASK 2: Determine Side of Market (Bias)               |
//+------------------------------------------------------------------+
void DetermineBias()
{
    double ema_buffer[];
    ArraySetAsSeries(ema_buffer, true);

    if(CopyBuffer(h_EMA, 0, 0, 3, ema_buffer) <= 0) return;

    double close_price = iClose(_Symbol, PERIOD_CURRENT, 1);

    if(current_regime == TREND)
    {
        if(close_price > ema_buffer[0])
            current_bias = 1;  // BUY bias
        else
            current_bias = -1; // SELL bias
    }
    else if(current_regime == RANGE)
    {
        // In range, bias only at extremes
        double range_high = GetRangeHigh();
        double range_low = GetRangeLow();
        double range_middle = (range_high + range_low) / 2;

        if(close_price < range_low + (range_high - range_low) * 0.2)
            current_bias = 1;  // Near bottom, BUY bias
        else if(close_price > range_high - (range_high - range_low) * 0.2)
            current_bias = -1; // Near top, SELL bias
        else
            current_bias = 0;  // NEUTRAL
    }
    else
    {
        current_bias = 0;  // NEUTRAL in transition
    }
}

//+------------------------------------------------------------------+
//| PHASE 2 - TASK 3: Mark Key Liquidity Levels                     |
//+------------------------------------------------------------------+
void MapLiquidityLevels()
{
    ArrayResize(liquidity_zones, 0);

    // Find swing highs and lows
    for(int i = SwingLookback; i < 100; i++)
    {
        double high = iHigh(_Symbol, PERIOD_CURRENT, i);
        double low = iLow(_Symbol, PERIOD_CURRENT, i);
        datetime time = iTime(_Symbol, PERIOD_CURRENT, i);

        // Check for swing high
        bool is_swing_high = true;
        for(int j = 1; j <= SwingLookback; j++)
        {
            if(iHigh(_Symbol, PERIOD_CURRENT, i-j) >= high ||
               iHigh(_Symbol, PERIOD_CURRENT, i+j) >= high)
            {
                is_swing_high = false;
                break;
            }
        }

        // Check for swing low
        bool is_swing_low = true;
        for(int j = 1; j <= SwingLookback; j++)
        {
            if(iLow(_Symbol, PERIOD_CURRENT, i-j) <= low ||
               iLow(_Symbol, PERIOD_CURRENT, i+j) <= low)
            {
                is_swing_low = false;
                break;
            }
        }

        if(is_swing_high)
        {
            int idx = ArraySize(liquidity_zones);
            ArrayResize(liquidity_zones, idx + 1);
            liquidity_zones[idx].price = high;
            liquidity_zones[idx].priority = 2;
            liquidity_zones[idx].time = time;
            liquidity_zones[idx].is_high = true;
        }

        if(is_swing_low)
        {
            int idx = ArraySize(liquidity_zones);
            ArrayResize(liquidity_zones, idx + 1);
            liquidity_zones[idx].price = low;
            liquidity_zones[idx].priority = 2;
            liquidity_zones[idx].time = time;
            liquidity_zones[idx].is_high = false;
        }
    }

    // Detect equal highs/lows (higher priority)
    DetectEqualLevels();
}

//+------------------------------------------------------------------+
//| Detect Equal Highs/Lows                                          |
//+------------------------------------------------------------------+
void DetectEqualLevels()
{
    double point = _Point;
    double tolerance = 10 * point;  // 10 pips tolerance

    for(int i = 0; i < ArraySize(liquidity_zones); i++)
    {
        int equal_count = 0;
        for(int j = 0; j < ArraySize(liquidity_zones); j++)
        {
            if(i == j) continue;

            if(MathAbs(liquidity_zones[i].price - liquidity_zones[j].price) < tolerance &&
               liquidity_zones[i].is_high == liquidity_zones[j].is_high)
            {
                equal_count++;
            }
        }

        if(equal_count >= 1)  // Found equal levels
        {
            liquidity_zones[i].priority = 3;  // Higher priority
        }
    }
}

//+------------------------------------------------------------------+
//| PHASE 2 - Fair Value Gaps Detection                             |
//+------------------------------------------------------------------+
void DetectFairValueGaps()
{
    ArrayResize(fvg_zones, 0);
    double point = _Point;
    double min_gap = FVG_MinPips * point * 10;

    for(int i = 1; i < 50; i++)
    {
        double high1 = iHigh(_Symbol, PERIOD_CURRENT, i+1);
        double low1 = iLow(_Symbol, PERIOD_CURRENT, i+1);
        double high2 = iHigh(_Symbol, PERIOD_CURRENT, i);
        double low2 = iLow(_Symbol, PERIOD_CURRENT, i);
        double high3 = iHigh(_Symbol, PERIOD_CURRENT, i-1);
        double low3 = iLow(_Symbol, PERIOD_CURRENT, i-1);

        // Bullish FVG: low3 > high1
        if(low3 > high1 && (low3 - high1) >= min_gap)
        {
            int idx = ArraySize(fvg_zones);
            ArrayResize(fvg_zones, idx + 1);
            fvg_zones[idx].top = low3;
            fvg_zones[idx].bottom = high1;
            fvg_zones[idx].time = iTime(_Symbol, PERIOD_CURRENT, i);
            fvg_zones[idx].is_bullish = true;
            fvg_zones[idx].filled = false;
        }

        // Bearish FVG: high3 < low1
        if(high3 < low1 && (low1 - high3) >= min_gap)
        {
            int idx = ArraySize(fvg_zones);
            ArrayResize(fvg_zones, idx + 1);
            fvg_zones[idx].top = low1;
            fvg_zones[idx].bottom = high3;
            fvg_zones[idx].time = iTime(_Symbol, PERIOD_CURRENT, i);
            fvg_zones[idx].is_bullish = false;
            fvg_zones[idx].filled = false;
        }
    }

    // Check if FVGs are filled
    double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
    for(int i = 0; i < ArraySize(fvg_zones); i++)
    {
        if(fvg_zones[i].is_bullish)
        {
            if(current_price <= fvg_zones[i].bottom)
                fvg_zones[i].filled = true;
        }
        else
        {
            if(current_price >= fvg_zones[i].top)
                fvg_zones[i].filled = true;
        }
    }
}

//+------------------------------------------------------------------+
//| PHASE 2 - Order Blocks Detection                                |
//+------------------------------------------------------------------+
void DetectOrderBlocks()
{
    ArrayResize(order_blocks, 0);

    for(int i = 2; i < OrderBlock_Lookback; i++)
    {
        double close_prev = iClose(_Symbol, PERIOD_CURRENT, i);
        double open_prev = iOpen(_Symbol, PERIOD_CURRENT, i);
        double close_curr = iClose(_Symbol, PERIOD_CURRENT, i-1);

        // Bullish Order Block: last bearish before bullish move
        if(close_prev < open_prev && close_curr > close_prev)
        {
            double body_top = MathMax(open_prev, close_prev);
            double body_bottom = MathMin(open_prev, close_prev);

            int idx = ArraySize(order_blocks);
            ArrayResize(order_blocks, idx + 1);
            order_blocks[idx].top = body_top;
            order_blocks[idx].bottom = body_bottom;
            order_blocks[idx].time = iTime(_Symbol, PERIOD_CURRENT, i);
            order_blocks[idx].is_bullish = true;
            order_blocks[idx].tested = false;
        }

        // Bearish Order Block: last bullish before bearish move
        if(close_prev > open_prev && close_curr < close_prev)
        {
            double body_top = MathMax(open_prev, close_prev);
            double body_bottom = MathMin(open_prev, close_prev);

            int idx = ArraySize(order_blocks);
            ArrayResize(order_blocks, idx + 1);
            order_blocks[idx].top = body_top;
            order_blocks[idx].bottom = body_bottom;
            order_blocks[idx].time = iTime(_Symbol, PERIOD_CURRENT, i);
            order_blocks[idx].is_bullish = false;
            order_blocks[idx].tested = false;
        }
    }
}

//+------------------------------------------------------------------+
//| PHASE 3 - Pattern Detection                                     |
//+------------------------------------------------------------------+
void ScanForPatterns()
{
    PatternInfo pattern;
    bool found = false;

    // Get price data
    double o[], h[], l[], c[];
    ArraySetAsSeries(o, true);
    ArraySetAsSeries(h, true);
    ArraySetAsSeries(l, true);
    ArraySetAsSeries(c, true);

    if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 5, o) <= 0) return;
    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 5, h) <= 0) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 5, l) <= 0) return;
    if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, c) <= 0) return;

    // SINGLE CANDLE PATTERNS
    if(DetectSingleCandles)
    {
        if(!found) found = DetectHammer(1, o, h, l, c, pattern);
        if(!found) found = DetectShootingStar(1, o, h, l, c, pattern);
        if(!found) found = DetectDoji(1, o, h, l, c, pattern);
        if(!found) found = DetectDragonflyDoji(1, o, h, l, c, pattern);
        if(!found) found = DetectGravestoneDoji(1, o, h, l, c, pattern);
        if(!found) found = DetectMarubozu(1, o, h, l, c, pattern);
        if(!found) found = DetectSpinningTop(1, o, h, l, c, pattern);
    }

    // TWO CANDLE PATTERNS
    if(DetectDoubleCandles)
    {
        if(!found) found = DetectEngulfing(1, o, h, l, c, pattern);
        if(!found) found = DetectHarami(1, o, h, l, c, pattern);
        if(!found) found = DetectPiercingLine(1, o, h, l, c, pattern);
        if(!found) found = DetectDarkCloudCover(1, o, h, l, c, pattern);
        if(!found) found = DetectTweezer(1, o, h, l, c, pattern);
    }

    // THREE CANDLE PATTERNS
    if(DetectTripleCandles)
    {
        if(!found) found = DetectMorningStar(1, o, h, l, c, pattern);
        if(!found) found = DetectEveningStar(1, o, h, l, c, pattern);
        if(!found) found = DetectThreeWhiteSoldiers(1, o, h, l, c, pattern);
        if(!found) found = DetectThreeBlackCrows(1, o, h, l, c, pattern);
        if(!found) found = DetectThreeInside(1, o, h, l, c, pattern);
    }

    if(found && pattern.strength >= MinPatternStrength)
    {
        last_pattern = pattern;
        has_active_pattern = true;

        // Draw pattern on chart
        if(ShowPatternBoxes || IndicatorMode)
        {
            DrawPatternBox(pattern);
        }

        if(ShowPatternLabels || IndicatorMode)
        {
            DrawPatternLabel(pattern);
        }
    }
}

//+------------------------------------------------------------------+
//| PHASE 3 - TASK 5: Evaluate Confluence                           |
//+------------------------------------------------------------------+
bool EvaluateConfluence()
{
    if(!has_active_pattern) return false;

    int confluence_count = 0;

    // 1. Market regime aligned
    if(current_regime == TREND)
    {
        if((current_bias == 1 && last_pattern.is_bullish) ||
           (current_bias == -1 && !last_pattern.is_bullish))
        {
            confluence_count++;
        }
    }

    // 2. Bias confirmation
    if((current_bias == 1 && last_pattern.is_bullish) ||
       (current_bias == -1 && !last_pattern.is_bullish) ||
       (current_regime == RANGE && current_bias != 0))
    {
        confluence_count++;
    }

    // 3. Near liquidity level
    double current_price = last_pattern.price;
    for(int i = 0; i < ArraySize(liquidity_zones); i++)
    {
        if(MathAbs(current_price - liquidity_zones[i].price) < 20 * _Point * 10)
        {
            confluence_count++;
            break;
        }
    }

    // 4. FVG or Order Block present
    bool near_fvg = false;
    for(int i = 0; i < ArraySize(fvg_zones); i++)
    {
        if(!fvg_zones[i].filled)
        {
            if(current_price >= fvg_zones[i].bottom && current_price <= fvg_zones[i].top)
            {
                near_fvg = true;
                break;
            }
        }
    }

    bool near_ob = false;
    for(int i = 0; i < ArraySize(order_blocks); i++)
    {
        if(!order_blocks[i].tested)
        {
            if(current_price >= order_blocks[i].bottom && current_price <= order_blocks[i].top)
            {
                near_ob = true;
                break;
            }
        }
    }

    if(near_fvg || near_ob) confluence_count++;

    // 5. Pattern strength
    if(last_pattern.strength >= 4) confluence_count++;

    return (confluence_count >= RequiredConfluence);
}

//+------------------------------------------------------------------+
//| PHASE 4 - TASK 7: Calculate Position Size                       |
//+------------------------------------------------------------------+
double CalculateLotSize(double stop_loss_pips)
{
    if(stop_loss_pips <= 0) return MinLotSize;

    double capital_risk = account.Balance() * (RiskPerTrade / 100.0) * current_risk_multiplier;

    double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    double sl_in_price = stop_loss_pips * point;
    double risk_per_lot = (sl_in_price / tick_size) * tick_value;

    double lot_size = capital_risk / risk_per_lot;

    // Round to lot step
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    lot_size = MathFloor(lot_size / lot_step) * lot_step;

    // Apply limits
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

    if(lot_size < MinLotSize) lot_size = MinLotSize;
    if(lot_size < min_lot) lot_size = min_lot;
    if(lot_size > max_lot) lot_size = max_lot;

    return lot_size;
}

//+------------------------------------------------------------------+
//| PHASE 4 - TASK 8: Stop Loss Placement                           |
//+------------------------------------------------------------------+
double CalculateStopLoss(bool is_buy)
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);

    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0)
        return 0;

    double atr = atr_buffer[0];
    double sl_distance = atr * StopLossATR;

    double entry_price = last_pattern.price;
    double sl_price;

    if(is_buy)
    {
        // Look for swing low
        double swing_low = GetSwingLow(SwingLookback);
        double atr_sl = entry_price - sl_distance;
        sl_price = MathMin(swing_low - 5 * _Point, atr_sl);
    }
    else
    {
        // Look for swing high
        double swing_high = GetSwingHigh(SwingLookback);
        double atr_sl = entry_price + sl_distance;
        sl_price = MathMax(swing_high + 5 * _Point, atr_sl);
    }

    return NormalizeDouble(sl_price, _Digits);
}

//+------------------------------------------------------------------+
//| PHASE 4 - TASK 9: Take Profit Calculation                       |
//+------------------------------------------------------------------+
void CalculateTakeProfits(bool is_buy, double entry, double sl, double &tp1, double &tp2, double &tp3)
{
    double sl_distance = MathAbs(entry - sl);

    if(TPModel == TP_LIQUIDITY)
    {
        // Find nearest liquidity targets
        tp1 = FindNearestLiquidity(is_buy, entry);
        tp2 = tp1 + (is_buy ? 1 : -1) * sl_distance * 2;
        tp3 = tp1 + (is_buy ? 1 : -1) * sl_distance * 3;
    }
    else if(TPModel == TP_RR_PARTIAL)
    {
        tp1 = entry + (is_buy ? 1 : -1) * sl_distance * TP1_RR;
        tp2 = entry + (is_buy ? 1 : -1) * sl_distance * TP2_RR;
        tp3 = entry + (is_buy ? 1 : -1) * sl_distance * TP3_RR;
    }
    else  // TP_IMBALANCE
    {
        // Find FVG to fill
        double fvg_target = FindFVGTarget(is_buy);
        tp1 = fvg_target;
        tp2 = entry + (is_buy ? 1 : -1) * sl_distance * TP2_RR;
        tp3 = entry + (is_buy ? 1 : -1) * sl_distance * TP3_RR;
    }

    tp1 = NormalizeDouble(tp1, _Digits);
    tp2 = NormalizeDouble(tp2, _Digits);
    tp3 = NormalizeDouble(tp3, _Digits);
}

//+------------------------------------------------------------------+
//| PHASE 3 - TASK 6: Execute Trade                                 |
//+------------------------------------------------------------------+
void ExecuteTrade()
{
    if(!CheckRiskLimits()) return;

    // Count open positions
    int open_count = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == MagicNumber)
                open_count++;
        }
    }

    if(open_count >= MaxOpenTrades) return;

    bool is_buy = last_pattern.is_bullish;
    double entry_price = SymbolInfoDouble(_Symbol, is_buy ? SYMBOL_ASK : SYMBOL_BID);

    // Calculate SL and TPs
    double sl = CalculateStopLoss(is_buy);
    double tp1, tp2, tp3;
    CalculateTakeProfits(is_buy, entry_price, sl, tp1, tp2, tp3);

    // Calculate lot size
    double sl_pips = MathAbs(entry_price - sl) / _Point;
    double lot_size = CalculateLotSize(sl_pips);

    // Execute order
    bool success = false;
    if(is_buy)
    {
        success = trade.Buy(lot_size, _Symbol, entry_price, sl, tp1,
                           "CPTEA|" + last_pattern.name + "|TP1");
    }
    else
    {
        success = trade.Sell(lot_size, _Symbol, entry_price, sl, tp1,
                            "CPTEA|" + last_pattern.name + "|TP1");
    }

    if(success)
    {
        Print("✓ Trade Executed: ", last_pattern.name, " | Lots: ", lot_size,
              " | SL: ", sl, " | TP: ", tp1);

        // Add pending orders for TP2 and TP3 with reduced lots
        if(TPModel == TP_RR_PARTIAL)
        {
            // Will be managed in trade management
        }

        has_active_pattern = false;  // Reset pattern flag
    }
    else
    {
        Print("✗ Trade Failed: ", GetLastError());
    }
}

//+------------------------------------------------------------------+
//| PHASE 4: Check Risk Limits                                      |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
    // Reset daily tracking
    MqlDateTime dt_current, dt_last;
    TimeToStruct(TimeCurrent(), dt_current);
    TimeToStruct(last_daily_reset, dt_last);

    if(dt_current.day != dt_last.day)
    {
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
    }

    // Reset weekly tracking
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
        Print("⚠ DAILY LOSS LIMIT REACHED: ", daily_loss, "%");
        return false;
    }

    // Check weekly loss limit
    double weekly_loss = ((weekly_start_balance - account.Balance()) / weekly_start_balance) * 100.0;
    if(weekly_loss >= WeeklyLossLimit)
    {
        Print("⚠ WEEKLY LOSS LIMIT REACHED: ", weekly_loss, "%");
        return false;
    }

    // Adjust risk after consecutive losses
    if(consecutive_losses >= 2)
    {
        current_risk_multiplier = 0.5;
        Print("⚠ Risk reduced to 50% after ", consecutive_losses, " consecutive losses");
    }
    else
    {
        current_risk_multiplier = 1.0;
    }

    return true;
}

//+------------------------------------------------------------------+
//| PHASE 5 - TASK 10-12: Manage Open Trades                        |
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

        // Calculate profit in R
        double sl_distance = MathAbs(entry - sl);
        double current_profit = is_buy ? (current_price - entry) : (entry - current_price);
        double r_profit = current_profit / sl_distance;

        // TASK 10: Breakeven Logic
        if(UseBreakeven && r_profit >= BreakevenAtRR && sl != entry)
        {
            if(trade.PositionModify(ticket, entry + (is_buy ? 1 : -1) * 5 * _Point, tp))
            {
                Print("✓ Moved to Breakeven: Ticket ", ticket);
            }
        }

        // TASK 11: Structure Trailing
        if(UseTrailing && r_profit >= 1.0)
        {
            double new_sl;
            if(is_buy)
            {
                new_sl = GetSwingLow(TrailingSwingBars);
                if(new_sl > sl && new_sl < current_price)
                {
                    if(trade.PositionModify(ticket, new_sl, tp))
                        Print("✓ Trailing SL: ", new_sl);
                }
            }
            else
            {
                new_sl = GetSwingHigh(TrailingSwingBars);
                if(new_sl < sl && new_sl > current_price)
                {
                    if(trade.PositionModify(ticket, new_sl, tp))
                        Print("✓ Trailing SL: ", new_sl);
                }
            }
        }

        // TASK 12: Exit Rules - Check for opposite structure break
        if(CheckOppositeStructureBreak(is_buy))
        {
            if(trade.PositionClose(ticket))
            {
                Print("✓ Closed due to opposite structure break");
            }
        }
    }
}

//+------------------------------------------------------------------+
//| PHASE 6 - TASK 14: Update Metrics                               |
//+------------------------------------------------------------------+
void UpdateMetrics()
{
    static int last_total_deals = 0;
    int current_total_deals = HistoryDealsTotal();

    if(current_total_deals == last_total_deals) return;

    last_total_deals = current_total_deals;

    // Recalculate metrics from history
    HistorySelect(0, TimeCurrent());

    metrics.total_trades = 0;
    metrics.winning_trades = 0;
    metrics.losing_trades = 0;
    metrics.total_profit = 0;
    metrics.total_loss = 0;
    metrics.largest_win = 0;
    metrics.largest_loss = 0;

    int current_streak = 0;
    int temp_wins = 0;
    int temp_losses = 0;

    for(int i = 0; i < HistoryDealsTotal(); i++)
    {
        ulong ticket = HistoryDealGetTicket(i);
        if(ticket <= 0) continue;

        if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != MagicNumber) continue;
        if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
        if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;

        double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);

        if(profit != 0)
        {
            metrics.total_trades++;

            if(profit > 0)
            {
                metrics.winning_trades++;
                metrics.total_profit += profit;
                if(profit > metrics.largest_win) metrics.largest_win = profit;

                temp_wins++;
                temp_losses = 0;
            }
            else
            {
                metrics.losing_trades++;
                metrics.total_loss += MathAbs(profit);
                if(MathAbs(profit) > metrics.largest_loss) metrics.largest_loss = MathAbs(profit);

                temp_losses++;
                temp_wins = 0;
            }

            if(temp_wins > metrics.max_consecutive_wins)
                metrics.max_consecutive_wins = temp_wins;
            if(temp_losses > metrics.max_consecutive_losses)
                metrics.max_consecutive_losses = temp_losses;

            // Track for risk adjustment
            consecutive_wins = temp_wins;
            consecutive_losses = temp_losses;
        }
    }

    // Calculate expectancy
    if(metrics.total_trades > 0)
    {
        double win_rate = (double)metrics.winning_trades / metrics.total_trades;
        double avg_win = metrics.winning_trades > 0 ? metrics.total_profit / metrics.winning_trades : 0;
        double avg_loss = metrics.losing_trades > 0 ? metrics.total_loss / metrics.losing_trades : 0;

        metrics.expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss);
    }
}

//+------------------------------------------------------------------+
//| Helper Functions                                                  |
//+------------------------------------------------------------------+
bool DetectBreakOfStructure()
{
    // Simplified BOS detection
    double high1 = iHigh(_Symbol, PERIOD_CURRENT, 1);
    double high2 = iHigh(_Symbol, PERIOD_CURRENT, 2);
    double low1 = iLow(_Symbol, PERIOD_CURRENT, 1);
    double low2 = iLow(_Symbol, PERIOD_CURRENT, 2);

    // Bullish BOS: break above previous high
    if(high1 > high2) return true;

    // Bearish BOS: break below previous low
    if(low1 < low2) return true;

    return false;
}

double GetRangeHigh()
{
    double high = 0;
    for(int i = 1; i < 50; i++)
    {
        double h = iHigh(_Symbol, PERIOD_CURRENT, i);
        if(h > high) high = h;
    }
    return high;
}

double GetRangeLow()
{
    double low = DBL_MAX;
    for(int i = 1; i < 50; i++)
    {
        double l = iLow(_Symbol, PERIOD_CURRENT, i);
        if(l < low) low = l;
    }
    return low;
}

double GetSwingHigh(int lookback)
{
    double high = 0;
    for(int i = 1; i <= lookback; i++)
    {
        double h = iHigh(_Symbol, PERIOD_CURRENT, i);
        if(h > high) high = h;
    }
    return high;
}

double GetSwingLow(int lookback)
{
    double low = DBL_MAX;
    for(int i = 1; i <= lookback; i++)
    {
        double l = iLow(_Symbol, PERIOD_CURRENT, i);
        if(l < low) low = l;
    }
    return low;
}

double FindNearestLiquidity(bool is_buy, double entry)
{
    double nearest = is_buy ? DBL_MAX : 0;

    for(int i = 0; i < ArraySize(liquidity_zones); i++)
    {
        if(is_buy && liquidity_zones[i].price > entry)
        {
            if(liquidity_zones[i].price < nearest)
                nearest = liquidity_zones[i].price;
        }
        else if(!is_buy && liquidity_zones[i].price < entry)
        {
            if(liquidity_zones[i].price > nearest)
                nearest = liquidity_zones[i].price;
        }
    }

    if(nearest == DBL_MAX || nearest == 0)
        nearest = entry + (is_buy ? 1 : -1) * 100 * _Point;

    return nearest;
}

double FindFVGTarget(bool is_buy)
{
    for(int i = 0; i < ArraySize(fvg_zones); i++)
    {
        if(!fvg_zones[i].filled)
        {
            if(is_buy && fvg_zones[i].is_bullish)
                return fvg_zones[i].top;
            else if(!is_buy && !fvg_zones[i].is_bullish)
                return fvg_zones[i].bottom;
        }
    }

    return 0;
}

bool CheckOppositeStructureBreak(bool is_buy_position)
{
    // Check if there's a structure break against the position
    double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);
    double close2 = iClose(_Symbol, PERIOD_CURRENT, 2);

    if(is_buy_position)
    {
        // Check for bearish structure break
        double swing_low = GetSwingLow(10);
        if(close1 < swing_low) return true;
    }
    else
    {
        // Check for bullish structure break
        double swing_high = GetSwingHigh(10);
        if(close1 > swing_high) return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Metrics Management                                                |
//+------------------------------------------------------------------+
void LoadMetricsFromFile()
{
    int handle = FileOpen("CPTEA_Metrics.dat", FILE_READ | FILE_BIN);
    if(handle != INVALID_HANDLE)
    {
        FileReadStruct(handle, metrics);
        FileClose(handle);
    }
}

void SaveMetricsToFile()
{
    int handle = FileOpen("CPTEA_Metrics.dat", FILE_WRITE | FILE_BIN);
    if(handle != INVALID_HANDLE)
    {
        FileWriteStruct(handle, metrics);
        FileClose(handle);
    }
}

void PrintMetricsSummary()
{
    Print("========================================");
    Print("  PERFORMANCE METRICS SUMMARY");
    Print("========================================");
    Print("Total Trades: ", metrics.total_trades);
    Print("Winning Trades: ", metrics.winning_trades);
    Print("Losing Trades: ", metrics.losing_trades);

    if(metrics.total_trades > 0)
    {
        double win_rate = (double)metrics.winning_trades / metrics.total_trades * 100.0;
        Print("Win Rate: ", DoubleToString(win_rate, 2), "%");
    }

    Print("Total Profit: $", DoubleToString(metrics.total_profit, 2));
    Print("Total Loss: $", DoubleToString(metrics.total_loss, 2));
    Print("Net P/L: $", DoubleToString(metrics.total_profit - metrics.total_loss, 2));
    Print("Largest Win: $", DoubleToString(metrics.largest_win, 2));
    Print("Largest Loss: $", DoubleToString(metrics.largest_loss, 2));
    Print("Max Consecutive Wins: ", metrics.max_consecutive_wins);
    Print("Max Consecutive Losses: ", metrics.max_consecutive_losses);
    Print("Expectancy: $", DoubleToString(metrics.expectancy, 2));
    Print("========================================");
}

//+------------------------------------------------------------------+
//| Drawing Functions                                                 |
//+------------------------------------------------------------------+
void DrawLiquidityLevels()
{
    for(int i = 0; i < ArraySize(liquidity_zones); i++)
    {
        string name = prefix + "LIQ_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            ObjectCreate(0, name, OBJ_HLINE, 0, 0, liquidity_zones[i].price);
            ObjectSetInteger(0, name, OBJPROP_COLOR, liquidity_zones[i].is_high ? clrRed : clrBlue);
            ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);
            ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
            ObjectSetString(0, name, OBJPROP_TEXT, "Liquidity");
        }
    }
}

void DrawFVGZones()
{
    for(int i = 0; i < ArraySize(fvg_zones); i++)
    {
        if(fvg_zones[i].filled) continue;

        string name = prefix + "FVG_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            datetime time_now = TimeCurrent();
            ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                        fvg_zones[i].time, fvg_zones[i].top,
                        time_now + PeriodSeconds(PERIOD_CURRENT) * 50, fvg_zones[i].bottom);
            ObjectSetInteger(0, name, OBJPROP_COLOR, fvg_zones[i].is_bullish ? clrLightGreen : clrLightPink);
            ObjectSetInteger(0, name, OBJPROP_BACK, true);
            ObjectSetInteger(0, name, OBJPROP_FILL, true);
        }
    }
}

void DrawOrderBlocks()
{
    for(int i = 0; i < ArraySize(order_blocks); i++)
    {
        if(order_blocks[i].tested) continue;

        string name = prefix + "OB_" + IntegerToString(i);

        if(ObjectFind(0, name) < 0)
        {
            datetime time_now = TimeCurrent();
            ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                        order_blocks[i].time, order_blocks[i].top,
                        time_now + PeriodSeconds(PERIOD_CURRENT) * 50, order_blocks[i].bottom);
            ObjectSetInteger(0, name, OBJPROP_COLOR, order_blocks[i].is_bullish ? clrGreen : clrCrimson);
            ObjectSetInteger(0, name, OBJPROP_BACK, true);
            ObjectSetInteger(0, name, OBJPROP_FILL, true);
        }
    }
}

void DrawPatternBox(PatternInfo &p)
{
    double atr_buffer[];
    ArraySetAsSeries(atr_buffer, true);

    if(CopyBuffer(h_ATR, 0, 0, 1, atr_buffer) <= 0) return;

    double atr = atr_buffer[0];
    datetime time = iTime(_Symbol, PERIOD_CURRENT, p.bar_index);

    string name = prefix + "BOX_" + TimeToString(time);

    double top = p.price + atr;
    double bottom = p.price - atr;

    ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                time, top,
                time + PeriodSeconds(PERIOD_CURRENT), bottom);

    color box_color = p.is_bullish ? BuyColor : SellColor;
    ObjectSetInteger(0, name, OBJPROP_COLOR, box_color);
    ObjectSetInteger(0, name, OBJPROP_BACK, false);
    ObjectSetInteger(0, name, OBJPROP_FILL, false);
    ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
}

void DrawPatternLabel(PatternInfo &p)
{
    datetime time = iTime(_Symbol, PERIOD_CURRENT, p.bar_index);
    string name = prefix + "LABEL_" + TimeToString(time);

    double price = p.is_bullish ? iLow(_Symbol, PERIOD_CURRENT, p.bar_index) - 10 * _Point :
                                   iHigh(_Symbol, PERIOD_CURRENT, p.bar_index) + 10 * _Point;

    ObjectCreate(0, name, OBJ_TEXT, 0, time, price);
    ObjectSetString(0, name, OBJPROP_TEXT, p.name + " (" + p.signal + ")");
    ObjectSetInteger(0, name, OBJPROP_COLOR, p.is_bullish ? BuyColor : SellColor);
    ObjectSetInteger(0, name, OBJPROP_FONTSIZE, LabelFontSize);
    ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
}

//+------------------------------------------------------------------+
//| CANDLESTICK PATTERN DETECTION FUNCTIONS                          |
//| All patterns copied from the indicator                           |
//+------------------------------------------------------------------+

#include "CandlestickPatterns.mqh"

//+------------------------------------------------------------------+