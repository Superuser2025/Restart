"""
AppleTrader Pro - Symbol Manager Dialog
Allows users to add/remove/edit tracked currency pairs
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QListWidget, QLineEdit,
                            QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from pathlib import Path
from typing import List


class SymbolManagerDialog(QDialog):
    """
    Symbol Manager Dialog

    Allows users to:
    - View all tracked symbols
    - Add new symbols
    - Remove symbols
    - Reset to defaults
    """

    symbols_changed = pyqtSignal(list)  # Emits when symbol list changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Symbol Manager")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Load current symbols
        self.symbols = self.load_symbols()

        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # === HEADER ===
        title = QLabel("📊 Manage Tracked Currency Pairs")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        info = QLabel("Add or remove currency pairs to track across all widgets")
        info.setFont(QFont("Arial", 10))
        info.setStyleSheet("color: #888;")
        layout.addWidget(info)

        # === SYMBOL LIST ===
        list_group = QGroupBox("Tracked Symbols")
        list_layout = QVBoxLayout()

        self.symbol_list = QListWidget()
        self.symbol_list.setFont(QFont("Courier", 11))
        self.refresh_symbol_list()
        list_layout.addWidget(self.symbol_list)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # === ADD SYMBOL ===
        add_group = QGroupBox("Add New Symbol")
        add_layout = QHBoxLayout()

        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter symbol (e.g., AUDCAD)")
        self.symbol_input.setFont(QFont("Courier", 11))
        self.symbol_input.returnPressed.connect(self.on_add_symbol)
        add_layout.addWidget(self.symbol_input)

        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.on_add_symbol)
        add_btn.setMinimumWidth(80)
        add_layout.addWidget(add_btn)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # === ACTIONS ===
        actions_layout = QHBoxLayout()

        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.clicked.connect(self.on_remove_symbol)
        actions_layout.addWidget(remove_btn)

        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self.on_reset_defaults)
        actions_layout.addWidget(reset_btn)

        layout.addLayout(actions_layout)

        # === DIALOG BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("💾 Save & Close")
        save_btn.clicked.connect(self.on_save)
        save_btn.setMinimumWidth(120)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #00aaff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0d7377;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #00aaff;
            }
            QPushButton {
                background-color: #0d7377;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14b1b8;
            }
            QPushButton:pressed {
                background-color: #0a5a5d;
            }
            QLabel {
                background-color: transparent;
            }
        """)

    def load_symbols(self) -> List[str]:
        """Load symbols from config file"""
        config_file = Path(__file__).parent.parent / "config" / "symbols.json"

        # Create default symbols if file doesn't exist
        default_symbols = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
            'NZDUSD', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY'
        ]

        if not config_file.exists():
            return default_symbols

        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('symbols', default_symbols)
        except:
            return default_symbols

    def save_symbols(self):
        """Save symbols to config file"""
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "symbols.json"

        try:
            with open(config_file, 'w') as f:
                json.dump({'symbols': self.symbols}, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save symbols: {e}")
            return False

    def refresh_symbol_list(self):
        """Refresh the symbol list display"""
        self.symbol_list.clear()
        for symbol in sorted(self.symbols):
            self.symbol_list.addItem(symbol)

    def on_add_symbol(self):
        """Add a new symbol"""
        symbol = self.symbol_input.text().strip().upper()

        if not symbol:
            return

        # Validate symbol format (should be 6 characters for forex)
        if len(symbol) != 6:
            QMessageBox.warning(
                self, "Invalid Symbol",
                "Symbol should be 6 characters (e.g., EURUSD, GBPJPY)"
            )
            return

        # Check if already exists
        if symbol in self.symbols:
            QMessageBox.information(
                self, "Duplicate",
                f"{symbol} is already in the list"
            )
            return

        # Add symbol
        self.symbols.append(symbol)
        self.refresh_symbol_list()
        self.symbol_input.clear()

    def on_remove_symbol(self):
        """Remove selected symbol"""
        current_item = self.symbol_list.currentItem()

        if not current_item:
            QMessageBox.warning(
                self, "No Selection",
                "Please select a symbol to remove"
            )
            return

        symbol = current_item.text()

        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove {symbol} from tracked symbols?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.symbols.remove(symbol)
            self.refresh_symbol_list()

    def on_reset_defaults(self):
        """Reset to default symbols"""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Reset to default 10 currency pairs? This will remove any custom symbols.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.symbols = [
                'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
                'NZDUSD', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY'
            ]
            self.refresh_symbol_list()

    def on_save(self):
        """Save and close dialog"""
        if not self.symbols:
            QMessageBox.warning(
                self, "No Symbols",
                "You must have at least one symbol to track"
            )
            return

        if self.save_symbols():
            # Emit signal with new symbol list
            self.symbols_changed.emit(self.symbols)
            self.accept()
