//+------------------------------------------------------------------+
//|                        InstitutionalTradingRobot_v4_MQL4.mq4     |
//|                    PROPERLY CALIBRATED AGGRESSION LEVELS         |
//|                         MQL4 - Strategy Tester Ready             |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.50"
#property description "MQL4 Robot - Professional Control Panel - Pattern-Driven Trading"
#property strict

//+------------------------------------------------------------------+
//| DROPDOWN ENUMS                                                    |
//+------------------------------------------------------------------+
enum ENUM_AGGRESSION
{
   AGG_1 = 1,  // Level 1 - Only 5-Star Patterns
   AGG_2 = 2,  // Level 2 - 4-5 Star Patterns
   AGG_3 = 3,  // Level 3 - 3-5 Star Patterns
   AGG_4 = 4,  // Level 4 - 2-5 Star Patterns
   AGG_5 = 5   // Level 5 - 2-5 Star + Relaxed Filters
};

enum ENUM_SIZING
{
   SIZE_FIXED,    // Fixed Lot
   SIZE_RISK      // Risk % of Account
};

enum ENUM_SL_MODE
{
   SL_MODE_ATR,    // ATR-Based
   SL_MODE_PIPS    // Fixed Pips
};

enum ENUM_LOT
{
   LOT_001 = 1,     // 0.01
   LOT_002 = 2,     // 0.02
   LOT_005 = 5,     // 0.05
   LOT_010 = 10,    // 0.10
   LOT_020 = 20,    // 0.20
   LOT_050 = 50,    // 0.50
   LOT_100 = 100,   // 1.00
   LOT_200 = 200,   // 2.00
   LOT_500 = 500    // 5.00
};

enum ENUM_RISK
{
   RISK_025 = 25,   // 0.25%
   RISK_050 = 50,   // 0.50%
   RISK_075 = 75,   // 0.75%
   RISK_100 = 100,  // 1.00%
   RISK_150 = 150,  // 1.50%
   RISK_200 = 200,  // 2.00%
   RISK_300 = 300,  // 3.00%
   RISK_500 = 500   // 5.00%
};

enum ENUM_ATR
{
   ATR_05 = 5,   // 0.5x ATR
   ATR_10 = 10,  // 1.0x ATR
   ATR_15 = 15,  // 1.5x ATR
   ATR_20 = 20,  // 2.0x ATR
   ATR_25 = 25,  // 2.5x ATR
   ATR_30 = 30,  // 3.0x ATR
   ATR_40 = 40,  // 4.0x ATR
   ATR_50 = 50   // 5.0x ATR
};

enum ENUM_SL_PIPS
{
   SLP_10 = 10,    // 10 pips
   SLP_15 = 15,    // 15 pips
   SLP_20 = 20,    // 20 pips
   SLP_25 = 25,    // 25 pips
   SLP_30 = 30,    // 30 pips
   SLP_40 = 40,    // 40 pips
   SLP_50 = 50,    // 50 pips
   SLP_75 = 75,    // 75 pips
   SLP_100 = 100,  // 100 pips
   SLP_150 = 150,  // 150 pips
   SLP_200 = 200   // 200 pips
};

enum ENUM_RR
{
   RR_10 = 10,  // 1.0 R:R
   RR_15 = 15,  // 1.5 R:R
   RR_20 = 20,  // 2.0 R:R
   RR_25 = 25,  // 2.5 R:R
   RR_30 = 30,  // 3.0 R:R
   RR_40 = 40,  // 4.0 R:R
   RR_50 = 50   // 5.0 R:R
};

enum ENUM_MAX_TRADES
{
   MT_1 = 1,    // 1
   MT_2 = 2,    // 2
   MT_3 = 3,    // 3
   MT_5 = 5,    // 5
   MT_10 = 10,  // 10
   MT_20 = 20,  // 20
   MT_50 = 50,  // 50
   MT_100 = 100 // Unlimited
};

enum ENUM_LOSS_LIM
{
   LL_1 = 10,   // 1%
   LL_2 = 20,   // 2%
   LL_3 = 30,   // 3%
   LL_5 = 50,   // 5%
   LL_10 = 100, // 10%
   LL_NONE = 1000 // No Limit
};

enum ENUM_VOL
{
   VOL_05 = 5,   // 0.5x Avg
   VOL_08 = 8,   // 0.8x Avg
   VOL_10 = 10,  // 1.0x Avg
   VOL_12 = 12,  // 1.2x Avg
   VOL_15 = 15,  // 1.5x Avg
   VOL_20 = 20   // 2.0x Avg
};

enum ENUM_SPREAD
{
   SPD_20 = 20,   // 20% ATR
   SPD_30 = 30,   // 30% ATR
   SPD_50 = 50,   // 50% ATR
   SPD_100 = 100, // 100% ATR
   SPD_NONE = 1000 // No Limit
};

enum ENUM_CORR
{
   CORR_05 = 5,  // 0.5
   CORR_07 = 7,  // 0.7
   CORR_09 = 9   // 0.9
};

enum ENUM_LOCK_R
{
   LR_10 = 10,  // 1.0R
   LR_15 = 15,  // 1.5R
   LR_20 = 20,  // 2.0R
   LR_25 = 25   // 2.5R
};

enum ENUM_PROFIT
{
   PR_50 = 50,      // $50
   PR_100 = 100,    // $100
   PR_200 = 200,    // $200
   PR_500 = 500,    // $500
   PR_1000 = 1000,  // $1000
   PR_2000 = 2000,  // $2000
   PR_5000 = 5000   // $5000
};

enum ENUM_PCT
{
   PC_25 = 25,  // 25%
   PC_33 = 33,  // 33%
   PC_50 = 50,  // 50%
   PC_75 = 75   // 75%
};

enum ENUM_ACCT_PCT
{
   AP_2 = 20,   // 2%
   AP_3 = 30,   // 3%
   AP_5 = 50,   // 5%
   AP_10 = 100  // 10%
};

enum ENUM_BARS
{
   BR_1 = 1,   // 1 Bar
   BR_2 = 2,   // 2 Bars
   BR_3 = 3,   // 3 Bars
   BR_5 = 5,   // 5 Bars
   BR_10 = 10  // 10 Bars
};

enum ENUM_GMT
{
   GMT_N5 = -5,  // GMT-5
   GMT_N4 = -4,  // GMT-4
   GMT_0 = 0,    // GMT+0
   GMT_P1 = 1,   // GMT+1
   GMT_P2 = 2,   // GMT+2
   GMT_P3 = 3,   // GMT+3
   GMT_P8 = 8,   // GMT+8
   GMT_P9 = 9    // GMT+9
};

//+------------------------------------------------------------------+
//| INPUTS - ALL DROPDOWNS                                            |
//+------------------------------------------------------------------+
input string           _1 = "═══════ CORE ═══════";
input bool             EnableTrading = true;                    // Enable Trading
input ENUM_TIMEFRAMES  Timeframe = PERIOD_H4;                   // Timeframe
input ENUM_AGGRESSION  AggressionLevel = AGG_3;                 // Aggression Level
input int              MagicNumber = 123456;                    // Magic Number

input string           _2 = "═══════ LOT SIZE ═══════";
input ENUM_SIZING      SizingMode = SIZE_FIXED;                 // Sizing Method
input ENUM_LOT         MinLot = LOT_010;                        // Min Lot
input ENUM_LOT         MaxLot = LOT_100;                        // Max Lot

input string           _3 = "═══════ STOP LOSS ═══════";
input ENUM_SL_MODE     SL_Mode = SL_MODE_ATR;                   // Stop Loss Mode
input ENUM_ATR         SL_ATR_Mult = ATR_20;                    // SL ATR Multiplier
input ENUM_SL_PIPS     SL_Fixed_Pips = SLP_50;                  // SL Fixed Pips

input string           _4 = "═══════ RISK ═══════";
input ENUM_RISK        RiskPercent = RISK_100;                  // Risk %
input ENUM_MAX_TRADES  MaxTrades = MT_100;                      // Max Trades (100=Unlimited)
input ENUM_MAX_TRADES  MaxPerSymbol = MT_10;                    // Max Per Symbol
input ENUM_LOSS_LIM    DailyLoss = LL_5;                        // Daily Loss Limit
input ENUM_LOSS_LIM    WeeklyLoss = LL_10;                      // Weekly Loss Limit

input string           _5 = "═══════ TARGETS ═══════";
input ENUM_RR          TP_RR = RR_20;                           // Take Profit R:R

input string           _6 = "═══════ FILTERS ═══════";
input bool             UseVolumeFilter = true;                  // Volume Filter
input ENUM_VOL         VolumeThreshold = VOL_12;                // Volume Threshold
input bool             UseSpreadFilter = true;                  // Spread Filter
input ENUM_SPREAD      SpreadLimit = SPD_50;                    // Spread Limit
input bool             UseMTF = true;                           // MTF Confirmation
input bool             UseCorrelation = false;                  // Correlation Filter
input ENUM_CORR        CorrLimit = CORR_07;                     // Correlation Limit

input string           _7 = "═══════ SESSION ═══════";
input bool             UseSessionFilter = true;                 // Session Filter
input ENUM_GMT         BrokerGMT = GMT_P2;                      // Broker GMT Offset
input bool             TradeAsian = true;                       // Trade Asian
input bool             TradeLondon = true;                      // Trade London
input bool             TradeNY = true;                          // Trade NY

input string           _8 = "═══════ TRADE LOGIC ═══════";
input bool             RequireTrendAlignment = true;            // Require Trend Alignment
input bool             AllowCounterTrend = false;               // Allow Counter-Trend
input bool             UsePatternDecay = true;                  // Pattern Decay
input ENUM_BARS        PatternExpiry = BR_5;                    // Pattern Expiry Bars

input string           _9 = "═══════ TRADE MANAGEMENT ═══════";
input bool             UseBreakeven = true;                     // Move to Breakeven
input bool             UseTrailingStop = true;                  // Trailing Stop
input bool             UsePartialClose = false;                 // Partial Close at TP1
input ENUM_PCT         PartialPct = PC_50;                      // Partial Close %

input string           _10 = "═══════ DISPLAY ═══════";
input bool             ShowChartInfo = false;                   // Show Info on Chart
input bool             ShowPatternArrows = true;                // Show Pattern Arrows

input string           _11 = "═══════ ALERTS ═══════";
input bool             AlertOnTrade = false;                    // Alert on Trade
input bool             AlertOnPattern = false;                  // Alert on Pattern

input string           _12 = "═══════ AVAILABILITY ═══════";
input bool             EnableAvailabilityCheck = true;          // Enable Availability Checks
input bool             ShowAvailabilityPanel = true;            // Show Status Panel on Chart
input bool             AlertOnUnavailable = true;               // Alert When Unavailable
input int              AvailCheckInterval = 30;                 // Check Interval (seconds)
input int              MaxRetryAttempts = 3;                    // Max Retry on Failure
input int              RetryDelaySeconds = 5;                   // Retry Delay (seconds)
input double           MinMarginLevel = 200.0;                  // Min Margin Level %
input int              MaxDataAgeSeconds = 60;                  // Max Price Data Age (sec)
input bool             RequireAllChecksPass = false;            // Require ALL Checks Pass

input string           _13 = "═══════ CONTROL PANEL ═══════";
input bool             ShowControlPanel = true;                  // Show Control Panel
input int              ControlPanelX = 250;                      // Panel X Position
input int              ControlPanelY = 50;                       // Panel Y Position
input double           ScaleInMultiplier = 0.5;                  // Scale-In Lot Multiplier
input int              TP_Adjust_Pips = 10;                      // TP Adjust Amount (pips)
input int              SL_Adjust_Pips = 10;                      // SL Adjust Amount (pips)

//+------------------------------------------------------------------+
//| AVAILABILITY CHECK ENUMS                                          |
//+------------------------------------------------------------------+
enum ENUM_AVAILABILITY_STATUS
{
   AVAIL_OK = 0,              // All systems operational
   AVAIL_WARNING = 1,         // Minor issues - trading possible with caution
   AVAIL_ERROR = 2,           // Trading not recommended
   AVAIL_CRITICAL = 3         // Trading impossible
};

