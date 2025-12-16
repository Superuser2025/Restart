# Session Momentum Widget - Testing Guide

**Created**: 2025-12-16
**Branch**: `claude/fix-ea-ai-ml-nuyBz`
**Status**: ✅ READY FOR TESTING

---

## What's Been Completed

The **Session Momentum Scanner Widget** is now fully functional with AI assistance! This is your first complete widget to test.

### Features Implemented:
1. ✅ **AI Checkbox** - Toggle AI suggestions on/off
2. ✅ **Demo/Live Mode** - Switches between demo data and real MT5 data
3. ✅ **Multi-Symbol Support** - Scans all configured symbols (EURUSD, GBPUSD, etc.)
4. ✅ **Momentum Leaderboard** - Shows top 10 pairs ranked by momentum
5. ✅ **AI Analysis** - Provides actionable trading recommendations
6. ✅ **Best Opportunity Highlight** - Shows top momentum pair
7. ✅ **Momentum Alerts** - Alerts for high momentum setups

---

## How to Test

### Step 1: Launch the Application

```bash
cd /home/user/Restart/Python_Restart/python
python3 main_enhanced.py
```

**Expected Result**: Application window opens with dashboard

### Step 2: Locate Session Momentum Widget

- Look for the **"⚡ Session Momentum Scanner"** panel
- Should be one of the visible widgets in the main window

### Step 3: Test Demo Mode (Default)

**What You Should See:**
- Orange **"🎮 DEMO MODE"** button in toolbar (top of window)
- Status: **"⚠️ DEMO DATA - Safe Testing Mode"**
- Leaderboard populated with 5 demo currency pairs
- Each pair shows:
  - Rank number (1-5)
  - Symbol name (e.g., EURUSD)
  - Colored momentum bar (green/yellow/orange/gray)
  - Momentum percentage (e.g., "89%")
  - Pips moved (e.g., "142 pips")
  - Direction indicator (🟢 bullish / 🔴 bearish)
  - Trending indicator (🔥 hot / ⚡ strong / blank)

**What to Check:**
1. ✓ Leaderboard refreshes every 3 seconds with new random data
2. ✓ Best opportunity shows top pair with highest momentum
3. ✓ Status shows "Demo Mode - 5 symbols" at bottom

### Step 4: Test AI Assistance

**Enable AI:**
1. Find the **"🤖 AI Assist"** checkbox in the widget header
2. Click to enable it

**What You Should See:**
- AI suggestion frame appears below alerts section
- After 3-second refresh, AI analysis displays:
  ```
  🔥 Prime opportunity on GBPUSD

  📊 Momentum: 89% (VERY STRONG)
  📈 Direction: BULLISH
  📏 Session Range: 142 pips

  💡 Recommendation: Consider bullish entry
  ✓ Strong trend + volume + session alignment
  ✓ Risk/Reward should be favorable
  ```

**What to Check:**
1. ✓ AI checkbox toggles on/off properly
2. ✓ AI suggestions update when data refreshes (every 3 seconds)
3. ✓ Different momentum scores show different recommendations:
   - 85%+: "🔥 Prime opportunity" + "Consider [direction] entry"
   - 75-84%: "⚡ Good momentum" + "Consider [direction] entry"
   - 65-74%: "✓ Decent setup" + "Watch for confirmation"
   - <65%: "⚠️ Low momentum" + "Wait for better setup"
4. ✓ Disabling AI checkbox hides suggestions

### Step 5: Test Live Mode Switch

**Switch to Live:**
1. Click the **"🎮 DEMO MODE"** button in the toolbar
2. Button should turn red: **"🔴 LIVE MODE"**
3. Status changes to: **"🔴 LIVE DATA - Real MT5 Connection"**

**Expected Behavior:**
- Widget attempts to connect to MetaTrader5
- If MT5 not running: Shows "Live: EURUSD" status
- If MT5 running: Would fetch real market data

**Note**: On Linux, MT5 may not be available. That's expected. The important thing is:
- ✓ Mode toggle button works
- ✓ Widget responds to mode change
- ✓ No crashes or errors

### Step 6: Test Symbol Selector

**Change Active Symbol:**
1. Find the **Symbol dropdown** in toolbar (next to Demo button)
2. Select different symbols (GBPUSD, USDJPY, etc.)

