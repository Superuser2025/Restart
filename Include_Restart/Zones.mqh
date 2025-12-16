//+------------------------------------------------------------------+
//|                                                        Zones.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| Supply/Demand Zone Detection and Management                      |
//| - Identifies institutional supply/demand zones                   |
//| - Tracks zone strength and touches                               |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Zone Structure                                                    |
//+------------------------------------------------------------------+
struct SZone
{
   double            topPrice;              // Zone top
   double            bottomPrice;           // Zone bottom
   int               type;                  // 0 = demand, 1 = supply
   double            strength;              // Zone strength (1-10)
   int               touches;               // Number of times tested
   datetime          created;               // Creation time
   bool              broken;                // Has zone been broken
};

//+------------------------------------------------------------------+
//| CZones Class                                                     |
//| Manages supply/demand zones                                      |
//+------------------------------------------------------------------+
class CZones
{
private:
   SZone             m_zones[];             // Array of zones
   int               m_lookback;            // Lookback period
   double            m_minStrength;         // Minimum strength threshold
   color             m_supplyColor;         // Supply zone color
   color             m_demandColor;         // Demand zone color
   int               m_maxZones;            // Maximum zones to track

public:
                     CZones();
                    ~CZones();

   //--- Initialization
   bool              Init(int lookback, double minStrength, color supplyColor, color demandColor);

   //--- Zone management
   void              UpdateZones();
   void              DetectNewZones();
   void              RemoveWeakZones();
   void              RemoveAllZones();
   void              DrawZones();

