//+------------------------------------------------------------------+
//|                        InstitutionalTradingRobot_v4_MQL4.mq4     |
//|                    TRADING-ONLY - ALL DROPDOWN INPUTS            |
//|                         MQL4 - Strategy Tester Ready             |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.20"
#property description "MQL4 Robot - All Dropdowns - Chart Display - Fixed Aggression"
#property strict

//+------------------------------------------------------------------+
//| DROPDOWN ENUMS                                                    |
//+------------------------------------------------------------------+
enum ENUM_AGGRESSION
{
   AGG_1 = 1,  // Level 1 - Ultra Conservative
   AGG_2 = 2,  // Level 2 - Conservative
   AGG_3 = 3,  // Level 3 - Balanced
   AGG_4 = 4,  // Level 4 - Aggressive
   AGG_5 = 5   // Level 5 - MAXIMUM
};

enum ENUM_SIZING
{
   SIZE_FIXED,    // Fixed Lot Range
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
   MT_8 = 8,    // 8
   MT_10 = 10,  // 10
   MT_15 = 15,  // 15
   MT_20 = 20   // 20
};

enum ENUM_LOSS_LIM
{
   LL_1 = 10,   // 1%
   LL_2 = 20,   // 2%
   LL_3 = 30,   // 3%
   LL_5 = 50,   // 5%
   LL_10 = 100  // 10%
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
   SPD_100 = 100  // 100% ATR
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
   BR_5 = 5    // 5 Bars
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
input ENUM_AGGRESSION  AggressionLevel = AGG_5;                 // Aggression Level
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
input ENUM_MAX_TRADES  MaxTrades = MT_10;                       // Max Total Trades
input ENUM_MAX_TRADES  MaxPerSymbol = MT_3;                     // Max Per Symbol
input ENUM_LOSS_LIM    DailyLoss = LL_5;                        // Daily Loss Limit
input ENUM_LOSS_LIM    WeeklyLoss = LL_10;                      // Weekly Loss Limit

input string           _5 = "═══════ TARGETS ═══════";
input ENUM_RR          TP1 = RR_20;                             // Take Profit 1
input ENUM_RR          TP2 = RR_30;                             // Take Profit 2
input ENUM_RR          TP3 = RR_50;                             // Take Profit 3

input string           _6 = "═══════ FILTERS ═══════";
input bool             UseVolumeFilter = true;                  // Volume Filter
input ENUM_VOL         VolumeThreshold = VOL_12;                // Volume Threshold
input bool             UseSpreadFilter = true;                  // Spread Filter
input ENUM_SPREAD      SpreadLimit = SPD_50;                    // Spread Limit
input bool             UseMTF = true;                           // MTF Confirmation
input bool             UseCorrelation = true;                   // Correlation Filter
input ENUM_CORR        CorrLimit = CORR_07;                     // Correlation Limit

input string           _7 = "═══════ SESSION ═══════";
input bool             UseSessionFilter = true;                 // Session Filter
input ENUM_GMT         BrokerGMT = GMT_P2;                      // Broker GMT Offset
input bool             TradeAsian = true;                       // Trade Asian
input bool             TradeLondon = true;                      // Trade London
input bool             TradeNY = true;                          // Trade NY

input string           _8 = "═══════ ADVANCED ═══════";
input bool             UseRegimeStrategy = true;                // Regime Strategy
input bool             UseVolatilityAdapt = true;               // Volatility Adapt
input bool             UseDynamicRisk = true;                   // Dynamic Risk
input bool             UsePatternDecay = true;                  // Pattern Decay
input ENUM_BARS        PatternExpiry = BR_3;                    // Pattern Expiry
input bool             UseLiquiditySweep = true;                // Liquidity Sweep
input bool             UseRetailTrap = true;                    // Retail Trap
input bool             UseMarketStructure = true;               // Market Structure

input string           _9 = "═══════ PROFIT LOCK ═══════";
input bool             UseProfitLock = true;                    // Per-Trade Lock
input ENUM_LOCK_R      LockTriggerR = LR_15;                    // Lock at R
input ENUM_PROFIT      LockFixedAmt = PR_100;                   // Lock at $
input ENUM_PCT         LockPct = PC_50;                         // Lock %
input bool             UsePartialClose = false;                 // Partial Close
input ENUM_PCT         PartialPct = PC_50;                      // Partial %

input string           _10 = "═══════ ACCOUNT LOCK ═══════";
input bool             UseAccountLock = true;                   // Account Lock
input ENUM_PROFIT      AcctLockAmt = PR_1000;                   // Lock at $
input ENUM_ACCT_PCT    AcctLockPct = AP_5;                      // Lock at %

input string           _11 = "═══════ DISPLAY ═══════";
input bool             ShowTradeReasons = true;                 // Show Trade Reasons
input bool             ShowPatternHistory = true;               // Show Pattern History
input bool             ShowAggressionInfo = true;               // Show Aggression Info

input string           _12 = "═══════ ALERTS ═══════";
input bool             AlertPopup = false;                      // Popup Alerts
input bool             AlertMobile = false;                     // Mobile Alerts

//+------------------------------------------------------------------+
//| INTERNAL TYPES                                                    |
//+------------------------------------------------------------------+
enum REGIME { TREND, RANGE, TRANSITION };
enum BIAS { BULL, BEAR, NEUTRAL };
enum SESSION { ASIAN, LONDON, OVERLAP, NEWYORK, CLOSED };

struct AggressionPreset
{
   int    confluence;
   double risk_mult;
   int    min_strength;
   bool   need_mtf;
   bool   need_vol;
   int    max_trades;
};

struct Pattern
{
   string   name;
   bool     is_bull;
   int      strength;
   double   price;
   datetime time;
};

struct TradeReason
{
   datetime time;
   string   symbol;
   string   direction;
   string   pattern;
   int      confluence;
   string   reasons;
};

struct PatternHistory
{
   datetime time;
   string   name;
   bool     is_bull;
   int      strength;
};

//+------------------------------------------------------------------+
//| GLOBALS                                                           |
//+------------------------------------------------------------------+
// Converted input values
double g_risk, g_min_lot, g_max_lot, g_sl_atr, g_sl_pips, g_tp1, g_tp2, g_tp3;
double g_vol_thresh, g_spread_lim, g_corr_lim;
double g_lock_r, g_lock_amt, g_lock_pct, g_partial_pct;
double g_daily_lim, g_weekly_lim, g_acct_lock_amt, g_acct_lock_pct;
int    g_max_trades, g_max_per_sym, g_pattern_expiry;

// Aggression presets
AggressionPreset g_presets[5];
AggressionPreset g_agg;

// Market state
REGIME  g_regime = TREND;
BIAS    g_bias = NEUTRAL;
SESSION g_session = ASIAN;
Pattern g_pattern;
bool    g_has_pattern = false;

// Tracking
double g_daily_start, g_weekly_start, g_peak_bal;
int    g_consec_loss = 0, g_consec_win = 0;

// Dynamic values
int    g_dyn_confluence = 3;
double g_dyn_risk = 0.5;
double g_dyn_tp = 2.0;

// Flags
bool g_mtf_ok = false;
bool g_corr_ok = true;
bool g_vol_ok = false;
bool g_spread_ok = true;
bool g_session_ok = true;

// Trade reason history (last 10)
TradeReason g_trade_reasons[10];
int g_trade_reason_count = 0;

// Pattern history (last 5)
PatternHistory g_pattern_history[5];
int g_pattern_history_count = 0;

// Current trade conditions for display
string g_current_conditions = "";

//+------------------------------------------------------------------+
//| INIT                                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════");
   Print("  INSTITUTIONAL TRADING ROBOT v4.20 MQL4");
   Print("  ALL DROPDOWN INPUTS - CHART DISPLAY - FIXED AGGRESSION");
   Print("═══════════════════════════════════════════════════════════");

