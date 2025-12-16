//+------------------------------------------------------------------+
//| ML_FeatureExtractor.mqh - MQL5 COMPATIBLE VERSION                |
//| MODULE: Feature Extraction - Converts market data to ML features |
//| DEPENDENCIES: None (standalone module)                            |
//+------------------------------------------------------------------+

#property strict

//+------------------------------------------------------------------+
//| CONFIGURATION                                                     |
//+------------------------------------------------------------------+
#define TOTAL_FEATURES 40  // Reduced for simplicity - still effective

//+------------------------------------------------------------------+
//| FEATURE VECTOR STRUCTURE                                          |
//+------------------------------------------------------------------+
struct MLFeatureVector
{
    double features[TOTAL_FEATURES];
    datetime timestamp;
    int bar_index;
    bool is_valid;
};

//+------------------------------------------------------------------+
//| FEATURE STATISTICS (for normalization)                            |
//+------------------------------------------------------------------+
struct FeatureStatistics
{
    double mean;
    double std;
    double min;
    double max;
    int sample_count;
};

FeatureStatistics g_FeatureStats[TOTAL_FEATURES];

//+------------------------------------------------------------------+
//| FEATURE EXTRACTOR CLASS - MQL5 COMPATIBLE                         |
//+------------------------------------------------------------------+
class CFeatureExtractor
{
private:
    string m_symbol;
    ENUM_TIMEFRAMES m_timeframe;
    bool m_normalize_enabled;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CFeatureExtractor(string symbol = NULL, ENUM_TIMEFRAMES tf = PERIOD_CURRENT)
    {
        m_symbol = (symbol == NULL) ? _Symbol : symbol;
        m_timeframe = (tf == PERIOD_CURRENT) ? _Period : tf;
        m_normalize_enabled = true;
    }

