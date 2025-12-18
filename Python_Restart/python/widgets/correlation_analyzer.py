"""
AppleTrader Pro - Multi-Symbol Correlation Heatmap (IMPROVEMENT #1)
Real-time correlation analysis across currency pairs
Detects divergence opportunities when correlations break down
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


class CorrelationPair:
    """Correlation data for a pair of symbols"""

    def __init__(self, symbol1: str, symbol2: str, correlation: float,
                 historical_avg: float, period: int):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.correlation = correlation
        self.historical_avg = historical_avg
        self.period = period
        self.divergence = abs(correlation - historical_avg)
        self.is_diverging = self.divergence > 0.3  # 30% divergence threshold

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol1': self.symbol1,
            'symbol2': self.symbol2,
            'correlation': self.correlation,
            'historical_avg': self.historical_avg,
            'divergence': self.divergence,
            'is_diverging': self.is_diverging,
            'period': self.period
        }


class MultiSymbolCorrelationAnalyzer:
    """
    Multi-Symbol Correlation Heatmap Engine

    Calculates rolling correlation between currency pairs to identify:
    - Current correlation strength and direction
    - Historical average correlations
    - Divergence opportunities (when correlation breaks down)
    - Correlated/inverse pairs for risk management

    Color coding:
    - Dark Green: +0.8 to +1.0 (strong positive correlation)
    - Light Green: +0.5 to +0.8 (moderate positive)
    - Gray: -0.5 to +0.5 (no correlation)
    - Orange: -0.5 to -0.8 (moderate negative)
    - Red: -0.8 to -1.0 (strong negative/inverse)

    Expected Impact: 15-20 min/day saved, catches hidden divergence setups
    """

    def __init__(self, symbols: List[str] = None):
        """
        Initialize analyzer

        Args:
            symbols: List of symbols to analyze (default: major pairs)
        """
        self.symbols = symbols or [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP',
            'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY'
        ]

        self.correlation_matrix = {}  # {(symbol1, symbol2): CorrelationPair}
        self.historical_correlations = {}  # Long-term averages
        self.divergence_alerts = []
        self.last_update = None

        # Known strong correlations (for reference)
        self.expected_correlations = {
            ('EURUSD', 'GBPUSD'): 0.85,
            ('EURUSD', 'AUDUSD'): 0.75,
            ('EURUSD', 'NZDUSD'): 0.70,
            ('GBPUSD', 'AUDUSD'): 0.70,
            ('USDJPY', 'USDCHF'): 0.80,
            ('AUDUSD', 'NZDUSD'): 0.90,
            ('EURJPY', 'GBPJPY'): 0.85,
            ('AUDJPY', 'NZDJPY'): 0.88,
            ('EURUSD', 'USDCHF'): -0.85,
            ('GBPUSD', 'USDCHF'): -0.75,
        }

    def calculate_correlations(self, market_data: Dict[str, pd.DataFrame],
                              short_period: int = 20,
                              long_period: int = 100) -> Dict:
        """
        Calculate correlation matrix for all symbol pairs

        Args:
            market_data: {symbol: DataFrame with close prices}
            short_period: Period for current correlation (default 20 bars)
            long_period: Period for historical average (default 100 bars)

        Returns:
            Complete correlation analysis
        """
        self.correlation_matrix = {}
        self.divergence_alerts = []

        # Prepare price data
        price_data = {}
        for symbol, df in market_data.items():
            if symbol not in self.symbols:
                continue
            if df is None or len(df) < short_period:
                continue
            if 'close' not in df.columns:
                continue

            price_data[symbol] = df['close'].values

        if len(price_data) < 2:
            return self._empty_result()

        # Calculate pairwise correlations
        symbols_list = list(price_data.keys())

        for i in range(len(symbols_list)):
            for j in range(i + 1, len(symbols_list)):
                symbol1 = symbols_list[i]
                symbol2 = symbols_list[j]

                prices1 = price_data[symbol1]
                prices2 = price_data[symbol2]

                # Align lengths
                min_len = min(len(prices1), len(prices2))
                if min_len < short_period:
                    continue

                prices1 = prices1[-min_len:]
                prices2 = prices2[-min_len:]

                # Calculate current correlation (short period)
                current_corr = self._calculate_correlation(
                    prices1[-short_period:],
                    prices2[-short_period:]
                )

                # Calculate historical correlation (long period)
                if min_len >= long_period:
                    historical_corr = self._calculate_correlation(
                        prices1[-long_period:],
                        prices2[-long_period:]
                    )
                else:
                    historical_corr = current_corr

                # Store historical average
                pair_key = (symbol1, symbol2)
                self.historical_correlations[pair_key] = historical_corr

                # Create correlation pair
                corr_pair = CorrelationPair(
                    symbol1, symbol2, current_corr,
                    historical_corr, short_period
                )

                self.correlation_matrix[pair_key] = corr_pair

                # Check for divergence
                if corr_pair.is_diverging:
                    self._generate_divergence_alert(corr_pair)

        self.last_update = datetime.now()

        return self._generate_report()

    def _calculate_correlation(self, prices1: np.ndarray,
                              prices2: np.ndarray) -> float:
        """
        Calculate Pearson correlation coefficient

        Args:
            prices1: Price array for symbol 1
            prices2: Price array for symbol 2

        Returns:
            Correlation coefficient (-1 to +1)
        """
        if len(prices1) < 2 or len(prices2) < 2:
            return 0.0

        # Convert to returns (percentage changes)
        returns1 = np.diff(prices1) / prices1[:-1]
        returns2 = np.diff(prices2) / prices2[:-1]

        # Remove any NaN or inf values
        mask = np.isfinite(returns1) & np.isfinite(returns2)
        returns1 = returns1[mask]
        returns2 = returns2[mask]

        if len(returns1) < 2:
            return 0.0

        # Calculate correlation
        correlation = np.corrcoef(returns1, returns2)[0, 1]

        if np.isnan(correlation):
            return 0.0

        return correlation

    def _generate_divergence_alert(self, corr_pair: CorrelationPair):
        """Generate alert for significant divergence"""
        symbol1 = corr_pair.symbol1
        symbol2 = corr_pair.symbol2
        current = corr_pair.correlation
        historical = corr_pair.historical_avg
        divergence = corr_pair.divergence

        # Determine alert message
        if historical > 0.7 and current < 0.4:
            # Normally correlated, now breaking down
            alert = {
                'type': 'CORRELATION_BREAKDOWN',
                'symbol1': symbol1,
                'symbol2': symbol2,
                'message': (f"🚨 DIVERGENCE: {symbol1}/{symbol2} normally "
                           f"+{historical:.2f}, now {current:+.2f}"),
                'recommendation': (f"Opportunity: One may be lagging. "
                                  f"Check which is stronger and trade it."),
                'divergence': divergence
            }
            self.divergence_alerts.append(alert)

        elif historical < -0.7 and current > -0.4:
            # Normally inverse, now converging
            alert = {
                'type': 'INVERSE_BREAKDOWN',
                'symbol1': symbol1,
                'symbol2': symbol2,
                'message': (f"🚨 INVERSE BREAKDOWN: {symbol1}/{symbol2} normally "
                           f"{historical:.2f}, now {current:+.2f}"),
                'recommendation': (f"Caution: Inverse relationship breaking down. "
                                  f"Market conditions changing."),
                'divergence': divergence
            }
            self.divergence_alerts.append(alert)

        elif abs(current - historical) > 0.5:
            # Significant change in correlation
            alert = {
                'type': 'CORRELATION_SHIFT',
                'symbol1': symbol1,
                'symbol2': symbol2,
                'message': (f"⚠️ SHIFT: {symbol1}/{symbol2} correlation changed "
                           f"{historical:+.2f} → {current:+.2f}"),
                'recommendation': "Monitor for potential opportunity",
                'divergence': divergence
            }
            self.divergence_alerts.append(alert)

    def _generate_report(self) -> Dict:
        """Generate complete correlation report"""
        # Sort divergence alerts by divergence magnitude
        self.divergence_alerts.sort(key=lambda x: x['divergence'], reverse=True)

        # Find strongest correlations (positive and negative)
        correlations_list = [
            (pair, corr.correlation)
            for pair, corr in self.correlation_matrix.items()
        ]

        correlations_list.sort(key=lambda x: abs(x[1]), reverse=True)

        strongest_positive = [
            (pair, corr) for pair, corr in correlations_list if corr > 0
        ][:5]

        strongest_negative = [
            (pair, corr) for pair, corr in correlations_list if corr < 0
        ][:5]

        # Export correlation matrix as DataFrame (widget expects this format)
        correlation_matrix_df = self.export_correlation_matrix_df()

        return {
            'correlation_matrix': correlation_matrix_df,  # Now returns DataFrame instead of dict
            'divergence_alerts': self.divergence_alerts,
            'strongest_positive': strongest_positive,
            'strongest_negative': strongest_negative,
            'symbols_analyzed': len(self.symbols),
            'pairs_calculated': len(self.correlation_matrix),
            'last_update': self.last_update
        }

    def _empty_result(self) -> Dict:
        """Return empty result"""
        return {
            'correlation_matrix': {},
            'divergence_alerts': [],
            'strongest_positive': [],
            'strongest_negative': [],
            'symbols_analyzed': 0,
            'pairs_calculated': 0,
            'last_update': None
        }

    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two specific symbols"""
        pair = (symbol1, symbol2)
        reverse_pair = (symbol2, symbol1)

        if pair in self.correlation_matrix:
            return self.correlation_matrix[pair].correlation
        elif reverse_pair in self.correlation_matrix:
            return self.correlation_matrix[reverse_pair].correlation
        else:
            return None

    def get_color_for_correlation(self, correlation: float) -> str:
        """
        Get color code for correlation value

        Returns:
            Color hex code
        """
        if correlation >= 0.8:
            return '#006400'  # Dark green
        elif correlation >= 0.5:
            return '#90EE90'  # Light green
        elif correlation >= 0.2:
            return '#ADFF2F'  # Yellow-green
        elif correlation >= -0.2:
            return '#808080'  # Gray
        elif correlation >= -0.5:
            return '#FFA500'  # Orange
        elif correlation >= -0.8:
            return '#FF4500'  # Red-orange
        else:
            return '#8B0000'  # Dark red

    def format_heatmap_text(self) -> str:
        """Generate formatted text for heatmap display"""
        if not self.correlation_matrix:
            return "No correlation data available"

        lines = []
        lines.append("═══ CORRELATION HEATMAP ═══\n")

        # Get unique symbols
        symbols_set = set()
        for (s1, s2) in self.correlation_matrix.keys():
            symbols_set.add(s1)
            symbols_set.add(s2)

        symbols = sorted(symbols_set)[:8]  # Limit to 8 for display

        # Create mini heatmap
        for i, sym1 in enumerate(symbols):
            line_parts = [f"{sym1:8}"]
            for j, sym2 in enumerate(symbols):
                if i == j:
                    line_parts.append("  1.00")
                elif i > j:
                    line_parts.append("      ")
                else:
                    corr = self.get_correlation(sym1, sym2)
                    if corr is not None:
                        line_parts.append(f"{corr:+6.2f}")
                    else:
                        line_parts.append("   --")

            lines.append(''.join(line_parts))

        # Add strongest correlations
        if self.correlation_matrix:
            lines.append("\n🟢 STRONGEST POSITIVE:")
            correlations_list = [
                ((s1, s2), corr.correlation)
                for (s1, s2), corr in self.correlation_matrix.items()
            ]
            correlations_list.sort(key=lambda x: x[1], reverse=True)

            for (s1, s2), corr in correlations_list[:3]:
                lines.append(f"   {s1}/{s2}: {corr:+.2f}")

            lines.append("\n🔴 STRONGEST NEGATIVE:")
            negative_corrs = [x for x in correlations_list if x[1] < 0]
            negative_corrs.sort(key=lambda x: x[1])

            for (s1, s2), corr in negative_corrs[:3]:
                lines.append(f"   {s1}/{s2}: {corr:+.2f}")

        return '\n'.join(lines)

    def format_divergence_alerts(self) -> str:
        """Format divergence alerts for display"""
        if not self.divergence_alerts:
            return "✓ No divergences detected"

        lines = []
        for alert in self.divergence_alerts[:5]:  # Top 5
            lines.append(alert['message'])
            lines.append(f"→ {alert['recommendation']}")
            lines.append("")

        return '\n'.join(lines)

    def export_correlation_matrix_df(self) -> pd.DataFrame:
        """Export correlation matrix as pandas DataFrame"""
        if not self.correlation_matrix:
            return pd.DataFrame()

        # Get unique symbols
        symbols_set = set()
        for (s1, s2) in self.correlation_matrix.keys():
            symbols_set.add(s1)
            symbols_set.add(s2)

        symbols = sorted(symbols_set)

        # Create matrix
        matrix = np.ones((len(symbols), len(symbols)))

        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i != j:
                    corr = self.get_correlation(sym1, sym2)
                    if corr is not None:
                        matrix[i, j] = corr

        df = pd.DataFrame(matrix, index=symbols, columns=symbols)
        return df

    def get_correlated_pairs(self, symbol: str,
                            threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Get all pairs that are strongly correlated with given symbol

        Args:
            symbol: Symbol to find correlations for
            threshold: Minimum correlation threshold (default 0.7)

        Returns:
            List of (symbol, correlation) tuples
        """
        correlated = []

        for (s1, s2), corr_pair in self.correlation_matrix.items():
            if s1 == symbol and abs(corr_pair.correlation) >= threshold:
                correlated.append((s2, corr_pair.correlation))
            elif s2 == symbol and abs(corr_pair.correlation) >= threshold:
                correlated.append((s1, corr_pair.correlation))

        correlated.sort(key=lambda x: abs(x[1]), reverse=True)
        return correlated


# Global instance
correlation_analyzer = MultiSymbolCorrelationAnalyzer()
