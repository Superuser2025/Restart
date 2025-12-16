//+------------------------------------------------------------------+
//|                                                  AppleTrader.mq5 |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| Professional Institutional Trading System                        |
//| - 20 Institutional Filters                                       |
//| - Pattern Recognition                                            |
//| - Supply/Demand Zones                                            |
//| - Machine Learning Integration                                   |
//| - Python GUI Communication via JSON                              |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

#include <Trade/Trade.mqh>
#include <AppleTrader/JSONExporter.mqh>
#include <AppleTrader/JSONReader.mqh>
#include <AppleTrader/Filters.mqh>
#include <AppleTrader/Patterns.mqh>
#include <AppleTrader/Zones.mqh>
#include <AppleTrader/RiskManager.mqh>
//#include <AppleTrader/ExportTradeHistory.mqh>

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+

//--- Trading Mode
input group "═══════════════════════════════════════════════════════"
input group "TRADING MODE"
input group "═══════════════════════════════════════════════════════"
input bool     EnableAutoTrading = false;         // Enable Auto Trading (false = Indicator Mode)
input bool     RequireConfirmation = true;        // Require Manual Confirmation for Trades

//--- Update & Communication Settings
input group "═══════════════════════════════════════════════════════"
input group "UPDATE SETTINGS"
input group "═══════════════════════════════════════════════════════"
input int      DataExportInterval = 10000;        // Data Export Interval (ms) - 10 seconds default
input string   ExportFilePath = "AppleTrader/market_data.json";  // Export JSON Path
input string   CommandFilePath = "AppleTrader/commands.json";    // Command JSON Path

//--- Risk Management
input group "═══════════════════════════════════════════════════════"
input group "RISK MANAGEMENT"
input group "═══════════════════════════════════════════════════════"
input double   RiskPercentage = 0.5;              // Risk Per Trade (%)
input double   MaxDailyLoss = 2.0;                // Max Daily Loss (%)
input double   MaxDailyProfit = 5.0;              // Max Daily Profit Target (%)
input int      MaxDailyTrades = 5;                // Max Daily Trades
input int      MaxOpenPositions = 1;              // Max Open Positions

//--- Filter Settings
input group "═══════════════════════════════════════════════════════"
input group "INSTITUTIONAL FILTERS"
input group "═══════════════════════════════════════════════════════"
input bool     Filter_Trend = true;               // [1] Trend Filter (200 EMA)
input bool     Filter_HTF_Alignment = true;       // [2] HTF Alignment Filter
input bool     Filter_MarketStructure = true;     // [3] Market Structure Filter
input bool     Filter_Supply_Demand = true;       // [4] Supply/Demand Zone Filter
input bool     Filter_Session = true;             // [5] Trading Session Filter
input bool     Filter_Spread = true;              // [6] Spread Filter
input bool     Filter_Volatility = true;          // [7] Volatility Filter
input bool     Filter_News = true;                // [8] News/High Impact Event Filter
input bool     Filter_Volume = true;              // [9] Volume Filter
input bool     Filter_OrderFlow = true;           // [10] Order Flow Filter
input bool     Filter_Momentum = true;            // [11] Momentum Filter (RSI)
input bool     Filter_Confluence = true;          // [12] Multi-Timeframe Confluence
input bool     Filter_FairValueGap = true;        // [13] Fair Value Gap (FVG) Filter
input bool     Filter_LiquiditySweep = true;      // [14] Liquidity Sweep Filter
input bool     Filter_ChochBOS = true;            // [15] CHoCH/BOS Detection
input bool     Filter_Divergence = true;          // [16] Divergence Filter
input bool     Filter_SmartMoney = true;          // [17] Smart Money Concepts
input bool     Filter_TimeOfDay = true;           // [18] Time of Day Filter
input bool     Filter_Correlation = true;         // [19] Currency Correlation Filter
input bool     Filter_ML_Signal = true;           // [20] Machine Learning Signal Filter

//--- ML Integration
input group "═══════════════════════════════════════════════════════"
input group "MACHINE LEARNING"
input group "═══════════════════════════════════════════════════════"
input bool     EnableML = true;                   // Enable ML Integration
input double   MinMLConfidence = 0.65;            // Minimum ML Confidence (0-1)
input double   MinMLProbability = 0.60;           // Minimum ML Probability (0-1)

