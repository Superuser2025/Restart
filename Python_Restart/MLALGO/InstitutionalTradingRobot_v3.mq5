//+------------------------------------------------------------------+
//|                                InstitutionalTradingRobot_v3.mq5  |
//|                         Institutional-Grade Trading System v3.0   |
//|                      Complete Rewrite - Pure MQL5 Implementation  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "3.00"
#property description "Citadel-Level Trading Robot - 20 Professional Fixes"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| TRADING PROFILE ENUMERATION                                       |
//+------------------------------------------------------------------+
enum ENUM_TRADING_PROFILE
{
    PROFILE_M5_SCALPING,        // M5 Scalping (Fast, Tight Stops, High Confluence)
    PROFILE_M15_INTRADAY,       // M15 Intraday (Balanced Scalping)
    PROFILE_H1_SWING,           // H1 Swing Trading (Medium-Term)
    PROFILE_H4_POSITION,        // H4 Position Trading (Default Institutional)
    PROFILE_D1_INVESTOR,        // D1 Position Trading (Long-Term)
    PROFILE_CUSTOM              // Custom (Manual Configuration)
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - INSTITUTIONAL CONFIGURATION                    |
//+------------------------------------------------------------------+
input group "═════════ 🎯 AUTO-CONFIGURATION (SELECT YOUR TIMEFRAME) ═════════"
input ENUM_TRADING_PROFILE TradingProfile = PROFILE_H4_POSITION;  // Trading Profile (Auto-Configures Everything!)

input group "═════════ CORE SETTINGS ═════════"
input bool     EnableTrading = true;                    // Enable Auto Trading (Independent from Indicator Mode)
input bool     IndicatorMode = true;                    // Visual Analysis Mode (Can run with Trading ON)
input ENUM_TIMEFRAMES PreferredTimeframe = PERIOD_H4;   // Trading Timeframe (Overridden by Profile)
input double   MinLotSize = 0.01;                       // Minimum Lot Size
input int      MagicNumber = 123456;                    // Magic Number

input group "═════════ PENDING ORDERS (DEFAULT METHOD) ═════════"
input bool     UsePendingOrders = true;                 // Use Pending Orders (DEFAULT)
input bool     AllowMarketOrders = false;               // Allow Market Orders (Manual Override)
input bool     UseBuyStop = true;                       // Use BUY STOP Orders
input bool     UseSellStop = true;                      // Use SELL STOP Orders
input bool     UseBuyLimit = true;                      // Use BUY LIMIT Orders
input bool     UseSellLimit = true;                     // Use SELL LIMIT Orders
input double   PendingOrderDistance = 0.5;              // Pending Order Distance (× ATR, if no structure found)
input int      PendingOrderExpiration = 24;             // Pending Order Expiration (Hours, 0=No Expiry)

input group "═════════ FIX #1-3: EXECUTION QUALITY ═════════"
input bool     UseVolumeFilter = true;                  // Volume Confirmation Required
input double   MinVolumeMultiplier = 1.5;               // Minimum Volume (× Average)
input bool     UseSpreadFilter = true;                  // Spread Protection
input double   MaxSpreadPercent = 0.3;                  // Max Spread (% of ATR)
input bool     UseSlippageModel = true;                 // Slippage Modeling
input double   ExpectedSlippagePercent = 0.1;           // Expected Slippage (% of ATR)

input group "═════════ FIX #5-8: MULTI-DIMENSIONAL ANALYSIS ═════════"
input bool     UseMTFConfirmation = true;               // Multi-Timeframe Confirmation
input bool     UseSessionFilter = true;                 // Session Filtering
input bool     TradeAsianSession = false;               // Trade Asian Session
input bool     TradeLondonSession = true;               // Trade London Session
input bool     TradeNYSession = true;                   // Trade NY Session
input bool     UseCorrelationFilter = true;             // Portfolio Correlation Check
input double   MaxCorrelationExposure = 0.7;            // Max Correlation Limit
input bool     UseNewsFilter = true;                    // Economic Calendar Filter
input int      NewsAvoidMinutes = 30;                   // Minutes Before/After News

input group "═════════ FIX #9-12: ADAPTIVE RISK ═════════"
input bool     UseVolatilityAdaptation = true;          // Volatility Regime Detection
input bool     UseDynamicRisk = true;                   // Drawdown-Based Risk Adjustment
input bool     UsePatternDecay = true;                  // Pattern Time Decay
input int      PatternExpiryBars = 3;                   // Pattern Valid For (Bars)
input bool     UsePositionCorrelation = true;           // Position Correlation Management

input group "═════════ FIX #13-16: SMART MONEY CONCEPTS ═════════"
input bool     UseLiquiditySweep = true;                // Liquidity Sweep Detection
input bool     UseRetailTrap = true;                    // Retail Trap Detection
input bool     UseOrderBlockInvalidation = true;        // Order Block Invalidation
input int      MaxOBTests = 3;                          // Max Order Block Re-Tests
input bool     UseMarketStructure = true;               // Market Structure Tracking

input group "═════════ FIX #17-20: MACHINE LEARNING ═════════"
input bool     UsePatternTracking = true;               // Pattern Performance Tracking
input bool     UseParameterAdaptation = true;           // Self-Optimization
input bool     UseRegimeStrategy = true;                // Regime-Specific Strategies
input int      AdaptationPeriod = 20;                   // Learning Period (Trades)

input group "═════════ RISK MANAGEMENT ═════════"
input double   BaseRiskPercent = 0.5;                   // Base Risk Per Trade (%)
input int      MaxOpenTrades = 999;                     // Max Concurrent Trades (999 = Unlimited)
input double   MaxLotPerTrade = 0.05;                   // Max Lot Size Per Single Trade
input double   MaxLotsPerSymbol = 0.10;                 // Max Total Lots Per Symbol
input double   DailyLossLimit = 2.0;                    // Daily Loss Limit (%)
input double   WeeklyLossLimit = 5.0;                   // Weekly Loss Limit (%)
input bool     EnableDuplicateDetection = true;         // Prevent Duplicate Orders

input group "═════════ STOP LOSS SETTINGS ═════════"
input bool     UseCustomSL = false;                     // Use Custom Stop Loss
input double   CustomSLPips = 50;                       // Custom SL (Pips, if UseCustomSL=true)
input double   StopLossATR = 2.0;                       // Stop Loss (× ATR, if UseCustomSL=false)
input bool     UseSwingStopLoss = true;                 // Use Swing High/Low for SL

input group "═════════ TAKE PROFIT SETTINGS ═════════"
input bool     UseCustomTP = false;                     // Use Custom Take Profit
input double   CustomTP1Pips = 100;                     // Custom TP1 (Pips, if UseCustomTP=true)
input double   CustomTP2Pips = 150;                     // Custom TP2 (Pips, if UseCustomTP=true)
input double   CustomTP3Pips = 200;                     // Custom TP3 (Pips, if UseCustomTP=true)
input double   TP1_RiskReward = 2.0;                    // Take Profit 1 (R:R, if UseCustomTP=false)
input double   TP2_RiskReward = 3.0;                    // Take Profit 2 (R:R, if UseCustomTP=false)
input double   TP3_RiskReward = 5.0;                    // Take Profit 3 (R:R, if UseCustomTP=false)
input bool     UsePartialTakeProfit = true;             // Use Partial TP
input double   TP1_ClosePercent = 50.0;                 // Close % at TP1
input double   TP2_ClosePercent = 30.0;                 // Close % at TP2
input double   TP3_ClosePercent = 20.0;                 // Close % at TP3

input group "═════════ TRAILING STOP SETTINGS ═════════"
input bool     UseTrailingStop = true;                  // Enable Trailing Stop
input double   TrailingStopActivationR = 1.0;           // Start Trailing at (R)
input double   TrailingStopDistanceATR = 1.0;           // Trail Distance (× ATR)
input bool     UseStructureTrailing = true;             // Trail to Swing Highs/Lows
input bool     MoveToBreakEven = true;                  // Move to Break-Even
input double   BreakEvenActivationR = 1.0;              // Break-Even at (R)

input group "═════════ PROFIT TARGETS (ACCOUNT & SYMBOL LEVEL) ═════════"
input bool     UseAccountProfitTarget = false;          // Enable Account-Level Profit Target
input double   AccountProfitTarget = 100.0;             // Account Profit Target ($)
input bool     UseSymbolProfitTarget = false;           // Enable Symbol-Level Profit Target
input double   SymbolProfitTarget = 50.0;               // Symbol Profit Target ($)

input group "═════════ TIER 1: SMART ORDER PLACEMENT ═════════"
input bool     UseSmartPlacement = true;                // Place Orders at FVG/OB Levels
input bool     UseStructureBasedTP = true;              // Target Structure Levels (not fixed R:R)
input bool     UseDynamicPositionSizing = true;         // Size by Confluence Score

input group "═════════ TIER 2: ADVANCED FILTERS ═════════"
input bool     UseAdvancedSL = true;                    // SL at OB/FVG Boundaries
input bool     UseTimeOfDayFilter = true;               // Trade Only High-Volume Hours
input int      StartTradingHour = 8;                    // Start Trading (GMT, 8=London Open)
input int      StopTradingHour = 16;                    // Stop Trading (GMT, 16=After NY Open)
input bool     UseVolatilityAdaptive = true;            // Adapt Pending Distance to Volatility

input group "═════════ TIER 3: PYRAMIDING & RE-ENTRY ═════════"
input bool     UsePyramiding = false;                   // Add to Winning Positions
input int      MaxPyramidLevels = 2;                    // Max Additions (1-3)
input double   PyramidAddAtR = 1.5;                     // Add Position at (R)
input bool     UseReEntry = true;                       // Re-enter After Stop Out
input int      MaxReEntries = 1;                        // Max Re-entry Attempts (0-2)

input group "═════════ VISUAL DASHBOARD ═════════"
input bool     ShowDashboard = true;                    // Show Dashboard
input bool     ShowCommentary = true;                   // Show Real-Time Commentary
input int      Dashboard_X = 20;                        // Dashboard X Position
input int      Dashboard_Y = 50;                        // Dashboard Y Position
input color    ColorBackground = C'20,20,30';           // Background Color
input color    ColorText = clrWhite;                    // Text Color
input int      FontSize = 9;                            // Font Size

input group "═════════ 🤖 MACHINE LEARNING SYSTEM ═════════"
input bool     ML_Enabled = false;                      // Enable ML System (MASTER SWITCH)
input bool     ML_UseForFiltering = true;               // Use ML to Filter Trades
input bool     ML_UseForSizing = false;                 // Use ML Confidence for Position Sizing
input bool     ML_CollectData = true;                   // Collect Training Data
input double   ML_MinProbability = 0.60;                // Minimum Probability to Enter (0-1)
input double   ML_MinConfidence = 0.50;                 // Minimum Model Confidence (0-1)
input int      ML_RetrainEvery = 100;                   // Auto-Retrain Every N Trades
input bool     ML_AutoExport = true;                    // Auto-Export Data Periodically

//+------------------------------------------------------------------+
//| GLOBAL TRADING OBJECTS                                            |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  position;
CAccountInfo   account;

//+------------------------------------------------------------------+
//| RUNTIME MODIFIABLE SETTINGS (Shadow Variables for GUI)           |
//| Input parameters are constants - these can be modified by GUI    |
//+------------------------------------------------------------------+
bool g_EnableTrading;
bool g_UseVolumeFilter;
bool g_UseSpreadFilter;
bool g_UseSlippageModel;
bool g_UseMTFConfirmation;
bool g_UseSessionFilter;
bool g_UseCorrelationFilter;
bool g_UseNewsFilter;
bool g_UseVolatilityAdaptation;
bool g_UseDynamicRisk;
bool g_UsePatternDecay;
bool g_UseLiquiditySweep;
bool g_UseRetailTrap;
bool g_UseOrderBlockInvalidation;
bool g_UseMarketStructure;
bool g_UsePatternTracking;
bool g_UseParameterAdaptation;
bool g_UseRegimeStrategy;
bool g_MLEnabled;  // Master switch for ML system

// Visual toggles (GUI-controllable - turn chart colors on/off)
bool g_ShowPatternBoxes = true;
bool g_ShowPatternLabels = true;
bool g_ShowLiquidityZones = true;
bool g_ShowFVGZones = true;
bool g_ShowOrderBlocks = true;
bool g_ShowDashboard = true;
bool g_ShowCommentary = true;
bool g_ShowColorLegend = true;

// GUI Minimize State
bool g_GuiMinimized = false;          // GUI panel minimized/maximized state

// Price Action Commentary Blink State
int  g_LatestCommentIndex = -1;       // Index of the latest comment that should blink
bool g_CommentBlinkState = false;     // Alternates true/false for blinking effect
datetime g_LastBlinkTime = 0;         // Last time blink state was toggled

// Alert Settings
input bool EnablePopupAlerts = false;        // Enable Pop-up Alerts
input bool EnableMobileNotifications = false; // Enable Mobile Push Notifications
input bool AlertOnCritical = true;           // Alert on CRITICAL priority messages
input bool AlertOnImportant = true;          // Alert on IMPORTANT priority messages
input bool AlertOnInfo = false;              // Alert on INFO priority messages

//+------------------------------------------------------------------+
//| INDICATOR HANDLES                                                 |
//+------------------------------------------------------------------+
int h_EMA_200;              // 200 EMA for regime detection
int h_EMA_Higher;           // Higher timeframe EMA
int h_ATR;                  // ATR for volatility
int h_ATR_Higher;           // Higher timeframe ATR
int h_Volume_MA;            // Volume moving average

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                      |
//+------------------------------------------------------------------+
enum MARKET_REGIME
{
    REGIME_TREND,           // Strong trending market
    REGIME_RANGE,           // Range-bound market
    REGIME_TRANSITION       // Choppy/transitioning
};

enum MARKET_BIAS
{
    BIAS_BULLISH,           // Bullish bias
    BIAS_BEARISH,           // Bearish bias
    BIAS_NEUTRAL            // Neutral/uncertain
};

enum TRADING_SESSION
{
    SESSION_ASIAN,          // Asian session (00:00-08:00 GMT)
    SESSION_LONDON,         // London session (08:00-13:00 GMT)
    SESSION_OVERLAP,        // London-NY overlap (13:00-16:00 GMT)
    SESSION_NY,             // NY session (16:00-21:00 GMT)
    SESSION_CLOSED          // Market closed
};

enum VOLATILITY_REGIME
{
    VOL_LOW,                // Low volatility (compression)
    VOL_NORMAL,             // Normal volatility
    VOL_HIGH                // High volatility (expansion)
};

enum TRADE_DECISION
{
    DECISION_ENTER,         // Enter the trade
    DECISION_SKIP,          // Skip this setup
    DECISION_WAIT           // Wait for more confirmation
};

enum COMMENTARY_PRIORITY
{
    PRIORITY_CRITICAL = 1,  // Critical information
    PRIORITY_IMPORTANT = 2, // Important updates
    PRIORITY_INFO = 3       // General information
};

//+------------------------------------------------------------------+
//| DATA STRUCTURES (MQL5 Compatible - NO DYNAMIC ARRAYS!)           |
//+------------------------------------------------------------------+

// Pattern Information
struct PatternInfo
{
    string      name;
    string      signal;                 // BUY or SELL
    int         strength;               // 1-5 rating
    datetime    detected_time;
    double      price;
    bool        is_bullish;
    int         bar_index;
};

// Liquidity Zone
struct LiquidityZone
{
    double      price;
    bool        is_high;                // true = resistance, false = support
    datetime    time;
    int         touch_count;
    bool        swept;
};

// Fair Value Gap
struct FairValueGap
{
    int         id;                     // Unique identifier for this FVG
    double      top;
    double      bottom;
    datetime    time;
    bool        is_bullish;
    bool        filled;
    double      fill_percentage;
    int         visit_count;            // Track how many times price visited
    datetime    first_visit_time;       // When price first reached this FVG
    datetime    last_visit_time;        // Most recent visit
    bool        ever_visited;           // Has price ever touched this FVG
};

// Order Block
struct OrderBlock
{
    int         id;                     // Unique identifier for this OB
    double      top;
    double      bottom;
    datetime    time;
    bool        is_bullish;
    int         test_count;
    bool        invalidated;
    datetime    last_test_time;
    int         visit_count;            // Track how many times price visited
    datetime    first_visit_time;       // When price first reached this OB
    bool        ever_visited;           // Has price ever touched this OB
};

// Market Structure
struct MarketStructure
{
    double      last_HH;                // Higher High
    double      last_HL;                // Higher Low
    double      last_LH;                // Lower High
    double      last_LL;                // Lower Low
    string      structure;              // "BULLISH", "BEARISH", "CHOPPY"
    datetime    last_update;
};

// Volume Data (FIX #1)
struct VolumeData
{
    double      current_volume;
    double      average_volume;
    double      volume_ratio;
    bool        above_threshold;
    bool        spike_detected;
};

// Spread Data (FIX #2)
struct SpreadData
{
    double      current_pips;
    double      max_allowed_pips;
    bool        acceptable;
};

// Session Data (FIX #6)
struct SessionData
{
    TRADING_SESSION current_session;
    string      session_name;
    bool        is_tradeable;
    double      expected_volatility;
};

// Volatility Data (FIX #9)
struct VolatilityData
{
    VOLATILITY_REGIME regime;
    double      atr_current;
    double      atr_average;
    double      ratio;
};

// Pattern Performance (FIX #17)
struct PatternPerformance
{
    string      pattern_name;
    MARKET_REGIME regime;
    int         total_trades;
    int         winning_trades;
    double      total_pnl;
    double      avg_rr;
    double      win_rate;
};

// News Event (FIX #8)
struct NewsEvent
{
    datetime    event_time;
    string      currency;
    string      event_name;
    int         importance;
    bool        is_near;
};

// Trade Decision (NO DYNAMIC ARRAYS!)
struct TradeDecision
{
    TRADE_DECISION  decision;
    string          primary_reason;
    string          explanation;
    string          passed_filters[20];     // Fixed array
    string          failed_filters[20];     // Fixed array
    int             passed_count;
    int             failed_count;
    int             confluence_score;
    string          advice;
};

// Commentary Line
struct CommentaryLine
{
    string      text;
    color       text_color;
    datetime    timestamp;
    int         priority;
    bool        is_trading_context;     // True = trading analysis, False = status update
};

// Dashboard Data
struct DashboardData
{
    MARKET_REGIME       regime;
    MARKET_BIAS         bias;
    TRADING_SESSION     session;
    VOLATILITY_REGIME   volatility;
    bool                volume_ok;
    bool                spread_ok;
    bool                session_ok;
    bool                news_ok;
    bool                mtf_ok;
    bool                correlation_ok;
    double              current_risk;
    double              daily_pnl;
    int                 open_trades;
    string              last_pattern;
    int                 confluence_score;
    double              win_rate;
};

//+------------------------------------------------------------------+
//| GLOBAL STATE VARIABLES                                            |
//+------------------------------------------------------------------+

// Market State
MARKET_REGIME       current_regime = REGIME_TREND;
MARKET_BIAS         current_bias = BIAS_NEUTRAL;
TRADING_SESSION     current_session = SESSION_ASIAN;
VOLATILITY_REGIME   current_volatility = VOL_NORMAL;

// Pattern & Zones (Multi-Timeframe)
PatternInfo         active_pattern;      // H4 pattern (main timeframe)
bool                has_active_pattern = false;
PatternInfo         active_pattern_h1;   // H1 pattern
bool                has_active_pattern_h1 = false;
PatternInfo         active_pattern_m15;  // M15 pattern
bool                has_active_pattern_m15 = false;
LiquidityZone       liquidity_zones[100];
int                 liquidity_count = 0;
FairValueGap        fvg_zones[50];
int                 fvg_count = 0;
int                 next_fvg_id = 1;           // Next ID to assign to new FVG
OrderBlock          order_blocks[50];
int                 ob_count = 0;
int                 next_ob_id = 1;            // Next ID to assign to new OB
MarketStructure     market_structure;

// Analysis Results
VolumeData          volume_data;
SpreadData          spread_data;
SessionData         session_data;
VolatilityData      volatility_data;
DashboardData       dashboard;
TradeDecision       last_decision;

// Commentary System
CommentaryLine      commentary_buffer[50];
int                 commentary_count = 0;

// Button Status System (displayed separately near MARKET STATUS)
CommentaryLine      button_status_buffer[10];  // Only keep last 10 button changes
int                 button_status_count = 0;

// NEW: Price Action Commentary System (Educational Explanations)
CommentaryLine      price_action_commentary[100];  // Detailed price action explanations (max 100)
int                 pa_commentary_count = 0;

// Pattern Performance (FIX #17)
PatternPerformance  pattern_performance[100];
int                 performance_count = 0;

// News Events (FIX #8)
NewsEvent           upcoming_news[20];
int                 news_count = 0;

// Risk Management
double              daily_start_balance;
double              weekly_start_balance;
datetime            last_daily_reset;
datetime            last_weekly_reset;
int                 consecutive_losses = 0;
int                 consecutive_wins = 0;
double              peak_balance = 0;

// Adaptive Parameters (FIX #18) - Modified by Trading Profile
int                 dynamic_confluence_required = 3;
double              dynamic_risk_percent = 0.5;
double              dynamic_tp1 = 2.0;
double              dynamic_tp2 = 3.0;
double              dynamic_tp3 = 5.0;

// Profile Shadow Variables (Override input parameters)
ENUM_TIMEFRAMES     g_PreferredTimeframe;
int                 g_PendingOrderExpiration;
double              g_PyramidAddAtR;
double              g_StopLossATR;
double              g_BreakEvenActivationR;
double              g_TrailingStopActivationR;
int                 g_PatternExpiryBars;

// Object prefix
string              prefix = "IGTR3_";

// Trade tracking for partial TP and pyramiding
struct ActiveTrade
{
    ulong       ticket;
    double      entry_price;
    double      stop_loss;
    double      tp1, tp2, tp3;
    bool        tp1_hit;
    bool        tp2_hit;
    bool        tp3_hit;
    bool        breakeven_moved;
    double      original_lot_size;
    datetime    open_time;
    bool        is_buy;
    string      pattern_name;
    int         pyramid_level;              // Track pyramid additions (0 = base, 1-3 = additions)
    int         re_entry_count;             // Track re-entry attempts
    double      best_price_reached;         // Track best price for pyramiding
};

ActiveTrade active_trades[100];
int active_trade_count = 0;

// Re-entry tracking
struct ReEntryPattern
{
    string      pattern_name;
    bool        is_bullish;
    datetime    stop_out_time;
    int         attempts;
    double      original_entry;
    bool        re_entry_active;        // FIX #1: Flag to indicate re-entry mode
};

ReEntryPattern re_entry_patterns[20];
int re_entry_count = 0;

//+------------------------------------------------------------------+
//| Add Button Status (displayed near MARKET STATUS)                 |
//+------------------------------------------------------------------+
void AddButtonStatus(string text, color text_color)
{
    // Shift buffer if full (keep only last 10)
    if(button_status_count >= 10)
    {
        for(int i = 0; i < 9; i++)
            button_status_buffer[i] = button_status_buffer[i+1];
        button_status_count = 9;
    }

    button_status_buffer[button_status_count].text = text;
    button_status_buffer[button_status_count].text_color = text_color;
    button_status_buffer[button_status_count].timestamp = TimeCurrent();
    button_status_buffer[button_status_count].priority = PRIORITY_CRITICAL;
    button_status_count++;
}

//+------------------------------------------------------------------+
//| Add Commentary Line (must be defined before includes)            |
//+------------------------------------------------------------------+
void AddComment(string text, color text_color, int priority)
{
    if(!g_ShowCommentary) return;

    // Button-related messages go to button status display instead
    bool is_button_message = (StringFind(text, "switched") >= 0) ||
                              (StringFind(text, "MODE:") >= 0) ||
                              (StringFind(text, "ENABLED") >= 0) ||
                              (StringFind(text, "INDICATOR MODE") >= 0);

    if(is_button_message)
    {
        AddButtonStatus(text, text_color);
        return;  // Don't add to commentary
    }

    // Shift buffer if full
    if(commentary_count >= 50)
    {
        for(int i = 0; i < 49; i++)
            commentary_buffer[i] = commentary_buffer[i+1];
        commentary_count = 49;
    }

    commentary_buffer[commentary_count].text = text;
    commentary_buffer[commentary_count].text_color = text_color;
    commentary_buffer[commentary_count].timestamp = TimeCurrent();
    commentary_buffer[commentary_count].priority = priority;
    commentary_count++;

    // Print critical messages to terminal
    if(priority == PRIORITY_CRITICAL)
        Print(">>> ", text);
}

//+------------------------------------------------------------------+
//| Format Time as DD.MM.YY.HH:MM                                    |
//+------------------------------------------------------------------+
string FormatTimeDifference(datetime past_time)
{
    MqlDateTime dt;
    TimeToStruct(past_time, dt);

    string day = StringFormat("%02d", dt.day);
    string month = StringFormat("%02d", dt.mon);
    string year = StringFormat("%02d", dt.year % 100);  // Last 2 digits of year
    string hour = StringFormat("%02d", dt.hour);
    string minute = StringFormat("%02d", dt.min);

    return day + "." + month + "." + year + "." + hour + ":" + minute;
}

//+------------------------------------------------------------------+
//| Add Price Action Commentary (Educational Detailed Analysis)      |
//+------------------------------------------------------------------+
void AddPriceActionComment(string text, color text_color, int priority, datetime event_time = 0, bool is_trading_context = true)
{
    if(!g_ShowCommentary) return;

    // Shift buffer if full (max 100 messages)
    if(pa_commentary_count >= 100)
    {
        for(int i = 0; i < 99; i++)
            price_action_commentary[i] = price_action_commentary[i+1];
        pa_commentary_count = 99;

        // CRITICAL FIX: Update g_LatestCommentIndex after shift
        // All indices shifted left by 1, so latest index also shifts
        if(g_LatestCommentIndex > 0)
            g_LatestCommentIndex--;
    }

    price_action_commentary[pa_commentary_count].text = text;
    price_action_commentary[pa_commentary_count].text_color = text_color;
    // Use chart time (bar time) instead of system time for accurate price-time correlation
    price_action_commentary[pa_commentary_count].timestamp = (event_time > 0) ? event_time : iTime(_Symbol, g_PreferredTimeframe, 0);
    price_action_commentary[pa_commentary_count].priority = priority;
    price_action_commentary[pa_commentary_count].is_trading_context = is_trading_context;

    // Mark this as the latest TRADING CONTEXT comment (only for actual analysis, not status updates)
    if(is_trading_context)
    {
        g_LatestCommentIndex = pa_commentary_count;
    }

    pa_commentary_count++;

    // Send alerts based on priority and settings
    bool should_alert = false;
    if(priority == PRIORITY_CRITICAL && AlertOnCritical) should_alert = true;
    else if(priority == PRIORITY_IMPORTANT && AlertOnImportant) should_alert = true;
    else if(priority == PRIORITY_INFO && AlertOnInfo) should_alert = true;

    if(should_alert)
    {
        string alert_msg = _Symbol + ": " + text;

        // Pop-up alert
        if(EnablePopupAlerts)
        {
            Alert(alert_msg);
        }

        // Mobile push notification
        if(EnableMobileNotifications)
        {
            SendNotification(alert_msg);
        }
    }
}

//+------------------------------------------------------------------+
//| INCLUDE SUPPORTING MODULES                                        |
//+------------------------------------------------------------------+
#include "InstitutionalTradingRobot_v3_Functions.mqh"
#include "InstitutionalTradingRobot_v3_Trading.mqh"
#include "InstitutionalTradingRobot_v3_Visual.mqh"
#include "InstitutionalTradingRobot_v3_GUI.mqh"
#include "ML_Modules/ML_MasterIntegration.mqh"

//+------------------------------------------------------------------+
//| GLOBAL ML SYSTEM                                                  |
//+------------------------------------------------------------------+
CMLTradingSystem* ml_system = NULL;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("╔═══════════════════════════════════════════════════════════╗");
    Print("║  INSTITUTIONAL TRADING ROBOT v3.0                        ║");
    Print("║  Complete MQL5 Rewrite - 20 Professional Fixes           ║");
    Print("╚═══════════════════════════════════════════════════════════╝");

