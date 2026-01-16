# 🔧 Development Mode Guide
## Continue Developing Without License Restrictions

This guide shows you how to **develop freely** while keeping production builds protected.

---

## 🎯 The Problem (Solved!)

You asked a great question:
> "Does that mean I have to make changes so that I can deploy and test like I have been doing in the past, for developing new features?"

**Answer: NO!** You can develop exactly like before. License checks are **automatically bypassed** in development mode.

---

## ✅ How It Works

There's a simple switch in `python/core/dev_config.py`:

```python
# Set to True during development (no license required)
# Set to False when building for production (license required)
DEVELOPMENT_MODE = True
```

**That's it!** One line controls everything.

---

## 🔧 Development Mode (Default)

When `DEVELOPMENT_MODE = True`:

### **What Happens:**
- ✅ **No license required** - app starts immediately
- ✅ **All features unlocked** - simulates Enterprise tier
- ✅ **No activation dialogs** - smooth development experience
- ✅ **Console message** - reminds you it's dev mode
- ✅ **Full access** - AI analysis, unlimited pairs, everything

### **Console Output:**
```
============================================================
🔧 DEVELOPMENT MODE - License checks bypassed
============================================================
```

### **You Can:**
- Run `python main.py` normally
- Test all features
- Debug without interruption
- Add new features freely
- Never see license dialogs

---

## 🔐 Production Mode

When `DEVELOPMENT_MODE = False`:

### **What Happens:**
- 🔒 **License required** - activation dialog on startup
- 🔒 **Feature restrictions** - based on tier (trial/basic/pro/enterprise)
- 🔒 **Time limits** - enforces expiry dates
- 🔒 **Hardware binding** - locks to specific machine
- 🔒 **Full protection** - all security layers active

### **Perfect For:**
- Building executables for customers
- Testing production behavior
- Verifying license enforcement
- Final QA before release

---

## 🚀 Your Development Workflow

### **Step 1: Develop Freely (Current State)**

**File:** `python/core/dev_config.py`
```python
DEVELOPMENT_MODE = True  # ← This is the default
```

**Just run:**
```bash
python main.py
```

**Expected:**
```
============================================================
🔧 DEVELOPMENT MODE - License checks bypassed
============================================================
[Your application starts normally]
```

**You can:**
- ✅ Add new features
- ✅ Test AI analysis
- ✅ Use all premium features
- ✅ Debug without license hassles
- ✅ Work exactly like you did before

---

### **Step 2: Test Production Mode (Optional)**

Want to test how customers will experience the license system?

**Change one line in `python/core/dev_config.py`:**
```python
DEVELOPMENT_MODE = False  # ← Test production behavior
```

**Run again:**
```bash
python main.py
```

**Expected:**
- License activation dialog appears
- You must enter a valid license key
- App won't start without license

**Test it:**
1. Generate a trial key: `python python/core/license_manager.py`
2. Activate the key in the dialog
3. App starts with trial restrictions (3 pairs max)

**When done testing, switch back:**
```python
DEVELOPMENT_MODE = True  # ← Back to dev mode
```

---

### **Step 3: Build for Customer**

Ready to send to a customer?

**1. Switch to production mode:**
```python
# python/core/dev_config.py
DEVELOPMENT_MODE = False  # ← Production build
```

**2. Build executable:**
```bash
pyinstaller --onefile --windowed --name "TradingApp" main.py
```

**3. Test the executable:**
```bash
./dist/TradingApp  # Should require license activation
```

**4. Generate license key:**
```bash
python python/core/license_manager.py
# Generate trial or professional key
```

**5. Send to customer:**
- `dist/TradingApp.exe`
- License key via email

**6. Switch back to dev mode:**
```python
# python/core/dev_config.py
DEVELOPMENT_MODE = True  # ← Back to development
```

---

## 🎛️ Alternative: Environment Variable

Don't want to edit the file? Use an environment variable instead.

### **On Linux/Mac:**

**Development (default):**
```bash
export TRADING_APP_DEV_MODE=1
python main.py  # Runs in dev mode
```

**Production:**
```bash
unset TRADING_APP_DEV_MODE
python main.py  # Requires license
```

### **On Windows:**

**Development:**
```cmd
set TRADING_APP_DEV_MODE=1
python main.py
```

**Production:**
```cmd
set TRADING_APP_DEV_MODE=
python main.py
```

### **Add to your shell profile:**

**Linux/Mac (`~/.bashrc` or `~/.zshrc`):**
```bash
export TRADING_APP_DEV_MODE=1
```

Now dev mode is **always on** when you're developing!

---

## 📋 Quick Reference

### **How to check current mode:**

**In code:**
```python
from core.dev_config import is_dev_mode, get_mode_label

if is_dev_mode():
    print("Development mode active")
else:
    print("Production mode active")

print(get_mode_label())  # "🔧 DEVELOPMENT MODE" or "🔐 PRODUCTION MODE"
```

**In console:**
```bash
python -c "from python.core.dev_config import is_dev_mode; print('Dev Mode:', is_dev_mode())"
```

---

## 🧪 Testing Scenarios

### **Scenario 1: Testing New AI Feature**

**Dev Mode (DEVELOPMENT_MODE = True):**
```python
@require_license('ai_analysis')
def new_ai_feature():
    # This works immediately, no license needed
    return "AI prediction"
```

Run and test → Works instantly → No license dialog

---

### **Scenario 2: Testing Trial Limits**

