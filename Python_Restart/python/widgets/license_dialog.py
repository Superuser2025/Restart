"""
License Activation Dialog
Shows license status and allows activation
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QLineEdit, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.license_manager import license_manager

# Development mode support
try:
    from core.dev_config import is_dev_mode, get_mode_label
except ImportError:
    def is_dev_mode():
        return False
    def get_mode_label():
        return "🔐 PRODUCTION MODE"


class LicenseDialog(QDialog):
    """
    Professional license activation dialog

    Features:
    - Shows current license status
    - Allows license key activation
    - Displays feature access information
    - Shows expiry countdown
    """

    def __init__(self, parent=None, force_activation=False):
        super().__init__(parent)
        self.force_activation = force_activation
        self.init_ui()
        self.load_license_status()

    def init_ui(self):
        self.setWindowTitle("License Activation")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("🔐 License Management")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Status Frame
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(self.status_frame)

        self.status_title = QLabel("License Status")
        self.status_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.status_title)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        status_layout.addWidget(self.status_text)

        layout.addWidget(self.status_frame)

        # Activation Section
        activation_label = QLabel("Enter License Key:")
        activation_label.setFont(QFont("Arial", 11))
        layout.addWidget(activation_label)

        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Paste your license key here...")
        self.license_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                font-size: 10pt;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        layout.addWidget(self.license_input)

        # Buttons
        button_layout = QHBoxLayout()

        self.activate_btn = QPushButton("Activate License")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.activate_btn.clicked.connect(self.activate_license)
        button_layout.addWidget(self.activate_btn)

        self.close_btn = QPushButton("Close" if not self.force_activation else "Quit")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        self.close_btn.clicked.connect(self.handle_close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Contact info
        contact_label = QLabel("Need a license? Contact: your.email@example.com")
        contact_label.setStyleSheet("color: #888888; font-size: 9pt;")
        contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(contact_label)

        # Machine ID (for support)
        machine_id = license_manager.get_machine_id()
        machine_label = QLabel(f"Machine ID: {machine_id[:16]}...")
        machine_label.setStyleSheet("color: #666666; font-size: 8pt;")
        machine_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        machine_label.setToolTip(f"Full Machine ID: {machine_id}\n(Provide this when requesting a license)")
        layout.addWidget(machine_label)

    def load_license_status(self):
        """Load and display current license status"""
        info = license_manager.get_license_info()

        if info['valid']:
            # Valid license
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e3a1e;
                    border: 2px solid #2d5a2d;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)

            status_text = f"""✓ LICENSE ACTIVE

Tier:            {info['tier']}
Customer:        {info['customer']}
Expires:         {info['expiry_date']}
Days Remaining:  {info['days_remaining']} days

Features:        {', '.join(info['features'])}
Max Pairs:       {info['max_pairs']}
AI Analysis:     {'Enabled' if info['ai_analysis'] else 'Disabled'}
"""
            self.status_text.setText(status_text)

            # Disable activation if valid
            if not self.force_activation:
                self.license_input.setEnabled(False)
                self.activate_btn.setEnabled(False)

            # Warning if expiring soon
            if info['days_remaining'] < 7:
                warning = QLabel(f"⚠️ License expires in {info['days_remaining']} days. Please renew.")
                warning.setStyleSheet("color: #ff9900; font-weight: bold;")
                warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.layout().insertWidget(2, warning)

        else:
            # Invalid or no license
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #3a1e1e;
                    border: 2px solid #5a2d2d;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)

            status_text = f"""✗ NO VALID LICENSE

Status:  {info['status']}
Message: {info['message']}

Please enter a valid license key below to activate.
"""
            self.status_text.setText(status_text)

    def activate_license(self):
        """Activate the entered license key"""
        license_key = self.license_input.text().strip()

        if not license_key:
            self.show_message("❌ Error", "Please enter a license key")
            return

        # Attempt activation
        success, message = license_manager.activate_license(license_key)

        if success:
            self.show_message("✓ Success", message)
            self.load_license_status()  # Refresh display
            self.license_input.clear()
        else:
            self.show_message("❌ Activation Failed", message)

    def show_message(self, title: str, message: str):
        """Show a message in the status area"""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Information if "✓" in title else QMessageBox.Icon.Warning)
        msg.exec()

    def handle_close(self):
        """Handle close button - quit app if license required"""
        if self.force_activation:
            # Check if license is now valid
            valid, _, _ = license_manager.validate_license()
            if not valid:
                # No valid license - quit application
                from PyQt6.QtWidgets import QApplication
                QApplication.quit()
            else:
                self.accept()
        else:
            self.accept()

    def closeEvent(self, event):
        """Override close event for forced activation"""
        if self.force_activation:
            valid, _, _ = license_manager.validate_license()
            if not valid:
                # Prevent closing without valid license
                event.ignore()
                self.show_message("License Required",
                                "You must activate a valid license to use this application.")
            else:
                event.accept()
        else:
            event.accept()


def check_license_on_startup() -> bool:
    """
    Check license on application startup
    Returns True if app should continue, False if should exit
    """
    # Development mode bypass
    if is_dev_mode():
        print("=" * 60)
        print("🔧 DEVELOPMENT MODE - License checks bypassed")
        print("=" * 60)
        return True

    valid, message, license_data = license_manager.validate_license()

    if valid:
        # Show notification if expiring soon
        days = license_manager.get_days_remaining()
        if days < 7:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("License Expiring Soon")
            msg.setText(f"Your license expires in {days} days.")
            msg.setInformativeText("Please contact support to renew your license.")
            msg.exec()
        return True
    else:
        # Show activation dialog
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        dialog = LicenseDialog(force_activation=True)
        result = dialog.exec()

        # Check again after dialog
        valid, _, _ = license_manager.validate_license()
        return valid
