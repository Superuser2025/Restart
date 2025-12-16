"""
ML Integration Layer - Connects Python Dashboard to EA ML System

This module provides the bridge between the Python GUI and the EA's ML system.
It reads predictions from ML_Data/ directory and provides them to widgets.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MLIntegration:
    """
    Manages communication between Python dashboard and EA ML system

    Communication Flow:
    1. EA writes features to ML_Data/current_features.json
    2. ml_training_service.py writes predictions to ML_Data/prediction.json
    3. This class reads predictions and provides to widgets
    """

    def __init__(self, ml_data_dir: str = None):
        """
        Initialize ML integration

        Args:
            ml_data_dir: Path to ML_Data directory (default: ~/ML_Data)
        """
        if ml_data_dir is None:
            # Try common locations
            possible_paths = [
                Path.home() / "ML_Data",
                Path("/home/user/Restart/ML_Data"),
                Path("ML_Data"),
                Path("../ML_Data"),
            ]

            for path in possible_paths:
                if path.exists():
                    self.ml_data_dir = path
                    break
            else:
                # Use default and create if doesn't exist
                self.ml_data_dir = Path.home() / "ML_Data"
                self.ml_data_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.ml_data_dir = Path(ml_data_dir)

        logger.info(f"ML Integration using directory: {self.ml_data_dir}")

        # File paths
        self.prediction_file = self.ml_data_dir / "prediction.json"
        self.features_file = self.ml_data_dir / "current_features.json"
        self.training_data_file = self.ml_data_dir / "training_data.csv"
        self.models_dir = self.ml_data_dir / "models"

        # Create models directory if doesn't exist
        self.models_dir.mkdir(exist_ok=True)

        # Cache
        self.last_prediction = None
        self.last_features = None
        self.last_update = None

    def is_ml_service_running(self) -> bool:
        """
        Check if ML training service is running

        Returns:
            True if service is responding, False otherwise
        """
        # Check if prediction file exists and was recently modified (< 60 seconds)
        if not self.prediction_file.exists():
            return False

        modified_time = os.path.getmtime(self.prediction_file)
        age = datetime.now().timestamp() - modified_time

        return age < 60  # Service active if file modified in last minute

    def get_current_prediction(self) -> Optional[Dict[str, Any]]:
        """
        Get latest ML prediction from EA ML system

        Returns:
            Dictionary with prediction data or None if unavailable
        """
        try:
            if not self.prediction_file.exists():
                logger.warning("Prediction file not found")
                return None

            with open(self.prediction_file, 'r') as f:
                prediction = json.load(f)

            self.last_prediction = prediction
            self.last_update = datetime.now()

            return prediction

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prediction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading prediction: {e}")
            return None

    def get_current_features(self) -> Optional[Dict[str, Any]]:
        """
        Get current feature values being used for prediction

        Returns:
            Dictionary with feature data or None if unavailable
        """
        try:
            if not self.features_file.exists():
                return None

            with open(self.features_file, 'r') as f:
                features = json.load(f)

            self.last_features = features
            return features

        except Exception as e:
            logger.error(f"Error reading features: {e}")
            return None

    def get_prediction_for_widget(self, widget_type: str) -> Optional[Dict[str, Any]]:
        """
        Get ML prediction specific to a widget type

        Args:
            widget_type: Type of widget requesting prediction
                        (e.g., 'session_momentum', 'pattern_scorer', etc.)

        Returns:
            Widget-specific prediction or None
        """
        prediction = self.get_current_prediction()

        if prediction is None:
            return None

        # Extract widget-specific prediction if available
        if widget_type in prediction:
            return prediction[widget_type]

        # Return general prediction otherwise
        return {
            'probability': prediction.get('probability', 0.5),
            'confidence': prediction.get('confidence', 0.5),
            'signal': prediction.get('signal', 'NEUTRAL'),
            'reasoning': prediction.get('reasoning', 'No specific analysis available'),
        }

    def get_ml_status(self) -> Dict[str, Any]:
        """
        Get overall ML system status

        Returns:
            Dictionary with status information
        """
        service_running = self.is_ml_service_running()
        has_prediction = self.prediction_file.exists()
        has_features = self.features_file.exists()

        status = {
            'service_running': service_running,
            'prediction_available': has_prediction,
            'features_available': has_features,
            'ml_data_dir': str(self.ml_data_dir),
            'last_update': self.last_update.isoformat() if self.last_update else None,
        }

        if has_prediction:
            prediction = self.get_current_prediction()
            if prediction:
                status['current_prediction'] = {
                    'probability': prediction.get('probability', 0),
                    'confidence': prediction.get('confidence', 0),
                    'signal': prediction.get('signal', 'UNKNOWN'),
                }

        return status

    def format_confidence_display(self, confidence: float) -> tuple[str, str]:
        """
        Format confidence value for display

        Args:
            confidence: Confidence value (0.0 - 1.0)

        Returns:
            Tuple of (emoji, color) for display
        """
        if confidence >= 0.75:
            return ("🟢", "green")  # High confidence
        elif confidence >= 0.60:
            return ("🟡", "yellow")  # Medium confidence
        else:
            return ("🔴", "red")  # Low confidence

    def create_ai_suggestion(self,
                           widget_type: str,
                           suggestion_text: str,
                           confidence: float,
                           data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create standardized AI suggestion for display

        Args:
            widget_type: Type of widget
            suggestion_text: Main suggestion text
            confidence: Confidence level (0.0 - 1.0)
            data: Additional data for the suggestion

        Returns:
            Formatted suggestion dictionary
        """
        emoji, color = self.format_confidence_display(confidence)

        return {
            'widget_type': widget_type,
            'text': suggestion_text,
            'confidence': confidence,
            'confidence_pct': f"{confidence * 100:.0f}%",
            'emoji': emoji,
            'color': color,
            'timestamp': datetime.now().isoformat(),
            'data': data or {},
        }


# Global singleton instance
ml_integration = MLIntegration()


# Convenience functions for widgets
def get_ml_prediction(widget_type: str = None) -> Optional[Dict[str, Any]]:
    """Get ML prediction (widget-specific if type provided)"""
    if widget_type:
        return ml_integration.get_prediction_for_widget(widget_type)
    return ml_integration.get_current_prediction()


def is_ml_available() -> bool:
    """Check if ML system is available"""
    return ml_integration.is_ml_service_running()


def get_ml_status() -> Dict[str, Any]:
    """Get ML system status"""
    return ml_integration.get_ml_status()


def create_ai_suggestion(widget_type: str, text: str, confidence: float, data: Dict = None):
    """Create AI suggestion for widget"""
    return ml_integration.create_ai_suggestion(widget_type, text, confidence, data)