    //+------------------------------------------------------------------+
    //| Main extraction method - SIMPLIFIED VERSION                       |
    //+------------------------------------------------------------------+
    bool Extract(MLFeatureVector &fv, int bar_index = 0)
    {
        fv.bar_index = bar_index;
        fv.timestamp = iTime(m_symbol, m_timeframe, bar_index);
        fv.is_valid = false;

        int idx = 0;

        // Get basic price data
        double close = iClose(m_symbol, m_timeframe, bar_index);
        double open = iOpen(m_symbol, m_timeframe, bar_index);
        double high = iHigh(m_symbol, m_timeframe, bar_index);
        double low = iLow(m_symbol, m_timeframe, bar_index);
        long volume = iVolume(m_symbol, m_timeframe, bar_index);

        if(close == 0 || open == 0)
            return false;

        // FEATURE GROUP 1: Price-based (15 features)

        // 1. Candle body size (normalized)
        double body_size = MathAbs(close - open) / close;
        fv.features[idx++] = body_size;

        // 2. Upper wick size
        double upper_wick = (high - MathMax(open, close)) / close;
        fv.features[idx++] = upper_wick;

        // 3. Lower wick size
        double lower_wick = (MathMin(open, close) - low) / close;
        fv.features[idx++] = lower_wick;

        // 4. Candle direction
        fv.features[idx++] = (close > open) ? 1.0 : -1.0;

        // 5. Range (high-low)
        double range = (high - low) / close;
        fv.features[idx++] = range;

        // 6-10. Price momentum (5 periods)
        for(int period = 5; period <= 25; period += 5)
        {
            double past_close = iClose(m_symbol, m_timeframe, bar_index + period);
            if(past_close > 0)
                fv.features[idx++] = (close - past_close) / past_close;
            else
                fv.features[idx++] = 0;
        }

        // 11-15. Moving average distances (simple calculation)
        int ma_periods[] = {10, 20, 50, 100, 200};
        for(int i = 0; i < 5; i++)
        {
            double ma_sum = 0;
            int period = ma_periods[i];

            for(int j = 0; j < period; j++)
            {
                double price = iClose(m_symbol, m_timeframe, bar_index + j);
                if(price > 0)
                    ma_sum += price;
            }

            double ma = ma_sum / period;
            if(ma > 0)
                fv.features[idx++] = (close - ma) / close;
            else
                fv.features[idx++] = 0;
        }

        // FEATURE GROUP 2: Volume-based (5 features)

        // 16. Volume ratio to recent average
        long vol_sum = 0;
        for(int i = 1; i <= 20; i++)
        {
            vol_sum += iVolume(m_symbol, m_timeframe, bar_index + i);
        }
        double avg_volume = vol_sum / 20.0;
        fv.features[idx++] = (avg_volume > 0) ? (double)volume / avg_volume : 1.0;

        // 17-20. Volume momentum
        for(int period = 5; period <= 20; period += 5)
        {
            long past_vol = iVolume(m_symbol, m_timeframe, bar_index + period);
            fv.features[idx++] = (past_vol > 0) ? (double)volume / past_vol : 1.0;
        }

        // FEATURE GROUP 3: Volatility (5 features)

        // 21-25. Range ratios over different periods
        for(int period = 5; period <= 25; period += 5)
        {
            double past_high = iHigh(m_symbol, m_timeframe, bar_index + period);
            double past_low = iLow(m_symbol, m_timeframe, bar_index + period);
            double past_range = past_high - past_low;

            if(past_range > 0 && close > 0)
                fv.features[idx++] = (high - low) / past_range;
            else
                fv.features[idx++] = 1.0;
        }

        // FEATURE GROUP 4: Multi-Timeframe (5 features)

        // 26-30. Higher timeframe trends
        ENUM_TIMEFRAMES higher_tfs[] = {PERIOD_M15, PERIOD_H1, PERIOD_H4, PERIOD_D1, PERIOD_W1};

        for(int i = 0; i < 5; i++)
        {
            if(higher_tfs[i] <= m_timeframe)
                continue;

            double htf_close = iClose(m_symbol, higher_tfs[i], 0);
            double htf_open = iOpen(m_symbol, higher_tfs[i], 1);

            if(htf_open > 0 && htf_close > 0)
                fv.features[idx++] = (htf_close > htf_open) ? 1.0 : -1.0;
            else
                fv.features[idx++] = 0;
        }

        // FEATURE GROUP 5: Time-based (10 features)

        MqlDateTime dt;
        TimeToStruct(fv.timestamp, dt);

        // 31. Hour of day (cyclical - sine)
        fv.features[idx++] = MathSin(2 * M_PI * dt.hour / 24.0);

        // 32. Hour of day (cyclical - cosine)
        fv.features[idx++] = MathCos(2 * M_PI * dt.hour / 24.0);

        // 33. Day of week (cyclical - sine)
        fv.features[idx++] = MathSin(2 * M_PI * dt.day_of_week / 7.0);

        // 34. Day of week (cyclical - cosine)
        fv.features[idx++] = MathCos(2 * M_PI * dt.day_of_week / 7.0);

        // 35-40. Session indicators (one-hot encoding)
        fv.features[idx++] = (dt.hour >= 0 && dt.hour < 8) ? 1.0 : 0.0;   // Asian
        fv.features[idx++] = (dt.hour >= 8 && dt.hour < 13) ? 1.0 : 0.0;  // London
        fv.features[idx++] = (dt.hour >= 13 && dt.hour < 16) ? 1.0 : 0.0; // Overlap
        fv.features[idx++] = (dt.hour >= 16 && dt.hour < 21) ? 1.0 : 0.0; // NY
        fv.features[idx++] = (dt.hour >= 21 || dt.hour < 0) ? 1.0 : 0.0;  // Closed
        fv.features[idx++] = dt.day_of_week == 1 ? 1.0 : 0.0;              // Monday

        // Normalize if enabled
        if(m_normalize_enabled)
            Normalize(fv);

        fv.is_valid = true;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Enable/disable normalization                                      |
    //+------------------------------------------------------------------+
    void SetNormalization(bool enabled) { m_normalize_enabled = enabled; }

    //+------------------------------------------------------------------+
    //| Update statistics for normalization                               |
    //+------------------------------------------------------------------+
    void UpdateStatistics(MLFeatureVector &fv)
    {
        for(int i = 0; i < TOTAL_FEATURES; i++)
        {
            double val = fv.features[i];

            // Online update of mean
            int n = g_FeatureStats[i].sample_count;
            double old_mean = g_FeatureStats[i].mean;
            g_FeatureStats[i].mean = (old_mean * n + val) / (n + 1);

            // Online update of variance (Welford's algorithm)
            if(n > 0)
            {
                double old_std = g_FeatureStats[i].std;
                g_FeatureStats[i].std = MathSqrt((old_std * old_std * n + (val - old_mean) * (val - g_FeatureStats[i].mean)) / (n + 1));
            }

            // Min/Max
            if(val < g_FeatureStats[i].min || n == 0)
                g_FeatureStats[i].min = val;
            if(val > g_FeatureStats[i].max || n == 0)
                g_FeatureStats[i].max = val;

            g_FeatureStats[i].sample_count++;
        }
    }

private:
    //+------------------------------------------------------------------+
    //| NORMALIZE FEATURES                                                |
    //+------------------------------------------------------------------+
    void Normalize(MLFeatureVector &fv)
    {
        for(int i = 0; i < TOTAL_FEATURES; i++)
        {
            double mean = g_FeatureStats[i].mean;
            double std = g_FeatureStats[i].std;

            if(std > 0.0001)
                fv.features[i] = (fv.features[i] - mean) / std;
            else
                fv.features[i] = 0;
        }
    }
};
