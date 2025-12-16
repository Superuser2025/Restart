//+------------------------------------------------------------------+
//|                                                     Patterns.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| Pattern Recognition System                                       |
//| - Double Top/Bottom, Head & Shoulders, Triangles, Wedges, etc.  |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CPatterns Class                                                  |
//| Detects chart patterns                                           |
//+------------------------------------------------------------------+
class CPatterns
{
private:
   string            m_activePattern;
   int               m_lookbackBars;

public:
                     CPatterns();
                    ~CPatterns();

   //--- Initialization
   bool              Init(int lookbackBars = 100);

   //--- Pattern detection
   string            DetectActivePattern(bool checkDoubleTop,
                                        bool checkHeadShoulders,
                                        bool checkTriangle,
                                        bool checkWedge,
                                        bool checkChannel);

   //--- Individual pattern detectors
   bool              DetectDoubleTop();
   bool              DetectDoubleBottom();
   bool              DetectHeadAndShoulders();
   bool              DetectInverseHeadAndShoulders();
   bool              DetectAscendingTriangle();
   bool              DetectDescendingTriangle();
   bool              DetectSymmetricalTriangle();
   bool              DetectRisingWedge();
   bool              DetectFallingWedge();
   bool              DetectAscendingChannel();
   bool              DetectDescendingChannel();

