"""
Visual Controls Manager - Controls what gets displayed on charts
"""

class VisualControls:
    """Manages visibility of chart visual elements"""

    def __init__(self):
        # Chart Visuals - User can toggle these
        self.pattern_boxes = True
        self.liquidity_lines = True
        self.fvg_zones = True
        self.order_blocks = True
        self.monthly_zones = True
        self.volatility_zones = True
        self.commentary = True
        self.smart_money_legend = False  # Legend OFF by default

    def set_visual(self, visual_name: str, enabled: bool):
        """Enable/disable a specific visual element"""
        # Normalize visual name to attribute name
        attr_name = visual_name.lower().replace(" ", "_").replace("-", "_")

        if hasattr(self, attr_name):
            setattr(self, attr_name, enabled)
            print(f"[VisualControls] {visual_name} = {enabled}")
            return True
        else:
            print(f"[VisualControls] WARNING: Unknown visual '{visual_name}'")
            return False

    def get_visual(self, visual_name: str) -> bool:
        """Get current state of a visual element"""
        attr_name = visual_name.lower().replace(" ", "_").replace("-", "_")
        return getattr(self, attr_name, True)  # Default to True if not found

    def should_draw_pattern_boxes(self) -> bool:
        """Check if pattern boxes should be drawn"""
        return self.pattern_boxes

    def should_draw_liquidity_lines(self) -> bool:
        """Check if liquidity lines should be drawn"""
        return self.liquidity_lines

    def should_draw_fvg_zones(self) -> bool:
        """Check if FVG zones should be drawn"""
        return self.fvg_zones

    def should_draw_order_blocks(self) -> bool:
        """Check if order blocks should be drawn"""
        return self.order_blocks

    def should_draw_monthly_zones(self) -> bool:
        """Check if monthly zones should be drawn"""
        return self.monthly_zones

    def should_draw_volatility_zones(self) -> bool:
        """Check if volatility zones should be drawn"""
        return self.volatility_zones

    def should_draw_commentary(self) -> bool:
        """Check if commentary should be drawn"""
        return self.commentary

    def should_draw_smart_money_legend(self) -> bool:
        """Check if smart money legend should be drawn"""
        return self.smart_money_legend


# Global singleton instance
visual_controls = VisualControls()
