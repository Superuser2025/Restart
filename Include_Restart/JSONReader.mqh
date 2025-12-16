//+------------------------------------------------------------------+
//|                                                   JSONReader.mqh |
//|                                    AppleTrader Pro Institutional |
//|                                                                  |
//| JSON Reader System for Python GUI Communication                  |
//| Reads commands and settings from Python GUI via JSON files      |
//+------------------------------------------------------------------+
#property copyright "AppleTrader Pro"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| CJSONReader Class                                                |
//| Handles reading commands from Python GUI via JSON files          |
//+------------------------------------------------------------------+
class CJSONReader
{
private:
   string            m_filePath;                  // Command file path
   string            m_jsonContent;               // Last read JSON content
   int               m_fileHandle;                // File handle
   datetime          m_lastModified;              // Last file modification time

   //--- Parsed data storage
   string            m_command;                   // Current command
   string            m_stringValues[];            // String values
   string            m_stringKeys[];              // String keys
   double            m_doubleValues[];            // Double values
   string            m_doubleKeys[];              // Double keys
   long              m_longValues[];              // Long values
   string            m_longKeys[];                // Long keys
   bool              m_boolValues[];              // Bool values
   string            m_boolKeys[];                // Bool keys

public:
                     CJSONReader();
                    ~CJSONReader();

   //--- Initialization
   bool              Init(string filePath);

   //--- Command reading
   string            ReadCommand();
   bool              HasNewCommand();

   //--- Data retrieval methods
   string            GetString(string key, string defaultValue);
   double            GetDouble(string key, double defaultValue);
   long              GetLong(string key, long defaultValue);
   bool              GetBool(string key, bool defaultValue);

   //--- Utility
   void              ClearData();
   string            GetLastError();

private:
   //--- Parsing methods
   bool              ParseJSON(string json);
   string            ExtractValue(string json, string key);
   bool              IsNumeric(string str);
   void              DeleteCommandFile();
};

//+------------------------------------------------------------------+
//| Constructor                                                       |
//+------------------------------------------------------------------+
CJSONReader::CJSONReader()
{
   m_filePath = "";
   m_jsonContent = "";
   m_fileHandle = INVALID_HANDLE;
   m_lastModified = 0;
   m_command = "";
}

//+------------------------------------------------------------------+
//| Destructor                                                        |
//+------------------------------------------------------------------+
CJSONReader::~CJSONReader()
{
   if(m_fileHandle != INVALID_HANDLE)
   {
      FileClose(m_fileHandle);
   }
}

//+------------------------------------------------------------------+
//| Initialize reader                                                |
//+------------------------------------------------------------------+
bool CJSONReader::Init(string filePath)
{
   m_filePath = filePath;
   Print("JSONReader initialized: ", filePath);
   return true;
}

