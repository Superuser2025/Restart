#!/usr/bin/env python3
"""
AppleTrader Pro - System Health Validator
Checks all components of the trading system for proper configuration
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import platform

class SystemValidator:
    """Validates the entire AppleTrader trading system"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []

    def log_pass(self, message):
        """Log a passed check"""
        self.passed.append(message)
        print(f"✓ {message}")

    def log_warning(self, message):
        """Log a warning"""
        self.warnings.append(message)
        print(f"⚠ WARNING: {message}")

    def log_fail(self, message):
        """Log a failure"""
        self.issues.append(message)
        print(f"✗ FAIL: {message}")

    def check_python_dependencies(self):
        """Check if required Python packages are installed"""
        print("\n" + "="*60)
        print("1. CHECKING PYTHON DEPENDENCIES")
        print("="*60)

        required = [
            'PyQt6',
            'numpy',
            'pandas',
            'matplotlib',
            'sklearn',
            'xgboost'
        ]

        for package in required:
            try:
                __import__(package)
                self.log_pass(f"{package} is installed")
            except ImportError:
                self.log_fail(f"{package} is NOT installed - run: pip install {package}")

    def check_ml_data_directory(self):
        """Check if ML_Data directory exists and has correct structure"""
        print("\n" + "="*60)
        print("2. CHECKING ML_DATA DIRECTORY")
        print("="*60)

        # Check common ML_Data locations
        possible_paths = [
            Path.home() / "ML_Data",
            Path("/home/user/Restart/ML_Data"),
            Path("ML_Data"),
            Path("../ML_Data")
        ]

        ml_dir_found = False
        for path in possible_paths:
            if path.exists():
                self.log_pass(f"ML_Data directory found at: {path}")
                ml_dir_found = True

                # Check for required subdirectories
                models_dir = path / "models"
                if models_dir.exists():
                    self.log_pass(f"Models directory exists: {models_dir}")
                else:
                    self.log_warning(f"Models directory missing: {models_dir}")

                # Check for data files
                files_to_check = [
                    "current_features.json",
                    "prediction.json",
                    "training_data.csv"
                ]

                for filename in files_to_check:
                    filepath = path / filename
                    if filepath.exists():
                        # Check file age
                        mtime = filepath.stat().st_mtime
                        age_seconds = datetime.now().timestamp() - mtime
                        age_minutes = age_seconds / 60

                        if age_minutes < 1:
                            self.log_pass(f"{filename} exists (updated {age_seconds:.0f}s ago)")
                        elif age_minutes < 60:
                            self.log_warning(f"{filename} exists but old ({age_minutes:.0f} min ago)")
                        else:
                            self.log_warning(f"{filename} exists but VERY old ({age_minutes/60:.1f} hours ago)")

                        # Try to read and validate JSON
                        if filename.endswith('.json'):
                            try:
                                with open(filepath, 'r') as f:
                                    data = json.load(f)
                                    self.log_pass(f"{filename} is valid JSON with {len(data)} fields")
                            except json.JSONDecodeError:
                                self.log_fail(f"{filename} is NOT valid JSON!")
                    else:
                        self.log_warning(f"{filename} not found at {path}")

                break

        if not ml_dir_found:
            self.log_fail("ML_Data directory NOT FOUND in any standard location!")
            self.log_fail("Create it with: mkdir -p ~/ML_Data/models")

    def check_mt5_data_directory(self):
        """Check if MT5 data directory exists"""
        print("\n" + "="*60)
        print("3. CHECKING MT5 DATA DIRECTORY")
        print("="*60)

        # MT5 typical paths
        if platform.system() == "Windows":
            mt5_paths = [
                Path(os.environ.get('APPDATA', '')) / "MetaTrader 5" / "MQL5" / "Files",
                Path("C:/Program Files/MetaTrader 5/MQL5/Files"),
            ]
        else:
            # Linux/Wine paths
            mt5_paths = [
                Path.home() / ".wine" / "drive_c" / "Program Files" / "MetaTrader 5" / "MQL5" / "Files",
                Path.home() / ".wine" / "drive_c" / "users" / os.environ.get('USER', 'user') / "AppData" / "Roaming" / "MetaTrader 5" / "MQL5" / "Files",
            ]

        mt5_found = False
        for path in mt5_paths:
            if path.exists():
                self.log_pass(f"MT5 Files directory found: {path}")
                mt5_found = True

                # Check for AppleTrader subdirectory
                appletrader_dir = path / "AppleTrader"
                if appletrader_dir.exists():
                    self.log_pass(f"AppleTrader directory exists: {appletrader_dir}")

                    # Check for market_data.json
                    market_data = appletrader_dir / "market_data.json"
                    if market_data.exists():
                        mtime = market_data.stat().st_mtime
                        age_seconds = datetime.now().timestamp() - mtime

                        if age_seconds < 30:
                            self.log_pass(f"market_data.json is FRESH ({age_seconds:.0f}s old) - EA IS RUNNING!")
                        else:
                            self.log_warning(f"market_data.json is STALE ({age_seconds/60:.1f} min old) - EA may not be running")

                        # Validate content
                        try:
                            with open(market_data, 'r') as f:
                                data = json.load(f)
                                self.log_pass(f"market_data.json is valid JSON")

                                # Check critical fields
                                if 'auto_trading' in data:
                                    if data['auto_trading']:
                                        self.log_pass("Auto trading is ENABLED in EA")
                                    else:
                                        self.log_warning("Auto trading is DISABLED - EA in indicator mode only")

                                if 'ml_enabled' in data:
                                    if data['ml_enabled']:
                                        self.log_pass("ML is ENABLED in EA")
                                    else:
                                        self.log_warning("ML is DISABLED in EA")

                                if 'confluence' in data:
                                    confluence = data['confluence']
                                    if confluence >= 70:
                                        self.log_pass(f"Confluence score is {confluence}% (sufficient for trading)")
                                    else:
                                        self.log_warning(f"Confluence score is {confluence}% (need 70%+ to trade)")

                        except json.JSONDecodeError:
                            self.log_fail("market_data.json is CORRUPT!")
                    else:
                        self.log_fail(f"market_data.json NOT FOUND - EA not exporting data!")
                else:
                    self.log_fail(f"AppleTrader directory not found - EA never ran or wrong path")

                break

        if not mt5_found:
            self.log_warning("MT5 Files directory not found - is MT5 installed?")

    def check_python_gui_files(self):
        """Check if Python GUI files exist"""
        print("\n" + "="*60)
        print("4. CHECKING PYTHON GUI FILES")
        print("="*60)

        base_dir = Path(__file__).parent

        critical_files = [
            "main_enhanced.py",
            "gui/enhanced_main_window.py",
            "core/ml_integration.py",
            "core/mt5_connector.py",
            "core/data_manager.py"
        ]

        for filepath in critical_files:
            full_path = base_dir / filepath
            if full_path.exists():
                self.log_pass(f"{filepath} exists")
            else:
                self.log_fail(f"{filepath} MISSING!")

    def check_ea_file(self):
        """Check if EA file exists"""
        print("\n" + "="*60)
        print("5. CHECKING EA FILE")
        print("="*60)

        base_dir = Path(__file__).parent.parent
        ea_path = base_dir / "AppleTrader.mq5"

        if ea_path.exists():
            self.log_pass(f"AppleTrader.mq5 found at {ea_path}")

            # Read EA to check critical settings
            try:
                with open(ea_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    # Check for problematic defaults
                    if 'EnableAutoTrading = false' in content:
                        self.log_warning("EA defaults to auto trading OFF - you must enable it in MT5")
                    elif 'EnableAutoTrading = true' in content:
                        self.log_pass("EA defaults to auto trading ON")

                    if 'RequireConfirmation = true' in content:
                        self.log_warning("EA requires manual confirmation for each trade")
                    elif 'RequireConfirmation = false' in content:
                        self.log_pass("EA will trade automatically without confirmation")

            except Exception as e:
                self.log_warning(f"Could not read EA file: {e}")
        else:
            self.log_fail(f"AppleTrader.mq5 NOT FOUND at {ea_path}")

    def check_ml_service(self):
        """Check if ML service is available"""
        print("\n" + "="*60)
        print("6. CHECKING ML SERVICE")
        print("="*60)

        base_dir = Path(__file__).parent.parent

        ml_service_paths = [
            base_dir / "ML_Modules" / "ml_training_service.py",
            base_dir / "python" / "core" / "ml_integration.py"
        ]

        ml_found = False
        for path in ml_service_paths:
            if path.exists():
                self.log_pass(f"ML service file found: {path}")
                ml_found = True

        if not ml_found:
            self.log_warning("ML service files not found - ML features unavailable")

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)

        print(f"\n✓ Passed: {len(self.passed)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        print(f"✗ Failed: {len(self.issues)}")

        if self.issues:
            print("\n" + "="*60)
            print("CRITICAL ISSUES - MUST FIX:")
            print("="*60)
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")

        if self.warnings:
            print("\n" + "="*60)
            print("WARNINGS - SHOULD FIX:")
            print("="*60)
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")

        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)

        if len(self.issues) > 0:
            print("❌ SYSTEM NOT READY FOR TRADING")
            print("   Fix critical issues above before trading!")
        elif len(self.warnings) > 3:
            print("⚠️  SYSTEM HAS ISSUES")
            print("   Review warnings - system may work but not optimally")
        else:
            print("✅ SYSTEM LOOKS GOOD")
            print("   Most components are working - ready for testing on DEMO!")

        print("\n" + "="*60)

    def run_all_checks(self):
        """Run all validation checks"""
        print("="*60)
        print("APPLETRADER PRO - SYSTEM VALIDATION")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Platform: {platform.system()}")
        print(f"Python: {sys.version.split()[0]}")

        self.check_python_dependencies()
        self.check_ml_data_directory()
        self.check_mt5_data_directory()
        self.check_python_gui_files()
        self.check_ea_file()
        self.check_ml_service()

        self.print_summary()

        return len(self.issues) == 0


if __name__ == "__main__":
    validator = SystemValidator()
    success = validator.run_all_checks()

    sys.exit(0 if success else 1)