//--- Pattern Recognition
input group "═══════════════════════════════════════════════════════"
input group "PATTERN RECOGNITION"
input group "═══════════════════════════════════════════════════════"
input bool     EnablePatterns = true;             // Enable Pattern Detection
input bool     Pattern_DoubleTop = true;          // Double Top/Bottom
input bool     Pattern_HeadShoulders = true;      // Head & Shoulders
input bool     Pattern_Triangle = true;           // Triangle Patterns
input bool     Pattern_Wedge = true;              // Wedge Patterns
input bool     Pattern_Channel = true;            // Channel Patterns

//--- Zone Settings
input group "═══════════════════════════════════════════════════════"
input group "SUPPLY/DEMAND ZONES"
input group "═══════════════════════════════════════════════════════"
input int      ZoneLookback = 100;                // Zone Lookback Period
input double   ZoneStrength = 2.0;                // Minimum Zone Strength
input color    SupplyZoneColor = clrCrimson;      // Supply Zone Color
input color    DemandZoneColor = clrDodgerBlue;   // Demand Zone Color

//--- Trading Session Times (GMT)
input group "═══════════════════════════════════════════════════════"
input group "TRADING SESSIONS"
input group "═══════════════════════════════════════════════════════"
input bool     Trade_Asian = false;               // Trade Asian Session
input bool     Trade_London = true;               // Trade London Session
input bool     Trade_NewYork = true;              // Trade New York Session
input string   AsianStart = "00:00";              // Asian Session Start
input string   AsianEnd = "09:00";                // Asian Session End
input string   LondonStart = "08:00";             // London Session Start
input string   LondonEnd = "17:00";               // London Session End
input string   NewYorkStart = "13:00";            // New York Session Start
input string   NewYorkEnd = "22:00";              // New York Session End

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
CTrade         trade;                             // Trade execution object
CJSONExporter  jsonExporter;                      // JSON export handler
CJSONReader    jsonReader;                        // JSON command reader
CFilters       filters;                           // Filter engine
CPatterns      patterns;                          // Pattern detector
CZones         zones;                             // Zone manager
CRiskManager   riskManager;                       // Risk management

datetime       lastExportTime = 0;                // Last data export timestamp
int            tradesExecutedToday = 0;           // Daily trade counter
double         todayProfitLoss = 0.0;             // Today's P/L
datetime       lastDayReset = 0;                  // Last daily reset

// Market data
string         currentBias = "NEUTRAL";           // Market bias
string         currentRegime = "RANGING";         // Market regime
string         currentSession = "NONE";           // Trading session
string         currentPattern = "NONE";           // Active pattern
double         currentVolatility = 0.0;           // Current volatility
double         currentSpread = 0.0;               // Current spread

// Filter states
bool           filterStates[20];                  // All filter pass/fail states
int            passedFilters = 0;                 // Count of passed filters
double         confluenceScore = 0.0;             // Confluence percentage

