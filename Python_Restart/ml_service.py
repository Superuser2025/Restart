#!/usr/bin/env python3
"""
ML Service - Monitors EA exports and generates trading predictions
Runs continuously in the background
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


class MLPredictionService:
    """
    ML Service that monitors EA exports and generates predictions
    """

    def __init__(self, mt5_files_dir=None):
        """
        Initialize ML service

        Args:
            mt5_files_dir: Path to MT5 Files directory
        """
        if mt5_files_dir is None:
            # Default MT5 path from user's system
            mt5_files_dir = Path(r"C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files")

        self.mt5_files_dir = Path(mt5_files_dir)
        self.ml_data_dir = self.mt5_files_dir / "ML_Data"

        # File paths
        self.market_data_file = self.ml_data_dir / "market_data.json"
        self.features_file = self.ml_data_dir / "features.json"
        self.prediction_file = self.ml_data_dir / "prediction.json"

        # Create ML_Data directory if it doesn't exist
        self.ml_data_dir.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.last_market_data_mtime = None
        self.last_features_mtime = None
        self.prediction_count = 0

        logger.info(f"ML Service initialized")
        logger.info(f"Monitoring directory: {self.ml_data_dir}")

    def check_for_new_data(self):
        """
        Check if there's new data from EA

        Returns:
            bool: True if new data available
        """
        if not self.market_data_file.exists():
            return False

        try:
            current_mtime = self.market_data_file.stat().st_mtime

            if current_mtime != self.last_market_data_mtime:
                self.last_market_data_mtime = current_mtime
                return True

        except Exception as e:
            logger.error(f"Error checking file: {e}")

        return False

    def read_market_data(self):
        """
        Read market data from EA export

        Returns:
            dict: Market data or None if error
        """
        try:
            with open(self.market_data_file, 'r') as f:
                data = json.load(f)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in market_data.json: {e}")
            return None

        except Exception as e:
            logger.error(f"Error reading market_data.json: {e}")
            return None

    def generate_prediction(self, market_data):
        """
        Generate ML prediction based on market data

        For now, this is a SIMPLE rule-based system.
        You'll replace this with actual ML models later.

        Args:
            market_data: Market data from EA

        Returns:
            dict: Prediction data
        """
        # Extract features
        symbol = market_data.get('symbol', 'UNKNOWN')
        bid = market_data.get('bid', 0)
        ask = market_data.get('ask', 0)
        spread = market_data.get('spread', 0)
        positions = market_data.get('positions_total', 0)
        account_balance = market_data.get('account_balance', 0)

        # SIMPLE LOGIC (replace with real ML later)
        # For now: approve trades if spread is reasonable
        signal = "WAIT"
        probability = 0.50
        confidence = 0.50
        reasoning = "Analyzing market conditions..."

        if spread < 2.0:  # Good spread
            signal = "ENTER"
            probability = 0.75
            confidence = 0.80
            reasoning = f"Spread is favorable ({spread:.1f} pips). Market conditions acceptable."
        elif spread < 5.0:  # Moderate spread
            signal = "WAIT"
            probability = 0.55
            confidence = 0.60
            reasoning = f"Spread is moderate ({spread:.1f} pips). Wait for better entry."
        else:  # Wide spread
            signal = "SKIP"
            probability = 0.30
            confidence = 0.70
            reasoning = f"Spread too wide ({spread:.1f} pips). Skip this setup."

        # Create prediction
        prediction = {
            'signal': signal,
            'probability': probability,
            'confidence': confidence,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'spread_analyzed': spread,
            'ml_version': '1.0_simple',
            'model_type': 'rule_based'  # Change to 'xgboost' or 'neural_net' when you add real ML
        }

        return prediction

    def write_prediction(self, prediction):
        """
        Write prediction to JSON file for EA to read

        Args:
            prediction: Prediction dictionary

        Returns:
            bool: Success status
        """
        try:
            with open(self.prediction_file, 'w') as f:
                json.dump(prediction, f, indent=2)

            self.prediction_count += 1
            return True

        except Exception as e:
            logger.error(f"Error writing prediction: {e}")
            return False

    def run_once(self):
        """
        Run one cycle of the ML service

        Returns:
            bool: True if prediction was generated
        """
        # Check for new data
        if not self.check_for_new_data():
            return False

        # Read market data
        market_data = self.read_market_data()
        if market_data is None:
            return False

        # Generate prediction
        logger.info(f"📊 Generating prediction for {market_data.get('symbol', 'UNKNOWN')}")
        prediction = self.generate_prediction(market_data)

        # Write prediction
        if self.write_prediction(prediction):
            logger.info(f"✅ Prediction #{self.prediction_count}: {prediction['signal']} "
                       f"(prob: {prediction['probability']:.2f}, conf: {prediction['confidence']:.2f})")
            logger.info(f"   Reasoning: {prediction['reasoning']}")
            return True

        return False

    def run(self, check_interval=5):
        """
        Run ML service continuously

        Args:
            check_interval: How often to check for new data (seconds)
        """
        logger.info("="*60)
        logger.info("ML PREDICTION SERVICE - STARTED")
        logger.info("="*60)
        logger.info(f"Checking for EA data every {check_interval} seconds")
        logger.info(f"Watching: {self.market_data_file}")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*60)

        try:
            while True:
                self.run_once()
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("\n" + "="*60)
            logger.info("ML Service stopped by user")
            logger.info(f"Total predictions generated: {self.prediction_count}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Fatal error in ML service: {e}")
            raise


def main():
    """Main entry point"""
    # Create and run ML service
    service = MLPredictionService()
    service.run(check_interval=5)


if __name__ == "__main__":
    main()
