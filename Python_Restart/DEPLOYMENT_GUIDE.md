# 🔐 Deployment & License Protection Guide
## How to Sell Your Trading Application Securely

This guide shows you how to protect your code and deploy your application commercially without customers being able to copy it.

---

## 🎯 Protection Layers Implemented

Your application now has **5 layers of protection**:

### 1. **License Key System** ✓
- Customers must activate with a unique license key
- Each license is cryptographically signed
- Prevents unauthorized use

### 2. **Hardware Binding** ✓
- License is locked to customer's specific machine
- Uses hardware ID (MAC + hostname + processor)
- **Can't copy to another computer**

### 3. **Time-Based Expiry** ✓
- Trial: 7 days
- Basic: 30 days (monthly subscription)
- Professional: 365 days (yearly)
- Enterprise: Lifetime
- Automatically stops working after expiry

### 4. **Feature Gating** ✓
- Different license tiers unlock different features
- Trial: Basic scanner only
- Professional: AI analysis + alerts
- Enterprise: All features

### 5. **Code Obfuscation** (You need to apply)
- Makes Python code unreadable
- Prevents reverse engineering
- We'll show you how below

---

## 📋 Step-by-Step Deployment Process

### **STEP 1: Change Master Secret (CRITICAL!)**

Before deploying, you MUST change the master secret in `core/license_manager.py`:

```python
# Line 37 - CHANGE THIS:
_MASTER_SECRET = "YOUR_MASTER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_12345"

# TO SOMETHING LIKE:
_MASTER_SECRET = "kJ8mP2nQ9vR4tW7xZ1aB5cD8eF3gH6jK"
```

**Generate a random secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

⚠️ **NEVER share this secret with anyone!** This is your master key.

---

### **STEP 2: Integrate License Check into Main Application**

Add license validation to your main window. Edit `gui/enhanced_main_window.py`:

```python
# Add at the top:
from widgets.license_dialog import check_license_on_startup, LicenseDialog
from core.license_manager import license_manager

# In EnhancedMainWindow.__init__(), add after super().__init__():
def __init__(self):
    super().__init__()

    # CHECK LICENSE ON STARTUP
    if not check_license_on_startup():
        sys.exit(0)  # Exit if no valid license

    # Rest of your initialization...
    self.init_ui()
```

Add a menu option to view license:

```python
# In your menu bar creation code:
help_menu = self.menuBar().addMenu("Help")

license_action = help_menu.addAction("License Info")
license_action.triggered.connect(self.show_license_dialog)

# Add this method:
def show_license_dialog(self):
    """Show license information dialog"""
    dialog = LicenseDialog(self)
    dialog.exec()
```

---

### **STEP 3: Add Feature Protection to Specific Functions**

Protect premium features with the `@require_license()` decorator:

**Example 1: Protect AI Analysis**

In `core/market_analyzer.py`:

```python
from core.license_manager import require_license

class MarketAnalyzer:

    @require_license('ai_analysis')
    def get_ai_prediction(self, symbol, timeframe):
        """AI predictions only for Professional+ licenses"""
        # Your AI code here
        pass
```

**Example 2: Protect Symbol Scanning**

In `widgets/opportunity_scanner_widget.py`:

```python
from core.license_manager import license_manager

def update_opportunities(self, opportunities: List[Dict]):
    """Update opportunity cards with license limits"""

    # Get license info
    info = license_manager.get_license_info()
    max_pairs = info.get('max_pairs', 3)

    # Limit opportunities based on license
    opportunities = opportunities[:max_pairs]

    # Rest of your code...
```

**Example 3: Protect Alert System**

```python
from core.license_manager import require_license

@require_license('alerts')
def send_trading_alert(self, message):
    """Alerts only for Professional+ licenses"""
    if not license_manager.check_feature_access('alerts'):
        print("⚠️ Alerts require Professional license")
        return

    # Send alert code here
    pass
```

---

### **STEP 4: Generate License Keys for Customers**

Run the license generator tool:

```bash
cd Python_Restart/python
python core/license_manager.py
```

**Interactive Menu:**
```
1. Generate License Key
2. Test License Activation
3. Check Current License

Choice: 1
```

