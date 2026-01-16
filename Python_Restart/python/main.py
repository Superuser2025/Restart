"""
AppleTrader Pro - Main Entry Point
Institutional-Grade Trading Dashboard

Features:
- 10 Advanced Trading Improvements
- Real-time MT5 Integration
- AI-Powered Analysis
- Automated Trade Journal
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow

# License system (bypassed in development mode)
from widgets.license_dialog import check_license_on_startup


def main():
    """Main application entry point"""

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AppleTrader Pro")
    app.setOrganizationName("AppleTrader")

    # ===== LICENSE CHECK (BYPASSED IN DEV MODE) =====
    # In development: DEVELOPMENT_MODE = True (default) → no license needed
    # In production: DEVELOPMENT_MODE = False → license required
    if not check_license_on_startup():
        print("\n⚠️  License validation failed. Application will exit.")
        sys.exit(1)
    # ================================================

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
