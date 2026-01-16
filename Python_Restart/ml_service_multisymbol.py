#!/usr/bin/env python3
"""
Multi-Symbol ML Service - Enterprise Grade
Monitors 10 symbols, generates predictions for all, EA reads its symbol's prediction
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 module not available - install with: pip install MetaTrader5")


class MultiSymbolMLService:
    """
    Advanced ML Service - Monitors all symbols, generates predictions for all
    """

    def __init__(self, mt5_files_dir=None):
        """Initialize multi-symbol ML service"""

        # MT5 Files directory
        if mt5_files_dir is None:
            mt5_files_dir = Path(r"C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files")

        self.mt5_files_dir = Path(mt5_files_dir)
        self.ml_data_dir = self.mt5_files_dir / "ML_Data"

        # Create directory
        self.ml_data_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.prediction_file = self.ml_data_dir / "prediction.json"

        # Symbols to monitor (same as Python GUI)
        self.symbols = [
            "USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD",
            "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "AUDJPY"
        ]

        # Timeframes
        self.timeframes = {
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4
        }

        # Tracking
        self.prediction_count = 0
        self.mt5_connected = False

        logger.info("Multi-Symbol ML Service initialized")
        logger.info(f"Monitoring {len(self.symbols)} symbols")
        logger.info(f"Output directory: {self.ml_data_dir}")

    def connect_mt5(self):
        """Connect to MT5"""
        if not MT5_AVAILABLE:
            logger.error("MT5 module not available!")
            return False

        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return False

        self.mt5_connected = True
        logger.info("✓ Connected to MT5")
        return True

    def get_symbol_data(self, symbol, timeframe_name='H4', bars=100):
        """
        Get market data for a symbol

        Args:
            symbol: Symbol name
            timeframe_name: Timeframe (M5, M15, M30, H1, H4)
            bars: Number of bars

        Returns:
            dict: Symbol data or None
        """
        if not self.mt5_connected:
            return None

        try:
            # Get rates
            timeframe = self.timeframes.get(timeframe_name, mt5.TIMEFRAME_H4)
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

            if rates is None or len(rates) == 0:
                return None

            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None

            # Calculate spread
            spread = (tick.ask - tick.bid) / tick.bid * 10000  # in pips

            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None

            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': spread,
                'last': tick.last,
                'volume': tick.volume,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'bars': len(rates),
                'last_close': rates[-1]['close'],
                'last_high': rates[-1]['high'],
                'last_low': rates[-1]['low']
            }

        except Exception as e:
            logger.error(f"Error getting data for {symbol}: {e}")
            return None

    def generate_prediction(self, symbol_data):
        """
        Generate ML prediction for a symbol

        Args:
            symbol_data: Symbol market data

        Returns:
            dict: Prediction
        """
        if symbol_data is None:
            return {
                'signal': 'WAIT',
                'probability': 0.50,
                'confidence': 0.50,
                'reasoning': 'No data available'
            }

        symbol = symbol_data['symbol']
        spread = symbol_data['spread']

        # ENHANCED ML LOGIC (still simple, but better than before)
        # You'll replace this with real ML models later

        signal = "WAIT"
        probability = 0.50
        confidence = 0.50
        reasoning = "Analyzing market conditions..."

        # Rule 1: Spread analysis
        if spread < 1.0:  # Excellent spread
            signal = "ENTER"
            probability = 0.80
            confidence = 0.85
            reasoning = f"Excellent spread ({spread:.2f} pips). Strong entry signal."
        elif spread < 2.0:  # Good spread
            signal = "ENTER"
            probability = 0.75
            confidence = 0.80
            reasoning = f"Good spread ({spread:.2f} pips). Favorable conditions."
        elif spread < 5.0:  # Moderate spread
            signal = "WAIT"
            probability = 0.55
            confidence = 0.60
            reasoning = f"Moderate spread ({spread:.2f} pips). Wait for better entry."
        else:  # Wide spread
            signal = "SKIP"
            probability = 0.30
            confidence = 0.70
            reasoning = f"Spread too wide ({spread:.2f} pips). Skip this setup."

        return {
            'signal': signal,
            'probability': probability,
            'confidence': confidence,
            'reasoning': reasoning,
            'spread_analyzed': spread,
            'timestamp': datetime.now().isoformat()
        }

    def generate_all_predictions(self):
        """
        Generate predictions for all symbols

        Returns:
            dict: Predictions for all symbols
        """
        predictions = {}

        for symbol in self.symbols:
            # Get symbol data
            symbol_data = self.get_symbol_data(symbol)

            # Generate prediction
            prediction = self.generate_prediction(symbol_data)

            predictions[symbol] = prediction

            # Log
            logger.info(f"📊 {symbol}: {prediction['signal']} (prob: {prediction['probability']:.2f}, spread: {prediction.get('spread_analyzed', 0):.1f} pips)")

        return predictions

    def write_predictions(self, predictions):
        """
        Write multi-symbol predictions to JSON

        Args:
            predictions: Dictionary of predictions by symbol

        Returns:
            bool: Success
        """
        try:
            output = {
                'timestamp': datetime.now().isoformat(),
                'ml_version': '2.0_multi_symbol',
                'model_type': 'rule_based_enhanced',
                'symbols': predictions
            }

            with open(self.prediction_file, 'w') as f:
                json.dump(output, f, indent=2)

            self.prediction_count += 1
            return True

        except Exception as e:
            logger.error(f"Error writing predictions: {e}")
            return False

    def run_once(self):
        """Run one cycle of ML predictions"""

        # Generate predictions for all symbols
        logger.info("="*60)
        logger.info(f"Generating predictions for {len(self.symbols)} symbols...")
        logger.info("="*60)

        predictions = self.generate_all_predictions()

        # Write to file
        if self.write_predictions(predictions):
            logger.info("="*60)
            logger.info(f"✅ Batch #{self.prediction_count} - All predictions written")
            logger.info("="*60)
            return True

        return False

    def run(self, check_interval=10):
        """
        Run ML service continuously

        Args:
            check_interval: Seconds between prediction updates
        """
        logger.info("="*70)
        logger.info("MULTI-SYMBOL ML PREDICTION SERVICE - STARTED")
        logger.info("="*70)
        logger.info(f"Monitoring {len(self.symbols)} symbols: {', '.join(self.symbols)}")
        logger.info(f"Prediction interval: {check_interval} seconds")
        logger.info(f"Output file: {self.prediction_file}")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*70)

        # Connect to MT5
        if not self.connect_mt5():
            logger.error("Failed to connect to MT5!")
            return

        try:
            while True:
                self.run_once()
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("\n" + "="*70)
            logger.info("Multi-Symbol ML Service stopped by user")
            logger.info(f"Total prediction batches: {self.prediction_count}")
            logger.info("="*70)

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            raise

        finally:
            if self.mt5_connected:
                mt5.shutdown()
                logger.info("MT5 connection closed")


def main():
    """Main entry point"""
    service = MultiSymbolMLService()
    service.run(check_interval=10)


if __name__ == "__main__":
    main()
