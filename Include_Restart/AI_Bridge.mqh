//+------------------------------------------------------------------+
//|                                              AI_Bridge.mqh       |
//|                    AI Bridge using Windows Named Pipes           |
//|                    CLEAN VERSION - NO INPUT CONFLICTS            |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, AI Trading System"
#property link      "https://www.mql5.com"
#property version   "2.00"
#property strict

//+------------------------------------------------------------------+
//| AI Bridge Class - Named Pipe Version                             |
//+------------------------------------------------------------------+
class CAIBridgePipe
{
private:
    int         m_pipe;
    string      m_pipe_name;
    int         m_timeout;
    bool        m_connected;
    datetime    m_last_update;
    int         m_request_count;
    int         m_error_count;
    
    bool        OpenPipe();
    void        ClosePipe();
    bool        SendMessage(string message, string &response);
    string      ReadResponse();
    
public:
    CAIBridgePipe(string pipe_name, int timeout);
    ~CAIBridgePipe();
    
    bool        Connect();
    bool        IsConnected() { return m_connected; }
    void        Disconnect();
    
    bool        SendMarketData(string symbol, ENUM_TIMEFRAMES timeframe);
    bool        GetAISignal(string symbol, string &direction, double &confidence, 
                           double &entry, double &sl, double &tp1, double &tp2, double &tp3);
    bool        GetRiskScore(string symbol, double &risk_score, string &risk_factors);
    
    int         GetRequestCount() { return m_request_count; }
    int         GetErrorCount() { return m_error_count; }
};

CAIBridgePipe::CAIBridgePipe(string pipe_name, int timeout)
{
    m_pipe_name = pipe_name;
    m_timeout = timeout;
    m_pipe = INVALID_HANDLE;
    m_connected = false;
    m_last_update = 0;
    m_request_count = 0;
    m_error_count = 0;
}

CAIBridgePipe::~CAIBridgePipe()
{
    Disconnect();
}

bool CAIBridgePipe::Connect()
{
    if(OpenPipe())
    {
        string response;
        if(SendMessage("{\"type\":\"ping\"}", response))
        {
            m_connected = true;
            Print("✓ AI Bridge Connected");
            return true;
        }
    }
    m_connected = false;
    return false;
}

void CAIBridgePipe::Disconnect()
{
    ClosePipe();
    m_connected = false;
}

bool CAIBridgePipe::OpenPipe()
{
    m_pipe = FileOpen(m_pipe_name, FILE_READ|FILE_WRITE|FILE_BIN|FILE_SHARE_READ|FILE_SHARE_WRITE);
    return (m_pipe != INVALID_HANDLE);
}

void CAIBridgePipe::ClosePipe()
{
    if(m_pipe != INVALID_HANDLE)
    {
        FileClose(m_pipe);
        m_pipe = INVALID_HANDLE;
    }
}

bool CAIBridgePipe::SendMessage(string message, string &response)
{
    if(m_pipe == INVALID_HANDLE)
        if(!OpenPipe()) return false;
    
    int msg_len = StringLen(message);
    if(FileWriteInteger(m_pipe, msg_len, INT_VALUE) <= 0) { ClosePipe(); return false; }
    if(FileWriteString(m_pipe, message) <= 0) { ClosePipe(); return false; }
    FileFlush(m_pipe);
    
    response = ReadResponse();
    m_request_count++;
    return (StringLen(response) > 0);
}

string CAIBridgePipe::ReadResponse()
{
    int resp_len = FileReadInteger(m_pipe, INT_VALUE);
    if(resp_len <= 0 || resp_len > 1048576) return "";
    return FileReadString(m_pipe, resp_len);
}

string BuildJSON(string symbol, ENUM_TIMEFRAMES timeframe)
{
    string json = "{\"type\":\"market_data\",\"timestamp\":" + IntegerToString(TimeCurrent()) + 
                  ",\"symbol\":\"" + symbol + "\",\"timeframe\":\"" + EnumToString(timeframe) + 
                  "\",\"bid\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_BID), 5) + 
                  ",\"ask\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_ASK), 5) + 
                  ",\"spread\":" + IntegerToString(SymbolInfoInteger(symbol, SYMBOL_SPREAD)) + ",\"ohlcv\":[";
    
    double o[], h[], l[], c[]; long vol[];
    ArraySetAsSeries(o, true); ArraySetAsSeries(h, true); 
    ArraySetAsSeries(l, true); ArraySetAsSeries(c, true); ArraySetAsSeries(vol, true);
    
    int bars = 50;
    if(CopyOpen(symbol, timeframe, 0, bars, o) > 0 && CopyHigh(symbol, timeframe, 0, bars, h) > 0 &&
       CopyLow(symbol, timeframe, 0, bars, l) > 0 && CopyClose(symbol, timeframe, 0, bars, c) > 0 &&
       CopyTickVolume(symbol, timeframe, 0, bars, vol) > 0)
    {
        for(int i = 0; i < bars; i++)
        {
            if(i > 0) json += ",";
            json += "{\"o\":" + DoubleToString(o[i], 5) + ",\"h\":" + DoubleToString(h[i], 5) + 
                    ",\"l\":" + DoubleToString(l[i], 5) + ",\"c\":" + DoubleToString(c[i], 5) + 
                    ",\"v\":" + IntegerToString(vol[i]) + "}";
        }
    }
    json += "]}";
    return json;
}