enum ENUM_CHECK_TYPE
{
   CHK_BROKER_CONNECTION,     // Broker/server connectivity
   CHK_SYMBOL_VALID,          // Symbol exists and valid
   CHK_SYMBOL_TRADEABLE,      // Symbol can be traded
   CHK_MARKET_OPEN,           // Market is open for trading
   CHK_TRADING_ALLOWED,       // Account allows trading
   CHK_EA_TRADING,            // EA trading enabled
   CHK_ACCOUNT_VALID,         // Account is valid and active
   CHK_MARGIN_SUFFICIENT,     // Enough margin for minimum trade
   CHK_SPREAD_ACCEPTABLE,     // Spread within limits
   CHK_DATA_AVAILABLE,        // Price data is current
   CHK_TOTAL                  // Total number of checks
};

//+------------------------------------------------------------------+
//| INTERNAL TYPES                                                    |
//+------------------------------------------------------------------+
enum REGIME { TREND_UP, TREND_DOWN, RANGE, TRANSITION };
enum SESSION { ASIAN, LONDON, OVERLAP, NEWYORK, CLOSED };

struct Pattern
{
   string   name;
   bool     is_bull;
   int      strength;     // 1-5 stars
   double   entry_price;
   double   sl_price;
   datetime time;
   int      bar_index;
};

// Availability check result for individual checks
struct AvailabilityCheck
{
   ENUM_CHECK_TYPE           check_type;
   ENUM_AVAILABILITY_STATUS  status;
   string                    message;
   datetime                  last_check;
   int                       retry_count;
};

// Overall availability report
struct AvailabilityReport
{
   ENUM_AVAILABILITY_STATUS  overall_status;
   int                       checks_passed;
   int                       checks_warning;
   int                       checks_failed;
   int                       checks_critical;
   string                    summary;
   datetime                  report_time;
   bool                      can_trade;
};

//+------------------------------------------------------------------+
//| GLOBALS                                                           |
//+------------------------------------------------------------------+
double g_risk, g_min_lot, g_max_lot, g_sl_atr, g_sl_pips, g_tp_rr;
double g_vol_thresh, g_spread_lim, g_corr_lim;
double g_daily_lim, g_weekly_lim;
int    g_max_trades, g_max_per_sym, g_pattern_expiry;

// Aggression settings
int    g_min_pattern_strength;  // Minimum pattern stars required
int    g_min_confluence;        // Minimum confluence score required
bool   g_require_mtf;           // MTF alignment mandatory?
bool   g_require_volume;        // Volume confirmation mandatory?
bool   g_allow_counter_trend;   // Allow counter-trend trades?

// Market state
REGIME  g_regime = RANGE;
SESSION g_session = ASIAN;
Pattern g_pattern;
bool    g_has_pattern = false;

// Tracking
double g_daily_start, g_weekly_start;

// Filter states
bool g_mtf_aligned = false;
bool g_volume_ok = false;
bool g_spread_ok = true;
bool g_session_ok = true;
bool g_trend_aligned = false;

// Availability checking system
AvailabilityCheck g_checks[10];       // Array of individual checks (CHK_TOTAL = 10)
AvailabilityReport g_avail_report;    // Current availability report
datetime g_last_avail_check = 0;      // Last availability check time
bool g_availability_ok = false;        // Quick flag: can we trade?
int g_consecutive_failures = 0;        // Track consecutive check failures
string g_avail_status_text = "";       // Status text for display
color g_avail_status_color = clrGray;  // Status color for display

// Control Panel state
bool g_trading_paused = false;         // Trading paused by user
bool g_trailing_enabled = true;        // Trailing stop toggle (inherits from UseTrailingStop)
bool g_control_panel_visible = true;   // Control panel visibility
double g_day_start_equity = 0;         // Equity at start of day for P&L calculation
double g_peak_equity = 0;              // Peak equity for drawdown calculation
datetime g_last_day = 0;               // Track day changes

//+------------------------------------------------------------------+
//| INIT                                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("===============================================================");
   Print("  INSTITUTIONAL TRADING ROBOT v4.50 MQL4");
   Print("  PROFESSIONAL CONTROL PANEL + AVAILABILITY SYSTEM");
   Print("===============================================================");

   // Convert inputs
   g_risk = (double)RiskPercent / 100.0;
   g_min_lot = (double)MinLot / 100.0;
   g_max_lot = (double)MaxLot / 100.0;
   g_sl_atr = (double)SL_ATR_Mult / 10.0;
   g_sl_pips = (double)SL_Fixed_Pips;
   g_tp_rr = (double)TP_RR / 10.0;
   g_vol_thresh = (double)VolumeThreshold / 10.0;
   g_spread_lim = (double)SpreadLimit / 100.0;
   g_corr_lim = (double)CorrLimit / 10.0;
   g_daily_lim = (double)DailyLoss / 10.0;
   g_weekly_lim = (double)WeeklyLoss / 10.0;
   g_max_trades = (int)MaxTrades;
   g_max_per_sym = (int)MaxPerSymbol;
   g_pattern_expiry = (int)PatternExpiry;

   // Apply aggression calibration
   ApplyAggressionLevel();

   // Init tracking
   g_daily_start = AccountBalance();
   g_weekly_start = AccountBalance();

   // Print configuration
   Print("===============================================================");
   Print("  AGGRESSION LEVEL: ", AggressionLevel);
   Print("  → Min Pattern Strength: ", g_min_pattern_strength, " stars");
   Print("  → Min Confluence: ", g_min_confluence, " factors");
   Print("  → MTF Required: ", g_require_mtf ? "YES" : "NO");
   Print("  → Volume Required: ", g_require_volume ? "YES" : "NO");
   Print("  → Counter-Trend: ", g_allow_counter_trend ? "ALLOWED" : "BLOCKED");
   Print("===============================================================");
   Print("  Stop Loss: ", SL_Mode == SL_MODE_ATR ? DoubleToString(g_sl_atr, 1) + "x ATR" : DoubleToString(g_sl_pips, 0) + " pips");
   Print("  Take Profit: ", DoubleToString(g_tp_rr, 1), " R:R");
   Print("  Risk: ", DoubleToString(g_risk * 100, 2), "%");
   Print("===============================================================");

   if(!EnableTrading)
      Print("*** WARNING: TRADING DISABLED ***");
   else
      Print("*** TRADING ENABLED ***");

   // Initialize availability checking system
   InitAvailabilitySystem();

   // Initialize control panel state
   g_trailing_enabled = UseTrailingStop;
   g_day_start_equity = AccountEquity();
   g_peak_equity = AccountEquity();
   g_last_day = TimeCurrent() / 86400;
   g_control_panel_visible = ShowControlPanel;

   // Perform initial availability check
   if(EnableAvailabilityCheck)
   {
      Print("===============================================================");
      Print("  PERFORMING INITIAL AVAILABILITY CHECK...");
      PerformAvailabilityCheck();
      PrintAvailabilityReport();

      if(ShowAvailabilityPanel)
         CreateAvailabilityPanel();
   }

   // Create control panel
   if(ShowControlPanel)
      CreateControlPanel();

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "IGTR_");
   ObjectsDeleteAll(0, "AVAIL_");  // Clean up availability panel
   ObjectsDeleteAll(0, "CTRL_");   // Clean up control panel
}

//+------------------------------------------------------------------+
//| AGGRESSION LEVEL CALIBRATION                                      |
//| Pattern strength is the PRIMARY differentiator                    |
//+------------------------------------------------------------------+
void ApplyAggressionLevel()
{
   switch((int)AggressionLevel)
   {
      case 1:  // Level 1: Only trade on PREMIUM patterns
         g_min_pattern_strength = 5;    // Only 5-star patterns
         g_min_confluence = 5;          // Need 5 factors aligned
         g_require_mtf = true;          // MTF must align
         g_require_volume = true;       // Volume must confirm
         g_allow_counter_trend = false; // No counter-trend
         break;

      case 2:  // Level 2: Trade on STRONG patterns
         g_min_pattern_strength = 4;    // 4-5 star patterns
         g_min_confluence = 4;          // Need 4 factors aligned
         g_require_mtf = true;          // MTF must align
         g_require_volume = true;       // Volume must confirm
         g_allow_counter_trend = false; // No counter-trend
         break;

      case 3:  // Level 3: Trade on GOOD patterns (DEFAULT)
         g_min_pattern_strength = 3;    // 3-5 star patterns
         g_min_confluence = 3;          // Need 3 factors aligned
         g_require_mtf = true;          // MTF must align
         g_require_volume = false;      // Volume optional
         g_allow_counter_trend = false; // No counter-trend
         break;

      case 4:  // Level 4: Trade on DECENT patterns
         g_min_pattern_strength = 2;    // 2-5 star patterns
         g_min_confluence = 2;          // Need 2 factors aligned
         g_require_mtf = false;         // MTF optional
         g_require_volume = false;      // Volume optional
         g_allow_counter_trend = true;  // Counter-trend allowed
         break;

      case 5:  // Level 5: Trade on ANY valid pattern - MAX AGGRESSION
         g_min_pattern_strength = 2;    // Still need real patterns (2-5 stars)
         g_min_confluence = 0;          // Pattern detection alone is sufficient
         g_require_mtf = false;         // MTF optional
         g_require_volume = false;      // Volume optional
         g_allow_counter_trend = true;  // Counter-trend allowed
         break;

      default:
         g_min_pattern_strength = 3;
         g_min_confluence = 3;
         g_require_mtf = true;
         g_require_volume = false;
         g_allow_counter_trend = false;
   }

   // Override with user settings if they explicitly allow counter-trend
   if(AllowCounterTrend)
      g_allow_counter_trend = true;
}

//+------------------------------------------------------------------+
//| TICK - Main Logic                                                 |
//+------------------------------------------------------------------+
void OnTick()
{
   // Update P&L tracking
   UpdatePnLTracking();

   // Update control panel display
   if(g_control_panel_visible)
      UpdateControlPanelInfo();

   // Manage existing trades first (always run, even when paused)
   ManageTrades();

   // Periodic availability check
   if(EnableAvailabilityCheck)
   {
      if(TimeCurrent() - g_last_avail_check >= AvailCheckInterval)
      {
         PerformAvailabilityCheck();

         if(ShowAvailabilityPanel)
            UpdateAvailabilityPanel();
      }

      // Block trading if availability check fails
      if(!g_availability_ok && RequireAllChecksPass)
      {
         return;
      }
   }

   // New bar check - only analyze on new bars
   static datetime last_bar = 0;
   datetime cur_bar = iTime(Symbol(), Timeframe, 0);
   if(cur_bar == last_bar) return;
   last_bar = cur_bar;

   // Pre-flight checks
   if(!EnableTrading) return;

   // Check if trading is paused by user
   if(g_trading_paused) return;

   // Additional availability gate check (even if not RequireAllChecksPass)
   if(EnableAvailabilityCheck && g_avail_report.overall_status == AVAIL_CRITICAL)
   {
      // Critical issues - do not attempt to trade
      return;
   }

   if(!CheckRiskLimits()) return;
   if(!CheckTradeCount()) return;

   // Check filters
   CheckSpread();
   if(UseSpreadFilter && !g_spread_ok) return;

   CheckSession();
   if(UseSessionFilter && !g_session_ok) return;

   // Analyze market
   DetectRegime();

   // Scan for candlestick patterns
   ScanPatterns();
   if(!g_has_pattern) return;

   // Check if pattern meets minimum strength for current aggression level
   if(g_pattern.strength < g_min_pattern_strength)
   {
      g_has_pattern = false;
      return;
   }

   // Check pattern expiry
   if(UsePatternDecay)
   {
      int bars_old = iBarShift(Symbol(), Timeframe, g_pattern.time, false);
      if(bars_old > g_pattern_expiry)
      {
         g_has_pattern = false;
         return;
      }
   }

   // Check trend alignment
   CheckTrendAlignment();
   if(RequireTrendAlignment && !g_trend_aligned)
   {
      // If counter-trend not allowed at this level, skip
      if(!g_allow_counter_trend)
      {
         g_has_pattern = false;
         return;
      }
   }

   // Check filters
   if(UseVolumeFilter) CheckVolume();
   if(UseMTF) CheckMTF();

   // Mandatory filter checks based on aggression level
   if(g_require_mtf && !g_mtf_aligned)
   {
      g_has_pattern = false;
      return;
   }

   if(g_require_volume && !g_volume_ok)
   {
      g_has_pattern = false;
      return;
   }

   // Calculate confluence score
   int confluence = CalcConfluence();
   if(confluence < g_min_confluence)
   {
      g_has_pattern = false;
      return;
   }

   // All checks passed - EXECUTE TRADE
   Print("===============================================================");
   Print("  SIGNAL: ", g_pattern.name, " [", g_pattern.strength, "*]");
   Print("  Direction: ", g_pattern.is_bull ? "BUY" : "SELL");
   Print("  Confluence: ", confluence, "/", g_min_confluence, " (Level ", AggressionLevel, ")");
   Print("===============================================================");

   ExecuteTrade();

   if(AlertOnPattern)
      Alert(Symbol(), " ", g_pattern.name, " ", g_pattern.is_bull ? "BUY" : "SELL");
}

