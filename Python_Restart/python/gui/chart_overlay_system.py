"""
Chart Overlay System - Zone Visualization and Real-Time Analysis
Displays colored zones and analysis overlay on the chart like InstitutionalTradingRobot_v3.mq5
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from typing import List, Dict, Optional
import random


class Zone:
    """Represents a price zone on the chart"""
    def __init__(self, name: str, color: str, top: float, bottom: float, zone_type: str = ""):
        self.name = name
        self.color = QColor(color)
        self.top = top
        self.bottom = bottom
        self.zone_type = zone_type  # OB, FVG, Liquidity, etc.


class ChartOverlaySystem(QWidget):
    """
    Manages and renders all chart overlays including:
    - Colored horizontal zones (red, green, cyan, pink, brown)
    - Real-time analysis panel
    - Price action commentary
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zones: List[Zone] = []
        self.show_zones = True
        self.show_analysis_panel = True
        self.show_commentary = True

        # Chart dimensions
        self.chart_width = 0
        self.chart_height = 0
        self.price_high = 0.0
        self.price_low = 0.0

        # Analysis data
        self.analysis_data = {
            'order_blocks': 90,
            'phase': 'Pattern Detection',
            'h1_status': 'No pattern detected',
            'h4_status': 'No pattern detected',
            'advice': 'Monitor for breakout near wick 4.85',
            'system_status': 'System active',
            'commentary': []
        }

        # Visual toggles
        self.visuals_enabled = {
            'Pattern Boxes': True,
            'Liquidity Lines': True,
            'EV Values': True,
            'FVG Zones': True,
            'Order Blocks': True,
            'Monthly Zones': True,
            'Volatility Zones': True,
            'Fair Value Only': False,
            'Commentary': True
        }

        self.setMinimumSize(800, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_chart_dimensions(self, width: int, height: int, price_high: float, price_low: float):
        """Set chart dimensions for proper zone rendering"""
        self.chart_width = width
        self.chart_height = height
        self.price_high = price_high
        self.price_low = price_low

    def add_zone(self, name: str, color: str, top: float, bottom: float, zone_type: str = ""):
        """Add a zone to the chart"""
        zone = Zone(name, color, top, bottom, zone_type)
        self.zones.append(zone)
        self.update()

    def clear_zones(self):
        """Clear all zones"""
        self.zones.clear()
        self.update()

    def generate_sample_zones(self, current_price: float):
        """Generate sample zones for demonstration"""
        self.clear_zones()

        # Price range for zones
        price_range = current_price * 0.1  # 10% range

        # Bearish Order Block (Red)
        self.add_zone("Bearish OB", "#ff0000", current_price + price_range * 0.8,
                     current_price + price_range * 0.7, "Order Block")

        # Bearish OB 2
        self.add_zone("Bearish OB", "#ff0000", current_price + price_range * 0.5,
                     current_price + price_range * 0.4, "Order Block")

        # Bullish Order Block (Green)
        self.add_zone("Bullish OB", "#00ff00", current_price - price_range * 0.4,
                     current_price - price_range * 0.5, "Order Block")

        # Bullish OB 2
        self.add_zone("Bullish OB", "#00ff00", current_price - price_range * 0.7,
                     current_price - price_range * 0.8, "Order Block")

        # FVG Up (Cyan)
        self.add_zone("FVG Up", "#00ffff", current_price + price_range * 0.2,
                     current_price + price_range * 0.1, "FVG")

        # FVG Down (Magenta)
        self.add_zone("FVG Down", "#ff00ff", current_price - price_range * 0.1,
                     current_price - price_range * 0.2, "FVG")

        # Liquidity Zone (Orange/Brown)
        self.add_zone("Liquidity", "#aa6600", current_price + price_range * 0.3,
                     current_price + price_range * 0.25, "Liquidity")

        # Monthly High (Pink)
        self.add_zone("Monthly High", "#ffaaaa", current_price + price_range * 0.95,
                     current_price + price_range * 0.9, "Monthly")

        self.update()

    def price_to_y(self, price: float) -> int:
        """Convert price to Y coordinate"""
        if self.price_high == self.price_low:
            return self.chart_height // 2

        # Normalize price to chart height
        price_ratio = (self.price_high - price) / (self.price_high - self.price_low)
        y = int(price_ratio * self.chart_height)
        return max(0, min(y, self.chart_height))

    def paintEvent(self, event):
        """Paint zones and overlays"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw zones if enabled
        if self.show_zones and self.visuals_enabled.get('Order Blocks', True):
            self.draw_zones(painter)

        # Draw real-time analysis panel if enabled
        if self.show_analysis_panel:
            self.draw_analysis_panel(painter)

        # Draw price action commentary if enabled
        if self.show_commentary and self.visuals_enabled.get('Commentary', True):
            self.draw_commentary(painter)

    def draw_zones(self, painter: QPainter):
        """Draw all price zones"""
        for zone in self.zones:
            # Skip if specific zone type is disabled
            if zone.zone_type == "FVG" and not self.visuals_enabled.get('FVG Zones', True):
                continue
            if zone.zone_type == "Order Block" and not self.visuals_enabled.get('Order Blocks', True):
                continue
            if zone.zone_type == "Monthly" and not self.visuals_enabled.get('Monthly Zones', True):
                continue
            if zone.zone_type == "Liquidity" and not self.visuals_enabled.get('Liquidity Lines', True):
                continue

            # Calculate Y coordinates
            y_top = self.price_to_y(zone.top)
            y_bottom = self.price_to_y(zone.bottom)

            # Zone height
            zone_height = y_bottom - y_top

            # Draw zone rectangle with transparency
            zone_color = QColor(zone.color)
            zone_color.setAlpha(120)  # INCREASED: More visible (was 40)
            painter.setBrush(QBrush(zone_color))

            # Border
            border_color = QColor(zone.color)
            border_color.setAlpha(220)  # INCREASED: Brighter border (was 180)
            painter.setPen(QPen(border_color, 3))  # Thicker border (was 2)

            # Draw rectangle
            painter.drawRect(0, y_top, self.width(), zone_height)

            # Draw zone label with background
            label_color = QColor(zone.color)
            label_color.setAlpha(255)

            # Label text with price range
            if zone.zone_type in ["Order Block", "FVG"]:
                label_text = f"{zone.name}: {zone.bottom:.5f} - {zone.top:.5f}"
            else:
                label_text = f"{zone.name}: {zone.top:.5f}"

            # Label position
            label_x = 10
            label_y = y_top + 15

            # Draw label background for better visibility
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            text_rect = painter.fontMetrics().boundingRect(label_text)
            bg_rect = text_rect.adjusted(-4, -2, 4, 2)
            bg_rect.translate(label_x, label_y - text_rect.height())

            bg_color = QColor(0, 0, 0, 180)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(label_color, 2))
            painter.drawRoundedRect(bg_rect, 4, 4)

            # Draw label text
            painter.setPen(QPen(label_color, 1))
            painter.drawText(label_x, label_y, label_text)

    def draw_analysis_panel(self, painter: QPainter):
        """Draw real-time analysis overlay panel"""
        # Panel dimensions
        panel_width = 400
        panel_height = 300
        panel_x = self.width() - panel_width - 20
        panel_y = 20

        # Draw semi-transparent background
        bg_color = QColor(0, 0, 0, 200)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawRoundedRect(panel_x, panel_y, panel_width, panel_height, 10, 10)

        # Title
        painter.setPen(QPen(QColor(0, 255, 0), 1))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(panel_x + 10, panel_y + 25, "═══ REAL-TIME ANALYSIS ═══")

        # Content
        painter.setFont(QFont("Arial", 10))
        y_offset = panel_y + 50

        # Order Blocks
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(panel_x + 10, y_offset, f"Order Blocks: {self.analysis_data['order_blocks']} active")
        y_offset += 25

        # Phase Detection
        painter.setPen(QPen(QColor(0, 200, 255), 1))
        painter.drawText(panel_x + 10, y_offset, "───── Phase  / Pattern Detection ─────")
        y_offset += 25

        # H1 Status
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(panel_x + 10, y_offset, f"[H1] {self.analysis_data['h1_status']}")
        y_offset += 20

        # H4 Status
        painter.drawText(panel_x + 10, y_offset, f"[H4] {self.analysis_data['h4_status']}")
        y_offset += 30

        # Advice
        painter.setPen(QPen(QColor(255, 200, 0), 1))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(panel_x + 10, y_offset, "ADVICE:")
        y_offset += 20

        painter.setFont(QFont("Arial", 9))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        # Word wrap advice text
        advice_words = self.analysis_data['advice'].split()
        line = ""
        for word in advice_words:
            test_line = line + word + " "
            if painter.fontMetrics().horizontalAdvance(test_line) > panel_width - 30:
                painter.drawText(panel_x + 10, y_offset, line)
                y_offset += 18
                line = word + " "
            else:
                line = test_line
        if line:
            painter.drawText(panel_x + 10, y_offset, line)
            y_offset += 25

        # System Status
        painter.setPen(QPen(QColor(0, 255, 0), 1))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(panel_x + 10, y_offset, f"✓ {self.analysis_data['system_status']}")

    def draw_commentary(self, painter: QPainter):
        """Draw price action commentary items"""
        if not self.analysis_data['commentary']:
            return

        # Commentary position (bottom left)
        x = 10
        y = self.height() - 100

        painter.setFont(QFont("Arial", 9))

        for i, comment in enumerate(self.analysis_data['commentary'][:5]):  # Show max 5
            # Draw comment with background
            bg_color = QColor(0, 0, 0, 180)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(QColor(0, 255, 255), 1))

            # Text metrics
            text_width = painter.fontMetrics().horizontalAdvance(comment) + 20
            text_height = 25

            painter.drawRoundedRect(x, y + (i * 30), text_width, text_height, 5, 5)

            # Draw text
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(x + 10, y + (i * 30) + 17, comment)

    def update_analysis(self, data: Dict):
        """Update analysis panel data"""
        self.analysis_data.update(data)
        self.update()

    def add_commentary(self, text: str):
        """Add a commentary item"""
        if 'commentary' not in self.analysis_data:
            self.analysis_data['commentary'] = []

        self.analysis_data['commentary'].insert(0, text)

        # Keep only last 10
        if len(self.analysis_data['commentary']) > 10:
            self.analysis_data['commentary'] = self.analysis_data['commentary'][:10]

        self.update()

    def toggle_visual(self, visual_name: str, enabled: bool):
        """Toggle specific visual element"""
        if visual_name in self.visuals_enabled:
            self.visuals_enabled[visual_name] = enabled
            self.update()

    def toggle_zones(self, enabled: bool):
        """Toggle all zones visibility"""
        self.show_zones = enabled
        self.update()

    def toggle_analysis_panel(self, enabled: bool):
        """Toggle analysis panel visibility"""
        self.show_analysis_panel = enabled
        self.update()

    def toggle_commentary(self, enabled: bool):
        """Toggle commentary visibility"""
        self.show_commentary = enabled
        self.update()
