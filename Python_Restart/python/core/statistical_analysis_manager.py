"""
AppleTrader Pro - Statistical Analysis Manager
Master controller for all probability and statistics calculations

This module provides:
- Global enable/disable for statistical analysis
- Timeframe-specific calculators
- Integration with existing trading system
- Surgical enhancement without breaking existing functionality
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from core.verbose_mode_manager import vprint


@dataclass
class StatisticalConfig:
    """Statistical analysis configuration"""
    enabled: bool = True  # Master switch
    show_chart_overlay: bool = True  # Chart overlay toggle
    selected_timeframe: str = "H4"  # Current timeframe
    use_expected_value: bool = True
    use_kelly_criterion: bool = True
    use_bayesian_learning: bool = True
    use_confidence_intervals: bool = True
    use_probabilistic_confluence: bool = True

    # Risk parameters
    max_kelly_fraction: float = 0.25  # Cap Kelly at 25%
    use_half_kelly: bool = True  # Conservative Kelly

    # Bayesian parameters
    bayesian_prior_alpha: int = 10
    bayesian_prior_beta: int = 10

    # Confidence interval parameters
    confidence_level: float = 0.95  # 95% CI


class StatisticalAnalysisManager:
    """
    Master controller for statistical analysis system

    Features:
    - Global enable/disable (Requirement #6)
    - Timeframe-specific calculations (Requirement #2)
    - Non-destructive integration (Requirement #5)
    - Chart overlay control (Requirement #3)
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - only one manager instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get singleton instance (alternative to calling constructor)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = StatisticalConfig()
        self.config_file = Path(__file__).parent.parent / "config" / "statistical_analysis.json"

        # Timeframe-specific calculators (lazy loaded)
        self.calculators: Dict[str, Any] = {}

        # Historical data storage
        self.data_file = Path(__file__).parent.parent / "config" / "statistical_data.json"
        self.historical_data: Dict[str, Any] = {}

        # Load configuration
        self._load_config()
        self._load_historical_data()

        self._initialized = True
        vprint("[StatisticsManager] ✓ Initialized")

    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Update config with saved values
                    for key, value in data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
                vprint(f"[StatisticsManager] Loaded config: enabled={self.config.enabled}")
        except Exception as e:
            vprint(f"[StatisticsManager] Could not load config: {e}")

    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            vprint("[StatisticsManager] Config saved")
        except Exception as e:
            vprint(f"[StatisticsManager] Could not save config: {e}")

    def _load_historical_data(self):
        """Load historical data for all timeframes"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    self.historical_data = json.load(f)
                vprint(f"[StatisticsManager] Loaded historical data")
        except Exception as e:
            vprint(f"[StatisticsManager] Could not load historical data: {e}")
            self.historical_data = self._create_empty_data_structure()

    def _create_empty_data_structure(self) -> Dict:
        """Create empty data structure for all timeframes"""
        timeframes = ['M15', 'H1', 'H4', 'D1']
        data = {}

        for tf in timeframes:
            data[tf] = {
                'trades': [],  # List of historical trades
                'patterns': {},  # Pattern-specific statistics
                'bayesian_priors': {},  # Bayesian learning data
                'kelly_calculations': {},  # Kelly criterion history
                'ev_calculations': {}  # Expected value history
            }

        return data

    def _save_historical_data(self):
        """Save historical data to file"""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
            vprint("[StatisticsManager] Historical data saved")
        except Exception as e:
            vprint(f"[StatisticsManager] Could not save historical data: {e}")

    # ==================== MASTER SWITCH ====================

    def is_enabled(self) -> bool:
        """Check if statistical analysis is enabled (Requirement #6)"""
        return self.config.enabled

    def enable(self):
        """Enable statistical analysis"""
        self.config.enabled = True
        self._save_config()
        vprint("[StatisticsManager] ✓ Statistical analysis ENABLED")

    def disable(self):
        """Disable statistical analysis (Requirement #6 - layman mode)"""
        self.config.enabled = False
        self._save_config()
        vprint("[StatisticsManager] ✗ Statistical analysis DISABLED (layman mode)")

    def toggle(self):
        """Toggle statistical analysis on/off"""
        if self.config.enabled:
            self.disable()
        else:
            self.enable()

    # ==================== CHART OVERLAY CONTROL ====================

    def is_chart_overlay_enabled(self) -> bool:
        """Check if chart overlay is enabled (Requirement #3)"""
        return self.config.enabled and self.config.show_chart_overlay

    def enable_chart_overlay(self):
        """Enable chart overlay"""
        self.config.show_chart_overlay = True
        self._save_config()
        vprint("[StatisticsManager] ✓ Chart overlay ENABLED")

    def disable_chart_overlay(self):
        """Disable chart overlay"""
        self.config.show_chart_overlay = False
        self._save_config()
        vprint("[StatisticsManager] ✗ Chart overlay DISABLED")

    def toggle_chart_overlay(self):
        """Toggle chart overlay on/off"""
        if self.config.show_chart_overlay:
            self.disable_chart_overlay()
        else:
            self.enable_chart_overlay()

    # ==================== TIMEFRAME MANAGEMENT ====================

    def get_selected_timeframe(self) -> str:
        """Get currently selected timeframe (Requirement #2)"""
        return self.config.selected_timeframe

    def set_timeframe(self, timeframe: str):
        """Set current timeframe for analysis"""
        if timeframe in ['M15', 'H1', 'H4', 'D1']:
            self.config.selected_timeframe = timeframe
            self._save_config()
            vprint(f"[StatisticsManager] Timeframe set to {timeframe}")
        else:
            vprint(f"[StatisticsManager] Invalid timeframe: {timeframe}")

    # ==================== DATA MANAGEMENT ====================

    def get_timeframe_data(self, timeframe: str) -> Dict:
        """Get historical data for specific timeframe"""
        if timeframe not in self.historical_data:
            self.historical_data[timeframe] = {
                'trades': [],
                'patterns': {},
                'bayesian_priors': {},
                'kelly_calculations': {},
                'ev_calculations': {}
            }
        return self.historical_data[timeframe]

    def add_trade_result(self, timeframe: str, trade_data: Dict):
        """
        Record trade result for statistical learning

        trade_data should contain:
        - symbol: str
        - pattern: str
        - outcome: 'win' or 'loss'
        - r_multiple: float (e.g., 2.5 for 2.5R win, -1.0 for 1R loss)
        - timestamp: str
        """
        tf_data = self.get_timeframe_data(timeframe)
        tf_data['trades'].append(trade_data)

        # Update pattern statistics
        pattern = trade_data.get('pattern', 'Unknown')
        if pattern not in tf_data['patterns']:
            tf_data['patterns'][pattern] = {
                'wins': 0,
                'losses': 0,
                'total_r': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }

        pattern_stats = tf_data['patterns'][pattern]
        r_multiple = trade_data.get('r_multiple', 0.0)

        if trade_data.get('outcome') == 'win':
            pattern_stats['wins'] += 1
            pattern_stats['total_r'] += r_multiple
            # Update avg_win
            wins = pattern_stats['wins']
            pattern_stats['avg_win'] = (pattern_stats['avg_win'] * (wins - 1) + r_multiple) / wins
        else:
            pattern_stats['losses'] += 1
            pattern_stats['total_r'] += r_multiple
            # Update avg_loss
            losses = pattern_stats['losses']
            pattern_stats['avg_loss'] = (pattern_stats['avg_loss'] * (losses - 1) + abs(r_multiple)) / losses

        self._save_historical_data()
        vprint(f"[StatisticsManager] Trade recorded: {timeframe} {pattern} {trade_data.get('outcome')}")

    def get_pattern_statistics(self, timeframe: str, pattern: str) -> Optional[Dict]:
        """Get statistics for specific pattern and timeframe"""
        tf_data = self.get_timeframe_data(timeframe)
        return tf_data['patterns'].get(pattern)

    def get_all_patterns(self, timeframe: str) -> Dict:
        """Get all pattern statistics for timeframe"""
        tf_data = self.get_timeframe_data(timeframe)
        return tf_data['patterns']

    # ==================== CALCULATOR ACCESS ====================

    def get_calculator(self, timeframe: str, calculator_type: str):
        """Get calculator instance for specific timeframe (lazy loading)"""
        key = f"{timeframe}_{calculator_type}"

        if key not in self.calculators:
            # Lazy load calculator when needed
            if calculator_type == 'ev':
                from core.expected_value_calculator import ExpectedValueCalculator
                self.calculators[key] = ExpectedValueCalculator(self, timeframe)
            elif calculator_type == 'kelly':
                from core.kelly_criterion_calculator import KellyCriterionCalculator
                self.calculators[key] = KellyCriterionCalculator(self, timeframe)
            elif calculator_type == 'bayesian':
                from core.bayesian_pattern_learner import BayesianPatternLearner
                self.calculators[key] = BayesianPatternLearner(self, timeframe)
            elif calculator_type == 'confidence':
                from core.confidence_interval_analyzer import ConfidenceIntervalAnalyzer
                self.calculators[key] = ConfidenceIntervalAnalyzer(self, timeframe)
            elif calculator_type == 'confluence':
                from core.probabilistic_confluence_calculator import ProbabilisticConfluenceCalculator
                self.calculators[key] = ProbabilisticConfluenceCalculator(self, timeframe)

        return self.calculators.get(key)

    # ==================== INTEGRATION HELPERS ====================

    def get_enhanced_score(self, timeframe: str, opportunity: Dict) -> Optional[float]:
        """
        Get statistically enhanced score for opportunity (Requirement #5)

        Returns None if statistics disabled (falls back to traditional scoring)
        """
        if not self.is_enabled():
            return None  # Use traditional scoring

        # Calculate statistical score
        ev_calc = self.get_calculator(timeframe, 'ev')
        if ev_calc and self.config.use_expected_value:
            ev_score = ev_calc.calculate(opportunity)
            return ev_score

        return None

    def get_optimal_position_size(self, timeframe: str, opportunity: Dict, base_risk: float) -> Optional[float]:
        """
        Get Kelly-optimized position size (Requirement #5)

        Returns None if statistics disabled (falls back to traditional sizing)
        """
        if not self.is_enabled() or not self.config.use_kelly_criterion:
            return None  # Use traditional fixed % risk

        kelly_calc = self.get_calculator(timeframe, 'kelly')
        if kelly_calc:
            return kelly_calc.calculate_position_size(opportunity, base_risk)

        return None

    def record_pattern_outcome(self, timeframe: str, pattern: str, is_win: bool, profit: float = 0.0):
        """
        Record a trade outcome for pattern learning

        Args:
            timeframe: Timeframe (M15, H1, H4, D1)
            pattern: Pattern name (e.g., 'Bullish_Engulfing')
            is_win: True if trade won, False if lost
            profit: Profit amount (for EV calculation)
        """
        tf_data = self.get_timeframe_data(timeframe)

        # Initialize pattern stats if not exists
        if pattern not in tf_data['patterns']:
            tf_data['patterns'][pattern] = {
                'wins': 0,
                'losses': 0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'trade_count': 0
            }

        pattern_stats = tf_data['patterns'][pattern]

        # Update counts
        pattern_stats['trade_count'] += 1

        if is_win:
            pattern_stats['wins'] += 1
            pattern_stats['total_profit'] += profit
        else:
            pattern_stats['losses'] += 1
            pattern_stats['total_loss'] += abs(profit)

        # Save updated data
        self.save_data()

        vprint(f"[StatsManager] Recorded outcome for {pattern} on {timeframe}: {'WIN' if is_win else 'LOSS'} | P&L: {profit:+.2f}")
        vprint(f"[StatsManager]   Updated stats: {pattern_stats['wins']}W / {pattern_stats['losses']}L = {pattern_stats['wins']/(pattern_stats['wins']+pattern_stats['losses'])*100:.1f}% win rate")

# Singleton instance
statistical_analysis_manager = StatisticalAnalysisManager()