//+------------------------------------------------------------------+
//| PATTERN DETECTION - All 20 Real Candlestick Patterns              |
//| Organized by strength (5-star to 2-star)                          |
//| NO fake patterns - every pattern is a real candlestick formation  |
//+------------------------------------------------------------------+
void ScanPatterns()
{
   g_has_pattern = false;

   double o1 = iOpen(Symbol(), Timeframe, 1);
   double h1 = iHigh(Symbol(), Timeframe, 1);
   double l1 = iLow(Symbol(), Timeframe, 1);
   double c1 = iClose(Symbol(), Timeframe, 1);

   double o2 = iOpen(Symbol(), Timeframe, 2);
   double h2 = iHigh(Symbol(), Timeframe, 2);
   double l2 = iLow(Symbol(), Timeframe, 2);
   double c2 = iClose(Symbol(), Timeframe, 2);

   double o3 = iOpen(Symbol(), Timeframe, 3);
   double h3 = iHigh(Symbol(), Timeframe, 3);
   double l3 = iLow(Symbol(), Timeframe, 3);
   double c3 = iClose(Symbol(), Timeframe, 3);

   double body1 = MathAbs(c1 - o1);
   double range1 = h1 - l1;
   double body2 = MathAbs(c2 - o2);
   double body3 = MathAbs(c3 - o3);

   if(range1 < Point * 5) return;  // Skip tiny candles

   double uw1 = h1 - MathMax(o1, c1);  // Upper wick
   double lw1 = MathMin(o1, c1) - l1;  // Lower wick
   double body_ratio = body1 / range1;

   double atr = iATR(Symbol(), Timeframe, 14, 0);

   // ═══════════════════════════════════════════════════════════════
   // 5-STAR PATTERNS - Highest reliability reversal signals
   // ═══════════════════════════════════════════════════════════════

   // BULLISH ENGULFING - Strong reversal after downtrend
   if(c2 < o2 && c1 > o1 && c1 > o2 && o1 < c2 && body1 > body2 * 1.1)
   {
      SetPattern("BULLISH ENGULFING", true, 5, c1, l1 - atr * 0.5);
      return;
   }

   // BEARISH ENGULFING - Strong reversal after uptrend
   if(c2 > o2 && c1 < o1 && o1 > c2 && c1 < o2 && body1 > body2 * 1.1)
   {
      SetPattern("BEARISH ENGULFING", false, 5, c1, h1 + atr * 0.5);
      return;
   }

   // MORNING STAR - 3-candle bullish reversal
   if(c3 < o3 && body2 < body3 * 0.3 && c1 > o1 && c1 > (o3 + c3) / 2 && body1 > body3 * 0.5)
   {
      SetPattern("MORNING STAR", true, 5, c1, MathMin(l1, MathMin(l2, l3)) - atr * 0.3);
      return;
   }

   // EVENING STAR - 3-candle bearish reversal
   if(c3 > o3 && body2 < body3 * 0.3 && c1 < o1 && c1 < (o3 + c3) / 2 && body1 > body3 * 0.5)
   {
      SetPattern("EVENING STAR", false, 5, c1, MathMax(h1, MathMax(h2, h3)) + atr * 0.3);
      return;
   }

   // THREE WHITE SOLDIERS - Strong bullish continuation
   if(c3 > o3 && c2 > o2 && c1 > o1 && c1 > c2 && c2 > c3 && o2 > o3 && o1 > o2)
   {
      if(body1 > range1 * 0.6 && body2 > (h2-l2) * 0.6 && body3 > (h3-l3) * 0.6)
      {
         SetPattern("THREE WHITE SOLDIERS", true, 5, c1, l3 - atr * 0.5);
         return;
      }
   }

   // THREE BLACK CROWS - Strong bearish continuation
   if(c3 < o3 && c2 < o2 && c1 < o1 && c1 < c2 && c2 < c3 && o2 < o3 && o1 < o2)
   {
      if(body1 > range1 * 0.6 && body2 > (h2-l2) * 0.6 && body3 > (h3-l3) * 0.6)
      {
         SetPattern("THREE BLACK CROWS", false, 5, c1, h3 + atr * 0.5);
         return;
      }
   }

   // BULLISH MARUBOZU - Full body, no wicks, strong buying
   if(c1 > o1 && uw1 < range1 * 0.02 && lw1 < range1 * 0.02 && body1 > range1 * 0.95)
   {
      SetPattern("BULLISH MARUBOZU", true, 5, c1, o1 - atr * 0.3);
      return;
   }

   // BEARISH MARUBOZU - Full body, no wicks, strong selling
   if(c1 < o1 && uw1 < range1 * 0.02 && lw1 < range1 * 0.02 && body1 > range1 * 0.95)
   {
      SetPattern("BEARISH MARUBOZU", false, 5, c1, o1 + atr * 0.3);
      return;
   }

   // ═══════════════════════════════════════════════════════════════
   // 4-STAR PATTERNS - High reliability signals
   // ═══════════════════════════════════════════════════════════════

   // HAMMER - Bullish reversal at bottom
   if(lw1 > body1 * 2.5 && uw1 < body1 * 0.3 && body1 > range1 * 0.1 && body_ratio < 0.35)
   {
      SetPattern("HAMMER", true, 4, c1, l1 - atr * 0.2);
      return;
   }

   // INVERTED HAMMER - Bullish reversal at bottom
   if(uw1 > body1 * 2.5 && lw1 < body1 * 0.3 && c1 > o1 && body_ratio < 0.35)
   {
      SetPattern("INVERTED HAMMER", true, 4, c1, l1 - atr * 0.2);
      return;
   }

   // SHOOTING STAR - Bearish reversal at top
   if(uw1 > body1 * 2.5 && lw1 < body1 * 0.3 && body1 > range1 * 0.1 && body_ratio < 0.35)
   {
      SetPattern("SHOOTING STAR", false, 4, c1, h1 + atr * 0.2);
      return;
   }

   // HANGING MAN - Bearish reversal at top
   if(lw1 > body1 * 2.5 && uw1 < body1 * 0.3 && c1 < o1 && body_ratio < 0.35)
   {
      SetPattern("HANGING MAN", false, 4, c1, h1 + atr * 0.2);
      return;
   }

   // BULLISH HARAMI - Inside bar bullish reversal
   if(c2 < o2 && c1 > o1 && o1 > c2 && c1 < o2 && body1 < body2 * 0.5)
   {
      SetPattern("BULLISH HARAMI", true, 4, c1, l2 - atr * 0.2);
      return;
   }

   // BEARISH HARAMI - Inside bar bearish reversal
   if(c2 > o2 && c1 < o1 && c1 > o2 && o1 < c2 && body1 < body2 * 0.5)
   {
      SetPattern("BEARISH HARAMI", false, 4, c1, h2 + atr * 0.2);
      return;
   }

   // PIERCING LINE - Bullish reversal
   if(c2 < o2 && c1 > o1 && o1 < c2 && c1 > (o2 + c2) / 2 && c1 < o2)
   {
      SetPattern("PIERCING LINE", true, 4, c1, l1 - atr * 0.2);
      return;
   }

   // DARK CLOUD COVER - Bearish reversal
   if(c2 > o2 && c1 < o1 && o1 > c2 && c1 < (o2 + c2) / 2 && c1 > o2)
   {
      SetPattern("DARK CLOUD COVER", false, 4, c1, h1 + atr * 0.2);
      return;
   }

   // ═══════════════════════════════════════════════════════════════
   // 3-STAR PATTERNS - Moderate reliability signals
   // ═══════════════════════════════════════════════════════════════

   // TWEEZER BOTTOM - Double bottom pattern
   double tol = atr * 0.1;
   if(MathAbs(l1 - l2) < tol && c2 < o2 && c1 > o1)
   {
      SetPattern("TWEEZER BOTTOM", true, 3, c1, MathMin(l1, l2) - atr * 0.2);
      return;
   }

   // TWEEZER TOP - Double top pattern
   if(MathAbs(h1 - h2) < tol && c2 > o2 && c1 < o1)
   {
      SetPattern("TWEEZER TOP", false, 3, c1, MathMax(h1, h2) + atr * 0.2);
      return;
   }

   // DRAGONFLY DOJI - Bullish reversal
   if(body_ratio < 0.05 && lw1 > range1 * 0.7 && uw1 < range1 * 0.1)
   {
      SetPattern("DRAGONFLY DOJI", true, 3, c1, l1 - atr * 0.2);
      return;
   }

   // GRAVESTONE DOJI - Bearish reversal
   if(body_ratio < 0.05 && uw1 > range1 * 0.7 && lw1 < range1 * 0.1)
   {
      SetPattern("GRAVESTONE DOJI", false, 3, c1, h1 + atr * 0.2);
      return;
   }

   // BULLISH BELT HOLD - Strong open at low
   if(c1 > o1 && lw1 < range1 * 0.02 && body1 > range1 * 0.7)
   {
      SetPattern("BULLISH BELT HOLD", true, 3, c1, o1 - atr * 0.2);
      return;
   }

   // BEARISH BELT HOLD - Strong open at high
   if(c1 < o1 && uw1 < range1 * 0.02 && body1 > range1 * 0.7)
   {
      SetPattern("BEARISH BELT HOLD", false, 3, c1, o1 + atr * 0.2);
      return;
   }

   // ═══════════════════════════════════════════════════════════════
   // 2-STAR PATTERNS - Lower reliability, need more confluence
   // ═══════════════════════════════════════════════════════════════

   // DOJI - Indecision, direction from prior candle context
   if(body_ratio < 0.1 && range1 > atr * 0.3)
   {
      // Look at prior candles to determine potential reversal direction
      // If prior candle was bearish, doji signals potential bullish reversal
      bool prior_bearish = (c2 < o2);
      bool is_bull = prior_bearish;
      SetPattern("DOJI", is_bull, 2, c1, is_bull ? l1 - atr * 0.3 : h1 + atr * 0.3);
      return;
   }

   // SPINNING TOP - Indecision with longer wicks
   if(body_ratio < 0.35 && uw1 > body1 * 0.8 && lw1 > body1 * 0.8 && body1 > 0)
   {
      // Same logic - reversal of prior direction
      bool prior_bearish = (c2 < o2);
      bool is_bull = prior_bearish;
      SetPattern("SPINNING TOP", is_bull, 2, c1, is_bull ? l1 - atr * 0.3 : h1 + atr * 0.3);
      return;
   }

   // No valid pattern found
}