   // Convert enum inputs to usable values
   g_risk = (double)RiskPercent / 100.0;
   g_min_lot = (double)MinLot / 100.0;
   g_max_lot = (double)MaxLot / 100.0;
   g_sl_atr = (double)SL_ATR_Mult / 10.0;
   g_sl_pips = (double)SL_Fixed_Pips;
   g_tp1 = (double)TP1 / 10.0;
   g_tp2 = (double)TP2 / 10.0;
   g_tp3 = (double)TP3 / 10.0;
   g_vol_thresh = (double)VolumeThreshold / 10.0;
   g_spread_lim = (double)SpreadLimit / 100.0;
   g_corr_lim = (double)CorrLimit / 10.0;
   g_lock_r = (double)LockTriggerR / 10.0;
   g_lock_amt = (double)LockFixedAmt;
   g_lock_pct = (double)LockPct;
   g_partial_pct = (double)PartialPct;
   g_daily_lim = (double)DailyLoss / 10.0;
   g_weekly_lim = (double)WeeklyLoss / 10.0;
   g_acct_lock_amt = (double)AcctLockAmt;
   g_acct_lock_pct = (double)AcctLockPct / 10.0;
   g_max_trades = (int)MaxTrades;
   g_max_per_sym = (int)MaxPerSymbol;
   g_pattern_expiry = (int)PatternExpiry;

   // Init presets
   InitPresets();
   ApplyAggression();

   // Init tracking
   g_daily_start = AccountBalance();
   g_weekly_start = AccountBalance();
   g_peak_bal = AccountBalance();

   // Show config
   double bmin = MarketInfo(Symbol(), MODE_MINLOT);
   double bmax = MarketInfo(Symbol(), MODE_MAXLOT);
   Print("Symbol: ", Symbol(), " MinLot: ", bmin, " MaxLot: ", bmax);
   Print("═══ AGGRESSION LEVEL ", AggressionLevel, " ═══");
   Print("  Confluence Required: ", g_agg.confluence);
   Print("  Min Pattern Strength: ", g_agg.min_strength);
   Print("  MTF Required: ", g_agg.need_mtf ? "YES" : "NO");
   Print("  Volume Required: ", g_agg.need_vol ? "YES" : "NO");
   Print("  Risk Multiplier: ", g_agg.risk_mult, "x");
   Print("  Max Trades: ", g_agg.max_trades);
   Print("═══════════════════════════════════════");

   if(SL_Mode == SL_MODE_ATR)
      Print("Stop Loss: ", g_sl_atr, "x ATR");
   else
      Print("Stop Loss: ", g_sl_pips, " pips (fixed)");

   Print("TP1: ", g_tp1, "R | TP2: ", g_tp2, "R | TP3: ", g_tp3, "R");

   if(!EnableTrading)
      Print("*** WARNING: TRADING DISABLED ***");
   else
      Print("*** TRADING ENABLED - READY ***");

   // Create chart objects
   CreateChartDisplay();

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   // Clean up chart objects
   ObjectsDeleteAll(0, "IGTR_");
   Print("EA Stopped");
}

//+------------------------------------------------------------------+
//| PRESETS - AGGRESSION LEVELS                                       |
//+------------------------------------------------------------------+
void InitPresets()
{
   // Level 1 - Ultra Conservative: Needs everything perfect
   g_presets[0].confluence = 6;      // Need 6 out of 10 confluence points
   g_presets[0].risk_mult = 0.5;     // Half risk
   g_presets[0].min_strength = 4;    // Only strong patterns (4-5 stars)
   g_presets[0].need_mtf = true;     // MUST have MTF alignment
   g_presets[0].need_vol = true;     // MUST have volume confirmation
   g_presets[0].max_trades = 1;      // Only 1 trade at a time

   // Level 2 - Conservative
   g_presets[1].confluence = 5;
   g_presets[1].risk_mult = 0.75;
   g_presets[1].min_strength = 3;
   g_presets[1].need_mtf = true;
   g_presets[1].need_vol = true;
   g_presets[1].max_trades = 2;

   // Level 3 - Balanced
   g_presets[2].confluence = 4;
   g_presets[2].risk_mult = 1.0;
   g_presets[2].min_strength = 2;
   g_presets[2].need_mtf = true;
   g_presets[2].need_vol = false;    // Volume not required
   g_presets[2].max_trades = 3;

   // Level 4 - Aggressive
   g_presets[3].confluence = 3;
   g_presets[3].risk_mult = 1.25;
   g_presets[3].min_strength = 2;
   g_presets[3].need_mtf = false;    // MTF not required
   g_presets[3].need_vol = false;
   g_presets[3].max_trades = 5;

   // Level 5 - MAXIMUM: Trade almost any setup
   g_presets[4].confluence = 2;      // Only need 2 confluence points
   g_presets[4].risk_mult = 1.5;     // 1.5x risk
   g_presets[4].min_strength = 1;    // Accept ANY pattern (even 1 star)
   g_presets[4].need_mtf = false;    // MTF not required
   g_presets[4].need_vol = false;    // Volume not required
   g_presets[4].max_trades = 10;     // Up to 10 trades
}

