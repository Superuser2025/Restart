//+------------------------------------------------------------------+
//|                                                  RiskManager.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| Professional Risk Management System                              |
//| - Position sizing, daily limits, drawdown protection             |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CRiskManager Class                                               |
//| Manages all risk-related calculations and limits                 |
//+------------------------------------------------------------------+
class CRiskManager
{
private:
   double            m_riskPercent;         // Risk per trade (%)
   double            m_maxDailyLoss;        // Max daily loss (%)
   double            m_maxDailyProfit;      // Max daily profit target (%)
   int               m_maxDailyTrades;      // Max trades per day

   //--- Account info
   double            m_accountBalance;
   double            m_accountEquity;
   double            m_dailyStartBalance;

public:
                     CRiskManager();
                    ~CRiskManager();

   //--- Initialization
   bool              Init(double riskPercent, double maxDailyLoss, double maxDailyProfit, int maxDailyTrades);

   //--- Position sizing
   double            CalculatePositionSize(string symbol, double riskPercent);
   double            CalculatePositionSizeFromDistance(string symbol, double entryPrice, double stopLoss);

   //--- Risk checks
   bool              CanTrade(int numTradesToday, double todayPnL);
   bool              IsWithinDailyLossLimit(double todayPnL);
   bool              IsWithinDailyProfitTarget(double todayPnL);
   bool              IsWithinTradeLimit(int numTradesToday);
   bool              IsWithinDrawdownLimit();

   //--- Utility
   double            CalculateStopLossDistance(double entryPrice, double stopLoss);
   double            CalculateRiskAmount();
   void              UpdateAccountInfo();
   double            GetRiskRewardRatio(double entry, double sl, double tp);