void SetPattern(string name, bool bull, int strength, double entry, double sl)
{
   g_pattern.name = name;
   g_pattern.is_bull = bull;
   g_pattern.strength = strength;
   g_pattern.entry_price = entry;
   g_pattern.sl_price = sl;
   g_pattern.time = iTime(Symbol(), Timeframe, 1);
   g_pattern.bar_index = 1;
   g_has_pattern = true;

   if(ShowPatternArrows)
   {
      string arrow_name = "IGTR_Arrow_" + TimeToString(g_pattern.time);
      ObjectCreate(0, arrow_name, OBJ_ARROW, 0, g_pattern.time, bull ? iLow(Symbol(), Timeframe, 1) - Point*20 : iHigh(Symbol(), Timeframe, 1) + Point*20);
      ObjectSetInteger(0, arrow_name, OBJPROP_ARROWCODE, bull ? 233 : 234);
      ObjectSetInteger(0, arrow_name, OBJPROP_COLOR, bull ? clrLime : clrRed);
   }
}

//+------------------------------------------------------------------+
//| REGIME DETECTION                                                  |
//+------------------------------------------------------------------+
void DetectRegime()
{
   double ema50 = iMA(Symbol(), Timeframe, 50, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema200 = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), Timeframe, 1);
   double atr = iATR(Symbol(), Timeframe, 14, 0);

   // Check EMA slope for trend direction
   double ema200_now = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema200_prev = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 10);
   double slope = ema200_now - ema200_prev;

   if(price > ema50 && price > ema200 && ema50 > ema200 && slope > atr * 0.05)
      g_regime = TREND_UP;
   else if(price < ema50 && price < ema200 && ema50 < ema200 && slope < -atr * 0.05)
      g_regime = TREND_DOWN;
   else if(MathAbs(slope) < atr * 0.02)
      g_regime = RANGE;
   else
      g_regime = TRANSITION;
}

//+------------------------------------------------------------------+
//| TREND ALIGNMENT CHECK                                             |
//+------------------------------------------------------------------+
void CheckTrendAlignment()
{
   g_trend_aligned = false;

   if(g_regime == TREND_UP && g_pattern.is_bull)
      g_trend_aligned = true;
   else if(g_regime == TREND_DOWN && !g_pattern.is_bull)
      g_trend_aligned = true;
   else if(g_regime == RANGE)
      g_trend_aligned = true;  // In range, both directions okay
}

//+------------------------------------------------------------------+
//| MTF CHECK                                                         |
//+------------------------------------------------------------------+
void CheckMTF()
{
   g_mtf_aligned = false;

   int htf = GetHigherTF();

   // Safety check for backtesting - if HTF data not available, assume aligned
   int htf_bars = iBars(Symbol(), htf);
   if(htf_bars < 50)
   {
      g_mtf_aligned = true;  // Assume aligned if data not available
      return;
   }

   double ema = iMA(Symbol(), htf, 50, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), htf, 0);

   // Check for invalid values (common in backtesting)
   if(ema <= 0 || price <= 0)
   {
      g_mtf_aligned = true;  // Assume aligned if data invalid
      return;
   }

   if(g_pattern.is_bull && price > ema)
      g_mtf_aligned = true;
   else if(!g_pattern.is_bull && price < ema)
      g_mtf_aligned = true;
}

int GetHigherTF()
{
   if(Timeframe == PERIOD_M1) return PERIOD_M5;
   if(Timeframe == PERIOD_M5) return PERIOD_M15;
   if(Timeframe == PERIOD_M15) return PERIOD_H1;
   if(Timeframe == PERIOD_M30) return PERIOD_H1;
   if(Timeframe == PERIOD_H1) return PERIOD_H4;
   if(Timeframe == PERIOD_H4) return PERIOD_D1;
   return PERIOD_W1;
}

//+------------------------------------------------------------------+
//| VOLUME CHECK                                                      |
//+------------------------------------------------------------------+
void CheckVolume()
{
   g_volume_ok = false;

   long current_vol = iVolume(Symbol(), Timeframe, 1);
   double avg_vol = 0;

   for(int i = 1; i <= 20; i++)
      avg_vol += (double)iVolume(Symbol(), Timeframe, i);
   avg_vol /= 20.0;

   if(avg_vol > 0 && (current_vol / avg_vol) >= g_vol_thresh)
      g_volume_ok = true;
}

//+------------------------------------------------------------------+
//| SPREAD CHECK                                                      |
//+------------------------------------------------------------------+
void CheckSpread()
{
   g_spread_ok = true;

   double spread = MarketInfo(Symbol(), MODE_SPREAD) * Point;
   double atr = iATR(Symbol(), Timeframe, 14, 0);

   if(spread > atr * g_spread_lim)
      g_spread_ok = false;
}

//+------------------------------------------------------------------+
//| SESSION CHECK                                                     |
//+------------------------------------------------------------------+
void CheckSession()
{
   g_session_ok = true;

   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour - (int)BrokerGMT;
   if(hour < 0) hour += 24;
   if(hour >= 24) hour -= 24;

   if(hour >= 0 && hour < 8)
   {
      g_session = ASIAN;
      g_session_ok = TradeAsian;
   }
   else if(hour >= 8 && hour < 13)
   {
      g_session = LONDON;
      g_session_ok = TradeLondon;
   }
   else if(hour >= 13 && hour < 17)
   {
      g_session = OVERLAP;
      g_session_ok = (TradeLondon || TradeNY);
   }
   else if(hour >= 17 && hour < 22)
   {
      g_session = NEWYORK;
      g_session_ok = TradeNY;
   }
   else
   {
      g_session = CLOSED;
      g_session_ok = false;
   }
}

//+------------------------------------------------------------------+
//| CONFLUENCE CALCULATION                                            |
//+------------------------------------------------------------------+
int CalcConfluence()
{
   int score = 0;

   // 1. Pattern strength bonus
   if(g_pattern.strength >= 4) score++;
   if(g_pattern.strength >= 5) score++;

   // 2. Trend alignment
   if(g_trend_aligned) score++;

   // 3. MTF alignment
   if(g_mtf_aligned) score++;

   // 4. Volume confirmation
   if(g_volume_ok) score++;

   // 5. Spread acceptable
   if(g_spread_ok) score++;

   // 6. Clear regime (not transition)
   if(g_regime != TRANSITION) score++;

   return score;
}

//+------------------------------------------------------------------+
//| RISK CHECKS                                                       |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   if(g_daily_lim < 100)
   {
      double daily_loss = (g_daily_start - AccountBalance()) / g_daily_start * 100.0;
      if(daily_loss >= g_daily_lim) return false;
   }

   if(g_weekly_lim < 100)
   {
      double weekly_loss = (g_weekly_start - AccountBalance()) / g_weekly_start * 100.0;
      if(weekly_loss >= g_weekly_lim) return false;
   }

   return true;
}

bool CheckTradeCount()
{
   int total = 0;
   int symbol_count = 0;

   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      total++;
      if(OrderSymbol() == Symbol()) symbol_count++;
   }

   if(total >= g_max_trades) return false;
   if(symbol_count >= g_max_per_sym) return false;

   return true;
}

//+------------------------------------------------------------------+
//| LOT CALCULATION                                                   |
//+------------------------------------------------------------------+
double CalcLot(double sl_distance)
{
   double bmin = MarketInfo(Symbol(), MODE_MINLOT);
   double bmax = MarketInfo(Symbol(), MODE_MAXLOT);
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);

   double lot;

   if(SizingMode == SIZE_FIXED)
   {
      lot = g_min_lot;
   }
   else
   {
      double risk_amount = AccountBalance() * g_risk;
      double tick_value = MarketInfo(Symbol(), MODE_TICKVALUE);
      double tick_size = MarketInfo(Symbol(), MODE_TICKSIZE);

      if(tick_size <= 0 || tick_value <= 0) return bmin;

      double loss_per_lot = (sl_distance / tick_size) * tick_value;
      lot = (loss_per_lot > 0) ? risk_amount / loss_per_lot : bmin;
   }

   // Normalize
   lot = MathFloor(lot / step) * step;
   if(lot < bmin) lot = bmin;
   if(lot > bmax) lot = bmax;
   if(lot > g_max_lot) lot = g_max_lot;

   return lot;
}

//+------------------------------------------------------------------+
//| TRADE EXECUTION                                                   |
//+------------------------------------------------------------------+
void ExecuteTrade()
{
   bool is_buy = g_pattern.is_bull;
   double entry = is_buy ? Ask : Bid;

   // Calculate stop loss
   double sl_distance;

   if(SL_Mode == SL_MODE_ATR)
   {
      double atr = iATR(Symbol(), Timeframe, 14, 0);
      sl_distance = atr * g_sl_atr;

      // Also respect pattern-based SL
      double pattern_sl_dist = MathAbs(entry - g_pattern.sl_price);
      sl_distance = MathMax(sl_distance, pattern_sl_dist);
   }
   else
   {
      sl_distance = g_sl_pips * Point;
      if(Digits == 5 || Digits == 3)
         sl_distance *= 10;
   }

   double sl = is_buy ? entry - sl_distance : entry + sl_distance;
   double tp = entry + (is_buy ? 1 : -1) * sl_distance * g_tp_rr;

   sl = NormalizeDouble(sl, Digits);
   tp = NormalizeDouble(tp, Digits);

   // Calculate lot
   double lot = CalcLot(sl_distance);

   // Execute
   string comment = g_pattern.name + "|L" + IntegerToString((int)AggressionLevel);
   int ticket;

   if(is_buy)
      ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 10, sl, tp, comment, MagicNumber, 0, clrGreen);
   else
      ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 10, sl, tp, comment, MagicNumber, 0, clrRed);

   if(ticket > 0)
   {
      Print("TRADE EXECUTED #", ticket, " | ", g_pattern.name, " | ", is_buy ? "BUY" : "SELL", " | Lot: ", lot);
      g_has_pattern = false;

      if(AlertOnTrade)
         Alert("Trade executed: ", Symbol(), " ", g_pattern.name);
   }
   else
   {
      Print("TRADE FAILED - Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| TRADE MANAGEMENT                                                  |
//+------------------------------------------------------------------+
void ManageTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      int ticket = OrderTicket();
      double entry = OrderOpenPrice();
      double sl = OrderStopLoss();
      double tp = OrderTakeProfit();
      double lots = OrderLots();
      bool is_buy = (OrderType() == OP_BUY);
      double price = is_buy ? Bid : Ask;

      double sl_dist = MathAbs(entry - sl);
      if(sl_dist < Point) continue;

      double profit_dist = is_buy ? (price - entry) : (entry - price);
      double r_multiple = profit_dist / sl_dist;

      // Breakeven at 1R
      if(UseBreakeven && r_multiple >= 1.0)
      {
         double be_sl = entry + (is_buy ? 1 : -1) * Point * 5;
         if((is_buy && be_sl > sl) || (!is_buy && be_sl < sl))
         {
            if(OrderModify(ticket, entry, be_sl, tp, 0, clrBlue))
               Print("Breakeven #", ticket);
         }
      }

      // Trailing stop at 1.5R
      if(g_trailing_enabled && r_multiple >= 1.5)
      {
         double trail_sl;
         if(is_buy)
         {
            trail_sl = price - sl_dist * 0.5;
            if(trail_sl > sl)
               OrderModify(ticket, entry, trail_sl, tp, 0, clrAqua);
         }
         else
         {
            trail_sl = price + sl_dist * 0.5;
            if(trail_sl < sl)
               OrderModify(ticket, entry, trail_sl, tp, 0, clrAqua);
         }
      }

      // Partial close at 2R
      if(UsePartialClose && r_multiple >= 2.0)
      {
         double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
         double close_lot = NormalizeDouble(lots * (double)PartialPct / 100.0, 2);

         if(close_lot >= min_lot && (lots - close_lot) >= min_lot)
         {
            if(OrderClose(ticket, close_lot, price, 10, clrYellow))
               Print("Partial close #", ticket);
         }
      }
   }
}