void ApplyAggression()
{
   int lv = MathMax(1, MathMin(5, (int)AggressionLevel));
   g_agg = g_presets[lv - 1];
   g_dyn_confluence = g_agg.confluence;
   g_dyn_risk = g_risk * g_agg.risk_mult;
   g_dyn_tp = g_tp1;

   Print("═══ AGGRESSION APPLIED: LEVEL ", lv, " ═══");
   Print("  → Confluence threshold: ", g_agg.confluence, " (lower = more trades)");
   Print("  → Pattern strength min: ", g_agg.min_strength, " (lower = more patterns accepted)");
   Print("  → Effective risk: ", DoubleToString(g_dyn_risk * 100, 2), "%");
}

//+------------------------------------------------------------------+
//| TICK                                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Account lock check
   if(UseAccountLock) CheckAccountLock();

   // Manage existing trades
   ManageTrades();

   // Update chart display every tick
   UpdateChartDisplay();

   // New bar check
   static datetime last_bar = 0;
   datetime cur_bar = iTime(Symbol(), Timeframe, 0);
   if(cur_bar == last_bar) return;
   last_bar = cur_bar;

   // Reset conditions string for this bar
   g_current_conditions = "";

   // Pre-flight checks
   if(!EnableTrading)
   {
      g_current_conditions = "TRADING DISABLED";
      return;
   }

   // Spread check
   if(UseSpreadFilter)
   {
      CheckSpread();
      if(!g_spread_ok)
      {
         g_current_conditions = "Spread too wide";
         return;
      }
   }

   // Session check
   if(UseSessionFilter)
   {
      CheckSession();
      if(!g_session_ok)
      {
         g_current_conditions = "Session closed";
         return;
      }
   }

   // Market analysis
   DetectRegime();
   DetectBias();

   // Pattern detection - scan ALL patterns
   ScanPatterns();

   if(!g_has_pattern)
   {
      g_current_conditions = "No pattern detected";
      return;
   }

   // Add pattern to history
   AddPatternToHistory(g_pattern.name, g_pattern.is_bull, g_pattern.strength);

   // Pattern strength gate - CONTROLLED BY AGGRESSION
   if(g_pattern.strength < g_agg.min_strength)
   {
      g_current_conditions = "Pattern " + g_pattern.name + " strength " +
                            IntegerToString(g_pattern.strength) + " < required " +
                            IntegerToString(g_agg.min_strength) + " (Level " +
                            IntegerToString((int)AggressionLevel) + ")";
      Print(g_current_conditions);
      g_has_pattern = false;
      return;
   }

   // Regime strategy
   if(UseRegimeStrategy) ApplyRegimeStrategy();
   if(!g_has_pattern)
   {
      g_current_conditions = "Regime strategy rejected trade";
      return;
   }

   // Pattern decay
   if(UsePatternDecay)
   {
      int bars = iBarShift(Symbol(), Timeframe, g_pattern.time, false);
      if(bars > g_pattern_expiry)
      {
         g_current_conditions = "Pattern expired (" + IntegerToString(bars) + " bars old)";
         g_has_pattern = false;
         return;
      }
   }

   // Build conditions string
   string conditions = "";
   conditions += "Pattern: " + g_pattern.name + " [" + IntegerToString(g_pattern.strength) + "*] ";
   conditions += (g_pattern.is_bull ? "BUY" : "SELL") + " | ";
   conditions += "Regime: " + (g_regime == TREND ? "TREND" : (g_regime == RANGE ? "RANGE" : "TRANS")) + " | ";
   conditions += "Bias: " + (g_bias == BULL ? "BULL" : (g_bias == BEAR ? "BEAR" : "NEUTRAL")) + " | ";

   Print("PATTERN: ", g_pattern.name, " [", g_pattern.strength, "*] ", g_pattern.is_bull ? "BUY" : "SELL");

   // Filter checks - CONTROLLED BY AGGRESSION
   if(UseVolumeFilter)
   {
      CheckVolume();
      conditions += "Vol:" + (g_vol_ok ? "OK" : "LOW") + " ";

      // Only block if aggression level REQUIRES volume
      if(!g_vol_ok && g_agg.need_vol)
      {
         g_current_conditions = "Volume too low (required at Level " + IntegerToString((int)AggressionLevel) + ")";
         Print(g_current_conditions);
         g_has_pattern = false;
         return;
      }
   }

   if(UseMTF)
   {
      g_mtf_ok = CheckMTF();
      conditions += "MTF:" + (g_mtf_ok ? "OK" : "NO") + " ";

      // Only block if aggression level REQUIRES MTF
      if(!g_mtf_ok && g_agg.need_mtf)
      {
         g_current_conditions = "MTF not aligned (required at Level " + IntegerToString((int)AggressionLevel) + ")";
         Print(g_current_conditions);
         g_has_pattern = false;
         return;
      }
   }

   if(UseCorrelation)
   {
      g_corr_ok = CheckCorrelation();
      conditions += "Corr:" + (g_corr_ok ? "OK" : "HIGH") + " ";

      // Only strict at lower aggression levels
      if(!g_corr_ok && g_agg.confluence > 3)
      {
         g_current_conditions = "Correlation too high";
         Print(g_current_conditions);
         return;
      }
   }

   // Confluence check - CONTROLLED BY AGGRESSION
   int conf = CalcConfluence();
   conditions += "| Confluence: " + IntegerToString(conf) + "/" + IntegerToString(g_dyn_confluence);

   Print("CONFLUENCE: ", conf, "/", g_dyn_confluence, " (Level ", AggressionLevel, " requires ", g_dyn_confluence, ")");

   if(conf < g_dyn_confluence)
   {
      g_current_conditions = "Confluence " + IntegerToString(conf) + " < " +
                            IntegerToString(g_dyn_confluence) + " (Level " +
                            IntegerToString((int)AggressionLevel) + ")";
      Print("Insufficient confluence: ", g_current_conditions);
      return;
   }

   g_current_conditions = conditions;

   // Risk limits
   if(!CheckRiskLimits())
   {
      g_current_conditions = "Risk limit reached";
      return;
   }

   // Per-symbol limit
   int sym_trades = CountSymbolTrades();
   if(sym_trades >= g_max_per_sym)
   {
      g_current_conditions = "Max per symbol: " + IntegerToString(sym_trades) + "/" + IntegerToString(g_max_per_sym);
      Print(g_current_conditions);
      return;
   }

   // EXECUTE
   double risk = UseDynamicRisk ? CalcDynamicRisk() : g_dyn_risk;

   // Store trade reason before executing
   string reason_details = conditions;

   if(ExecuteTrade(risk))
   {
      // Add to trade reason history
      AddTradeReason(g_pattern.is_bull ? "BUY" : "SELL", g_pattern.name, conf, reason_details);
   }
}