// ML data
bool           mlEnabled = false;                 // ML system status
double         mlProbability = 0.0;               // ML prediction probability
double         mlConfidence = 0.0;                // ML confidence level
string         mlSignal = "WAIT";                 // ML signal (ENTER/WAIT/SKIP)

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("═══════════════════════════════════════════════════════════");
   Print("         AppleTrader Pro - Institutional System");
   Print("═══════════════════════════════════════════════════════════");

   //--- Initialize trade object
   trade.SetExpertMagicNumber(888888);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_FOK);
   trade.LogLevel(LOG_LEVEL_ERRORS);

   //--- Initialize components
   if(!jsonExporter.Init(ExportFilePath))
   {
      Print("ERROR: Failed to initialize JSON exporter");
      return(INIT_FAILED);
   }

   if(!jsonReader.Init(CommandFilePath))
   {
      Print("ERROR: Failed to initialize JSON command reader");
      return(INIT_FAILED);
   }

   if(!filters.Init())
   {
      Print("ERROR: Failed to initialize filter engine");
      return(INIT_FAILED);
   }

   if(!patterns.Init())
   {
      Print("ERROR: Failed to initialize pattern detector");
      return(INIT_FAILED);
   }

   if(!zones.Init(ZoneLookback, ZoneStrength, SupplyZoneColor, DemandZoneColor))
   {
      Print("ERROR: Failed to initialize zone manager");
      return(INIT_FAILED);
   }

   if(!riskManager.Init(RiskPercentage, MaxDailyLoss, MaxDailyProfit, MaxDailyTrades))
   {
      Print("ERROR: Failed to initialize risk manager");
      return(INIT_FAILED);
   }

   //--- Set trading mode
   Print("Trading Mode: ", EnableAutoTrading ? "AUTO TRADING" : "INDICATOR MODE");
   Print("ML Integration: ", EnableML ? "ENABLED" : "DISABLED");
   Print("Data Export Interval: ", DataExportInterval, " ms");

   //--- Initialize daily tracking
   lastDayReset = TimeCurrent();

   //--- Set timer to ensure export happens even without ticks
   EventSetTimer(DataExportInterval / 1000);  // Timer in seconds
   Print("Timer set for ", DataExportInterval / 1000, " seconds");

   Print("═══════════════════════════════════════════════════════════");
   Print("Initialization Complete - System Ready");
   Print("═══════════════════════════════════════════════════════════");

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("═══════════════════════════════════════════════════════════");
   Print("AppleTrader Pro - Shutting Down");
   Print("Reason: ", GetDeinitReasonText(reason));

   //--- Kill timer
   EventKillTimer();

   //--- Clean up zones
   zones.RemoveAllZones();

   //--- Export final state
   ExportMarketDataToJSON();

   Print("═══════════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Daily reset check
   CheckDailyReset();

       // ML: Monitor closed positions for training data collection (always run)
   // if(ml_system != NULL)
     //   {MonitorClosedPositions();}
   
   //--- Export market data at specified interval
   if(TimeCurrent() - lastExportTime >= DataExportInterval / 1000)
   {
      ExportMarketDataToJSON();
      lastExportTime = TimeCurrent();
   }

   //--- Read commands from Python GUI
   ProcessPythonCommands();

   //--- Update market analysis
   UpdateMarketAnalysis();

   //--- Check for trading signals (only if auto trading enabled)
   if(EnableAutoTrading)
   {
      CheckTradingSignals();
   }
}

//+------------------------------------------------------------------+
//| Timer function (exports data at regular intervals)              |
//+------------------------------------------------------------------+
void OnTimer()
{
   Print("[TIMER] Timer triggered - Exporting market data...");

   //--- Export market data
   ExportMarketDataToJSON();

   //--- Read commands from Python GUI
   ProcessPythonCommands();

   //--- Update market analysis
   UpdateMarketAnalysis();
}

//+------------------------------------------------------------------+
//| Update Market Analysis                                           |
//+------------------------------------------------------------------+
void UpdateMarketAnalysis()
{
   //--- Update current session
   currentSession = GetCurrentSession();

   //--- Update spread and volatility
   currentSpread = (SymbolInfoDouble(Symbol(), SYMBOL_ASK) - SymbolInfoDouble(Symbol(), SYMBOL_BID)) / _Point;
   currentVolatility = filters.CalculateVolatility();

   //--- Run all filters
   RunAllFilters();

   //--- Detect patterns
   if(EnablePatterns)
   {
      currentPattern = patterns.DetectActivePattern(
         Pattern_DoubleTop,
         Pattern_HeadShoulders,
         Pattern_Triangle,
         Pattern_Wedge,
         Pattern_Channel
      );
   }

   //--- Update zones
   zones.UpdateZones();

   //--- Update market regime
   currentRegime = filters.GetMarketRegime();

   //--- Update bias
   currentBias = filters.GetMarketBias();
}

