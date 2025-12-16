"""
Enhanced AppleTrader Pro - Main Window with Institutional Features
Integrates the comprehensive institutional panel and enhanced chart system
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QSplitter, QStatusBar, QMenu, QMessageBox,
                             QPushButton, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from datetime import datetime

from gui.merged_institutional_panel import MergedInstitutionalPanel
from gui.chart_panel_matplotlib import ChartPanel  # USE ORIGINAL EXCELLENT CHART!
from gui.symbol_manager_dialog import SymbolManagerDialog

# Import existing widgets
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

from core.mt5_connector import MT5Connector
from core.demo_mode_manager import demo_mode_manager, is_demo_mode
from core.multi_symbol_manager import symbol_manager, get_all_symbols


class EnhancedMainWindow(QMainWindow):
    """
    Enhanced Main Window with Institutional Trading Robot v3.0 features
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
        self.data_timer.start(1000)

    def init_ui(self):
        """Initialize the enhanced user interface"""
        self.setWindowTitle("")  # Empty title - user requested removal
        self.setGeometry(50, 50, 1920, 1080)  # Full HD size for better visibility

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # === OPPORTUNITY SCANNER ===
        self.scanner_widget = OpportunityScannerWidget()
        self.scanner_widget.setMinimumHeight(300)  # Increased from 260 to 300
        self.scanner_widget.setMaximumHeight(330)  # Increased from 280 to 330
        self.scanner_widget.set_mt5_connector(self.mt5_connector)
        main_layout.addWidget(self.scanner_widget)

        # === MAIN CONTENT (3-COLUMN LAYOUT) ===
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(3)  # Make splitter handle visible and draggable

        # LEFT COLUMN: Merged Institutional Panel (Fully Resizable!)
        self.institutional_panel = MergedInstitutionalPanel()
        self.institutional_panel.setMinimumWidth(350)  # Minimum width only, user can expand!

        # Connect all institutional panel signals
        self.institutional_panel.filter_toggled.connect(self.on_filter_toggled)
        self.institutional_panel.mode_changed.connect(self.on_mode_changed)
        self.institutional_panel.setting_changed.connect(self.on_setting_changed)
        self.institutional_panel.order_requested.connect(self.on_order_requested)

        self.splitter.addWidget(self.institutional_panel)

        # CENTER COLUMN: Chart + Analysis Tabs (No controls panel - merged into left!)
        self.center_panel = self.create_center_panel()
        self.splitter.addWidget(self.center_panel)

        # RIGHT COLUMN: Performance Tabs
        self.right_panel = self.create_right_panel()
        self.splitter.addWidget(self.right_panel)

        # Set initial column widths (user can resize any time!)
        # Left: 450px, Center: 810px, Right: 540px (totals 1800px)
        self.splitter.setSizes([450, 870, 480])

        # Make splitter stretchable
        self.splitter.setStretchFactor(0, 1)  # Left can stretch
        self.splitter.setStretchFactor(1, 2)  # Center gets more stretch priority
        self.splitter.setStretchFactor(2, 1)  # Right can stretch

        main_layout.addWidget(self.splitter)

        # === STATUS BAR ===
        self.create_status_bar()

        # === MENU BAR ===
        self.create_menu_bar()

        # Apply dark theme
        self.apply_dark_theme()

    def create_center_panel(self) -> QWidget:
        """Create center panel with ORIGINAL excellent chart + analysis tabs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # === ORIGINAL EXCELLENT CHART (TradingView-style with zones!) ===
        self.chart_panel = ChartPanel()  # The original excellent implementation!
        self.chart_panel.timeframe_changed.connect(self.on_timeframe_changed)
        self.chart_panel.symbol_changed.connect(self.on_symbol_changed)  # CRITICAL: Connect symbol changes!
        self.chart_panel.display_mode_changed.connect(self.on_display_mode_changed)  # CRITICAL: Connect MAX MODE!
        layout.addWidget(self.chart_panel, 4)  # 80% height - give chart MORE space!

        # === ANALYSIS TABS ===
        self.analysis_tabs = QTabWidget()
        self.analysis_tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: PRICE ACTION COMMENTARY
        commentary_tab = QWidget()
        commentary_layout = QVBoxLayout(commentary_tab)
        self.commentary_widget = PriceActionCommentaryWidget()
        commentary_layout.addWidget(self.commentary_widget)
        self.analysis_tabs.addTab(commentary_tab, "📊 Price Action")

        # Tab 2: Momentum
        momentum_tab = QWidget()
        momentum_layout = QVBoxLayout(momentum_tab)
        self.momentum_widget = SessionMomentumWidget()
        momentum_layout.addWidget(self.momentum_widget)
        self.analysis_tabs.addTab(momentum_tab, "⚡ Momentum")

        # Tab 3: Correlation
        correlation_tab = QWidget()
        correlation_layout = QVBoxLayout(correlation_tab)
        self.correlation_widget = CorrelationHeatmapWidget()
        correlation_layout.addWidget(self.correlation_widget)
        self.analysis_tabs.addTab(correlation_tab, "🔥 Correlation")

        # Tab 4: Structure
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        self.structure_widget = MTFStructureWidget()
        structure_layout.addWidget(self.structure_widget)
        self.analysis_tabs.addTab(structure_tab, "📊 Structure")

        # Tab 5: Order Flow
        orderflow_tab = QWidget()
        orderflow_layout = QVBoxLayout(orderflow_tab)
        self.orderflow_widget = InstitutionalOrderFlowWidget()
        orderflow_layout.addWidget(self.orderflow_widget)
        self.analysis_tabs.addTab(orderflow_tab, "💼 Order Flow")

        # Tab 6: News
        news_tab = QWidget()
        news_layout = QVBoxLayout(news_tab)
        self.news_widget = NewsImpactWidget()
        news_layout.addWidget(self.news_widget)
        self.analysis_tabs.addTab(news_tab, "📰 News")

        layout.addWidget(self.analysis_tabs, 1)  # 20% height

        return widget

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

        self.status_bar.addPermanentWidget(
            QLabel(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        )

    def on_symbol_changed(self, symbol: str):
        """Handle symbol change - MUST UPDATE ALL WIDGETS"""
        self.current_symbol = symbol
        self.status_label.setText(f"Symbol changed to: {symbol}")

        # Update ALL analysis tab widgets with new symbol
        if hasattr(self, 'commentary_widget'):
            self.commentary_widget.set_symbol(symbol)

        if hasattr(self, 'momentum_widget'):
            self.momentum_widget.set_symbol(symbol)

        if hasattr(self, 'correlation_widget'):
            self.correlation_widget.set_symbol(symbol)

        if hasattr(self, 'structure_widget'):
            self.structure_widget.set_symbol(symbol)

        if hasattr(self, 'orderflow_widget'):
            self.orderflow_widget.set_symbol(symbol)

        if hasattr(self, 'news_widget'):
            self.news_widget.set_symbol(symbol)

        # Update ALL right panel widgets with new symbol
        if hasattr(self, 'position_widget'):
            self.position_widget.set_symbol(symbol)

        if hasattr(self, 'rr_widget'):
            self.rr_widget.set_symbol(symbol)

        if hasattr(self, 'pattern_widget'):
            self.pattern_widget.set_symbol(symbol)

        if hasattr(self, 'equity_widget'):
            self.equity_widget.set_symbol(symbol)

        if hasattr(self, 'journal_widget'):
            self.journal_widget.set_symbol(symbol)

        self.update_all_data()

    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.status_label.setText(f"Timeframe changed to: {timeframe}")
        self.update_all_data()

    def on_display_mode_changed(self, is_max_mode: bool):
        """Handle MAX MODE toggle - hide/show ONLY analysis tabs to maximize chart in center area"""
        print(f"[DEBUG] MAX MODE toggled: is_max_mode={is_max_mode}")

        if is_max_mode:
            # MAX MODE: Hide ONLY the analysis tabs below chart
            # Keep left panel, right panel, and scanner visible!
            print("[DEBUG] Entering MAX MODE - hiding analysis tabs only")

            # Hide ONLY analysis tabs below chart - chart expands to fill blue rectangle
            self.analysis_tabs.setVisible(False)

            print("[DEBUG] MAX MODE active - chart fills blue rectangle, all panels still visible")
        else:
            # SMALL MODE: Show analysis tabs again
            print("[DEBUG] Exiting MAX MODE - showing analysis tabs")

            # Show analysis tabs
            self.analysis_tabs.setVisible(True)

            print("[DEBUG] SMALL MODE active - normal layout restored")

    def on_filter_toggled(self, filter_name: str, enabled: bool):
        """Handle filter toggle from institutional panel - ACTUALLY APPLIES FILTERS"""
        from core.filter_manager import filter_manager

        # Update filter in filter manager
        filter_manager.set_filter(filter_name, enabled)

        # Update status
        self.status_label.setText(f"Filter {filter_name}: {'Enabled' if enabled else 'Disabled'}")
        print(f"[Main Window] Filter {filter_name} {'enabled' if enabled else 'disabled'}")

        # Trigger opportunity scanner refresh with new filters
        if hasattr(self, 'opportunity_scanner'):
            self.opportunity_scanner.refresh_with_filters()
            print(f"[Main Window] Scanner refreshed with active filters: {filter_manager.get_active_filters()}")

    def on_mode_changed(self, mode: str):
        """Handle mode change (AUTO/MANUAL)"""
        self.status_label.setText(f"Trading mode: {mode}")
        print(f"[Main Window] Trading mode changed to {mode}")

    def on_order_requested(self, order_type: str):
        """Handle quick order button click from controls panel"""
        print(f"[Main Window] {order_type} order requested")
        self.status_label.setText(f"{order_type} order requested - sending to MT5...")

        # Send order command to MT5 via command manager
        from core.command_manager import command_manager
        try:
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
        """Handle setting change from controls panel - ACTUALLY CONTROLS CHART VISUALS"""
        print(f"[Main Window] Setting changed: {setting_name} = {value}")
        self.status_label.setText(f"Setting updated: {setting_name}")

        # Handle Chart Visual toggles
        if setting_name.startswith('visual_'):
            from core.visual_controls import visual_controls
            visual_name = setting_name.replace('visual_', '')
            visual_controls.set_visual(visual_name, value)

            # Trigger chart redraw
            if hasattr(self, 'chart_panel'):
                self.chart_panel.plot_candlesticks()
                print(f"[Main Window] Chart redrawn with {visual_name} {'ON' if value else 'OFF'}")

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

            # Update chart refresh timer
            if hasattr(self, 'chart_panel') and hasattr(self.chart_panel, 'update_timer'):
                self.chart_panel.update_timer.stop()
                self.chart_panel.update_timer.setInterval(interval)
                self.chart_panel.update_timer.start()
                print(f"[Main Window] Chart refresh rate changed to {interval}ms ({value})")
                self.status_label.setText(f"Chart refresh: {interval/1000}s")

                # Force immediate chart reload
                if hasattr(self.chart_panel, 'load_historical_data'):
                    success = self.chart_panel.load_historical_data()
                    if success and hasattr(self.chart_panel, 'plot_candlesticks'):
                        self.chart_panel.plot_candlesticks()
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

    def update_all_data(self):
        """Update all widgets with latest data"""
        # Time display now in chart panel, not needed here

        # Update institutional panel with sample data
        if hasattr(self, 'institutional_panel'):
            self.institutional_panel.update_market_status("Trending market - High volume detected")
            self.institutional_panel.update_context("LONDON", "H4/H1", "BULLISH", "HH forming")
            self.institutional_panel.update_risk_metrics(2.0, 5.2, 68.0)
            # Performance section removed per user request
            # self.institutional_panel.update_performance(2.3, 8.7, 15.2)

        # Update status bar
        self.status_bar.showMessage(f"Updated: {datetime.now().strftime('%H:%M:%S')}", 2000)

    def on_mt5_connection_changed(self, connected: bool):
        """Handle MT5 connection status change"""
        # Connection status now shown in chart panel, not in top toolbar
        if hasattr(self, 'status_label'):
            if connected:
                self.status_label.setText("MT5 connection established")
            else:
                self.status_label.setText("MT5 connection lost")

    def on_mt5_data_updated(self, data: dict):
        """Handle new data from MT5"""
        if 'symbol' in data:
            self.current_symbol = data['symbol']
        if 'timeframe' in data:
            self.current_timeframe = data['timeframe']

        if hasattr(self, 'status_label'):
            self.status_label.setText(f"MT5 data received: {self.current_symbol} {self.current_timeframe}")

    def on_mt5_error(self, error_message: str):
        """Handle MT5 error"""
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"MT5 Error: {error_message}")
        print(f"[MT5 ERROR] {error_message}")

    def create_menu_bar(self):
        """Create menu bar with File, View, Help menus"""
        menubar = self.menuBar()

        # === FILE MENU ===
        file_menu = menubar.addMenu("&File")

        export_action = QAction("Export Data", self)
        export_action.triggered.connect(self.on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # === VIEW MENU ===
        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("Refresh All", self)
        refresh_action.triggered.connect(self.update_all_data)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        manage_symbols_action = QAction("Manage Symbols...", self)
        manage_symbols_action.triggered.connect(self.on_manage_symbols)
        view_menu.addAction(manage_symbols_action)

        # === HELP MENU ===
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def on_export(self):
        """Handle export action"""
        self.status_label.setText("Exporting data...")
        # Export trade journal
        if hasattr(self, 'journal_widget'):
            self.journal_widget.on_export_clicked()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AppleTrader Pro Enhanced",
            "AppleTrader Pro v3.0 - Enhanced Edition\n\n"
            "Institutional Trading Robot with Machine Learning\n\n"
            "Features:\n"
            "✓ 10 Advanced Trading Improvements\n"
            "✓ Institutional Filters & Controls\n"
            "✓ Real-time Market Analysis\n"
            "✓ AI-Powered Insights\n"
            "✓ FVG, Order Block, Liquidity Zone Detection\n"
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
