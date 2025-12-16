//+------------------------------------------------------------------+
//|                                                 JSONExporter.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| JSON Export System for Python GUI Communication                  |
//| Exports market data, filter states, and trading info to JSON    |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CJSONExporter Class                                              |
//| Handles exporting MT5 data to JSON files for Python GUI          |
//+------------------------------------------------------------------+
class CJSONExporter
{
private:
   string            m_filePath;                  // Export file path
   string            m_jsonContent;               // Current JSON being built
   int               m_fileHandle;                // File handle
   bool              m_isArrayOpen;               // Track if array is open
   bool              m_isObjectOpen;              // Track if object is open
   int               m_arrayDepth;                // Nesting depth
   bool              m_firstElement;              // Track first element for comma placement

public:
                     CJSONExporter();
                    ~CJSONExporter();

   //--- Initialization
   bool              Init(string filePath);

   //--- Export control
   void              BeginExport();
   bool              EndExport();

   //--- Data addition methods
   void              AddString(string key, string value);
   void              AddInt(string key, int value);
   void              AddLong(string key, long value);
   void              AddDouble(string key, double value, int digits);
   void              AddBool(string key, bool value);

   //--- Array methods
   void              BeginArray(string key);
   void              EndArray();
   void              AddArrayString(string value);
   void              AddArrayInt(int value);
   void              AddArrayDouble(double value, int digits);
   void              AddArrayBool(bool value);

   //--- Object methods
   void              BeginObject(string key);
   void              EndObject();

