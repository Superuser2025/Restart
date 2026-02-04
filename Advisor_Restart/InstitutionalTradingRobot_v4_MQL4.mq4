//+------------------------------------------------------------------+
//|                        InstitutionalTradingRobot_v4_MQL4.mq4     |
//|                    TRADING-ONLY VERSION (No GUI/No ML Export)    |
//|                         MQL4 Conversion from MQL5 v4.0           |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Institutional Grade Trading"
#property link      "https://www.mql5.com"
#property version   "4.00"
#property description "MQL4 Trading Robot - Aggression Levels 1-5"
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
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+
input string   _1 = "═════════ CORE SETTINGS ═════════";
input bool     EnableTrading = false;                   // Enable Auto Trading
input int      PreferredTimeframe = PERIOD_H4;          // Trading Timeframe
input int      MagicNumber = 123456;                    // Magic Number

input string   _2 = "═════════ POSITION SIZING ═════════";
input ENUM_POSITION_SIZING_MODE PositionSizingMode = LOT_SIZE_RANGE;
input double   MinLotSize = 0.01;                       // Minimum Lot Size
input double   MaxLotSize = 0.10;                       // Maximum Lot Size

input string   _3 = "═════════ AGGRESSION LEVEL ═════════";
input int      AggressionLevel = 3;                     // Aggression (1=Conservative, 5=Maximum)

input string   _4 = "═════════ FILTERS ═════════";
input bool     UseVolumeFilter = true;                  // Volume Confirmation
input double   MinVolumeMultiplier = 1.5;               // Min Volume (x Average)
input bool     UseSpreadFilter = true;                  // Spread Protection
input double   MaxSpreadPercent = 0.3;                  // Max Spread (% of ATR)
input bool     UseMTFConfirmation = true;               // Multi-Timeframe Confirmation
input bool     UseSessionFilter = true;                 // Session Filtering
input bool     TradeAsianSession = false;               // Trade Asian Session
input bool     TradeLondonSession = true;               // Trade London Session
input bool     TradeNYSession = true;                   // Trade NY Session
input bool     UseCorrelationFilter = true;             // Portfolio Correlation Check
input double   MaxCorrelationExposure = 0.7;            // Max Correlation Limit
input bool     UseVolatilityAdaptation = true;          // Volatility Regime Detection
input bool     UseDynamicRisk = true;                   // Drawdown-Based Risk
input bool     UsePatternDecay = true;                  // Pattern Time Decay
input int      PatternExpiryBars = 3;                   // Pattern Valid For (Bars)
input bool     UseLiquiditySweep = true;                // Liquidity Sweep Detection
input bool     UseRetailTrap = true;                    // Retail Trap Detection
input bool     UseOrderBlockInvalidation = true;        // Order Block Invalidation
input int      MaxOBTests = 3;                          // Max Order Block Re-Tests
input bool     UseMarketStructure = true;               // Market Structure Tracking

input string   _5 = "═════════ RISK MANAGEMENT ═════════";
input double   BaseRiskPercent = 0.5;                   // Base Risk Per Trade (%)
input int      MaxOpenTrades = 3;                       // Max Concurrent Trades
input double   DailyLossLimit = 2.0;                    // Daily Loss Limit (%)
input double   WeeklyLossLimit = 5.0;                   // Weekly Loss Limit (%)
input double   StopLossATR = 2.0;                       // Stop Loss (x ATR)

input string   _6 = "═════════ TAKE PROFIT ═════════";
input double   TP1_RiskReward = 2.0;                    // Take Profit 1 (R:R)
input double   TP2_RiskReward = 3.0;                    // Take Profit 2 (R:R)
input double   TP3_RiskReward = 5.0;                    // Take Profit 3 (R:R)

input string   _7 = "═════════ PROFIT PROTECTION ═════════";
input bool     UseProfitLock = true;                    // Enable Profit Lock
input double   ProfitLockTrigger = 1.5;                 // Lock Trigger (R multiple)
input double   ProfitLockFixedAmount = 100.0;           // OR Lock at Fixed Profit
input double   ProfitLockPercent = 50.0;                // Lock % of Profit

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

struct OrderBlock
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
   string          reason;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
// Market State
MARKET_REGIME       g_current_regime = REGIME_TREND;
MARKET_BIAS         g_current_bias = BIAS_NEUTRAL;
TRADING_SESSION     g_current_session = SESSION_ASIAN;
VOLATILITY_REGIME   g_current_volatility = VOL_NORMAL;

// Pattern & Zones
PatternInfo         g_active_pattern;
bool                g_has_active_pattern = false;
LiquidityZone       g_liquidity_zones[100];
int                 g_liquidity_count = 0;
FairValueGap        g_fvg_zones[50];
int                 g_fvg_count = 0;
OrderBlock          g_order_blocks[50];
int                 g_ob_count = 0;
MarketStructure     g_market_structure;

// Analysis Data
VolumeData          g_volume_data;
SpreadData          g_spread_data;
SessionData         g_session_data;
VolatilityData      g_volatility_data;

// Aggression
AggressionSettings  g_aggression_presets[5];
AggressionSettings  g_active_aggression;

// Risk Management
double              g_daily_start_balance;
double              g_weekly_start_balance;
double              g_hourly_start_balance;
datetime            g_last_daily_reset;
datetime            g_last_weekly_reset;
datetime            g_last_hourly_reset;
int                 g_consecutive_losses = 0;
double              g_peak_balance = 0;