//+------------------------------------------------------------------+
//| SPREAD CHECK                                                      |
//+------------------------------------------------------------------+
void CheckSpread()
{
   double spread_pts = MarketInfo(Symbol(), MODE_SPREAD);
   double spread_price = spread_pts * Point;
   double atr = iATR(Symbol(), Timeframe, 14, 0);
   double max_spread = atr * g_spread_lim;
   g_spread_ok = (spread_price <= max_spread);
}

//+------------------------------------------------------------------+
//| SESSION CHECK (FIXED FOR TESTER)                                  |
//+------------------------------------------------------------------+
void CheckSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int server_hour = dt.hour;
   int gmt_hour = server_hour - (int)BrokerGMT;
   if(gmt_hour < 0) gmt_hour += 24;
   if(gmt_hour >= 24) gmt_hour -= 24;

   if(gmt_hour >= 0 && gmt_hour < 8)
   {
      g_session = ASIAN;
      g_session_ok = TradeAsian;
   }
   else if(gmt_hour >= 8 && gmt_hour < 13)
   {
      g_session = LONDON;
      g_session_ok = TradeLondon;
   }
   else if(gmt_hour >= 13 && gmt_hour < 17)
   {
      g_session = OVERLAP;
      g_session_ok = (TradeLondon || TradeNY);  // Either session enabled allows overlap trading
   }
   else if(gmt_hour >= 17 && gmt_hour < 22)
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
//| VOLUME CHECK                                                      |
//+------------------------------------------------------------------+
void CheckVolume()
{
   long cv = iVolume(Symbol(), Timeframe, 1);
   double sum = 0;
   for(int i = 1; i <= 20; i++) sum += (double)iVolume(Symbol(), Timeframe, i);
   double avg = sum / 20.0;
   double ratio = (avg > 0) ? cv / avg : 0;
   g_vol_ok = (ratio >= g_vol_thresh);
}

//+------------------------------------------------------------------+
//| REGIME DETECTION                                                  |
//+------------------------------------------------------------------+
void DetectRegime()
{
   double ema0 = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema10 = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 10);
   double slope = MathAbs(ema0 - ema10);
   double atr = iATR(Symbol(), Timeframe, 14, 0);

   if(slope > atr * 0.1)
      g_regime = TREND;
   else if(slope < atr * 0.02)
      g_regime = RANGE;
   else
      g_regime = TRANSITION;
}

void DetectBias()
{
   double ema = iMA(Symbol(), Timeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), Timeframe, 1);

   if(price > ema)
      g_bias = BULL;
   else if(price < ema)
      g_bias = BEAR;
   else
      g_bias = NEUTRAL;
}

//+------------------------------------------------------------------+
//| REGIME STRATEGY (CONTROLLED BY AGGRESSION)                        |
//+------------------------------------------------------------------+
void ApplyRegimeStrategy()
{
   if(!g_has_pattern) return;

   int base = g_agg.confluence;

   switch(g_regime)
   {
      case TREND:
         g_dyn_confluence = base;
         // Only reject counter-trend at conservative levels (1-3)
         // Levels 4-5 allow counter-trend trades
         if(base > 3)  // Levels 1, 2, 3 have confluence 4, 5, 6
         {
            if((g_bias == BULL && !g_pattern.is_bull) ||
               (g_bias == BEAR && g_pattern.is_bull))
            {
               Print("Counter-trend rejected at Level ", AggressionLevel);
               g_has_pattern = false;
            }
         }
         break;

      case RANGE:
         // In range, require slightly more confluence
         g_dyn_confluence = MathMin(base + 1, 6);
         break;

      case TRANSITION:
         g_dyn_confluence = MathMin(base + 1, 6);
         break;
   }
}

