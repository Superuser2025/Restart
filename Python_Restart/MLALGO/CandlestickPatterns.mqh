//+------------------------------------------------------------------+
//|                                          CandlestickPatterns.mqh |
//|                                      Copyright 2025, Pankhuri    |
//|                   All Candlestick Pattern Detection Functions    |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Pankhuri"
#property link      "https://www.mql5.com"
#property strict

//+------------------------------------------------------------------+
//| Pattern structure (must match EA)                                |
//+------------------------------------------------------------------+
// NOTE: PatternInfo struct is defined in the main EA file
// This include file only contains the detection functions

//+------------------------------------------------------------------+
//| SINGLE CANDLE PATTERNS                                           |
//+------------------------------------------------------------------+

//--- HAMMER ---
bool DetectHammer(int shift, const double &o[], const double &h[],
                  const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Hammer: small body at top, long lower shadow
    if(lowerShadow > body * 2.0 && upperShadow < body * 0.3 && body > 0)
    {
        pattern.name = "HAMMER";
        pattern.signal = "BUY";
        pattern.strength = (lowerShadow > body * 3.0) ? 5 : 4;
        pattern.is_bullish = true;
        pattern.price = l[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- SHOOTING STAR ---
bool DetectShootingStar(int shift, const double &o[], const double &h[],
                       const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Shooting Star: small body at bottom, long upper shadow
    if(upperShadow > body * 2.0 && lowerShadow < body * 0.3 && body > 0)
    {
        pattern.name = "SHOOTING STAR";
        pattern.signal = "SELL";
        pattern.strength = (upperShadow > body * 3.0) ? 5 : 4;
        pattern.is_bullish = false;
        pattern.price = h[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- DOJI ---
bool DetectDoji(int shift, const double &o[], const double &h[],
                const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Doji: very small body, shows indecision
    if(body < range * 0.1)
    {
        pattern.name = "DOJI";
        pattern.signal = "SPARK";
        pattern.strength = 3;
        pattern.is_bullish = false; // neutral
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- DRAGONFLY DOJI ---
bool DetectDragonflyDoji(int shift, const double &o[], const double &h[],
                        const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Dragonfly Doji: no upper shadow, long lower shadow, tiny body
    if(body < range * 0.1 && upperShadow < range * 0.1 && lowerShadow > range * 0.6)
    {
        pattern.name = "DRAGONFLY DOJI";
        pattern.signal = "BUY";
        pattern.strength = 4;
        pattern.is_bullish = true;
        pattern.price = l[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- GRAVESTONE DOJI ---
bool DetectGravestoneDoji(int shift, const double &o[], const double &h[],
                         const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Gravestone Doji: no lower shadow, long upper shadow, tiny body
    if(body < range * 0.1 && lowerShadow < range * 0.1 && upperShadow > range * 0.6)
    {
        pattern.name = "GRAVESTONE DOJI";
        pattern.signal = "SELL";
        pattern.strength = 4;
        pattern.is_bullish = false;
        pattern.price = h[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- MARUBOZU ---
bool DetectMarubozu(int shift, const double &o[], const double &h[],
                   const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Marubozu: no shadows, full body
    if(upperShadow < range * 0.05 && lowerShadow < range * 0.05 && body > range * 0.85)
    {
        bool bullish = c[shift] > o[shift];

        pattern.name = bullish ? "BULLISH MARUBOZU" : "BEARISH MARUBOZU";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = bullish;
        pattern.price = bullish ? h[shift] : l[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- SPINNING TOP ---
bool DetectSpinningTop(int shift, const double &o[], const double &h[],
                      const double &l[], const double &c[], PatternInfo &pattern)
{
    double body = MathAbs(c[shift] - o[shift]);
    double upperShadow = h[shift] - MathMax(c[shift], o[shift]);
    double lowerShadow = MathMin(c[shift], o[shift]) - l[shift];
    double range = h[shift] - l[shift];

    if(range == 0) return false;

    // Spinning Top: small body, long shadows both sides
    if(body < range * 0.3 && upperShadow > body && lowerShadow > body)
    {
        pattern.name = "SPINNING TOP";
        pattern.signal = "SPARK";
        pattern.strength = 3;
        pattern.is_bullish = false; // neutral
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| TWO CANDLE PATTERNS                                              |
//+------------------------------------------------------------------+

//--- BULLISH/BEARISH ENGULFING ---
bool DetectEngulfing(int shift, const double &o[], const double &h[],
                    const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 1 >= ArraySize(c)) return false;

    bool bullishEngulfing = (o[shift+1] > c[shift+1]) && (c[shift] > o[shift]) &&
                           (c[shift] > o[shift+1]) && (o[shift] < c[shift+1]);

    bool bearishEngulfing = (c[shift+1] > o[shift+1]) && (o[shift] > c[shift]) &&
                           (o[shift] > c[shift+1]) && (c[shift] < o[shift+1]);

    if(bullishEngulfing)
    {
        pattern.name = "BULLISH ENGULFING";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    if(bearishEngulfing)
    {
        pattern.name = "BEARISH ENGULFING";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- HARAMI ---
bool DetectHarami(int shift, const double &o[], const double &h[],
                 const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 1 >= ArraySize(c)) return false;

    double body1 = MathAbs(c[shift+1] - o[shift+1]);
    double body2 = MathAbs(c[shift] - o[shift]);

    // Harami: small candle inside large candle
    bool bullishHarami = (o[shift+1] > c[shift+1]) && (c[shift] > o[shift]) &&
                        (o[shift] > c[shift+1]) && (c[shift] < o[shift+1]) &&
                        (body2 < body1 * 0.5);

    bool bearishHarami = (c[shift+1] > o[shift+1]) && (o[shift] > c[shift]) &&
                        (c[shift] > o[shift+1]) && (o[shift] < c[shift+1]) &&
                        (body2 < body1 * 0.5);

    if(bullishHarami)
    {
        pattern.name = "BULLISH HARAMI";
        pattern.signal = "BUY";
        pattern.strength = 4;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    if(bearishHarami)
    {
        pattern.name = "BEARISH HARAMI";
        pattern.signal = "SELL";
        pattern.strength = 4;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- PIERCING LINE ---
bool DetectPiercingLine(int shift, const double &o[], const double &h[],
                       const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 1 >= ArraySize(c)) return false;

    // Piercing: bearish candle followed by bullish that closes above 50% of first
    if(o[shift+1] > c[shift+1] && c[shift] > o[shift] &&
       o[shift] < c[shift+1] && c[shift] > (o[shift+1] + c[shift+1]) / 2 &&
       c[shift] < o[shift+1])
    {
        pattern.name = "PIERCING LINE";
        pattern.signal = "BUY";
        pattern.strength = 4;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- DARK CLOUD COVER ---
bool DetectDarkCloudCover(int shift, const double &o[], const double &h[],
                         const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 1 >= ArraySize(c)) return false;

    // Dark Cloud: bullish candle followed by bearish that closes below 50% of first
    if(c[shift+1] > o[shift+1] && o[shift] > c[shift] &&
       o[shift] > c[shift+1] && c[shift] < (o[shift+1] + c[shift+1]) / 2 &&
       c[shift] > o[shift+1])
    {
        pattern.name = "DARK CLOUD COVER";
        pattern.signal = "SELL";
        pattern.strength = 4;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- TWEEZER TOP/BOTTOM ---
bool DetectTweezer(int shift, const double &o[], const double &h[],
                  const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 1 >= ArraySize(c)) return false;

    // Simplified ATR - use range of previous candles
    double atr = 0;
    for(int i = shift; i < shift + 10 && i < ArraySize(c); i++)
        atr += h[i] - l[i];
    atr /= 10;

    double tolerance = atr * 0.1;

    // Tweezer Bottom: two candles with same low
    if(MathAbs(l[shift] - l[shift+1]) < tolerance && l[shift] < l[shift+1] + tolerance)
    {
        pattern.name = "TWEEZER BOTTOM";
        pattern.signal = "BUY";
        pattern.strength = 3;
        pattern.is_bullish = true;
        pattern.price = l[shift];
        pattern.bar_index = shift;
        return true;
    }

    // Tweezer Top: two candles with same high
    if(MathAbs(h[shift] - h[shift+1]) < tolerance && h[shift] > h[shift+1] - tolerance)
    {
        pattern.name = "TWEEZER TOP";
        pattern.signal = "SELL";
        pattern.strength = 3;
        pattern.is_bullish = false;
        pattern.price = h[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| THREE CANDLE PATTERNS                                            |
//+------------------------------------------------------------------+

//--- MORNING STAR ---
bool DetectMorningStar(int shift, const double &o[], const double &h[],
                      const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 2 >= ArraySize(c)) return false;

    double body1 = MathAbs(c[shift+2] - o[shift+2]);
    double body2 = MathAbs(c[shift+1] - o[shift+1]);
    double body3 = MathAbs(c[shift] - o[shift]);

    // Morning Star: bearish, small body, bullish
    if(o[shift+2] > c[shift+2] &&                     // First bearish
       body2 < body1 * 0.5 &&                         // Middle small
       c[shift] > o[shift] &&                         // Third bullish
       c[shift] > (o[shift+2] + c[shift+2]) / 2)      // Closes above midpoint of first
    {
        pattern.name = "MORNING STAR";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- EVENING STAR ---
bool DetectEveningStar(int shift, const double &o[], const double &h[],
                      const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 2 >= ArraySize(c)) return false;

    double body1 = MathAbs(c[shift+2] - o[shift+2]);
    double body2 = MathAbs(c[shift+1] - o[shift+1]);
    double body3 = MathAbs(c[shift] - o[shift]);

    // Evening Star: bullish, small body, bearish
    if(c[shift+2] > o[shift+2] &&                     // First bullish
       body2 < body1 * 0.5 &&                         // Middle small
       o[shift] > c[shift] &&                         // Third bearish
       c[shift] < (o[shift+2] + c[shift+2]) / 2)      // Closes below midpoint of first
    {
        pattern.name = "EVENING STAR";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- THREE WHITE SOLDIERS ---
bool DetectThreeWhiteSoldiers(int shift, const double &o[], const double &h[],
                             const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 2 >= ArraySize(c)) return false;

    // Three consecutive bullish candles with higher closes
    if(c[shift+2] > o[shift+2] && c[shift+1] > o[shift+1] && c[shift] > o[shift] &&
       c[shift+1] > c[shift+2] && c[shift] > c[shift+1] &&
       o[shift+1] > o[shift+2] && o[shift+1] < c[shift+2] &&
       o[shift] > o[shift+1] && o[shift] < c[shift+1])
    {
        pattern.name = "THREE WHITE SOLDIERS";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- THREE BLACK CROWS ---
bool DetectThreeBlackCrows(int shift, const double &o[], const double &h[],
                          const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 2 >= ArraySize(c)) return false;

    // Three consecutive bearish candles with lower closes
    if(o[shift+2] > c[shift+2] && o[shift+1] > c[shift+1] && o[shift] > c[shift] &&
       c[shift+1] < c[shift+2] && c[shift] < c[shift+1] &&
       o[shift+1] < o[shift+2] && o[shift+1] > c[shift+2] &&
       o[shift] < o[shift+1] && o[shift] > c[shift+1])
    {
        pattern.name = "THREE BLACK CROWS";
        pattern.signal = "ENTER";
        pattern.strength = 5;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//--- THREE INSIDE UP/DOWN ---
bool DetectThreeInside(int shift, const double &o[], const double &h[],
                      const double &l[], const double &c[], PatternInfo &pattern)
{
    if(shift + 2 >= ArraySize(c)) return false;

    // Three Inside Up: Bullish harami + confirmation
    bool threeInsideUp = (o[shift+2] > c[shift+2]) && (c[shift+1] > o[shift+1]) &&
                        (o[shift+1] > c[shift+2]) && (c[shift+1] < o[shift+2]) &&
                        (c[shift] > o[shift]) && (c[shift] > c[shift+1]);

    // Three Inside Down: Bearish harami + confirmation
    bool threeInsideDown = (c[shift+2] > o[shift+2]) && (o[shift+1] > c[shift+1]) &&
                          (c[shift+1] > o[shift+2]) && (o[shift+1] < c[shift+2]) &&
                          (o[shift] > c[shift]) && (c[shift] < c[shift+1]);

    if(threeInsideUp)
    {
        pattern.name = "THREE INSIDE UP";
        pattern.signal = "ENTER";
        pattern.strength = 4;
        pattern.is_bullish = true;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    if(threeInsideDown)
    {
        pattern.name = "THREE INSIDE DOWN";
        pattern.signal = "ENTER";
        pattern.strength = 4;
        pattern.is_bullish = false;
        pattern.price = c[shift];
        pattern.bar_index = shift;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+