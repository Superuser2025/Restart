"""
LICENSE INTEGRATION EXAMPLE
Copy these code snippets into your application files to enable license protection
"""

# ============================================================================
# EXAMPLE 1: Add to gui/enhanced_main_window.py
# ============================================================================

"""
Add these imports at the top of enhanced_main_window.py:
"""

from widgets.license_dialog import check_license_on_startup, LicenseDialog
from core.license_manager import license_manager


"""
In EnhancedMainWindow.__init__(), add license check BEFORE ui initialization:
"""

class EnhancedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ===== LICENSE CHECK - ADD THIS =====
        if not check_license_on_startup():
            sys.exit(0)  # Exit if no valid license
        # ====================================

        # Your existing code continues here...
        self.setWindowTitle("Trading Application")
        self.init_ui()
        # ... rest of your code


"""
Add a menu item to view/manage license (optional but recommended):
"""

def create_menu_bar(self):
    """Create menu bar with license option"""
    menubar = self.menuBar()

    # Your existing menus...
    file_menu = menubar.addMenu("File")
    # ... file menu items ...

    # Add Help menu with License option
    help_menu = menubar.addMenu("Help")

    license_action = help_menu.addAction("📋 License Information")
    license_action.triggered.connect(self.show_license_dialog)

    manual_action = help_menu.addAction("📖 Trading Manual")
    manual_action.triggered.connect(self.show_manual)

    about_action = help_menu.addAction("ℹ️ About")
    about_action.triggered.connect(self.show_about)

def show_license_dialog(self):
    """Show license management dialog"""
    dialog = LicenseDialog(self)
    dialog.exec()

def show_about(self):
    """Show about dialog with license info"""
    info = license_manager.get_license_info()

    about_text = f"""
    <h2>Trading Application Pro</h2>
    <p>Version: 1.0</p>
    <p>Professional-grade trading analysis and opportunity scanner</p>
    <hr>
    <p><b>License Status:</b> {info['status']}</p>
    <p><b>License Tier:</b> {info['tier']}</p>
    """

    if info['valid']:
        about_text += f"""
        <p><b>Days Remaining:</b> {info['days_remaining']}</p>
        <p><b>Expires:</b> {info['expiry_date']}</p>
        """

    from PyQt6.QtWidgets import QMessageBox
    msg = QMessageBox(self)
    msg.setWindowTitle("About")
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setText(about_text)
    msg.exec()


# ============================================================================
# EXAMPLE 2: Protect AI Analysis Features
# ============================================================================

"""
In core/market_analyzer.py or wherever you have AI features:
"""

from core.license_manager import require_license, license_manager


class MarketAnalyzer:

    # Option A: Use decorator (simplest)
    @require_license('ai_analysis')
    def get_ai_prediction(self, symbol: str, timeframe: str) -> Dict:
        """
        AI predictions - PROFESSIONAL LICENSE REQUIRED
        Decorator automatically blocks if license doesn't have 'ai_analysis'
        """
        # Your AI prediction code here
        prediction = self._run_ml_model(symbol, timeframe)
        return prediction

    # Option B: Manual check (more control)
    def get_enhanced_signals(self, symbol: str) -> List[Dict]:
        """Enhanced signals with manual license check"""

        # Check if AI analysis is allowed
        if not license_manager.check_feature_access('ai_analysis'):
            # Return basic signals for lower tier licenses
            return self._get_basic_signals(symbol)

        # Full AI-powered signals for professional licenses
        return self._get_ai_powered_signals(symbol)


# ============================================================================
# EXAMPLE 3: Limit Features Based on License Tier
# ============================================================================

"""
In widgets/opportunity_scanner_widget.py:
"""

from core.license_manager import license_manager


class OpportunityScannerWidget(QWidget):

    def update_opportunities(self, opportunities: List[Dict]):
        """Update opportunities with license tier limits"""

        # Get license information
        info = license_manager.get_license_info()

        if not info['valid']:
            # No license - show demo mode
            self.show_demo_mode()
            return

        # Limit opportunities based on license tier
        max_pairs = info.get('max_pairs', 3)
        opportunities = opportunities[:max_pairs]

        # Show upgrade message if hitting limit
        if len(opportunities) >= max_pairs and max_pairs < 50:
            self.show_upgrade_banner(
                f"Showing {max_pairs} pairs. Upgrade to Professional for 50+ pairs!"
            )

        # Update display
        self._display_opportunities(opportunities)

    def show_demo_mode(self):
        """Show demo/trial mode banner"""
        banner = QLabel("📋 TRIAL MODE - Activate license to unlock all features")
        banner.setStyleSheet("""
            background-color: #ff9900;
            color: white;
            padding: 10px;
            font-weight: bold;
        """)
        # Add banner to layout