//+------------------------------------------------------------------+
//| PATTERN DETECTION - ALL 20 PATTERNS                               |
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

   if(range1 < Point) return;

   double uw1 = h1 - MathMax(o1, c1);
   double lw1 = MathMin(o1, c1) - l1;
   double br = body1 / range1;

   // ═══════════════════════════════════════════════════════════════
   // PRIORITY 1: STRONGEST PATTERNS (5 STARS)
   // ═══════════════════════════════════════════════════════════════

   // BULLISH ENGULFING - Very strong reversal
   if(o2 > c2 && c1 > o1 && c1 > o2 && o1 < c2 && body1 > body2)
   { SetPattern("BULL ENGULF", true, 5, c1); return; }

   // BEARISH ENGULFING
   if(c2 > o2 && o1 > c1 && o1 > c2 && c1 < o2 && body1 > body2)
   { SetPattern("BEAR ENGULF", false, 5, c1); return; }

   // MORNING STAR - 3 candle reversal
   if(o3 > c3 && body2 < body3*0.5 && c1 > o1 && c1 > (o3+c3)/2)
   { SetPattern("MORNING STAR", true, 5, c1); return; }

   // EVENING STAR
   if(c3 > o3 && body2 < body3*0.5 && o1 > c1 && c1 < (o3+c3)/2)
   { SetPattern("EVENING STAR", false, 5, c1); return; }

   // THREE WHITE SOLDIERS
   if(c3>o3 && c2>o2 && c1>o1 && c2>c3 && c1>c2 && o2>o3 && o1>o2)
   { SetPattern("3 WHITE SOLDIERS", true, 5, c1); return; }

   // THREE BLACK CROWS
   if(o3>c3 && o2>c2 && o1>c1 && c2<c3 && c1<c2 && o2<o3 && o1<o2)
   { SetPattern("3 BLACK CROWS", false, 5, c1); return; }

   // BULLISH MARUBOZU - Full body, no wicks
   if(uw1 < range1*0.05 && lw1 < range1*0.05 && body1 > range1*0.85 && c1 > o1)
   { SetPattern("BULL MARUBOZU", true, 5, h1); return; }

   // BEARISH MARUBOZU
   if(uw1 < range1*0.05 && lw1 < range1*0.05 && body1 > range1*0.85 && c1 < o1)
   { SetPattern("BEAR MARUBOZU", false, 5, l1); return; }

   // ═══════════════════════════════════════════════════════════════
   // PRIORITY 2: STRONG PATTERNS (4 STARS)
   // ═══════════════════════════════════════════════════════════════

   // HAMMER - Long lower wick
   if(lw1 > body1*2.0 && uw1 < body1*0.3 && body1 > 0 && br < 0.4)
   { SetPattern("HAMMER", true, (lw1>body1*3)?5:4, l1); return; }

   // SHOOTING STAR - Long upper wick
   if(uw1 > body1*2.0 && lw1 < body1*0.3 && body1 > 0 && br < 0.4)
   { SetPattern("SHOOTING STAR", false, (uw1>body1*3)?5:4, h1); return; }

   // BULLISH HARAMI
   if(o2>c2 && c1>o1 && o1>c2 && c1<o2 && body1<body2*0.5)
   { SetPattern("BULL HARAMI", true, 4, c1); return; }

   // BEARISH HARAMI
   if(c2>o2 && o1>c1 && c1>o2 && o1<c2 && body1<body2*0.5)
   { SetPattern("BEAR HARAMI", false, 4, c1); return; }

   // PIERCING LINE
   if(o2>c2 && c1>o1 && o1<c2 && c1>(o2+c2)/2 && c1<o2)
   { SetPattern("PIERCING LINE", true, 4, c1); return; }

   // DARK CLOUD COVER
   if(c2>o2 && o1>c1 && o1>c2 && c1<(o2+c2)/2 && c1>o2)
   { SetPattern("DARK CLOUD", false, 4, c1); return; }

   // DRAGONFLY DOJI - Bullish
   if(br < 0.1 && uw1 < range1*0.1 && lw1 > range1*0.6)
   { SetPattern("DRAGONFLY DOJI", true, 4, l1); return; }

   // GRAVESTONE DOJI - Bearish
   if(br < 0.1 && lw1 < range1*0.1 && uw1 > range1*0.6)
   { SetPattern("GRAVESTONE DOJI", false, 4, h1); return; }

   // ═══════════════════════════════════════════════════════════════
   // PRIORITY 3: MODERATE PATTERNS (3 STARS)
   // ═══════════════════════════════════════════════════════════════

   // TWEEZER BOTTOM
   double tol = iATR(Symbol(), Timeframe, 14, 0) * 0.1;
   if(MathAbs(l1-l2) < tol && o2 > c2 && c1 > o1)
   { SetPattern("TWEEZER BOTTOM", true, 3, l1); return; }

   // TWEEZER TOP
   if(MathAbs(h1-h2) < tol && c2 > o2 && o1 > c1)
   { SetPattern("TWEEZER TOP", false, 3, h1); return; }

   // SPINNING TOP - Indecision
   if(br < 0.3 && uw1 > body1 && lw1 > body1 && body1 > 0)
   { SetPattern("SPINNING TOP", (g_bias==BULL), 2, c1); return; }

   // DOJI - Indecision
   if(br < 0.1 && range1 > Point * 10)
   { SetPattern("DOJI", (g_bias==BULL), 2, c1); return; }

   // ═══════════════════════════════════════════════════════════════
   // PRIORITY 4: WEAK PATTERNS (1-2 STARS) - Only at Level 5
   // ═══════════════════════════════════════════════════════════════

   // INVERTED HAMMER
   if(uw1 > body1*2.0 && lw1 < body1*0.3 && c1 > o1 && br < 0.4)
   { SetPattern("INV HAMMER", true, 2, h1); return; }

   // HANGING MAN
   if(lw1 > body1*2.0 && uw1 < body1*0.3 && o1 > c1 && br < 0.4)
   { SetPattern("HANGING MAN", false, 2, l1); return; }

   // BULLISH BELT HOLD
   if(lw1 < range1*0.05 && c1 > o1 && body1 > range1*0.6)
   { SetPattern("BULL BELT", true, 2, o1); return; }

   // BEARISH BELT HOLD
   if(uw1 < range1*0.05 && o1 > c1 && body1 > range1*0.6)
   { SetPattern("BEAR BELT", false, 2, o1); return; }

   // Simple bullish/bearish candle as last resort (strength 1)
   // ANY bullish or bearish candle - ensures Level 5 always finds a pattern
   if(c1 > o1)
   { SetPattern("BULL CANDLE", true, 1, c1); return; }

   if(o1 > c1)
   { SetPattern("BEAR CANDLE", false, 1, c1); return; }

   // Absolute fallback - flat candle, use bias
   SetPattern("FLAT", (g_bias == BULL), 1, c1);
}

