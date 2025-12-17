"""
AppleTrader Pro - Enhanced Version Entry Point
Institutional Trading Robot v3.0 Features

This version includes:
- Comprehensive institutional filters panel
- Multi-color zone overlays on chart
- Real-time analysis overlay
- Price action commentary
- All original 10 improvements

Run this to see the full EA-style interface!
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.enhanced_main_window import EnhancedMainWindow


def main():
    """Main application entry point for enhanced version"""

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AppleTrader Pro - Enhanced")
    app.setOrganizationName("AppleTrader")

    # FORCE LIVE MODE ON STARTUP (user requested)
    from core.demo_mode_manager import demo_mode_manager
    demo_mode_manager.demo_mode = False  # False = LIVE MODE
    print("\n🔴 FORCING LIVE MODE ON STARTUP 🔴")
    print(f"demo_mode = {demo_mode_manager.demo_mode}")
    print(f"is_demo_mode() = {demo_mode_manager.is_demo()}")
    print(f"is_live_mode() = {demo_mode_manager.is_live()}\n")

    # Create and show enhanced main window
    window = EnhancedMainWindow()
    window.show()

    print("=" * 60)
    print("  AppleTrader Pro - Enhanced Version")
    print("  Institutional Trading Robot v3.0 Features")
    print("=" * 60)
    print("\nNEW FEATURES:")
    print("  ✓ Institutional Filters Panel (Left)")
    print("  ✓ Multi-Color Zone Overlays on Chart")
    print("  ✓ Real-Time Analysis Panel on Chart")
    print("  ✓ Price Action Commentary")
    print("  ✓ Chart Visuals Toggle Controls")
    print("\nCONTROLS:")
    print("  - Toggle filters ON/OFF in left panel")
    print("  - Switch chart visuals at bottom of left panel")
    print("  - View zones and analysis on chart")
    print("=" * 60)

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