   //--- Zone queries
   bool              IsNearZone(double price = 0);
   double            GetNearestSupplyZone();
   double            GetNearestDemandZone();
   int               GetZoneCount() { return ArraySize(m_zones); }

private:
   //--- Helper methods
   bool              IsSupplyZone(int startBar);
   bool              IsDemandZone(int startBar);
   double            CalculateZoneStrength(int startBar, int type);
   void              AddZone(double top, double bottom, int type, double strength);
   void              UpdateZoneTouches();
   bool              IsPriceInZone(double price, const SZone &zone);
   double            GetHigh(int shift);
   double            GetLow(int shift);
   double            GetClose(int shift);
   double            GetOpen(int shift);
   long              GetVolume(int shift);
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CZones::CZones()
{
   m_lookback = 100;
   m_minStrength = 2.0;
   m_supplyColor = clrCrimson;
   m_demandColor = clrDodgerBlue;
   m_maxZones = 50;
   ArrayResize(m_zones, 0);
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CZones::~CZones()
{
   RemoveAllZones();
}

//+------------------------------------------------------------------+
//| Initialize zones manager                                         |
//+------------------------------------------------------------------+
bool CZones::Init(int lookback, double minStrength, color supplyColor, color demandColor)
{
   m_lookback = lookback;
   m_minStrength = minStrength;
   m_supplyColor = supplyColor;
   m_demandColor = demandColor;

   Print("Zones manager initialized (lookback: ", m_lookback, ", min strength: ", m_minStrength, ")");
   return true;
}

//+------------------------------------------------------------------+
//| Update all zones                                                  |
//+------------------------------------------------------------------+
void CZones::UpdateZones()
{
   //--- Detect new zones
   DetectNewZones();

   //--- Update zone touches
   UpdateZoneTouches();

   //--- Remove weak or broken zones
   RemoveWeakZones();

   //--- Draw zones on chart
   DrawZones();
}

//+------------------------------------------------------------------+
//| Detect new supply/demand zones                                   |
//+------------------------------------------------------------------+
void CZones::DetectNewZones()
{
   //--- Don't add too many zones
   if(ArraySize(m_zones) >= m_maxZones)
      return;

   //--- Scan for new zones in recent bars
   for(int i = 10; i < m_lookback && i < Bars(Symbol(), PERIOD_CURRENT); i++)
   {
      //--- Check for supply zone
      if(IsSupplyZone(i))
      {
         double strength = CalculateZoneStrength(i, 1);
         if(strength >= m_minStrength)
         {
            double top = GetHigh(i);
            double bottom = GetLow(i) - (GetHigh(i) - GetLow(i)) * 0.1;  // Extend zone slightly
            AddZone(top, bottom, 1, strength);
         }
      }

      //--- Check for demand zone
      if(IsDemandZone(i))
      {
         double strength = CalculateZoneStrength(i, 0);
         if(strength >= m_minStrength)
         {
            double bottom = GetLow(i);
            double top = GetHigh(i) + (GetHigh(i) - GetLow(i)) * 0.1;  // Extend zone slightly
            AddZone(top, bottom, 0, strength);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check if bar is a supply zone (strong rejection from top)        |
//+------------------------------------------------------------------+
bool CZones::IsSupplyZone(int startBar)
{
   //--- Supply zone characteristics:
   //--- 1. Strong bearish candle
   //--- 2. High volume
   //--- 3. Price moved down significantly after

   double open = GetOpen(startBar);
   double close = GetClose(startBar);
   double high = GetHigh(startBar);
   double low = GetLow(startBar);

   //--- Must be bearish
   if(close >= open) return false;

   //--- Large bearish body (at least 60% of range)
   double range = high - low;
   double body = open - close;

   if(body < range * 0.6) return false;

   //--- Check volume is above average
   long volume = GetVolume(startBar);
   long avgVolume = 0;
   for(int i = startBar; i < startBar + 20; i++)
   {
      avgVolume += GetVolume(i);
   }
   avgVolume /= 20;

   if(volume < avgVolume * 1.2) return false;

   //--- Price should have dropped after this zone
   double priceAfter = GetClose(startBar - 5);
   if(priceAfter >= low) return false;

   return true;
}

//+------------------------------------------------------------------+
//| Check if bar is a demand zone (strong rejection from bottom)     |
//+------------------------------------------------------------------+
bool CZones::IsDemandZone(int startBar)
{
   //--- Demand zone characteristics:
   //--- 1. Strong bullish candle
   //--- 2. High volume
   //--- 3. Price moved up significantly after

   double open = GetOpen(startBar);
   double close = GetClose(startBar);
   double high = GetHigh(startBar);
   double low = GetLow(startBar);

   //--- Must be bullish
   if(close <= open) return false;

   //--- Large bullish body (at least 60% of range)
   double range = high - low;
   double body = close - open;

   if(body < range * 0.6) return false;

   //--- Check volume is above average
   long volume = GetVolume(startBar);
   long avgVolume = 0;
   for(int i = startBar; i < startBar + 20; i++)
   {
      avgVolume += GetVolume(i);
   }
   avgVolume /= 20;

   if(volume < avgVolume * 1.2) return false;

   //--- Price should have risen after this zone
   double priceAfter = GetClose(startBar - 5);
   if(priceAfter <= high) return false;

   return true;
}

//+------------------------------------------------------------------+
//| Calculate zone strength                                          |
//+------------------------------------------------------------------+
double CZones::CalculateZoneStrength(int startBar, int type)
{
   double strength = 1.0;

   //--- Factor 1: Candle size (larger = stronger)
   double range = GetHigh(startBar) - GetLow(startBar);
   double avgRange = 0;
   for(int i = startBar; i < startBar + 20; i++)
   {
      avgRange += GetHigh(i) - GetLow(i);
   }
   avgRange /= 20.0;

   if(range > avgRange * 1.5) strength += 2.0;
   else if(range > avgRange * 1.2) strength += 1.0;

   //--- Factor 2: Volume (higher = stronger)
   long volume = GetVolume(startBar);
   long avgVolume = 0;
   for(int i = startBar; i < startBar + 20; i++)
   {
      avgVolume += GetVolume(i);
   }
   avgVolume /= 20;

   if(volume > avgVolume * 2.0) strength += 3.0;
   else if(volume > avgVolume * 1.5) strength += 2.0;
   else if(volume > avgVolume * 1.2) strength += 1.0;

   //--- Factor 3: Price reaction (how far price moved away)
   double closeAfter = GetClose(MathMax(0, startBar - 10));
   double reactionDistance = 0;

   if(type == 1)  // Supply
   {
      reactionDistance = (GetHigh(startBar) - closeAfter) / avgRange;
   }
   else  // Demand
   {
      reactionDistance = (closeAfter - GetLow(startBar)) / avgRange;
   }

   if(reactionDistance > 3.0) strength += 2.0;
   else if(reactionDistance > 2.0) strength += 1.0;

   return strength;
}

//+------------------------------------------------------------------+
//| Add a new zone                                                    |
//+------------------------------------------------------------------+
void CZones::AddZone(double top, double bottom, int type, double strength)
{
   //--- Check if zone already exists (overlapping)
   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      //--- Check for overlap
      if((bottom >= m_zones[i].bottomPrice && bottom <= m_zones[i].topPrice) ||
         (top >= m_zones[i].bottomPrice && top <= m_zones[i].topPrice))
      {
         //--- Zone overlaps, update if stronger
         if(strength > m_zones[i].strength)
         {
            m_zones[i].topPrice = top;
            m_zones[i].bottomPrice = bottom;
            m_zones[i].strength = strength;
         }
         return;  // Don't add duplicate
      }
   }

   //--- Add new zone
   int size = ArraySize(m_zones);
   ArrayResize(m_zones, size + 1);

   m_zones[size].topPrice = top;
   m_zones[size].bottomPrice = bottom;
   m_zones[size].type = type;
   m_zones[size].strength = strength;
   m_zones[size].touches = 0;
   m_zones[size].created = TimeCurrent();
   m_zones[size].broken = false;
}

//+------------------------------------------------------------------+
//| Update zone touches                                              |
//+------------------------------------------------------------------+
void CZones::UpdateZoneTouches()
{
   double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);

   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      //--- Check if price is touching zone
      if(IsPriceInZone(currentPrice, m_zones[i]))
      {
         m_zones[i].touches++;

         //--- If touched too many times, mark as broken
         if(m_zones[i].touches > 3)
         {
            m_zones[i].broken = true;
            m_zones[i].strength *= 0.5;  // Reduce strength
         }
      }

      //--- Check if zone is broken (price closed through it)
      if(m_zones[i].type == 1)  // Supply zone
      {
         if(currentPrice > m_zones[i].topPrice)
         {
            m_zones[i].broken = true;
         }
      }
      else  // Demand zone
      {
         if(currentPrice < m_zones[i].bottomPrice)
         {
            m_zones[i].broken = true;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Remove weak or broken zones                                      |
//+------------------------------------------------------------------+
void CZones::RemoveWeakZones()
{
   for(int i = ArraySize(m_zones) - 1; i >= 0; i--)
   {
      //--- Remove if broken
      if(m_zones[i].broken)
      {
         //--- Remove object from chart
         string name = "Zone_" + IntegerToString(i);
         ObjectDelete(0, name);

         //--- Remove from array
         for(int j = i; j < ArraySize(m_zones) - 1; j++)
         {
            m_zones[j] = m_zones[j + 1];
         }
         ArrayResize(m_zones, ArraySize(m_zones) - 1);
         continue;
      }

      //--- Remove if too old (older than 100 bars)
      if(TimeCurrent() - m_zones[i].created > PeriodSeconds() * 100)
      {
         string name = "Zone_" + IntegerToString(i);
         ObjectDelete(0, name);

         for(int j = i; j < ArraySize(m_zones) - 1; j++)
         {
            m_zones[j] = m_zones[j + 1];
         }
         ArrayResize(m_zones, ArraySize(m_zones) - 1);
      }
   }
}

//+------------------------------------------------------------------+
//| Remove all zones from chart                                      |
//+------------------------------------------------------------------+
void CZones::RemoveAllZones()
{
   //--- Remove all zone objects
   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      string name = "Zone_" + IntegerToString(i);
      ObjectDelete(0, name);
   }

   ArrayResize(m_zones, 0);
}

//+------------------------------------------------------------------+
//| Draw zones on chart                                              |
//+------------------------------------------------------------------+
void CZones::DrawZones()
{
   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      string name = "Zone_" + IntegerToString(i);

      //--- Create rectangle if doesn't exist
      if(ObjectFind(0, name) < 0)
      {
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
      }

      //--- Set rectangle properties
      datetime timeNow = TimeCurrent();
      datetime timeBack = timeNow - PeriodSeconds() * 50;

      ObjectSetInteger(0, name, OBJPROP_TIME, 0, timeBack);
      ObjectSetDouble(0, name, OBJPROP_PRICE, 0, m_zones[i].topPrice);
      ObjectSetInteger(0, name, OBJPROP_TIME, 1, timeNow);
      ObjectSetDouble(0, name, OBJPROP_PRICE, 1, m_zones[i].bottomPrice);

      //--- Set color based on type
      color zoneColor = (m_zones[i].type == 1) ? m_supplyColor : m_demandColor;
      ObjectSetInteger(0, name, OBJPROP_COLOR, zoneColor);
      ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);

      //--- Set transparency based on strength
      int alpha = (int)(m_zones[i].strength * 20);
      if(alpha > 100) alpha = 100;
      ObjectSetInteger(0, name, OBJPROP_BGCOLOR, zoneColor);
   }
}

//+------------------------------------------------------------------+
//| Check if price is near any zone                                  |
//+------------------------------------------------------------------+
bool CZones::IsNearZone(double price = 0)
{
   if(price == 0)
      price = SymbolInfoDouble(Symbol(), SYMBOL_BID);

   //--- Check all zones
   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      if(!m_zones[i].broken)
      {
         if(IsPriceInZone(price, m_zones[i]))
         {
            return true;
         }

         //--- Also check if price is within 0.5% of zone
         double range = m_zones[i].topPrice - m_zones[i].bottomPrice;
         double buffer = range * 0.5;

         if(price >= m_zones[i].bottomPrice - buffer &&
            price <= m_zones[i].topPrice + buffer)
         {
            return true;
         }
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Get nearest supply zone                                          |
//+------------------------------------------------------------------+
double CZones::GetNearestSupplyZone()
{
   double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   double nearestSupply = 0;
   double minDistance = 999999;

   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      if(m_zones[i].type == 1 && !m_zones[i].broken)  // Supply zone
      {
         double distance = m_zones[i].bottomPrice - currentPrice;

         if(distance > 0 && distance < minDistance)
         {
            minDistance = distance;
            nearestSupply = m_zones[i].bottomPrice;
         }
      }
   }

   return nearestSupply;
}

//+------------------------------------------------------------------+
//| Get nearest demand zone                                          |
//+------------------------------------------------------------------+
double CZones::GetNearestDemandZone()
{
   double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
   double nearestDemand = 0;
   double minDistance = 999999;

   for(int i = 0; i < ArraySize(m_zones); i++)
   {
      if(m_zones[i].type == 0 && !m_zones[i].broken)  // Demand zone
      {
         double distance = currentPrice - m_zones[i].topPrice;

         if(distance > 0 && distance < minDistance)
         {
            minDistance = distance;
            nearestDemand = m_zones[i].topPrice;
         }
      }
   }

   return nearestDemand;
}

//+------------------------------------------------------------------+
//| Check if price is in zone                                        |
//+------------------------------------------------------------------+
bool CZones::IsPriceInZone(double price, const SZone &zone)
{
   return (price >= zone.bottomPrice && price <= zone.topPrice);
}

//+------------------------------------------------------------------+
//| Helper: Get High price                                           |
//+------------------------------------------------------------------+
double CZones::GetHigh(int shift)
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
double CZones::GetLow(int shift)
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
double CZones::GetClose(int shift)
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
double CZones::GetOpen(int shift)
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
long CZones::GetVolume(int shift)
{
   long volume[];
   ArraySetAsSeries(volume, true);
   if(CopyTickVolume(Symbol(), PERIOD_CURRENT, 0, shift + 2, volume) < shift + 2)
      return 0;
   return volume[shift];
}