# ============================================================================
# EXAMPLE 4: Dashboard Card with License Status
# ============================================================================

"""
In widgets/dashboard_cards_widget.py:
"""

from core.license_manager import license_manager


class DashboardCardsWidget(QWidget):

    def init_ui(self):
        """Initialize with license status card"""
        layout = QHBoxLayout(self)

        # Your existing cards
        self.account_card = DashboardCard("Account", "💰")
        self.market_card = DashboardCard("Market", "📈")
        # ... etc

        # Add license status card (optional)
        self.license_card = DashboardCard("License", "🔐")
        self.update_license_card()

        layout.addWidget(self.account_card)
        layout.addWidget(self.market_card)
        # ...
        layout.addWidget(self.license_card)

    def update_license_card(self):
        """Update license status card"""
        info = license_manager.get_license_info()

        if info['valid']:
            days = info['days_remaining']
            tier = info['tier']

            self.license_card.set_value(tier)
            self.license_card.set_subtitle(f"{days} days remaining")

            # Change color based on days remaining
            if days < 7:
                self.license_card.set_color("#ff9900")  # Warning orange
            else:
                self.license_card.set_color("#00ff00")  # Good green
        else:
            self.license_card.set_value("INACTIVE")
            self.license_card.set_subtitle("Activate license")
            self.license_card.set_color("#ff0000")  # Red


# ============================================================================
# EXAMPLE 5: Protect Alert/Notification System
# ============================================================================

"""
If you have an alert system:
"""

from core.license_manager import require_license, license_manager


class AlertSystem:

    @require_license('alerts')
    def send_trading_alert(self, message: str, priority: str = "normal"):
        """
        Send trading alert - PROFESSIONAL LICENSE REQUIRED
        """
        # Send email, SMS, push notification, etc.
        self._send_notification(message, priority)

    def maybe_send_alert(self, message: str):
        """Send alert only if license tier supports it"""
        if license_manager.check_feature_access('alerts'):
            self.send_trading_alert(message)
        else:
            # Log to console for lower tiers
            print(f"Alert (upgrade to enable): {message}")


# ============================================================================
# EXAMPLE 6: Watermark for Trial Users
# ============================================================================

"""
Add watermark to charts for trial users:
"""

from core.license_manager import license_manager


class ChartWidget(QWidget):

    def draw_chart(self):
        """Draw chart with trial watermark if needed"""
        # Your chart drawing code
        self._draw_candlesticks()
        self._draw_indicators()

        # Add watermark for trial licenses
        info = license_manager.get_license_info()
        if not info['valid'] or info['tier'] == 'TRIAL':
            self._add_watermark("TRIAL VERSION - trading-app.com")

    def _add_watermark(self, text: str):
        """Add semi-transparent watermark to chart"""
        # Implementation depends on your charting library
        # For matplotlib:
        # plt.text(0.5, 0.5, text, transform=ax.transAxes,
        #          fontsize=40, color='gray', alpha=0.3,
        #          ha='center', va='center', rotation=30)
        pass


# ============================================================================
# EXAMPLE 7: Periodic License Revalidation
# ============================================================================

"""
Recheck license periodically (every hour) to catch expiration:
"""

from PyQt6.QtCore import QTimer
from core.license_manager import license_manager


class EnhancedMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Initial license check
        if not check_license_on_startup():
            sys.exit(0)

        self.init_ui()

        # Setup periodic license revalidation (every 1 hour)
        self.license_check_timer = QTimer(self)
        self.license_check_timer.timeout.connect(self.revalidate_license)
        self.license_check_timer.start(3600000)  # 1 hour in milliseconds

    def revalidate_license(self):
        """Periodically check if license is still valid"""
        valid, message, _ = license_manager.validate_license()

        if not valid:
            # License expired or revoked
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("License Expired")
            msg.setText("Your license has expired.")
            msg.setInformativeText("Please renew your license to continue using the application.")
            msg.exec()

            # Show license dialog
            dialog = LicenseDialog(self, force_activation=True)
            dialog.exec()

            # If still invalid, quit
            valid, _, _ = license_manager.validate_license()
            if not valid:
                QApplication.quit()


# ============================================================================
# EXAMPLE 8: Startup Banner Showing License Info
# ============================================================================