// Dynamic Parameters
int                 g_dynamic_confluence = 3;
double              g_dynamic_risk = 0.5;
double              g_dynamic_tp1 = 2.0;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("╔═══════════════════════════════════════════════════════════╗");
   Print("║  INSTITUTIONAL TRADING ROBOT v4.0 (MQL4)                 ║");
   Print("║  Trading-Only Version - No GUI                           ║");
   Print("╚═══════════════════════════════════════════════════════════╝");

   // Initialize aggression presets
   InitializeAggressionPresets();
   ApplyAggressionLevel();

   // Initialize risk management
   g_daily_start_balance = AccountBalance();
   g_weekly_start_balance = AccountBalance();
   g_hourly_start_balance = AccountBalance();
   g_peak_balance = AccountBalance();
   g_last_daily_reset = TimeCurrent();
   g_last_weekly_reset = TimeCurrent();
   g_last_hourly_reset = TimeCurrent();

   // Log symbol constraints
   LogSymbolConstraints();

   if(!EnableTrading)
      Print("WARNING: Trading is DISABLED - Indicator mode only");
   else
      Print("AUTO-TRADING ENABLED - Aggression Level ", AggressionLevel);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("═══════════════════════════════════════════════════════════");
   Print("  Institutional Trading Robot v4.0 (MQL4) Stopped");
   Print("═══════════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // P&L Reset Check
   CheckPnLResets();

   // Account-Level Profit Lock (runs every tick)
   if(UseAccountProfitLock)
      CheckAccountProfitLock();

   // Check for new bar
   static datetime last_bar_time = 0;
   datetime current_bar_time = iTime(Symbol(), PreferredTimeframe, 0);

   if(current_bar_time == last_bar_time)
      return;

   last_bar_time = current_bar_time;

   Print("═══ NEW BAR: ", TimeToString(current_bar_time), " ═══");

   //═══════════════════════════════════════════════════════════════
   // PHASE 0: PRE-FLIGHT CHECKS
   //═══════════════════════════════════════════════════════════════

   // Spread Check
   if(UseSpreadFilter)
   {
      AnalyzeSpread();
      if(!g_spread_data.acceptable)
      {
         Print("SPREAD TOO WIDE: ", DoubleToString(g_spread_data.current_pips, 1), " pips");
         return;
      }
   }

   // Session Check
   if(UseSessionFilter)
   {
      AnalyzeSession();
      if(!g_session_data.is_tradeable)
      {
         Print("Session not tradeable: ", g_session_data.session_name);
         return;
      }
   }

   //═══════════════════════════════════════════════════════════════
   // PHASE 1: MARKET CONTEXT
   //═══════════════════════════════════════════════════════════════

   if(UseVolatilityAdaptation)
      AnalyzeVolatilityRegime();

   DetectMarketRegime();
   DetermineBias();

   if(UseMarketStructure)
      UpdateMarketStructure();

   //═══════════════════════════════════════════════════════════════
   // PHASE 2: LIQUIDITY MAPPING
   //═══════════════════════════════════════════════════════════════

   MapLiquidityZones();
   DetectFairValueGaps();
   DetectOrderBlocks();

   //═══════════════════════════════════════════════════════════════
   // PHASE 3: PATTERN DETECTION
   //═══════════════════════════════════════════════════════════════

   ScanForCandlestickPatterns();

   if(!g_has_active_pattern)
   {
      Print("No valid patterns detected - Waiting...");
      return;
   }

   // Check pattern strength
   if(g_active_pattern.strength < g_active_aggression.min_pattern_strength)
   {
      Print("Pattern strength too low: ", g_active_pattern.strength, " < ", g_active_aggression.min_pattern_strength);
      g_has_active_pattern = false;
      return;
   }

   // Pattern decay check
   if(UsePatternDecay && !IsPatternValid())
   {
      Print("Pattern expired");
      g_has_active_pattern = false;
      return;
   }

   Print("PATTERN DETECTED: ", g_active_pattern.name, " [", g_active_pattern.strength, " stars]");

   //═══════════════════════════════════════════════════════════════
   // PHASE 4: INSTITUTIONAL FILTERS
   //═══════════════════════════════════════════════════════════════

   // Volume Check
   if(UseVolumeFilter)
   {
      AnalyzeVolume();
      if(!g_volume_data.above_threshold && g_active_aggression.require_volume)
      {
         Print("Volume below threshold - Required for Level ", AggressionLevel);
         g_has_active_pattern = false;
         return;
      }
   }

   // MTF Check
   if(UseMTFConfirmation)
   {
      if(!CheckMultiTimeframeAlignment() && g_active_aggression.require_mtf)
      {
         Print("MTF not aligned - Required for Level ", AggressionLevel);
         g_has_active_pattern = false;
         return;
      }
   }

   // Correlation Check
   if(UseCorrelationFilter && !CheckPortfolioCorrelation())
   {
      Print("Portfolio over-correlated");
      return;
   }

   // Liquidity Sweep Check
   if(UseLiquiditySweep)
   {
      if(CheckLiquiditySweep(g_active_pattern.is_bullish))
         Print("LIQUIDITY SWEEP confirmed!");
   }

   // Retail Trap Check
   if(UseRetailTrap && DetectRetailTrap())
   {
      Print("RETAIL TRAP detected - Skipping");
      g_has_active_pattern = false;
      return;
   }

   // Evaluate Confluence
   TradeDecisionInfo decision = EvaluateTradeDecision();

   Print("CONFLUENCE: ", decision.confluence_score, "/", g_dynamic_confluence);

   //═══════════════════════════════════════════════════════════════
   // PHASE 5: TRADE EXECUTION
   //═══════════════════════════════════════════════════════════════

   if(decision.decision == DECISION_ENTER && EnableTrading)
   {
      if(!CheckRiskLimits())
      {
         Print("Risk limit reached - Cannot trade");
         return;
      }

      double risk_percent = UseDynamicRisk ? CalculateDynamicRisk() : g_dynamic_risk;
      ExecuteTrade(risk_percent);
   }

   //═══════════════════════════════════════════════════════════════
   // PHASE 6: TRADE MANAGEMENT
   //═══════════════════════════════════════════════════════════════

   ManageOpenTrades();
}