//+------------------------------------------------------------------+
//| Run All Institutional Filters                                    |
//+------------------------------------------------------------------+
void RunAllFilters()
{
   passedFilters = 0;

   //--- Filter 1: Trend Filter
   filterStates[0] = !Filter_Trend || filters.CheckTrendFilter();
   if(filterStates[0]) passedFilters++;

   //--- Filter 2: HTF Alignment
   filterStates[1] = !Filter_HTF_Alignment || filters.CheckHTFAlignment();
   if(filterStates[1]) passedFilters++;

   //--- Filter 3: Market Structure
   filterStates[2] = !Filter_MarketStructure || filters.CheckMarketStructure();
   if(filterStates[2]) passedFilters++;

   //--- Filter 4: Supply/Demand Zones
   filterStates[3] = !Filter_Supply_Demand || zones.IsNearZone();
   if(filterStates[3]) passedFilters++;

   //--- Filter 5: Session Filter
   filterStates[4] = !Filter_Session || CheckSessionFilter();
   if(filterStates[4]) passedFilters++;

   //--- Filter 6: Spread Filter
   filterStates[5] = !Filter_Spread || filters.CheckSpreadFilter(currentSpread);
   if(filterStates[5]) passedFilters++;

   //--- Filter 7: Volatility Filter
   filterStates[6] = !Filter_Volatility || filters.CheckVolatilityFilter(currentVolatility);
   if(filterStates[6]) passedFilters++;

   //--- Filter 8: News Filter
   filterStates[7] = !Filter_News || filters.CheckNewsFilter();
   if(filterStates[7]) passedFilters++;

   //--- Filter 9: Volume Filter
   filterStates[8] = !Filter_Volume || filters.CheckVolumeFilter();
   if(filterStates[8]) passedFilters++;

   //--- Filter 10: Order Flow
   filterStates[9] = !Filter_OrderFlow || filters.CheckOrderFlow();
   if(filterStates[9]) passedFilters++;

   //--- Filter 11: Momentum (RSI)
   filterStates[10] = !Filter_Momentum || filters.CheckMomentumFilter();
   if(filterStates[10]) passedFilters++;

   //--- Filter 12: Confluence
   filterStates[11] = !Filter_Confluence || filters.CheckConfluence();
   if(filterStates[11]) passedFilters++;

   //--- Filter 13: Fair Value Gap
   filterStates[12] = !Filter_FairValueGap || filters.CheckFVG();
   if(filterStates[12]) passedFilters++;

   //--- Filter 14: Liquidity Sweep
   filterStates[13] = !Filter_LiquiditySweep || filters.CheckLiquiditySweep();
   if(filterStates[13]) passedFilters++;

   //--- Filter 15: CHoCH/BOS
   filterStates[14] = !Filter_ChochBOS || filters.CheckCHoCH_BOS();
   if(filterStates[14]) passedFilters++;

   //--- Filter 16: Divergence
   filterStates[15] = !Filter_Divergence || filters.CheckDivergence();
   if(filterStates[15]) passedFilters++;

   //--- Filter 17: Smart Money
   filterStates[16] = !Filter_SmartMoney || filters.CheckSmartMoney();
   if(filterStates[16]) passedFilters++;

   //--- Filter 18: Time of Day
   filterStates[17] = !Filter_TimeOfDay || filters.CheckTimeFilter();
   if(filterStates[17]) passedFilters++;

   //--- Filter 19: Correlation
   filterStates[18] = !Filter_Correlation || filters.CheckCorrelation();
   if(filterStates[18]) passedFilters++;

   //--- Filter 20: ML Signal
   filterStates[19] = !Filter_ML_Signal || CheckMLFilter();
   if(filterStates[19]) passedFilters++;

   //--- Calculate confluence score
   int totalActiveFilters = 0;
   for(int i = 0; i < 20; i++)
   {
      if(IsFilterActive(i)) totalActiveFilters++;
   }

   confluenceScore = totalActiveFilters > 0 ? (double)passedFilters / totalActiveFilters * 100.0 : 0.0;
}

//+------------------------------------------------------------------+
//| Check if filter is active                                        |
//+------------------------------------------------------------------+
bool IsFilterActive(int filterIndex)
{
   switch(filterIndex)
   {
      case 0: return Filter_Trend;
      case 1: return Filter_HTF_Alignment;
      case 2: return Filter_MarketStructure;
      case 3: return Filter_Supply_Demand;
      case 4: return Filter_Session;
      case 5: return Filter_Spread;
      case 6: return Filter_Volatility;
      case 7: return Filter_News;
      case 8: return Filter_Volume;
      case 9: return Filter_OrderFlow;
      case 10: return Filter_Momentum;
      case 11: return Filter_Confluence;
      case 12: return Filter_FairValueGap;
      case 13: return Filter_LiquiditySweep;
      case 14: return Filter_ChochBOS;
      case 15: return Filter_Divergence;
      case 16: return Filter_SmartMoney;
      case 17: return Filter_TimeOfDay;
      case 18: return Filter_Correlation;
      case 19: return Filter_ML_Signal;
      default: return false;
   }
}