"""
Show license info on startup (non-intrusive):
"""

class EnhancedMainWindow(QMainWindow):

    def show_startup_banner(self):
        """Show license status banner at startup"""
        info = license_manager.get_license_info()

        banner = QLabel()
        banner.setWordWrap(True)

        if info['valid']:
            days = info['days_remaining']
            tier = info['tier']

            if days < 7:
                # Expiring soon - warning
                banner.setText(f"⚠️ Your {tier} license expires in {days} days. Please renew.")
                banner.setStyleSheet("background-color: #ff9900; color: white; padding: 10px;")
            else:
                # All good - subtle info
                banner.setText(f"✓ {tier} License Active - {days} days remaining")
                banner.setStyleSheet("background-color: #2d5a2d; color: white; padding: 5px;")

            # Show banner at top of window
            self.layout().insertWidget(0, banner)

            # Auto-hide after 5 seconds
            QTimer.singleShot(5000, banner.hide)
        else:
            # Invalid license
            banner.setText("❌ No valid license. Click here to activate.")
            banner.setStyleSheet("background-color: #5a2d2d; color: white; padding: 10px;")
            banner.mousePressEvent = lambda e: self.show_license_dialog()
            self.layout().insertWidget(0, banner)


# ============================================================================
# EXAMPLE 9: Feature Access Checks in UI
# ============================================================================

"""
Enable/disable UI elements based on license:
"""

class EnhancedMainWindow(QMainWindow):

    def setup_ui_based_on_license(self):
        """Enable/disable features based on license tier"""
        info = license_manager.get_license_info()

        # AI Analysis button
        if info.get('ai_analysis', False):
            self.ai_analysis_btn.setEnabled(True)
            self.ai_analysis_btn.setToolTip("Get AI-powered analysis")
        else:
            self.ai_analysis_btn.setEnabled(False)
            self.ai_analysis_btn.setToolTip("AI Analysis requires Professional license - Click to upgrade")
            self.ai_analysis_btn.clicked.connect(self.show_upgrade_dialog)

        # Alerts section
        if license_manager.check_feature_access('alerts'):
            self.alerts_section.show()
        else:
            self.alerts_section.hide()

        # Pair limit indicator
        max_pairs = info.get('max_pairs', 3)
        self.pair_limit_label.setText(f"Monitoring {len(self.active_pairs)}/{max_pairs} pairs")

    def show_upgrade_dialog(self):
        """Show upgrade options"""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Upgrade License")
        msg.setText("This feature requires a Professional or Enterprise license.")
        msg.setInformativeText(
            "Professional: $149/month - 50 pairs, AI analysis, alerts\n"
            "Enterprise: $4,999 lifetime - Unlimited everything\n\n"
            "Contact: sales@your-trading-app.com"
        )
        msg.exec()


# ============================================================================
# EXAMPLE 10: Main Entry Point with License Protection
# ============================================================================

"""
Your main.py should look like this:
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.enhanced_main_window import EnhancedMainWindow
from widgets.license_dialog import check_license_on_startup


def main():
    """Main entry point with license protection"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Trading Application Pro")
    app.setOrganizationName("YourCompany")
    app.setApplicationVersion("1.0")

    # CHECK LICENSE BEFORE CREATING MAIN WINDOW
    print("Checking license...")
    if not check_license_on_startup():
        print("License validation failed. Exiting.")
        sys.exit(1)

    print("License valid. Starting application...")

    # Create and show main window
    window = EnhancedMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# ============================================================================
# SUMMARY OF INTEGRATION POINTS
# ============================================================================

"""
WHERE TO ADD LICENSE CHECKS:

1. main.py (or main entry point)
   - Call check_license_on_startup() BEFORE creating main window
   - Exit if no valid license

2. EnhancedMainWindow.__init__()
   - Add license check at start
   - Add periodic revalidation timer
   - Add license info menu item

3. Premium features (AI analysis, alerts, etc.)
   - Use @require_license('feature_name') decorator
   - Or manual check with license_manager.check_feature_access()

4. Opportunity scanner / Chart widgets
   - Limit display based on max_pairs from license
   - Show upgrade prompts when hitting limits

5. Dashboard
   - Optional: Add license status card
   - Show warnings when expiring soon

6. UI Elements
   - Enable/disable based on license tier
   - Show tooltips explaining which tier unlocks feature

REMEMBER:
- Change _MASTER_SECRET before deploying!
- Test on clean machine
- Keep customer database with license keys
- Generate unique key for each customer
"""