void SetPattern(string name, bool bull, int str, double price)
{
   g_pattern.name = name;
   g_pattern.is_bull = bull;
   g_pattern.strength = str;
   g_pattern.price = price;
   g_pattern.time = TimeCurrent();
   g_has_pattern = true;
}

//+------------------------------------------------------------------+
//| MTF & CORRELATION                                                 |
//+------------------------------------------------------------------+
bool CheckMTF()
{
   int htf = GetHigherTF();
   double ema = iMA(Symbol(), htf, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), htf, 0);

   if(g_pattern.is_bull && price < ema) return false;
   if(!g_pattern.is_bull && price > ema) return false;
   return true;
}

bool CheckCorrelation()
{
   double net = 0;
   string base = StringSubstr(Symbol(), 0, 3);
   string quote = StringSubstr(Symbol(), 3, 3);

   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      string s = OrderSymbol();
      string sb = StringSubstr(s, 0, 3);
      string sq = StringSubstr(s, 3, 3);
      int dir = (OrderType() == OP_BUY) ? 1 : -1;

      if(sb == base || sq == quote || sb == quote || sq == base)
         net += OrderLots() * dir;
   }

   return (MathAbs(net) <= g_corr_lim * 10);
}

int GetHigherTF()
{
   if(Timeframe == PERIOD_M1) return PERIOD_M5;
   if(Timeframe == PERIOD_M5) return PERIOD_M15;
   if(Timeframe == PERIOD_M15) return PERIOD_H1;
   if(Timeframe == PERIOD_H1) return PERIOD_H4;
   if(Timeframe == PERIOD_H4) return PERIOD_D1;
   return PERIOD_W1;
}

//+------------------------------------------------------------------+
//| CONFLUENCE CALCULATION                                            |
//+------------------------------------------------------------------+
int CalcConfluence()
{
   int score = 0;

   // 1. Regime is clear (not transition)
   if(g_regime != TRANSITION) score++;

   // 2. Bias alignment with pattern
   if((g_bias == BULL && g_pattern.is_bull) || (g_bias == BEAR && !g_pattern.is_bull)) score++;

   // 3. Volume confirmation
   if(g_vol_ok) score++;

   // 4. Spread acceptable
   if(g_spread_ok) score++;

   // 5. Session active
   if(g_session_ok) score++;

   // 6. MTF alignment
   if(g_mtf_ok) score++;

   // 7. Correlation acceptable
   if(g_corr_ok) score++;

   // 8. Pattern strength >= 4
   if(g_pattern.strength >= 4) score++;

   // 9. Market structure alignment
   if(UseMarketStructure)
   {
      if((g_pattern.is_bull && g_bias == BULL) || (!g_pattern.is_bull && g_bias == BEAR)) score++;
   }

   // 10. Extra point for 5-star pattern
   if(g_pattern.strength == 5) score++;

   return score;
}

//+------------------------------------------------------------------+
//| RISK CHECKS                                                       |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   // Daily loss check
   double dl = ((g_daily_start - AccountBalance()) / g_daily_start) * 100.0;
   if(dl >= g_daily_lim)
   {
      Print("Daily loss limit: ", DoubleToString(dl, 1), "%");
      return false;
   }

   // Weekly loss check
   double wl = ((g_weekly_start - AccountBalance()) / g_weekly_start) * 100.0;
   if(wl >= g_weekly_lim)
   {
      Print("Weekly loss limit: ", DoubleToString(wl, 1), "%");
      return false;
   }

   // Max trades check - USE AGGRESSION SETTING
   int total = CountAllTrades();
   int max_allowed = MathMin(g_max_trades, g_agg.max_trades);
   if(total >= max_allowed)
   {
      Print("Max trades: ", total, "/", max_allowed, " (Level ", AggressionLevel, ")");
      return false;
   }

   return true;
}

int CountAllTrades()
{
   int c = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() == MagicNumber && OrderType() <= OP_SELL) c++;
   }
   return c;
}

int CountSymbolTrades()
{
   int c = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() == MagicNumber && OrderSymbol() == Symbol() && OrderType() <= OP_SELL) c++;
   }
   return c;
}

double CalcDynamicRisk()
{
   double r = g_dyn_risk;

   if(AccountBalance() > g_peak_bal) g_peak_bal = AccountBalance();
   double dd = (g_peak_bal > 0) ? (g_peak_bal - AccountBalance()) / g_peak_bal : 0;

   if(dd > 0.05) r *= (1.0 - dd);
   if(g_consec_loss >= 2) r *= 0.5;

   return MathMax(r, 0.001);
}

//+------------------------------------------------------------------+
//| LOT SIZING                                                        |
//+------------------------------------------------------------------+
double CalcLot(double sl_pips, double risk_pct)
{
   double bmin = MarketInfo(Symbol(), MODE_MINLOT);
   double bmax = MarketInfo(Symbol(), MODE_MAXLOT);
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);

   double lot;

   if(SizingMode == SIZE_FIXED)
   {
      lot = (g_min_lot < bmin) ? bmin : g_min_lot;
      if(lot > g_max_lot) lot = g_max_lot;
   }
   else
   {
      double cap = AccountBalance() * risk_pct;
      double tv = MarketInfo(Symbol(), MODE_TICKVALUE);
      double ts = MarketInfo(Symbol(), MODE_TICKSIZE);
      if(ts <= 0 || tv <= 0) return bmin;

      double rpl = (sl_pips * Point / ts) * tv;
      lot = (rpl > 0) ? cap / rpl : bmin;
   }

   // Normalize
   lot = MathFloor(lot / step) * step;
   if(lot < bmin) lot = bmin;
   if(lot > bmax) lot = bmax;

   return lot;
}

