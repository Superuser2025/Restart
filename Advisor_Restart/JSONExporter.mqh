//+------------------------------------------------------------------+
//|                                                 JSONExporter.mqh |
//|                      Exports market data and features to JSON    |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property link      ""
#property strict

//+------------------------------------------------------------------+
//| JSON Exporter Class - Simple and Reliable                        |
//+------------------------------------------------------------------+
class CJSONExporter
{
private:
    string m_filename;
    string m_content;
    int m_file_handle;
    bool m_in_object;
    bool m_in_array;
    int m_field_count;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CJSONExporter()
    {
        m_filename = "";
        m_content = "";
        m_file_handle = INVALID_HANDLE;
        m_in_object = false;
        m_in_array = false;
        m_field_count = 0;
    }

    //+------------------------------------------------------------------+
    //| Destructor                                                        |
    //+------------------------------------------------------------------+
    ~CJSONExporter()
    {
        if(m_file_handle != INVALID_HANDLE)
        {
            FileClose(m_file_handle);
        }
    }

    //+------------------------------------------------------------------+
    //| Initialize exporter with filename                                 |
    //+------------------------------------------------------------------+
    bool Init(string filename)
    {
        m_filename = filename;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Begin JSON export                                                 |
    //+------------------------------------------------------------------+
    void BeginExport()
    {
        m_content = "{\n";
        m_field_count = 0;
        m_in_object = true;
    }

    //+------------------------------------------------------------------+
    //| Add string field                                                  |
    //+------------------------------------------------------------------+
    void AddString(string key, string value)
    {
        if(m_field_count > 0) m_content += ",\n";

        // Escape quotes in value
        string escaped_value = value;
        StringReplace(escaped_value, "\"", "\\\"");

        m_content += "  \"" + key + "\": \"" + escaped_value + "\"";
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Add double field                                                  |
    //+------------------------------------------------------------------+
    void AddDouble(string key, double value, int digits = 5)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": " + DoubleToString(value, digits);
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Add integer field                                                 |
    //+------------------------------------------------------------------+
    void AddInt(string key, int value)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": " + IntegerToString(value);
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Add long field                                                    |
    //+------------------------------------------------------------------+
    void AddLong(string key, long value)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": " + IntegerToString(value);
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Add boolean field                                                 |
    //+------------------------------------------------------------------+
    void AddBool(string key, bool value)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": " + (value ? "true" : "false");
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Begin array                                                       |
    //+------------------------------------------------------------------+
    void BeginArray(string key)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": [\n";
        m_in_array = true;
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| Add array boolean                                                 |
    //+------------------------------------------------------------------+
    void AddArrayBool(bool value)
    {
        static int array_item_count = 0;

        if(array_item_count > 0) m_content += ", ";
        m_content += (value ? "true" : "false");
        array_item_count++;
    }

    //+------------------------------------------------------------------+
    //| Add array double                                                  |
    //+------------------------------------------------------------------+
    void AddArrayDouble(double value, int digits = 5)
    {
        static int array_item_count = 0;

        if(array_item_count > 0) m_content += ", ";
        m_content += DoubleToString(value, digits);
        array_item_count++;
    }

    //+------------------------------------------------------------------+
    //| End array                                                         |
    //+------------------------------------------------------------------+
    void EndArray()
    {
        m_content += "\n  ]";
        m_in_array = false;
    }

    //+------------------------------------------------------------------+
    //| Begin nested object                                               |
    //+------------------------------------------------------------------+
    void BeginObject(string key)
    {
        if(m_field_count > 0) m_content += ",\n";
        m_content += "  \"" + key + "\": {\n";
        m_field_count++;
    }

    //+------------------------------------------------------------------+
    //| End nested object                                                 |
    //+------------------------------------------------------------------+
    void EndObject()
    {
        m_content += "\n  }";
    }

    //+------------------------------------------------------------------+
    //| End export and write to file                                      |
    //+------------------------------------------------------------------+
    bool EndExport()
    {
        m_content += "\n}\n";

        // Write to file using FILE_COMMON to save to Common/Files folder
        // This allows Python app to read from %APPDATA%\MetaQuotes\Terminal\Common\Files\
        m_file_handle = FileOpen(m_filename, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);

        if(m_file_handle == INVALID_HANDLE)
        {
            Print("ERROR: Failed to create file: ", m_filename);
            Print("Error code: ", GetLastError());
            return false;
        }

        FileWriteString(m_file_handle, m_content);
        FileClose(m_file_handle);
        m_file_handle = INVALID_HANDLE;

        // Reset state
        m_content = "";
        m_field_count = 0;
        m_in_object = false;

        return true;
    }
};
