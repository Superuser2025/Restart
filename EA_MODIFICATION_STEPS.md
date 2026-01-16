# EA Modification Guide - YOUR MLALGO EA

## Your EA Location:
```
C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Experts\Advisors\MLALGO\InstitutionalTradingRobot_v3.mq5
```

---

## Changes to Make:

### 1. Add Include Statement (Around Line 14-15)

**Find this:**
```mql5
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
```

**Add this line AFTER:**
```mql5
#include "JSONExporter.mqh"
```

**Result should look like:**
```mql5
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include "JSONExporter.mqh"  // ← NEW LINE
```

---

### 2. Add Global Variable (Around Line 721)

**Find this:**
```mql5
CMLTradingSystem* ml_system = NULL;
```

**Add this line AFTER:**
```mql5
CJSONExporter jsonExporter;
```

**Result should look like:**
```mql5
CMLTradingSystem* ml_system = NULL;
CJSONExporter jsonExporter;  // ← NEW LINE
```

---

### 3. Initialize in OnInit() (Around Line 860)

**Find a place in OnInit() function (after ML system initialization)**

**Add these lines:**
```mql5
    // Initialize JSON Exporter
    if(!jsonExporter.Init("ML_Data\\market_data.json"))
    {
        Print("WARNING: JSON Exporter init failed");
    }
    else
    {
        Print("✓ JSON Exporter initialized");
    }

    // Set timer for data export
    EventSetTimer(10);
    Print("✓ Timer set for 10-second data export");
```

---

### 4. Add Export Function (Add at the END of file, before last closing brace)

**Scroll to the VERY END of the file**

**Add this NEW function:**
```mql5
//+------------------------------------------------------------------+
//| Export Market Data to JSON                                       |
//+------------------------------------------------------------------+
void ExportMarketDataToJSON()
{
    jsonExporter.BeginExport();

    // Basic info
    jsonExporter.AddString("symbol", Symbol());
    jsonExporter.AddString("timeframe", EnumToString(Period()));
    jsonExporter.AddLong("timestamp", TimeCurrent());
    jsonExporter.AddDouble("bid", SymbolInfoDouble(Symbol(), SYMBOL_BID), 5);
    jsonExporter.AddDouble("ask", SymbolInfoDouble(Symbol(), SYMBOL_ASK), 5);

    double spread = (SymbolInfoDouble(Symbol(), SYMBOL_ASK) - SymbolInfoDouble(Symbol(), SYMBOL_BID)) / _Point;
    jsonExporter.AddDouble("spread", spread, 2);

    // Account
    jsonExporter.AddDouble("account_balance", AccountInfoDouble(ACCOUNT_BALANCE), 2);
    jsonExporter.AddDouble("account_equity", AccountInfoDouble(ACCOUNT_EQUITY), 2);

    // Trading
    jsonExporter.AddBool("auto_trading", EnableTrading);
    jsonExporter.AddInt("positions_total", PositionsTotal());
    jsonExporter.AddInt("orders_total", OrdersTotal());

    double total_pnl = 0.0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
            total_pnl += PositionGetDouble(POSITION_PROFIT);
    }
    jsonExporter.AddDouble("total_pnl", total_pnl, 2);

    // ML status
    jsonExporter.AddBool("ml_enabled", ML_Enabled);

    jsonExporter.EndExport();
}
```

---

### 5. Modify or Add OnTimer() Function

**Look for OnTimer() function**

**If it EXISTS, ADD this line inside:**
```mql5
void OnTimer()
{
    ExportMarketDataToJSON();  // ← ADD THIS
    // ... other timer code ...
}
```

**If it DOESN'T EXIST, ADD this entire function:**
```mql5
//+------------------------------------------------------------------+
//| Timer function                                                    |
//+------------------------------------------------------------------+
void OnTimer()
{
    ExportMarketDataToJSON();
}
```

---

### 6. Cleanup in OnDeinit() (Find OnDeinit function)

**Inside OnDeinit(), ADD:**
```mql5
void OnDeinit(const int reason)
{
    EventKillTimer();  // ← ADD THIS LINE

    // ... rest of existing code ...
}
```

---

## Compile and Test:

1. **Press F7** to compile
2. **Should see:** "0 error(s), 0 warning(s)"
3. **Remove EA from chart**
4. **Drag EA back onto chart**
5. **Wait 10 seconds**
6. **Check for file:**
   ```
   C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files\ML_Data\market_data.json
   ```

---

## If You Get Errors:

**"Cannot open include file JSONExporter.mqh"**
- JSONExporter.mqh is not in the MLALGO folder
- Copy it there

**"Undeclared identifier"**
- Check you added the #include line
- Make sure no typos

**"Timer already exists"**
- EventSetTimer is being called twice
- Remove one of them

---

**Start with Step 1 and let me know if you need help with any step!**