//+------------------------------------------------------------------+
//| Check ML Filter                                                  |
//+------------------------------------------------------------------+
bool CheckMLFilter()
{
   if(!EnableML) return true;

   //--- ML signal must be ENTER with sufficient confidence
   if(mlSignal == "ENTER" &&
      mlConfidence >= MinMLConfidence &&
      mlProbability >= MinMLProbability)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Check Session Filter                                             |
//+------------------------------------------------------------------+
bool CheckSessionFilter()
{
   string session = GetCurrentSession();

   if(session == "ASIAN" && Trade_Asian) return true;
   if(session == "LONDON" && Trade_London) return true;
   if(session == "NEW YORK" && Trade_NewYork) return true;

   return false;
}

//+------------------------------------------------------------------+
//| Get Current Trading Session                                      |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   int currentHour = dt.hour;

   //--- Parse session times (simplified - would need full time parsing)
   if(currentHour >= 0 && currentHour < 9) return "ASIAN";
   if(currentHour >= 8 && currentHour < 17) return "LONDON";
   if(currentHour >= 13 && currentHour < 22) return "NEW YORK";

   return "NONE";
}

//+------------------------------------------------------------------+
//| Check for Trading Signals                                        |
//+------------------------------------------------------------------+
void CheckTradingSignals()
{
   //--- Check if max positions reached
   if(PositionsTotal() >= MaxOpenPositions) return;

   //--- Check daily limits
   if(!riskManager.CanTrade(tradesExecutedToday, todayProfitLoss))
   {
      return;
   }

   //--- Require minimum confluence
   if(confluenceScore < 70.0) return;  // Need at least 70% of filters passing

   //--- Check for BUY signal
   if(currentBias == "BULLISH" && allFiltersPass())
   {
      ExecuteBuySignal();
   }

   //--- Check for SELL signal
   if(currentBias == "BEARISH" && allFiltersPass())
   {
      ExecuteSellSignal();
   }
}

//+------------------------------------------------------------------+
//| Check if all active filters pass                                 |
//+------------------------------------------------------------------+
bool allFiltersPass()
{
   for(int i = 0; i < 20; i++)
   {
      if(IsFilterActive(i) && !filterStates[i])
      {
         return false;
      }
   }
   return true;
}

//+------------------------------------------------------------------+
//| Execute BUY Signal                                               |
//+------------------------------------------------------------------+
void ExecuteBuySignal()
{
   //--- Calculate position size
   double lotSize = riskManager.CalculatePositionSize(Symbol(), RiskPercentage);

   //--- Get current prices
   double askPrice = SymbolInfoDouble(Symbol(), SYMBOL_ASK);

   //--- Calculate SL and TP
   double sl = zones.GetNearestDemandZone() - 10 * _Point;
   double tp = askPrice + (askPrice - sl) * 2.0;  // 1:2 Risk:Reward

   //--- Require confirmation if enabled
   if(RequireConfirmation)
   {
      Print("BUY Signal Generated - Awaiting Manual Confirmation");
      Print("Entry: ", askPrice, " | SL: ", sl, " | TP: ", tp, " | Size: ", lotSize);
      return;
   }

   //--- Execute trade
   if(trade.Buy(lotSize, Symbol(), askPrice, sl, tp, "AppleTrader BUY"))
   {
      Print("BUY Order Executed: ", trade.ResultOrder());
      tradesExecutedToday++;
   }
   else
   {
      Print("BUY Order Failed: ", trade.ResultRetcodeDescription());
   }
}