**Expected Behavior:**
- Symbol changes globally (affects other widgets too)
- Session Momentum Scanner continues showing ALL symbols (it's a multi-symbol widget)
- Status updates accordingly

### Step 7: Test Interaction

**Click on Pairs:**
1. Click on any pair in the leaderboard
2. Should highlight that row
3. Emits signal to switch other widgets to that symbol

**Auto-Focus:**
1. Click the **"🎯 Auto-Focus"** button
2. System should automatically switch to highest momentum pair
3. Button highlights when active

**Refresh:**
1. Click the **"🔄"** button
2. Forces immediate data refresh

---

## What AI Suggestions Mean

### Confidence Indicators:
- 🔥 **VERY STRONG** (85%+ momentum): Excellent setup, all factors aligned
- ⚡ **STRONG** (75-84% momentum): Good setup, favorable conditions
- ✓ **MODERATE** (65-74% momentum): Decent setup, needs confirmation
- ⚠️ **WEAK** (<65% momentum): Poor setup, wait for better opportunity

### Recommendations:
1. **"Consider [bullish/bearish] entry"**: Setup looks good, align with your strategy
2. **"Watch for confirmation"**: Setup marginal, wait for price action confirmation
3. **"Wait for better setup"**: Momentum insufficient, don't force trades

---

## Troubleshooting

### Problem: Widget doesn't appear
**Solution**: Check that widget is enabled in main_enhanced.py configuration

### Problem: "No data" in leaderboard
**Solution**:
1. Verify demo mode is ON (orange button)
2. Check console for error messages
3. Restart application

### Problem: AI suggestions don't update
**Solution**:
1. Ensure AI checkbox is checked (🤖 AI Assist)
2. Wait 3 seconds for refresh cycle
3. Check that leaderboard has data

### Problem: Application won't start
**Solution**:
```bash
# Check dependencies
pip3 list | grep -E "PyQt6|numpy|pandas"

# If missing, reinstall
cd /home/user/Restart
pip3 install -r requirements.txt
```

### Problem: Demo mode toggle doesn't work
**Solution**:
1. Check console output for error messages
2. Verify demo_mode_manager is imported correctly
3. Try restarting application

---

## Expected Test Results Summary

| Feature | Status | What You Should See |
|---------|--------|---------------------|
| Widget Loads | ✅ | Panel visible with title "⚡ Session Momentum Scanner" |
| Demo Data | ✅ | 5 currency pairs with momentum bars |
| Data Refresh | ✅ | Updates every 3 seconds with new random values |
| AI Checkbox | ✅ | Toggles AI suggestions on/off |
| AI Suggestions | ✅ | Detailed momentum analysis with recommendations |
| Best Opportunity | ✅ | Top pair highlighted in green frame |
| Alerts | ✅ | Shows high momentum alerts (>70%) |
| Demo/Live Toggle | ✅ | Button switches orange ↔ red, no crashes |
| Symbol Selector | ✅ | Changes active symbol in dropdown |
| Leaderboard Click | ✅ | Rows highlight when clicked |
| Auto-Focus | ✅ | Button toggles, emits signal for top pair |
| Refresh Button | ✅ | Forces immediate update |

---

## What to Report

If everything works:
✅ **"Session Momentum Widget WORKING! Ready for next widget."**

If something doesn't work:
❌ **Describe what you see vs what you expected**
- Include any error messages from console
- Screenshot if possible
- Which feature specifically isn't working

---

## Next Steps After Testing

Once you confirm this widget works properly:

### Option A: Implement More Widgets (Recommended)
Apply the same pattern to remaining widgets:
1. Pattern Scorer Widget
2. Correlation Heatmap Widget
3. MTF Structure Map Widget
4. Order Flow Detector Widget
5. News Impact Predictor Widget
6. Risk/Reward Optimizer Widget
7. Opportunity Scanner Widget
8. Volatility Position Sizer Widget
9. Equity Curve Analyzer Widget
10. Trade Journal Widget
11. Price Action Commentary Widget

### Option B: Test on Windows with MT5
- Deploy to Windows machine with MT5
- Test live mode with real market data
- Verify MT5 integration works

### Option C: Start ML Training Pipeline
- Begin Phase 1 implementation from AI_STRATEGY_AND_PROFITABILITY_PLAN.md
- Set up database for trade tracking
- Implement feature engineering

---

## Quick Start Command

```bash
cd /home/user/Restart/Python_Restart/python
python3 main_enhanced.py
```

**Then**:
1. Find "⚡ Session Momentum Scanner" panel
2. Enable "🤖 AI Assist" checkbox
3. Watch AI suggestions update every 3 seconds
4. Test Demo ↔ Live toggle

---

**Questions?** Check SESSION_STATUS.md for implementation details or CRITICAL_ANALYSIS.md for system overview.
