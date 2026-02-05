//+------------------------------------------------------------------+
//|                        InstitutionalTradingRobot_v4_MQL4.mq4     |
//|                    TRADING-ONLY VERSION (No GUI/No ML Export)    |
//|                         MQL4 Conversion from MQL5 v4.0           |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.00"
#property description "MQL4 Trading Robot - All Filters + Aggression 1-5"
#property strict

//+------------------------------------------------------------------+
//| POSITION SIZING MODE ENUM                                         |
//+------------------------------------------------------------------+
enum ENUM_POSITION_SIZING_MODE
{
   LOT_SIZE_RANGE,      // Fixed Lot Range (Min/Max Bounds)
   RISK_PERCENTAGE      // Dynamic Risk % (Account-Based)
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - COMPLETE SET FROM MQL5 v4.0                    |
//+------------------------------------------------------------------+
input string   _1 = "═════════ CORE SETTINGS ═════════";
input bool     EnableTrading = false;                   // Enable Auto Trading (START FALSE!)
input bool     IndicatorMode = true;                    // Visual Analysis Mode (no trades)
input int      PreferredTimeframe = PERIOD_H4;          // Trading Timeframe
input int      MagicNumber = 123456;                    // Magic Number

input string   _2 = "═════════ POSITION SIZING ═════════";
input ENUM_POSITION_SIZING_MODE PositionSizingMode = LOT_SIZE_RANGE;
input double   MinLotSize = 0.01;                       // Minimum Lot Size
input double   MaxLotSize = 0.10;                       // Maximum Lot Size

input string   _3 = "═════════ AGGRESSION & ADAPTATION ═════════";
input int      AggressionLevel = 3;                     // Aggression (1=Conservative, 5=Maximum)
input bool     UsePatternTracking = true;               // Pattern Performance Tracking
input bool     UseParameterAdaptation = true;           // Self-Optimization
input bool     UseRegimeStrategy = true;                // Regime-Specific Strategies
input int      AdaptationPeriod = 20;                   // Learning Period (Trades)

input string   _4a = "═════════ EXECUTION QUALITY ═════════";
input bool     UseVolumeFilter = true;                  // Volume Confirmation
input double   MinVolumeMultiplier = 1.5;               // Min Volume (x Average)
input bool     UseSpreadFilter = true;                  // Spread Protection
input double   MaxSpreadPercent = 0.3;                  // Max Spread (% of ATR)
input bool     UseSlippageModel = true;                 // Slippage Modeling
input double   ExpectedSlippagePercent = 0.1;           // Expected Slippage (% of ATR)

input string   _4b = "═════════ MULTI-DIMENSIONAL FILTERS ═════════";
input bool     UseMTFConfirmation = true;               // Multi-Timeframe Confirmation
input bool     UseSessionFilter = true;                 // Session Filtering
input bool     TradeAsianSession = false;               // Trade Asian Session
input bool     TradeLondonSession = true;               // Trade London Session
input bool     TradeNYSession = true;                   // Trade NY Session
input bool     UseCorrelationFilter = true;             // Portfolio Correlation Check
input double   MaxCorrelationExposure = 0.7;            // Max Correlation Limit
input bool     UsePositionCorrelation = true;           // Position Correlation Management

input string   _4c = "═════════ ADAPTIVE RISK ═════════";
input bool     UseVolatilityAdaptation = true;          // Volatility Regime Detection
input bool     UseDynamicRisk = true;                   // Drawdown-Based Risk
input bool     UsePatternDecay = true;                  // Pattern Time Decay
input int      PatternExpiryBars = 3;                   // Pattern Valid For (Bars)

input string   _4d = "═════════ SMART MONEY CONCEPTS ═════════";
input bool     UseLiquiditySweep = true;                // Liquidity Sweep Detection
input bool     UseRetailTrap = true;                    // Retail Trap Detection
input bool     UseOrderBlockInvalidation = true;        // Order Block Invalidation
input int      MaxOBTests = 3;                          // Max Order Block Re-Tests
input bool     UseMarketStructure = true;               // Market Structure Tracking

input string   _5 = "═════════ RISK MANAGEMENT ═════════";
input double   BaseRiskPercent = 0.5;                   // Base Risk Per Trade (%)
input int      MaxOpenTrades = 3;                       // Max Total Open Trades
input int      MaxTradesPerSymbol = 1;                  // Max Trades Per Symbol
input double   DailyLossLimit = 2.0;                    // Daily Loss Limit (%)
input double   WeeklyLossLimit = 5.0;                   // Weekly Loss Limit (%)
input double   StopLossATR = 2.0;                       // Stop Loss (x ATR)

input string   _6 = "═════════ TAKE PROFIT ═════════";
input double   TP1_RiskReward = 2.0;                    // Take Profit 1 (R:R)
input double   TP2_RiskReward = 3.0;                    // Take Profit 2 (R:R)
input double   TP3_RiskReward = 5.0;                    // Take Profit 3 (R:R)

input string   _7 = "═════════ PROFIT PROTECTION (Per Position) ═════════";
input bool     UseProfitLock = true;                    // Enable Profit Lock
input double   ProfitLockTrigger = 1.5;                 // Lock Trigger (R multiple)
input double   ProfitLockFixedAmount = 100.0;           // OR Lock at Fixed Profit
input double   ProfitLockPercent = 50.0;                // Lock % of Profit
input bool     UsePartialClose = false;                 // Partial Close at TP1
input double   PartialClosePercent = 50.0;              // % to Close at TP1

input string   _8 = "═════════ ACCOUNT PROFIT LOCK ═════════";
input bool     UseAccountProfitLock = true;             // Account-Level Profit Lock
input double   AccountProfitLockAmount = 1000.0;        // Close ALL at Profit Amount
input double   AccountProfitLockPercent = 5.0;          // OR Close ALL at % of Balance

input string   _9 = "═════════ ALERTS ═════════";
input bool     EnablePopupAlerts = false;               // Enable Pop-up Alerts
input bool     EnableMobileNotifications = false;       // Enable Mobile Push

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                      |
//+------------------------------------------------------------------+
enum MARKET_REGIME { REGIME_TREND, REGIME_RANGE, REGIME_TRANSITION };
enum MARKET_BIAS { BIAS_BULLISH, BIAS_BEARISH, BIAS_NEUTRAL };
enum TRADING_SESSION { SESSION_ASIAN, SESSION_LONDON, SESSION_OVERLAP, SESSION_NY, SESSION_CLOSED };
enum VOLATILITY_REGIME { VOL_LOW, VOL_NORMAL, VOL_HIGH };
enum TRADE_DECISION { DECISION_ENTER, DECISION_SKIP, DECISION_WAIT };

//+------------------------------------------------------------------+
//| DATA STRUCTURES                                                   |
//+------------------------------------------------------------------+
struct PatternInfo
{
   string      name;
   string      signal;
   int         strength;
   datetime    detected_time;
   double      price;
   bool        is_bullish;
   int         bar_index;
};

struct LiquidityZone
{
   double      price;
   bool        is_high;
   datetime    time;
   int         touch_count;
   bool        swept;
};

struct FairValueGap
{
   double      top;
   double      bottom;
   datetime    time;
   bool        is_bullish;
   bool        filled;
};

struct OrderBlockInfo
{
   double      top;
   double      bottom;
   datetime    time;
   bool        is_bullish;
   int         test_count;
   bool        invalidated;
};

struct MarketStructure
{
   double      last_HH;
   double      last_HL;
   double      last_LH;
   double      last_LL;
   string      structure;
};

struct AggressionSettings
{
   int         confluence_required;
   double      risk_multiplier;
   int         min_pattern_strength;
   bool        require_mtf;
   bool        require_volume;
   int         max_trades;
   double      tp_multiplier;
   string      description;
};

struct VolumeData
{
   double      current_volume;
   double      average_volume;
   double      volume_ratio;
   bool        above_threshold;
   bool        spike_detected;
};

struct SpreadData
{
   double      current_pips;
   double      max_allowed_pips;
   bool        acceptable;
};

struct SessionData
{
   TRADING_SESSION current_session;
   string      session_name;
   bool        is_tradeable;
   double      expected_volatility;
};

struct VolatilityData
{
   VOLATILITY_REGIME regime;
   double      atr_current;
   double      atr_average;
   double      ratio;
};

struct TradeDecisionInfo
{
   TRADE_DECISION  decision;
   int             confluence_score;
   int             passed_count;
   int             failed_count;
   string          reason;
};

struct PatternPerformance
{
   string      pattern_name;
   MARKET_REGIME regime;
   int         total_trades;
   int         winning_trades;
   double      total_pnl;
   double      win_rate;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
MARKET_REGIME       g_regime = REGIME_TREND;
MARKET_BIAS         g_bias = BIAS_NEUTRAL;
TRADING_SESSION     g_session = SESSION_ASIAN;
VOLATILITY_REGIME   g_volatility = VOL_NORMAL;

PatternInfo         g_pattern;
bool                g_has_pattern = false;
PatternInfo         g_pattern_h1;
bool                g_has_pattern_h1 = false;
PatternInfo         g_pattern_m15;
bool                g_has_pattern_m15 = false;

LiquidityZone       g_liq_zones[100];
int                 g_liq_count = 0;
FairValueGap        g_fvg_zones[50];
int                 g_fvg_count = 0;
OrderBlockInfo      g_ob_zones[50];
int                 g_ob_count = 0;
MarketStructure     g_structure;

VolumeData          g_vol_data;
SpreadData          g_spread_data;
SessionData         g_sess_data;
VolatilityData      g_atr_data;

// Dashboard tracking bools
bool                g_mtf_ok = false;
bool                g_correlation_ok = true;

AggressionSettings  g_presets[5];
AggressionSettings  g_aggression;

PatternPerformance  g_perf[100];
int                 g_perf_count = 0;

double              g_daily_start_bal;
double              g_weekly_start_bal;
double              g_hourly_start_bal;
datetime            g_last_daily_reset;
datetime            g_last_weekly_reset;
datetime            g_last_hourly_reset;
int                 g_consecutive_losses = 0;
int                 g_consecutive_wins = 0;
double              g_peak_balance = 0;

int                 g_dyn_confluence = 3;
double              g_dyn_risk = 0.5;
double              g_dyn_tp1 = 2.0;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("╔═══════════════════════════════════════════════════════════╗");
   Print("║  INSTITUTIONAL TRADING ROBOT v4.0 (MQL4)                 ║");
   Print("║  Trading-Only - All Filters + Aggression Levels          ║");
   Print("╚═══════════════════════════════════════════════════════════╝");