//+------------------------------------------------------------------+
//| INITIALIZE AGGRESSION PRESETS                                     |
//+------------------------------------------------------------------+
void InitializeAggressionPresets()
{
   // Level 1: Ultra Conservative
   g_aggression_presets[0].confluence_required = 6;
   g_aggression_presets[0].risk_multiplier = 0.5;
   g_aggression_presets[0].min_pattern_strength = 4;
   g_aggression_presets[0].require_mtf = true;
   g_aggression_presets[0].require_volume = true;
   g_aggression_presets[0].max_trades = 1;
   g_aggression_presets[0].tp_multiplier = 1.5;
   g_aggression_presets[0].description = "ULTRA CONSERVATIVE";

   // Level 2: Conservative
   g_aggression_presets[1].confluence_required = 5;
   g_aggression_presets[1].risk_multiplier = 0.75;
   g_aggression_presets[1].min_pattern_strength = 3;
   g_aggression_presets[1].require_mtf = true;
   g_aggression_presets[1].require_volume = true;
   g_aggression_presets[1].max_trades = 2;
   g_aggression_presets[1].tp_multiplier = 1.8;
   g_aggression_presets[1].description = "CONSERVATIVE";

   // Level 3: Balanced
   g_aggression_presets[2].confluence_required = 4;
   g_aggression_presets[2].risk_multiplier = 1.0;
   g_aggression_presets[2].min_pattern_strength = 2;
   g_aggression_presets[2].require_mtf = true;
   g_aggression_presets[2].require_volume = false;
   g_aggression_presets[2].max_trades = 3;
   g_aggression_presets[2].tp_multiplier = 2.0;
   g_aggression_presets[2].description = "BALANCED";

   // Level 4: Aggressive
   g_aggression_presets[3].confluence_required = 3;
   g_aggression_presets[3].risk_multiplier = 1.25;
   g_aggression_presets[3].min_pattern_strength = 2;
   g_aggression_presets[3].require_mtf = false;
   g_aggression_presets[3].require_volume = false;
   g_aggression_presets[3].max_trades = 5;
   g_aggression_presets[3].tp_multiplier = 2.5;
   g_aggression_presets[3].description = "AGGRESSIVE";

   // Level 5: Maximum
   g_aggression_presets[4].confluence_required = 2;
   g_aggression_presets[4].risk_multiplier = 1.5;
   g_aggression_presets[4].min_pattern_strength = 1;
   g_aggression_presets[4].require_mtf = false;
   g_aggression_presets[4].require_volume = false;
   g_aggression_presets[4].max_trades = 8;
   g_aggression_presets[4].tp_multiplier = 3.0;
   g_aggression_presets[4].description = "MAXIMUM";
}

