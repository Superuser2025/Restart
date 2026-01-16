# ML Integration System - Implementation Guide

## 🎯 Goal
Connect your MLALGO EA with Python ML system for intelligent trading decisions.

---

## 📁 File Structure

```
MT5 Files Directory:
C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files\
├── ML_Data/
│   ├── market_data.json      (EA → Python GUI)
│   ├── features.json          (EA → Python ML)
│   └── prediction.json        (Python ML → EA)
```

---

## STEP 1: Modify Your MLALGO EA

### Changes Needed in `InstitutionalTradingRobot_v3.mq5`:

#### 1. Add JSON Exporter Include (after line 14)
```mql5
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include "JSONExporter.mqh"  // ← ADD THIS LINE
```

#### 2. Add Global JSON Exporter (around line 721, after ml_system declaration)
```mql5
CMLTradingSystem* ml_system = NULL;
CJSONExporter jsonExporter;  // ← ADD THIS LINE
```

#### 3. Initialize JSON Exporter in OnInit() (around line 860)
```mql5
    // Initialize JSON Exporter
    if(!jsonExporter.Init("ML_Data\\market_data.json"))
    {
        Print("WARNING: JSON Exporter initialization failed");
    }
    else
    {
        Print("✓ JSON Exporter initialized");
    }
```

#### 4. Add Export Function (add this new function anywhere after OnInit)
```mql5
//+------------------------------------------------------------------+
//| Export Market Data to JSON for Python                            |
//+------------------------------------------------------------------+
void ExportMarketDataToJSON()
{
    jsonExporter.BeginExport();

    // Basic market info
    jsonExporter.AddString("symbol", Symbol());
    jsonExporter.AddString("timeframe", EnumToString(Period()));
    jsonExporter.AddLong("timestamp", TimeCurrent());
    jsonExporter.AddDouble("bid", SymbolInfoDouble(Symbol(), SYMBOL_BID), 5);
    jsonExporter.AddDouble("ask", SymbolInfoDouble(Symbol(), SYMBOL_ASK), 5);
    jsonExporter.AddDouble("spread", (SymbolInfoDouble(Symbol(), SYMBOL_ASK) - SymbolInfoDouble(Symbol(), SYMBOL_BID)) / _Point, 1);

    // Account info
    jsonExporter.AddDouble("account_balance", AccountInfoDouble(ACCOUNT_BALANCE), 2);
    jsonExporter.AddDouble("account_equity", AccountInfoDouble(ACCOUNT_EQUITY), 2);
    jsonExporter.AddDouble("account_margin", AccountInfoDouble(ACCOUNT_MARGIN), 2);
    jsonExporter.AddDouble("account_free_margin", AccountInfoDouble(ACCOUNT_FREEMARGIN), 2);

    // Trading status
    jsonExporter.AddBool("auto_trading", EnableTrading);
    jsonExporter.AddInt("positions_total", PositionsTotal());
    jsonExporter.AddInt("orders_total", OrdersTotal());

    // Calculate total P&L
    double total_pnl = 0.0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            total_pnl += PositionGetDouble(POSITION_PROFIT);
        }
    }
    jsonExporter.AddDouble("total_pnl", total_pnl, 2);

    // ML System status
    jsonExporter.AddBool("ml_enabled", ML_Enabled);

    // Profile info
    string profile_name = "";
    switch(TradingProfile)
    {
        case PROFILE_M5_SCALPING: profile_name = "M5_SCALPING"; break;
        case PROFILE_M15_INTRADAY: profile_name = "M15_INTRADAY"; break;
        case PROFILE_H1_SWING: profile_name = "H1_SWING"; break;
        case PROFILE_H4_POSITION: profile_name = "H4_POSITION"; break;
        case PROFILE_D1_INVESTOR: profile_name = "D1_INVESTOR"; break;
        default: profile_name = "CUSTOM"; break;
    }
    jsonExporter.AddString("trading_profile", profile_name);

    jsonExporter.EndExport();
}
```

#### 5. Add Timer to Export Data (in OnInit, around line 900)
```mql5
    // Set timer for data export (every 10 seconds)
    EventSetTimer(10);
    Print("✓ Timer set for data export (10 seconds)");
```

#### 6. Modify OnTimer() Function (add export call)
```mql5
void OnTimer()
{
    // Export data to Python
    ExportMarketDataToJSON();
}
```

#### 7. Add OnDeinit Cleanup
```mql5
void OnDeinit(const int reason)
{
    EventKillTimer();

    // ... existing cleanup code ...
}
```

---

## STEP 2: Copy Files to MT5

1. **Copy JSONExporter.mqh**:
   ```
   From: C:\PythonProjects\Restart\Python_Restart\MLALGO\JSONExporter.mqh
   To:   C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Include\
   ```

2. **Create ML_Data directory**:
   ```
   C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files\ML_Data\
   ```

---

## STEP 3: Recompile EA in MT5

1. Open MetaEditor (F4 in MT5)
2. Open `InstitutionalTradingRobot_v3.mq5`
3. Make the changes listed above
4. Press F7 to compile
5. Fix any errors
6. Reload EA on chart

---

## STEP 4: Verify Export

1. Wait 10 seconds
2. Check:
   ```
   C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files\ML_Data\market_data.json
   ```
3. File should exist and contain JSON data

---

## STEP 5: Python ML Service (I'll create this next)

Coming up:
- `ml_service.py` - Reads features, generates predictions
- Auto-runs in background
- Writes prediction.json for EA to read

---

## Expected Data Flow

```
Every 10 seconds:

EA (OnTimer)
  → Exports market_data.json
  → Exports features.json

Python ML Service (watching files)
  → Reads features.json
  → Runs ML model
  → Writes prediction.json

EA (OnTick)
  → Reads prediction.json
  → Uses ML prediction in trading decision
```

---

## Troubleshooting

**If JSON files not created:**
1. Check MT5 Experts log for errors
2. Verify ML_Data directory exists
3. Check file permissions
4. Look for error messages in OnTimer

**If EA won't compile:**
1. Ensure JSONExporter.mqh is in Include folder
2. Check for syntax errors
3. Verify all brackets match

---

## Next Steps

After EA is exporting data:
1. I'll create the Python ML service
2. Set up automatic prediction generation
3. Connect EA to read predictions
4. Test complete pipeline

---

**Ready to implement? Let me know when you've made the changes and recompiled!**