   InitializeAggressionPresets();
   ApplyAggressionLevel();
   LoadPatternPerformance();

   g_daily_start_bal = AccountBalance();
   g_weekly_start_bal = AccountBalance();
   g_hourly_start_bal = AccountBalance();
   g_peak_balance = AccountBalance();
   g_last_daily_reset = TimeCurrent();
   g_last_weekly_reset = TimeCurrent();
   g_last_hourly_reset = TimeCurrent();

   double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
   double max_lot = MarketInfo(Symbol(), MODE_MAXLOT);
   double lot_step = MarketInfo(Symbol(), MODE_LOTSTEP);
   Print("═══ ", Symbol(), " LOT CONSTRAINTS ═══");
   Print("  Min: ", DoubleToString(min_lot, 2), " Max: ", DoubleToString(max_lot, 2), " Step: ", DoubleToString(lot_step, 4));

   if(!EnableTrading || IndicatorMode)
      Print("WARNING: Trading DISABLED - Indicator mode");
   else
      Print("AUTO-TRADING ENABLED - Level ", AggressionLevel);

   Print("Max per symbol: ", MaxTradesPerSymbol, " | Max total: ", g_aggression.max_trades);

   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   SavePatternPerformance();
   Print("Institutional Trading Robot v4.0 (MQL4) Stopped");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   CheckPnLResets();

   if(UseAccountProfitLock)
      CheckAccountProfitLock();

   // Manage existing trades EVERY tick (profit lock, trailing, partial close)
   ManageOpenTrades();

   // New bar check for trade entries
   static datetime last_bar_time = 0;
   datetime current_bar_time = iTime(Symbol(), PreferredTimeframe, 0);
   if(current_bar_time == last_bar_time) return;
   last_bar_time = current_bar_time;

   //═══ PHASE 0: PRE-FLIGHT ═══
   if(UseSpreadFilter)
   {
      AnalyzeSpread();
      if(!g_spread_data.acceptable)
      {
         Print("Spread too wide: ", DoubleToString(g_spread_data.current_pips, 1), " pips > ", DoubleToString(g_spread_data.max_allowed_pips, 1));
         return;
      }
   }

   if(UseSessionFilter)
   {
      AnalyzeSession();
      if(!g_sess_data.is_tradeable) return;
   }

   //═══ PHASE 1: MARKET CONTEXT ═══
   if(UseVolatilityAdaptation) AnalyzeVolatilityRegime();
   DetectMarketRegime();
   DetermineBias();
   if(UseMarketStructure) UpdateMarketStructure();

   //═══ PHASE 2: LIQUIDITY MAPPING ═══
   MapLiquidityZones();
   DetectFairValueGaps();
   DetectOrderBlocks();

   //═══ PHASE 3: PATTERN DETECTION ═══
   ScanForCandlestickPatterns();
   ScanLowerTimeframes();

   if(!g_has_pattern) return;

   // Pattern strength gate
   if(g_pattern.strength < g_aggression.min_pattern_strength)
   {
      g_has_pattern = false;
      return;
   }

   // Regime-specific strategy
   if(UseRegimeStrategy) ApplyRegimeStrategy();
   if(!g_has_pattern) return;

   // Pattern decay
   if(UsePatternDecay && !IsPatternValid())
   {
      g_has_pattern = false;
      return;
   }

   Print("PATTERN: ", g_pattern.name, " [", g_pattern.strength, " stars] ", g_pattern.is_bullish ? "BUY" : "SELL");

   //═══ PHASE 4: INSTITUTIONAL FILTERS ═══
   if(UseVolumeFilter)
   {
      AnalyzeVolume();
      if(!g_vol_data.above_threshold && g_aggression.require_volume)
      {
         g_has_pattern = false;
         return;
      }
   }

   if(UseMTFConfirmation)
   {
      g_mtf_ok = CheckMTFAlignment();
      if(!g_mtf_ok && g_aggression.require_mtf)
      {
         g_has_pattern = false;
         return;
      }
   }

   if(UseCorrelationFilter)
   {
      g_correlation_ok = CheckCorrelation();
      if(!g_correlation_ok) return;
   }

   if(UseLiquiditySweep && CheckLiquiditySweep(g_pattern.is_bullish))
      Print("LIQUIDITY SWEEP confirmed!");

   if(UseRetailTrap && DetectRetailTrap())
   {
      g_has_pattern = false;
      return;
   }

   // Confluence evaluation
   TradeDecisionInfo decision = EvaluateDecision();
   Print("CONFLUENCE: ", decision.confluence_score, "/", g_dyn_confluence, " - ", decision.reason);