//+------------------------------------------------------------------+
//|              AVAILABILITY CHECKING SYSTEM                         |
//+------------------------------------------------------------------+
//| Professional-grade pre-trade validation system                    |
//| Ensures all prerequisites are met before trading                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Initialize the availability checking system                       |
//+------------------------------------------------------------------+
void InitAvailabilitySystem()
{
   // Initialize all checks to unknown state
   for(int i = 0; i < 10; i++)
   {
      g_checks[i].check_type = (ENUM_CHECK_TYPE)i;
      g_checks[i].status = AVAIL_OK;
      g_checks[i].message = "Not checked";
      g_checks[i].last_check = 0;
      g_checks[i].retry_count = 0;
   }

   // Initialize report
   g_avail_report.overall_status = AVAIL_OK;
   g_avail_report.checks_passed = 0;
   g_avail_report.checks_warning = 0;
   g_avail_report.checks_failed = 0;
   g_avail_report.checks_critical = 0;
   g_avail_report.summary = "Initializing...";
   g_avail_report.report_time = TimeCurrent();
   g_avail_report.can_trade = false;

   g_availability_ok = false;
   g_consecutive_failures = 0;
   g_last_avail_check = 0;

   Print("  Availability checking system initialized");
}

//+------------------------------------------------------------------+
//| Master function: Perform all availability checks                  |
//+------------------------------------------------------------------+
void PerformAvailabilityCheck()
{
   g_last_avail_check = TimeCurrent();

   // Reset counters
   g_avail_report.checks_passed = 0;
   g_avail_report.checks_warning = 0;
   g_avail_report.checks_failed = 0;
   g_avail_report.checks_critical = 0;

   // Run all individual checks
   CheckBrokerConnection();
   CheckSymbolValid();
   CheckSymbolTradeable();
   CheckMarketOpen();
   CheckTradingAllowed();
   CheckEATrading();
   CheckAccountValid();
   CheckMarginSufficient();
   CheckSpreadAcceptable();
   CheckDataAvailable();

   // Aggregate results
   AggregateAvailabilityResults();

   // Handle failures with retry logic
   if(!g_availability_ok)
   {
      g_consecutive_failures++;

      if(g_consecutive_failures <= MaxRetryAttempts)
      {
         Print("  AVAILABILITY: Check failed (attempt ", g_consecutive_failures,
               "/", MaxRetryAttempts, ") - will retry in ", RetryDelaySeconds, "s");
      }
      else if(g_consecutive_failures == MaxRetryAttempts + 1)
      {
         Print("  AVAILABILITY: Max retries exceeded - trading suspended");
         if(AlertOnUnavailable)
            Alert(Symbol(), " - Trading unavailable: ", g_avail_report.summary);
      }
   }
   else
   {
      // Reset failure counter on success
      if(g_consecutive_failures > 0)
      {
         Print("  AVAILABILITY: System recovered after ", g_consecutive_failures, " failures");
         g_consecutive_failures = 0;
      }
   }
}

//+------------------------------------------------------------------+
//| Check 1: Broker/Server Connection                                 |
//+------------------------------------------------------------------+
void CheckBrokerConnection()
{
   int idx = CHK_BROKER_CONNECTION;
   g_checks[idx].last_check = TimeCurrent();

   // Check if connected to server
   if(!IsConnected())
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Not connected to broker server";
      return;
   }

   // Check ping/latency through recent tick
   datetime last_tick = MarketInfo(Symbol(), MODE_TIME);
   int data_age = (int)(TimeCurrent() - last_tick);

   if(data_age > MaxDataAgeSeconds * 3)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Server connection unstable (data age: " + IntegerToString(data_age) + "s)";
      return;
   }

   if(data_age > MaxDataAgeSeconds)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Possible connection issues (data age: " + IntegerToString(data_age) + "s)";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Connected (data age: " + IntegerToString(data_age) + "s)";
}

//+------------------------------------------------------------------+
//| Check 2: Symbol Validity                                          |
//+------------------------------------------------------------------+
void CheckSymbolValid()
{
   int idx = CHK_SYMBOL_VALID;
   g_checks[idx].last_check = TimeCurrent();

   string sym = Symbol();

   // Check if symbol exists in Market Watch
   double bid = MarketInfo(sym, MODE_BID);
   double ask = MarketInfo(sym, MODE_ASK);

   if(bid <= 0 || ask <= 0)
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Symbol not found or no price data";
      return;
   }

   // Check for valid digits
   int digits = (int)MarketInfo(sym, MODE_DIGITS);
   if(digits < 0 || digits > 8)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Invalid symbol configuration (digits: " + IntegerToString(digits) + ")";
      return;
   }

   // Check point value
   double point = MarketInfo(sym, MODE_POINT);
   if(point <= 0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Invalid point value";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Symbol valid (" + sym + ", " + IntegerToString(digits) + " digits)";
}

//+------------------------------------------------------------------+
//| Check 3: Symbol Tradeable                                         |
//+------------------------------------------------------------------+
void CheckSymbolTradeable()
{
   int idx = CHK_SYMBOL_TRADEABLE;
   g_checks[idx].last_check = TimeCurrent();

   string sym = Symbol();

   // Check trade mode
   int trade_mode = (int)MarketInfo(sym, MODE_TRADEALLOWED);

   if(trade_mode == 0)
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Trading disabled for this symbol";
      return;
   }

   // Check minimum lot
   double min_lot = MarketInfo(sym, MODE_MINLOT);
   double max_lot = MarketInfo(sym, MODE_MAXLOT);
   double lot_step = MarketInfo(sym, MODE_LOTSTEP);

   if(min_lot <= 0 || max_lot <= 0 || lot_step <= 0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Invalid lot specifications";
      return;
   }

   // Check tick value
   double tick_value = MarketInfo(sym, MODE_TICKVALUE);
   if(tick_value <= 0)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Cannot calculate tick value - may affect position sizing";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Tradeable (lot: " + DoubleToString(min_lot, 2) + "-" + DoubleToString(max_lot, 2) + ")";
}

//+------------------------------------------------------------------+
//| Check 4: Market Open                                              |
//+------------------------------------------------------------------+
void CheckMarketOpen()
{
   int idx = CHK_MARKET_OPEN;
   g_checks[idx].last_check = TimeCurrent();

   // Check spread as indicator of market state
   // Very high spread often indicates market closed or illiquid
   double spread = MarketInfo(Symbol(), MODE_SPREAD) * Point;
   double atr = iATR(Symbol(), Timeframe, 14, 0);

   // If spread is extremely high (> 500% ATR), market is likely closed
   if(atr > 0 && spread > atr * 5.0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Market appears closed (extreme spread)";
      return;
   }

   // Check recent price movement
   datetime last_tick = MarketInfo(Symbol(), MODE_TIME);
   int seconds_since_tick = (int)(TimeCurrent() - last_tick);

   // If no tick for more than 5 minutes, market might be closed
   if(seconds_since_tick > 300)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "No recent ticks (" + IntegerToString(seconds_since_tick) + "s) - market may be closed";
      return;
   }

   // Check if it's weekend
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   // Saturday = 6, Sunday = 0
   if(dt.day_of_week == 0 || dt.day_of_week == 6)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Weekend - limited liquidity expected";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Market open";
}

//+------------------------------------------------------------------+
//| Check 5: Account Trading Allowed                                  |
//+------------------------------------------------------------------+
void CheckTradingAllowed()
{
   int idx = CHK_TRADING_ALLOWED;
   g_checks[idx].last_check = TimeCurrent();

   // Check if trading is allowed for the account
   if(!IsTradeAllowed())
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Trading not allowed (check account/context)";
      return;
   }

   // Check for trade context availability
   if(IsTradeContextBusy())
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Trade context busy - another EA may be trading";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Trading allowed";
}

//+------------------------------------------------------------------+
//| Check 6: EA Trading Enabled                                       |
//+------------------------------------------------------------------+
void CheckEATrading()
{
   int idx = CHK_EA_TRADING;
   g_checks[idx].last_check = TimeCurrent();

   // Check if EA trading is enabled globally
   if(!IsExpertEnabled())
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Expert Advisors disabled (check AutoTrading button)";
      return;
   }

   // Check if DLLs are allowed (sometimes needed for advanced features)
   if(!IsDllsAllowed())
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "DLLs not allowed - some features may be limited";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "EA trading enabled";
}

//+------------------------------------------------------------------+
//| Check 7: Account Valid                                            |
//+------------------------------------------------------------------+
void CheckAccountValid()
{
   int idx = CHK_ACCOUNT_VALID;
   g_checks[idx].last_check = TimeCurrent();

   // Check account number
   int account = AccountNumber();
   if(account <= 0)
   {
      g_checks[idx].status = AVAIL_CRITICAL;
      g_checks[idx].message = "Invalid account - not logged in";
      return;
   }

   // Check account type info
   string account_name = AccountName();
   string account_company = AccountCompany();

   if(StringLen(account_name) == 0 || StringLen(account_company) == 0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Account information incomplete";
      return;
   }

   // Check balance
   double balance = AccountBalance();
   if(balance <= 0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Zero or negative balance";
      return;
   }

   // Check account currency
   string currency = AccountCurrency();
   if(StringLen(currency) == 0)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Account currency not set";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Account #" + IntegerToString(account) + " (" + currency + ")";
}

//+------------------------------------------------------------------+
//| Check 8: Margin Sufficient                                        |
//+------------------------------------------------------------------+
void CheckMarginSufficient()
{
   int idx = CHK_MARGIN_SUFFICIENT;
   g_checks[idx].last_check = TimeCurrent();

   double balance = AccountBalance();
   double equity = AccountEquity();
   double free_margin = AccountFreeMargin();
   double margin_level = 0;

   // Calculate margin level if there are open positions
   double used_margin = AccountMargin();
   if(used_margin > 0)
      margin_level = (equity / used_margin) * 100.0;

   // Check if we can open minimum lot
   double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
   double margin_required = MarketInfo(Symbol(), MODE_MARGINREQUIRED) * min_lot;

   if(margin_required <= 0)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Cannot calculate margin requirements";
      return;
   }

   // Check if free margin is sufficient for minimum trade
   if(free_margin < margin_required * 1.5)  // 50% buffer
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Insufficient margin (need: " + DoubleToString(margin_required, 2) +
                              ", have: " + DoubleToString(free_margin, 2) + ")";
      return;
   }

   // Check margin level against minimum
   if(used_margin > 0 && margin_level < MinMarginLevel)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Margin level low (" + DoubleToString(margin_level, 1) +
                              "% < " + DoubleToString(MinMarginLevel, 1) + "%)";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   if(used_margin > 0)
      g_checks[idx].message = "Margin OK (level: " + DoubleToString(margin_level, 1) + "%)";
   else
      g_checks[idx].message = "Margin OK (free: " + DoubleToString(free_margin, 2) + ")";
}