   //--- Utility
   string            EscapeString(string str);
   string            GetLastError();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CJSONExporter::CJSONExporter()
{
   m_filePath = "";
   m_jsonContent = "";
   m_fileHandle = INVALID_HANDLE;
   m_isArrayOpen = false;
   m_isObjectOpen = false;
   m_arrayDepth = 0;
   m_firstElement = true;
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CJSONExporter::~CJSONExporter()
{
   if(m_fileHandle != INVALID_HANDLE)
   {
      FileClose(m_fileHandle);
   }
}

//+------------------------------------------------------------------+
//| Initialize exporter                                              |
//+------------------------------------------------------------------+
bool CJSONExporter::Init(string filePath)
{
   m_filePath = filePath;

   //--- Ensure directory exists
   string directory = "";
   int lastSlash = StringFind(filePath, "/", 0);
   if(lastSlash > 0)
   {
      directory = StringSubstr(filePath, 0, lastSlash);

      //--- Create directory if it doesn't exist
      if(!FolderCreate(directory, FILE_COMMON))
      {
         int errorCode = ::GetLastError();
         if(errorCode != 5019)  // 5019 = folder already exists (not an error)
         {
            Print("Failed to create directory: ", directory, " Error: ", errorCode);
            return false;
         }
      }
   }

   Print("JSONExporter initialized: ", filePath);
   return true;
}

//+------------------------------------------------------------------+
//| Begin JSON export                                                |
//+------------------------------------------------------------------+
void CJSONExporter::BeginExport()
{
   m_jsonContent = "{\n";
   m_firstElement = true;
   m_arrayDepth = 0;
   m_isArrayOpen = false;
   m_isObjectOpen = false;
}

//+------------------------------------------------------------------+
//| End JSON export and write to file                                |
//+------------------------------------------------------------------+
bool CJSONExporter::EndExport()
{
   //--- Close JSON
   m_jsonContent += "\n}";

   Print("[JSON] Attempting to write to: ", m_filePath);
   Print("[JSON] Content size: ", StringLen(m_jsonContent), " characters");

   //--- Write to file
   m_fileHandle = FileOpen(m_filePath, FILE_WRITE | FILE_COMMON | FILE_TXT | FILE_ANSI);

   if(m_fileHandle == INVALID_HANDLE)
   {
      int errorCode = ::GetLastError();
      Print("[JSON] ✗ Failed to open file for writing: ", m_filePath);
      Print("[JSON] Error code: ", errorCode);
      return false;
   }

   Print("[JSON] File opened successfully, handle: ", m_fileHandle);

   //--- Write content
   uint bytesWritten = FileWriteString(m_fileHandle, m_jsonContent);

   Print("[JSON] Bytes written: ", bytesWritten);

   //--- Close file
   FileClose(m_fileHandle);
   m_fileHandle = INVALID_HANDLE;

   if(bytesWritten == 0)
   {
      Print("[JSON] ✗ Failed to write JSON content (0 bytes written)");
      return false;
   }

   Print("[JSON] ✓ File closed successfully");
   return true;
}

//+------------------------------------------------------------------+
//| Add string value                                                 |
//+------------------------------------------------------------------+
void CJSONExporter::AddString(string key, string value)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": \"" + EscapeString(value) + "\"";
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add integer value                                                |
//+------------------------------------------------------------------+
void CJSONExporter::AddInt(string key, int value)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": " + IntegerToString(value);
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add long value                                                   |
//+------------------------------------------------------------------+
void CJSONExporter::AddLong(string key, long value)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": " + IntegerToString(value);
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add double value                                                 |
//+------------------------------------------------------------------+
void CJSONExporter::AddDouble(string key, double value, int digits)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": " + DoubleToString(value, digits);
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add boolean value                                                |
//+------------------------------------------------------------------+
void CJSONExporter::AddBool(string key, bool value)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   string boolStr = value ? "true" : "false";
   m_jsonContent += indent + "\"" + key + "\": " + boolStr;
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Begin array                                                       |
//+------------------------------------------------------------------+
void CJSONExporter::BeginArray(string key)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": [";
   m_isArrayOpen = true;
   m_arrayDepth++;
   m_firstElement = true;
}

//+------------------------------------------------------------------+
//| End array                                                         |
//+------------------------------------------------------------------+
void CJSONExporter::EndArray()
{
   m_arrayDepth--;
   m_jsonContent += "]";
   m_isArrayOpen = false;
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add string to array                                              |
//+------------------------------------------------------------------+
void CJSONExporter::AddArrayString(string value)
{
   if(!m_firstElement)
      m_jsonContent += ", ";

   m_jsonContent += "\"" + EscapeString(value) + "\"";
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add integer to array                                             |
//+------------------------------------------------------------------+
void CJSONExporter::AddArrayInt(int value)
{
   if(!m_firstElement)
      m_jsonContent += ", ";

   m_jsonContent += IntegerToString(value);
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add double to array                                              |
//+------------------------------------------------------------------+
void CJSONExporter::AddArrayDouble(double value, int digits)
{
   if(!m_firstElement)
      m_jsonContent += ", ";

   m_jsonContent += DoubleToString(value, digits);
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Add boolean to array                                             |
//+------------------------------------------------------------------+
void CJSONExporter::AddArrayBool(bool value)
{
   if(!m_firstElement)
      m_jsonContent += ", ";

   string boolStr = value ? "true" : "false";
   m_jsonContent += boolStr;
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Begin object                                                      |
//+------------------------------------------------------------------+
void CJSONExporter::BeginObject(string key)
{
   if(!m_firstElement)
      m_jsonContent += ",\n";

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += indent + "\"" + key + "\": {\n";
   m_isObjectOpen = true;
   m_arrayDepth++;
   m_firstElement = true;
}

//+------------------------------------------------------------------+
//| End object                                                        |
//+------------------------------------------------------------------+
void CJSONExporter::EndObject()
{
   m_arrayDepth--;

   string indent = "  ";
   for(int i = 0; i < m_arrayDepth; i++)
      indent += "  ";

   m_jsonContent += "\n" + indent + "}";
   m_isObjectOpen = false;
   m_firstElement = false;
}

//+------------------------------------------------------------------+
//| Escape special characters in strings                             |
//+------------------------------------------------------------------+
string CJSONExporter::EscapeString(string str)
{
   string output = str;

   //--- Replace backslash first
   StringReplace(output, "\\", "\\\\");

   //--- Replace double quotes
   StringReplace(output, "\"", "\\\"");

   //--- Replace newlines
   StringReplace(output, "\n", "\\n");

   //--- Replace tabs
   StringReplace(output, "\t", "\\t");

   //--- Replace carriage returns
   StringReplace(output, "\r", "\\r");

   return output;
}

//+------------------------------------------------------------------+
//| Get last error message                                           |
//+------------------------------------------------------------------+
string CJSONExporter::GetLastError()
{
   int errorCode = ::GetLastError();
   return "Error " + IntegerToString(errorCode);
}