   //═══ PHASE 5: EXECUTION ═══
   if(decision.decision == DECISION_ENTER && EnableTrading && !IndicatorMode)
   {
      if(!CheckRiskLimits()) return;

      // Per-symbol limit check
      int sym_trades = CountSymbolTrades(Symbol());
      if(sym_trades >= MaxTradesPerSymbol)
      {
         Print("MAX TRADES PER SYMBOL: ", sym_trades, "/", MaxTradesPerSymbol, " on ", Symbol());
         return;
      }

      double risk = UseDynamicRisk ? CalcDynamicRisk() : g_dyn_risk;
      double slippage = UseSlippageModel ? CalcSlippage() : 0;
      ExecuteTrade(risk, slippage);
   }

   //═══ PHASE 7: ADAPTATION ═══
   if(UseParameterAdaptation) AdaptParameters();
}

//+------------------------------------------------------------------+
//| AGGRESSION PRESETS                                                |
//+------------------------------------------------------------------+
void InitializeAggressionPresets()
{
   g_presets[0].confluence_required = 6; g_presets[0].risk_multiplier = 0.5;
   g_presets[0].min_pattern_strength = 4; g_presets[0].require_mtf = true;
   g_presets[0].require_volume = true; g_presets[0].max_trades = 1;
   g_presets[0].tp_multiplier = 1.5; g_presets[0].description = "ULTRA CONSERVATIVE";

   g_presets[1].confluence_required = 5; g_presets[1].risk_multiplier = 0.75;
   g_presets[1].min_pattern_strength = 3; g_presets[1].require_mtf = true;
   g_presets[1].require_volume = true; g_presets[1].max_trades = 2;
   g_presets[1].tp_multiplier = 1.8; g_presets[1].description = "CONSERVATIVE";

   g_presets[2].confluence_required = 4; g_presets[2].risk_multiplier = 1.0;
   g_presets[2].min_pattern_strength = 2; g_presets[2].require_mtf = true;
   g_presets[2].require_volume = false; g_presets[2].max_trades = 3;
   g_presets[2].tp_multiplier = 2.0; g_presets[2].description = "BALANCED";

   g_presets[3].confluence_required = 3; g_presets[3].risk_multiplier = 1.25;
   g_presets[3].min_pattern_strength = 2; g_presets[3].require_mtf = false;
   g_presets[3].require_volume = false; g_presets[3].max_trades = 5;
   g_presets[3].tp_multiplier = 2.5; g_presets[3].description = "AGGRESSIVE";

   g_presets[4].confluence_required = 2; g_presets[4].risk_multiplier = 1.5;
   g_presets[4].min_pattern_strength = 1; g_presets[4].require_mtf = false;
   g_presets[4].require_volume = false; g_presets[4].max_trades = 8;
   g_presets[4].tp_multiplier = 3.0; g_presets[4].description = "MAXIMUM";
}

void ApplyAggressionLevel()
{
   int lv = MathMax(1, MathMin(5, AggressionLevel));
   g_aggression = g_presets[lv - 1];
   g_dyn_confluence = g_aggression.confluence_required;
   g_dyn_risk = BaseRiskPercent * g_aggression.risk_multiplier;
   g_dyn_tp1 = TP1_RiskReward * g_aggression.tp_multiplier / 2.0;
   Print("AGGRESSION ", lv, ": ", g_aggression.description,
         " | Confluence: ", g_aggression.confluence_required,
         " | Risk: x", g_aggression.risk_multiplier,
         " | Max: ", g_aggression.max_trades);
}

//+------------------------------------------------------------------+
//| P&L RESETS                                                        |
//+------------------------------------------------------------------+
void CheckPnLResets()
{
   MqlDateTime ct, ld, lh;
   TimeToStruct(TimeCurrent(), ct);
   TimeToStruct(g_last_daily_reset, ld);
   TimeToStruct(g_last_hourly_reset, lh);

   if(ct.day != ld.day)
   {
      Print("DAY P&L: ", DoubleToString(AccountBalance() - g_daily_start_bal, 2));
      g_daily_start_bal = AccountBalance();
      g_last_daily_reset = TimeCurrent();
   }
   if(ct.hour != lh.hour)
   {
      double hp = AccountBalance() - g_hourly_start_bal;
      if(MathAbs(hp) > 0.01)
         Print("HOUR P&L: ", DoubleToString(hp, 2));
      g_hourly_start_bal = AccountBalance();
      g_last_hourly_reset = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| SPREAD ANALYSIS                                                   |
//+------------------------------------------------------------------+
void AnalyzeSpread()
{
   double spread_pts = MarketInfo(Symbol(), MODE_SPREAD);
   double spread_pips = spread_pts * Point / 10.0;
   double atr = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double max_pips = (atr * MaxSpreadPercent) / Point / 10.0;

   g_spread_data.current_pips = spread_pips;
   g_spread_data.max_allowed_pips = max_pips;
   g_spread_data.acceptable = (spread_pips <= max_pips);
}

//+------------------------------------------------------------------+
//| SESSION ANALYSIS                                                  |
//+------------------------------------------------------------------+
void AnalyzeSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   int h = dt.hour;

   if(h >= 0 && h < 8)       { g_session = SESSION_ASIAN;   g_sess_data.session_name = "Asian";          g_sess_data.is_tradeable = TradeAsianSession; g_sess_data.expected_volatility = 0.5; }
   else if(h >= 8 && h < 13) { g_session = SESSION_LONDON;  g_sess_data.session_name = "London";         g_sess_data.is_tradeable = TradeLondonSession; g_sess_data.expected_volatility = 1.2; }
   else if(h >= 13 && h < 16){ g_session = SESSION_OVERLAP; g_sess_data.session_name = "London-NY";      g_sess_data.is_tradeable = (TradeLondonSession && TradeNYSession); g_sess_data.expected_volatility = 1.5; }
   else if(h >= 16 && h < 21){ g_session = SESSION_NY;      g_sess_data.session_name = "New York";       g_sess_data.is_tradeable = TradeNYSession; g_sess_data.expected_volatility = 1.1; }
   else                       { g_session = SESSION_CLOSED;  g_sess_data.session_name = "After Hours";    g_sess_data.is_tradeable = false; g_sess_data.expected_volatility = 0.3; }
   g_sess_data.current_session = g_session;
}

//+------------------------------------------------------------------+
//| VOLATILITY REGIME                                                 |
//+------------------------------------------------------------------+
void AnalyzeVolatilityRegime()
{
   double atr_now = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double atr_sum = 0;
   for(int i = 0; i < 100; i++) atr_sum += iATR(Symbol(), PreferredTimeframe, 14, i);
   double atr_avg = atr_sum / 100;
   double ratio = (atr_avg > 0) ? atr_now / atr_avg : 1.0;

   g_atr_data.atr_current = atr_now;
   g_atr_data.atr_average = atr_avg;
   g_atr_data.ratio = ratio;

   if(ratio < 0.7)      g_volatility = VOL_LOW;
   else if(ratio > 1.5)  g_volatility = VOL_HIGH;
   else                   g_volatility = VOL_NORMAL;
   g_atr_data.regime = g_volatility;

   if(g_volatility == VOL_HIGH)
   {
      g_dyn_risk = BaseRiskPercent * g_aggression.risk_multiplier * 0.5;
      g_dyn_confluence = g_aggression.confluence_required + 1;
   }
}

//+------------------------------------------------------------------+
//| MARKET REGIME & BIAS                                              |
//+------------------------------------------------------------------+
void DetectMarketRegime()
{
   double ema0 = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema10 = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 10);
   double slope = (ema0 - ema10) / 10;

   double atr_sum = 0;
   for(int i = 0; i < 10; i++) atr_sum += iATR(Symbol(), PreferredTimeframe, 14, i);
   double atr_ratio = iATR(Symbol(), PreferredTimeframe, 14, 0) / (atr_sum / 10);

   if(MathAbs(slope) > 0.0001 && atr_ratio > 0.8)       g_regime = REGIME_TREND;
   else if(MathAbs(slope) < 0.00005 && atr_ratio < 1.1)  g_regime = REGIME_RANGE;
   else                                                    g_regime = REGIME_TRANSITION;
}

void DetermineBias()
{
   double ema = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double cp = iClose(Symbol(), PreferredTimeframe, 1);

   if(g_regime == REGIME_TREND)
   {
      g_bias = (cp > ema) ? BIAS_BULLISH : BIAS_BEARISH;
   }
   else if(g_regime == REGIME_RANGE)
   {
      double rh = GetRangeHigh(50), rl = GetRangeLow(50), rs = rh - rl;
      if(cp < rl + rs * 0.2)      g_bias = BIAS_BULLISH;
      else if(cp > rh - rs * 0.2) g_bias = BIAS_BEARISH;
      else                         g_bias = BIAS_NEUTRAL;
   }
   else g_bias = BIAS_NEUTRAL;
}

void UpdateMarketStructure()
{
   double sh = GetSwingHigh(20), sl = GetSwingLow(20);
   if(sh > g_structure.last_HH && sl > g_structure.last_HL)
   { g_structure.structure = "BULLISH"; g_structure.last_HH = sh; g_structure.last_HL = sl; }
   else if(sh < g_structure.last_LH && sl < g_structure.last_LL)
   { g_structure.structure = "BEARISH"; g_structure.last_LH = sh; g_structure.last_LL = sl; }
   else g_structure.structure = "CHOPPY";
}

//+------------------------------------------------------------------+
//| REGIME-SPECIFIC STRATEGY (FIX #19)                                |
//+------------------------------------------------------------------+
void ApplyRegimeStrategy()
{
   if(!g_has_pattern) return;
   switch(g_regime)
   {
      case REGIME_TREND:
         g_dyn_confluence = 3;
         g_dyn_tp1 = TP1_RiskReward;
         if((g_bias == BIAS_BULLISH && !g_pattern.is_bullish) ||
            (g_bias == BIAS_BEARISH && g_pattern.is_bullish))
         {
            Print("Counter-trend REJECTED in trending market");
            g_has_pattern = false;
         }
         break;
      case REGIME_RANGE:
         g_dyn_confluence = 4;
         g_dyn_tp1 = 1.5;
         if(g_bias == BIAS_NEUTRAL)
         {
            Print("Middle of range - waiting for extremes");
            g_has_pattern = false;
         }
         break;
      case REGIME_TRANSITION:
         g_dyn_confluence = 5;
         break;
   }
}

//+------------------------------------------------------------------+
//| LIQUIDITY MAPPING                                                 |
//+------------------------------------------------------------------+
void MapLiquidityZones()
{
   g_liq_count = 0;
   int lb = 20;
   for(int i = lb; i < 100 && g_liq_count < 100; i++)
   {
      double hi = iHigh(Symbol(), PreferredTimeframe, i);
      double lo = iLow(Symbol(), PreferredTimeframe, i);
      datetime t = iTime(Symbol(), PreferredTimeframe, i);

      bool is_sh = true;
      for(int j = 1; j <= lb; j++)
      {
         if(i-j<0 || i+j>=iBars(Symbol(), PreferredTimeframe)) { is_sh=false; break; }
         if(iHigh(Symbol(), PreferredTimeframe, i-j)>=hi || iHigh(Symbol(), PreferredTimeframe, i+j)>=hi) { is_sh=false; break; }
      }
      if(is_sh) { g_liq_zones[g_liq_count].price=hi; g_liq_zones[g_liq_count].is_high=true; g_liq_zones[g_liq_count].time=t; g_liq_zones[g_liq_count].swept=false; g_liq_count++; }

      bool is_sl = true;
      for(int j = 1; j <= lb; j++)
      {
         if(i-j<0 || i+j>=iBars(Symbol(), PreferredTimeframe)) { is_sl=false; break; }
         if(iLow(Symbol(), PreferredTimeframe, i-j)<=lo || iLow(Symbol(), PreferredTimeframe, i+j)<=lo) { is_sl=false; break; }
      }
      if(is_sl && g_liq_count<100) { g_liq_zones[g_liq_count].price=lo; g_liq_zones[g_liq_count].is_high=false; g_liq_zones[g_liq_count].time=t; g_liq_zones[g_liq_count].swept=false; g_liq_count++; }
   }
}

void DetectFairValueGaps()
{
   g_fvg_count = 0;
   double mg = 5 * Point * 10;
   for(int i = 1; i < 50 && g_fvg_count < 50; i++)
   {
      double h1=iHigh(Symbol(),PreferredTimeframe,i+1), l3=iLow(Symbol(),PreferredTimeframe,i-1);
      double l1=iLow(Symbol(),PreferredTimeframe,i+1), h3=iHigh(Symbol(),PreferredTimeframe,i-1);

      if(l3>h1 && (l3-h1)>=mg) { g_fvg_zones[g_fvg_count].top=l3; g_fvg_zones[g_fvg_count].bottom=h1; g_fvg_zones[g_fvg_count].time=iTime(Symbol(),PreferredTimeframe,i); g_fvg_zones[g_fvg_count].is_bullish=true; g_fvg_zones[g_fvg_count].filled=false; g_fvg_count++; }
      if(h3<l1 && (l1-h3)>=mg && g_fvg_count<50) { g_fvg_zones[g_fvg_count].top=l1; g_fvg_zones[g_fvg_count].bottom=h3; g_fvg_zones[g_fvg_count].time=iTime(Symbol(),PreferredTimeframe,i); g_fvg_zones[g_fvg_count].is_bullish=false; g_fvg_zones[g_fvg_count].filled=false; g_fvg_count++; }
   }
}

void DetectOrderBlocks()
{
   g_ob_count = 0;
   for(int i = 2; i < 100 && g_ob_count < 50; i++)
   {
      double cp=iClose(Symbol(),PreferredTimeframe,i), op=iOpen(Symbol(),PreferredTimeframe,i), cc=iClose(Symbol(),PreferredTimeframe,i-1);
      if(cp<op && cc>cp) { g_ob_zones[g_ob_count].top=MathMax(op,cp); g_ob_zones[g_ob_count].bottom=MathMin(op,cp); g_ob_zones[g_ob_count].time=iTime(Symbol(),PreferredTimeframe,i); g_ob_zones[g_ob_count].is_bullish=true; g_ob_zones[g_ob_count].test_count=0; g_ob_zones[g_ob_count].invalidated=false; g_ob_count++; }
      if(cp>op && cc<cp && g_ob_count<50) { g_ob_zones[g_ob_count].top=MathMax(op,cp); g_ob_zones[g_ob_count].bottom=MathMin(op,cp); g_ob_zones[g_ob_count].time=iTime(Symbol(),PreferredTimeframe,i); g_ob_zones[g_ob_count].is_bullish=false; g_ob_zones[g_ob_count].test_count=0; g_ob_zones[g_ob_count].invalidated=false; g_ob_count++; }
   }
   if(UseOrderBlockInvalidation)
   {
      double price = iClose(Symbol(), PreferredTimeframe, 0);
      for(int i = 0; i < g_ob_count; i++)
      {
         if(!g_ob_zones[i].invalidated && price >= g_ob_zones[i].bottom && price <= g_ob_zones[i].top)
         {
            g_ob_zones[i].test_count++;
            if(g_ob_zones[i].test_count >= MaxOBTests) g_ob_zones[i].invalidated = true;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| CANDLESTICK PATTERN DETECTION - ALL 15+ PATTERNS                  |
//+------------------------------------------------------------------+
void ScanForCandlestickPatterns()
{
   g_has_pattern = false;

   double o1=iOpen(Symbol(),PreferredTimeframe,1), h1=iHigh(Symbol(),PreferredTimeframe,1);
   double l1=iLow(Symbol(),PreferredTimeframe,1), c1=iClose(Symbol(),PreferredTimeframe,1);
   double o2=iOpen(Symbol(),PreferredTimeframe,2), h2=iHigh(Symbol(),PreferredTimeframe,2);
   double l2=iLow(Symbol(),PreferredTimeframe,2), c2=iClose(Symbol(),PreferredTimeframe,2);
   double o3=iOpen(Symbol(),PreferredTimeframe,3), h3=iHigh(Symbol(),PreferredTimeframe,3);
   double l3=iLow(Symbol(),PreferredTimeframe,3), c3=iClose(Symbol(),PreferredTimeframe,3);

   double body1=MathAbs(c1-o1), range1=h1-l1, body2=MathAbs(c2-o2), body3=MathAbs(c3-o3);
   if(range1 < Point) return;

   double uw1=h1-MathMax(o1,c1), lw1=MathMin(o1,c1)-l1;
   double br = body1 / range1;

   // --- HAMMER (Bullish) ---
   if(lw1 > body1*2.0 && uw1 < body1*0.3 && body1 > 0 && br < 0.4)
   { SetPattern("HAMMER", true, (lw1>body1*3.0)?5:4, l1); return; }

   // --- SHOOTING STAR (Bearish) ---
   if(uw1 > body1*2.0 && lw1 < body1*0.3 && body1 > 0 && br < 0.4)
   { SetPattern("SHOOTING STAR", false, (uw1>body1*3.0)?5:4, h1); return; }

   // --- BULLISH ENGULFING ---
   if(o2>c2 && c1>o1 && c1>o2 && o1<c2)
   { SetPattern("BULLISH ENGULFING", true, 5, c1); return; }

   // --- BEARISH ENGULFING ---
   if(c2>o2 && o1>c1 && o1>c2 && c1<o2)
   { SetPattern("BEARISH ENGULFING", false, 5, c1); return; }

   // --- MORNING STAR (3-candle bullish reversal) ---
   if(o3>c3 && body2<body3*0.5 && c1>o1 && c1>(o3+c3)/2)
   { SetPattern("MORNING STAR", true, 5, c1); return; }

   // --- EVENING STAR (3-candle bearish reversal) ---
   if(c3>o3 && body2<body3*0.5 && o1>c1 && c1<(o3+c3)/2)
   { SetPattern("EVENING STAR", false, 5, c1); return; }

   // --- THREE WHITE SOLDIERS ---
   if(c3>o3 && c2>o2 && c1>o1 && c2>c3 && c1>c2 && o2>o3 && o2<c3 && o1>o2 && o1<c2)
   { SetPattern("THREE WHITE SOLDIERS", true, 5, c1); return; }

   // --- THREE BLACK CROWS ---
   if(o3>c3 && o2>c2 && o1>c1 && c2<c3 && c1<c2 && o2<o3 && o2>c3 && o1<o2 && o1>c2)
   { SetPattern("THREE BLACK CROWS", false, 5, c1); return; }

   // --- BULLISH MARUBOZU ---
   if(uw1 < range1*0.05 && lw1 < range1*0.05 && body1 > range1*0.85 && c1 > o1)
   { SetPattern("BULLISH MARUBOZU", true, 5, h1); return; }

   // --- BEARISH MARUBOZU ---
   if(uw1 < range1*0.05 && lw1 < range1*0.05 && body1 > range1*0.85 && c1 < o1)
   { SetPattern("BEARISH MARUBOZU", false, 5, l1); return; }

   // --- BULLISH HARAMI ---
   if(o2>c2 && c1>o1 && o1>c2 && c1<o2 && body1<body2*0.5)
   { SetPattern("BULLISH HARAMI", true, 4, c1); return; }

   // --- BEARISH HARAMI ---
   if(c2>o2 && o1>c1 && c1>o2 && o1<c2 && body1<body2*0.5)
   { SetPattern("BEARISH HARAMI", false, 4, c1); return; }

   // --- THREE INSIDE UP ---
   if(o3>c3 && c2>o2 && o2>c3 && c2<o3 && c1>o1 && c1>c2)
   { SetPattern("THREE INSIDE UP", true, 4, c1); return; }

   // --- THREE INSIDE DOWN ---
   if(c3>o3 && o2>c2 && c2>o3 && o2<c3 && o1>c1 && c1<c2)
   { SetPattern("THREE INSIDE DOWN", false, 4, c1); return; }

   // --- PIERCING LINE ---
   if(o2>c2 && c1>o1 && o1<c2 && c1>(o2+c2)/2 && c1<o2)
   { SetPattern("PIERCING LINE", true, 4, c1); return; }

   // --- DARK CLOUD COVER ---
   if(c2>o2 && o1>c1 && o1>c2 && c1<(o2+c2)/2 && c1>o2)
   { SetPattern("DARK CLOUD COVER", false, 4, c1); return; }

   // --- DRAGONFLY DOJI ---
   if(br < 0.1 && uw1 < range1*0.1 && lw1 > range1*0.6)
   { SetPattern("DRAGONFLY DOJI", true, 4, l1); return; }

   // --- GRAVESTONE DOJI ---
   if(br < 0.1 && lw1 < range1*0.1 && uw1 > range1*0.6)
   { SetPattern("GRAVESTONE DOJI", false, 4, h1); return; }

   // --- TWEEZER BOTTOM ---
   double tol = iATR(Symbol(), PreferredTimeframe, 14, 0) * 0.1;
   if(MathAbs(l1-l2) < tol && l1 < l2 + tol)
   { SetPattern("TWEEZER BOTTOM", true, 3, l1); return; }

   // --- TWEEZER TOP ---
   if(MathAbs(h1-h2) < tol && h1 > h2 - tol)
   { SetPattern("TWEEZER TOP", false, 3, h1); return; }

   // --- SPINNING TOP ---
   if(br < 0.3 && uw1 > body1 && lw1 > body1 && body1 > 0)
   { SetPattern("SPINNING TOP", (g_bias==BIAS_BULLISH), 3, c1); return; }

   // --- DOJI ---
   if(br < 0.1)
   { SetPattern("DOJI", (g_bias==BIAS_BULLISH), 3, c1); return; }
}

void SetPattern(string name, bool bullish, int str, double price)
{
   g_pattern.name = name;
   g_pattern.is_bullish = bullish;
   g_pattern.strength = str;
   g_pattern.price = price;
   g_pattern.detected_time = TimeCurrent();
   g_pattern.bar_index = 1;
   g_has_pattern = true;
}

//+------------------------------------------------------------------+
//| SCAN LOWER TIMEFRAMES                                             |
//+------------------------------------------------------------------+
void ScanLowerTimeframes()
{
   g_has_pattern_h1 = ScanTF(PERIOD_H1, g_pattern_h1);
   g_has_pattern_m15 = ScanTF(PERIOD_M15, g_pattern_m15);
}

bool ScanTF(int tf, PatternInfo &p)
{
   double o1=iOpen(Symbol(),tf,1), h1=iHigh(Symbol(),tf,1), l1=iLow(Symbol(),tf,1), c1=iClose(Symbol(),tf,1);
   double o2=iOpen(Symbol(),tf,2), c2=iClose(Symbol(),tf,2);
   double body1=MathAbs(c1-o1), body2=MathAbs(c2-o2), range1=h1-l1;
   if(range1 < Point) return false;

   double uw=h1-MathMax(o1,c1), lw=MathMin(o1,c1)-l1;

   // Hammer
   if(lw>body1*2 && uw<body1*0.3 && body1>0) { p.name="HAMMER"; p.is_bullish=true; p.strength=(lw>body1*3)?5:4; p.price=l1; p.detected_time=TimeCurrent(); return true; }
   // Shooting Star
   if(uw>body1*2 && lw<body1*0.3 && body1>0) { p.name="SHOOTING STAR"; p.is_bullish=false; p.strength=(uw>body1*3)?5:4; p.price=h1; p.detected_time=TimeCurrent(); return true; }
   // Engulfing
   if(o2>c2 && c1>o1 && c1>o2 && o1<c2) { p.name="BULLISH ENGULFING"; p.is_bullish=true; p.strength=5; p.price=c1; p.detected_time=TimeCurrent(); return true; }
   if(c2>o2 && o1>c1 && o1>c2 && c1<o2) { p.name="BEARISH ENGULFING"; p.is_bullish=false; p.strength=5; p.price=c1; p.detected_time=TimeCurrent(); return true; }

   return false;
}

bool IsPatternValid()
{
   int bars = iBarShift(Symbol(), PreferredTimeframe, g_pattern.detected_time, false);
   return (bars <= PatternExpiryBars);
}

//+------------------------------------------------------------------+
//| VOLUME ANALYSIS                                                   |
//+------------------------------------------------------------------+
void AnalyzeVolume()
{
   long cv = iVolume(Symbol(), PreferredTimeframe, 1);
   double vs = 0;
   for(int i = 1; i <= 20; i++) vs += (double)iVolume(Symbol(), PreferredTimeframe, i);
   double av = vs / 20;
   g_vol_data.current_volume = (double)cv;
   g_vol_data.average_volume = av;
   g_vol_data.volume_ratio = (av > 0) ? cv / av : 0;
   g_vol_data.above_threshold = (g_vol_data.volume_ratio >= MinVolumeMultiplier);
   g_vol_data.spike_detected = (g_vol_data.volume_ratio >= 2.0);
}

//+------------------------------------------------------------------+
//| MTF / CORRELATION / LIQUIDITY / RETAIL TRAP                       |
//+------------------------------------------------------------------+
bool CheckMTFAlignment()
{
   int htf = GetHigherTF(PreferredTimeframe);
   double ema = iMA(Symbol(), htf, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price = iClose(Symbol(), htf, 0);
   if(g_pattern.is_bullish && price < ema) return false;
   if(!g_pattern.is_bullish && price > ema) return false;
   return true;
}

bool CheckCorrelation()
{
   string base = StringSubstr(Symbol(), 0, 3), quote = StringSubstr(Symbol(), 3, 3);
   double net = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber || OrderType() > OP_SELL) continue;
      string s = OrderSymbol(), sb = StringSubstr(s,0,3), sq = StringSubstr(s,3,3);
      int dir = (OrderType()==OP_BUY)?1:-1;
      if(sb==base||sq==quote||sb==quote||sq==base)
         net += OrderLots() * dir;
   }
   return (MathAbs(net) <= MaxCorrelationExposure * 10);
}

bool CheckLiquiditySweep(bool is_buy)
{
   double ch=iHigh(Symbol(),PreferredTimeframe,1), cl=iLow(Symbol(),PreferredTimeframe,1), cc=iClose(Symbol(),PreferredTimeframe,1);
   for(int i = 0; i < g_liq_count; i++)
   {
      if(is_buy && !g_liq_zones[i].is_high && cl<g_liq_zones[i].price && cc>g_liq_zones[i].price) { g_liq_zones[i].swept=true; return true; }
      if(!is_buy && g_liq_zones[i].is_high && ch>g_liq_zones[i].price && cc<g_liq_zones[i].price) { g_liq_zones[i].swept=true; return true; }
   }
   return false;
}

bool DetectRetailTrap()
{
   double h1=iHigh(Symbol(),PreferredTimeframe,1), c1=iClose(Symbol(),PreferredTimeframe,1);
   double res = 0;
   for(int i=0;i<g_liq_count;i++)
      if(g_liq_zones[i].is_high && g_liq_zones[i].price>c1 && (res==0||g_liq_zones[i].price<res))
         res = g_liq_zones[i].price;
   if(res==0) return false;
   return (h1>res && c1<res && g_vol_data.volume_ratio>2.0);
}

//+------------------------------------------------------------------+
//| CONFLUENCE EVALUATION - ALL 10 FACTORS FROM MQL5                  |
//+------------------------------------------------------------------+
TradeDecisionInfo EvaluateDecision()
{
   TradeDecisionInfo d;
   d.confluence_score = 0;
   d.passed_count = 0;
   d.failed_count = 0;

   // 1. Market Regime
   if(g_regime != REGIME_TRANSITION) { d.confluence_score++; d.passed_count++; } else d.failed_count++;

   // 2. Bias Alignment
   if((g_bias==BIAS_BULLISH && g_pattern.is_bullish)||(g_bias==BIAS_BEARISH && !g_pattern.is_bullish)) { d.confluence_score++; d.passed_count++; } else d.failed_count++;

   // 3. Volume
   if(UseVolumeFilter && g_vol_data.above_threshold) { d.confluence_score++; d.passed_count++; } else if(UseVolumeFilter) d.failed_count++;

   // 4. Spread
   if(UseSpreadFilter && g_spread_data.acceptable) { d.confluence_score++; d.passed_count++; } else if(UseSpreadFilter) d.failed_count++;

   // 5. Session
   if(UseSessionFilter && g_sess_data.is_tradeable) { d.confluence_score++; d.passed_count++; } else if(UseSessionFilter) d.failed_count++;

   // 6. MTF
   if(UseMTFConfirmation && g_mtf_ok) { d.confluence_score++; d.passed_count++; } else if(UseMTFConfirmation) d.failed_count++;

   // 7. Correlation
   if(UseCorrelationFilter && g_correlation_ok) { d.confluence_score++; d.passed_count++; } else if(UseCorrelationFilter) d.failed_count++;

   // 8. Pattern Strength (high = 4+)
   if(g_pattern.strength >= 4) { d.confluence_score++; d.passed_count++; } else d.failed_count++;

   // 9. Historical Performance
   if(UsePatternTracking && CheckPatternHistory()) { d.confluence_score++; d.passed_count++; } else if(UsePatternTracking) d.failed_count++;

   // 10. Market Structure alignment
   if(UseMarketStructure)
   {
      if((g_pattern.is_bullish && g_structure.structure=="BULLISH") || (!g_pattern.is_bullish && g_structure.structure=="BEARISH"))
      { d.confluence_score++; d.passed_count++; }
      else d.failed_count++;
   }

   if(d.confluence_score >= g_dyn_confluence)      { d.decision = DECISION_ENTER; d.reason = "Confluence met"; }
   else if(d.confluence_score == g_dyn_confluence-1){ d.decision = DECISION_WAIT;  d.reason = "Need 1 more"; }
   else                                             { d.decision = DECISION_SKIP;  d.reason = "Insufficient"; }

   return d;
}

//+------------------------------------------------------------------+
//| PATTERN HISTORY (FIX #17)                                         |
//+------------------------------------------------------------------+
bool CheckPatternHistory()
{
   for(int i = 0; i < g_perf_count; i++)
   {
      if(g_perf[i].pattern_name == g_pattern.name && g_perf[i].regime == g_regime)
      {
         if(g_perf[i].total_trades < 30) return true;
         return (g_perf[i].win_rate >= 0.5);
      }
   }
   return true;
}

//+------------------------------------------------------------------+
//| PARAMETER ADAPTATION (FIX #18)                                    |
//+------------------------------------------------------------------+
void AdaptParameters()
{
   if(g_consecutive_losses >= 3)
      g_dyn_confluence = MathMin(g_dyn_confluence + 1, 5);
   if(g_consecutive_wins >= 5)
      g_dyn_confluence = MathMax(g_dyn_confluence - 1, 3);
}

//+------------------------------------------------------------------+
//| SLIPPAGE MODEL (FIX #3)                                           |
//+------------------------------------------------------------------+
double CalcSlippage()
{
   double atr = iATR(Symbol(), PreferredTimeframe, 14, 0);
   return atr * ExpectedSlippagePercent;
}

//+------------------------------------------------------------------+
//| RISK CHECKS                                                       |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   double dl = ((g_daily_start_bal - AccountBalance()) / g_daily_start_bal) * 100.0;
   if(dl >= DailyLossLimit) { Print("DAILY LOSS LIMIT: ", DoubleToString(dl,1), "%"); return false; }

   double wl = ((g_weekly_start_bal - AccountBalance()) / g_weekly_start_bal) * 100.0;
   if(wl >= WeeklyLossLimit) { Print("WEEKLY LOSS LIMIT: ", DoubleToString(wl,1), "%"); return false; }

   int total = CountAllTrades();
   if(total >= g_aggression.max_trades) { Print("MAX TOTAL TRADES: ", total, "/", g_aggression.max_trades); return false; }

   return true;
}

int CountAllTrades()
{
   int c = 0;
   for(int i = 0; i < OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderMagicNumber()==MagicNumber && OrderType()<=OP_SELL) c++;
   return c;
}

int CountSymbolTrades(string sym)
{
   int c = 0;
   for(int i = 0; i < OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderMagicNumber()==MagicNumber && OrderType()<=OP_SELL && OrderSymbol()==sym) c++;
   return c;
}

//+------------------------------------------------------------------+
//| DYNAMIC RISK (FIX #10)                                            |
//+------------------------------------------------------------------+
double CalcDynamicRisk()
{
   double r = BaseRiskPercent;
   if(AccountBalance() > g_peak_balance) g_peak_balance = AccountBalance();
   double dd = (g_peak_balance > 0) ? (g_peak_balance - AccountBalance()) / g_peak_balance : 0;

   if(dd > 0.05) r *= (1.0 - dd);
   if(g_consecutive_losses >= 2) r *= 0.5;
   if(g_volatility == VOL_HIGH) r *= 0.5;

   return MathMax(r, 0.1);
}

//+------------------------------------------------------------------+
//| LOT SIZE NORMALIZATION                                            |
//+------------------------------------------------------------------+
double NormalizeLot(double lot, double intended_risk, double sl_pips)
{
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   double bmin = MarketInfo(Symbol(), MODE_MINLOT);
   double bmax = MarketInfo(Symbol(), MODE_MAXLOT);

   double nl = MathFloor(lot / step) * step;
   if(nl < bmin)
   {
      nl = bmin;
      double tv = MarketInfo(Symbol(), MODE_TICKVALUE);
      double ts = MarketInfo(Symbol(), MODE_TICKSIZE);
      if(ts > 0 && AccountBalance() > 0)
      {
         double rpl = (sl_pips * Point / ts) * tv;
         double ar = (nl * rpl / AccountBalance()) * 100.0;
         Print("LOT MIN-ADJUSTED: ", DoubleToString(bmin,2), " Risk: ", DoubleToString(intended_risk,2), "% -> ", DoubleToString(ar,2), "%");
         if(ar > intended_risk * 3) Print("RISK WARNING: ", DoubleToString(ar,2), "% exceeds 3x intended!");
      }
   }
   if(nl > bmax) nl = bmax;
   return nl;
}

double CalcLotSize(double sl_pips, double risk_pct)
{
   double bmin = MarketInfo(Symbol(), MODE_MINLOT);

   if(PositionSizingMode == LOT_SIZE_RANGE)
   {
      double lot = (MinLotSize < bmin) ? bmin : MinLotSize;
      lot = NormalizeLot(lot, risk_pct, sl_pips);
      if(lot > MaxLotSize && MaxLotSize >= bmin) lot = MaxLotSize;
      return lot;
   }
   else
   {
      double cap = AccountBalance() * (risk_pct / 100.0);
      double tv = MarketInfo(Symbol(), MODE_TICKVALUE);
      double ts = MarketInfo(Symbol(), MODE_TICKSIZE);
      if(ts <= 0 || tv <= 0) return bmin;

      double rpl = (sl_pips * Point / ts) * tv;
      double lot = (rpl > 0) ? cap / rpl : bmin;
      return NormalizeLot(lot, risk_pct, sl_pips);
   }
}

//+------------------------------------------------------------------+
//| TRADE EXECUTION                                                   |
//+------------------------------------------------------------------+
void ExecuteTrade(double risk_pct, double slippage)
{
   bool is_buy = g_pattern.is_bullish;
   double entry = is_buy ? Ask : Bid;

   // Apply slippage
   entry += is_buy ? slippage : -slippage;

   double sl = CalcStopLoss(is_buy);
   double sl_pips = MathAbs(entry - sl) / Point;
   double lot = CalcLotSize(sl_pips, risk_pct);

   double sl_dist = MathAbs(entry - sl);
   double tp1 = entry + (is_buy?1:-1) * sl_dist * g_dyn_tp1;

   sl = NormalizeDouble(sl, Digits);
   tp1 = NormalizeDouble(tp1, Digits);

   Print("═══ TRADE ═══ ", (is_buy?"BUY":"SELL"), " ", Symbol(),
         " | Lots: ", DoubleToString(lot,2),
         " | Entry: ", DoubleToString(entry, Digits),
         " | SL: ", DoubleToString(sl, Digits),
         " | TP: ", DoubleToString(tp1, Digits),
         " | Risk: ", DoubleToString(risk_pct,2), "%");

   string comment = "IGTR4|" + g_pattern.name + "|L" + IntegerToString(AggressionLevel);
   int ticket = -1;

   if(is_buy)
      ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 10, sl, tp1, comment, MagicNumber, 0, clrGreen);
   else
      ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 10, sl, tp1, comment, MagicNumber, 0, clrRed);

   if(ticket > 0)
   {
      Print("EXECUTED #", ticket);
      g_has_pattern = false;
      g_consecutive_losses = 0;
   }
   else
      Print("FAILED Error: ", GetLastError());
}

double CalcStopLoss(bool is_buy)
{
   double atr = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double sl_dist = atr * StopLossATR;
   double ep = g_pattern.price;

   if(is_buy)
   {
      double sw = GetSwingLow(20);
      return NormalizeDouble(MathMin(sw - 5*Point, ep - sl_dist), Digits);
   }
   else
   {
      double sw = GetSwingHigh(20);
      return NormalizeDouble(MathMax(sw + 5*Point, ep + sl_dist), Digits);
   }
}

//+------------------------------------------------------------------+
//| TRADE MANAGEMENT - EVERY TICK                                     |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
   for(int i = OrdersTotal()-1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol()!=Symbol() || OrderMagicNumber()!=MagicNumber || OrderType()>OP_SELL) continue;

