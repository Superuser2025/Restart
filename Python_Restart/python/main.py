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

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
