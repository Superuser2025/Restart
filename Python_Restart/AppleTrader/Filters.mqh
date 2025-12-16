//+------------------------------------------------------------------+
//|                                                      Filters.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| 20 Institutional-Grade Filters                                   |
//| - Trend, Structure, Momentum, Volume, Smart Money, etc.         |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CFilters Class                                                   |
//| Implements all 20 institutional filters                          |
//+------------------------------------------------------------------+
class CFilters
{
private:
   //--- Indicator handles
   int               m_ema200Handle;
   int               m_ema50Handle;
   int               m_ema20Handle;
   int               m_rsiHandle;
   int               m_atrHandle;

   //--- Market state
   string            m_marketBias;
   string            m_marketRegime;
   double            m_volatility;

   //--- Filter thresholds
   double            m_maxSpread;
   double            m_minVolume;
   double            m_maxVolatility;

public:
                     CFilters();
                    ~CFilters();

   //--- Initialization
   bool              Init();
   void              Deinit();

   //--- Filter 1: Trend Filter (200 EMA)
   bool              CheckTrendFilter();

   //--- Filter 2: HTF Alignment
   bool              CheckHTFAlignment();

   //--- Filter 3: Market Structure
   bool              CheckMarketStructure();

   //--- Filter 4: Supply/Demand (handled by Zones class)
   // bool           CheckSupplyDemand();

   //--- Filter 5: Session Filter (handled in main EA)
   // bool           CheckSessionFilter();

   //--- Filter 6: Spread Filter
   bool              CheckSpreadFilter(double spread);

   //--- Filter 7: Volatility Filter
   bool              CheckVolatilityFilter(double volatility);

   //--- Filter 8: News Filter
   bool              CheckNewsFilter();

   //--- Filter 9: Volume Filter
   bool              CheckVolumeFilter();

   //--- Filter 10: Order Flow
   bool              CheckOrderFlow();

   //--- Filter 11: Momentum (RSI)
   bool              CheckMomentumFilter();

   //--- Filter 12: Confluence
   bool              CheckConfluence();

   //--- Filter 13: Fair Value Gap (FVG)
   bool              CheckFVG();

   //--- Filter 14: Liquidity Sweep
   bool              CheckLiquiditySweep();

   //--- Filter 15: CHoCH/BOS (Change of Character/Break of Structure)
   bool              CheckCHoCH_BOS();

   //--- Filter 16: Divergence
   bool              CheckDivergence();

   //--- Filter 17: Smart Money Concepts
   bool              CheckSmartMoney();

   //--- Filter 18: Time of Day
   bool              CheckTimeFilter();

   //--- Filter 19: Currency Correlation
   bool              CheckCorrelation();

   //--- Filter 20: ML Signal (handled in main EA)
   // bool           CheckMLFilter();