//+------------------------------------------------------------------+
//| Check 9: Spread Acceptable                                        |
//+------------------------------------------------------------------+
void CheckSpreadAcceptable()
{
   int idx = CHK_SPREAD_ACCEPTABLE;
   g_checks[idx].last_check = TimeCurrent();

   double spread_points = MarketInfo(Symbol(), MODE_SPREAD);
   double spread_value = spread_points * Point;
   double atr = iATR(Symbol(), Timeframe, 14, 0);

   if(atr <= 0)
   {
      // Can't evaluate relative to ATR, use absolute check
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Cannot evaluate spread (ATR unavailable)";
      return;
   }

   double spread_atr_ratio = spread_value / atr;

   // Critical: spread > 200% ATR
   if(spread_atr_ratio > 2.0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Extreme spread (" + DoubleToString(spread_atr_ratio * 100, 0) + "% ATR)";
      return;
   }

   // Warning: spread > 100% ATR
   if(spread_atr_ratio > 1.0)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "High spread (" + DoubleToString(spread_atr_ratio * 100, 0) + "% ATR)";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Spread OK (" + DoubleToString(spread_points, 1) + " pts / " +
                           DoubleToString(spread_atr_ratio * 100, 0) + "% ATR)";
}

//+------------------------------------------------------------------+
//| Check 10: Price Data Available                                    |
//+------------------------------------------------------------------+
void CheckDataAvailable()
{
   int idx = CHK_DATA_AVAILABLE;
   g_checks[idx].last_check = TimeCurrent();

   // Check if we have enough bars for analysis
   int bars = iBars(Symbol(), Timeframe);

   if(bars < 200)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "Insufficient history (" + IntegerToString(bars) + " bars, need 200+)";
      return;
   }

   // Check data freshness
   datetime last_bar_time = iTime(Symbol(), Timeframe, 0);
   int bar_age = (int)(TimeCurrent() - last_bar_time);

   // Calculate expected max age based on timeframe
   int tf_seconds = PeriodSeconds(Timeframe);
   int max_expected_age = tf_seconds * 2;  // Allow 2x timeframe

   if(bar_age > max_expected_age)
   {
      g_checks[idx].status = AVAIL_WARNING;
      g_checks[idx].message = "Data may be stale (bar age: " + IntegerToString(bar_age) + "s)";
      return;
   }

   // Check ATR availability (indicator we use for calculations)
   double atr = iATR(Symbol(), Timeframe, 14, 0);
   if(atr <= 0)
   {
      g_checks[idx].status = AVAIL_ERROR;
      g_checks[idx].message = "ATR indicator failed - check data";
      return;
   }

   g_checks[idx].status = AVAIL_OK;
   g_checks[idx].message = "Data OK (" + IntegerToString(bars) + " bars available)";
}

//+------------------------------------------------------------------+
//| Aggregate all check results                                       |
//+------------------------------------------------------------------+
void AggregateAvailabilityResults()
{
   g_avail_report.checks_passed = 0;
   g_avail_report.checks_warning = 0;
   g_avail_report.checks_failed = 0;
   g_avail_report.checks_critical = 0;

   string issues = "";
   ENUM_AVAILABILITY_STATUS worst_status = AVAIL_OK;

   for(int i = 0; i < 10; i++)
   {
      switch(g_checks[i].status)
      {
         case AVAIL_OK:
            g_avail_report.checks_passed++;
            break;
         case AVAIL_WARNING:
            g_avail_report.checks_warning++;
            if(worst_status < AVAIL_WARNING) worst_status = AVAIL_WARNING;
            break;
         case AVAIL_ERROR:
            g_avail_report.checks_failed++;
            if(worst_status < AVAIL_ERROR) worst_status = AVAIL_ERROR;
            if(StringLen(issues) > 0) issues += "; ";
            issues += g_checks[i].message;
            break;
         case AVAIL_CRITICAL:
            g_avail_report.checks_critical++;
            worst_status = AVAIL_CRITICAL;
            if(StringLen(issues) > 0) issues += "; ";
            issues += g_checks[i].message;
            break;
      }
   }

   g_avail_report.overall_status = worst_status;
   g_avail_report.report_time = TimeCurrent();

   // Determine if trading is possible
   g_availability_ok = (g_avail_report.checks_critical == 0);

   if(RequireAllChecksPass)
      g_availability_ok = (g_avail_report.checks_passed == 10);

   g_avail_report.can_trade = g_availability_ok;

   // Build summary (using ASCII symbols - MT4 can't render Unicode)
   if(worst_status == AVAIL_OK)
   {
      g_avail_report.summary = "All systems operational";
      g_avail_status_text = "[+] READY";
      g_avail_status_color = clrLime;
   }
   else if(worst_status == AVAIL_WARNING)
   {
      g_avail_report.summary = IntegerToString(g_avail_report.checks_warning) + " warnings - trading with caution";
      g_avail_status_text = "[!] CAUTION";
      g_avail_status_color = clrYellow;
   }
   else if(worst_status == AVAIL_ERROR)
   {
      g_avail_report.summary = issues;
      g_avail_status_text = "[-] LIMITED";
      g_avail_status_color = clrOrange;
   }
   else
   {
      g_avail_report.summary = issues;
      g_avail_status_text = "[X] UNAVAILABLE";
      g_avail_status_color = clrRed;
   }
}

//+------------------------------------------------------------------+
//| Print detailed availability report to log                         |
//+------------------------------------------------------------------+
void PrintAvailabilityReport()
{
   Print("===============================================================");
   Print("  AVAILABILITY REPORT - ", TimeToString(g_avail_report.report_time, TIME_DATE | TIME_SECONDS));
   Print("===============================================================");

   for(int i = 0; i < 10; i++)
   {
      string status_str;
      switch(g_checks[i].status)
      {
         case AVAIL_OK:       status_str = "[+] "; break;
         case AVAIL_WARNING:  status_str = "[!] "; break;
         case AVAIL_ERROR:    status_str = "[-] "; break;
         case AVAIL_CRITICAL: status_str = "[X] "; break;
      }

      string check_name = GetCheckName((ENUM_CHECK_TYPE)i);
      Print("  ", status_str, check_name, ": ", g_checks[i].message);
   }

   Print("---------------------------------------------------------------");
   Print("  SUMMARY: ", g_avail_report.summary);
   Print("  Passed: ", g_avail_report.checks_passed,
         " | Warnings: ", g_avail_report.checks_warning,
         " | Failed: ", g_avail_report.checks_failed,
         " | Critical: ", g_avail_report.checks_critical);
   Print("  CAN TRADE: ", g_avail_report.can_trade ? "YES" : "NO");
   Print("===============================================================");
}

//+------------------------------------------------------------------+
//| Get human-readable name for check type                            |
//+------------------------------------------------------------------+
string GetCheckName(ENUM_CHECK_TYPE check)
{
   switch(check)
   {
      case CHK_BROKER_CONNECTION: return "Broker Connection";
      case CHK_SYMBOL_VALID:      return "Symbol Valid";
      case CHK_SYMBOL_TRADEABLE:  return "Symbol Tradeable";
      case CHK_MARKET_OPEN:       return "Market Open";
      case CHK_TRADING_ALLOWED:   return "Trading Allowed";
      case CHK_EA_TRADING:        return "EA Trading";
      case CHK_ACCOUNT_VALID:     return "Account Valid";
      case CHK_MARGIN_SUFFICIENT: return "Margin Sufficient";
      case CHK_SPREAD_ACCEPTABLE: return "Spread Acceptable";
      case CHK_DATA_AVAILABLE:    return "Data Available";
      default:                    return "Unknown Check";
   }
}

//+------------------------------------------------------------------+
//| Get status icon for display                                       |
//+------------------------------------------------------------------+
string GetStatusIcon(ENUM_AVAILABILITY_STATUS status)
{
   switch(status)
   {
      case AVAIL_OK:       return "+";  // MT4 can't render Unicode ✓
      case AVAIL_WARNING:  return "!";
      case AVAIL_ERROR:    return "-";  // MT4 can't render Unicode ✗
      case AVAIL_CRITICAL: return "X";
      default:             return "?";
   }
}

//+------------------------------------------------------------------+
//| Get status color for display                                      |
//+------------------------------------------------------------------+
color GetStatusColor(ENUM_AVAILABILITY_STATUS status)
{
   switch(status)
   {
      case AVAIL_OK:       return clrLime;
      case AVAIL_WARNING:  return clrYellow;
      case AVAIL_ERROR:    return clrOrange;
      case AVAIL_CRITICAL: return clrRed;
      default:             return clrGray;
   }
}

//+------------------------------------------------------------------+
//| Create availability status panel on chart                         |
//+------------------------------------------------------------------+
void CreateAvailabilityPanel()
{
   if(!ShowAvailabilityPanel) return;

   int x_start = 10;
   int y_start = 50;
   int line_height = 16;
   int panel_width = 220;
   int panel_height = 200;

   // Panel background
   string bg_name = "AVAIL_Background";
   ObjectCreate(0, bg_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bg_name, OBJPROP_XDISTANCE, x_start - 5);
   ObjectSetInteger(0, bg_name, OBJPROP_YDISTANCE, y_start - 5);
   ObjectSetInteger(0, bg_name, OBJPROP_XSIZE, panel_width);
   ObjectSetInteger(0, bg_name, OBJPROP_YSIZE, panel_height);
   ObjectSetInteger(0, bg_name, OBJPROP_BGCOLOR, C'20,20,30');
   ObjectSetInteger(0, bg_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bg_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, bg_name, OBJPROP_COLOR, C'50,50,70');
   ObjectSetInteger(0, bg_name, OBJPROP_WIDTH, 1);

   // Title
   CreateLabel("AVAIL_Title", x_start, y_start, "SYSTEM STATUS", clrWhite, 9);

   // Overall status
   CreateLabel("AVAIL_Status", x_start, y_start + line_height + 5, g_avail_status_text, g_avail_status_color, 10);

   // Individual checks
   int y = y_start + line_height * 3;
   for(int i = 0; i < 10; i++)
   {
      string icon = GetStatusIcon(g_checks[i].status);
      color clr = GetStatusColor(g_checks[i].status);
      string name = GetCheckName((ENUM_CHECK_TYPE)i);

      // Truncate name if too long
      if(StringLen(name) > 18)
         name = StringSubstr(name, 0, 18);

      CreateLabel("AVAIL_Check_" + IntegerToString(i), x_start, y,
                  icon + " " + name, clr, 8);
      y += line_height;
   }

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Update availability panel                                         |
//+------------------------------------------------------------------+
void UpdateAvailabilityPanel()
{
   if(!ShowAvailabilityPanel) return;

   // Update overall status
   ObjectSetString(0, "AVAIL_Status", OBJPROP_TEXT, g_avail_status_text);
   ObjectSetInteger(0, "AVAIL_Status", OBJPROP_COLOR, g_avail_status_color);

   // Update individual checks
   for(int i = 0; i < 10; i++)
   {
      string obj_name = "AVAIL_Check_" + IntegerToString(i);
      string icon = GetStatusIcon(g_checks[i].status);
      color clr = GetStatusColor(g_checks[i].status);
      string name = GetCheckName((ENUM_CHECK_TYPE)i);

      if(StringLen(name) > 18)
         name = StringSubstr(name, 0, 18);

      ObjectSetString(0, obj_name, OBJPROP_TEXT, icon + " " + name);
      ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
   }

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Helper: Create text label                                         |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int font_size)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, font_size);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| Get availability status for external queries                      |
//+------------------------------------------------------------------+
bool IsSystemAvailable()
{
   return g_availability_ok;
}

//+------------------------------------------------------------------+
//| Get detailed check result                                         |
//+------------------------------------------------------------------+
ENUM_AVAILABILITY_STATUS GetCheckStatus(ENUM_CHECK_TYPE check_type)
{
   if(check_type >= 0 && check_type < 10)
      return g_checks[check_type].status;
   return AVAIL_ERROR;
}

//+------------------------------------------------------------------+
//| Force refresh availability (for manual trigger)                   |
//+------------------------------------------------------------------+
void RefreshAvailability()
{
   g_last_avail_check = 0;  // Force immediate recheck
   PerformAvailabilityCheck();
   PrintAvailabilityReport();

   if(ShowAvailabilityPanel)
      UpdateAvailabilityPanel();
}