      int ticket = OrderTicket();
      double entry = OrderOpenPrice(), sl = OrderStopLoss(), tp = OrderTakeProfit();
      double lots = OrderLots();
      bool is_buy = (OrderType()==OP_BUY);
      double price = is_buy ? Bid : Ask;

      double sl_dist = MathAbs(entry - sl);
      if(sl_dist < Point) continue;
      double profit_dist = is_buy ? (price - entry) : (entry - price);
      double r_profit = profit_dist / sl_dist;
      double cash_profit = OrderProfit() + OrderSwap() + OrderCommission();

      // PARTIAL CLOSE at TP1
      if(UsePartialClose && r_profit >= g_dyn_tp1 && lots > MarketInfo(Symbol(), MODE_MINLOT) * 1.5)
      {
         double close_lots = NormalizeDouble(lots * (PartialClosePercent / 100.0), 2);
         double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
         if(close_lots >= min_lot && (lots - close_lots) >= min_lot)
         {
            double close_price = is_buy ? Bid : Ask;
            if(OrderClose(ticket, close_lots, close_price, 10, clrYellow))
               Print("PARTIAL CLOSE: ", DoubleToString(PartialClosePercent,0), "% at ", DoubleToString(g_dyn_tp1,1), "R");
         }
      }

      // BREAKEVEN at 1R
      if(r_profit >= 1.0 && MathAbs(sl - entry) > Point * 2)
      {
         double new_sl = entry + (is_buy?1:-1) * 5 * Point;
         if(OrderModify(ticket, entry, new_sl, tp, 0, clrBlue))
            Print("BREAKEVEN #", ticket);
      }