   //--- Utility methods
   double            CalculateVolatility();
   string            GetMarketBias();
   string            GetMarketRegime();

private:
   //--- Helper methods
   double            GetEMA(int handle, int shift = 0);
   double            GetRSI(int shift = 0);
   double            GetATR(int shift = 0);
   bool              IsBullishCandle(int shift = 1);
   bool              IsBearishCandle(int shift = 1);
   double            GetHigh(int shift);
   double            GetLow(int shift);
   double            GetClose(int shift);
   double            GetOpen(int shift);
   long              GetVolume(int shift);
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CFilters::CFilters()
{
   m_ema200Handle = INVALID_HANDLE;
   m_ema50Handle = INVALID_HANDLE;
   m_ema20Handle = INVALID_HANDLE;
   m_rsiHandle = INVALID_HANDLE;
   m_atrHandle = INVALID_HANDLE;

   m_marketBias = "NEUTRAL";
   m_marketRegime = "RANGING";
   m_volatility = 0.0;

   m_maxSpread = 20.0;          // Max 20 pips spread
   m_minVolume = 100;           // Minimum tick volume
   m_maxVolatility = 0.01;      // Max 1% volatility
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CFilters::~CFilters()
{
   Deinit();
}

//+------------------------------------------------------------------+
//| Initialize all indicators                                        |
//+------------------------------------------------------------------+
bool CFilters::Init()
{
   //--- Create EMA indicators
   m_ema200Handle = iMA(Symbol(), PERIOD_CURRENT, 200, 0, MODE_EMA, PRICE_CLOSE);
   m_ema50Handle = iMA(Symbol(), PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);
   m_ema20Handle = iMA(Symbol(), PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);

   //--- Create RSI indicator
   m_rsiHandle = iRSI(Symbol(), PERIOD_CURRENT, 14, PRICE_CLOSE);

   //--- Create ATR indicator
   m_atrHandle = iATR(Symbol(), PERIOD_CURRENT, 14);

   //--- Check if all indicators created successfully
   if(m_ema200Handle == INVALID_HANDLE ||
      m_ema50Handle == INVALID_HANDLE ||
      m_ema20Handle == INVALID_HANDLE ||
      m_rsiHandle == INVALID_HANDLE ||
      m_atrHandle == INVALID_HANDLE)
   {
      Print("Failed to create indicators");
      return false;
   }

   Print("Filters initialized successfully");
   return true;
}

//+------------------------------------------------------------------+
//| Cleanup indicators                                               |
//+------------------------------------------------------------------+
void CFilters::Deinit()
{
   if(m_ema200Handle != INVALID_HANDLE) IndicatorRelease(m_ema200Handle);
   if(m_ema50Handle != INVALID_HANDLE) IndicatorRelease(m_ema50Handle);
   if(m_ema20Handle != INVALID_HANDLE) IndicatorRelease(m_ema20Handle);
   if(m_rsiHandle != INVALID_HANDLE) IndicatorRelease(m_rsiHandle);
   if(m_atrHandle != INVALID_HANDLE) IndicatorRelease(m_atrHandle);
}

//+------------------------------------------------------------------+
//| Filter 1: Trend Filter (200 EMA)                                 |
//| Price above 200 EMA = Bullish, below = Bearish                   |
//+------------------------------------------------------------------+
bool CFilters::CheckTrendFilter()
{
   double ema200 = GetEMA(m_ema200Handle, 1);
   double close = GetClose(1);

   if(ema200 == 0) return false;

   //--- Update market bias based on 200 EMA
   if(close > ema200)
   {
      m_marketBias = "BULLISH";
      return true;
   }
   else if(close < ema200)
   {
      m_marketBias = "BEARISH";
      return true;
   }

   m_marketBias = "NEUTRAL";
   return false;
}

//+------------------------------------------------------------------+
//| Filter 2: HTF Alignment (Higher Timeframe)                       |
//| Check if higher timeframes align with current direction          |
//+------------------------------------------------------------------+
bool CFilters::CheckHTFAlignment()
{
   //--- Get current timeframe
   ENUM_TIMEFRAMES currentTF = Period();

   //--- Determine higher timeframe
   ENUM_TIMEFRAMES htf = PERIOD_H4;
   if(currentTF >= PERIOD_H4) htf = PERIOD_D1;

   //--- Get HTF EMA200
   int htfEMA = iMA(Symbol(), htf, 200, 0, MODE_EMA, PRICE_CLOSE);
   if(htfEMA == INVALID_HANDLE) return false;

   double htfEMA200[];
   ArraySetAsSeries(htfEMA200, true);
   if(CopyBuffer(htfEMA, 0, 0, 2, htfEMA200) < 2)
   {
      IndicatorRelease(htfEMA);
      return false;
   }

   //--- Get HTF close price
   double htfClose[];
   ArraySetAsSeries(htfClose, true);
   if(CopyClose(Symbol(), htf, 0, 2, htfClose) < 2)
   {
      IndicatorRelease(htfEMA);
      return false;
   }

   //--- Check alignment
   bool htfBullish = htfClose[1] > htfEMA200[1];
   bool htfBearish = htfClose[1] < htfEMA200[1];

   IndicatorRelease(htfEMA);

   //--- Current timeframe should align with HTF
   if(m_marketBias == "BULLISH" && htfBullish) return true;
   if(m_marketBias == "BEARISH" && htfBearish) return true;

   return false;
}

//+------------------------------------------------------------------+
//| Filter 3: Market Structure (Higher Highs/Lower Lows)             |
//| Confirms trend with swing structure                              |
//+------------------------------------------------------------------+
bool CFilters::CheckMarketStructure()
{
   //--- Check last 20 bars for swing points
   double highs[20], lows[20];

   for(int i = 0; i < 20; i++)
   {
      highs[i] = GetHigh(i + 1);
      lows[i] = GetLow(i + 1);
   }

   //--- Find swing highs and lows
   bool higherHighs = false;
   bool lowerLows = false;

   //--- Simple structure check: compare recent highs/lows
   if(highs[0] > highs[10] && lows[0] > lows[10])
   {
      higherHighs = true;  // Uptrend structure
   }
   else if(highs[0] < highs[10] && lows[0] < lows[10])
   {
      lowerLows = true;    // Downtrend structure
   }

   //--- Structure should align with bias
   if(m_marketBias == "BULLISH" && higherHighs) return true;
   if(m_marketBias == "BEARISH" && lowerLows) return true;

   return false;
}

//+------------------------------------------------------------------+
//| Filter 6: Spread Filter                                          |
//| Ensures spread is within acceptable range                        |
//+------------------------------------------------------------------+
bool CFilters::CheckSpreadFilter(double spread)
{
   return spread <= m_maxSpread;
}

//+------------------------------------------------------------------+
//| Filter 7: Volatility Filter                                      |
//| Ensures market is not too volatile                               |
//+------------------------------------------------------------------+
bool CFilters::CheckVolatilityFilter(double volatility)
{
   //--- Update stored volatility
   m_volatility = volatility;

   //--- Check if volatility is within acceptable range
   if(volatility > 0 && volatility < m_maxVolatility)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 8: News Filter                                            |
//| Avoid trading during high-impact news (simplified)               |
//+------------------------------------------------------------------+
bool CFilters::CheckNewsFilter()
{
   //--- Get current time
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   //--- Avoid trading at :00 and :30 minutes (common news release times)
   if(dt.min == 0 || dt.min == 30)
   {
      //--- Check if within 5 minutes of news time
      if(dt.min <= 5 || (dt.min >= 25 && dt.min <= 35))
      {
         return false;  // Don't trade during news
      }
   }

   //--- Major news times (GMT): 8:30, 12:30, 14:00, 18:00
   int majorNewsTimes[] = {8, 12, 14, 18};
   for(int i = 0; i < ArraySize(majorNewsTimes); i++)
   {
      if(dt.hour == majorNewsTimes[i] && dt.min <= 30)
      {
         return false;  // Don't trade 30 min after major news
      }
   }

   return true;
}

//+------------------------------------------------------------------+
//| Filter 9: Volume Filter                                          |
//| Ensures sufficient market volume                                 |
//+------------------------------------------------------------------+
bool CFilters::CheckVolumeFilter()
{
   long volume = GetVolume(1);

   //--- Calculate average volume over last 20 bars
   long totalVolume = 0;
   for(int i = 1; i <= 20; i++)
   {
      totalVolume += GetVolume(i);
   }

   double avgVolume = (double)totalVolume / 20.0;

   //--- Current volume should be above 80% of average
   if(volume >= avgVolume * 0.8)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 10: Order Flow                                            |
//| Analyzes buying vs selling pressure                              |
//+------------------------------------------------------------------+
bool CFilters::CheckOrderFlow()
{
   //--- Calculate order flow from last 10 bars
   int bullishBars = 0;
   int bearishBars = 0;

   for(int i = 1; i <= 10; i++)
   {
      if(IsBullishCandle(i))
         bullishBars++;
      else if(IsBearishCandle(i))
         bearishBars++;
   }

   //--- Order flow should align with bias
   if(m_marketBias == "BULLISH" && bullishBars > bearishBars) return true;
   if(m_marketBias == "BEARISH" && bearishBars > bullishBars) return true;

   return false;
}

//+------------------------------------------------------------------+
//| Filter 11: Momentum Filter (RSI)                                 |
//| RSI between 30-70, avoiding overbought/oversold extremes         |
//+------------------------------------------------------------------+
bool CFilters::CheckMomentumFilter()
{
   double rsi = GetRSI(1);

   if(rsi == 0) return false;

   //--- For bullish: RSI should be above 50 but not overbought
   if(m_marketBias == "BULLISH")
   {
      return (rsi > 50 && rsi < 70);
   }

   //--- For bearish: RSI should be below 50 but not oversold
   if(m_marketBias == "BEARISH")
   {
      return (rsi < 50 && rsi > 30);
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 12: Confluence (Multiple Timeframe Agreement)             |
//| Checks if multiple indicators agree                              |
//+------------------------------------------------------------------+
bool CFilters::CheckConfluence()
{
   //--- Get EMAs
   double ema200 = GetEMA(m_ema200Handle, 1);
   double ema50 = GetEMA(m_ema50Handle, 1);
   double ema20 = GetEMA(m_ema20Handle, 1);
   double close = GetClose(1);

   //--- For bullish confluence
   if(m_marketBias == "BULLISH")
   {
      //--- Price above all EMAs and EMAs in order (20>50>200)
      if(close > ema20 && close > ema50 && close > ema200 &&
         ema20 > ema50 && ema50 > ema200)
      {
         return true;
      }
   }

   //--- For bearish confluence
   if(m_marketBias == "BEARISH")
   {
      //--- Price below all EMAs and EMAs in order (20<50<200)
      if(close < ema20 && close < ema50 && close < ema200 &&
         ema20 < ema50 && ema50 < ema200)
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 13: Fair Value Gap (FVG)                                  |
//| Detects imbalance/inefficiency zones                             |
//+------------------------------------------------------------------+
bool CFilters::CheckFVG()
{
   //--- FVG: Gap between candle[2] and candle[0] with candle[1] not filling it
   double high0 = GetHigh(0);
   double low0 = GetLow(0);
   double high1 = GetHigh(1);
   double low1 = GetLow(1);
   double high2 = GetHigh(2);
   double low2 = GetLow(2);

   //--- Bullish FVG: Gap down that could be filled
   if(m_marketBias == "BULLISH")
   {
      if(low0 > high2 && low1 > high2)
      {
         return true;  // Bullish FVG present
      }
   }

   //--- Bearish FVG: Gap up that could be filled
   if(m_marketBias == "BEARISH")
   {
      if(high0 < low2 && high1 < low2)
      {
         return true;  // Bearish FVG present
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 14: Liquidity Sweep                                       |
//| Detects stop hunts and liquidity grabs                           |
//+------------------------------------------------------------------+
bool CFilters::CheckLiquiditySweep()
{
   //--- Check if recent candle swept previous high/low then reversed
   double high1 = GetHigh(1);
   double low1 = GetLow(1);
   double close1 = GetClose(1);

   //--- Find recent swing high/low (last 20 bars)
   double swingHigh = high1;
   double swingLow = low1;

   for(int i = 2; i <= 20; i++)
   {
      if(GetHigh(i) > swingHigh) swingHigh = GetHigh(i);
      if(GetLow(i) < swingLow) swingLow = GetLow(i);
   }

   //--- Bullish liquidity sweep: Swept below low then closed higher
   if(m_marketBias == "BULLISH")
   {
      if(low1 < swingLow && close1 > GetOpen(1))
      {
         return true;  // Liquidity grabbed below, then reversed up
      }
   }

   //--- Bearish liquidity sweep: Swept above high then closed lower
   if(m_marketBias == "BEARISH")
   {
      if(high1 > swingHigh && close1 < GetOpen(1))
      {
         return true;  // Liquidity grabbed above, then reversed down
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 15: CHoCH/BOS (Change of Character / Break of Structure)  |
//| Identifies trend changes and continuations                       |
//+------------------------------------------------------------------+
bool CFilters::CheckCHoCH_BOS()
{
   //--- Simplified: Check if we broke previous structure
   double high5 = GetHigh(5);
   double low5 = GetLow(5);
   double close1 = GetClose(1);

   //--- Bullish BOS: Broke above previous high
   if(m_marketBias == "BULLISH" && close1 > high5)
   {
      return true;
   }

   //--- Bearish BOS: Broke below previous low
   if(m_marketBias == "BEARISH" && close1 < low5)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 16: Divergence (RSI vs Price)                             |
//| Detects divergence between price and momentum                    |
//+------------------------------------------------------------------+
bool CFilters::CheckDivergence()
{
   //--- Get RSI values
   double rsi1 = GetRSI(1);
   double rsi10 = GetRSI(10);

   //--- Get price values
   double close1 = GetClose(1);
   double close10 = GetClose(10);

   //--- Bullish divergence: Price making lower lows, RSI making higher lows
   if(m_marketBias == "BULLISH")
   {
      if(close1 < close10 && rsi1 > rsi10)
      {
         return true;  // Bullish divergence
      }
   }

   //--- Bearish divergence: Price making higher highs, RSI making lower highs
   if(m_marketBias == "BEARISH")
   {
      if(close1 > close10 && rsi1 < rsi10)
      {
         return true;  // Bearish divergence
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 17: Smart Money Concepts                                  |
//| Combines multiple smart money principles                         |
//+------------------------------------------------------------------+
bool CFilters::CheckSmartMoney()
{
   //--- Check for smart money characteristics:
   //--- 1. Order blocks (strong rejection candles)
   //--- 2. Breaker blocks (failed support/resistance)
   //--- 3. Mitigation zones

   bool hasOrderBlock = false;

   //--- Look for strong rejection candles in last 10 bars
   for(int i = 1; i <= 10; i++)
   {
      double bodySize = MathAbs(GetClose(i) - GetOpen(i));
      double wickSize = 0;

      if(IsBullishCandle(i))
      {
         wickSize = GetClose(i) - GetLow(i);  // Lower wick
      }
      else
      {
         wickSize = GetHigh(i) - GetClose(i);  // Upper wick
      }

      //--- Strong rejection if wick is 2x body size
      if(wickSize > bodySize * 2.0)
      {
         hasOrderBlock = true;
         break;
      }
   }

   return hasOrderBlock;
}

//+------------------------------------------------------------------+
//| Filter 18: Time of Day Filter                                    |
//| Trade only during optimal hours                                  |
//+------------------------------------------------------------------+
bool CFilters::CheckTimeFilter()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   //--- Avoid trading during low liquidity hours (23:00 - 02:00 GMT)
   if(dt.hour >= 23 || dt.hour < 2)
   {
      return false;
   }

   //--- Best trading hours: London open to NY close (7:00 - 21:00 GMT)
   if(dt.hour >= 7 && dt.hour <= 21)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Filter 19: Currency Correlation                                  |
//| Check correlated pairs for confirmation                          |
//+------------------------------------------------------------------+
bool CFilters::CheckCorrelation()
{
   //--- For EUR/USD, check DXY (US Dollar Index) correlation
   //--- Simplified: Just return true for now
   //--- Full implementation would check correlated pairs

   string currentSymbol = Symbol();

   //--- For now, accept all symbols
   //--- TODO: Implement actual correlation checking
   return true;
}

//+------------------------------------------------------------------+
//| Calculate current volatility (ATR-based)                         |
//+------------------------------------------------------------------+
double CFilters::CalculateVolatility()
{
   double atr = GetATR(1);
   double close = GetClose(1);

   if(close == 0) return 0;

   //--- Volatility as percentage of price
   return (atr / close) * 100.0;
}

//+------------------------------------------------------------------+
//| Get market bias                                                  |
//+------------------------------------------------------------------+
string CFilters::GetMarketBias()
{
   return m_marketBias;
}

//+------------------------------------------------------------------+
//| Get market regime                                                |
//+------------------------------------------------------------------+
string CFilters::GetMarketRegime()
{
   //--- Calculate ADX to determine trending vs ranging
   double atr = GetATR(1);
   double avgATR = 0;

   for(int i = 1; i <= 20; i++)
   {
      avgATR += GetATR(i);
   }
   avgATR /= 20.0;

   //--- If current ATR is significantly higher than average, it's trending
   if(atr > avgATR * 1.2)
   {
      m_marketRegime = "TRENDING";
   }
   else if(atr < avgATR * 0.8)
   {
      m_marketRegime = "RANGING";
   }
   else
   {
      m_marketRegime = "TRANSITIONING";
   }

   return m_marketRegime;
}

//+------------------------------------------------------------------+
//| Helper: Get EMA value                                            |
//+------------------------------------------------------------------+
double CFilters::GetEMA(int handle, int shift = 0)
{
   double buffer[];
   ArraySetAsSeries(buffer, true);

   if(CopyBuffer(handle, 0, 0, shift + 2, buffer) < shift + 2)
   {
      return 0;
   }

   return buffer[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get RSI value                                            |
//+------------------------------------------------------------------+
double CFilters::GetRSI(int shift = 0)
{
   double buffer[];
   ArraySetAsSeries(buffer, true);

   if(CopyBuffer(m_rsiHandle, 0, 0, shift + 2, buffer) < shift + 2)
   {
      return 0;
   }

   return buffer[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get ATR value                                            |
//+------------------------------------------------------------------+
double CFilters::GetATR(int shift = 0)
{
   double buffer[];
   ArraySetAsSeries(buffer, true);

   if(CopyBuffer(m_atrHandle, 0, 0, shift + 2, buffer) < shift + 2)
   {
      return 0;
   }

   return buffer[shift];
}

//+------------------------------------------------------------------+
//| Helper: Check if candle is bullish                               |
//+------------------------------------------------------------------+
bool CFilters::IsBullishCandle(int shift = 1)
{
   return GetClose(shift) > GetOpen(shift);
}

//+------------------------------------------------------------------+
//| Helper: Check if candle is bearish                               |
//+------------------------------------------------------------------+
bool CFilters::IsBearishCandle(int shift = 1)
{
   return GetClose(shift) < GetOpen(shift);
}

//+------------------------------------------------------------------+
//| Helper: Get High price                                           |
//+------------------------------------------------------------------+
double CFilters::GetHigh(int shift)
{
   double high[];
   ArraySetAsSeries(high, true);
   if(CopyHigh(Symbol(), PERIOD_CURRENT, 0, shift + 2, high) < shift + 2)
      return 0;
   return high[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get Low price                                            |
//+------------------------------------------------------------------+
double CFilters::GetLow(int shift)
{
   double low[];
   ArraySetAsSeries(low, true);
   if(CopyLow(Symbol(), PERIOD_CURRENT, 0, shift + 2, low) < shift + 2)
      return 0;
   return low[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get Close price                                          |
//+------------------------------------------------------------------+
double CFilters::GetClose(int shift)
{
   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(Symbol(), PERIOD_CURRENT, 0, shift + 2, close) < shift + 2)
      return 0;
   return close[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get Open price                                           |
//+------------------------------------------------------------------+
double CFilters::GetOpen(int shift)
{
   double open[];
   ArraySetAsSeries(open, true);
   if(CopyOpen(Symbol(), PERIOD_CURRENT, 0, shift + 2, open) < shift + 2)
      return 0;
   return open[shift];
}

//+------------------------------------------------------------------+
//| Helper: Get Volume                                               |
//+------------------------------------------------------------------+
long CFilters::GetVolume(int shift)
{
   long volume[];
   ArraySetAsSeries(volume, true);
   if(CopyTickVolume(Symbol(), PERIOD_CURRENT, 0, shift + 2, volume) < shift + 2)
      return 0;
   return volume[shift];
}
