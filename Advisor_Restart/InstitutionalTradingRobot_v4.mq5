//+------------------------------------------------------------------+
//|                                InstitutionalTradingRobot_v4.mq5  |
//|                         Institutional-Grade Trading System v4.0   |
//|                      Aggression Levels + Python Integration       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.00"
#property description "Advanced Trading Robot - Aggression Levels 1-5 + Python ML Integration"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <AI_Bridge_NamedPipe.mqh>
#include "JSONExporter.mqh"

//+------------------------------------------------------------------+
//| POSITION SIZING MODE ENUM                                         |
//+------------------------------------------------------------------+
enum ENUM_POSITION_SIZING_MODE
{
   LOT_SIZE_RANGE,      // Fixed Lot Range (Min/Max Bounds)
   RISK_PERCENTAGE      // Dynamic Risk % (Account-Based)
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - INSTITUTIONAL CONFIGURATION                    |
//+------------------------------------------------------------------+
input group "═════════ CORE SETTINGS ═════════"
input bool     EnableTrading = false;                   // Enable Auto Trading (START FALSE!)
input bool     IndicatorMode = true;                    // Visual Analysis Mode
input ENUM_TIMEFRAMES PreferredTimeframe = PERIOD_H4;   // Trading Timeframe (H4 Default)
input int      MagicNumber = 123456;                    // Magic Number

input group "═════════ POSITION SIZING MODE ═════════"
input ENUM_POSITION_SIZING_MODE PositionSizingMode = LOT_SIZE_RANGE;  // Position Sizing Mode
input double   MinLotSize = 0.01;                       // [LOT_SIZE_RANGE] Minimum Lot Size
input double   MaxLotSize = 0.10;                       // [LOT_SIZE_RANGE] Maximum Lot Size

input group "═════════ NEW V4: AGGRESSION & ML INTEGRATION ═════════"
input int      AggressionLevel = 3;                     // Aggression Level (1=Conservative, 5=Maximum)
input bool     EnablePythonFileExport = true;           // Export Trade Data for Python ML
input string   PythonDataFolder = "MLData";             // Python Data Folder Name

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
input double   BaseRiskPercent = 0.5;                   // [RISK_PERCENTAGE] Base Risk Per Trade (%)
input int      MaxOpenTrades = 3;                       // Max Concurrent Trades
input double   DailyLossLimit = 2.0;                    // Daily Loss Limit (%)
input double   WeeklyLossLimit = 5.0;                   // Weekly Loss Limit (%)
input double   StopLossATR = 2.0;                       // Stop Loss (× ATR)

input group "═════════ TAKE PROFIT SETTINGS ═════════"
input double   TP1_RiskReward = 2.0;                    // Take Profit 1 (R:R)
input double   TP2_RiskReward = 3.0;                    // Take Profit 2 (R:R)
input double   TP3_RiskReward = 5.0;                    // Take Profit 3 (R:R)

input group "═════════ PROFIT PROTECTION ═════════"
input bool     UseProfitLock = true;                    // Enable Profit Lock
input double   ProfitLockTrigger = 1.5;                 // Lock Trigger (R multiple, e.g. 1.5R)
input double   ProfitLockPercent = 50.0;                // Lock % of Profit (e.g. 50%)
input bool     UsePartialClose = false;                 // Enable Partial Close at TP1
input double   PartialClosePercent = 50.0;              // % to Close at TP1

input group "═════════ VISUAL DASHBOARD ═════════"
input bool     ShowDashboard = true;                    // Show Dashboard
input bool     ShowCommentary = true;                   // Show Real-Time Commentary
input int      Dashboard_X = 20;                        // Dashboard X Position
input int      Dashboard_Y = 50;                        // Dashboard Y Position
input color    ColorBackground = C'20,20,30';           // Background Color
input color    ColorText = clrWhite;                    // Text Color
input int      FontSize = 9;                            // Font Size

//+------------------------------------------------------------------+
//| GLOBAL TRADING OBJECTS                                            |
//+------------------------------------------------------------------+
CTrade         trade;
CPositionInfo  position;
CAccountInfo   account;
CJSONExporter  jsonExporter;

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

// Visual toggles (GUI-controllable - turn chart colors on/off)
bool g_ShowPatternBoxes = true;
bool g_ShowPatternLabels = true;
bool g_ShowLiquidityZones = true;
bool g_ShowFVGZones = true;
bool g_ShowOrderBlocks = true;
bool g_ShowDashboard = true;
bool g_ShowCommentary = true;
bool g_ShowColorLegend = true;

// Alert Settings
input bool EnablePopupAlerts = false;        // Enable Pop-up Alerts
input bool EnableMobileNotifications = false; // Enable Mobile Push Notifications
input bool AlertOnCritical = true;           // Alert on CRITICAL priority messages
input bool AlertOnImportant = true;          // Alert on IMPORTANT priority messages
input bool AlertOnInfo = false;              // Alert on INFO priority messages

//+------------------------------------------------------------------+
//| V4 NEW: AGGRESSION LEVEL PARAMETERS                              |
//+------------------------------------------------------------------+
struct AggressionSettings
{
    int     confluence_required;        // How many factors needed
    double  risk_multiplier;            // Risk adjustment
    double  min_pattern_strength;       // Minimum pattern strength (1-5)
    bool    require_mtf;                // Require MTF confirmation
    bool    require_volume;             // Require volume confirmation
    int     max_trades;                 // Max concurrent trades
    double  tp_multiplier;              // TP multiplier
    string  description;                // Description
};

AggressionSettings aggression_presets[5];   // Levels 1-5

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
    int                 aggression_level;   // NEW V4
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
OrderBlock          order_blocks[50];
int                 ob_count = 0;
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
CommentaryLine      price_action_commentary[50];  // Detailed price action explanations (max 50)
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
double              hourly_start_balance;
datetime            last_daily_reset;
datetime            last_weekly_reset;
datetime            last_hourly_reset;
int                 consecutive_losses = 0;
int                 consecutive_wins = 0;
double              peak_balance = 0;

// Adaptive Parameters (FIX #18)
int                 dynamic_confluence_required = 3;
double              dynamic_risk_percent = 0.5;
double              dynamic_tp1 = 2.0;

// Object prefix
string              prefix = "IGTR4_";

// V4 NEW: Active aggression settings
AggressionSettings  active_aggression;

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
void AddPriceActionComment(string text, color text_color, int priority, datetime event_time = 0)
{
    if(!g_ShowCommentary) return;

    // Shift buffer if full (max 50 messages)
    if(pa_commentary_count >= 50)
    {
        for(int i = 0; i < 49; i++)
            price_action_commentary[i] = price_action_commentary[i+1];
        pa_commentary_count = 49;
    }

    price_action_commentary[pa_commentary_count].text = text;
    price_action_commentary[pa_commentary_count].text_color = text_color;
    // Use event_time if provided, otherwise use current time
    price_action_commentary[pa_commentary_count].timestamp = (event_time > 0) ? event_time : TimeCurrent();
    price_action_commentary[pa_commentary_count].priority = priority;
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
//| V4 NEW: INITIALIZE AGGRESSION PRESETS                            |
//+------------------------------------------------------------------+
void InitializeAggressionPresets()
{
    // LEVEL 1: ULTRA CONSERVATIVE (Maximum Safety)
    aggression_presets[0].confluence_required = 6;
    aggression_presets[0].risk_multiplier = 0.5;
    aggression_presets[0].min_pattern_strength = 4;
    aggression_presets[0].require_mtf = true;
    aggression_presets[0].require_volume = true;
    aggression_presets[0].max_trades = 1;
    aggression_presets[0].tp_multiplier = 1.5;
    aggression_presets[0].description = "ULTRA CONSERVATIVE - Only Perfect Setups";

    // LEVEL 2: CONSERVATIVE (High Quality)
    aggression_presets[1].confluence_required = 5;
    aggression_presets[1].risk_multiplier = 0.75;
    aggression_presets[1].min_pattern_strength = 3;
    aggression_presets[1].require_mtf = true;
    aggression_presets[1].require_volume = true;
    aggression_presets[1].max_trades = 2;
    aggression_presets[1].tp_multiplier = 1.8;
    aggression_presets[1].description = "CONSERVATIVE - High Quality Only";

    // LEVEL 3: BALANCED (Default - Best for Most Traders)
    aggression_presets[2].confluence_required = 4;
    aggression_presets[2].risk_multiplier = 1.0;
    aggression_presets[2].min_pattern_strength = 2;
    aggression_presets[2].require_mtf = true;
    aggression_presets[2].require_volume = false;
    aggression_presets[2].max_trades = 3;
    aggression_presets[2].tp_multiplier = 2.0;
    aggression_presets[2].description = "BALANCED - Quality & Quantity";

    // LEVEL 4: AGGRESSIVE (More Trades)
    aggression_presets[3].confluence_required = 3;
    aggression_presets[3].risk_multiplier = 1.25;
    aggression_presets[3].min_pattern_strength = 2;
    aggression_presets[3].require_mtf = false;
    aggression_presets[3].require_volume = false;
    aggression_presets[3].max_trades = 5;
    aggression_presets[3].tp_multiplier = 2.5;
    aggression_presets[3].description = "AGGRESSIVE - High Frequency";

    // LEVEL 5: MAXIMUM AGGRESSION (Scalping Mode)
    aggression_presets[4].confluence_required = 2;
    aggression_presets[4].risk_multiplier = 1.5;
    aggression_presets[4].min_pattern_strength = 1;
    aggression_presets[4].require_mtf = false;
    aggression_presets[4].require_volume = false;
    aggression_presets[4].max_trades = 8;
    aggression_presets[4].tp_multiplier = 3.0;
    aggression_presets[4].description = "MAXIMUM - All Valid Setups";

    Print("✓ Aggression presets initialized (Levels 1-5)");
}

//+------------------------------------------------------------------+
//| V4 NEW: APPLY AGGRESSION LEVEL                                   |
//+------------------------------------------------------------------+
void ApplyAggressionLevel()
{
    int level = MathMax(1, MathMin(5, AggressionLevel));  // Clamp 1-5
    active_aggression = aggression_presets[level - 1];

    // Apply to dynamic parameters
    dynamic_confluence_required = active_aggression.confluence_required;
    dynamic_risk_percent = BaseRiskPercent * active_aggression.risk_multiplier;
    dynamic_tp1 = TP1_RiskReward * active_aggression.tp_multiplier / 2.0;

    Print("═══════════════════════════════════════════════════");
    Print("  AGGRESSION LEVEL ", level, ": ", active_aggression.description);
    Print("  Confluence Required: ", active_aggression.confluence_required);
    Print("  Risk Multiplier: ", active_aggression.risk_multiplier);
    Print("  Min Pattern Strength: ", active_aggression.min_pattern_strength);
    Print("  Max Trades: ", active_aggression.max_trades);
    Print("═══════════════════════════════════════════════════");

    AddComment("═══ AGGRESSION LEVEL " + IntegerToString(level) + " ═══", clrYellow, PRIORITY_CRITICAL);
    AddComment(active_aggression.description, clrAqua, PRIORITY_IMPORTANT);
    AddComment("Confluence: " + IntegerToString(active_aggression.confluence_required) +
              " | Risk: " + DoubleToString(dynamic_risk_percent, 2) + "%", clrWhite, PRIORITY_IMPORTANT);
}

//+------------------------------------------------------------------+
//| INCLUDE SUPPORTING MODULES                                        |
//+------------------------------------------------------------------+
#include "InstitutionalTradingRobot_v4_Functions.mqh"
#include "InstitutionalTradingRobot_v4_Trading.mqh"
#include "InstitutionalTradingRobot_v4_Visual.mqh"
#include "InstitutionalTradingRobot_v4_GUI.mqh"

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("╔═══════════════════════════════════════════════════════════╗");
    Print("║  INSTITUTIONAL TRADING ROBOT v4.0                        ║");
    Print("║  Aggression Levels + Python ML Integration              ║");
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

    // V4 NEW: Initialize aggression system
    InitializeAggressionPresets();
    ApplyAggressionLevel();

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
    dashboard.aggression_level = AggressionLevel;

    // Initial commentary
    AddComment("═══ SYSTEM INITIALIZED ═══", clrLime, PRIORITY_CRITICAL);
    AddComment("Timeframe: " + EnumToString(PreferredTimeframe), clrYellow, PRIORITY_IMPORTANT);
    AddComment("Python Export: " + (EnablePythonFileExport ? "ENABLED" : "DISABLED"),
              EnablePythonFileExport ? clrLime : clrGray, PRIORITY_IMPORTANT);

    if(!g_EnableTrading)
    {
        AddComment("⚠ INDICATOR MODE - No Trading", clrOrange, PRIORITY_CRITICAL);
        AddComment("ADVICE: Enable trading only after thorough testing", clrYellow, PRIORITY_IMPORTANT);
    }
    else
    {
        AddComment("✓ AUTO-TRADING ENABLED", clrLime, PRIORITY_CRITICAL);
        AddComment("ADVICE: Monitor closely during first sessions", clrOrange, PRIORITY_IMPORTANT);
    }

    // Timeframe warning
    if(_Period != PreferredTimeframe)
    {
        AddComment("⚠ Chart timeframe mismatch!", clrRed, PRIORITY_CRITICAL);
        AddComment("ADVICE: Switch to " + EnumToString(PreferredTimeframe) + " for optimal results", clrYellow, PRIORITY_IMPORTANT);
    }

    Print("✓ All systems operational");

    // Create interactive GUI with clickable buttons
    CreateInteractiveDashboard();

    // Initialize button status display
    DrawButtonStatus();

    Print("✓ Interactive GUI created - Click buttons to toggle settings!");

    // Initialize JSON Exporter for Python GUI sync
    if(!jsonExporter.Init("AppleTrader\\market_data.json"))
    {
        Print("WARNING: JSON Exporter initialization failed - Python sync disabled");
    }
    else
    {
        Print("✓ JSON Exporter initialized - saving to Common/Files/AppleTrader/market_data.json");
    }

    // Set timer for JSON export (every 1 second)
    EventSetTimer(1);
    Print("✓ Timer set for 1-second JSON export to Python GUI");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Kill timer
    EventKillTimer();

    // Release indicators
    if(h_EMA_200 != INVALID_HANDLE) IndicatorRelease(h_EMA_200);
    if(h_EMA_Higher != INVALID_HANDLE) IndicatorRelease(h_EMA_Higher);
    if(h_ATR != INVALID_HANDLE) IndicatorRelease(h_ATR);
    if(h_ATR_Higher != INVALID_HANDLE) IndicatorRelease(h_ATR_Higher);
    if(h_Volume_MA != INVALID_HANDLE) IndicatorRelease(h_Volume_MA);

    // Save pattern performance
    SavePatternPerformance();

    // Clean up chart objects
    ObjectsDeleteAll(0, prefix);

    Print("═══════════════════════════════════════════════════");
    Print("  Institutional Trading Robot v4.0 Stopped");
    Print("═══════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Timer function - Export data to Python GUI                        |
//+------------------------------------------------------------------+
void OnTimer()
{
    ExportMarketDataToJSON();
}

//+------------------------------------------------------------------+
//| Export Market Data to JSON for Python GUI                         |
//+------------------------------------------------------------------+
void ExportMarketDataToJSON()
{
    jsonExporter.BeginExport();

    // Basic market info
    jsonExporter.AddString("symbol", Symbol());
    jsonExporter.AddString("timeframe", EnumToString(Period()));
    jsonExporter.AddLong("timestamp", TimeCurrent());
    jsonExporter.AddDouble("bid", SymbolInfoDouble(Symbol(), SYMBOL_BID), 5);
    jsonExporter.AddDouble("ask", SymbolInfoDouble(Symbol(), SYMBOL_ASK), 5);

    double spread = (SymbolInfoDouble(Symbol(), SYMBOL_ASK) - SymbolInfoDouble(Symbol(), SYMBOL_BID)) / _Point;
    jsonExporter.AddDouble("spread", spread, 2);

    // Account info - CRITICAL FOR PYTHON BALANCE SYNC
    jsonExporter.AddDouble("account_balance", AccountInfoDouble(ACCOUNT_BALANCE), 2);
    jsonExporter.AddDouble("account_equity", AccountInfoDouble(ACCOUNT_EQUITY), 2);
    jsonExporter.AddDouble("account_margin", AccountInfoDouble(ACCOUNT_MARGIN), 2);
    jsonExporter.AddDouble("account_free_margin", AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2);

    // Trading status
    jsonExporter.AddBool("auto_trading", g_EnableTrading);
    jsonExporter.AddInt("positions_total", PositionsTotal());
    jsonExporter.AddInt("orders_total", OrdersTotal());

    // Calculate total P&L
    double total_pnl = 0.0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            total_pnl += PositionGetDouble(POSITION_PROFIT);
        }
    }
    jsonExporter.AddDouble("total_pnl", total_pnl, 2);

    // V4 specific: Aggression level
    jsonExporter.AddInt("aggression_level", AggressionLevel);

    // Position sizing mode
    jsonExporter.AddString("position_sizing_mode", PositionSizingMode == LOT_SIZE_RANGE ? "LOT_SIZE_RANGE" : "RISK_PERCENTAGE");

    jsonExporter.EndExport();
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // ═══════════════════════════════════════════════════════════════
    // DAILY & HOURLY P&L RESET CHECK
    // ═══════════════════════════════════════════════════════════════
    MqlDateTime current_time, last_daily, last_hourly;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(last_daily_reset, last_daily);
    TimeToStruct(last_hourly_reset, last_hourly);

    // Reset daily P&L at midnight
    if(current_time.day != last_daily.day)
    {
        Print("═══ NEW DAY: Resetting Daily P&L ═══");
        Print("Yesterday's P&L: ", DoubleToString(account.Balance() - daily_start_balance, 2));
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
    }

    // Reset hourly P&L at each hour
    if(current_time.hour != last_hourly.hour)
    {
        double hourly_pnl = account.Balance() - hourly_start_balance;
        if(MathAbs(hourly_pnl) > 0.01)
        {
            Print("═══ HOURLY P&L UPDATE ═══");
            Print("Hour ", last_hourly.hour, ":00 P&L: ", DoubleToString(hourly_pnl, 2), " ", AccountInfoString(ACCOUNT_CURRENCY));
        }
        hourly_start_balance = account.Balance();
        last_hourly_reset = TimeCurrent();
    }

    // Check for new bar on preferred timeframe
    static datetime last_bar_time = 0;
    datetime current_bar_time = iTime(_Symbol, PreferredTimeframe, 0);

    if(current_bar_time == last_bar_time)
        return;

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
                dynamic_risk_percent = BaseRiskPercent * active_aggression.risk_multiplier * 0.5;
                dynamic_confluence_required = active_aggression.confluence_required + 1;
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
        // V4 NEW: Check pattern strength against aggression level
        if(active_pattern.strength < active_aggression.min_pattern_strength)
        {
            AddComment("⚠ Pattern strength too low for Level " + IntegerToString(AggressionLevel),
                      clrOrange, PRIORITY_IMPORTANT);
            AddComment("ADVICE: Need " + IntegerToString(active_aggression.min_pattern_strength) +
                      "★ minimum (current: " + IntegerToString(active_pattern.strength) + "★)",
                      clrYellow, PRIORITY_INFO);
            has_active_pattern = false;
        }
        else
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
                // V4: Volume requirement depends on aggression level
                if(active_aggression.require_volume)
                {
                    AddComment("⛔ Volume: Below threshold (REQUIRED for Level " + IntegerToString(AggressionLevel) + ")",
                              clrRed, PRIORITY_CRITICAL);
                    has_active_pattern = false;
                }
                else
                {
                    AddComment("⚠ Volume: Below threshold - Weak conviction", clrOrange, PRIORITY_IMPORTANT);
                }
                dashboard.volume_ok = false;
            }
        }

        // FIX #5: Multi-Timeframe Confirmation
        if(g_UseMTFConfirmation)
        {
            bool mtf_aligned = CheckMultiTimeframeAlignment();

            if(mtf_aligned)
            {
                AddComment("✓ MTF: Higher timeframe confirms direction", clrLime, PRIORITY_INFO);
                dashboard.mtf_ok = true;
            }
            else
            {
                // V4: MTF requirement depends on aggression level
                if(active_aggression.require_mtf)
                {
                    AddComment("⛔ MTF: Higher timeframe CONFLICTS (REQUIRED for Level " + IntegerToString(AggressionLevel) + ")",
                              clrRed, PRIORITY_CRITICAL);
                    has_active_pattern = false;
                }
                else
                {
                    AddComment("⚠ MTF: Higher timeframe CONFLICTS", clrOrange, PRIORITY_IMPORTANT);
                    AddComment("ADVICE: Counter-trend trades have lower win rate", clrYellow, PRIORITY_INFO);
                }
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

        if(decision.decision == DECISION_ENTER && g_EnableTrading && !IndicatorMode)
        {
            AddComment("─── Phase 5: Trade Execution ───", clrAqua, PRIORITY_IMPORTANT);

            // V4: Check max trades from aggression level
            if(PositionsTotal() >= active_aggression.max_trades)
            {
                AddComment("⛔ MAX POSITIONS REACHED FOR LEVEL " + IntegerToString(AggressionLevel),
                          clrRed, PRIORITY_CRITICAL);
                AddComment("ADVICE: Limit " + IntegerToString(active_aggression.max_trades) +
                          " trades at aggression level " + IntegerToString(AggressionLevel),
                          clrOrange, PRIORITY_IMPORTANT);
            }
            else if(!CheckRiskLimits())
            {
                AddComment("⛔ RISK LIMIT REACHED - Cannot trade", clrRed, PRIORITY_CRITICAL);
                AddComment("ADVICE: Daily/weekly loss limit hit - Stop trading now", clrOrange, PRIORITY_CRITICAL);
            }
            else
            {
                // FIX #10: Dynamic Risk Calculation
                double risk_percent = UseDynamicRisk ? CalculateDynamicRisk() : dynamic_risk_percent;
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
    // PHASE 8: PRICE ACTION COMMENTARY (Educational Deep Analysis)
    //═══════════════════════════════════════════════════════════════

    // Perform comprehensive price action analysis with detailed commentary
    PerformPriceActionAnalysis();

    // Update & Draw Dashboard
    UpdateDashboard();
    DrawDashboard();  // Function checks g_ShowDashboard internally

    // Draw BIG READABLE Commentary
    DrawBigCommentary();  // Function checks g_ShowCommentary internally

    // Draw Button Status (always show)
    DrawButtonStatus();

    // Draw Color Legend
    DrawColorLegend();  // Function checks g_ShowColorLegend internally

    // Draw PRICE ACTION COMMENTARY (Educational)
    DrawPriceActionCommentary();  // Function checks g_ShowCommentary internally
}

//+------------------------------------------------------------------+
//| Initialize All Indicators                                         |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
    // Current timeframe indicators
    h_EMA_200 = iMA(_Symbol, PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE);
    h_ATR = iATR(_Symbol, PreferredTimeframe, 14);
    h_Volume_MA = iMA(_Symbol, PreferredTimeframe, 20, 0, MODE_SMA, VOLUME_TICK);

    // Higher timeframe indicators for MTF confirmation
    ENUM_TIMEFRAMES higher_tf = GetHigherTimeframe(PreferredTimeframe);
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
    hourly_start_balance = account.Balance();
    peak_balance = account.Balance();
    last_daily_reset = TimeCurrent();
    last_weekly_reset = TimeCurrent();
    last_hourly_reset = TimeCurrent();

    AddComment("Risk: " + DoubleToString(dynamic_risk_percent, 2) + "% per trade, Max " +
              IntegerToString(active_aggression.max_trades) + " positions", clrAqua, PRIORITY_INFO);
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
//| CLOSE TRADES ON CURRENT SYMBOL                                   |
//+------------------------------------------------------------------+
void CloseSymbolTrades()
{
    int closed = 0;
    int failed = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket > 0)
        {
            if(PositionGetString(POSITION_SYMBOL) == _Symbol)
            {
                if(trade.PositionClose(ticket))
                {
                    closed++;
                    Print("✓ Closed position #", ticket, " on ", _Symbol);
                }
                else
                {
                    failed++;
                    Print("✗ Failed to close position #", ticket, " Error: ", GetLastError());
                }
            }
        }
    }

    if(closed > 0 || failed > 0)
    {
        AddComment("Closed " + IntegerToString(closed) + " " + _Symbol + " trades" +
                  (failed > 0 ? " (" + IntegerToString(failed) + " failed)" : ""),
                  failed > 0 ? clrOrange : clrLime, PRIORITY_CRITICAL);
    }
    else
    {
        AddComment("No " + _Symbol + " trades to close", clrYellow, PRIORITY_IMPORTANT);
    }
}

//+------------------------------------------------------------------+
//| CLOSE ALL TRADES ON ALL SYMBOLS                                  |
//+------------------------------------------------------------------+
void CloseAllTrades()
{
    int closed = 0;
    int failed = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket > 0)
        {
            string symbol = PositionGetString(POSITION_SYMBOL);
            if(trade.PositionClose(ticket))
            {
                closed++;
                Print("✓ Closed position #", ticket, " on ", symbol);
            }
            else
            {
                failed++;
                Print("✗ Failed to close position #", ticket, " Error: ", GetLastError());
            }
        }
    }

    if(closed > 0 || failed > 0)
    {
        AddComment("Closed ALL " + IntegerToString(closed) + " trades" +
                  (failed > 0 ? " (" + IntegerToString(failed) + " failed)" : ""),
                  failed > 0 ? clrOrange : clrLime, PRIORITY_CRITICAL);
    }
    else
    {
        AddComment("No trades to close", clrYellow, PRIORITY_IMPORTANT);
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
        // ═══════════════════════════════════════════════════════════════
        // ACTION BUTTONS (Close trades) - Handle these first
        // ═══════════════════════════════════════════════════════════════
        if(sparam == prefix + "BTN_CLOSE_SYMBOL")
        {
            Print("═══ CLOSE SYMBOL BUTTON CLICKED ═══");
            CloseSymbolTrades();
            // Reset button state
            ObjectSetInteger(0, sparam, OBJPROP_STATE, false);
            ChartRedraw();
            return;
        }

        if(sparam == prefix + "BTN_CLOSE_ALL")
        {
            Print("═══ CLOSE ALL BUTTON CLICKED ═══");
            CloseAllTrades();
            // Reset button state
            ObjectSetInteger(0, sparam, OBJPROP_STATE, false);
            ChartRedraw();
            return;
        }

        // ═══════════════════════════════════════════════════════════════
        // TOGGLE BUTTONS - Check if clicked object is one of our buttons
        // ═══════════════════════════════════════════════════════════════
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