//+------------------------------------------------------------------+
//| Execute SELL Signal                                              |
//+------------------------------------------------------------------+
void ExecuteSellSignal()
{
   //--- Calculate position size
   double lotSize = riskManager.CalculatePositionSize(Symbol(), RiskPercentage);

   //--- Get current prices
   double bidPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);

   //--- Calculate SL and TP
   double sl = zones.GetNearestSupplyZone() + 10 * _Point;
   double tp = bidPrice - (sl - bidPrice) * 2.0;  // 1:2 Risk:Reward

   //--- Require confirmation if enabled
   if(RequireConfirmation)
   {
      Print("SELL Signal Generated - Awaiting Manual Confirmation");
      Print("Entry: ", bidPrice, " | SL: ", sl, " | TP: ", tp, " | Size: ", lotSize);
      return;
   }

   //--- Execute trade
   if(trade.Sell(lotSize, Symbol(), bidPrice, sl, tp, "AppleTrader SELL"))
   {
      Print("SELL Order Executed: ", trade.ResultOrder());
      tradesExecutedToday++;
   }
   else
   {
      Print("SELL Order Failed: ", trade.ResultRetcodeDescription());
   }
}

//+------------------------------------------------------------------+
//| Export Market Data to JSON                                       |
//+------------------------------------------------------------------+
void ExportMarketDataToJSON()
{
   Print("[EXPORT] Starting market data export...");

   //--- Collect position data
   int totalPositions = PositionsTotal();
   double totalPnL = 0.0;

   for(int i = 0; i < totalPositions; i++)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         totalPnL += PositionGetDouble(POSITION_PROFIT);
      }
   }

   Print("[EXPORT] Building JSON data...");

   //--- Export comprehensive market data
   jsonExporter.BeginExport();

   //--- Market info
   jsonExporter.AddString("symbol", Symbol());
   jsonExporter.AddDouble("bid", SymbolInfoDouble(Symbol(), SYMBOL_BID), 5);
   jsonExporter.AddDouble("ask", SymbolInfoDouble(Symbol(), SYMBOL_ASK), 5);
   jsonExporter.AddDouble("spread", currentSpread, 2);
   jsonExporter.AddString("timeframe", EnumToString(Period()));
   jsonExporter.AddLong("timestamp", TimeCurrent());

   //--- Market context
   jsonExporter.AddString("bias", currentBias);
   jsonExporter.AddString("regime", currentRegime);
   jsonExporter.AddString("session", currentSession);
   jsonExporter.AddDouble("volatility", currentVolatility, 4);

   //--- Pattern info
   jsonExporter.AddString("pattern", currentPattern);

   //--- Filter states (all 20 filters)
   jsonExporter.BeginArray("filters");
   for(int i = 0; i < 20; i++)
   {
      jsonExporter.AddArrayBool(filterStates[i]);
   }
   jsonExporter.EndArray();

   jsonExporter.AddInt("passed_filters", passedFilters);
   jsonExporter.AddDouble("confluence", confluenceScore, 2);

   //--- Trading status
   jsonExporter.AddBool("auto_trading", EnableAutoTrading);
   jsonExporter.AddInt("positions", totalPositions);
   jsonExporter.AddDouble("total_pnl", totalPnL, 2);
   jsonExporter.AddInt("trades_today", tradesExecutedToday);
   jsonExporter.AddDouble("today_pnl", todayProfitLoss, 2);

   //--- ML data
   jsonExporter.AddBool("ml_enabled", mlEnabled);
   jsonExporter.AddString("ml_signal", mlSignal);
   jsonExporter.AddDouble("ml_probability", mlProbability, 4);
   jsonExporter.AddDouble("ml_confidence", mlConfidence, 4);

   //--- Risk metrics
   jsonExporter.AddDouble("account_balance", AccountInfoDouble(ACCOUNT_BALANCE), 2);
   jsonExporter.AddDouble("account_equity", AccountInfoDouble(ACCOUNT_EQUITY), 2);
   jsonExporter.AddDouble("risk_percent", RiskPercentage, 2);

   Print("[EXPORT] Writing JSON to file...");
   bool success = jsonExporter.EndExport();

   if(success)
   {
      Print("[EXPORT] ✓ Market data successfully exported to ", ExportFilePath);
   }
   else
   {
      Print("[EXPORT] ✗ FAILED to export market data!");
   }
}

