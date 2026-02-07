//+------------------------------------------------------------------+
//|                        InstitutionalTradingRobot_v4_MQL4.mq4     |
//|                    PROPERLY CALIBRATED AGGRESSION LEVELS         |
//|                         MQL4 - Strategy Tester Ready             |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.30"
#property description "MQL4 Robot - Proper Calibration - Pattern-Driven Trading"
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

//+------------------------------------------------------------------+
//| INIT                                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════════");
   Print("  INSTITUTIONAL TRADING ROBOT v4.30 MQL4");
   Print("  PATTERN-DRIVEN TRADING - PROPER CALIBRATION");
   Print("═══════════════════════════════════════════════════════════════");

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
   Print("═══════════════════════════════════════════════════════════════");
   Print("  AGGRESSION LEVEL: ", AggressionLevel);
   Print("  → Min Pattern Strength: ", g_min_pattern_strength, " stars");
   Print("  → Min Confluence: ", g_min_confluence, " factors");
   Print("  → MTF Required: ", g_require_mtf ? "YES" : "NO");
   Print("  → Volume Required: ", g_require_volume ? "YES" : "NO");
   Print("  → Counter-Trend: ", g_allow_counter_trend ? "ALLOWED" : "BLOCKED");
   Print("═══════════════════════════════════════════════════════════════");
   Print("  Stop Loss: ", SL_Mode == SL_MODE_ATR ? DoubleToString(g_sl_atr, 1) + "x ATR" : DoubleToString(g_sl_pips, 0) + " pips");
   Print("  Take Profit: ", DoubleToString(g_tp_rr, 1), " R:R");
   Print("  Risk: ", DoubleToString(g_risk * 100, 2), "%");
   Print("═══════════════════════════════════════════════════════════════");

   if(!EnableTrading)
      Print("*** WARNING: TRADING DISABLED ***");
   else
      Print("*** TRADING ENABLED ***");

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "IGTR_");
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

      case 5:  // Level 5: Trade on ANY valid pattern
         g_min_pattern_strength = 2;    // Still need real patterns (2-5 stars)
         g_min_confluence = 1;          // Just need 1 factor (the pattern itself)
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
   // Manage existing trades first
   ManageTrades();

   // New bar check - only analyze on new bars
   static datetime last_bar = 0;
   datetime cur_bar = iTime(Symbol(), Timeframe, 0);
   if(cur_bar == last_bar) return;
   last_bar = cur_bar;

   // Pre-flight checks
   if(!EnableTrading) return;
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
   Print("═══════════════════════════════════════════════════════════════");
   Print("  SIGNAL: ", g_pattern.name, " [", g_pattern.strength, "★]");
   Print("  Direction: ", g_pattern.is_bull ? "BUY" : "SELL");
   Print("  Confluence: ", confluence, "/", g_min_confluence, " (Level ", AggressionLevel, ")");
   Print("═══════════════════════════════════════════════════════════════");

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

   // DOJI - Indecision, direction from context
   if(body_ratio < 0.1 && range1 > atr * 0.3)
   {
      bool is_bull = (g_regime == TREND_DOWN);  // Doji in downtrend = potential reversal up
      SetPattern("DOJI", is_bull, 2, c1, is_bull ? l1 - atr * 0.3 : h1 + atr * 0.3);
      return;
   }

   // SPINNING TOP - Indecision with longer wicks
   if(body_ratio < 0.35 && uw1 > body1 * 0.8 && lw1 > body1 * 0.8 && body1 > 0)
   {
      bool is_bull = (g_regime == TREND_DOWN);
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
   double ema = iMA(Symbol(), htf, 50, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), htf, 0);

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
      if(UseTrailingStop && r_multiple >= 1.5)
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