      // PROFIT LOCK (R-based OR fixed amount)
      bool r_hit = (r_profit >= ProfitLockTrigger);
      bool fixed_hit = (cash_profit >= ProfitLockFixedAmount);
      if(UseProfitLock && (r_hit || fixed_hit))
      {
         double lock_dist = profit_dist * (ProfitLockPercent / 100.0);
         double locked_sl = is_buy ? (entry + lock_dist) : (entry - lock_dist);
         if((is_buy && locked_sl > sl) || (!is_buy && locked_sl < sl))
         {
            if(OrderModify(ticket, entry, locked_sl, tp, 0, clrGold))
               Print("PROFIT LOCKED #", ticket, " at ", r_hit ? DoubleToString(ProfitLockTrigger,1)+"R" : "$"+DoubleToString(ProfitLockFixedAmount,0));
         }
      }

      // TRAILING STOP at 1.5R
      if(r_profit >= 1.5)
      {
         if(is_buy)
         {
            double nsw = GetSwingLow(10);
            if(nsw > sl && nsw < price)
               OrderModify(ticket, entry, nsw, tp, 0, clrAqua);
         }
         else
         {
            double nsw = GetSwingHigh(10);
            if(nsw < sl && nsw > price)
               OrderModify(ticket, entry, nsw, tp, 0, clrAqua);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| ACCOUNT PROFIT LOCK                                               |
//+------------------------------------------------------------------+
void CheckAccountProfitLock()
{
   double tp = 0;
   for(int i=0;i<OrdersTotal();i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderType()<=OP_SELL)
         tp += OrderProfit()+OrderSwap()+OrderCommission();

   if(tp <= 0) return;
   double pct = (tp / AccountBalance()) * 100.0;

   if(tp >= AccountProfitLockAmount || pct >= AccountProfitLockPercent)
   {
      Print("ACCOUNT PROFIT LOCK! Profit: ", DoubleToString(tp,2), " (", DoubleToString(pct,2), "%)");
      CloseAllTrades();
      if(EnablePopupAlerts) Alert("PROFIT LOCKED: ", DoubleToString(tp,2));
      if(EnableMobileNotifications) SendNotification("PROFIT LOCKED: " + DoubleToString(tp,2));
   }
}

void CloseAllTrades()
{
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES) || OrderType()>OP_SELL) continue;
      double p = (OrderType()==OP_BUY) ? Bid : Ask;
      if(OrderClose(OrderTicket(), OrderLots(), p, 10, clrRed))
         Print("Closed #", OrderTicket());
      else
         Print("Failed close #", OrderTicket(), " Err:", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| PATTERN PERFORMANCE FILE I/O                                      |
//+------------------------------------------------------------------+
void LoadPatternPerformance()
{
   string fname = "IGTR4_Perf_L" + IntegerToString(AggressionLevel) + ".csv";
   int h = FileOpen(fname, FILE_READ|FILE_CSV|FILE_ANSI, ',');
   if(h == INVALID_HANDLE) return;
   g_perf_count = 0;
   FileReadString(h); // skip header
   while(!FileIsEnding(h) && g_perf_count < 100)
   {
      g_perf[g_perf_count].pattern_name = FileReadString(h);
      g_perf[g_perf_count].regime = (MARKET_REGIME)FileReadInteger(h);
      g_perf[g_perf_count].total_trades = FileReadInteger(h);
      g_perf[g_perf_count].winning_trades = FileReadInteger(h);
      g_perf[g_perf_count].total_pnl = FileReadDouble(h);
      g_perf[g_perf_count].win_rate = FileReadDouble(h);
      g_perf_count++;
   }
   FileClose(h);
   Print("Loaded ", g_perf_count, " performance records");
}

void SavePatternPerformance()
{
   string fname = "IGTR4_Perf_L" + IntegerToString(AggressionLevel) + ".csv";
   int h = FileOpen(fname, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(h == INVALID_HANDLE) return;
   FileWrite(h, "Pattern", "Regime", "Trades", "Wins", "PnL", "WinRate");
   for(int i = 0; i < g_perf_count; i++)
      FileWrite(h, g_perf[i].pattern_name, (int)g_perf[i].regime, g_perf[i].total_trades, g_perf[i].winning_trades, g_perf[i].total_pnl, g_perf[i].win_rate);
   FileClose(h);
}

//+------------------------------------------------------------------+
//| HELPERS                                                           |
//+------------------------------------------------------------------+
double GetSwingHigh(int lb) { double h=0; for(int i=1;i<=lb;i++){double v=iHigh(Symbol(),PreferredTimeframe,i);if(v>h)h=v;} return h; }
double GetSwingLow(int lb) { double l=DBL_MAX; for(int i=1;i<=lb;i++){double v=iLow(Symbol(),PreferredTimeframe,i);if(v<l)l=v;} return l; }
double GetRangeHigh(int lb) { return iHigh(Symbol(),PreferredTimeframe,iHighest(Symbol(),PreferredTimeframe,MODE_HIGH,lb,1)); }
double GetRangeLow(int lb) { return iLow(Symbol(),PreferredTimeframe,iLowest(Symbol(),PreferredTimeframe,MODE_LOW,lb,1)); }

int GetHigherTF(int tf)
{
   if(tf==PERIOD_M1) return PERIOD_M5; if(tf==PERIOD_M5) return PERIOD_M15;
   if(tf==PERIOD_M15) return PERIOD_H1; if(tf==PERIOD_H1) return PERIOD_H4;
   if(tf==PERIOD_H4) return PERIOD_D1; if(tf==PERIOD_D1) return PERIOD_W1;
   if(tf==PERIOD_W1) return PERIOD_MN1; return PERIOD_D1;
}
//+------------------------------------------------------------------+