//+------------------------------------------------------------------+
//| APPLY AGGRESSION LEVEL                                            |
//+------------------------------------------------------------------+
void ApplyAggressionLevel()
{
   int level = MathMax(1, MathMin(5, AggressionLevel));
   g_active_aggression = g_aggression_presets[level - 1];

   g_dynamic_confluence = g_active_aggression.confluence_required;
   g_dynamic_risk = BaseRiskPercent * g_active_aggression.risk_multiplier;
   g_dynamic_tp1 = TP1_RiskReward * g_active_aggression.tp_multiplier / 2.0;

   Print("═══════════════════════════════════════════════════");
   Print("  AGGRESSION LEVEL ", level, ": ", g_active_aggression.description);
   Print("  Confluence Required: ", g_active_aggression.confluence_required);
   Print("  Risk Multiplier: ", g_active_aggression.risk_multiplier);
   Print("  Min Pattern Strength: ", g_active_aggression.min_pattern_strength);
   Print("  Max Trades: ", g_active_aggression.max_trades);
   Print("═══════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| LOG SYMBOL CONSTRAINTS                                            |
//+------------------------------------------------------------------+
void LogSymbolConstraints()
{
   double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
   double max_lot = MarketInfo(Symbol(), MODE_MAXLOT);
   double lot_step = MarketInfo(Symbol(), MODE_LOTSTEP);

   Print("═══ ", Symbol(), " LOT CONSTRAINTS ═══");
   Print("  Min Lot: ", DoubleToString(min_lot, 2));
   Print("  Max Lot: ", DoubleToString(max_lot, 2));
   Print("  Lot Step: ", DoubleToString(lot_step, 4));
}

//+------------------------------------------------------------------+
//| CHECK P&L RESETS                                                  |
//+------------------------------------------------------------------+
void CheckPnLResets()
{
   MqlDateTime current_time, last_daily, last_hourly;
   TimeToStruct(TimeCurrent(), current_time);
   TimeToStruct(g_last_daily_reset, last_daily);
   TimeToStruct(g_last_hourly_reset, last_hourly);

   // Daily reset
   if(current_time.day != last_daily.day)
   {
      double daily_pnl = AccountBalance() - g_daily_start_balance;
      Print("═══ NEW DAY: Yesterday's P&L: ", DoubleToString(daily_pnl, 2), " ═══");
      g_daily_start_balance = AccountBalance();
      g_last_daily_reset = TimeCurrent();
   }

   // Hourly reset
   if(current_time.hour != last_hourly.hour)
   {
      double hourly_pnl = AccountBalance() - g_hourly_start_balance;
      if(MathAbs(hourly_pnl) > 0.01)
         Print("Hourly P&L: ", DoubleToString(hourly_pnl, 2));
      g_hourly_start_balance = AccountBalance();
      g_last_hourly_reset = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| ANALYZE SPREAD                                                    |
//+------------------------------------------------------------------+
void AnalyzeSpread()
{
   double spread_points = MarketInfo(Symbol(), MODE_SPREAD);
   double spread_pips = spread_points * Point / 10.0;

   double atr = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double max_spread = atr * MaxSpreadPercent;
   double max_spread_pips = max_spread / Point / 10.0;

   g_spread_data.current_pips = spread_pips;
   g_spread_data.max_allowed_pips = max_spread_pips;
   g_spread_data.acceptable = (spread_pips <= max_spread_pips);
}

//+------------------------------------------------------------------+
//| ANALYZE SESSION                                                   |
//+------------------------------------------------------------------+
void AnalyzeSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   int hour = dt.hour;

   if(hour >= 0 && hour < 8)
   {
      g_current_session = SESSION_ASIAN;
      g_session_data.session_name = "Asian";
      g_session_data.is_tradeable = TradeAsianSession;
   }
   else if(hour >= 8 && hour < 13)
   {
      g_current_session = SESSION_LONDON;
      g_session_data.session_name = "London";
      g_session_data.is_tradeable = TradeLondonSession;
   }
   else if(hour >= 13 && hour < 16)
   {
      g_current_session = SESSION_OVERLAP;
      g_session_data.session_name = "London-NY Overlap";
      g_session_data.is_tradeable = (TradeLondonSession && TradeNYSession);
   }
   else if(hour >= 16 && hour < 21)
   {
      g_current_session = SESSION_NY;
      g_session_data.session_name = "New York";
      g_session_data.is_tradeable = TradeNYSession;
   }
   else
   {
      g_current_session = SESSION_CLOSED;
      g_session_data.session_name = "After Hours";
      g_session_data.is_tradeable = false;
   }

   g_session_data.current_session = g_current_session;
}

//+------------------------------------------------------------------+
//| ANALYZE VOLATILITY REGIME                                         |
//+------------------------------------------------------------------+
void AnalyzeVolatilityRegime()
{
   double atr_current = iATR(Symbol(), PreferredTimeframe, 14, 0);

   double atr_sum = 0;
   for(int i = 0; i < 100; i++)
      atr_sum += iATR(Symbol(), PreferredTimeframe, 14, i);
   double atr_avg = atr_sum / 100;

   double ratio = atr_current / atr_avg;

   g_volatility_data.atr_current = atr_current;
   g_volatility_data.atr_average = atr_avg;
   g_volatility_data.ratio = ratio;

   if(ratio < 0.7)
      g_current_volatility = VOL_LOW;
   else if(ratio > 1.5)
      g_current_volatility = VOL_HIGH;
   else
      g_current_volatility = VOL_NORMAL;

   g_volatility_data.regime = g_current_volatility;

   // Adapt parameters for high volatility
   if(g_current_volatility == VOL_HIGH)
   {
      g_dynamic_risk = BaseRiskPercent * g_active_aggression.risk_multiplier * 0.5;
      g_dynamic_confluence = g_active_aggression.confluence_required + 1;
   }
}

//+------------------------------------------------------------------+
//| DETECT MARKET REGIME                                              |
//+------------------------------------------------------------------+
void DetectMarketRegime()
{
   double ema_current = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema_10bars = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 10);

   double ema_slope = (ema_current - ema_10bars) / 10;

   double atr_current = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double atr_sum = 0;
   for(int i = 0; i < 10; i++)
      atr_sum += iATR(Symbol(), PreferredTimeframe, 14, i);
   double atr_avg = atr_sum / 10;
   double atr_ratio = atr_current / atr_avg;

   if(MathAbs(ema_slope) > 0.0001 && atr_ratio > 0.8)
      g_current_regime = REGIME_TREND;
   else if(MathAbs(ema_slope) < 0.00005 && atr_ratio < 1.1)
      g_current_regime = REGIME_RANGE;
   else
      g_current_regime = REGIME_TRANSITION;
}

//+------------------------------------------------------------------+
//| DETERMINE MARKET BIAS                                             |
//+------------------------------------------------------------------+
void DetermineBias()
{
   double ema200 = iMA(Symbol(), PreferredTimeframe, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double close_price = iClose(Symbol(), PreferredTimeframe, 1);

   if(g_current_regime == REGIME_TREND)
   {
      if(close_price > ema200)
         g_current_bias = BIAS_BULLISH;
      else
         g_current_bias = BIAS_BEARISH;
   }
   else if(g_current_regime == REGIME_RANGE)
   {
      double range_high = GetRangeHigh(50);
      double range_low = GetRangeLow(50);
      double range_size = range_high - range_low;

      if(close_price < range_low + range_size * 0.2)
         g_current_bias = BIAS_BULLISH;
      else if(close_price > range_high - range_size * 0.2)
         g_current_bias = BIAS_BEARISH;
      else
         g_current_bias = BIAS_NEUTRAL;
   }
   else
   {
      g_current_bias = BIAS_NEUTRAL;
   }
}

//+------------------------------------------------------------------+
//| UPDATE MARKET STRUCTURE                                           |
//+------------------------------------------------------------------+
void UpdateMarketStructure()
{
   double swing_high = GetSwingHigh(20);
   double swing_low = GetSwingLow(20);

   if(swing_high > g_market_structure.last_HH && swing_low > g_market_structure.last_HL)
   {
      g_market_structure.structure = "BULLISH";
      g_market_structure.last_HH = swing_high;
      g_market_structure.last_HL = swing_low;
   }
   else if(swing_high < g_market_structure.last_LH && swing_low < g_market_structure.last_LL)
   {
      g_market_structure.structure = "BEARISH";
      g_market_structure.last_LH = swing_high;
      g_market_structure.last_LL = swing_low;
   }
   else
   {
      g_market_structure.structure = "CHOPPY";
   }
}

//+------------------------------------------------------------------+
//| MAP LIQUIDITY ZONES                                               |
//+------------------------------------------------------------------+
void MapLiquidityZones()
{
   g_liquidity_count = 0;
   int lookback = 20;

   for(int i = lookback; i < 100 && g_liquidity_count < 100; i++)
   {
      double high = iHigh(Symbol(), PreferredTimeframe, i);
      double low = iLow(Symbol(), PreferredTimeframe, i);
      datetime time = iTime(Symbol(), PreferredTimeframe, i);

      // Check for swing high
      bool is_swing_high = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(i-j < 0 || i+j >= Bars)
         {
            is_swing_high = false;
            break;
         }
         if(iHigh(Symbol(), PreferredTimeframe, i-j) >= high ||
            iHigh(Symbol(), PreferredTimeframe, i+j) >= high)
         {
            is_swing_high = false;
            break;
         }
      }

      if(is_swing_high)
      {
         g_liquidity_zones[g_liquidity_count].price = high;
         g_liquidity_zones[g_liquidity_count].is_high = true;
         g_liquidity_zones[g_liquidity_count].time = time;
         g_liquidity_zones[g_liquidity_count].swept = false;
         g_liquidity_count++;
      }

      // Check for swing low
      bool is_swing_low = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(i-j < 0 || i+j >= Bars)
         {
            is_swing_low = false;
            break;
         }
         if(iLow(Symbol(), PreferredTimeframe, i-j) <= low ||
            iLow(Symbol(), PreferredTimeframe, i+j) <= low)
         {
            is_swing_low = false;
            break;
         }
      }

      if(is_swing_low && g_liquidity_count < 100)
      {
         g_liquidity_zones[g_liquidity_count].price = low;
         g_liquidity_zones[g_liquidity_count].is_high = false;
         g_liquidity_zones[g_liquidity_count].time = time;
         g_liquidity_zones[g_liquidity_count].swept = false;
         g_liquidity_count++;
      }
   }
}

//+------------------------------------------------------------------+
//| DETECT FAIR VALUE GAPS                                            |
//+------------------------------------------------------------------+
void DetectFairValueGaps()
{
   g_fvg_count = 0;
   double min_gap = 5 * Point * 10;

   for(int i = 1; i < 50 && g_fvg_count < 50; i++)
   {
      double high1 = iHigh(Symbol(), PreferredTimeframe, i+1);
      double low3 = iLow(Symbol(), PreferredTimeframe, i-1);
      double low1 = iLow(Symbol(), PreferredTimeframe, i+1);
      double high3 = iHigh(Symbol(), PreferredTimeframe, i-1);

      // Bullish FVG
      if(low3 > high1 && (low3 - high1) >= min_gap)
      {
         g_fvg_zones[g_fvg_count].top = low3;
         g_fvg_zones[g_fvg_count].bottom = high1;
         g_fvg_zones[g_fvg_count].time = iTime(Symbol(), PreferredTimeframe, i);
         g_fvg_zones[g_fvg_count].is_bullish = true;
         g_fvg_zones[g_fvg_count].filled = false;
         g_fvg_count++;
      }

      // Bearish FVG
      if(high3 < low1 && (low1 - high3) >= min_gap && g_fvg_count < 50)
      {
         g_fvg_zones[g_fvg_count].top = low1;
         g_fvg_zones[g_fvg_count].bottom = high3;
         g_fvg_zones[g_fvg_count].time = iTime(Symbol(), PreferredTimeframe, i);
         g_fvg_zones[g_fvg_count].is_bullish = false;
         g_fvg_zones[g_fvg_count].filled = false;
         g_fvg_count++;
      }
   }
}

//+------------------------------------------------------------------+
//| DETECT ORDER BLOCKS                                               |
//+------------------------------------------------------------------+
void DetectOrderBlocks()
{
   g_ob_count = 0;

   for(int i = 2; i < 100 && g_ob_count < 50; i++)
   {
      double close_prev = iClose(Symbol(), PreferredTimeframe, i);
      double open_prev = iOpen(Symbol(), PreferredTimeframe, i);
      double close_curr = iClose(Symbol(), PreferredTimeframe, i-1);

      // Bullish Order Block
      if(close_prev < open_prev && close_curr > close_prev)
      {
         g_order_blocks[g_ob_count].top = MathMax(open_prev, close_prev);
         g_order_blocks[g_ob_count].bottom = MathMin(open_prev, close_prev);
         g_order_blocks[g_ob_count].time = iTime(Symbol(), PreferredTimeframe, i);
         g_order_blocks[g_ob_count].is_bullish = true;
         g_order_blocks[g_ob_count].test_count = 0;
         g_order_blocks[g_ob_count].invalidated = false;
         g_ob_count++;
      }

      // Bearish Order Block
      if(close_prev > open_prev && close_curr < close_prev && g_ob_count < 50)
      {
         g_order_blocks[g_ob_count].top = MathMax(open_prev, close_prev);
         g_order_blocks[g_ob_count].bottom = MathMin(open_prev, close_prev);
         g_order_blocks[g_ob_count].time = iTime(Symbol(), PreferredTimeframe, i);
         g_order_blocks[g_ob_count].is_bullish = false;
         g_order_blocks[g_ob_count].test_count = 0;
         g_order_blocks[g_ob_count].invalidated = false;
         g_ob_count++;
      }
   }

   // Update invalidation
   if(UseOrderBlockInvalidation)
      UpdateOrderBlockInvalidation();
}

//+------------------------------------------------------------------+
//| UPDATE ORDER BLOCK INVALIDATION                                   |
//+------------------------------------------------------------------+
void UpdateOrderBlockInvalidation()
{
   double current_price = iClose(Symbol(), PreferredTimeframe, 0);

   for(int i = 0; i < g_ob_count; i++)
   {
      if(g_order_blocks[i].invalidated) continue;

      if(current_price >= g_order_blocks[i].bottom && current_price <= g_order_blocks[i].top)
      {
         g_order_blocks[i].test_count++;

         if(g_order_blocks[i].test_count >= MaxOBTests)
            g_order_blocks[i].invalidated = true;
      }
   }
}

//+------------------------------------------------------------------+
//| SCAN FOR CANDLESTICK PATTERNS                                     |
//+------------------------------------------------------------------+
void ScanForCandlestickPatterns()
{
   g_has_active_pattern = false;

   double o1 = iOpen(Symbol(), PreferredTimeframe, 1);
   double h1 = iHigh(Symbol(), PreferredTimeframe, 1);
   double l1 = iLow(Symbol(), PreferredTimeframe, 1);
   double c1 = iClose(Symbol(), PreferredTimeframe, 1);

   double o2 = iOpen(Symbol(), PreferredTimeframe, 2);
   double h2 = iHigh(Symbol(), PreferredTimeframe, 2);
   double l2 = iLow(Symbol(), PreferredTimeframe, 2);
   double c2 = iClose(Symbol(), PreferredTimeframe, 2);

   double body1 = MathAbs(c1 - o1);
   double range1 = h1 - l1;
   double body2 = MathAbs(c2 - o2);

   if(range1 < Point) return;

   double upper_wick = h1 - MathMax(o1, c1);
   double lower_wick = MathMin(o1, c1) - l1;
   double body_ratio = body1 / range1;

   // Hammer / Pin Bar (Bullish)
   if(body_ratio < 0.3 && lower_wick > body1 * 2 && upper_wick < body1)
   {
      g_active_pattern.name = "Bullish Pin Bar";
      g_active_pattern.is_bullish = true;
      g_active_pattern.strength = 3;
      g_active_pattern.price = c1;
      g_active_pattern.detected_time = TimeCurrent();
      g_has_active_pattern = true;
      return;
   }

   // Shooting Star / Pin Bar (Bearish)
   if(body_ratio < 0.3 && upper_wick > body1 * 2 && lower_wick < body1)
   {
      g_active_pattern.name = "Bearish Pin Bar";
      g_active_pattern.is_bullish = false;
      g_active_pattern.strength = 3;
      g_active_pattern.price = c1;
      g_active_pattern.detected_time = TimeCurrent();
      g_has_active_pattern = true;
      return;
   }

   // Bullish Engulfing
   if(c2 < o2 && c1 > o1 && body1 > body2 * 1.5 && c1 > o2 && o1 < c2)
   {
      g_active_pattern.name = "Bullish Engulfing";
      g_active_pattern.is_bullish = true;
      g_active_pattern.strength = 4;
      g_active_pattern.price = c1;
      g_active_pattern.detected_time = TimeCurrent();
      g_has_active_pattern = true;
      return;
   }

   // Bearish Engulfing
   if(c2 > o2 && c1 < o1 && body1 > body2 * 1.5 && c1 < o2 && o1 > c2)
   {
      g_active_pattern.name = "Bearish Engulfing";
      g_active_pattern.is_bullish = false;
      g_active_pattern.strength = 4;
      g_active_pattern.price = c1;
      g_active_pattern.detected_time = TimeCurrent();
      g_has_active_pattern = true;
      return;
   }

   // Doji
   if(body_ratio < 0.1)
   {
      g_active_pattern.name = "Doji";
      g_active_pattern.is_bullish = (g_current_bias == BIAS_BULLISH);
      g_active_pattern.strength = 2;
      g_active_pattern.price = c1;
      g_active_pattern.detected_time = TimeCurrent();
      g_has_active_pattern = true;
      return;
   }
}

//+------------------------------------------------------------------+
//| IS PATTERN VALID (Decay Check)                                    |
//+------------------------------------------------------------------+
bool IsPatternValid()
{
   int bars_since = iBarShift(Symbol(), PreferredTimeframe, g_active_pattern.detected_time, false);
   return (bars_since <= PatternExpiryBars);
}

//+------------------------------------------------------------------+
//| ANALYZE VOLUME                                                    |
//+------------------------------------------------------------------+
void AnalyzeVolume()
{
   long current_vol = iVolume(Symbol(), PreferredTimeframe, 1);

   double vol_sum = 0;
   for(int i = 1; i <= 20; i++)
      vol_sum += (double)iVolume(Symbol(), PreferredTimeframe, i);
   double avg_vol = vol_sum / 20;

   g_volume_data.current_volume = (double)current_vol;
   g_volume_data.average_volume = avg_vol;
   g_volume_data.volume_ratio = current_vol / avg_vol;
   g_volume_data.above_threshold = (g_volume_data.volume_ratio >= MinVolumeMultiplier);
}

//+------------------------------------------------------------------+
//| CHECK MULTI-TIMEFRAME ALIGNMENT                                   |
//+------------------------------------------------------------------+
bool CheckMultiTimeframeAlignment()
{
   int higher_tf = GetHigherTimeframe(PreferredTimeframe);

   double ema_higher = iMA(Symbol(), higher_tf, 200, 0, MODE_EMA, PRICE_CLOSE, 0);
   double price_higher = iClose(Symbol(), higher_tf, 0);

   bool higher_bullish = (price_higher > ema_higher);
   bool higher_bearish = (price_higher < ema_higher);

   if(g_active_pattern.is_bullish && higher_bearish) return false;
   if(!g_active_pattern.is_bullish && higher_bullish) return false;

   return true;
}

//+------------------------------------------------------------------+
//| CHECK PORTFOLIO CORRELATION                                       |
//+------------------------------------------------------------------+
bool CheckPortfolioCorrelation()
{
   string base_currency = StringSubstr(Symbol(), 0, 3);
   string quote_currency = StringSubstr(Symbol(), 3, 3);

   double net_exposure = 0;

   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() != MagicNumber) continue;
         if(OrderType() > OP_SELL) continue;

         string pos_symbol = OrderSymbol();
         string pos_base = StringSubstr(pos_symbol, 0, 3);
         string pos_quote = StringSubstr(pos_symbol, 3, 3);

         double lots = OrderLots();
         int direction = (OrderType() == OP_BUY) ? 1 : -1;

         if(pos_base == base_currency || pos_quote == quote_currency ||
            pos_base == quote_currency || pos_quote == base_currency)
         {
            net_exposure += lots * direction;
         }
      }
   }

   return (MathAbs(net_exposure) <= MaxCorrelationExposure * 10);
}

