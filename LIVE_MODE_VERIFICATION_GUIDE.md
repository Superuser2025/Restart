# Live Mode Verification Guide

**How to confirm your application is actually using real MT5 data**

---

## 🔍 Quick Diagnostic Script

Run this while the application is running:

```bash
cd C:\PythonProjects\Restart\Python_Restart\python
py check_live_mode.py
```

This will tell you:
- ✓ Is demo mode OFF?
- ✓ Is MT5 connector active?
- ✓ What data is flowing?
- ✓ Are widgets using real data?

---

## 👀 Visual Verification Checklist

### **1. Check Status Bar (Bottom of Window)**

**DEMO Mode:**
- Color: Orange/Yellow
- Text: "DEMO mode" or similar

**LIVE Mode:**
- Color: **GREEN**
- Text: "LIVE mode" or "Switched to LIVE mode"

---

### **2. Check Settings Menu**

Click **Settings** in top menu bar:

**DEMO Mode:**
- Shows: "Enable Live Mode" (unchecked ☐)

**LIVE Mode:**
- Shows: "Disable Live Mode" (checked ✓)

---

### **3. Compare Dashboard Cards (Top) with MT5**

Open your MT5 terminal and compare:

| Field | MT5 Terminal | AppleTrader Dashboard |
|-------|--------------|----------------------|
| Account Balance | $10,000.00 | Should MATCH |
| Account Equity | $10,250.00 | Should MATCH |
| Profit | +$250.00 | Should MATCH |

**If they DON'T match → Still in DEMO mode**

---

### **4. Compare Current Prices with MT5**

Look at any widget showing prices (Dashboard, Opportunity Cards, Chart):

**Example:**
- MT5 shows EURUSD: 1.08456
- AppleTrader shows: 1.08456 ± 0.0001

**Tolerance:** Within 1-2 pips is OK (small delay)

**If completely different → Still in DEMO mode**

---

### **5. Check Opportunity Scanner Symbols**

**DEMO Mode Behavior:**
- Shows generic symbols: EURUSD, GBPUSD, USDJPY
- Quality scores look "perfect" (75-95)
- Same opportunities appear repeatedly

**LIVE Mode Behavior:**
- Shows YOUR tracked symbols from MT5
- Quality scores vary realistically
- Opportunities change based on real market

---

### **6. Check Symbol in Dashboard Cards**

Look at the symbol name in dashboard cards:

**DEMO Mode:**
- Always shows "EURUSD" or generic symbol
- Doesn't change even if you select different symbol

**LIVE Mode:**
- Shows actual symbol from MT5 (EURAUD, GBPJPY, etc.)
- Changes when you select different chart in MT5

---

### **7. Account Balance Test**

**Definitive Test:**

1. Note your account balance in AppleTrader dashboard
2. Open MT5 terminal
3. Check actual account balance

**Result:**
- **Matches** → Using LIVE data ✓
- **Different** → Using DEMO data ✗

---

## 🔧 Troubleshooting: "I enabled Live Mode but still seeing demo data"

### **Symptom:** Toggled to Live Mode but widgets unchanged

**Possible Causes:**

### **Issue 1: Menu toggle didn't actually switch**

**Check:**
```bash
py check_live_mode.py
```

Look for: `demo_mode = False`

**If still True:**
- Try toggling again in GUI
- Restart application and toggle on startup

---

### **Issue 2: Widgets cached demo data**

**Solution:** Force refresh all widgets

In the application:
1. Click **View** → **Refresh All**
2. Or restart the application with Live Mode enabled

---

### **Issue 3: MT5 not sending fresh data**

**Check:**
```bash
py verify_mt5_connection.py
```

Look for:
- ✓ File is FRESH (< 60s old)
- ✓ MT5 Connector: CONNECTED

**If DISCONNECTED:**
1. Check MT5 terminal is open
2. Check EA is loaded on a chart
3. Check AutoTrading button is ON (green)

---

### **Issue 4: Data update timer not running**

**Symptom:** Data never updates, even in Live Mode

**Solution:**
- Restart the application
- Check console for errors
- Verify `self.data_timer.start(1000)` is running

---

## 📊 Expected Behavior in LIVE Mode

### **Dashboard Cards:**
- 💰 Account Balance → Real MT5 account balance
- 📊 Market → Actual current price
- 🛡️ Risk → Real drawdown calculation
- 🤖 AI Action → Based on real market conditions

### **Opportunity Scanner:**
- Shows real pattern detections
- Symbols match your MT5 watchlist
- Quality scores based on actual confluences
- Entry/SL/TP prices are actionable

### **Correlation Heatmap:**
- Real-time correlations between pairs
- Updates as market moves
- Matches actual price relationships

### **All Other Widgets:**
- Display real-time MT5 data
- Update every 1-5 seconds
- Reflect actual market conditions

---

## ✅ Final Verification

**Run all 3 checks:**

```bash
# Check 1: MT5 Connection
py verify_mt5_connection.py
# Should show: ✓ MT5 Connector: CONNECTED

# Check 2: Live Mode Status
py check_live_mode.py
# Should show: ✓ LIVE MODE IS ACTIVE

# Check 3: Manual Verification
# Compare account balance with MT5 terminal
```

**If all 3 pass → You're definitely in LIVE mode!**

---

## 🎯 Quick Test Script

Want a one-liner to check? Run this in Python console:

```python
from core.demo_mode_manager import is_demo_mode
from core.mt5_connector import mt5_connector

print(f"Demo Mode: {is_demo_mode()}")
print(f"MT5 Connected: {mt5_connector.is_connection_active()}")
print(f"Current Symbol: {mt5_connector.last_data.get('symbol', 'N/A')}")
print(f"Current Bid: {mt5_connector.last_data.get('bid', 0)}")
```

**Expected Output (Live Mode):**
```
Demo Mode: False
MT5 Connected: True
Current Symbol: EURAUD
Current Bid: 1.77178
```

---

## 📞 Still Not Sure?

**Take a screenshot showing:**
1. Top menu bar with Settings menu open (showing "Disable Live Mode" checked)
2. Status bar at bottom (showing GREEN color)
3. Dashboard cards with account balance
4. One opportunity card with symbol/price

**Then compare:**
- Dashboard balance with MT5 terminal balance
- Opportunity price with MT5 chart price

**If they match → You're in LIVE mode!**