    // Configure trade object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);

    // Initialize shadow variables from input parameters (GUI can modify these)
    g_EnableTrading = EnableTrading;
    g_UseVolumeFilter = UseVolumeFilter;
    g_UseSpreadFilter = UseSpreadFilter;
    g_UseSlippageModel = UseSlippageModel;
    g_UseMTFConfirmation = UseMTFConfirmation;
    g_UseSessionFilter = UseSessionFilter;
    g_UseCorrelationFilter = UseCorrelationFilter;
    g_UseNewsFilter = UseNewsFilter;
    g_UseVolatilityAdaptation = UseVolatilityAdaptation;
    g_UseDynamicRisk = UseDynamicRisk;
    g_UsePatternDecay = UsePatternDecay;
    g_UseLiquiditySweep = UseLiquiditySweep;
    g_UseRetailTrap = UseRetailTrap;
    g_UseOrderBlockInvalidation = UseOrderBlockInvalidation;
    g_UseMarketStructure = UseMarketStructure;
    g_UsePatternTracking = UsePatternTracking;
    g_UseParameterAdaptation = UseParameterAdaptation;
    g_UseRegimeStrategy = UseRegimeStrategy;
    g_MLEnabled = ML_Enabled;

    // Apply Trading Profile (Auto-configure all settings based on selected timeframe)
    ApplyTradingProfile();

