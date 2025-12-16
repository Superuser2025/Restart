"""
AppleTrader Pro - Main Application Window
Integrates all 10 improvements into a unified trading dashboard
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QLabel, QComboBox, QPushButton,
                            QStatusBar, QMenuBar, QMenu, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from datetime import datetime

# Import all improvement widgets
from widgets.opportunity_scanner_widget import OpportunityScannerWidget
from widgets.price_action_commentary_widget import PriceActionCommentaryWidget
from widgets.correlation_heatmap_widget import CorrelationHeatmapWidget
from widgets.volatility_position_widget import VolatilityPositionWidget
from widgets.session_momentum_widget import SessionMomentumWidget
from widgets.order_flow_widget import InstitutionalOrderFlowWidget
from widgets.pattern_scorer_widget import PatternScorerWidget
from widgets.mtf_structure_widget import MTFStructureWidget
from widgets.news_impact_widget import NewsImpactWidget
from widgets.risk_reward_widget import RiskRewardWidget
from widgets.equity_curve_widget import EquityCurveWidget
from widgets.trade_journal_widget import TradeJournalWidget
from gui.chart_panel_matplotlib import ChartPanel
from gui.controls_panel import ControlsPanel
from gui.symbol_manager_dialog import SymbolManagerDialog
from core.mt5_connector import MT5Connector


class MainWindow(QMainWindow):
    """
    AppleTrader Pro Main Window

    Combines all 10 improvements into a cohesive trading dashboard
    """

    def __init__(self):
        super().__init__()
        self.current_symbol = "EURUSD"
        self.current_timeframe = "H4"

        # Initialize MT5 connector
        self.mt5_connector = MT5Connector()
        self.mt5_connector.connection_status_changed.connect(self.on_mt5_connection_changed)
        self.mt5_connector.data_updated.connect(self.on_mt5_data_updated)
        self.mt5_connector.error_occurred.connect(self.on_mt5_error)

        self.init_ui()

        # Start data update timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_all_data)
        self.data_timer.start(1000)  # Update every 1 second

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("")  # Empty title - no text shown
        self.setGeometry(100, 100, 1600, 1000)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        main_layout.setSpacing(0)  # Remove spacing

        # NO TOOLBAR - Scanner goes directly to top as requested

        # === OPPORTUNITY SCANNER (at very top of screen) ===
        self.scanner_widget = OpportunityScannerWidget()
        self.scanner_widget.setMinimumHeight(320)  # Increased so cards don't get cut off
        self.scanner_widget.setMaximumHeight(340)
        # Give scanner access to MT5 connector immediately
        self.scanner_widget.set_mt5_connector(self.mt5_connector)
        main_layout.addWidget(self.scanner_widget)

        # === STACKED WIDGET FOR MODE SWITCHING ===
        from PyQt6.QtWidgets import QStackedWidget
        self.mode_stack = QStackedWidget()

        # Page 0: Normal dashboard view
        normal_page = QWidget()
        normal_layout = QVBoxLayout(normal_page)
        normal_layout.setContentsMargins(0, 0, 0, 0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT COLUMN: Chart + Controls
        left_panel = self.create_left_panel()
        self.main_splitter.addWidget(left_panel)

        # CENTER COLUMN: Analysis Tabs
        self.center_panel = self.create_center_panel()
        self.main_splitter.addWidget(self.center_panel)

        # RIGHT COLUMN: Performance Tabs
        self.right_panel = self.create_right_panel()
        self.main_splitter.addWidget(self.right_panel)

        # Set column widths (40% left, 35% center, 25% right)
        self.main_splitter.setSizes([640, 560, 400])

        normal_layout.addWidget(self.main_splitter)
        self.mode_stack.addWidget(normal_page)  # Index 0

        # Page 1: MAX MODE full-screen chart
        self.max_mode_panel = self.create_max_mode_panel()
        self.mode_stack.addWidget(self.max_mode_panel)  # Index 1

        # Start in normal mode
        self.mode_stack.setCurrentIndex(0)

        main_layout.addWidget(self.mode_stack)

        # === STATUS BAR ===
        self.create_status_bar()

        # === MENU BAR ===
        self.create_menu_bar()

        # Apply dark theme
        self.apply_dark_theme()

    def create_max_mode_panel(self) -> QWidget:
        """Create independent MAX MODE chart panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create a new independent chart panel for MAX MODE
        self.max_mode_chart = ChartPanel()

        # Connect signals
        self.max_mode_chart.timeframe_changed.connect(self.on_timeframe_changed)
        self.max_mode_chart.symbol_changed.connect(self.on_symbol_changed)
        self.max_mode_chart.display_mode_changed.connect(self.on_display_mode_changed)

        layout.addWidget(self.max_mode_chart)

        return panel

    def create_toolbar(self) -> QHBoxLayout:
        """Create top toolbar - compact without title"""
        layout = QHBoxLayout()

        # Time display
        self.time_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.time_label.setFont(QFont("Arial", 10))
        self.time_label.setStyleSheet("color: #94A3B8;")
        layout.addWidget(self.time_label)

        layout.addStretch()

        # Connection status
        self.connection_label = QLabel("🔴 MT5: Disconnected")
        self.connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_label.setStyleSheet("color: #EF4444; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;")
        layout.addWidget(self.connection_label)

        return layout

    def create_left_panel(self) -> QWidget:
        """Create left panel with chart and controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Chart
        self.chart_panel = ChartPanel()
        layout.addWidget(self.chart_panel, 3)  # 75% height

        # Controls
        self.controls_panel = ControlsPanel()
        layout.addWidget(self.controls_panel, 1)  # 25% height

        # Connect controls panel signals
        self.controls_panel.order_requested.connect(self.on_order_requested)
        self.controls_panel.setting_changed.connect(self.on_setting_changed)

        # Connect chart panel signals
        self.chart_panel.timeframe_changed.connect(self.on_timeframe_changed)
        self.chart_panel.symbol_changed.connect(self.on_symbol_changed)
        self.chart_panel.display_mode_changed.connect(self.on_display_mode_changed)

        return widget

    def create_center_panel(self) -> QWidget:
        """Create center panel with analysis tabs"""
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: PRICE ACTION COMMENTARY (Most Important!)
        commentary_tab = QWidget()
        commentary_layout = QVBoxLayout(commentary_tab)
        self.commentary_widget = PriceActionCommentaryWidget()
        # Connect to MT5 for live data
        self.commentary_widget.set_symbol(self.current_symbol)
        commentary_layout.addWidget(self.commentary_widget)
        tabs.addTab(commentary_tab, "📊 Price Action")

        # Tab 2: Momentum & Correlation
        momentum_tab = QWidget()
        momentum_layout = QVBoxLayout(momentum_tab)
        self.momentum_widget = SessionMomentumWidget()
        momentum_layout.addWidget(self.momentum_widget)
        tabs.addTab(momentum_tab, "⚡ Momentum")

        # Tab 3: Correlation Heatmap
        correlation_tab = QWidget()
        correlation_layout = QVBoxLayout(correlation_tab)
        self.correlation_widget = CorrelationHeatmapWidget()
        correlation_layout.addWidget(self.correlation_widget)
        tabs.addTab(correlation_tab, "🔥 Correlation")

        # Tab 4: Structure Map
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        self.structure_widget = MTFStructureWidget()
        structure_layout.addWidget(self.structure_widget)
        tabs.addTab(structure_tab, "📊 Structure")

        # Tab 5: Order Flow
        orderflow_tab = QWidget()
        orderflow_layout = QVBoxLayout(orderflow_tab)
        self.orderflow_widget = InstitutionalOrderFlowWidget()
        orderflow_layout.addWidget(self.orderflow_widget)
        tabs.addTab(orderflow_tab, "💼 Order Flow")

        # Tab 6: News Events
        news_tab = QWidget()
        news_layout = QVBoxLayout(news_tab)
        self.news_widget = NewsImpactWidget()
        news_layout.addWidget(self.news_widget)
        tabs.addTab(news_tab, "📰 News")

        return tabs

    def create_right_panel(self) -> QWidget:
        """Create right panel with performance tabs"""
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Position Sizing
        sizing_tab = QWidget()
        sizing_layout = QVBoxLayout(sizing_tab)
        self.position_widget = VolatilityPositionWidget()
        sizing_layout.addWidget(self.position_widget)
        tabs.addTab(sizing_tab, "🎯 Position Size")

        # Tab 2: Risk-Reward
        rr_tab = QWidget()
        rr_layout = QVBoxLayout(rr_tab)
        self.rr_widget = RiskRewardWidget()
        rr_layout.addWidget(self.rr_widget)
        tabs.addTab(rr_tab, "🎯 Risk-Reward")

        # Tab 3: Pattern Scorer
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout(pattern_tab)
        self.pattern_widget = PatternScorerWidget()
        pattern_layout.addWidget(self.pattern_widget)
        tabs.addTab(pattern_tab, "⭐ Quality")

        # Tab 4: Equity Curve
        equity_tab = QWidget()
        equity_layout = QVBoxLayout(equity_tab)
        self.equity_widget = EquityCurveWidget()
        equity_layout.addWidget(self.equity_widget)
        tabs.addTab(equity_tab, "📊 Equity")

        # Tab 5: Trade Journal
        journal_tab = QWidget()
        journal_layout = QVBoxLayout(journal_tab)
        self.journal_widget = TradeJournalWidget()
        journal_layout.addWidget(self.journal_widget)
        tabs.addTab(journal_tab, "📝 Journal")

        return tabs

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.addPermanentWidget(QLabel(f"Last Update: {datetime.now().strftime('%H:%M:%S')}"))

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        export_action = QAction("Export Data", self)
        export_action.triggered.connect(self.on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("Refresh All", self)
        refresh_action.triggered.connect(self.update_all_data)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        manage_symbols_action = QAction("Manage Symbols...", self)
        manage_symbols_action.triggered.connect(self.on_manage_symbols)
        view_menu.addAction(manage_symbols_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def on_symbol_changed(self, symbol: str):
        """Handle symbol change - update ALL widgets to new symbol"""
        self.current_symbol = symbol
        self.status_label.setText(f"Symbol changed to: {symbol}")

        # Sync both chart panels to the same symbol
        if hasattr(self, 'chart_panel') and self.chart_panel.current_symbol != symbol:
            self.chart_panel.current_symbol = symbol
            self.chart_panel.symbol_combo.setCurrentText(symbol)

        if hasattr(self, 'max_mode_chart') and self.max_mode_chart.current_symbol != symbol:
            self.max_mode_chart.current_symbol = symbol
            self.max_mode_chart.symbol_combo.setCurrentText(symbol)

        # Update all widgets with new symbol
        if hasattr(self, 'orderflow_widget'):
            self.orderflow_widget.set_symbol(symbol)

        if hasattr(self, 'commentary_widget'):
            self.commentary_widget.set_symbol(symbol)

        if hasattr(self, 'momentum_widget'):
            self.momentum_widget.set_symbol(symbol)

        if hasattr(self, 'correlation_widget'):
            self.correlation_widget.set_symbol(symbol)

        if hasattr(self, 'position_widget'):
            self.position_widget.set_symbol(symbol)

        if hasattr(self, 'rr_widget'):
            self.rr_widget.set_symbol(symbol)

        if hasattr(self, 'pattern_widget'):
            self.pattern_widget.set_symbol(symbol)

        if hasattr(self, 'structure_widget'):
            self.structure_widget.set_symbol(symbol)

        if hasattr(self, 'news_widget'):
            self.news_widget.set_symbol(symbol)

        if hasattr(self, 'equity_widget'):
            self.equity_widget.set_symbol(symbol)

        if hasattr(self, 'journal_widget'):
            self.journal_widget.set_symbol(symbol)

        # Request fresh data for this symbol from MT5
        self.update_all_data()

    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.status_label.setText(f"Timeframe changed to: {timeframe}")

        # Sync both chart panels to the same timeframe
        if hasattr(self, 'chart_panel') and self.chart_panel.current_timeframe != timeframe:
            self.chart_panel.current_timeframe = timeframe
            self.chart_panel.timeframe_combo.setCurrentText(timeframe)

        if hasattr(self, 'max_mode_chart') and self.max_mode_chart.current_timeframe != timeframe:
            self.max_mode_chart.current_timeframe = timeframe
            self.max_mode_chart.timeframe_combo.setCurrentText(timeframe)

        self.update_all_data()

    def on_display_mode_changed(self, is_max_mode: bool):
        """Handle chart display mode change - switch between stacked pages"""
        print(f"[DEBUG] on_display_mode_changed called: is_max_mode={is_max_mode}")

        if is_max_mode:
            # MAX MODE: Switch to page 1 (full-screen chart)
            print("[DEBUG] Entering MAX MODE")

            # Sync current symbol and timeframe to MAX MODE chart
            self.max_mode_chart.current_symbol = self.chart_panel.current_symbol
            self.max_mode_chart.current_timeframe = self.chart_panel.current_timeframe
            self.max_mode_chart.symbol_combo.setCurrentText(self.chart_panel.current_symbol)
            self.max_mode_chart.timeframe_combo.setCurrentText(self.chart_panel.current_timeframe)

            # CRITICAL: Sync the is_max_mode state and button on MAX MODE chart
            self.max_mode_chart.is_max_mode = True
            self.max_mode_chart.display_toggle_btn.setText("⊟ SMALL MODE")
            self.max_mode_chart.display_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #EF4444;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #DC2626;
                }}
                QPushButton:pressed {{
                    background-color: #B91C1C;
                }}
            """)

            # CRITICAL: Hide scanner AND controls panel for true full-screen
            self.scanner_widget.setVisible(False)
            self.controls_panel.setVisible(False)

            # Switch to MAX MODE page
            self.mode_stack.setCurrentIndex(1)

            # Update MAX MODE chart
            self.max_mode_chart.update_chart()

            self.status_label.setText("Chart: MAX MODE - Full Screen")
        else:
            # SMALL MODE: Switch to page 0 (dashboard)
            print("[DEBUG] Entering SMALL MODE")

            # Sync current symbol and timeframe back to normal chart
            self.chart_panel.current_symbol = self.max_mode_chart.current_symbol
            self.chart_panel.current_timeframe = self.max_mode_chart.current_timeframe
            self.chart_panel.symbol_combo.setCurrentText(self.max_mode_chart.current_symbol)
            self.chart_panel.timeframe_combo.setCurrentText(self.max_mode_chart.current_timeframe)

            # CRITICAL: Sync the is_max_mode state and button on normal chart
            self.chart_panel.is_max_mode = False
            self.chart_panel.display_toggle_btn.setText("⛶ MAX MODE")
            self.chart_panel.display_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #2563EB;
                }}
                QPushButton:pressed {{
                    background-color: #1E40AF;
                }}
            """)

            # Show scanner AND controls panel, switch to normal page
            self.scanner_widget.setVisible(True)
            self.controls_panel.setVisible(True)
            self.mode_stack.setCurrentIndex(0)  # Switch to normal dashboard page

            # Update normal chart
            self.chart_panel.update_chart()

            self.status_label.setText("Chart: SMALL MODE - Dashboard View")

    def update_all_data(self):
        """Update all widgets with latest data"""
        # Update time display in toolbar
        if hasattr(self, 'time_label'):
            self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

        # Update status bar
        self.status_bar.showMessage(f"Updated: {datetime.now().strftime('%H:%M:%S')}", 2000)

    def on_mt5_connection_changed(self, connected: bool):
        """Handle MT5 connection status change"""
        if connected:
            self.connection_label.setText("🟢 MT5: Connected")
            self.connection_label.setStyleSheet("color: #10B981; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;")
            self.status_label.setText("MT5 connection established")
        else:
            self.connection_label.setText("🔴 MT5: Disconnected")
            self.connection_label.setStyleSheet("color: #EF4444; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;")
            self.status_label.setText("MT5 connection lost")

    def on_mt5_data_updated(self, data: dict):
        """Handle new data from MT5"""
        # Extract symbol and timeframe from data if available
        if 'symbol' in data:
            self.current_symbol = data['symbol']
        if 'timeframe' in data:
            self.current_timeframe = data['timeframe']

        # CRITICAL: Update data_manager with MT5 data so all widgets get live data
        from core.data_manager import data_manager
        data_manager.update_from_mt5_data(data)
        print(f"[MT5] Updated data_manager with live data for {self.current_symbol}")

        # Feed real data to Chart Panel
        if hasattr(self, 'chart_panel'):
            # Update chart's symbol if changed
            if self.chart_panel.current_symbol != self.current_symbol:
                self.chart_panel.current_symbol = self.current_symbol
                success = self.chart_panel.load_historical_data()  # Reload chart data with CORRECT method
                if success and hasattr(self.chart_panel, 'plot_candlesticks'):
                    self.chart_panel.plot_candlesticks()  # CRITICAL: Redraw the chart!
            # Chart auto-updates via its own timer using data_manager

        # Feed real data to Order Flow widget
        if hasattr(self, 'orderflow_widget'):
            # Get candle data for analysis
            df = self.mt5_connector.get_candles(self.current_symbol, self.current_timeframe, 200)
            if df is not None and len(df) > 50:
                # Scan for institutional orders using real data
                self.orderflow_widget.scan_and_update(self.current_symbol, df, lookback=50)
                print(f"[MT5] Fed {len(df)} candles to Order Flow widget for {self.current_symbol}")

        # Feed real data to Opportunity Scanner
        if hasattr(self, 'scanner_widget'):
            # Notify scanner that real data is available
            self.scanner_widget.set_mt5_connector(self.mt5_connector)
            print(f"[MT5] Opportunity Scanner now using REAL market data")

        # Feed real data to Momentum Widget
        if hasattr(self, 'momentum_widget'):
            # Get all symbols data from MT5 for momentum scanning
            market_data = self.mt5_connector.get_all_symbols_data()
            if market_data and len(market_data) > 0:
                self.momentum_widget.scan_and_update(market_data)
                print(f"[MT5] Fed {len(market_data)} symbols to Momentum Widget")

        # Feed real data to Correlation Widget
        if hasattr(self, 'correlation_widget'):
            # Get all symbols data for correlation analysis
            market_data = self.mt5_connector.get_all_symbols_data()
            if market_data and len(market_data) > 0:
                self.correlation_widget.update_data(market_data)
                print(f"[MT5] Fed {len(market_data)} symbols to Correlation Widget")

        # Update status
        self.status_label.setText(f"MT5 data received: {self.current_symbol} {self.current_timeframe}")

    def on_mt5_error(self, error_message: str):
        """Handle MT5 error"""
        self.status_label.setText(f"MT5 Error: {error_message}")
        print(f"[MT5 ERROR] {error_message}")

    def on_order_requested(self, order_type: str):
        """Handle quick order button click from controls panel"""
        print(f"[Main Window] {order_type} order requested")
        self.status_label.setText(f"{order_type} order requested - sending to MT5...")

        # Send order command to MT5 via command manager
        from core.command_manager import command_manager
        try:
            # CORRECT METHOD: send_order() with lot_size parameter
            command_manager.send_order(
                order_type=order_type,
                symbol=self.current_symbol,
                lot_size=0.01  # Default volume
            )
            self.status_label.setText(f"✓ {order_type} order sent to MT5 EA")
            print(f"[Main Window] {order_type} order command sent successfully")
        except Exception as e:
            self.status_label.setText(f"✗ Failed to send {order_type} order: {e}")
            print(f"[Main Window] Error sending order: {e}")

    def on_setting_changed(self, setting_name: str, value):
        """Handle setting change from controls panel"""
        print(f"[Main Window] Setting changed: {setting_name} = {value}")
        self.status_label.setText(f"Setting updated: {setting_name}")

        # Handle update speed changes
        if setting_name == 'update_speed':
            # Map speed to milliseconds
            speed_intervals = {
                'SLOW': 5000,      # 5 seconds
                'NORMAL': 2000,    # 2 seconds
                'FAST': 1000,      # 1 second
                'REALTIME': 500    # 0.5 seconds
            }

            interval = speed_intervals.get(value, 1000)

            # Update chart refresh timer - STOP, CHANGE, START to apply immediately
            if hasattr(self, 'chart_panel') and hasattr(self.chart_panel, 'update_timer'):
                self.chart_panel.update_timer.stop()
                self.chart_panel.update_timer.setInterval(interval)
                self.chart_panel.update_timer.start()
                print(f"[Main Window] Chart refresh rate changed to {interval}ms ({value})")
                self.status_label.setText(f"Chart refresh: {interval/1000}s")

                # Force immediate chart reload to show it's working
                if hasattr(self.chart_panel, 'load_historical_data'):
                    success = self.chart_panel.load_historical_data()
                    if success and hasattr(self.chart_panel, 'plot_candlesticks'):
                        self.chart_panel.plot_candlesticks()  # CRITICAL: Redraw the chart!
                    print(f"[Main Window] Chart reloaded immediately")

            # Update main window timer
            if hasattr(self, 'data_timer'):
                self.data_timer.stop()
                self.data_timer.setInterval(interval)
                self.data_timer.start()
                print(f"[Main Window] Data update rate changed to {interval}ms ({value})")

        # Handle filter changes
        elif setting_name in ['use_fvg_filter', 'use_ob_filter', 'use_liquidity_filter']:
            if hasattr(self, 'scanner_widget'):
                # Trigger a rescan with new filters
                self.scanner_widget.scan_market()

    def on_export(self):
        """Handle export action"""
        self.status_label.setText("Exporting data...")
        # Export trade journal
        self.journal_widget.on_export_clicked()

    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About AppleTrader Pro",
            "AppleTrader Pro v1.0\n\n"
            "Institutional-Grade Trading Dashboard\n\n"
            "Features:\n"
            "✓ 10 Advanced Trading Improvements\n"
            "✓ Real-time Market Analysis\n"
            "✓ AI-Powered Insights\n"
            "✓ Automated Trade Journal\n\n"
            "© 2025 AppleTrader Pro"
        )

    def on_manage_symbols(self):
        """Show symbol manager dialog"""
        dialog = SymbolManagerDialog(self)
        dialog.symbols_changed.connect(self.on_symbols_updated)
        dialog.exec()

    def on_symbols_updated(self, symbols: list):
        """Handle symbol list update from symbol manager"""
        self.status_label.setText(f"Symbol list updated: {len(symbols)} symbols")
        print(f"[Main Window] Symbol list updated: {symbols}")
        # Update all widgets that use symbols
        if hasattr(self, 'scanner_widget'):
            self.scanner_widget.pairs_to_scan = symbols
            self.scanner_widget.scan_market()
        # Future: Update other widgets as needed

    def apply_dark_theme(self):
        """Apply dark theme to main window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #444;
            }
            QMenuBar::item:selected {
                background-color: #0d7377;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #0d7377;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #444;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #444;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
            }
            QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #0d7377;
                border: 1px solid #444;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def closeEvent(self, event):
        """Handle window close event"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit AppleTrader Pro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