//+------------------------------------------------------------------+
//| Check if file has new command                                    |
//+------------------------------------------------------------------+
bool CJSONReader::HasNewCommand()
{
   //--- Check if file exists
   string fullPath = m_filePath;

   //--- Get file modification time
   datetime modified = (datetime)FileGetInteger(fullPath, FILE_MODIFY_DATE, FILE_COMMON);

   if(modified == 0)
   {
      return false;  // File doesn't exist
   }

   //--- Check if file was modified since last read
   if(modified > m_lastModified)
   {
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Read command from JSON file                                      |
//+------------------------------------------------------------------+
string CJSONReader::ReadCommand()
{
   //--- Clear previous data
   ClearData();

   //--- Check if file has new command
   if(!HasNewCommand())
   {
      return "";
   }

   //--- Open file
   m_fileHandle = FileOpen(m_filePath, FILE_READ | FILE_COMMON | FILE_TXT | FILE_ANSI);

   if(m_fileHandle == INVALID_HANDLE)
   {
      // File doesn't exist or can't be opened (not an error, just no commands)
      return "";
   }

   //--- Read file content
   m_jsonContent = "";
   while(!FileIsEnding(m_fileHandle))
   {
      m_jsonContent += FileReadString(m_fileHandle);
   }

   //--- Close file
   FileClose(m_fileHandle);
   m_fileHandle = INVALID_HANDLE;

   //--- Update last modified time
   m_lastModified = TimeCurrent();

   //--- Delete command file after reading (one-time command)
   DeleteCommandFile();

   //--- Parse JSON
   if(!ParseJSON(m_jsonContent))
   {
      Print("Failed to parse JSON command");
      return "";
   }

   return m_command;
}

//+------------------------------------------------------------------+
//| Parse JSON content                                               |
//+------------------------------------------------------------------+
bool CJSONReader::ParseJSON(string json)
{
   //--- Extract command
   m_command = ExtractValue(json, "command");

   if(m_command == "")
   {
      return false;
   }

   //--- Extract common parameters based on command type
   if(m_command == "PLACE_ORDER")
   {
      //--- Extract order parameters
      ArrayResize(m_stringKeys, 1);
      ArrayResize(m_stringValues, 1);
      m_stringKeys[0] = "type";
      m_stringValues[0] = ExtractValue(json, "type");

      ArrayResize(m_doubleKeys, 3);
      ArrayResize(m_doubleValues, 3);
      m_doubleKeys[0] = "volume";
      m_doubleValues[0] = StringToDouble(ExtractValue(json, "volume"));
      m_doubleKeys[1] = "sl";
      m_doubleValues[1] = StringToDouble(ExtractValue(json, "sl"));
      m_doubleKeys[2] = "tp";
      m_doubleValues[2] = StringToDouble(ExtractValue(json, "tp"));
   }
   else if(m_command == "CLOSE_POSITION")
   {
      //--- Extract ticket
      ArrayResize(m_longKeys, 1);
      ArrayResize(m_longValues, 1);
      m_longKeys[0] = "ticket";
      m_longValues[0] = StringToInteger(ExtractValue(json, "ticket"));
   }
   else if(m_command == "UPDATE_SETTINGS")
   {
      //--- Extract settings
      ArrayResize(m_boolKeys, 1);
      ArrayResize(m_boolValues, 1);
      m_boolKeys[0] = "enable_trading";
      string val = ExtractValue(json, "enable_trading");
      m_boolValues[0] = (val == "true");

      ArrayResize(m_doubleKeys, 1);
      ArrayResize(m_doubleValues, 1);
      m_doubleKeys[0] = "risk_percent";
      m_doubleValues[0] = StringToDouble(ExtractValue(json, "risk_percent"));
   }
   else if(m_command == "UPDATE_ML")
   {
      //--- Extract ML data
      ArrayResize(m_boolKeys, 1);
      ArrayResize(m_boolValues, 1);
      m_boolKeys[0] = "enabled";
      string val = ExtractValue(json, "enabled");
      m_boolValues[0] = (val == "true");

      ArrayResize(m_stringKeys, 1);
      ArrayResize(m_stringValues, 1);
      m_stringKeys[0] = "signal";
      m_stringValues[0] = ExtractValue(json, "signal");

      ArrayResize(m_doubleKeys, 2);
      ArrayResize(m_doubleValues, 2);
      m_doubleKeys[0] = "probability";
      m_doubleValues[0] = StringToDouble(ExtractValue(json, "probability"));
      m_doubleKeys[1] = "confidence";
      m_doubleValues[1] = StringToDouble(ExtractValue(json, "confidence"));
   }

   return true;
}

//+------------------------------------------------------------------+
//| Extract value from JSON by key                                   |
//+------------------------------------------------------------------+
string CJSONReader::ExtractValue(string json, string key)
{
   //--- Simple JSON parser (basic implementation)
   //--- Look for "key": "value" or "key": value pattern

   string searchPattern = "\"" + key + "\"";
   int keyPos = StringFind(json, searchPattern);

   if(keyPos == -1)
   {
      return "";
   }

   //--- Find the colon after the key
   int colonPos = StringFind(json, ":", keyPos);
   if(colonPos == -1)
   {
      return "";
   }

   //--- Skip whitespace after colon
   int valueStart = colonPos + 1;
   while(valueStart < StringLen(json) &&
         (StringGetCharacter(json, valueStart) == ' ' ||
          StringGetCharacter(json, valueStart) == '\t' ||
          StringGetCharacter(json, valueStart) == '\n'))
   {
      valueStart++;
   }

   //--- Check if value is a string (starts with ")
   bool isString = false;
   if(StringGetCharacter(json, valueStart) == '"')
   {
      isString = true;
      valueStart++;  // Skip opening quote
   }

   //--- Find end of value
   int valueEnd = valueStart;
   if(isString)
   {
      //--- Find closing quote
      valueEnd = StringFind(json, "\"", valueStart);
      if(valueEnd == -1)
      {
         return "";
      }
   }
   else
   {
      //--- Find comma, closing brace, or end of string
      while(valueEnd < StringLen(json))
      {
         ushort ch = StringGetCharacter(json, valueEnd);
         if(ch == ',' || ch == '}' || ch == ']' || ch == '\n')
         {
            break;
         }
         valueEnd++;
      }
   }

   //--- Extract value
   string value = StringSubstr(json, valueStart, valueEnd - valueStart);

   //--- Trim whitespace
   StringTrimLeft(value);
   StringTrimRight(value);

   return value;
}

//+------------------------------------------------------------------+
//| Check if string is numeric                                       |
//+------------------------------------------------------------------+
bool CJSONReader::IsNumeric(string str)
{
   if(StringLen(str) == 0)
      return false;

   for(int i = 0; i < StringLen(str); i++)
   {
      ushort ch = StringGetCharacter(str, i);
      if(ch != '.' && ch != '-' && ch != '+' && (ch < '0' || ch > '9'))
      {
         return false;
      }
   }

   return true;
}

//+------------------------------------------------------------------+
//| Get string value by key                                          |
//+------------------------------------------------------------------+
string CJSONReader::GetString(string key, string defaultValue)
{
   for(int i = 0; i < ArraySize(m_stringKeys); i++)
   {
      if(m_stringKeys[i] == key)
      {
         return m_stringValues[i];
      }
   }
   return defaultValue;
}

//+------------------------------------------------------------------+
//| Get double value by key                                          |
//+------------------------------------------------------------------+
double CJSONReader::GetDouble(string key, double defaultValue)
{
   for(int i = 0; i < ArraySize(m_doubleKeys); i++)
   {
      if(m_doubleKeys[i] == key)
      {
         return m_doubleValues[i];
      }
   }
   return defaultValue;
}

//+------------------------------------------------------------------+
//| Get long value by key                                            |
//+------------------------------------------------------------------+
long CJSONReader::GetLong(string key, long defaultValue)
{
   for(int i = 0; i < ArraySize(m_longKeys); i++)
   {
      if(m_longKeys[i] == key)
      {
         return m_longValues[i];
      }
   }
   return defaultValue;
}

//+------------------------------------------------------------------+
//| Get bool value by key                                            |
//+------------------------------------------------------------------+
bool CJSONReader::GetBool(string key, bool defaultValue)
{
   for(int i = 0; i < ArraySize(m_boolKeys); i++)
   {
      if(m_boolKeys[i] == key)
      {
         return m_boolValues[i];
      }
   }
   return defaultValue;
}

//+------------------------------------------------------------------+
//| Clear all stored data                                            |
//+------------------------------------------------------------------+
void CJSONReader::ClearData()
{
   m_command = "";
   ArrayResize(m_stringKeys, 0);
   ArrayResize(m_stringValues, 0);
   ArrayResize(m_doubleKeys, 0);
   ArrayResize(m_doubleValues, 0);
   ArrayResize(m_longKeys, 0);
   ArrayResize(m_longValues, 0);
   ArrayResize(m_boolKeys, 0);
   ArrayResize(m_boolValues, 0);
}

//+------------------------------------------------------------------+
//| Delete command file after reading                                |
//+------------------------------------------------------------------+
void CJSONReader::DeleteCommandFile()
{
   //--- Delete the command file to prevent re-reading
   FileDelete(m_filePath, FILE_COMMON);
}

//+------------------------------------------------------------------+
//| Get last error message                                           |
//+------------------------------------------------------------------+
string CJSONReader::GetLastError()
{
   int errorCode = ::GetLastError();
   return "Error " + IntegerToString(errorCode);
}