//+------------------------------------------------------------------+
//|                    CONTROL PANEL SYSTEM                           |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Create the control panel with tiered buttons                      |
//+------------------------------------------------------------------+
void CreateControlPanel()
{
   if(!g_control_panel_visible) return;

   int x = ControlPanelX;
   int y = ControlPanelY;
   int btn_width = 85;
   int btn_height = 22;
   int btn_spacing = 4;
   int row_height = btn_height + btn_spacing;
   int panel_width = btn_width * 3 + btn_spacing * 4;
   int panel_height = row_height * 10 + 100;  // 10 rows of buttons + info area

   // Panel background
   CreatePanelBackground("CTRL_Background", x - 5, y - 5, panel_width + 10, panel_height);

   // === INFO DISPLAY SECTION ===
   int info_y = y;
   CreateInfoLabel("CTRL_Title", x, info_y, "CONTROL PANEL", clrWhite, 10);
   info_y += 20;

   // P&L Display
   CreateInfoLabel("CTRL_PnL_Label", x, info_y, "Daily P&L:", clrGray, 8);
   CreateInfoLabel("CTRL_PnL_Value", x + 70, info_y, "$0.00", clrWhite, 8);
   info_y += 16;

   // Drawdown Display
   CreateInfoLabel("CTRL_DD_Label", x, info_y, "Drawdown:", clrGray, 8);
   CreateInfoLabel("CTRL_DD_Value", x + 70, info_y, "0.00%", clrWhite, 8);
   info_y += 16;

   // Session Display
   CreateInfoLabel("CTRL_Session_Label", x, info_y, "Session:", clrGray, 8);
   CreateInfoLabel("CTRL_Session_Value", x + 70, info_y, "---", clrWhite, 8);
   info_y += 16;

   // Spread Display
   CreateInfoLabel("CTRL_Spread_Label", x, info_y, "Spread:", clrGray, 8);
   CreateInfoLabel("CTRL_Spread_Value", x + 70, info_y, "0.0", clrWhite, 8);
   info_y += 20;

   // Separator
   CreateInfoLabel("CTRL_Sep1", x, info_y, "--- ADVANCED ---", clrDimGray, 8);
   info_y += 18;

   // === ADVANCED TIER (Top) ===
   int col1 = x;
   int col2 = x + btn_width + btn_spacing;
   int col3 = x + (btn_width + btn_spacing) * 2;

   // Row 1: Manual trading
   CreateButton("CTRL_BuyManual", col1, info_y, btn_width, btn_height, "BUY", clrWhite, clrDarkGreen);
   CreateButton("CTRL_SellManual", col2, info_y, btn_width, btn_height, "SELL", clrWhite, clrDarkRed);
   CreateButton("CTRL_ScaleIn", col3, info_y, btn_width, btn_height, "Scale In", clrWhite, clrDarkSlateGray);
   info_y += row_height;

   // Row 2: Position management
   CreateButton("CTRL_Hedge", col1, info_y, btn_width, btn_height, "Hedge", clrWhite, clrDarkOrange);
   CreateButton("CTRL_Reverse", col2, info_y, btn_width, btn_height, "Reverse", clrWhite, clrDarkMagenta);
   CreateButton("CTRL_Trailing", col3, info_y, btn_width, btn_height, "Trail: ON", clrBlack, clrLime);
   info_y += row_height;

   // Row 3: TP/SL adjustments
   CreateButton("CTRL_TP_Plus", col1, info_y, btn_width, btn_height, "TP +"+IntegerToString(TP_Adjust_Pips), clrWhite, clrSeaGreen);
   CreateButton("CTRL_TP_Minus", col2, info_y, btn_width, btn_height, "TP -"+IntegerToString(TP_Adjust_Pips), clrWhite, clrIndianRed);
   CreateButton("CTRL_SL_Plus", col3, info_y, btn_width, btn_height, "SL +"+IntegerToString(SL_Adjust_Pips), clrWhite, clrSteelBlue);
   info_y += row_height;

   // Row 4: More SL adjust
   CreateButton("CTRL_SL_Minus", col1, info_y, btn_width, btn_height, "SL -"+IntegerToString(SL_Adjust_Pips), clrWhite, clrSlateGray);
   info_y += row_height;

   // Separator
   CreateInfoLabel("CTRL_Sep2", x, info_y, "--- USEFUL ---", clrDimGray, 8);
   info_y += 18;

   // === USEFUL TIER (Middle) ===
   // Row 5: Partial management
   CreateButton("CTRL_CloseLosses", col1, info_y, btn_width, btn_height, "Close Losses", clrWhite, clrMaroon);
   CreateButton("CTRL_Partial50", col2, info_y, btn_width, btn_height, "Close 50%", clrBlack, clrGold);
   CreateButton("CTRL_Refresh", col3, info_y, btn_width, btn_height, "Refresh", clrWhite, clrDodgerBlue);
   info_y += row_height;

   // Row 6: Toggle panel
   CreateButton("CTRL_ToggleAvail", col1, info_y, btn_width * 2 + btn_spacing, btn_height, "Toggle Status Panel", clrWhite, clrDarkCyan);
   info_y += row_height;

   // Separator
   CreateInfoLabel("CTRL_Sep3", x, info_y, "--- ESSENTIAL ---", clrLime, 8);
   info_y += 18;

   // === ESSENTIAL TIER (Bottom) ===
   // Row 7: Quick closes
   CreateButton("CTRL_CloseProfits", col1, info_y, btn_width, btn_height, "Close Profits", clrBlack, clrLime);
   CreateButton("CTRL_BreakEven", col2, info_y, btn_width, btn_height, "Break-Even", clrBlack, clrYellow);
   CreateButton("CTRL_CloseSymbol", col3, info_y, btn_width, btn_height, "Close Symbol", clrWhite, clrOrangeRed);
   info_y += row_height;

   // Row 8: Critical controls
   CreateButton("CTRL_Pause", col1, info_y, btn_width * 2 + btn_spacing, btn_height, "PAUSE TRADING", clrWhite, clrDarkOrange);
   CreateButton("CTRL_CloseAll", col3, info_y, btn_width, btn_height, "CLOSE ALL", clrWhite, clrRed);

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Create panel background                                           |
//+------------------------------------------------------------------+
void CreatePanelBackground(string name, int x, int y, int width, int height)
{
   ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, C'25,25,35');
   ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_COLOR, C'60,60,80');
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
}

//+------------------------------------------------------------------+
//| Create info label                                                 |
//+------------------------------------------------------------------+
void CreateInfoLabel(string name, int x, int y, string text, color clr, int font_size)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, font_size);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| Create button                                                     |
//+------------------------------------------------------------------+
void CreateButton(string name, int x, int y, int width, int height, string text, color txt_clr, color bg_clr)
{
   ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE, width);
   ObjectSetInteger(0, name, OBJPROP_YSIZE, height);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, name, OBJPROP_COLOR, txt_clr);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg_clr);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, clrGray);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_STATE, false);
}

//+------------------------------------------------------------------+
//| Update P&L tracking                                               |
//+------------------------------------------------------------------+
void UpdatePnLTracking()
{
   // Check for new day
   datetime today = TimeCurrent() / 86400;
   if(today != g_last_day)
   {
      g_day_start_equity = AccountEquity();
      g_last_day = today;
   }

   // Update peak equity for drawdown
   double current_equity = AccountEquity();
   if(current_equity > g_peak_equity)
      g_peak_equity = current_equity;
}

//+------------------------------------------------------------------+
//| Update control panel info displays                                |
//+------------------------------------------------------------------+
void UpdateControlPanelInfo()
{
   // Daily P&L
   double daily_pnl = AccountEquity() - g_day_start_equity;
   string pnl_text = (daily_pnl >= 0 ? "+" : "") + DoubleToString(daily_pnl, 2);
   color pnl_color = daily_pnl >= 0 ? clrLime : clrRed;
   ObjectSetString(0, "CTRL_PnL_Value", OBJPROP_TEXT, "$" + pnl_text);
   ObjectSetInteger(0, "CTRL_PnL_Value", OBJPROP_COLOR, pnl_color);

   // Drawdown
   double drawdown = 0;
   if(g_peak_equity > 0)
      drawdown = (g_peak_equity - AccountEquity()) / g_peak_equity * 100;
   color dd_color = drawdown < 5 ? clrLime : (drawdown < 10 ? clrYellow : clrRed);
   ObjectSetString(0, "CTRL_DD_Value", OBJPROP_TEXT, DoubleToString(drawdown, 2) + "%");
   ObjectSetInteger(0, "CTRL_DD_Value", OBJPROP_COLOR, dd_color);

   // Session
   string session_text = GetSessionName();
   ObjectSetString(0, "CTRL_Session_Value", OBJPROP_TEXT, session_text);

   // Spread
   double spread = MarketInfo(Symbol(), MODE_SPREAD) / 10.0;
   color spread_color = spread < 2 ? clrLime : (spread < 5 ? clrYellow : clrRed);
   ObjectSetString(0, "CTRL_Spread_Value", OBJPROP_TEXT, DoubleToString(spread, 1) + " pips");
   ObjectSetInteger(0, "CTRL_Spread_Value", OBJPROP_COLOR, spread_color);

   // Update pause button state
   if(g_trading_paused)
   {
      ObjectSetString(0, "CTRL_Pause", OBJPROP_TEXT, "RESUME TRADING");
      ObjectSetInteger(0, "CTRL_Pause", OBJPROP_BGCOLOR, clrGreen);
   }
   else
   {
      ObjectSetString(0, "CTRL_Pause", OBJPROP_TEXT, "PAUSE TRADING");
      ObjectSetInteger(0, "CTRL_Pause", OBJPROP_BGCOLOR, clrDarkOrange);
   }

   // Update trailing button state
   if(g_trailing_enabled)
   {
      ObjectSetString(0, "CTRL_Trailing", OBJPROP_TEXT, "Trail: ON");
      ObjectSetInteger(0, "CTRL_Trailing", OBJPROP_BGCOLOR, clrLime);
      ObjectSetInteger(0, "CTRL_Trailing", OBJPROP_COLOR, clrBlack);
   }
   else
   {
      ObjectSetString(0, "CTRL_Trailing", OBJPROP_TEXT, "Trail: OFF");
      ObjectSetInteger(0, "CTRL_Trailing", OBJPROP_BGCOLOR, clrGray);
      ObjectSetInteger(0, "CTRL_Trailing", OBJPROP_COLOR, clrWhite);
   }
}

//+------------------------------------------------------------------+
//| Get current session name                                          |
//+------------------------------------------------------------------+
string GetSessionName()
{
   int hour = TimeHour(TimeCurrent()) - (int)BrokerGMT;
   if(hour < 0) hour += 24;
   if(hour >= 24) hour -= 24;

   if(hour >= 0 && hour < 8) return "Tokyo";
   if(hour >= 8 && hour < 12) return "London";
   if(hour >= 12 && hour < 17) return "NY/London";
   if(hour >= 17 && hour < 22) return "New York";
   return "Sydney";
}

//+------------------------------------------------------------------+
//| Chart event handler for button clicks                             |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id != CHARTEVENT_OBJECT_CLICK) return;

   // Reset button state
   ObjectSetInteger(0, sparam, OBJPROP_STATE, false);

   // === ESSENTIAL TIER ===
   if(sparam == "CTRL_CloseAll")
   {
      CloseAllPositions();
   }
   else if(sparam == "CTRL_Pause")
   {
      ToggleTradingPause();
   }
   else if(sparam == "CTRL_CloseProfits")
   {
      CloseProfitablePositions();
   }
   else if(sparam == "CTRL_BreakEven")
   {
      MoveAllToBreakeven();
   }
   else if(sparam == "CTRL_CloseSymbol")
   {
      CloseSymbolPositions();
   }
   // === USEFUL TIER ===
   else if(sparam == "CTRL_CloseLosses")
   {
      CloseLosingPositions();
   }
   else if(sparam == "CTRL_Partial50")
   {
      PartialCloseAll(50);
   }
   else if(sparam == "CTRL_Refresh")
   {
      RefreshAvailability();
      Print("STATUS: Availability refreshed");
   }
   else if(sparam == "CTRL_ToggleAvail")
   {
      ToggleAvailabilityPanel();
   }
   // === ADVANCED TIER ===
   else if(sparam == "CTRL_BuyManual")
   {
      OpenManualTrade(OP_BUY);
   }
   else if(sparam == "CTRL_SellManual")
   {
      OpenManualTrade(OP_SELL);
   }
   else if(sparam == "CTRL_ScaleIn")
   {
      ScaleIntoPosition();
   }
   else if(sparam == "CTRL_Hedge")
   {
      HedgePositions();
   }
   else if(sparam == "CTRL_Reverse")
   {
      ReversePositions();
   }
   else if(sparam == "CTRL_Trailing")
   {
      ToggleTrailing();
   }
   else if(sparam == "CTRL_TP_Plus")
   {
      AdjustAllTP(TP_Adjust_Pips);
   }
   else if(sparam == "CTRL_TP_Minus")
   {
      AdjustAllTP(-TP_Adjust_Pips);
   }
   else if(sparam == "CTRL_SL_Plus")
   {
      AdjustAllSL(SL_Adjust_Pips);
   }
   else if(sparam == "CTRL_SL_Minus")
   {
      AdjustAllSL(-SL_Adjust_Pips);
   }

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| ESSENTIAL: Close all positions                                    |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   int closed = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      double price = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), price, 10, clrYellow))
         closed++;
   }
   Print("CLOSE ALL: Closed ", closed, " positions");
   Alert("Closed ALL ", closed, " positions");
}