//+------------------------------------------------------------------+
//| TRADE EXECUTION                                                   |
//+------------------------------------------------------------------+
bool ExecuteTrade(double risk_pct)
{
   bool is_buy = g_pattern.is_bull;
   double entry = is_buy ? Ask : Bid;

   // Stop loss calculation - BASED ON MODE
   double sl_dist;

   if(SL_Mode == SL_MODE_ATR)
   {
      // ATR-based stop loss
      double atr = iATR(Symbol(), Timeframe, 14, 0);
      sl_dist = atr * g_sl_atr;

      // Also consider swing points
      double sw;
      if(is_buy)
      {
         sw = GetSwingLow(20);
         sl_dist = MathMax(sl_dist, entry - sw + 5*Point);
      }
      else
      {
         sw = GetSwingHigh(20);
         sl_dist = MathMax(sl_dist, sw - entry + 5*Point);
      }
   }
   else
   {
      // Fixed pips stop loss
      sl_dist = g_sl_pips * Point;

      // Adjust for 5-digit brokers
      if(Digits == 5 || Digits == 3)
         sl_dist = g_sl_pips * Point * 10;
   }

   double sl = is_buy ? entry - sl_dist : entry + sl_dist;
   double tp = entry + (is_buy ? 1 : -1) * sl_dist * g_dyn_tp;

   sl = NormalizeDouble(sl, Digits);
   tp = NormalizeDouble(tp, Digits);

   // Lot size
   double sl_pips = sl_dist / Point;
   double lot = CalcLot(sl_pips, risk_pct);

   Print("═══════════════════════════════════════════════════════════");
   Print("  EXECUTING TRADE - LEVEL ", AggressionLevel);
   Print("═══════════════════════════════════════════════════════════");
   Print("  Direction: ", is_buy ? "BUY" : "SELL");
   Print("  Pattern: ", g_pattern.name, " [", g_pattern.strength, " stars]");
   Print("  Lot: ", lot);
   Print("  Entry: ", entry);
   Print("  SL: ", sl, " (", SL_Mode == SL_MODE_ATR ? "ATR-based" : "Fixed pips", ")");
   Print("  TP: ", tp);
   Print("═══════════════════════════════════════════════════════════");

   string comment = "IGTR|" + g_pattern.name + "|L" + IntegerToString((int)AggressionLevel);
   int ticket;

   if(is_buy)
      ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 10, sl, tp, comment, MagicNumber, 0, clrGreen);
   else
      ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 10, sl, tp, comment, MagicNumber, 0, clrRed);

   if(ticket > 0)
   {
      Print("*** TRADE EXECUTED #", ticket, " ***");
      g_has_pattern = false;
      g_consec_loss = 0;
      return true;
   }
   else
   {
      int err = GetLastError();
      Print("*** TRADE FAILED - Error: ", err, " ***");
      return false;
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
      double r_profit = profit_dist / sl_dist;
      double cash_profit = OrderProfit() + OrderSwap() + OrderCommission();

      // Partial close at TP1
      if(UsePartialClose && r_profit >= g_tp1)
      {
         double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
         if(lots > min_lot * 1.5)
         {
            double close_lots = NormalizeDouble(lots * g_partial_pct / 100.0, 2);
            if(close_lots >= min_lot && (lots - close_lots) >= min_lot)
            {
               if(OrderClose(ticket, close_lots, is_buy ? Bid : Ask, 10, clrYellow))
                  Print("Partial close ", g_partial_pct, "% at ", g_tp1, "R");
            }
         }
      }

      // Breakeven at 1R
      if(r_profit >= 1.0 && MathAbs(sl - entry) > Point * 2)
      {
         double new_sl = entry + (is_buy ? 1 : -1) * 5 * Point;
         if((is_buy && new_sl > sl) || (!is_buy && new_sl < sl))
         {
            if(OrderModify(ticket, entry, new_sl, tp, 0, clrBlue))
               Print("Breakeven #", ticket);
         }
      }

      // Profit lock
      bool r_hit = (r_profit >= g_lock_r);
      bool fixed_hit = (cash_profit >= g_lock_amt);
      if(UseProfitLock && (r_hit || fixed_hit))
      {
         double lock_dist = profit_dist * g_lock_pct / 100.0;
         double locked_sl = is_buy ? (entry + lock_dist) : (entry - lock_dist);

         if((is_buy && locked_sl > sl) || (!is_buy && locked_sl < sl))
         {
            if(OrderModify(ticket, entry, locked_sl, tp, 0, clrGold))
               Print("Profit locked #", ticket);
         }
      }

      // Trailing at 1.5R
      if(r_profit >= 1.5)
      {
         double nsw;
         if(is_buy)
         {
            nsw = GetSwingLow(10);
            if(nsw > sl && nsw < price)
               OrderModify(ticket, entry, nsw, tp, 0, clrAqua);
         }
         else
         {
            nsw = GetSwingHigh(10);
            if(nsw < sl && nsw > price)
               OrderModify(ticket, entry, nsw, tp, 0, clrAqua);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| ACCOUNT LOCK                                                      |
//+------------------------------------------------------------------+
void CheckAccountLock()
{
   double tp = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderType() > OP_SELL) continue;
      tp += OrderProfit() + OrderSwap() + OrderCommission();
   }

   if(tp <= 0) return;

   double pct = (tp / AccountBalance()) * 100.0;

   if(tp >= g_acct_lock_amt || pct >= g_acct_lock_pct)
   {
      Print("ACCOUNT LOCK! Profit: ", tp, " (", pct, "%)");
      CloseAll();
      if(AlertPopup) Alert("Account profit locked: ", tp);
      if(AlertMobile) SendNotification("Account profit locked: " + DoubleToString(tp, 2));
   }
}

void CloseAll()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderType() > OP_SELL) continue;

      double p = (OrderType() == OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), p, 10, clrRed))
         Print("Closed #", OrderTicket());
   }
}

