//+------------------------------------------------------------------+
//| ExportTradeHistory.mqh                                            |
//| Export trade history to JSON for Python GUI                      |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Export Today's Trade History to JSON                             |
//+------------------------------------------------------------------+
void ExportTradeHistoryToJSON()
{
    // Get AppleTrader data directory
    string terminal_data_path = TerminalInfoString(TERMINAL_DATA_PATH);
    string folder_path = terminal_data_path + "\\MQL5\\Files\\AppleTrader\\";

    // Create directory if it doesn't exist
    if(!FolderCreate(folder_path, FILE_COMMON))
    {
        int error = GetLastError();
        if(error != 5018 && error != 0)  // 5018 = folder already exists
        {
            Print("ERROR: Failed to create AppleTrader folder: ", error);
            return;
        }
    }

    string file_path = folder_path + "market_data.json";

    // Get today's start time
    datetime today_start = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));
    datetime now = TimeCurrent();

    // Select history for today
    if(!HistorySelect(today_start, now))
    {
        Print("ERROR: Failed to select history");
        return;
    }

    // Build trade history JSON array
    string trade_history_json = "[\n";
    int total_deals = HistoryDealsTotal();
    int exported_count = 0;

    for(int i = 0; i < total_deals; i++)
    {
        ulong deal_ticket = HistoryDealGetTicket(i);
        if(deal_ticket == 0) continue;

        // Only include EXIT deals (completed trades)
        ENUM_DEAL_ENTRY entry_type = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
        if(entry_type != DEAL_ENTRY_OUT) continue;

        // Only include our EA's trades
        long magic = HistoryDealGetInteger(deal_ticket, DEAL_MAGIC);
        if(magic != MagicNumber && magic != 0) continue;  // Include manual trades (magic=0)

        // Get deal details
        string symbol = HistoryDealGetString(deal_ticket, DEAL_SYMBOL);
        datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
        double volume = HistoryDealGetDouble(deal_ticket, DEAL_VOLUME);
        double price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
        double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);
        double commission = HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION);
        double swap = HistoryDealGetDouble(deal_ticket, DEAL_SWAP);

        // Determine deal type
        ENUM_DEAL_TYPE deal_type = (ENUM_DEAL_TYPE)HistoryDealGetInteger(deal_ticket, DEAL_TYPE);
        string type_str = (deal_type == DEAL_TYPE_BUY) ? "BUY" : "SELL";

        // Add comma if not first entry
        if(exported_count > 0)
            trade_history_json += ",\n";

        // Build JSON object for this trade
        trade_history_json += "    {\n";
        trade_history_json += "        \"ticket\": " + IntegerToString(deal_ticket) + ",\n";
        trade_history_json += "        \"symbol\": \"" + symbol + "\",\n";
        trade_history_json += "        \"type\": \"" + type_str + "\",\n";
        trade_history_json += "        \"time\": " + IntegerToString(deal_time) + ",\n";
        trade_history_json += "        \"volume\": " + DoubleToString(volume, 2) + ",\n";
        trade_history_json += "        \"price\": " + DoubleToString(price, 5) + ",\n";
        trade_history_json += "        \"profit\": " + DoubleToString(profit, 2) + ",\n";
        trade_history_json += "        \"commission\": " + DoubleToString(commission, 2) + ",\n";
        trade_history_json += "        \"swap\": " + DoubleToString(swap, 2) + "\n";
        trade_history_json += "    }";

        exported_count++;
    }

    trade_history_json += "\n]";

    // Open file for writing
    int file_handle = FileOpen(file_path, FILE_WRITE|FILE_TXT|FILE_ANSI, '\n', CP_UTF8);

    if(file_handle == INVALID_HANDLE)
    {
        Print("ERROR: Failed to open file for writing: ", GetLastError());
        return;
    }

    // Build complete JSON with trade history
    string json_content = "{\n";
    json_content += "    \"timestamp\": " + IntegerToString(TimeCurrent()) + ",\n";
    json_content += "    \"symbol\": \"" + _Symbol + "\",\n";
    json_content += "    \"trade_history\": " + trade_history_json + "\n";
    json_content += "}\n";

    // Write to file
    FileWriteString(file_handle, json_content);
    FileClose(file_handle);

    if(exported_count > 0)
        Print("✓ Exported ", exported_count, " trades to ", file_path);
}
