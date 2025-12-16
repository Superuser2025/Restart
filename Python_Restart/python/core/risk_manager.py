"""
AppleTrader Pro - Risk Manager
Symbol position limits, risk calculations, and exposure tracking
"""

from typing import Dict, Tuple, List
from datetime import datetime


class SymbolExposure:
    """Tracks exposure for a single symbol"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.total_lots = 0.0
        self.long_lots = 0.0
        self.short_lots = 0.0
        self.position_count = 0
        self.unrealized_pnl = 0.0
        self.last_update = datetime.now()


class RiskManager:
    """
    Manages risk limits and position sizing

    Features:
    - Symbol-specific position limits (USER CRITICAL REQUIREMENT)
    - Daily/weekly loss limits
    - Risk per trade calculations
    - Real-time exposure tracking from MT5 positions
    """

    def __init__(self):
        # Symbol position limits (USER EXPLICITLY REQUESTED - CRITICAL!)
        self.max_lots_per_symbol = 0.10  # Maximum lots allowed per symbol
        self.symbol_exposure: Dict[str, SymbolExposure] = {}  # Track current exposure per symbol

        # Account-level limits
        self.daily_loss_limit_percent = 2.0  # 2% daily loss limit
        self.weekly_loss_limit_percent = 5.0  # 5% weekly loss limit

        # Risk settings
        self.base_risk_percent = 0.5  # Base risk per trade
        self.current_risk_percent = 0.5  # Dynamic risk (adjusted based on conditions)

        # Tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.account_balance = 10000.0  # Will be updated from MT5
        self.peak_balance = 10000.0
        self.current_drawdown_percent = 0.0

        # Timestamps for reset tracking
        self.last_daily_reset = datetime.now().date()
        self.last_weekly_reset = datetime.now().date()


    def check_symbol_limit(self, symbol: str, requested_lot: float) -> Tuple[bool, str]:
        """
        Check if adding requested lot size would exceed symbol limit

        Args:
            symbol: Trading symbol (e.g., 'GBPUSD')
            requested_lot: Lot size to add

        Returns:
            (allowed: bool, message: str)
        """
        current_exposure = self.symbol_exposure.get(symbol, 0.0)
        new_total = current_exposure + requested_lot

        if new_total > self.max_lots_per_symbol:
            return False, f"❌ Symbol limit exceeded: {current_exposure:.2f} + {requested_lot:.2f} = {new_total:.2f} > {self.max_lots_per_symbol:.2f}"

        return True, f"✓ Within limit: {new_total:.2f} / {self.max_lots_per_symbol:.2f} lots"

    def update_from_positions(self, positions: List[Dict]):
        """
        Update exposure tracking from actual MT5 positions
        This is the PRIMARY way to track exposure (not manual updates)

        Args:
            positions: List of position dictionaries from MT5
        """
        # Get unique symbols from positions
        symbols = set(pos.get('symbol') for pos in positions if 'symbol' in pos)

        # Ensure exposure objects exist for all symbols with positions
        for symbol in symbols:
            if symbol not in self.symbol_exposure:
                self.symbol_exposure[symbol] = SymbolExposure(symbol)

        # Reset all exposure counts to zero first
        for exposure in self.symbol_exposure.values():
            exposure.total_lots = 0.0
            exposure.long_lots = 0.0
            exposure.short_lots = 0.0
            exposure.position_count = 0
            exposure.unrealized_pnl = 0.0

        # Recalculate from actual positions
        for pos in positions:
            symbol = pos.get('symbol')
            if not symbol:
                continue

            if symbol not in self.symbol_exposure:
                self.symbol_exposure[symbol] = SymbolExposure(symbol)

            exposure = self.symbol_exposure[symbol]

            # Get lot size and type
            lot_size = pos.get('volume', 0.0)
            profit = pos.get('profit', 0.0)

            # Determine if buy or sell (handle both string and int type)
            pos_type = pos.get('type')
            is_buy = (pos_type == 'buy') or (pos_type == 0)

            # Update exposure
            exposure.total_lots += lot_size
            if is_buy:
                exposure.long_lots += lot_size
            else:
                exposure.short_lots += lot_size

            exposure.position_count += 1
            exposure.unrealized_pnl += profit
            exposure.last_update = datetime.now()

        # Check for limit violations and warn
        for symbol, exposure in self.symbol_exposure.items():
            if exposure.total_lots > self.max_lots_per_symbol:
                pass  # Limit exceeded

    def update_symbol_exposure(self, symbol: str, lot_size: float, is_opening: bool = True):
        """
        Manual update of symbol exposure (use update_from_positions instead when possible)

        Args:
            symbol: Trading symbol
            lot_size: Lot size to add/subtract
            is_opening: True if opening position, False if closing
        """
        if symbol not in self.symbol_exposure:
            self.symbol_exposure[symbol] = SymbolExposure(symbol)

        exposure = self.symbol_exposure[symbol]

        if is_opening:
            exposure.total_lots += lot_size
        else:
            exposure.total_lots = max(0.0, exposure.total_lots - lot_size)

    def get_symbol_exposure(self, symbol: str) -> Dict[str, float]:
        """Get current exposure for symbol"""
        exposure = self.symbol_exposure.get(symbol)

        if not exposure:
            return {
                'symbol': symbol,
                'current': 0.0,
                'long': 0.0,
                'short': 0.0,
                'limit': self.max_lots_per_symbol,
                'remaining': self.max_lots_per_symbol,
                'utilization_percent': 0.0,
                'position_count': 0,
                'unrealized_pnl': 0.0,
                'limit_exceeded': False
            }

        remaining = self.max_lots_per_symbol - exposure.total_lots
        utilization_percent = (exposure.total_lots / self.max_lots_per_symbol) * 100
        limit_exceeded = exposure.total_lots > self.max_lots_per_symbol

        return {
            'symbol': symbol,
            'current': exposure.total_lots,
            'long': exposure.long_lots,
            'short': exposure.short_lots,
            'limit': self.max_lots_per_symbol,
            'remaining': remaining,
            'utilization_percent': utilization_percent,
            'position_count': exposure.position_count,
            'unrealized_pnl': exposure.unrealized_pnl,
            'limit_exceeded': limit_exceeded
        }

    def get_all_exposures(self) -> Dict[str, Dict]:
        """Get exposure for all symbols with positions"""
        return {
            symbol: self.get_symbol_exposure(symbol)
            for symbol in self.symbol_exposure.keys()
        }

    def check_daily_limit(self) -> Tuple[bool, str]:
        """Check if daily loss limit reached"""
        daily_loss_limit_dollars = self.account_balance * (self.daily_loss_limit_percent / 100)
        remaining = daily_loss_limit_dollars + self.daily_pnl  # daily_pnl is negative if losing

        if self.daily_pnl <= -daily_loss_limit_dollars:
            return False, f"❌ Daily loss limit reached: ${self.daily_pnl:.2f} / -${daily_loss_limit_dollars:.2f}"

        return True, f"✓ Daily limit OK: ${remaining:.2f} remaining"

    def check_weekly_limit(self) -> Tuple[bool, str]:
        """Check if weekly loss limit reached"""
        weekly_loss_limit_dollars = self.account_balance * (self.weekly_loss_limit_percent / 100)
        remaining = weekly_loss_limit_dollars + self.weekly_pnl

        if self.weekly_pnl <= -weekly_loss_limit_dollars:
            return False, f"❌ Weekly loss limit reached: ${self.weekly_pnl:.2f} / -${weekly_loss_limit_dollars:.2f}"

        return True, f"✓ Weekly limit OK: ${remaining:.2f} remaining"

    def calculate_position_size(self, symbol: str, entry_price: float, sl_price: float) -> Dict[str, float]:
        """
        Calculate position size based on risk parameters

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            sl_price: Stop loss price

        Returns:
            Dict with lot_size, risk_amount, etc.
        """
        # Calculate risk amount in account currency
        risk_amount = self.account_balance * (self.current_risk_percent / 100)

        # Calculate pip risk
        pip_size = 0.0001  # For most pairs
        pips_risk = abs(entry_price - sl_price) / pip_size

        # Calculate lot size (simplified - would need proper pip value calculation)
        # For GBPUSD: 1 lot = $10/pip, 0.01 lot = $0.10/pip
        pip_value_per_lot = 10.0  # $10 per pip for 1 standard lot
        lot_size = risk_amount / (pips_risk * pip_value_per_lot)

        # Round to 0.01
        lot_size = round(lot_size, 2)

        # Check against symbol limit
        allowed, message = self.check_symbol_limit(symbol, lot_size)

        if not allowed:
            # Reduce to fit limit
            current_exposure = self.symbol_exposure.get(symbol, 0.0)
            lot_size = max(0.01, self.max_lots_per_symbol - current_exposure)

        return {
            'lot_size': lot_size,
            'risk_amount': risk_amount,
            'pips_risk': pips_risk,
            'pip_value': pip_value_per_lot * lot_size,
            'allowed': allowed,
            'message': message
        }

    def adjust_risk_for_conditions(self, volatility: str, mtf_aligned: bool, confluence_score: int):
        """
        Adjust risk based on market conditions

        Args:
            volatility: 'LOW', 'NORMAL', 'HIGH'
            mtf_aligned: True if MTF confirmation present
            confluence_score: Number of confluence factors (0-5)
        """
        risk = self.base_risk_percent

        # Volatility adjustment
        if volatility == 'HIGH':
            risk *= 0.7  # Reduce by 30% in high volatility
        elif volatility == 'LOW':
            risk *= 1.3  # Increase by 30% in low volatility

        # MTF adjustment
        if not mtf_aligned:
            risk *= 0.8  # Reduce by 20% if no MTF confirmation

        # Confluence adjustment
        if confluence_score >= 4:
            risk *= 1.2  # Increase by 20% for high confluence
        elif confluence_score <= 2:
            risk *= 0.8  # Reduce by 20% for low confluence

        # Cap at reasonable limits
        risk = max(0.1, min(2.0, risk))  # Between 0.1% and 2.0%

        self.current_risk_percent = risk

    def update_account(self, balance: float, equity: float = None, daily_pnl: float = None):
        """
        Update account tracking and check for daily/weekly resets

        Args:
            balance: Current account balance
            equity: Current equity (defaults to balance if not provided)
            daily_pnl: Today's P&L (calculated if not provided)
        """
        self.account_balance = balance

        if equity is None:
            equity = balance

        # Update peak balance
        if balance > self.peak_balance:
            self.peak_balance = balance

        # Calculate current drawdown
        if self.peak_balance > 0:
            self.current_drawdown_percent = ((self.peak_balance - equity) / self.peak_balance) * 100

        # Check for daily reset
        today = datetime.now().date()
        if today != self.last_daily_reset:
            self.daily_pnl = 0.0
            self.last_daily_reset = today

        # Check for weekly reset (Monday)
        if today.weekday() == 0 and today != self.last_weekly_reset:
            self.weekly_pnl = 0.0
            self.last_weekly_reset = today

        # Update P&L
        if daily_pnl is not None:
            self.daily_pnl = daily_pnl

    def get_risk_status(self) -> Dict:
        """Get current risk status for display"""
        daily_ok, daily_msg = self.check_daily_limit()
        weekly_ok, weekly_msg = self.check_weekly_limit()

        # Calculate remaining buffer
        daily_loss_limit_dollars = self.account_balance * (self.daily_loss_limit_percent / 100)
        weekly_loss_limit_dollars = self.account_balance * (self.weekly_loss_limit_percent / 100)
        daily_remaining = daily_loss_limit_dollars + self.daily_pnl  # daily_pnl negative if losing
        weekly_remaining = weekly_loss_limit_dollars + self.weekly_pnl

        return {
            'current_risk_percent': self.current_risk_percent,
            'base_risk_percent': self.base_risk_percent,
            'daily_limit_ok': daily_ok,
            'daily_limit_message': daily_msg,
            'weekly_limit_ok': weekly_ok,
            'weekly_limit_message': weekly_msg,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'daily_pnl_percent': (self.daily_pnl / self.account_balance * 100) if self.account_balance > 0 else 0,
            'weekly_pnl_percent': (self.weekly_pnl / self.account_balance * 100) if self.account_balance > 0 else 0,
            'daily_remaining': daily_remaining,
            'weekly_remaining': weekly_remaining,
            'daily_limit_percent': self.daily_loss_limit_percent,
            'weekly_limit_percent': self.weekly_loss_limit_percent,
            'account_balance': self.account_balance,
            'peak_balance': self.peak_balance,
            'current_drawdown_percent': self.current_drawdown_percent,
            'symbol_limits': self.get_all_exposures()
        }

    def get_exposure_summary(self) -> str:
        """Get human-readable summary of all exposures"""
        if not self.symbol_exposure:
            return "No open positions"

        lines = []
        for symbol, exposure in self.symbol_exposure.items():
            if exposure.total_lots > 0:
                status = "⚠️ LIMIT EXCEEDED" if exposure.total_lots > self.max_lots_per_symbol else "✓"
                lines.append(f"{status} {symbol}: {exposure.total_lots:.3f}/{self.max_lots_per_symbol:.3f} lots "
                           f"(Long: {exposure.long_lots:.3f}, Short: {exposure.short_lots:.3f})")

        return "\n".join(lines) if lines else "No open positions"


# Global instance
risk_manager = RiskManager()
