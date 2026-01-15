# 🚀 Quick Start: License System

## ⏱️ Get Your First Customer in 30 Minutes

This is the **fastest path** from code to paid customer.

---

## Step 1: Install Dependencies (2 minutes)

```bash
cd Python_Restart/python
pip install cryptography
```

That's it! The license system is ready to use.

---

## Step 2: Change Master Secret (1 minute)

**CRITICAL - DO THIS FIRST!**

Open `core/license_manager.py` and find line 37:

```python
_MASTER_SECRET = "YOUR_MASTER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_12345"
```

Change it to something random:

```python
_MASTER_SECRET = "kJ8mP2nQ9vR4tW7xZ1aB5cD8eF3gH6jK"  # Use your own!
```

**Generate a random secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

⚠️ **Save this secret somewhere safe!** You need it to generate licenses.

---

## Step 3: Test License Generation (2 minutes)

```bash
cd Python_Restart/python
python core/license_manager.py
```

Choose option `1` (Generate License Key)

**Example:**
```
Enter tier: trial
Enter customer name: Test User

LICENSE KEY GENERATED
══════════════════════════════════════════════════════════
Customer: Test User
Tier: TRIAL

License Key:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

══════════════════════════════════════════════════════════
```

**Copy this key** - you'll test activation next.

---

## Step 4: Test Activation (2 minutes)

Still in the same terminal:

```bash
python core/license_manager.py
```

Choose option `2` (Test License Activation)

Paste the key you just generated.

**Expected output:**
```
✓ License activated successfully!
Tier: TRIAL
Days remaining: 7
```

Perfect! Your license system works.

---

## Step 5: Integrate into Application (5 minutes)

Open `gui/enhanced_main_window.py` and add at the very top:

```python
from widgets.license_dialog import check_license_on_startup, LicenseDialog
from core.license_manager import license_manager
```

Find the `__init__` method and add **IMMEDIATELY AFTER `super().__init__()`**:

```python
class EnhancedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ADD THIS - License check on startup
        if not check_license_on_startup():
            import sys
            sys.exit(0)

        # Your existing code continues...
        self.init_ui()
```

**Save the file.**

---

## Step 6: Test Application with License (3 minutes)

First, remove any existing license to test activation:

```bash
# Delete license file (hidden)
rm -rf ~/.trading_app/.license  # Linux/Mac
# or
del %USERPROFILE%\.trading_app\.license  # Windows
```

Now run your application:

```bash
python main.py
```

**What happens:**
1. License activation dialog appears (forced)
2. You paste your trial key
3. Click "Activate License"
4. Application launches normally

**Try it now!**

---

## Step 7: Package as Executable (10 minutes)

Install PyInstaller:

```bash
pip install pyinstaller
```

Create executable:

```bash
cd Python_Restart/python
pyinstaller --onefile --windowed --name "TradingApp" main.py
```

Wait for build to complete (5-8 minutes).

**Output:** `dist/TradingApp.exe` (or `.app` on Mac, binary on Linux)

**Test it:**
```bash
cd dist
./TradingApp  # or TradingApp.exe on Windows
```

---

## Step 8: Send to Customer (2 minutes)

**Email Template:**

```
Subject: Your Trading Application Trial

Hi [Customer Name],

Thank you for your interest in Trading Application Pro!

Attached is your 7-day trial version.

Installation:
1. Download TradingApp.exe
2. Run the application
3. When prompted, enter this license key:

[PASTE TRIAL KEY HERE]

4. Click "Activate License"
5. Start trading!

Features included in trial:
- Real-time market analysis
- 3 currency pairs
- Wyckoff pattern detection
- Dashboard overview

To unlock all features (50+ pairs, AI analysis, alerts),
upgrade to Professional for $149/month.

Questions? Reply to this email.

Best regards,
[Your Name]
```

**Attach:** `dist/TradingApp.exe`

**Done!** You just sent your first licensed application. 🎉

---

## Step 9: When Customer Wants to Upgrade (3 minutes)

Customer tried the trial and wants to buy. Great!

**1. Collect Payment** (Stripe, PayPal, etc.)

**2. Generate Professional Key:**

```bash
python core/license_manager.py
```

Choose option `1`:
```
Enter tier: professional
Enter customer name: John Smith
```

**3. Email Customer:**

```
Subject: Your Professional License

Hi John,

Thank you for upgrading to Professional!

Your new license key:

[PASTE PROFESSIONAL KEY]

Instructions:
1. Open Trading Application
2. Menu → Help → License Information
3. Enter the new key above
4. Click "Activate License"

Your Professional features are now unlocked:
✓ 50 currency pairs (was 3)
✓ AI-powered analysis
✓ Real-time alerts
✓ 365 days access

Thank you for your business!

[Your Name]
```