   //--- Getters
   string            GetActivePattern() { return m_activePattern; }

private:
   //--- Helper methods
   bool              FindSwingHighs(double &highs[], int &indices[], int count);
   bool              FindSwingLows(double &lows[], int &indices[], int count);
   double            GetHigh(int shift);
   double            GetLow(int shift);
   double            GetClose(int shift);
   double            GetOpen(int shift);
   bool              IsSwingHigh(int index);
   bool              IsSwingLow(int index);
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CPatterns::CPatterns()
{
   m_activePattern = "NONE";
   m_lookbackBars = 100;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CPatterns::~CPatterns()
{
}

//+------------------------------------------------------------------+
//| Initialize pattern detector                                      |
//+------------------------------------------------------------------+
bool CPatterns::Init(int lookbackBars = 100)
{
   m_lookbackBars = lookbackBars;
   Print("Pattern detector initialized (lookback: ", m_lookbackBars, " bars)");
   return true;
}

//+------------------------------------------------------------------+
//| Detect active pattern                                            |
//+------------------------------------------------------------------+
string CPatterns::DetectActivePattern(bool checkDoubleTop,
                                     bool checkHeadShoulders,
                                     bool checkTriangle,
                                     bool checkWedge,
                                     bool checkChannel)
{
   m_activePattern = "NONE";

   //--- Check for Double Top/Bottom
   if(checkDoubleTop)
   {
      if(DetectDoubleTop())
      {
         m_activePattern = "DOUBLE TOP";
         return m_activePattern;
      }
      if(DetectDoubleBottom())
      {
         m_activePattern = "DOUBLE BOTTOM";
         return m_activePattern;
      }
   }

   //--- Check for Head & Shoulders
   if(checkHeadShoulders)
   {
      if(DetectHeadAndShoulders())
      {
         m_activePattern = "HEAD & SHOULDERS";
         return m_activePattern;
      }
      if(DetectInverseHeadAndShoulders())
      {
         m_activePattern = "INVERSE H&S";
         return m_activePattern;
      }
   }

   //--- Check for Triangles
   if(checkTriangle)
   {
      if(DetectAscendingTriangle())
      {
         m_activePattern = "ASCENDING TRIANGLE";
         return m_activePattern;
      }
      if(DetectDescendingTriangle())
      {
         m_activePattern = "DESCENDING TRIANGLE";
         return m_activePattern;
      }
      if(DetectSymmetricalTriangle())
      {
         m_activePattern = "SYMMETRICAL TRIANGLE";
         return m_activePattern;
      }
   }

   //--- Check for Wedges
   if(checkWedge)
   {
      if(DetectRisingWedge())
      {
         m_activePattern = "RISING WEDGE";
         return m_activePattern;
      }
      if(DetectFallingWedge())
      {
         m_activePattern = "FALLING WEDGE";
         return m_activePattern;
      }
   }

   //--- Check for Channels
   if(checkChannel)
   {
      if(DetectAscendingChannel())
      {
         m_activePattern = "ASCENDING CHANNEL";
         return m_activePattern;
      }
      if(DetectDescendingChannel())
      {
         m_activePattern = "DESCENDING CHANNEL";
         return m_activePattern;
      }
   }

   return m_activePattern;
}

//+------------------------------------------------------------------+
//| Detect Double Top pattern                                        |
//+------------------------------------------------------------------+
bool CPatterns::DetectDoubleTop()
{
   //--- Find swing highs
   double highs[];
   int indices[];

   if(!FindSwingHighs(highs, indices, 3))
      return false;

   //--- Check if we have at least 2 highs
   if(ArraySize(highs) < 2)
      return false;

   //--- Compare the two most recent highs
   double high1 = highs[0];
   double high2 = highs[1];

   //--- Highs should be approximately equal (within 0.5%)
   double tolerance = high1 * 0.005;

   if(MathAbs(high1 - high2) <= tolerance)
   {
      //--- Check if there's a valley between them
      int index1 = indices[0];
      int index2 = indices[1];

      double lowestBetween = GetLow(index1);
      for(int i = index1; i < index2; i++)
      {
         if(GetLow(i) < lowestBetween)
            lowestBetween = GetLow(i);
      }

      //--- Valley should be significantly lower (at least 1% below highs)
      if(lowestBetween < high1 * 0.99)
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Double Bottom pattern                                     |
//+------------------------------------------------------------------+
bool CPatterns::DetectDoubleBottom()
{
   //--- Find swing lows
   double lows[];
   int indices[];

   if(!FindSwingLows(lows, indices, 3))
      return false;

   //--- Check if we have at least 2 lows
   if(ArraySize(lows) < 2)
      return false;

   //--- Compare the two most recent lows
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Lows should be approximately equal (within 0.5%)
   double tolerance = low1 * 0.005;

   if(MathAbs(low1 - low2) <= tolerance)
   {
      //--- Check if there's a peak between them
      int index1 = indices[0];
      int index2 = indices[1];

      double highestBetween = GetHigh(index1);
      for(int i = index1; i < index2; i++)
      {
         if(GetHigh(i) > highestBetween)
            highestBetween = GetHigh(i);
      }

      //--- Peak should be significantly higher (at least 1% above lows)
      if(highestBetween > low1 * 1.01)
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Head & Shoulders pattern                                  |
//+------------------------------------------------------------------+
bool CPatterns::DetectHeadAndShoulders()
{
   //--- Find swing highs
   double highs[];
   int indices[];

   if(!FindSwingHighs(highs, indices, 4))
      return false;

   //--- Need at least 3 highs for H&S
   if(ArraySize(highs) < 3)
      return false;

   //--- Get the three most recent highs
   double leftShoulder = highs[2];
   double head = highs[1];
   double rightShoulder = highs[0];

   //--- Head should be higher than both shoulders
   if(head > leftShoulder && head > rightShoulder)
   {
      //--- Shoulders should be approximately equal (within 1%)
      double tolerance = leftShoulder * 0.01;

      if(MathAbs(leftShoulder - rightShoulder) <= tolerance)
      {
         //--- Head should be at least 2% higher than shoulders
         if(head >= leftShoulder * 1.02)
         {
            return true;
         }
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Inverse Head & Shoulders pattern                          |
//+------------------------------------------------------------------+
bool CPatterns::DetectInverseHeadAndShoulders()
{
   //--- Find swing lows
   double lows[];
   int indices[];

   if(!FindSwingLows(lows, indices, 4))
      return false;

   //--- Need at least 3 lows for inverse H&S
   if(ArraySize(lows) < 3)
      return false;

   //--- Get the three most recent lows
   double leftShoulder = lows[2];
   double head = lows[1];
   double rightShoulder = lows[0];

   //--- Head should be lower than both shoulders
   if(head < leftShoulder && head < rightShoulder)
   {
      //--- Shoulders should be approximately equal (within 1%)
      double tolerance = leftShoulder * 0.01;

      if(MathAbs(leftShoulder - rightShoulder) <= tolerance)
      {
         //--- Head should be at least 2% lower than shoulders
         if(head <= leftShoulder * 0.98)
         {
            return true;
         }
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Ascending Triangle                                        |
//+------------------------------------------------------------------+
bool CPatterns::DetectAscendingTriangle()
{
   //--- Find swing highs and lows
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   //--- Ascending triangle: Flat resistance (highs equal), rising support (lows rising)
   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Highs should be approximately equal (within 0.5%)
   double tolerance = high1 * 0.005;

   if(MathAbs(high1 - high2) <= tolerance)
   {
      //--- Lows should be rising
      if(low1 > low2 * 1.005)  // At least 0.5% higher
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Descending Triangle                                       |
//+------------------------------------------------------------------+
bool CPatterns::DetectDescendingTriangle()
{
   //--- Find swing highs and lows
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   //--- Descending triangle: Falling resistance (highs falling), flat support (lows equal)
   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Lows should be approximately equal (within 0.5%)
   double tolerance = low1 * 0.005;

   if(MathAbs(low1 - low2) <= tolerance)
   {
      //--- Highs should be falling
      if(high1 < high2 * 0.995)  // At least 0.5% lower
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Detect Symmetrical Triangle                                      |
//+------------------------------------------------------------------+
bool CPatterns::DetectSymmetricalTriangle()
{
   //--- Find swing highs and lows
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   //--- Symmetrical triangle: Falling resistance AND rising support
   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Highs should be falling
   bool fallingHighs = (high1 < high2 * 0.995);

   //--- Lows should be rising
   bool risingLows = (low1 > low2 * 1.005);

   return (fallingHighs && risingLows);
}

//+------------------------------------------------------------------+
//| Detect Rising Wedge                                              |
//+------------------------------------------------------------------+
bool CPatterns::DetectRisingWedge()
{
   //--- Rising wedge: Both highs and lows rising, but converging
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Both should be rising
   bool risingHighs = (high1 > high2);
   bool risingLows = (low1 > low2);

   //--- Lows rising faster than highs (converging)
   double highChange = (high1 - high2) / high2;
   double lowChange = (low1 - low2) / low2;

   return (risingHighs && risingLows && lowChange > highChange);
}

//+------------------------------------------------------------------+
//| Detect Falling Wedge                                             |
//+------------------------------------------------------------------+
bool CPatterns::DetectFallingWedge()
{
   //--- Falling wedge: Both highs and lows falling, but converging
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Both should be falling
   bool fallingHighs = (high1 < high2);
   bool fallingLows = (low1 < low2);

   //--- Highs falling faster than lows (converging)
   double highChange = (high2 - high1) / high2;
   double lowChange = (low2 - low1) / low2;

   return (fallingHighs && fallingLows && highChange > lowChange);
}

//+------------------------------------------------------------------+
//| Detect Ascending Channel                                         |
//+------------------------------------------------------------------+
bool CPatterns::DetectAscendingChannel()
{
   //--- Ascending channel: Parallel rising highs and lows
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Both should be rising
   bool risingHighs = (high1 > high2);
   bool risingLows = (low1 > low2);

   //--- Changes should be similar (parallel - within 20% difference)
   double highChange = (high1 - high2) / high2;
   double lowChange = (low1 - low2) / low2;

   double changeDiff = MathAbs(highChange - lowChange);

   return (risingHighs && risingLows && changeDiff < 0.002);  // Within 0.2%
}

//+------------------------------------------------------------------+
//| Detect Descending Channel                                        |
//+------------------------------------------------------------------+
bool CPatterns::DetectDescendingChannel()
{
   //--- Descending channel: Parallel falling highs and lows
   double highs[];
   int highIndices[];
   double lows[];
   int lowIndices[];

   if(!FindSwingHighs(highs, highIndices, 3)) return false;
   if(!FindSwingLows(lows, lowIndices, 3)) return false;

   if(ArraySize(highs) < 2 || ArraySize(lows) < 2) return false;

   double high1 = highs[0];
   double high2 = highs[1];
   double low1 = lows[0];
   double low2 = lows[1];

   //--- Both should be falling
   bool fallingHighs = (high1 < high2);
   bool fallingLows = (low1 < low2);

   //--- Changes should be similar (parallel - within 20% difference)
   double highChange = (high2 - high1) / high2;
   double lowChange = (low2 - low1) / low2;

   double changeDiff = MathAbs(highChange - lowChange);

   return (fallingHighs && fallingLows && changeDiff < 0.002);  // Within 0.2%
}

//+------------------------------------------------------------------+
//| Find swing highs                                                  |
//+------------------------------------------------------------------+
bool CPatterns::FindSwingHighs(double &highs[], int &indices[], int count)
{
   ArrayResize(highs, 0);
   ArrayResize(indices, 0);

   for(int i = 5; i < m_lookbackBars - 5; i++)
   {
      if(IsSwingHigh(i))
      {
         int size = ArraySize(highs);
         ArrayResize(highs, size + 1);
         ArrayResize(indices, size + 1);

         highs[size] = GetHigh(i);
         indices[size] = i;

         if(ArraySize(highs) >= count)
            break;
      }
   }

   return (ArraySize(highs) > 0);
}

//+------------------------------------------------------------------+
//| Find swing lows                                                   |
//+------------------------------------------------------------------+
bool CPatterns::FindSwingLows(double &lows[], int &indices[], int count)
{
   ArrayResize(lows, 0);
   ArrayResize(indices, 0);

   for(int i = 5; i < m_lookbackBars - 5; i++)
   {
      if(IsSwingLow(i))
      {
         int size = ArraySize(lows);
         ArrayResize(lows, size + 1);
         ArrayResize(indices, size + 1);

         lows[size] = GetLow(i);
         indices[size] = i;

         if(ArraySize(lows) >= count)
            break;
      }
   }

   return (ArraySize(lows) > 0);
}

//+------------------------------------------------------------------+
//| Check if bar is swing high                                       |
//+------------------------------------------------------------------+
bool CPatterns::IsSwingHigh(int index)
{
   double current = GetHigh(index);

   //--- Check 2 bars on each side
   for(int i = 1; i <= 2; i++)
   {
      if(GetHigh(index - i) >= current) return false;
      if(GetHigh(index + i) >= current) return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check if bar is swing low                                        |
//+------------------------------------------------------------------+
bool CPatterns::IsSwingLow(int index)
{
   double current = GetLow(index);

   //--- Check 2 bars on each side
   for(int i = 1; i <= 2; i++)
   {
      if(GetLow(index - i) <= current) return false;
      if(GetLow(index + i) <= current) return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Helper: Get High price                                           |
//+------------------------------------------------------------------+
double CPatterns::GetHigh(int shift)
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
double CPatterns::GetLow(int shift)
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
double CPatterns::GetClose(int shift)
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
double CPatterns::GetOpen(int shift)
{
   double open[];
   ArraySetAsSeries(open, true);
   if(CopyOpen(Symbol(), PERIOD_CURRENT, 0, shift + 2, open) < shift + 2)
      return 0;
   return open[shift];
}