**Example Session:**
```
Enter tier (trial/basic/professional/enterprise): professional
Enter customer name: John Smith Trading LLC

LICENSE KEY GENERATED
══════════════════════════════════════════════════════════
Customer: John Smith Trading LLC
Tier: PROFESSIONAL

License Key:
eyJ0aWVyIjogInByb2Zlc3Npb25hbCIsICJjdXN0b21lciI6ICJKb2huIFNtaXRoIFRyYWRpbmcgTExDIiwgImlzc3VlZCI6ICIyMDI2LTAxLTE1VDA4OjMwOjAwIiwgImV4cGlyeSI6ICIyMDI3LTAxLTE1VDA4OjMwOjAwIiwgImZlYXR1cmVzIjogWyJiYXNpY19zY2FubmVyIiwgImRhc2hib2FyZCIsICJ3eWNrb2ZmX2FuYWx5c2lzIiwgImFpX2FuYWx5c2lzIiwgImFsZXJ0cyJdLCAibWF4X3BhaXJzIjogNTAsICJhaV9hbmFseXNpcyI6IHRydWV9fDEyMzRhYmNkZWY=

══════════════════════════════════════════════════════════
Give this key to the customer for activation.
```

**Send this license key to your customer via email.**

---

### **STEP 5: Customer Activation Process**

Your customer will:

1. Launch the application
2. See "License Activation" dialog (forced on first run)
3. Paste the license key you sent them
4. Click "Activate License"
5. Application validates and activates (bound to their machine)

**Customer can check license info:**
- Menu → Help → License Info

---

### **STEP 6: Code Obfuscation (Hide Source Code)**

Python code is readable by default. We need to **obfuscate** it to prevent customers from reading/copying your algorithms.

#### **Option A: PyArmor (Recommended - Commercial)**

**Install:**
```bash
pip install pyarmor
```

**Obfuscate your code:**
```bash
cd Python_Restart/python

# Obfuscate all Python files
pyarmor gen --recursive --output dist/obfuscated .
```

**What this does:**
- Converts `.py` files to encrypted `.pyx` files
- Makes code completely unreadable
- Still runs normally
- Very hard to reverse engineer

**Commercial license required** for selling ($99/year): https://pyarmor.dashingsoft.com/

---

#### **Option B: Nuitka (Free - Compiles to Binary)**

**Install:**
```bash
pip install nuitka
```

**Compile to binary:**
```bash
python -m nuitka --standalone --onefile --follow-imports main.py
```

**What this does:**
- Converts Python to C code
- Compiles to native binary (.exe on Windows)
- No Python code visible at all
- Harder to reverse engineer than PyArmor
- Free and open source

**Downside:** Larger file size, slower compilation

---

#### **Option C: PyInstaller + PyArmor (Best Combo)**

Combine both for maximum protection:

1. **First obfuscate with PyArmor:**
```bash
pyarmor gen --recursive --output dist/obfuscated .
```

2. **Then package with PyInstaller:**
```bash
cd dist/obfuscated
pyinstaller --onefile --windowed --name "TradingApp" main.py
```

**Result:** Single `.exe` file with obfuscated code inside.

---

### **STEP 7: Create Distributable Package**

#### **For Windows:**

```bash
# Install PyInstaller
pip install pyinstaller

# Create spec file (first time only)
pyi-makespec --onefile --windowed --name "TradingApplication" main.py

# Edit TradingApplication.spec to include data files:
datas = [
    ('core/*.py', 'core'),
    ('widgets/*.py', 'widgets'),
    ('gui/*.py', 'gui'),
    # Add any other resource files
]

# Build the executable
pyinstaller TradingApplication.spec
```

**Output:** `dist/TradingApplication.exe`

---

#### **For Mac/Linux:**

Same process, but output will be:
- Mac: `TradingApplication.app`
- Linux: `TradingApplication` (binary)

---

### **STEP 8: Create Installer (Optional but Professional)**

#### **Windows - Inno Setup**

1. Download Inno Setup: https://jrsoftware.org/isdl.php
2. Create script `installer.iss`:

```ini
[Setup]
AppName=Trading Application Pro
AppVersion=1.0
DefaultDirName={pf}\TradingApp
DefaultGroupName=Trading Application
OutputDir=output
OutputBaseFilename=TradingAppSetup

[Files]
Source: "dist\TradingApplication.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Trading Application"; Filename: "{app}\TradingApplication.exe"
Name: "{commondesktop}\Trading Application"; Filename: "{app}\TradingApplication.exe"
```

3. Compile with Inno Setup
4. **Output:** `TradingAppSetup.exe` (professional installer)

---

## 🛡️ Security Best Practices

### ✅ **DO:**

1. **Change the master secret** before ANY deployment
2. **Keep the master secret safe** (never share, never commit to git)
3. **Use PyArmor or Nuitka** to obfuscate code
4. **Generate unique licenses** for each customer
5. **Keep a customer database** with license keys and machine IDs
6. **Test activation** on a clean machine before sending
7. **Set appropriate expiry dates** (trials = 7 days, subscriptions = 30/365 days)
8. **Version your releases** (track which customer has which version)

---

### ❌ **DON'T:**

1. **Don't distribute raw `.py` files** - always obfuscate or compile
2. **Don't reuse license keys** - one customer = one unique key
3. **Don't disable license checks** in production builds
4. **Don't store master secret in git** - keep it offline
5. **Don't forget to test** on customer's OS (Windows/Mac/Linux)
6. **Don't make license files easy to find** (they're hidden by design)
7. **Don't give lifetime licenses** unless paid significantly more

---

## 💰 Pricing Strategy Recommendations

Based on your feature tiers:

### **Trial (7 Days) - FREE**
- Limited to 3 currency pairs
- Basic scanner only
- No AI analysis
- **Purpose:** Let them experience the quality

### **Basic ($49/month)**
- 10 currency pairs
- Wyckoff analysis
- No AI predictions
- **Target:** Beginner traders

### **Professional ($149/month or $1,499/year)**
- 50 currency pairs
- Full Wyckoff + AI analysis
- Alerts and notifications
- **Target:** Serious traders (BEST VALUE)
- **Discount:** $291 saved on yearly

### **Enterprise ($4,999 - Lifetime)**
- Unlimited pairs
- All features forever
- Priority support
- Custom indicators
- **Target:** Professional firms, prop traders

---

## 🔄 Subscription & Renewal Workflow

### **Month 1 (Trial):**
1. Customer downloads application
2. Sees activation dialog
3. You send them 7-day trial key
4. They test the application

### **Month 2 (Conversion):**
1. Trial expires
2. Application shows "License Expired" dialog
3. Customer contacts you to purchase
4. You generate 30-day or 365-day key
5. They activate and continue using

### **Renewal Process:**
1. 7 days before expiry, show warning dialog
2. Customer contacts you
3. Generate new key (extend by 30/365 days)
4. Customer activates new key
5. No interruption in service

---

## 📊 Customer Management

### **Track These Details:**

Create a spreadsheet:

| Customer Name | Email | License Key | Machine ID | Tier | Issued | Expires | Renewed |
|--------------|-------|------------|-----------|------|---------|---------|---------|
| John Smith | john@email.com | eyJ0aWVy... | a1b2c3d4... | Pro | 2026-01-15 | 2027-01-15 | No |
| Jane Doe | jane@email.com | eyJ0YWVy... | x9y8z7w6... | Basic | 2026-01-10 | 2026-02-10 | Yes |

**Why Important:**
- Track renewals and revenue
- Handle support requests (need Machine ID)
- Prevent piracy (if same key used on multiple machines)
- Marketing (follow up with trial users)

---

## 🆘 Handling Common Customer Issues

### **Issue 1: "License won't activate"**

**Causes:**
- Wrong license key (typo)
- License already activated on different machine
- License expired

**Solution:**
1. Ask for their Machine ID (shown in dialog)
2. Check your records
3. Generate new key if needed

---

### **Issue 2: "I got a new computer"**

**Problem:** License is hardware-locked to old machine

**Solution:**
1. Revoke old license (if they can access old machine)
2. Generate new key with same expiry date
3. Activate on new machine

---

### **Issue 3: "Can I use on multiple computers?"**