bool CAIBridgePipe::SendMarketData(string symbol, ENUM_TIMEFRAMES timeframe)
{
    if(!m_connected) return false;
    string response;
    return SendMessage(BuildJSON(symbol, timeframe), response);
}

bool CAIBridgePipe::GetAISignal(string symbol, string &direction, double &confidence, 
                                double &entry, double &sl, double &tp1, double &tp2, double &tp3)
{
    if(!m_connected) return false;
    string request = "{\"type\":\"get_signal\",\"symbol\":\"" + symbol + "\"}";
    string response;
    
    if(SendMessage(request, response))
    {
        int pos = StringFind(response, "\"direction\":\"");
        if(pos >= 0)
        {
            pos += 13;
            int end = StringFind(response, "\"", pos);
            if(end > pos) direction = StringSubstr(response, pos, end - pos);
        }
        
        pos = StringFind(response, "\"confidence\":");
        if(pos >= 0)
        {
            pos += 13;
            string num = "";
            for(int i = pos; i < StringLen(response) && i < pos + 20; i++)
            {
                ushort ch = StringGetCharacter(response, i);
                if((ch >= '0' && ch <= '9') || ch == '.') num += ShortToString(ch);
                else if(StringLen(num) > 0) break;
            }
            if(StringLen(num) > 0) confidence = StringToDouble(num);
        }
        
        entry = SymbolInfoDouble(symbol, SYMBOL_BID);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        sl = entry - 200 * point;
        tp1 = entry + 200 * point;
        tp2 = entry + 300 * point;
        tp3 = entry + 500 * point;
        return true;
    }
    return false;
}

bool CAIBridgePipe::GetRiskScore(string symbol, double &risk_score, string &risk_factors)
{
    if(!m_connected) return false;
    string request = "{\"type\":\"risk_score\",\"symbol\":\"" + symbol + "\"}";
    string response;
    
    if(SendMessage(request, response))
    {
        int pos = StringFind(response, "\"risk_score\":");
        if(pos >= 0)
        {
            pos += 13;
            string num = "";
            for(int i = pos; i < StringLen(response) && i < pos + 20; i++)
            {
                ushort ch = StringGetCharacter(response, i);
                if((ch >= '0' && ch <= '9') || ch == '.') num += ShortToString(ch);
                else if(StringLen(num) > 0) break;
            }
            if(StringLen(num) > 0) risk_score = StringToDouble(num);
        }
        
        pos = StringFind(response, "\"factors\":\"");
        if(pos >= 0)
        {
            pos += 11;
            int end = StringFind(response, "\"", pos);
            if(end > pos) risk_factors = StringSubstr(response, pos, end - pos);
        }
        return true;
    }
    return false;
}

CAIBridgePipe *g_ai_bridge = NULL;

bool AI_Init(string pipe_name = "\\\\.\\pipe\\mt5_ai_bridge", int timeout = 5000)
{
    if(g_ai_bridge != NULL) delete g_ai_bridge;
    g_ai_bridge = new CAIBridgePipe(pipe_name, timeout);
    Sleep(1000);
    
    if(g_ai_bridge.Connect())
    {
        Print("✓ AI Bridge initialized - Pipe: ", pipe_name);
        return true;
    }
    Print("✗ AI init failed - Start: python ai_server_namedpipe.py");
    return false;
}

void AI_Deinit()
{
    if(g_ai_bridge != NULL)
    {
        g_ai_bridge.Disconnect();
        delete g_ai_bridge;
        g_ai_bridge = NULL;
    }
}

bool AI_IsConnected() { return (g_ai_bridge != NULL && g_ai_bridge.IsConnected()); }
bool AI_SendData(string symbol, ENUM_TIMEFRAMES timeframe) { if(g_ai_bridge == NULL) return false; return g_ai_bridge.SendMarketData(symbol, timeframe); }
bool AI_GetSignal(string symbol, string &direction, double &confidence, double &entry, double &sl, double &tp1, double &tp2, double &tp3) { if(g_ai_bridge == NULL) return false; return g_ai_bridge.GetAISignal(symbol, direction, confidence, entry, sl, tp1, tp2, tp3); }
bool AI_GetRisk(string symbol, double &risk_score, string &risk_factors) { if(g_ai_bridge == NULL) return false; return g_ai_bridge.GetRiskScore(symbol, risk_score, risk_factors); }
//+------------------------------------------------------------------+