//+------------------------------------------------------------------+
//| HELPERS                                                           |
//+------------------------------------------------------------------+
double GetSwingHigh(int lb)
{
   double h = 0;
   for(int i = 1; i <= lb; i++)
   {
      double v = iHigh(Symbol(), Timeframe, i);
      if(v > h) h = v;
   }
   return h;
}

double GetSwingLow(int lb)
{
   double l = DBL_MAX;
   for(int i = 1; i <= lb; i++)
   {
      double v = iLow(Symbol(), Timeframe, i);
      if(v < l) l = v;
   }
   return l;
}

//+------------------------------------------------------------------+
//| TRADE REASON HISTORY                                              |
//+------------------------------------------------------------------+
void AddTradeReason(string direction, string pattern, int confluence, string reasons)
{
   // Shift array down
   for(int i = 9; i > 0; i--)
   {
      g_trade_reasons[i] = g_trade_reasons[i-1];
   }

   // Add new reason at position 0
   g_trade_reasons[0].time = TimeCurrent();
   g_trade_reasons[0].symbol = Symbol();
   g_trade_reasons[0].direction = direction;
   g_trade_reasons[0].pattern = pattern;
   g_trade_reasons[0].confluence = confluence;
   g_trade_reasons[0].reasons = reasons;

   if(g_trade_reason_count < 10) g_trade_reason_count++;
}

//+------------------------------------------------------------------+
//| PATTERN HISTORY                                                   |
//+------------------------------------------------------------------+
void AddPatternToHistory(string name, bool is_bull, int strength)
{
   // Shift array down
   for(int i = 4; i > 0; i--)
   {
      g_pattern_history[i] = g_pattern_history[i-1];
   }

   // Add new pattern at position 0
   g_pattern_history[0].time = TimeCurrent();
   g_pattern_history[0].name = name;
   g_pattern_history[0].is_bull = is_bull;
   g_pattern_history[0].strength = strength;

   if(g_pattern_history_count < 5) g_pattern_history_count++;
}

//+------------------------------------------------------------------+
//| CHART DISPLAY                                                     |
//+------------------------------------------------------------------+
void CreateChartDisplay()
{
   // Create background rectangles and labels
   if(ShowAggressionInfo)
   {
      CreateLabel("IGTR_AGG_TITLE", 10, 30, "═══ AGGRESSION LEVEL " + IntegerToString((int)AggressionLevel) + " ═══", clrGold, 10);
      CreateLabel("IGTR_AGG_CONF", 10, 50, "Confluence Required: " + IntegerToString(g_agg.confluence), clrWhite, 9);
      CreateLabel("IGTR_AGG_STR", 10, 65, "Min Pattern Strength: " + IntegerToString(g_agg.min_strength), clrWhite, 9);
      CreateLabel("IGTR_AGG_MTF", 10, 80, "MTF Required: " + (g_agg.need_mtf ? "YES" : "NO"), g_agg.need_mtf ? clrOrange : clrLime, 9);
      CreateLabel("IGTR_AGG_VOL", 10, 95, "Volume Required: " + (g_agg.need_vol ? "YES" : "NO"), g_agg.need_vol ? clrOrange : clrLime, 9);
      CreateLabel("IGTR_AGG_RISK", 10, 110, "Risk Mult: " + DoubleToString(g_agg.risk_mult, 2) + "x", clrWhite, 9);
   }

   if(ShowPatternHistory)
   {
      CreateLabel("IGTR_PAT_TITLE", 10, 140, "═══ LAST 5 PATTERNS ═══", clrCyan, 10);
      for(int i = 0; i < 5; i++)
      {
         CreateLabel("IGTR_PAT_" + IntegerToString(i), 10, 160 + i*15, "---", clrGray, 8);
      }
   }

   if(ShowTradeReasons)
   {
      CreateLabel("IGTR_TR_TITLE", 10, 250, "═══ LAST 10 TRADES ═══", clrYellow, 10);
      for(int i = 0; i < 10; i++)
      {
         CreateLabel("IGTR_TR_" + IntegerToString(i), 10, 270 + i*15, "---", clrGray, 8);
      }
   }

   // Current conditions
   CreateLabel("IGTR_COND_TITLE", 10, 440, "═══ CURRENT STATUS ═══", clrMagenta, 10);
   CreateLabel("IGTR_COND", 10, 460, "Initializing...", clrWhite, 9);
}

void UpdateChartDisplay()
{
   // Update pattern history
   if(ShowPatternHistory)
   {
      for(int i = 0; i < 5; i++)
      {
         string name = "IGTR_PAT_" + IntegerToString(i);
         if(i < g_pattern_history_count)
         {
            string txt = TimeToString(g_pattern_history[i].time, TIME_MINUTES) + " | " +
                        g_pattern_history[i].name + " [" +
                        IntegerToString(g_pattern_history[i].strength) + "*] " +
                        (g_pattern_history[i].is_bull ? "BUY" : "SELL");
            color clr = g_pattern_history[i].is_bull ? clrLime : clrRed;
            ObjectSetString(0, name, OBJPROP_TEXT, txt);
            ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
         }
      }
   }

   // Update trade reasons
   if(ShowTradeReasons)
   {
      for(int i = 0; i < 10; i++)
      {
         string name = "IGTR_TR_" + IntegerToString(i);
         if(i < g_trade_reason_count)
         {
            string txt = TimeToString(g_trade_reasons[i].time, TIME_MINUTES) + " | " +
                        g_trade_reasons[i].symbol + " " +
                        g_trade_reasons[i].direction + " | " +
                        g_trade_reasons[i].pattern + " | Conf:" +
                        IntegerToString(g_trade_reasons[i].confluence);
            color clr = (g_trade_reasons[i].direction == "BUY") ? clrLime : clrRed;
            ObjectSetString(0, name, OBJPROP_TEXT, txt);
            ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
         }
      }
   }

   // Update current conditions
   if(g_current_conditions != "")
   {
      ObjectSetString(0, "IGTR_COND", OBJPROP_TEXT, g_current_conditions);
   }
}

void CreateLabel(string name, int x, int y, string text, color clr, int size)
{
   ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}
//+------------------------------------------------------------------+