**Answer:** No, one license = one machine. Offer:
- Multi-seat licenses at discount (e.g., 3 licenses for 2.5x price)
- Or separate licenses for each machine

---

### **Issue 4: "Application says license expired but I just renewed"**

**Cause:** They didn't activate the new key

**Solution:**
1. Application still has old expired license
2. They need to open license dialog
3. Enter new key you sent
4. Click activate

---

## 🔒 Additional Security Measures (Advanced)

### **Online License Validation (Optional)**

For extra security, implement server-based validation:

1. **Setup a license server** (Flask/FastAPI)
2. **Application checks license online** every 7 days
3. **Revoke licenses remotely** if customer refunds/chargebacks

**Pros:**
- Remote revocation
- Detect key sharing
- Real-time analytics

**Cons:**
- Requires server
- Application needs internet
- More complex

We can implement this if needed (not included in current system).

---

### **Code Signing (Recommended)**

Sign your executable to prevent "Unknown Publisher" warnings:

**Windows:**
- Get code signing certificate ($50-200/year)
- Sign with SignTool: `signtool sign /f cert.pfx /p password TradingApp.exe`

**Mac:**
- Get Apple Developer account ($99/year)
- Sign with codesign and notarize

**Why:** Customers trust signed applications more.

---

## 📦 Final Deployment Checklist

Before sending to customers:

- [ ] Changed master secret from default
- [ ] Integrated license checks in main window
- [ ] Protected premium features with decorators
- [ ] Tested license generation
- [ ] Tested activation on clean machine
- [ ] Obfuscated code (PyArmor or Nuitka)
- [ ] Built executable with PyInstaller
- [ ] Created installer (optional)
- [ ] Code signed executable (optional)
- [ ] Tested on customer's OS
- [ ] Prepared customer database spreadsheet
- [ ] Written customer setup instructions
- [ ] Set up payment method (Stripe/PayPal)
- [ ] Created refund policy
- [ ] Prepared support email/channel

---

## 🎯 Quick Start Deployment (Minimum)

If you want to deploy **TODAY**, minimum steps:

### **1. Change Master Secret (5 min)**
```python
# core/license_manager.py line 37
_MASTER_SECRET = "your-random-secret-here-32-chars"
```

### **2. Add License Check to Main (5 min)**
```python
# gui/enhanced_main_window.py
from widgets.license_dialog import check_license_on_startup
if not check_license_on_startup():
    sys.exit(0)
```

### **3. Generate License Key (2 min)**
```bash
python core/license_manager.py
# Choose option 1, generate key
```

### **4. Package Application (10 min)**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### **5. Send to Customer (2 min)**
- Email them `dist/main.exe`
- Email them the license key
- Done!

**Total: 24 minutes to first customer**

---

## 💡 Next Steps After First Sale

1. **Collect feedback** - improve based on user experience
2. **Add telemetry** (optional) - track feature usage
3. **Build marketing site** - professional landing page
4. **Create video tutorials** - helps with sales
5. **Implement online validation** - extra security
6. **Add auto-update system** - push new features
7. **Create affiliate program** - let users refer others

---

## 📞 Support Resources

**License System Issues:**
- Check `~/.trading_app/.license` (hidden file)
- Delete to force re-activation
- Machine ID changes if hardware changes

**Build Issues:**
- PyInstaller docs: https://pyinstaller.org
- PyArmor docs: https://pyarmor.readingdocs.io
- Nuitka docs: https://nuitka.net

**Payment Processing:**
- Stripe (recommended): https://stripe.com
- Gumroad (easiest): https://gumroad.com
- LemonSqueezy: https://lemonsqueezy.com

---

## ✅ Summary

You now have:

1. ✅ **License key system** - customers need valid key
2. ✅ **Hardware locking** - can't copy to other machines
3. ✅ **Time expiry** - auto-stops after period
4. ✅ **Feature gating** - different tiers unlock features
5. ✅ **Obfuscation ready** - can hide source code
6. ✅ **Professional deployment** - ready to sell

**Your code is now PROTECTED and MONETIZABLE.** 🚀

---

*Last Updated: January 2026*
*Version: 1.0*