//+------------------------------------------------------------------+
//| ESSENTIAL: Toggle trading pause                                   |
//+------------------------------------------------------------------+
void ToggleTradingPause()
{
   g_trading_paused = !g_trading_paused;
   if(g_trading_paused)
   {
      Print("TRADING PAUSED by user");
      Alert("Trading PAUSED - No new trades will be opened");
   }
   else
   {
      Print("TRADING RESUMED by user");
      Alert("Trading RESUMED - EA will trade normally");
   }
}

//+------------------------------------------------------------------+
//| ESSENTIAL: Close profitable positions                             |
//+------------------------------------------------------------------+
void CloseProfitablePositions()
{
   int closed = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;
      if(OrderProfit() <= 0) continue;

      double price = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), price, 10, clrLime))
         closed++;
   }
   Print("CLOSE PROFITS: Closed ", closed, " profitable positions");
}

//+------------------------------------------------------------------+
//| ESSENTIAL: Move all to breakeven                                  |
//+------------------------------------------------------------------+
void MoveAllToBreakeven()
{
   int modified = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      double entry = OrderOpenPrice();
      double sl = OrderStopLoss();
      double tp = OrderTakeProfit();
      bool is_buy = (OrderType() == OP_BUY);
      double price = is_buy ? Bid : Ask;

      // Only move to breakeven if in profit
      double profit_dist = is_buy ? (price - entry) : (entry - price);
      if(profit_dist <= 0) continue;

      // Set SL slightly above/below entry
      double new_sl = entry + (is_buy ? 1 : -1) * Point * 5;

      // Only if it improves the SL
      if((is_buy && new_sl > sl) || (!is_buy && new_sl < sl))
      {
         if(OrderModify(OrderTicket(), entry, new_sl, tp, 0, clrBlue))
            modified++;
      }
   }
   Print("BREAKEVEN: Modified ", modified, " positions");
}

//+------------------------------------------------------------------+
//| ESSENTIAL: Close positions for current symbol only                |
//+------------------------------------------------------------------+
void CloseSymbolPositions()
{
   int closed = 0;
   string sym = Symbol();
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderSymbol() != sym) continue;
      if(OrderType() > OP_SELL) continue;

      double price = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), price, 10, clrOrange))
         closed++;
   }
   Print("CLOSE SYMBOL: Closed ", closed, " positions on ", sym);
}

//+------------------------------------------------------------------+
//| USEFUL: Close losing positions                                    |
//+------------------------------------------------------------------+
void CloseLosingPositions()
{
   int closed = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;
      if(OrderProfit() >= 0) continue;

      double price = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), price, 10, clrRed))
         closed++;
   }
   Print("CLOSE LOSSES: Closed ", closed, " losing positions");
}

//+------------------------------------------------------------------+
//| USEFUL: Partial close all positions                               |
//+------------------------------------------------------------------+
void PartialCloseAll(int percent)
{
   int closed = 0;
   double min_lot = MarketInfo(Symbol(), MODE_MINLOT);

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      double close_lots = NormalizeDouble(OrderLots() * percent / 100.0, 2);
      if(close_lots < min_lot) continue;

      double price = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), close_lots, price, 10, clrGold))
         closed++;
   }
   Print("PARTIAL CLOSE: Closed ", percent, "% of ", closed, " positions");
}

//+------------------------------------------------------------------+
//| USEFUL: Toggle availability panel                                 |
//+------------------------------------------------------------------+
void ToggleAvailabilityPanel()
{
   // Check if panel exists
   if(ObjectFind(0, "AVAIL_Background") >= 0)
   {
      ObjectsDeleteAll(0, "AVAIL_");
      Print("STATUS: Availability panel hidden");
   }
   else
   {
      CreateAvailabilityPanel();
      Print("STATUS: Availability panel shown");
   }
}

//+------------------------------------------------------------------+
//| ADVANCED: Open manual trade                                       |
//+------------------------------------------------------------------+
void OpenManualTrade(int order_type)
{
   double lot = g_min_lot;
   double price = (order_type == OP_BUY) ? Ask : Bid;

   // Calculate SL/TP based on ATR
   double atr = iATR(Symbol(), Timeframe, 14, 1);
   double sl_dist = atr * g_sl_atr;
   double tp_dist = sl_dist * g_tp_rr;

   double sl, tp;
   if(order_type == OP_BUY)
   {
      sl = price - sl_dist;
      tp = price + tp_dist;
   }
   else
   {
      sl = price + sl_dist;
      tp = price - tp_dist;
   }

   string comment = "Manual_" + (order_type == OP_BUY ? "Buy" : "Sell");
   int ticket = OrderSend(Symbol(), order_type, lot, price, 10, sl, tp, comment, MagicNumber, 0,
                          order_type == OP_BUY ? clrGreen : clrRed);

   if(ticket > 0)
      Print("MANUAL: Opened ", (order_type == OP_BUY ? "BUY" : "SELL"), " #", ticket);
   else
      Print("MANUAL: Failed to open trade, error ", GetLastError());
}

//+------------------------------------------------------------------+
//| ADVANCED: Scale into existing position                            |
//+------------------------------------------------------------------+
void ScaleIntoPosition()
{
   // Find existing position on current symbol
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderType() > OP_SELL) continue;

      int order_type = OrderType();
      double base_lot = OrderLots();
      double scale_lot = NormalizeDouble(base_lot * ScaleInMultiplier, 2);
      double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
      if(scale_lot < min_lot) scale_lot = min_lot;

      double price = (order_type == OP_BUY) ? Ask : Bid;
      double sl = OrderStopLoss();
      double tp = OrderTakeProfit();

      string comment = "ScaleIn_" + IntegerToString(OrderTicket());
      int ticket = OrderSend(Symbol(), order_type, scale_lot, price, 10, sl, tp, comment, MagicNumber, 0, clrAqua);

      if(ticket > 0)
         Print("SCALE IN: Added ", scale_lot, " lots to position");
      else
         Print("SCALE IN: Failed, error ", GetLastError());

      return;  // Only scale into first found position
   }
   Print("SCALE IN: No existing position found on ", Symbol());
}

//+------------------------------------------------------------------+
//| ADVANCED: Hedge current positions                                 |
//+------------------------------------------------------------------+
void HedgePositions()
{
   double buy_lots = 0, sell_lots = 0;

   // Calculate net exposure on current symbol
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderType() > OP_SELL) continue;

      if(OrderType() == OP_BUY)
         buy_lots += OrderLots();
      else
         sell_lots += OrderLots();
   }

   double net = buy_lots - sell_lots;
   if(MathAbs(net) < MarketInfo(Symbol(), MODE_MINLOT))
   {
      Print("HEDGE: Position already hedged or no position");
      return;
   }

   // Open opposite position to hedge
   int order_type = (net > 0) ? OP_SELL : OP_BUY;
   double hedge_lots = MathAbs(net);
   double price = (order_type == OP_BUY) ? Ask : Bid;

   string comment = "Hedge_" + Symbol();
   int ticket = OrderSend(Symbol(), order_type, hedge_lots, price, 10, 0, 0, comment, MagicNumber, 0, clrOrange);

   if(ticket > 0)
      Print("HEDGE: Opened ", (order_type == OP_BUY ? "BUY" : "SELL"), " ", hedge_lots, " lots to hedge");
   else
      Print("HEDGE: Failed, error ", GetLastError());
}

//+------------------------------------------------------------------+
//| ADVANCED: Reverse all positions                                   |
//+------------------------------------------------------------------+
void ReversePositions()
{
   double buy_lots = 0, sell_lots = 0;

   // Calculate current exposure
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderType() > OP_SELL) continue;

      if(OrderType() == OP_BUY)
         buy_lots += OrderLots();
      else
         sell_lots += OrderLots();
   }

   // Close all positions on this symbol first
   CloseSymbolPositions();

   // Open opposite position
   double net = buy_lots - sell_lots;
   if(MathAbs(net) < MarketInfo(Symbol(), MODE_MINLOT))
   {
      Print("REVERSE: No net position to reverse");
      return;
   }

   int order_type = (net > 0) ? OP_SELL : OP_BUY;  // Reverse direction
   double lots = MathAbs(net);
   double price = (order_type == OP_BUY) ? Ask : Bid;

   // Calculate SL/TP based on ATR
   double atr = iATR(Symbol(), Timeframe, 14, 1);
   double sl_dist = atr * g_sl_atr;
   double tp_dist = sl_dist * g_tp_rr;

   double sl, tp;
   if(order_type == OP_BUY)
   {
      sl = price - sl_dist;
      tp = price + tp_dist;
   }
   else
   {
      sl = price + sl_dist;
      tp = price - tp_dist;
   }

   string comment = "Reverse_" + Symbol();
   int ticket = OrderSend(Symbol(), order_type, lots, price, 10, sl, tp, comment, MagicNumber, 0, clrMagenta);

   if(ticket > 0)
      Print("REVERSE: Opened ", (order_type == OP_BUY ? "BUY" : "SELL"), " ", lots, " lots (reversed)");
   else
      Print("REVERSE: Failed, error ", GetLastError());
}

//+------------------------------------------------------------------+
//| ADVANCED: Toggle trailing stop                                    |
//+------------------------------------------------------------------+
void ToggleTrailing()
{
   g_trailing_enabled = !g_trailing_enabled;
   Print("TRAILING: ", g_trailing_enabled ? "ENABLED" : "DISABLED");
}

//+------------------------------------------------------------------+
//| ADVANCED: Adjust all TPs by pips                                  |
//+------------------------------------------------------------------+
void AdjustAllTP(int pips)
{
   int modified = 0;
   double pip_value = Point * 10;  // For 5-digit brokers

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      double tp = OrderTakeProfit();
      if(tp == 0) continue;  // No TP set

      double new_tp;
      if(OrderType() == OP_BUY)
         new_tp = tp + pips * pip_value;
      else
         new_tp = tp - pips * pip_value;

      if(OrderModify(OrderTicket(), OrderOpenPrice(), OrderStopLoss(), new_tp, 0, clrAqua))
         modified++;
   }
   Print("TP ADJUST: Modified ", modified, " positions by ", pips, " pips");
}

//+------------------------------------------------------------------+
//| ADVANCED: Adjust all SLs by pips                                  |
//+------------------------------------------------------------------+
void AdjustAllSL(int pips)
{
   int modified = 0;
   double pip_value = Point * 10;  // For 5-digit brokers

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      double sl = OrderStopLoss();
      if(sl == 0) continue;  // No SL set

      double new_sl;
      if(OrderType() == OP_BUY)
         new_sl = sl + pips * pip_value;  // Positive = tighter for buys
      else
         new_sl = sl - pips * pip_value;  // Positive = tighter for sells

      if(OrderModify(OrderTicket(), OrderOpenPrice(), new_sl, OrderTakeProfit(), 0, clrYellow))
         modified++;
   }
   Print("SL ADJUST: Modified ", modified, " positions by ", pips, " pips");
}

//+------------------------------------------------------------------+