//+------------------------------------------------------------------+
//| CHECK LIQUIDITY SWEEP                                             |
//+------------------------------------------------------------------+
bool CheckLiquiditySweep(bool is_buy_pattern)
{
   double current_high = iHigh(Symbol(), PreferredTimeframe, 1);
   double current_low = iLow(Symbol(), PreferredTimeframe, 1);
   double current_close = iClose(Symbol(), PreferredTimeframe, 1);

   if(is_buy_pattern)
   {
      for(int i = 0; i < g_liquidity_count; i++)
      {
         if(!g_liquidity_zones[i].is_high)
         {
            double prev_low = g_liquidity_zones[i].price;
            if(current_low < prev_low && current_close > prev_low)
            {
               g_liquidity_zones[i].swept = true;
               return true;
            }
         }
      }
   }
   else
   {
      for(int i = 0; i < g_liquidity_count; i++)
      {
         if(g_liquidity_zones[i].is_high)
         {
            double prev_high = g_liquidity_zones[i].price;
            if(current_high > prev_high && current_close < prev_high)
            {
               g_liquidity_zones[i].swept = true;
               return true;
            }
         }
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| DETECT RETAIL TRAP                                                |
//+------------------------------------------------------------------+
bool DetectRetailTrap()
{
   double high1 = iHigh(Symbol(), PreferredTimeframe, 1);
   double close1 = iClose(Symbol(), PreferredTimeframe, 1);

   double resistance = 0;
   for(int i = 0; i < g_liquidity_count; i++)
   {
      if(g_liquidity_zones[i].is_high && g_liquidity_zones[i].price > close1)
      {
         if(resistance == 0 || g_liquidity_zones[i].price < resistance)
            resistance = g_liquidity_zones[i].price;
      }
   }

   if(resistance == 0) return false;

   if(high1 > resistance && close1 < resistance && g_volume_data.volume_ratio > 2.0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| EVALUATE TRADE DECISION                                           |
//+------------------------------------------------------------------+
TradeDecisionInfo EvaluateTradeDecision()
{
   TradeDecisionInfo decision;
   decision.confluence_score = 0;

   // 1. Market Regime
   if(g_current_regime != REGIME_TRANSITION)
      decision.confluence_score++;

   // 2. Bias Alignment
   if((g_current_bias == BIAS_BULLISH && g_active_pattern.is_bullish) ||
      (g_current_bias == BIAS_BEARISH && !g_active_pattern.is_bullish))
      decision.confluence_score++;

   // 3. Volume
   if(UseVolumeFilter && g_volume_data.above_threshold)
      decision.confluence_score++;

   // 4. Spread
   if(UseSpreadFilter && g_spread_data.acceptable)
      decision.confluence_score++;

   // 5. Session
   if(UseSessionFilter && g_session_data.is_tradeable)
      decision.confluence_score++;

   // 6. Pattern Strength
   if(g_active_pattern.strength >= 4)
      decision.confluence_score++;

   // Make decision
   if(decision.confluence_score >= g_dynamic_confluence)
   {
      decision.decision = DECISION_ENTER;
      decision.reason = "Confluence met";
   }
   else if(decision.confluence_score == g_dynamic_confluence - 1)
   {
      decision.decision = DECISION_WAIT;
      decision.reason = "Need 1 more factor";
   }
   else
   {
      decision.decision = DECISION_SKIP;
      decision.reason = "Insufficient confluence";
   }

   return decision;
}

//+------------------------------------------------------------------+
//| CHECK RISK LIMITS                                                 |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   // Daily loss limit
   double daily_loss = ((g_daily_start_balance - AccountBalance()) / g_daily_start_balance) * 100.0;
   if(daily_loss >= DailyLossLimit)
   {
      Print("DAILY LOSS LIMIT REACHED: ", DoubleToString(daily_loss, 1), "%");
      return false;
   }

   // Weekly loss limit
   double weekly_loss = ((g_weekly_start_balance - AccountBalance()) / g_weekly_start_balance) * 100.0;
   if(weekly_loss >= WeeklyLossLimit)
   {
      Print("WEEKLY LOSS LIMIT REACHED: ", DoubleToString(weekly_loss, 1), "%");
      return false;
   }

   // Max open trades
   int open_trades = CountOpenTrades();
   if(open_trades >= g_active_aggression.max_trades)
   {
      Print("MAX POSITIONS REACHED: ", open_trades, "/", g_active_aggression.max_trades);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| COUNT OPEN TRADES                                                 |
//+------------------------------------------------------------------+
int CountOpenTrades()
{
   int count = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() == MagicNumber && OrderType() <= OP_SELL)
            count++;
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| CALCULATE DYNAMIC RISK                                            |
//+------------------------------------------------------------------+
double CalculateDynamicRisk()
{
   double base_risk = BaseRiskPercent;

   if(AccountBalance() > g_peak_balance)
      g_peak_balance = AccountBalance();

   double drawdown = 0;
   if(g_peak_balance > 0)
      drawdown = (g_peak_balance - AccountBalance()) / g_peak_balance;

   if(drawdown > 0.05)
      base_risk *= (1.0 - drawdown);

   if(g_consecutive_losses >= 2)
      base_risk *= 0.5;

   if(g_current_volatility == VOL_HIGH)
      base_risk *= 0.5;

   return MathMax(base_risk, 0.1);
}

//+------------------------------------------------------------------+
//| NORMALIZE LOT SIZE                                                |
//+------------------------------------------------------------------+
double NormalizeLotSize(double calculated_lot, double intended_risk, double sl_pips)
{
   double lot_step = MarketInfo(Symbol(), MODE_LOTSTEP);
   double broker_min_lot = MarketInfo(Symbol(), MODE_MINLOT);
   double broker_max_lot = MarketInfo(Symbol(), MODE_MAXLOT);

   double normalized_lot = MathFloor(calculated_lot / lot_step) * lot_step;

   if(normalized_lot < broker_min_lot)
   {
      normalized_lot = broker_min_lot;

      // Calculate actual risk
      double tick_value = MarketInfo(Symbol(), MODE_TICKVALUE);
      double tick_size = MarketInfo(Symbol(), MODE_TICKSIZE);
      double sl_in_price = sl_pips * Point;
      double risk_per_lot = (sl_in_price / tick_size) * tick_value;
      double actual_risk = (normalized_lot * risk_per_lot / AccountBalance()) * 100.0;

      Print("LOT ADJUSTED to minimum: ", DoubleToString(broker_min_lot, 2),
            " | Intended Risk: ", DoubleToString(intended_risk, 2), "%",
            " | Actual Risk: ", DoubleToString(actual_risk, 2), "%");

      if(actual_risk > intended_risk * 2)
         Print("WARNING: Actual risk significantly higher than intended!");
   }

   if(normalized_lot > broker_max_lot)
      normalized_lot = broker_max_lot;

   return normalized_lot;
}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE                                                |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_pips, double risk_percent)
{
   double lot_size = 0.0;
   double broker_min_lot = MarketInfo(Symbol(), MODE_MINLOT);

   if(PositionSizingMode == LOT_SIZE_RANGE)
   {
      lot_size = MinLotSize;

      if(MinLotSize < broker_min_lot)
         lot_size = broker_min_lot;

      lot_size = NormalizeLotSize(lot_size, risk_percent, sl_pips);

      if(lot_size > MaxLotSize && MaxLotSize >= broker_min_lot)
         lot_size = MaxLotSize;
   }
   else // RISK_PERCENTAGE
   {
      double capital_risk = AccountBalance() * (risk_percent / 100.0);
      double tick_value = MarketInfo(Symbol(), MODE_TICKVALUE);
      double tick_size = MarketInfo(Symbol(), MODE_TICKSIZE);

      if(tick_size <= 0 || tick_value <= 0)
         return broker_min_lot;

      double sl_in_price = sl_pips * Point;
      double risk_per_lot = (sl_in_price / tick_size) * tick_value;

      if(risk_per_lot > 0)
         lot_size = capital_risk / risk_per_lot;
      else
         lot_size = broker_min_lot;

      lot_size = NormalizeLotSize(lot_size, risk_percent, sl_pips);
   }

   return lot_size;
}

//+------------------------------------------------------------------+
//| EXECUTE TRADE                                                     |
//+------------------------------------------------------------------+
void ExecuteTrade(double risk_percent)
{
   bool is_buy = g_active_pattern.is_bullish;
   double entry_price = is_buy ? Ask : Bid;

   // Calculate Stop Loss
   double sl = CalculateStopLoss(is_buy);
   double sl_pips = MathAbs(entry_price - sl) / Point;

   // Calculate lot size
   double lot_size = CalculateLotSize(sl_pips, risk_percent);

   // Calculate Take Profit
   double sl_distance = MathAbs(entry_price - sl);
   double tp = entry_price + (is_buy ? 1 : -1) * sl_distance * g_dynamic_tp1;

   // Normalize prices
   sl = NormalizeDouble(sl, Digits);
   tp = NormalizeDouble(tp, Digits);

   Print("═══ EXECUTING TRADE ═══");
   Print("Direction: ", (is_buy ? "BUY" : "SELL"));
   Print("Entry: ", DoubleToString(entry_price, Digits));
   Print("SL: ", DoubleToString(sl, Digits), " (", DoubleToString(sl_pips/10, 1), " pips)");
   Print("TP: ", DoubleToString(tp, Digits));
   Print("Lots: ", DoubleToString(lot_size, 2));

   string comment = "IGTR4|" + g_active_pattern.name + "|L" + IntegerToString(AggressionLevel);

   int ticket = -1;
   if(is_buy)
      ticket = OrderSend(Symbol(), OP_BUY, lot_size, Ask, 10, sl, tp, comment, MagicNumber, 0, clrGreen);
   else
      ticket = OrderSend(Symbol(), OP_SELL, lot_size, Bid, 10, sl, tp, comment, MagicNumber, 0, clrRed);

   if(ticket > 0)
   {
      Print("TRADE EXECUTED - Ticket #", ticket);
      g_has_active_pattern = false;
   }
   else
   {
      Print("TRADE FAILED - Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| CALCULATE STOP LOSS                                               |
//+------------------------------------------------------------------+
double CalculateStopLoss(bool is_buy)
{
   double atr = iATR(Symbol(), PreferredTimeframe, 14, 0);
   double sl_distance = atr * StopLossATR;
   double entry_price = g_active_pattern.price;

   double sl_price;
   if(is_buy)
   {
      double swing_low = GetSwingLow(20);
      double atr_sl = entry_price - sl_distance;
      sl_price = MathMin(swing_low - 5 * Point, atr_sl);
   }
   else
   {
      double swing_high = GetSwingHigh(20);
      double atr_sl = entry_price + sl_distance;
      sl_price = MathMax(swing_high + 5 * Point, atr_sl);
   }

   return NormalizeDouble(sl_price, Digits);
}

//+------------------------------------------------------------------+
//| MANAGE OPEN TRADES                                                |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() > OP_SELL) continue;

      int ticket = OrderTicket();
      double entry = OrderOpenPrice();
      double sl = OrderStopLoss();
      double tp = OrderTakeProfit();
      bool is_buy = (OrderType() == OP_BUY);

      double current_price = is_buy ? Bid : Ask;

      // Calculate R profit
      double sl_distance = MathAbs(entry - sl);
      double current_profit = is_buy ? (current_price - entry) : (entry - current_price);
      double r_profit = (sl_distance > 0) ? current_profit / sl_distance : 0;

      // Move to breakeven at 1R
      if(r_profit >= 1.0 && MathAbs(sl - entry) > Point)
      {
         double new_sl = entry + (is_buy ? 1 : -1) * 5 * Point;
         if(OrderModify(ticket, entry, new_sl, tp, 0, clrBlue))
            Print("Position moved to BREAKEVEN");
      }

      // Profit Lock
      double position_profit = OrderProfit();
      bool r_trigger_hit = (r_profit >= ProfitLockTrigger);
      bool fixed_trigger_hit = (position_profit >= ProfitLockFixedAmount);

      if(UseProfitLock && (r_trigger_hit || fixed_trigger_hit))
      {
         double profit_to_lock = current_profit * (ProfitLockPercent / 100.0);
         double locked_sl;

         if(is_buy)
            locked_sl = entry + profit_to_lock;
         else
            locked_sl = entry - profit_to_lock;

         if((is_buy && locked_sl > sl) || (!is_buy && locked_sl < sl))
         {
            if(OrderModify(ticket, entry, locked_sl, tp, 0, clrGold))
               Print("PROFIT LOCKED at ", r_trigger_hit ? DoubleToString(ProfitLockTrigger, 1) + "R" : "$" + DoubleToString(ProfitLockFixedAmount, 0));
         }
      }

      // Trailing stop
      if(r_profit >= 1.5)
      {
         double new_sl;
         if(is_buy)
         {
            new_sl = GetSwingLow(10);
            if(new_sl > sl && new_sl < current_price)
            {
               if(OrderModify(ticket, entry, new_sl, tp, 0, clrAqua))
                  Print("Trailing stop updated");
            }
         }
         else
         {
            new_sl = GetSwingHigh(10);
            if(new_sl < sl && new_sl > current_price)
            {
               if(OrderModify(ticket, entry, new_sl, tp, 0, clrAqua))
                  Print("Trailing stop updated");
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| CHECK ACCOUNT PROFIT LOCK                                         |
//+------------------------------------------------------------------+
void CheckAccountProfitLock()
{
   double total_profit = 0;

   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderType() <= OP_SELL)
            total_profit += OrderProfit() + OrderSwap() + OrderCommission();
      }
   }

   if(total_profit <= 0)
      return;

   double current_balance = AccountBalance();
   double profit_percent = (total_profit / current_balance) * 100.0;

   bool amount_trigger_hit = (total_profit >= AccountProfitLockAmount);
   bool percent_trigger_hit = (profit_percent >= AccountProfitLockPercent);

   if(amount_trigger_hit || percent_trigger_hit)
   {
      Print("═══════════════════════════════════════════════════════════════");
      Print("  ACCOUNT PROFIT LOCK TRIGGERED!");
      Print("  Total Profit: ", DoubleToString(total_profit, 2));
      Print("  Profit %: ", DoubleToString(profit_percent, 2), "%");
      Print("═══════════════════════════════════════════════════════════════");

      CloseAllTrades();

      if(EnablePopupAlerts)
         Alert("ACCOUNT PROFIT LOCK: Closed all at ", DoubleToString(total_profit, 2), " profit");

      if(EnableMobileNotifications)
         SendNotification("PROFIT LOCKED! " + DoubleToString(total_profit, 2) + " - All closed");
   }
}

//+------------------------------------------------------------------+
//| CLOSE ALL TRADES                                                  |
//+------------------------------------------------------------------+
void CloseAllTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderType() <= OP_SELL)
         {
            bool result = false;
            if(OrderType() == OP_BUY)
               result = OrderClose(OrderTicket(), OrderLots(), Bid, 10, clrRed);
            else
               result = OrderClose(OrderTicket(), OrderLots(), Ask, 10, clrRed);

            if(result)
               Print("Closed position #", OrderTicket());
            else
               Print("Failed to close #", OrderTicket(), " Error: ", GetLastError());
         }
      }
   }
}

//+------------------------------------------------------------------+
//| HELPER FUNCTIONS                                                  |
//+------------------------------------------------------------------+
double GetSwingHigh(int lookback)
{
   double high = 0;
   for(int i = 1; i <= lookback; i++)
   {
      double h = iHigh(Symbol(), PreferredTimeframe, i);
      if(h > high) high = h;
   }
   return high;
}

double GetSwingLow(int lookback)
{
   double low = DBL_MAX;
   for(int i = 1; i <= lookback; i++)
   {
      double l = iLow(Symbol(), PreferredTimeframe, i);
      if(l < low) low = l;
   }
   return low;
}

double GetRangeHigh(int lookback)
{
   return iHigh(Symbol(), PreferredTimeframe, iHighest(Symbol(), PreferredTimeframe, MODE_HIGH, lookback, 1));
}

double GetRangeLow(int lookback)
{
   return iLow(Symbol(), PreferredTimeframe, iLowest(Symbol(), PreferredTimeframe, MODE_LOW, lookback, 1));
}

int GetHigherTimeframe(int current)
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