    // Initialize indicators
    if(!InitializeIndicators())
    {
        Print("ERROR: Failed to initialize indicators");
        return INIT_FAILED;
    }

    // Initialize risk management
    InitializeRiskManagement();

    // Initialize market structure
    ZeroMemory(market_structure);
    market_structure.structure = "INITIALIZING";

    // Load historical pattern performance
    LoadPatternPerformance();

    // Initialize dashboard
    ZeroMemory(dashboard);

    // Initial commentary
    AddComment("═══ SYSTEM INITIALIZED ═══", clrLime, PRIORITY_CRITICAL);
    AddComment("Timeframe: " + EnumToString(g_PreferredTimeframe), clrYellow, PRIORITY_IMPORTANT);
    AddComment("20 Institutional Filters Active", clrAqua, PRIORITY_IMPORTANT);

    // Display mode status
    if(IndicatorMode)
        AddComment("✓ INDICATOR MODE: Visual analysis ENABLED", clrCyan, PRIORITY_IMPORTANT);
    else
        AddComment("○ INDICATOR MODE: Visual analysis DISABLED", clrGray, PRIORITY_INFO);

    if(g_EnableTrading)
    {
        AddComment("✓ AUTO-TRADING: ENABLED", clrLime, PRIORITY_CRITICAL);
        AddComment("ADVICE: Monitor closely - EA will execute trades automatically", clrOrange, PRIORITY_IMPORTANT);
    }
    else
    {
        AddComment("⚠ AUTO-TRADING: DISABLED", clrOrange, PRIORITY_CRITICAL);
        AddComment("ADVICE: Enable trading in settings when ready to go live", clrYellow, PRIORITY_IMPORTANT);
    }