//+------------------------------------------------------------------+
//| Process Python Commands                                          |
//+------------------------------------------------------------------+
void ProcessPythonCommands()
{
   string command = jsonReader.ReadCommand();

   if(command == "") return;  // No command

   //--- Process different commands
   if(command == "PLACE_ORDER")
   {
      string orderType = jsonReader.GetString("type", "");
      double volume = jsonReader.GetDouble("volume", 0.0);
      double sl = jsonReader.GetDouble("sl", 0.0);
      double tp = jsonReader.GetDouble("tp", 0.0);

      PlaceOrder(orderType, volume, sl, tp);
   }
   else if(command == "CLOSE_POSITION")
   {
      long ticket = jsonReader.GetLong("ticket", 0);
      ClosePosition(ticket);
   }
   else if(command == "CLOSE_ALL")
   {
      CloseAllPositions();
   }
   else if(command == "UPDATE_SETTINGS")
   {
      UpdateSettingsFromPython();
   }
   else if(command == "UPDATE_ML")
   {
      UpdateMLDataFromPython();
   }
}

//+------------------------------------------------------------------+
//| Place Order from Python                                          |
//+------------------------------------------------------------------+
void PlaceOrder(string orderType, double volume, double sl, double tp)
{
   if(orderType == "BUY")
   {
      double askPrice = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      trade.Buy(volume, Symbol(), askPrice, sl, tp, "AppleTrader GUI BUY");
   }
   else if(orderType == "SELL")
   {
      double bidPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
      trade.Sell(volume, Symbol(), bidPrice, sl, tp, "AppleTrader GUI SELL");
   }

   if(trade.ResultRetcode() == TRADE_RETCODE_DONE)
   {
      Print("Order placed successfully from Python GUI");
      tradesExecutedToday++;
   }
}

//+------------------------------------------------------------------+
//| Close Position                                                    |
//+------------------------------------------------------------------+
void ClosePosition(long ticket)
{
   if(PositionSelectByTicket(ticket))
   {
      trade.PositionClose(ticket);
      Print("Position closed: ", ticket);
   }
}

//+------------------------------------------------------------------+
//| Close All Positions                                              |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         trade.PositionClose(PositionGetTicket(i));
      }
   }
   Print("All positions closed from Python GUI");
}

//+------------------------------------------------------------------+
//| Update Settings from Python                                      |
//+------------------------------------------------------------------+
void UpdateSettingsFromPython()
{
   //--- Read updated settings from JSON
   // This would update EA parameters based on GUI changes
   Print("Settings updated from Python GUI");
}

//+------------------------------------------------------------------+
//| Update ML Data from Python                                       |
//+------------------------------------------------------------------+
void UpdateMLDataFromPython()
{
   mlEnabled = jsonReader.GetBool("enabled", false);
   mlSignal = jsonReader.GetString("signal", "WAIT");
   mlProbability = jsonReader.GetDouble("probability", 0.0);
   mlConfidence = jsonReader.GetDouble("confidence", 0.0);

   Print("ML Data Updated: ", mlSignal, " | Prob: ", mlProbability, " | Conf: ", mlConfidence);
}

//+------------------------------------------------------------------+
//| Check Daily Reset                                                |
//+------------------------------------------------------------------+
void CheckDailyReset()
{
   MqlDateTime now, last;
   TimeToStruct(TimeCurrent(), now);
   TimeToStruct(lastDayReset, last);

   if(now.day != last.day)
   {
      Print("═══════════════════════════════════════════════════════════");
      Print("Daily Reset - New Trading Day");
      Print("Previous Day Trades: ", tradesExecutedToday);
      Print("Previous Day P/L: $", todayProfitLoss);
      Print("═══════════════════════════════════════════════════════════");

      tradesExecutedToday = 0;
      todayProfitLoss = 0.0;
      lastDayReset = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Get Deinit Reason Text                                           |
//+------------------------------------------------------------------+
string GetDeinitReasonText(int reason)
{
   switch(reason)
   {
      case REASON_PROGRAM: return "Program stopped by user";
      case REASON_REMOVE: return "EA removed from chart";
      case REASON_RECOMPILE: return "EA recompiled";
      case REASON_CHARTCHANGE: return "Chart symbol/period changed";
      case REASON_CHARTCLOSE: return "Chart closed";
      case REASON_PARAMETERS: return "Input parameters changed";
      case REASON_ACCOUNT: return "Account changed";
      default: return "Unknown reason";
   }
}
