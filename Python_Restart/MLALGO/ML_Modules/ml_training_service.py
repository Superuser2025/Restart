#!/usr/bin/env python3
"""
ML Training Service for Trading EA
Monitors for training data, trains models, and provides predictions
"""

import pandas as pd
import numpy as np
import json
import joblib
import time
import os
from pathlib import Path
from datetime import datetime

# ML libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import xgboost as xgb

# Configuration
DATA_DIR = Path("ML_Data")
FEATURES_FILE = DATA_DIR / "current_features.json"
PREDICTION_FILE = DATA_DIR / "prediction.json"
TRAINING_DATA_FILE = DATA_DIR / "training_data.csv"
RETRAIN_TRIGGER_FILE = DATA_DIR / "retrain_trigger.txt"
MODEL_FILE = "trading_model.pkl"
SCALER_FILE = "feature_scaler.pkl"

class MLTradingModel:
    """
    Machine learning model for trading signal prediction
    """

    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.metrics = {}

    def train(self, df, target_rr=1.5):
        """
        Train model on historical data

        Args:
            df: DataFrame with features and labels
            target_rr: Minimum R:R for positive label
        """
        print(f"\n{'='*60}")
        print(f"Training {self.model_type} model...")
        print(f"{'='*60}")

        # Prepare features
        feature_cols = [col for col in df.columns if col.startswith('feature_')]
        X = df[feature_cols].values
        y = df['label'].values

        print(f"Dataset: {len(df)} samples, {len(feature_cols)} features")
        print(f"Positive samples: {y.sum()} ({y.mean()*100:.1f}%)")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)

        # Model selection
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=20,
                min_samples_leaf=10,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                subsample=0.8,
                random_state=42
            )
        elif self.model_type == 'xgboost':
            scale_pos_weight = (y == 0).sum() / (y == 1).sum()
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                n_jobs=-1
            )

        # Cross-validation
        print("\nPerforming time-series cross-validation...")
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=tscv, scoring='roc_auc', n_jobs=-1)

        print(f"CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Train final model
        print("\nTraining final model on all data...")
        self.model.fit(X_scaled, y)

        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

            print("\nTop 10 Most Important Features:")
            print(self.feature_importance.head(10).to_string(index=False))

        # Evaluate on full dataset (just for reference)
        y_pred = self.model.predict(X_scaled)
        y_prob = self.model.predict_proba(X_scaled)[:, 1]

        print("\n" + "="*60)
        print("TRAINING SET PERFORMANCE (Reference Only)")
        print("="*60)
        print(classification_report(y, y_pred, target_names=['Loss', 'Win']))
        print(f"ROC-AUC: {roc_auc_score(y, y_prob):.4f}")

        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        print("\nConfusion Matrix:")
        print(f"TN: {cm[0,0]:4d}  FP: {cm[0,1]:4d}")
        print(f"FN: {cm[1,0]:4d}  TP: {cm[1,1]:4d}")

        # Store metrics
        self.metrics = {
            'cv_roc_auc_mean': cv_scores.mean(),
            'cv_roc_auc_std': cv_scores.std(),
            'train_roc_auc': roc_auc_score(y, y_prob),
            'trained_at': datetime.now().isoformat()
        }

        # Save model and scaler
        self.save()

        print(f"\n{'='*60}")
        print("Training Complete!")
        print(f"{'='*60}\n")

        return self.model

    def predict_probability(self, features):
        """
        Predict probability of profitable trade

        Args:
            features: List or array of 80 features

        Returns:
            dict with probability, confidence, and signal
        """
        if self.model is None:
            self.load()

        # Ensure features is 2D array
        features = np.array(features).reshape(1, -1)

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Get prediction
        probability = self.model.predict_proba(features_scaled)[0][1]

        # Calculate confidence (distance from 0.5)
        confidence = abs(probability - 0.5) * 2  # 0 to 1 scale

        # Determine signal
        if probability >= 0.6 and confidence >= 0.5:
            signal = "ENTER"
        elif probability >= 0.5:
            signal = "WAIT"
        else:
            signal = "SKIP"

        return {
            'probability': float(probability),
            'confidence': float(confidence),
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        }

    def save(self):
        """Save model and scaler to disk"""
        joblib.dump(self.model, MODEL_FILE)
        joblib.dump(self.scaler, SCALER_FILE)
        print(f"Model saved to {MODEL_FILE}")
        print(f"Scaler saved to {SCALER_FILE}")

        # Save feature importance
        if self.feature_importance is not None:
            self.feature_importance.to_csv(DATA_DIR / 'feature_importance.csv', index=False)

    def load(self):
        """Load model and scaler from disk"""
        if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
            self.model = joblib.load(MODEL_FILE)
            self.scaler = joblib.load(SCALER_FILE)
            print("Model and scaler loaded successfully")
            return True
        else:
            print("WARNING: Model files not found")
            return False


class PredictionServer:
    """
    Service that monitors for prediction requests and responds
    """

    def __init__(self, model):
        self.model = model
        self.prediction_count = 0

    def run(self):
        """
        Main loop: monitor for feature requests and provide predictions
        """
        print(f"\n{'='*60}")
        print("ML Prediction Server Started")
        print(f"{'='*60}")
        print(f"Monitoring: {FEATURES_FILE}")
        print(f"Predictions: {PREDICTION_FILE}")
        print("Waiting for requests...\n")

        last_modified_time = 0

        while True:
            try:
                # Check if features file exists and has been updated
                if FEATURES_FILE.exists():
                    current_modified_time = FEATURES_FILE.stat().st_mtime

                    if current_modified_time > last_modified_time:
                        # New request received
                        with open(FEATURES_FILE, 'r') as f:
                            data = json.load(f)

                        features = data['features']

                        # Get prediction
                        prediction = self.model.predict_probability(features)

                        # Write prediction
                        with open(PREDICTION_FILE, 'w') as f:
                            json.dump(prediction, f, indent=2)

                        self.prediction_count += 1
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"Prediction #{self.prediction_count}: "
                              f"P={prediction['probability']:.3f} "
                              f"C={prediction['confidence']:.3f} "
                              f"Signal={prediction['signal']}")

                        last_modified_time = current_modified_time

                # Check for retrain trigger
                if RETRAIN_TRIGGER_FILE.exists():
                    print("\n" + "!"*60)
                    print("RETRAIN TRIGGER DETECTED")
                    print("!"*60)

                    # Load new data and retrain
                    if TRAINING_DATA_FILE.exists():
                        df = pd.read_csv(TRAINING_DATA_FILE)
                        self.model.train(df)

                    # Remove trigger file
                    RETRAIN_TRIGGER_FILE.unlink()

                    print("Resuming prediction service...\n")

                time.sleep(0.1)  # Check every 100ms

            except KeyboardInterrupt:
                print("\nShutting down prediction server...")
                break
            except Exception as e:
                print(f"ERROR: {e}")
                time.sleep(1)


def initial_training():
    """
    Perform initial training if training data exists
    """
    if not TRAINING_DATA_FILE.exists():
        print(f"No training data found at {TRAINING_DATA_FILE}")
        print("Waiting for data collection...")
        return None

    print(f"Loading training data from {TRAINING_DATA_FILE}...")
    df = pd.read_csv(TRAINING_DATA_FILE)

    # Create and train model
    model = MLTradingModel(model_type='xgboost')  # Can change to 'random_forest' or 'gradient_boosting'
    model.train(df)

    return model


def main():
    """
    Main entry point
    """
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        ML TRADING SERVICE - Real Machine Learning             ║
    ║        Developed for Institutional Trading Robot v3           ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)

    # Initial training or load existing model
    model = MLTradingModel()

    if os.path.exists(MODEL_FILE):
        print("Loading existing model...")
        model.load()
    else:
        print("No existing model found. Performing initial training...")
        model = initial_training()

        if model is None:
            print("\nStarting in data collection mode...")
            print("Model will be trained once sufficient data is collected.")
            model = MLTradingModel()
            # Create a dummy neutral model for now
            print("Using neutral predictions until first training...")

    # Start prediction server
    server = PredictionServer(model)
    server.run()


if __name__ == "__main__":
    main()
