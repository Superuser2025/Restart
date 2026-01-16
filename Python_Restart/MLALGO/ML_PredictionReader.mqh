//+------------------------------------------------------------------+
//|                                            ML_PredictionReader.mqh |
//|                      Reads ML predictions from multi-symbol JSON  |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property strict

//+------------------------------------------------------------------+
//| ML Prediction Reader - Handles Multi-Symbol Predictions          |
//+------------------------------------------------------------------+
class CMLPredictionReader
{
private:
    string m_filename;
    string m_last_content;
    datetime m_last_read_time;

public:
    string ml_signal;           // ENTER, WAIT, SKIP
    double ml_probability;      // 0.0 - 1.0
    double ml_confidence;       // 0.0 - 1.0
    string ml_reasoning;        // Why this decision
    bool   is_valid;            // Is prediction valid

    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CMLPredictionReader()
    {
        m_filename = "ML_Data\\prediction.json";
        m_last_content = "";
        m_last_read_time = 0;

        ml_signal = "WAIT";
        ml_probability = 0.50;
        ml_confidence = 0.50;
        ml_reasoning = "No prediction available";
        is_valid = false;
    }

    //+------------------------------------------------------------------+
    //| Read ML prediction for current symbol                            |
    //+------------------------------------------------------------------+
    bool ReadPrediction(string symbol)
    {
        int file_handle = FileOpen(m_filename, FILE_READ|FILE_TXT|FILE_ANSI);

        if(file_handle == INVALID_HANDLE)
        {
            is_valid = false;
            ml_signal = "WAIT";
            ml_reasoning = "Prediction file not found";
            return false;
        }

        // Read entire file
        string content = "";
        while(!FileIsEnding(file_handle))
        {
            content += FileReadString(file_handle);
        }
        FileClose(file_handle);

        // Check if content changed
        if(content == m_last_content && (TimeCurrent() - m_last_read_time) < 5)
        {
            return is_valid;  // Return cached result
        }

        m_last_content = content;
        m_last_read_time = TimeCurrent();

        // Parse JSON (simple string extraction - works for our format)
        return ParsePrediction(content, symbol);
    }

    //+------------------------------------------------------------------+
    //| Parse JSON prediction for symbol                                  |
    //+------------------------------------------------------------------+
    bool ParsePrediction(string json_content, string symbol)
    {
        // Look for symbol section
        string symbol_marker = "\"" + symbol + "\": {";
        int symbol_pos = StringFind(json_content, symbol_marker);

        if(symbol_pos < 0)
        {
            // Try old single-symbol format
            return ParseSingleSymbolFormat(json_content);
        }

        // Extract symbol's prediction section
        int section_start = symbol_pos + StringLen(symbol_marker);
        int section_end = StringFind(json_content, "}", section_start);

        if(section_end < 0)
        {
            is_valid = false;
            return false;
        }

        string prediction_section = StringSubstr(json_content, section_start, section_end - section_start);

        // Extract signal
        ml_signal = ExtractStringValue(prediction_section, "signal");

        // Extract probability
        ml_probability = ExtractDoubleValue(prediction_section, "probability");

        // Extract confidence
        ml_confidence = ExtractDoubleValue(prediction_section, "confidence");

        // Extract reasoning
        ml_reasoning = ExtractStringValue(prediction_section, "reasoning");

        is_valid = true;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Parse old single-symbol format (backward compatibility)          |
    //+------------------------------------------------------------------+
    bool ParseSingleSymbolFormat(string json_content)
    {
        ml_signal = ExtractStringValue(json_content, "signal");
        ml_probability = ExtractDoubleValue(json_content, "probability");
        ml_confidence = ExtractDoubleValue(json_content, "confidence");
        ml_reasoning = ExtractStringValue(json_content, "reasoning");

        is_valid = (ml_signal != "");
        return is_valid;
    }

    //+------------------------------------------------------------------+
    //| Extract string value from JSON                                    |
    //+------------------------------------------------------------------+
    string ExtractStringValue(string json, string key)
    {
        string search = "\"" + key + "\": \"";
        int start_pos = StringFind(json, search);

        if(start_pos < 0) return "";

        start_pos += StringLen(search);
        int end_pos = StringFind(json, "\"", start_pos);

        if(end_pos < 0) return "";

        return StringSubstr(json, start_pos, end_pos - start_pos);
    }

    //+------------------------------------------------------------------+
    //| Extract double value from JSON                                    |
    //+------------------------------------------------------------------+
    double ExtractDoubleValue(string json, string key)
    {
        string search = "\"" + key + "\": ";
        int start_pos = StringFind(json, search);

        if(start_pos < 0) return 0.0;

        start_pos += StringLen(search);

        // Find end (comma or closing brace)
        int end_pos = StringFind(json, ",", start_pos);
        if(end_pos < 0) end_pos = StringFind(json, "}", start_pos);
        if(end_pos < 0) end_pos = StringFind(json, "\n", start_pos);

        if(end_pos < 0) return 0.0;

        string value_str = StringSubstr(json, start_pos, end_pos - start_pos);
        StringTrimLeft(value_str);
        StringTrimRight(value_str);

        return StringToDouble(value_str);
    }

    //+------------------------------------------------------------------+
    //| Get ML decision for EA                                            |
    //+------------------------------------------------------------------+
    bool ShouldEnterTrade()
    {
        return (is_valid && ml_signal == "ENTER");
    }

    //+------------------------------------------------------------------+
    //| Get prediction summary                                            |
    //+------------------------------------------------------------------+
    string GetSummary()
    {
        if(!is_valid)
            return "ML: No prediction";

        return StringFormat("ML: %s (P:%.0f%% C:%.0f%%) - %s",
                          ml_signal,
                          ml_probability * 100,
                          ml_confidence * 100,
                          ml_reasoning);
    }
};