**Customer activates the new key and gets full access instantly.**

---

## License Tier Reference

Quick reference for generating licenses:

| Tier | Command | Duration | Price | Features |
|------|---------|----------|-------|----------|
| **trial** | `tier: trial` | 7 days | FREE | 3 pairs, basic scanner |
| **basic** | `tier: basic` | 30 days | $49/mo | 10 pairs, Wyckoff |
| **professional** | `tier: professional` | 365 days | $149/mo or $1,499/yr | 50 pairs, AI, alerts |
| **enterprise** | `tier: enterprise` | Lifetime | $4,999 | Unlimited everything |

---

## Common Commands

**Generate trial key:**
```bash
python core/license_manager.py
# 1 → trial → [Customer Name]
```

**Generate professional key:**
```bash
python core/license_manager.py
# 1 → professional → [Customer Name]
```

**Check current license:**
```bash
python core/license_manager.py
# 3
```

**Revoke license** (start fresh):
```bash
rm -rf ~/.trading_app/.license
```

**Build executable:**
```bash
pyinstaller --onefile --windowed main.py
```

---

## Customer Management Spreadsheet

Track your customers in a spreadsheet:

| Date | Customer | Email | Tier | Key (last 10 chars) | Machine ID | Expires | Status |
|------|----------|-------|------|-------------------|-----------|---------|--------|
| 2026-01-15 | John Smith | john@email.com | Professional | ...abc123 | a1b2c3d4 | 2027-01-15 | Active |
| 2026-01-14 | Jane Doe | jane@email.com | Trial | ...xyz789 | x9y8z7w6 | 2026-01-21 | Active |

**Important columns:**
- **Machine ID:** For support (customer needs to reinstall)
- **Expires:** Follow up 7 days before for renewal
- **Status:** Active, Expired, Refunded

---

## Troubleshooting

**"License won't activate"**
- Check customer copied entire key (no spaces/line breaks)
- Verify you used correct master secret when generating
- Check key hasn't expired

**"Application won't start without license dialog"**
- Good! That means protection is working
- Generate a key and activate it

**"Customer can't activate on new computer"**
- License is hardware-locked (feature, not bug)
- Generate new key with same expiry date
- Or implement transfer policy (charge small fee)

**"How do I revoke a license?"**
- Delete `~/.trading_app/.license` on customer's machine
- Or implement server-based validation (advanced)

**"Can I change the master secret later?"**
- Technically yes, but all old licenses become invalid
- Only do this if compromised
- Better: Use different secret for each version

---

## Security Checklist

Before sending to ANY customer:

- [ ] Changed master secret from default
- [ ] Tested license generation
- [ ] Tested license activation
- [ ] Tested application with valid license
- [ ] Tested application with expired license
- [ ] Built executable successfully
- [ ] Tested executable on clean machine
- [ ] Application exits if no valid license

---

## Next Level (Optional)

Once you have customers, consider:

### **1. Code Obfuscation** (Protect source code)
```bash
pip install pyarmor
pyarmor gen --recursive --output dist/obfuscated .
# Then package the obfuscated version
```

### **2. Code Signing** (Remove "Unknown Publisher" warning)
- Windows: Get code signing certificate ($99/year)
- Mac: Apple Developer account ($99/year)

### **3. Auto-Update System**
- Check for updates on startup
- Download and install automatically
- Keep customers on latest version

### **4. Online License Validation**
- Validate license against server every 7 days
- Remotely revoke licenses
- Prevent key sharing

### **5. Analytics** (Optional)
- Track which features are used
- Improve based on data
- Identify upsell opportunities

---

## Support Resources

**Payment Processing:**
- [Stripe](https://stripe.com) - Professional, 2.9% + 30¢
- [Gumroad](https://gumroad.com) - Easiest, 10% fee
- [LemonSqueezy](https://lemonsqueezy.com) - Good alternative, 5% + 50¢

**Code Signing:**
- Windows: [DigiCert](https://www.digicert.com/signing/code-signing-certificates)
- Mac: [Apple Developer](https://developer.apple.com)

**Help:**
- License system: See `DEPLOYMENT_GUIDE.md`
- Integration examples: See `LICENSE_INTEGRATION_EXAMPLE.py`
- Full manual: See `TRADING_MANUAL.md`

---

## Summary

You now know how to:

1. ✅ Generate license keys (trial, basic, pro, enterprise)
2. ✅ Integrate license checks into your app
3. ✅ Package as distributable executable
4. ✅ Send to customers with instructions
5. ✅ Handle upgrades and renewals
6. ✅ Track customers in spreadsheet

**Time to first customer: 30 minutes**

**Your application is now a PRODUCT.** 💰

Go get your first sale! 🚀

---

*Questions? Check the full DEPLOYMENT_GUIDE.md for detailed information.*