    // Timeframe warning
    if(_Period != g_PreferredTimeframe)
    {
        AddComment("⚠ Chart timeframe mismatch!", clrRed, PRIORITY_CRITICAL);
        AddComment("ADVICE: Switch to " + EnumToString(g_PreferredTimeframe) + " for optimal results", clrYellow, PRIORITY_IMPORTANT);
    }

    Print("✓ All systems operational");

    // Create interactive GUI with clickable buttons
    CreateInteractiveDashboard();

    // Initialize button status display
    DrawButtonStatus();

    Print("✓ Interactive GUI created - Click buttons to toggle settings!");

    //═══════════════════════════════════════════════════════════════
    // MACHINE LEARNING SYSTEM INITIALIZATION
    //═══════════════════════════════════════════════════════════════
    if(ML_Enabled)
    {
        Print("\n╔═══════════════════════════════════════════════════════════╗");
        Print("║         INITIALIZING MACHINE LEARNING SYSTEM              ║");
        Print("╚═══════════════════════════════════════════════════════════╝");

        ml_system = new CMLTradingSystem();

        MLConfig ml_config;
        ml_config.enabled = ML_Enabled;
        ml_config.use_for_filtering = ML_UseForFiltering;
        ml_config.use_for_sizing = ML_UseForSizing;
        ml_config.collect_training_data = ML_CollectData;
        ml_config.min_probability_threshold = ML_MinProbability;
        ml_config.min_confidence_threshold = ML_MinConfidence;
        ml_config.retrain_every_n_trades = ML_RetrainEvery;
        ml_config.auto_export_data = ML_AutoExport;

        if(ml_system.Initialize(ml_config))
        {
            Print("✓ ML System initialized successfully");
            AddComment("🤖 ML SYSTEM ACTIVE", clrLime, PRIORITY_CRITICAL);
        }
        else
        {
            Print("WARNING: ML System initialization failed");
            AddComment("⚠ ML System init failed - continuing without ML", clrOrange, PRIORITY_IMPORTANT);
        }
    }
    else
    {
        Print("ML System disabled (ML_Enabled = false)");
    }

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release indicators
    if(h_EMA_200 != INVALID_HANDLE) IndicatorRelease(h_EMA_200);
    if(h_EMA_Higher != INVALID_HANDLE) IndicatorRelease(h_EMA_Higher);
    if(h_ATR != INVALID_HANDLE) IndicatorRelease(h_ATR);
    if(h_ATR_Higher != INVALID_HANDLE) IndicatorRelease(h_ATR_Higher);
    if(h_Volume_MA != INVALID_HANDLE) IndicatorRelease(h_Volume_MA);

    // Save pattern performance
    SavePatternPerformance();

    // ML System cleanup and final report
    if(ml_system != NULL)
    {
        Print("\n╔═══════════════════════════════════════════════════════════╗");
        Print("║         ML SYSTEM SHUTDOWN - FINAL REPORT                 ║");
        Print("╚═══════════════════════════════════════════════════════════╝");

        ml_system.PrintPerformanceReport();
        ml_system.ExportEquityCurve();

        delete ml_system;
        ml_system = NULL;

        Print("✓ ML System shutdown complete");
    }

    // Clean up chart objects
    ObjectsDeleteAll(0, prefix);

    Print("═══════════════════════════════════════════════════");
    Print("  Institutional Trading Robot v3.0 Stopped");
    Print("═══════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Monitor closed positions for ML training data                    |
//+------------------------------------------------------------------+
void MonitorClosedPositions()
{
    static ulong last_processed_ticket = 0;

    // Select deals from today
    datetime from = iTime(_Symbol, PERIOD_D1, 0);
    datetime to = TimeCurrent();

    if(!HistorySelect(from, to))
        return;

    // Check recent deals
    int total_deals = HistoryDealsTotal();

    for(int i = total_deals - 1; i >= 0 && i >= total_deals - 10; i--)
    {
        ulong deal_ticket = HistoryDealGetTicket(i);
        if(deal_ticket == 0) continue;

        // Skip if already processed
        if(deal_ticket <= last_processed_ticket)
            continue;

        // Check if this is an exit deal (OUT)
        if(HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT)
            continue;

        // Check if it's our EA's magic number
        if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != MagicNumber)
            continue;

        // Get position ticket to find entry details
        ulong position_id = HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID);

        // Select position history
        if(!HistorySelectByPosition(position_id))
            continue;

        // Find entry deal
        datetime entry_time = 0;
        double entry_price = 0;
        double volume = 0;
        bool is_buy = false;

        for(int j = 0; j < HistoryDealsTotal(); j++)
        {
            ulong entry_deal = HistoryDealGetTicket(j);
            if(HistoryDealGetInteger(entry_deal, DEAL_POSITION_ID) == position_id &&
               HistoryDealGetInteger(entry_deal, DEAL_ENTRY) == DEAL_ENTRY_IN)
            {
                entry_time = (datetime)HistoryDealGetInteger(entry_deal, DEAL_TIME);
                entry_price = HistoryDealGetDouble(entry_deal, DEAL_PRICE);
                volume = HistoryDealGetDouble(entry_deal, DEAL_VOLUME);
                is_buy = (HistoryDealGetInteger(entry_deal, DEAL_TYPE) == DEAL_TYPE_BUY);
                break;
            }
        }

        // Get exit details
        datetime exit_time = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
        double exit_price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
        double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);