   //--- Getters
   double            GetAccountBalance() { return m_accountBalance; }
   double            GetAccountEquity() { return m_accountEquity; }
   double            GetRiskPercent() { return m_riskPercent; }

private:
   //--- Helper methods
   double            GetTickValue(string symbol);
   double            GetTickSize(string symbol);
   double            GetMinLot(string symbol);
   double            GetMaxLot(string symbol);
   double            GetLotStep(string symbol);
   double            NormalizeLot(string symbol, double lot);
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CRiskManager::CRiskManager()
{
   m_riskPercent = 0.5;
   m_maxDailyLoss = 2.0;
   m_maxDailyProfit = 5.0;
   m_maxDailyTrades = 5;

   m_accountBalance = 0;
   m_accountEquity = 0;
   m_dailyStartBalance = 0;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CRiskManager::~CRiskManager()
{
}

//+------------------------------------------------------------------+
//| Initialize risk manager                                          |
//+------------------------------------------------------------------+
bool CRiskManager::Init(double riskPercent, double maxDailyLoss, double maxDailyProfit, int maxDailyTrades)
{
   m_riskPercent = riskPercent;
   m_maxDailyLoss = maxDailyLoss;
   m_maxDailyProfit = maxDailyProfit;
   m_maxDailyTrades = maxDailyTrades;

   //--- Update account info
   UpdateAccountInfo();
   m_dailyStartBalance = m_accountBalance;

   Print("Risk Manager initialized:");
   Print("  Risk per trade: ", m_riskPercent, "%");
   Print("  Max daily loss: ", m_maxDailyLoss, "%");
   Print("  Max daily profit: ", m_maxDailyProfit, "%");
   Print("  Max daily trades: ", m_maxDailyTrades);
   Print("  Account balance: $", m_accountBalance);

   return true;
}

//+------------------------------------------------------------------+
//| Calculate position size based on risk percentage                 |
//+------------------------------------------------------------------+
double CRiskManager::CalculatePositionSize(string symbol, double riskPercent)
{
   UpdateAccountInfo();

   //--- Calculate risk amount in account currency
   double riskAmount = m_accountBalance * (riskPercent / 100.0);

   //--- Get typical stop loss distance (e.g., 50 pips)
   double typicalSLPips = 50.0;
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   //--- Adjust for 5-digit brokers
   double pipSize = point;
   if(digits == 5 || digits == 3)
   {
      pipSize = point * 10;
   }

   double slDistance = typicalSLPips * pipSize;

   //--- Calculate position size
   double tickValue = GetTickValue(symbol);
   double tickSize = GetTickSize(symbol);

   if(tickValue == 0 || tickSize == 0 || slDistance == 0)
   {
      Print("Error calculating position size: Invalid parameters");
      return GetMinLot(symbol);
   }

   double lotSize = riskAmount / (slDistance / tickSize * tickValue);

   //--- Normalize lot size
   lotSize = NormalizeLot(symbol, lotSize);

   Print("Position Size Calculation:");
   Print("  Risk Amount: $", riskAmount);
   Print("  SL Distance: ", slDistance / pipSize, " pips");
   Print("  Lot Size: ", lotSize);

   return lotSize;
}

//+------------------------------------------------------------------+
//| Calculate position size from specific SL distance                |
//+------------------------------------------------------------------+
double CRiskManager::CalculatePositionSizeFromDistance(string symbol, double entryPrice, double stopLoss)
{
   UpdateAccountInfo();

   //--- Calculate risk amount
   double riskAmount = m_accountBalance * (m_riskPercent / 100.0);

   //--- Calculate SL distance
   double slDistance = MathAbs(entryPrice - stopLoss);

   if(slDistance == 0)
   {
      Print("Error: Stop loss distance is zero");
      return GetMinLot(symbol);
   }

   //--- Calculate position size
   double tickValue = GetTickValue(symbol);
   double tickSize = GetTickSize(symbol);

   if(tickValue == 0 || tickSize == 0)
   {
      Print("Error calculating position size: Invalid tick parameters");
      return GetMinLot(symbol);
   }

   double lotSize = riskAmount / (slDistance / tickSize * tickValue);

   //--- Normalize lot size
   lotSize = NormalizeLot(symbol, lotSize);

   return lotSize;
}

//+------------------------------------------------------------------+
//| Check if trading is allowed                                      |
//+------------------------------------------------------------------+
bool CRiskManager::CanTrade(int numTradesToday, double todayPnL)
{
   //--- Check daily loss limit
   if(!IsWithinDailyLossLimit(todayPnL))
   {
      Print("Trading stopped: Daily loss limit reached");
      return false;
   }

   //--- Check daily profit target
   if(!IsWithinDailyProfitTarget(todayPnL))
   {
      Print("Trading stopped: Daily profit target reached");
      return false;
   }

   //--- Check trade limit
   if(!IsWithinTradeLimit(numTradesToday))
   {
      Print("Trading stopped: Daily trade limit reached");
      return false;
   }

   //--- Check drawdown limit
   if(!IsWithinDrawdownLimit())
   {
      Print("Trading stopped: Drawdown limit exceeded");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check if within daily loss limit                                 |
//+------------------------------------------------------------------+
bool CRiskManager::IsWithinDailyLossLimit(double todayPnL)
{
   UpdateAccountInfo();

   double maxLossAmount = m_dailyStartBalance * (m_maxDailyLoss / 100.0);

   if(todayPnL < -maxLossAmount)
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check if within daily profit target                              |
//+------------------------------------------------------------------+
bool CRiskManager::IsWithinDailyProfitTarget(double todayPnL)
{
   UpdateAccountInfo();

   double profitTarget = m_dailyStartBalance * (m_maxDailyProfit / 100.0);

   //--- If profit target reached, stop trading for the day
   if(todayPnL >= profitTarget)
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check if within daily trade limit                                |
//+------------------------------------------------------------------+
bool CRiskManager::IsWithinTradeLimit(int numTradesToday)
{
   if(numTradesToday >= m_maxDailyTrades)
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check if within drawdown limit                                   |
//+------------------------------------------------------------------+
bool CRiskManager::IsWithinDrawdownLimit()
{
   UpdateAccountInfo();

   //--- Calculate current drawdown from balance
   double drawdown = ((m_accountBalance - m_accountEquity) / m_accountBalance) * 100.0;

   //--- Maximum acceptable drawdown: 10%
   double maxDrawdown = 10.0;

   if(drawdown > maxDrawdown)
   {
      Print("Current drawdown: ", drawdown, "% exceeds limit of ", maxDrawdown, "%");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Calculate stop loss distance                                     |
//+------------------------------------------------------------------+
double CRiskManager::CalculateStopLossDistance(double entryPrice, double stopLoss)
{
   return MathAbs(entryPrice - stopLoss);
}

//+------------------------------------------------------------------+
//| Calculate risk amount in account currency                        |
//+------------------------------------------------------------------+
double CRiskManager::CalculateRiskAmount()
{
   UpdateAccountInfo();
   return m_accountBalance * (m_riskPercent / 100.0);
}

//+------------------------------------------------------------------+
//| Update account information                                       |
//+------------------------------------------------------------------+
void CRiskManager::UpdateAccountInfo()
{
   m_accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   m_accountEquity = AccountInfoDouble(ACCOUNT_EQUITY);

   //--- If daily start balance is 0, set it
   if(m_dailyStartBalance == 0)
   {
      m_dailyStartBalance = m_accountBalance;
   }
}

//+------------------------------------------------------------------+
//| Calculate Risk:Reward ratio                                      |
//+------------------------------------------------------------------+
double CRiskManager::GetRiskRewardRatio(double entry, double sl, double tp)
{
   double risk = MathAbs(entry - sl);
   double reward = MathAbs(tp - entry);

   if(risk == 0) return 0;

   return reward / risk;
}

//+------------------------------------------------------------------+
//| Get tick value for symbol                                        |
//+------------------------------------------------------------------+
double CRiskManager::GetTickValue(string symbol)
{
   return SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
}

//+------------------------------------------------------------------+
//| Get tick size for symbol                                         |
//+------------------------------------------------------------------+
double CRiskManager::GetTickSize(string symbol)
{
   return SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
}

//+------------------------------------------------------------------+
//| Get minimum lot size                                             |
//+------------------------------------------------------------------+
double CRiskManager::GetMinLot(string symbol)
{
   double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   if(minLot == 0) minLot = 0.01;
   return minLot;
}

//+------------------------------------------------------------------+
//| Get maximum lot size                                             |
//+------------------------------------------------------------------+
double CRiskManager::GetMaxLot(string symbol)
{
   double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   if(maxLot == 0) maxLot = 100.0;
   return maxLot;
}

//+------------------------------------------------------------------+
//| Get lot step                                                      |
//+------------------------------------------------------------------+
double CRiskManager::GetLotStep(string symbol)
{
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   if(lotStep == 0) lotStep = 0.01;
   return lotStep;
}

//+------------------------------------------------------------------+
//| Normalize lot size to broker requirements                        |
//+------------------------------------------------------------------+
double CRiskManager::NormalizeLot(string symbol, double lot)
{
   double minLot = GetMinLot(symbol);
   double maxLot = GetMaxLot(symbol);
   double lotStep = GetLotStep(symbol);

   //--- Round to lot step
   lot = MathRound(lot / lotStep) * lotStep;

   //--- Ensure within limits
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;

   //--- Round to 2 decimal places
   lot = NormalizeDouble(lot, 2);

   return lot;
}