**Production Mode (DEVELOPMENT_MODE = False):**

1. Switch to production mode
2. Generate trial key (3 pairs max)
3. Activate key
4. Try adding 10 pairs
5. Should be limited to 3
6. Verify upgrade prompt works

Switch back to dev mode for continued development.

---

### **Scenario 3: Testing License Expiry**

**Production Mode with Expired Key:**

1. Switch to production mode
2. Generate key with past expiry date (or wait for trial to expire)
3. Try to launch app
4. Should show "License Expired" dialog
5. Test renewal workflow

---

## ⚠️ Important Reminders

### **1. Always Check Before Building for Customers**

Before running `pyinstaller`, verify:
```bash
grep "DEVELOPMENT_MODE = False" python/core/dev_config.py
```

If it returns nothing, **DON'T BUILD YET!** Switch to production mode first.

---

### **2. Git Ignore dev_config.py (Optional)**

If working in a team, add to `.gitignore`:
```
python/core/dev_config.py
```

Each developer can have their own setting without conflicts.

---

### **3. Automated Build Script**

Create `build_production.sh`:
```bash
#!/bin/bash
# Ensure production mode
sed -i 's/DEVELOPMENT_MODE = True/DEVELOPMENT_MODE = False/g' python/core/dev_config.py

# Build
pyinstaller --onefile --windowed --name "TradingApp" main.py

# Restore dev mode
sed -i 's/DEVELOPMENT_MODE = False/DEVELOPMENT_MODE = True/g' python/core/dev_config.py

echo "✓ Production build complete: dist/TradingApp"
echo "✓ Dev mode restored"
```

Run: `./build_production.sh`

---

## 🎓 FAQ

### **Q: I keep seeing license dialogs during development. Why?**
**A:** Check `python/core/dev_config.py` - make sure `DEVELOPMENT_MODE = True`

---

### **Q: Will dev mode be included in production builds?**
**A:** Only if you forget to switch it off. Always set `DEVELOPMENT_MODE = False` before building with PyInstaller.

---

### **Q: Can customers enable dev mode?**
**A:** No. Even if they somehow change the file, PyArmor obfuscation will encrypt it. Plus, executables are compiled, so there's no Python file to edit.

---

### **Q: Does dev mode affect performance?**
**A:** No performance impact. It's just an `if` statement at startup.

---

### **Q: Can I have different dev modes for different features?**
**A:** Yes! Modify `dev_config.py`:

```python
DEVELOPMENT_MODE = True
SKIP_AI_LICENSE = True  # Test AI with different rules
SKIP_ALERT_LICENSE = True
```

Then in your code:
```python
from core.dev_config import SKIP_AI_LICENSE

if not SKIP_AI_LICENSE:
    # Check license for AI
    ...
```

---

### **Q: What if I want to test with a real license in dev mode?**
**A:** Two options:

**Option 1: Temporarily disable dev mode**
```python
DEVELOPMENT_MODE = False
```

**Option 2: Force license check in code**
```python
from core.license_manager import license_manager

# Explicitly validate even in dev mode
valid, msg, info = license_manager.validate_license()
# (But bypass will still happen unless you modify the manager)
```

---

## 🔍 Behind the Scenes

### **How Dev Mode Works:**

**1. In `license_manager.py`:**
```python
def validate_license(self):
    # Check if dev mode first
    if is_dev_mode():
        # Return fake "enterprise" license
        return True, "Dev mode", {'tier': 'enterprise', 'features': ['all']}

    # Normal validation continues...
```

**2. In `license_dialog.py`:**
```python
def check_license_on_startup():
    # Bypass entire dialog in dev mode
    if is_dev_mode():
        print("🔧 Development mode active")
        return True

    # Normal license check...
```

**3. Decorator protection:**
```python
@require_license('ai_analysis')
def ai_feature():
    # Decorator calls validate_license()
    # Which returns True in dev mode
    # So this function works without license
    ...
```

**Everything flows through `validate_license()`, which respects dev mode.**

---

## ✅ Summary

### **For Daily Development:**
```python
# python/core/dev_config.py
DEVELOPMENT_MODE = True  # ← Leave this as-is
```

**Just code normally!** No license dialogs, no restrictions, full feature access.

---

### **Before Sending to Customer:**
```python
# python/core/dev_config.py
DEVELOPMENT_MODE = False  # ← Change this line
```

Then:
1. Build executable
2. Test it requires license
3. Generate customer's license key
4. Send both to customer
5. **Switch back to `True` for continued development**

---

### **Your Workflow (Updated):**

**BEFORE (without licensing):**
```bash
python main.py  # Works
# Add features
python main.py  # Still works
```

**NOW (with licensing):**
```bash
python main.py  # Works (dev mode)
# Add features
python main.py  # Still works (dev mode)

# When deploying:
# 1. Switch DEVELOPMENT_MODE = False
# 2. Build executable
# 3. Switch back DEVELOPMENT_MODE = True
```

**You're adding ONE step (switching a flag) only when deploying to customers.**

**Your daily development is completely unchanged.** ✅

---

## 🎉 You're All Set!

**Current state:**
- ✅ Dev mode is ON by default
- ✅ You can develop freely
- ✅ No license restrictions during dev
- ✅ One-line switch for production builds
- ✅ Zero impact on your workflow

**Continue coding exactly as you were before!** 🚀

The license system only activates when you build for customers.

---

*Questions? Check `DEPLOYMENT_GUIDE.md` for full documentation.*