        // Get SL from position (if available)
        double stop_loss = 0;
        if(HistorySelectByPosition(position_id))
        {
            for(int j = 0; j < HistoryOrdersTotal(); j++)
            {
                ulong order_ticket = HistoryOrderGetTicket(j);
                if(HistoryOrderGetInteger(order_ticket, ORDER_POSITION_ID) == position_id)
                {
                    stop_loss = HistoryOrderGetDouble(order_ticket, ORDER_SL);
                    break;
                }
            }
        }

        // Extract features at exit time (best effort)
        MLFeatureVector features;
        if(ml_system.ExtractCurrentFeatures(features))
        {
            // Record trade exit for ML training
            ml_system.OnTradeExit(features, entry_time, exit_time,
                                 entry_price, exit_price, stop_loss,
                                 is_buy, volume, 0, 0); // MAE/MFE set to 0 for now

            Print("ML: Recorded closed position #", position_id,
                  " | Profit: ", DoubleToString(profit, 2),
                  " | Samples: ", ml_system.GetSampleCount());
        }

        last_processed_ticket = deal_ticket;
    }
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // ML: Monitor closed positions for training data collection (always run)
    if(ml_system != NULL)
        MonitorClosedPositions();

    // Run price action analysis on EVERY TICK (uses edge detection to avoid spam)
    // This ensures commentary is responsive and updates as events happen
    PerformPriceActionAnalysis();

    // Check for new bar on preferred timeframe (configured by profile)
    static datetime last_bar_time = 0;
    datetime current_bar_time = iTime(_Symbol, g_PreferredTimeframe, 0);
    bool is_new_bar = (current_bar_time != last_bar_time);

    if(!is_new_bar)
    {
        // Not a new bar - skip trading logic but still update visuals
        UpdateDashboard();
        DrawDashboard();
        DrawBigCommentary();
        DrawButtonStatus();
        DrawMLStatus();
        DrawColorLegend();
        DrawPriceActionCommentary();
        return;
    }

    last_bar_time = current_bar_time;

    // Clear commentary for new bar
    commentary_count = 0;
    AddComment("═══ NEW BAR: " + TimeToString(current_bar_time) + " ═══", clrWhite, PRIORITY_IMPORTANT);

    //═══════════════════════════════════════════════════════════════
    // PHASE 0: PRE-FLIGHT CHECKS
    //═══════════════════════════════════════════════════════════════

    AddComment("─── Phase 0: Pre-Flight Checks ───", clrAqua, PRIORITY_IMPORTANT);

    // FIX #2: Spread Check
    if(g_UseSpreadFilter)
    {
        AnalyzeSpread();
        if(!spread_data.acceptable)
        {
            AddComment("⛔ SPREAD TOO WIDE: " + DoubleToString(spread_data.current_pips, 1) + " pips", clrRed, PRIORITY_CRITICAL);
            AddComment("ADVICE: Wait for spread to tighten (off hours/low liquidity)", clrOrange, PRIORITY_IMPORTANT);
            dashboard.spread_ok = false;
        }
        else
        {
            AddComment("✓ Spread: " + DoubleToString(spread_data.current_pips, 1) + " pips (OK)", clrLime, PRIORITY_INFO);
            dashboard.spread_ok = true;
        }
    }

    // FIX #6: Session Check
    if(UseSessionFilter)
    {
        AnalyzeSession();
        if(!session_data.is_tradeable)
        {
            AddComment("⏸ " + session_data.session_name + " Session - Not Trading", clrYellow, PRIORITY_IMPORTANT);
            AddComment("ADVICE: " + session_data.session_name + " has low volatility/liquidity", clrOrange, PRIORITY_INFO);
            dashboard.session_ok = false;
        }
        else
        {
            AddComment("✓ " + session_data.session_name + " Session (Active)", clrLime, PRIORITY_INFO);
            dashboard.session_ok = true;
        }
    }

    // FIX #8: News Calendar Check
    if(UseNewsFilter)
    {
        CheckEconomicCalendar();
        bool news_clear = true;

        for(int i = 0; i < news_count; i++)
        {
            if(upcoming_news[i].is_near)
            {
                int minutes_away = (int)((upcoming_news[i].event_time - TimeCurrent()) / 60);
                AddComment("📰 HIGH IMPACT NEWS IN " + IntegerToString(minutes_away) + " MIN", clrRed, PRIORITY_CRITICAL);
                AddComment("Event: " + upcoming_news[i].event_name, clrOrange, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Avoid trading around major economic events", clrYellow, PRIORITY_IMPORTANT);
                news_clear = false;
                break;
            }
        }

        dashboard.news_ok = news_clear;
        if(news_clear)
            AddComment("✓ Economic Calendar Clear", clrLime, PRIORITY_INFO);
    }

    //═══════════════════════════════════════════════════════════════
    // PHASE 1: MARKET REGIME & CONTEXT ANALYSIS
    //═══════════════════════════════════════════════════════════════

    AddComment("─── Phase 1: Market Context ───", clrAqua, PRIORITY_IMPORTANT);

    // FIX #9: Volatility Regime
    if(UseVolatilityAdaptation)
    {
        AnalyzeVolatilityRegime();

        string vol_text = "Volatility: ";
        color vol_color = clrWhite;

        switch(current_volatility)
        {
            case VOL_LOW:
                vol_text += "LOW (Compression)";
                vol_color = clrYellow;
                AddComment(vol_text, vol_color, PRIORITY_INFO);
                AddComment("ADVICE: Expect expansion soon - Tighten stops, smaller targets", clrOrange, PRIORITY_IMPORTANT);
                break;

            case VOL_HIGH:
                vol_text += "HIGH (Expansion)";
                vol_color = clrOrange;
                AddComment(vol_text, vol_color, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Reduce size, widen stops, be very selective", clrRed, PRIORITY_CRITICAL);
                // Automatically adapt parameters
                dynamic_risk_percent = BaseRiskPercent * 0.5;
                dynamic_confluence_required = 5;
                break;

            case VOL_NORMAL:
                vol_text += "NORMAL";
                vol_color = clrLime;
                AddComment(vol_text, vol_color, PRIORITY_INFO);
                break;
        }
    }

    // Detect Market Regime
    DetectMarketRegime();

    string regime_text = "Regime: ";
    string regime_detail = "";
    color regime_color = clrWhite;

    switch(current_regime)
    {
        case REGIME_TREND:
            regime_text += "TRENDING";
            regime_color = clrLime;
            regime_detail = current_bias == BIAS_BULLISH ? " (Uptrend)" : " (Downtrend)";
            AddComment(regime_text + regime_detail, regime_color, PRIORITY_IMPORTANT);
            AddComment("ADVICE: Momentum-based - Ride the trend, trail stops", clrAqua, PRIORITY_IMPORTANT);
            break;

        case REGIME_RANGE:
            regime_text += "RANGING";
            regime_color = clrYellow;
            AddComment(regime_text + " (Sideways consolidation)", regime_color, PRIORITY_IMPORTANT);
            AddComment("ADVICE: Mean reversion - Fade extremes, tight targets", clrAqua, PRIORITY_IMPORTANT);
            break;

        case REGIME_TRANSITION:
            regime_text += "CHOPPY";
            regime_color = clrOrange;
            AddComment(regime_text + " (Uncertain direction)", regime_color, PRIORITY_IMPORTANT);
            AddComment("ADVICE: Low probability environment - Skip or wait for clarity", clrRed, PRIORITY_CRITICAL);
            break;
    }

    // Determine Market Bias
    DetermineBias();

    string bias_text = "Bias: ";
    color bias_color = clrWhite;

    switch(current_bias)
    {
        case BIAS_BULLISH:
            bias_text += "BULLISH (Look for longs)";
            bias_color = clrLime;
            break;
        case BIAS_BEARISH:
            bias_text += "BEARISH (Look for shorts)";
            bias_color = clrRed;
            break;
        case BIAS_NEUTRAL:
            bias_text += "NEUTRAL (Wait for direction)";
            bias_color = clrGray;
            break;
    }
    AddComment(bias_text, bias_color, PRIORITY_IMPORTANT);

    // FIX #16: Market Structure
    if(UseMarketStructure)
    {
        UpdateMarketStructure();
        AddComment("Structure: " + market_structure.structure, clrWhite, PRIORITY_INFO);
    }

    //═══════════════════════════════════════════════════════════════
    // PHASE 2: LIQUIDITY MAPPING
    //═══════════════════════════════════════════════════════════════

    AddComment("─── Phase 2: Liquidity Mapping ───", clrAqua, PRIORITY_IMPORTANT);

    MapLiquidityZones();
    AddComment("Liquidity Zones: " + IntegerToString(liquidity_count) + " identified", clrWhite, PRIORITY_INFO);

    DetectFairValueGaps();
    int unfilled_fvg = 0;
    for(int i = 0; i < fvg_count; i++)
        if(!fvg_zones[i].filled) unfilled_fvg++;

    if(unfilled_fvg > 0)
        AddComment("Fair Value Gaps: " + IntegerToString(unfilled_fvg) + " unfilled", clrAqua, PRIORITY_INFO);

    DetectOrderBlocks();
    int active_ob = 0;
    for(int i = 0; i < ob_count; i++)
        if(!order_blocks[i].invalidated) active_ob++;

    if(active_ob > 0)
        AddComment("Order Blocks: " + IntegerToString(active_ob) + " active", clrAqua, PRIORITY_INFO);

    // Draw zones (functions check their own toggles)
    DrawLiquidityZones();
    DrawFVGZones();
    DrawOrderBlocks();

    //═══════════════════════════════════════════════════════════════
    // PHASE 3: PATTERN DETECTION
    //═══════════════════════════════════════════════════════════════

    AddComment("─── Phase 3: Pattern Detection ───", clrAqua, PRIORITY_IMPORTANT);

    ScanForCandlestickPatterns();  // Scan H4 (main timeframe)
    ScanLowerTimeframes();         // Scan H1 and M15

    if(has_active_pattern)
    {
        string direction_arrow = active_pattern.is_bullish ? "↑" : "↓";
        AddComment("✓ PATTERN: " + active_pattern.name + " " + direction_arrow + " [" +
                  IntegerToString(active_pattern.strength) + "★/" + IntegerToString(5) + "]",
                  active_pattern.is_bullish ? clrLime : clrRed, PRIORITY_CRITICAL);

        // Show multi-timeframe patterns if available
        if(has_active_pattern_h1)
            AddComment("  H1: " + active_pattern_h1.name + " [" + IntegerToString(active_pattern_h1.strength) + "★]",
                      active_pattern_h1.is_bullish ? clrLime : clrRed, PRIORITY_INFO);

        if(has_active_pattern_m15)
            AddComment("  M15: " + active_pattern_m15.name + " [" + IntegerToString(active_pattern_m15.strength) + "★]",
                      active_pattern_m15.is_bullish ? clrLime : clrRed, PRIORITY_INFO);

        // Draw pattern visualization
        DrawPatternBox(active_pattern);
        DrawPatternLabel(active_pattern);

        // FIX #11: Pattern Decay Check
        if(UsePatternDecay)
        {
            if(!IsPatternValid())
            {
                int bars_old = Bars(_Symbol, PreferredTimeframe, active_pattern.detected_time, TimeCurrent()) - 1;
                AddComment("⚠ Pattern EXPIRED (" + IntegerToString(bars_old) + " bars old) - Need fresh setup",
                          clrOrange, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Stale patterns lose edge - Only trade fresh signals", clrYellow, PRIORITY_INFO);
                has_active_pattern = false;
            }
        }
    }
    else
    {
        AddComment("No valid patterns detected - Waiting...", clrGray, PRIORITY_INFO);
        AddComment("ADVICE: Patience is key - Wait for high-quality setups", clrYellow, PRIORITY_INFO);
    }

    //═══════════════════════════════════════════════════════════════
    // PHASE 4: INSTITUTIONAL FILTERS & CONFLUENCE
    //═══════════════════════════════════════════════════════════════

    if(has_active_pattern)
    {
        AddComment("─── Phase 4: Institutional Filters ───", clrAqua, PRIORITY_IMPORTANT);

        // FIX #1: Volume Analysis
        if(g_UseVolumeFilter)
        {
            AnalyzeVolume();

            if(volume_data.above_threshold)
            {
                AddComment("✓ Volume: " + DoubleToString(volume_data.volume_ratio, 1) + "x average (Strong)", clrLime, PRIORITY_INFO);
                dashboard.volume_ok = true;
            }
            else
            {
                AddComment("⚠ Volume: Below threshold - Weak conviction", clrOrange, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Low volume patterns fail more often - Wait for confirmation", clrYellow, PRIORITY_INFO);
                dashboard.volume_ok = false;
            }
        }

        // FIX #5: Multi-Timeframe Confirmation
        if(UseMTFConfirmation)
        {
            bool mtf_aligned = CheckMultiTimeframeAlignment();

            if(mtf_aligned)
            {
                AddComment("✓ MTF: Higher timeframe confirms direction", clrLime, PRIORITY_INFO);
                dashboard.mtf_ok = true;
            }
            else
            {
                AddComment("⚠ MTF: Higher timeframe CONFLICTS", clrOrange, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Counter-trend trades have lower win rate", clrYellow, PRIORITY_INFO);
                dashboard.mtf_ok = false;
            }
        }

        // FIX #7: Correlation Check
        if(UseCorrelationFilter)
        {
            bool corr_ok = CheckPortfolioCorrelation();

            if(!corr_ok)
            {
                AddComment("⛔ CORRELATION: Portfolio too concentrated", clrRed, PRIORITY_CRITICAL);
                AddComment("ADVICE: Already exposed to this currency - Skip to manage risk", clrOrange, PRIORITY_IMPORTANT);
                dashboard.correlation_ok = false;
            }
            else
            {
                AddComment("✓ Correlation: Portfolio exposure OK", clrLime, PRIORITY_INFO);
                dashboard.correlation_ok = true;
            }
        }

        // FIX #13: Liquidity Sweep Detection
        if(UseLiquiditySweep)
        {
            bool sweep_detected = CheckLiquiditySweep(active_pattern.is_bullish);

            if(sweep_detected)
            {
                AddComment("✓ LIQUIDITY SWEEP: Stop hunt confirmed!", clrLime, PRIORITY_IMPORTANT);
                AddComment("ADVICE: Smart money entry - High probability setup", clrAqua, PRIORITY_IMPORTANT);
            }
        }

        // FIX #14: Retail Trap Detection
        if(UseRetailTrap)
        {
            bool is_trap = DetectRetailTrap();

            if(is_trap)
            {
                AddComment("⛔ RETAIL TRAP: False breakout detected", clrRed, PRIORITY_CRITICAL);
                AddComment("ADVICE: Smart money fading retail - SKIP THIS SETUP", clrOrange, PRIORITY_CRITICAL);
                has_active_pattern = false;
                // Skip further analysis
                UpdateDashboard();
                DrawDashboard();  // Checks g_ShowDashboard internally
                DrawBigCommentary();  // Checks g_ShowCommentary internally
                DrawButtonStatus();  // Always show button status
                DrawColorLegend();  // Checks g_ShowColorLegend internally
                return;
            }
        }

        // Evaluate Full Confluence
        TradeDecision decision = EvaluateTradeDecision();
        last_decision = decision;

        // Enhanced confluence reporting
        int factors_needed = dynamic_confluence_required - decision.confluence_score;
        string confluence_status = "";

        if(decision.confluence_score >= dynamic_confluence_required)
            confluence_status = " ✓ THRESHOLD MET";
        else if(factors_needed == 1)
            confluence_status = " (Need 1 more)";
        else
            confluence_status = " (Need " + IntegerToString(factors_needed) + " more)";

        AddComment("═══ CONFLUENCE: " + IntegerToString(decision.confluence_score) + "/" +
                  IntegerToString(dynamic_confluence_required) + confluence_status + " ═══",
                  decision.confluence_score >= dynamic_confluence_required ? clrLime : clrOrange,
                  PRIORITY_CRITICAL);

        // Show passed filters (limited to 3 for brevity due to 5-line limit)
        if(decision.passed_count > 0)
        {
            string passed_summary = "✓ PASSED (" + IntegerToString(decision.passed_count) + "): ";
            for(int i = 0; i < decision.passed_count && i < 3; i++)
            {
                if(i > 0) passed_summary += ", ";
                passed_summary += decision.passed_filters[i];
            }
            if(decision.passed_count > 3)
                passed_summary += "... (+" + IntegerToString(decision.passed_count - 3) + " more)";

            AddComment(passed_summary, clrLime, PRIORITY_IMPORTANT);
        }

        // Show failed filters (limited to 3 for brevity)
        if(decision.failed_count > 0)
        {
            string failed_summary = "✗ FAILED (" + IntegerToString(decision.failed_count) + "): ";
            for(int i = 0; i < decision.failed_count && i < 3; i++)
            {
                if(i > 0) failed_summary += ", ";
                failed_summary += decision.failed_filters[i];
            }
            if(decision.failed_count > 3)
                failed_summary += "... (+" + IntegerToString(decision.failed_count - 3) + " more)";

            AddComment(failed_summary, clrRed, PRIORITY_IMPORTANT);
        }

        // Decision & Advice - WITH FULL DETAILS
        string decision_text = "";
        color decision_color = clrWhite;

        switch(decision.decision)
        {
            case DECISION_ENTER:
                decision_text = "🎯 DECISION: ENTER TRADE";
                decision_color = clrLime;
                break;
            case DECISION_SKIP:
                decision_text = "⛔ DECISION: SKIP TRADE";
                decision_color = clrRed;
                break;
            case DECISION_WAIT:
                decision_text = "⏸ DECISION: WAIT FOR MORE CONFIRMATION";
                decision_color = clrYellow;
                break;
        }

        AddComment(decision_text, decision_color, PRIORITY_CRITICAL);

        // Add detailed signal information
        string signal_direction = active_pattern.is_bullish ? "BUY" : "SELL";
        color signal_color = active_pattern.is_bullish ? clrLime : clrRed;
        AddComment("SIGNAL: " + signal_direction + " (" + EnumToString(PreferredTimeframe) + ")",
                  signal_color, PRIORITY_CRITICAL);

        // Add timestamp
        datetime current_time = TimeCurrent();
        AddComment("TIME: " + TimeToString(current_time, TIME_DATE|TIME_MINUTES),
                  clrWhite, PRIORITY_IMPORTANT);

        // Show aligned factors in REASON
        string factors_aligned = "";
        for(int i = 0; i < decision.passed_count && i < 5; i++)  // Show max 5 factors
        {
            if(i > 0) factors_aligned += ", ";
            factors_aligned += decision.passed_filters[i];
        }

        AddComment("REASON: " + IntegerToString(decision.confluence_score) + " factors aligned - " +
                  decision.explanation, clrWhite, PRIORITY_IMPORTANT);

        if(decision.passed_count > 0)
            AddComment("ALIGNED: " + factors_aligned, clrLime, PRIORITY_IMPORTANT);

        if(decision.advice != "")
            AddComment("ADVICE: " + decision.advice, clrAqua, PRIORITY_IMPORTANT);

        //═══════════════════════════════════════════════════════════
        // PHASE 5: TRADE EXECUTION
        //═══════════════════════════════════════════════════════════

        if(decision.decision == DECISION_ENTER && g_EnableTrading)
        {
            AddComment("─── Phase 5: Trade Execution ───", clrAqua, PRIORITY_IMPORTANT);

            // Check risk limits
            if(!CheckRiskLimits())
            {
                AddComment("⛔ RISK LIMIT REACHED - Cannot trade", clrRed, PRIORITY_CRITICAL);
                AddComment("ADVICE: Daily/weekly loss limit hit - Stop trading now", clrOrange, PRIORITY_CRITICAL);
            }
            else
            {
                // FIX #10: Dynamic Risk Calculation
                double risk_percent = UseDynamicRisk ? CalculateDynamicRisk() : BaseRiskPercent;
                AddComment("Risk Allocation: " + DoubleToString(risk_percent, 2) + "%", clrYellow, PRIORITY_IMPORTANT);

                // FIX #3: Slippage Modeling
                double expected_slippage = 0;
                if(UseSlippageModel)
                {
                    expected_slippage = CalculateExpectedSlippage();
                    AddComment("Expected Slippage: " + DoubleToString(expected_slippage * 10000, 1) + " pips", clrYellow, PRIORITY_INFO);
                }

                // Execute trade
                ExecuteTrade(risk_percent, expected_slippage);
            }
        }
    }

    //═══════════════════════════════════════════════════════════════
    // PHASE 6: TRADE MANAGEMENT
    //═══════════════════════════════════════════════════════════════

    if(PositionsTotal() > 0)
    {
        // Check profit targets first (close all if targets hit)
        if(CheckAccountProfitTarget()) return;  // Account target hit, positions closed
        if(CheckSymbolProfitTarget()) return;   // Symbol target hit, positions closed

        // Continue with normal trade management
        ManageOpenTrades();
    }

    //═══════════════════════════════════════════════════════════════
    // PHASE 7: LEARNING & ADAPTATION
    //═══════════════════════════════════════════════════════════════

    // FIX #18: Parameter Adaptation
    if(UseParameterAdaptation)
    {
        AdaptParameters();
    }

    //═══════════════════════════════════════════════════════════════
    // VISUAL UPDATES (Updated on every new bar after trading logic)
    //═══════════════════════════════════════════════════════════════

    // Update & Draw Dashboard
    UpdateDashboard();
    DrawDashboard();  // Function checks g_ShowDashboard internally

    // Draw BIG READABLE Commentary
    DrawBigCommentary();  // Function checks g_ShowCommentary internally

    // Draw Button Status (always show)
    DrawButtonStatus();

    // Draw ML STATUS & COMMENTARY (always show when ML enabled)
    DrawMLStatus();

    // Draw Color Legend
    DrawColorLegend();  // Function checks g_ShowColorLegend internally

    // Draw PRICE ACTION COMMENTARY (Educational) - with arrow indicator on latest
    DrawPriceActionCommentary();  // Function checks g_ShowCommentary internally
}

//+------------------------------------------------------------------+
//| Initialize All Indicators                                         |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
    // Current timeframe indicators (use profile-configured timeframe)
    h_EMA_200 = iMA(_Symbol, g_PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE);
    h_ATR = iATR(_Symbol, g_PreferredTimeframe, 14);
    h_Volume_MA = iMA(_Symbol, g_PreferredTimeframe, 20, 0, MODE_SMA, VOLUME_TICK);

    // Higher timeframe indicators for MTF confirmation
    ENUM_TIMEFRAMES higher_tf = GetHigherTimeframe(g_PreferredTimeframe);
    h_EMA_Higher = iMA(_Symbol, higher_tf, 200, 0, MODE_EMA, PRICE_CLOSE);
    h_ATR_Higher = iATR(_Symbol, higher_tf, 14);

    // Validate all handles
    if(h_EMA_200 == INVALID_HANDLE || h_ATR == INVALID_HANDLE ||
       h_Volume_MA == INVALID_HANDLE || h_EMA_Higher == INVALID_HANDLE ||
       h_ATR_Higher == INVALID_HANDLE)
    {
        Print("ERROR: Failed to create indicator handles");
        return false;
    }

    AddComment("✓ Indicators initialized successfully", clrLime, PRIORITY_INFO);
    return true;
}

//+------------------------------------------------------------------+
//| Initialize Risk Management                                        |
//+------------------------------------------------------------------+
void InitializeRiskManagement()
{
    daily_start_balance = account.Balance();
    weekly_start_balance = account.Balance();
    peak_balance = account.Balance();
    last_daily_reset = TimeCurrent();
    last_weekly_reset = TimeCurrent();

    AddComment("Risk: " + DoubleToString(BaseRiskPercent, 2) + "% per trade, Max " +
              IntegerToString(MaxOpenTrades) + " positions", clrAqua, PRIORITY_INFO);
}

//+------------------------------------------------------------------+
//| Apply Trading Profile (Auto-Configure All Settings)              |
//+------------------------------------------------------------------+
void ApplyTradingProfile()
{
    string profile_name = "";

    switch(TradingProfile)
    {
        case PROFILE_M5_SCALPING:
            profile_name = "M5 SCALPING";
            g_PreferredTimeframe = PERIOD_M5;
            g_PendingOrderExpiration = 2;               // 2 hours
            dynamic_tp1 = 1.0;                          // 1R target
            dynamic_tp2 = 1.5;                          // 1.5R target
            dynamic_tp3 = 2.0;                          // 2R target
            g_PyramidAddAtR = 0.8;                      // Add at 0.8R
            dynamic_risk_percent = 0.3;                 // Lower risk for M5
            dynamic_confluence_required = 7;            // HIGH confluence for M5
            g_PatternExpiryBars = 3;                    // 15 minutes
            g_StopLossATR = 1.5;                        // Tighter stops
            g_BreakEvenActivationR = 0.8;               // Quick breakeven
            g_TrailingStopActivationR = 1.0;            // Start trailing at 1R

            AddComment("🎯 PROFILE: M5 Scalping - Fast execution, tight stops, high confluence (7+)", clrGold, PRIORITY_CRITICAL);
            AddComment("→ Optimized for: Quick scalps, 1-2R targets, 2-hour pending expiry", clrAqua, PRIORITY_IMPORTANT);
            break;

        case PROFILE_M15_INTRADAY:
            profile_name = "M15 INTRADAY";
            g_PreferredTimeframe = PERIOD_M15;
            g_PendingOrderExpiration = 4;               // 4 hours
            dynamic_tp1 = 1.2;                          // 1.2R target
            dynamic_tp2 = 1.8;                          // 1.8R target
            dynamic_tp3 = 2.5;                          // 2.5R target
            g_PyramidAddAtR = 1.0;                      // Add at 1R
            dynamic_risk_percent = 0.4;                 // Moderate risk
            dynamic_confluence_required = 6;            // High confluence
            g_PatternExpiryBars = 3;                    // 45 minutes
            g_StopLossATR = 1.8;                        // Moderate stops
            g_BreakEvenActivationR = 0.9;               // Quick breakeven
            g_TrailingStopActivationR = 1.0;            // Start trailing at 1R

            AddComment("🎯 PROFILE: M15 Intraday - Balanced scalping, moderate confluence (6+)", clrGold, PRIORITY_CRITICAL);
            AddComment("→ Optimized for: Intraday moves, 1.2-2.5R targets, 4-hour expiry", clrAqua, PRIORITY_IMPORTANT);
            break;

        case PROFILE_H1_SWING:
            profile_name = "H1 SWING";
            g_PreferredTimeframe = PERIOD_H1;
            g_PendingOrderExpiration = 12;              // 12 hours
            dynamic_tp1 = 1.5;                          // 1.5R target
            dynamic_tp2 = 2.5;                          // 2.5R target
            dynamic_tp3 = 3.5;                          // 3.5R target
            g_PyramidAddAtR = 1.2;                      // Add at 1.2R
            dynamic_risk_percent = 0.5;                 // Standard risk
            dynamic_confluence_required = 5;            // Moderate confluence
            g_PatternExpiryBars = 3;                    // 3 hours
            g_StopLossATR = 2.0;                        // Standard stops
            g_BreakEvenActivationR = 1.0;               // Standard breakeven
            g_TrailingStopActivationR = 1.0;            // Start trailing at 1R

            AddComment("🎯 PROFILE: H1 Swing - Medium-term trades, balanced confluence (5+)", clrGold, PRIORITY_CRITICAL);
            AddComment("→ Optimized for: Swing trades, 1.5-3.5R targets, 12-hour expiry", clrAqua, PRIORITY_IMPORTANT);
            break;

        case PROFILE_H4_POSITION:
            profile_name = "H4 POSITION (Default)";
            g_PreferredTimeframe = PERIOD_H4;
            g_PendingOrderExpiration = 24;              // 24 hours
            dynamic_tp1 = 2.0;                          // 2R target
            dynamic_tp2 = 3.0;                          // 3R target
            dynamic_tp3 = 5.0;                          // 5R target
            g_PyramidAddAtR = 1.5;                      // Add at 1.5R
            dynamic_risk_percent = 0.5;                 // Standard risk
            dynamic_confluence_required = 3;            // Lower confluence (institutional)
            g_PatternExpiryBars = 3;                    // 12 hours
            g_StopLossATR = 2.0;                        // Standard stops
            g_BreakEvenActivationR = 1.0;               // Standard breakeven
            g_TrailingStopActivationR = 1.0;            // Start trailing at 1R

            AddComment("🎯 PROFILE: H4 Position - Institutional trading, lower confluence (3+)", clrGold, PRIORITY_CRITICAL);
            AddComment("→ Optimized for: Position trades, 2-5R targets, 24-hour expiry", clrAqua, PRIORITY_IMPORTANT);
            break;

        case PROFILE_D1_INVESTOR:
            profile_name = "D1 INVESTOR";
            g_PreferredTimeframe = PERIOD_D1;
            g_PendingOrderExpiration = 72;              // 3 days
            dynamic_tp1 = 2.5;                          // 2.5R target
            dynamic_tp2 = 4.0;                          // 4R target
            dynamic_tp3 = 6.0;                          // 6R target
            g_PyramidAddAtR = 2.0;                      // Add at 2R
            dynamic_risk_percent = 0.5;                 // Standard risk
            dynamic_confluence_required = 3;            // Lower confluence
            g_PatternExpiryBars = 3;                    // 3 days
            g_StopLossATR = 2.5;                        // Wider stops
            g_BreakEvenActivationR = 1.2;               // Patient breakeven
            g_TrailingStopActivationR = 1.5;            // Patient trailing

            AddComment("🎯 PROFILE: D1 Investor - Long-term positions, patient targets (2.5-6R)", clrGold, PRIORITY_CRITICAL);
            AddComment("→ Optimized for: Multi-day trades, 3-day expiry, wider stops", clrAqua, PRIORITY_IMPORTANT);
            break;

        case PROFILE_CUSTOM:
            profile_name = "CUSTOM (Manual)";
            // Use input parameters as-is (no override)
            g_PreferredTimeframe = PreferredTimeframe;
            g_PendingOrderExpiration = PendingOrderExpiration;
            dynamic_tp1 = TP1_RiskReward;
            dynamic_tp2 = TP2_RiskReward;
            dynamic_tp3 = TP3_RiskReward;
            g_PyramidAddAtR = PyramidAddAtR;
            dynamic_risk_percent = BaseRiskPercent;
            dynamic_confluence_required = 3;            // Default
            g_PatternExpiryBars = PatternExpiryBars;
            g_StopLossATR = StopLossATR;
            g_BreakEvenActivationR = BreakEvenActivationR;
            g_TrailingStopActivationR = TrailingStopActivationR;

            AddComment("🎯 PROFILE: Custom - Using manual input parameters", clrGold, PRIORITY_CRITICAL);
            AddComment("→ All settings controlled by user input values", clrAqua, PRIORITY_IMPORTANT);
            break;
    }

    // Log the applied profile
    Print("════════════════════════════════════════════════════════");
    Print("  TRADING PROFILE APPLIED: ", profile_name);
    Print("════════════════════════════════════════════════════════");
    Print("  Timeframe: ", EnumToString(g_PreferredTimeframe));
    Print("  Pending Expiry: ", g_PendingOrderExpiration, " hours");
    Print("  TP Targets: ", dynamic_tp1, "R / ", dynamic_tp2, "R / ", dynamic_tp3, "R");
    Print("  Pyramid At: ", g_PyramidAddAtR, "R");
    Print("  Base Risk: ", dynamic_risk_percent, "%");
    Print("  Min Confluence: ", dynamic_confluence_required);
    Print("  Stop Loss: ", g_StopLossATR, " × ATR");
    Print("  Breakeven: ", g_BreakEvenActivationR, "R");
    Print("  Trailing: ", g_TrailingStopActivationR, "R");
    Print("════════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Get Higher Timeframe                                              |
//+------------------------------------------------------------------+
ENUM_TIMEFRAMES GetHigherTimeframe(ENUM_TIMEFRAMES current)
{
    switch(current)
    {
        case PERIOD_M1:  return PERIOD_M5;
        case PERIOD_M5:  return PERIOD_M15;
        case PERIOD_M15: return PERIOD_H1;
        case PERIOD_H1:  return PERIOD_H4;
        case PERIOD_H4:  return PERIOD_D1;
        case PERIOD_D1:  return PERIOD_W1;
        case PERIOD_W1:  return PERIOD_MN1;
        default:         return PERIOD_D1;
    }
}

//+------------------------------------------------------------------+
//| Chart Event Handler - FOR BUTTON CLICKS                          |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
    // Handle button clicks - OBJ_BUTTON generates CHARTEVENT_OBJECT_CLICK
    if(id == CHARTEVENT_OBJECT_CLICK)
    {
        // Check if clicked object is one of our buttons
        for(int i = 0; i < button_count; i++)
        {
            if(sparam == gui_buttons[i].name)
            {
                // Toggle button state
                gui_buttons[i].state = !gui_buttons[i].state;

                // Update the actual setting variable
                UpdateSetting(gui_buttons[i].setting, gui_buttons[i].state);

                // Update button visual immediately
                color bg_color = gui_buttons[i].state ? gui_buttons[i].color_on : gui_buttons[i].color_off;
                ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_BGCOLOR, bg_color);

                // Set text color: Black for green buttons (ON), White for grey/off buttons
                color text_color = (gui_buttons[i].state && gui_buttons[i].color_on == clrLime) ? clrBlack : clrWhite;
                ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_COLOR, text_color);

                string button_text = gui_buttons[i].text + (gui_buttons[i].state ? " [ON]" : " [OFF]");
                ObjectSetString(0, gui_buttons[i].name, OBJPROP_TEXT, button_text);

                // Reset button state (so it doesn't stay pressed)
                ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_STATE, false);

                // Log the change
                Print("✓ BUTTON TOGGLED: ", gui_buttons[i].setting, " = ",
                     (gui_buttons[i].state ? "ON" : "OFF"));

                // Add visual feedback comment
                AddComment("✓ " + gui_buttons[i].text + " switched " +
                          (gui_buttons[i].state ? "ON" : "OFF"),
                          gui_buttons[i].state ? clrLime : clrOrange,
                          PRIORITY_CRITICAL);

                // For visual toggle buttons, redraw chart elements immediately
                if(StringFind(gui_buttons[i].setting, "SHOW_") >= 0)
                {
                    DrawLiquidityZones();
                    DrawFVGZones();
                    DrawOrderBlocks();
                    if(has_active_pattern)
                    {
                        DrawPatternBox(active_pattern);
                        DrawPatternLabel(active_pattern);
                    }
                    DrawDashboard();
                    DrawBigCommentary();
                    DrawButtonStatus();
                    DrawColorLegend();
                }

                // Force chart redraw
                ChartRedraw();

                break;
            }
        }
    }
}

//+------------------------------------------------------------------+
//|                      END OF EA                                    |
//+------------------------------------------------------------------+