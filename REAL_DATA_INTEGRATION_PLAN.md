# AppleTrader Pro - Real Data Integration & SQL Implementation Plan

**Date:** December 17, 2025
**Status:** Ready for Implementation
**Current Branch:** `claude/fix-ea-ai-ml-nuyBz`

---

## 📊 Executive Summary

This document outlines the complete plan for transitioning AppleTrader Pro from demo mode to real data integration, including SQL database implementation for ML/AI training.

### Current Status:
- ✅ **11/11 Widgets** have AI integration complete
- ✅ **Demo/Live Mode** infrastructure exists
- ✅ **MT5 Connector** ready for real-time data
- ❌ **SQL Database** NOT implemented (planned but not built)
- ❌ **Trade Tracking** NOT implemented
- ❌ **ML Training Pipeline** NOT implemented

### Immediate Goals:
1. **Enable Live Mode** (Today) - Switch from demo to real MT5 data
2. **Build SQL Infrastructure** (This week) - Persistent storage for trade tracking
3. **Implement ML Training** (Next week) - Self-learning AI based on YOUR trades

---

## 🎯 Three-Phase Implementation Plan

### **Phase 1: Enable Live Mode (Today - 30 minutes)**

**Objective:** Get real MT5 market data flowing to all widgets immediately

**Prerequisites:**
- MT5 Expert Advisor must be running
- EA must be writing to: `%APPDATA%\MetaQuotes\Terminal\Common\Files\AppleTrader\market_data.json`
- Python application must have read access to MT5 data directory

**Implementation Steps:**

1. **Verify MT5 Connection**
   ```python
   # Check if MT5 EA is writing data
   # Location: core/mt5_connector.py
   mt5_connector.is_connection_active()  # Should return True
   ```

2. **Toggle Demo Mode OFF**
   ```python
   # Location: core/demo_mode_manager.py:29
   demo_mode_manager.demo_mode = False
   # OR via UI toggle (if implemented)
   ```

3. **Verify Widgets Switch to Live Data**
   - Dashboard Cards → Real account balance, P&L
   - Opportunity Scanner → Real pattern detections
   - Correlation Heatmap → Real symbol correlations
   - All 11 widgets → Live market data

**Files Modified:**
- None (infrastructure already exists)

**Testing:**
- Compare prices in widgets to MT5 terminal
- Verify account balance matches MT5
- Confirm opportunity cards use real patterns (not demo)

**Limitations:**
- ⚠️ No persistent storage (data lost on restart)
- ⚠️ No historical tracking
- ⚠️ ML cannot train on YOUR trades

---

### **Phase 2: SQL Database Infrastructure (Week 1 - 5-7 days)**

**Objective:** Build persistent storage for opportunities, trades, and ML training data

#### **2.1 Database Schema**

**File:** `python/database/schema.sql`

```sql
-- ============================================
-- OPPORTUNITIES TABLE
-- Stores every opportunity detected by scanner
-- ============================================
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    pattern_type VARCHAR(50),
    setup_type VARCHAR(50),

    -- Entry details
    entry_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),
    risk_reward DECIMAL(5,2),

    -- Quality metrics
    quality_score DECIMAL(5,2),
    pattern_strength DECIMAL(5,2),
    confidence DECIMAL(5,2),

    -- Market context (50+ features for ML)
    trend VARCHAR(20),
    volatility VARCHAR(20),
    session VARCHAR(20),
    atr_14 DECIMAL(10,5),
    rsi_14 DECIMAL(5,2),
    volume_ratio DECIMAL(5,2),

    -- Multi-timeframe
    h4_trend VARCHAR(20),
    h1_trend VARCHAR(20),
    m15_trend VARCHAR(20),

    -- Key level flags
    at_fvg BOOLEAN DEFAULT 0,
    at_order_block BOOLEAN DEFAULT 0,
    at_support_resistance BOOLEAN DEFAULT 0,

    -- Correlation
    has_divergence BOOLEAN DEFAULT 0,
    divergence_pair VARCHAR(10),

    -- News calendar
    news_in_5min BOOLEAN DEFAULT 0,
    upcoming_event VARCHAR(100),

    -- Source widget
    detected_by VARCHAR(50),

    UNIQUE(symbol, timestamp, pattern_type)
);

-- ============================================
-- TRADES TABLE
-- Stores user actions and trade results
-- ============================================
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER,

    -- User action
    user_action VARCHAR(10) NOT NULL,  -- 'TAKE', 'SKIP', 'MANUAL'
    action_timestamp DATETIME NOT NULL,

    -- Execution details
    actual_entry DECIMAL(10,5),
    actual_sl DECIMAL(10,5),
    actual_tp DECIMAL(10,5),
    lot_size DECIMAL(5,2),

    -- Trade result
    exit_price DECIMAL(10,5),
    exit_timestamp DATETIME,
    outcome VARCHAR(10),  -- 'WIN', 'LOSS', 'BE', 'OPEN'
    profit_loss DECIMAL(10,2),
    r_multiple DECIMAL(5,2),

    -- Position tracking
    mt5_ticket INTEGER,
    is_closed BOOLEAN DEFAULT 0,

    -- Performance
    holding_time_minutes INTEGER,
    slippage_pips DECIMAL(5,2),

    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

-- ============================================
-- PERFORMANCE_METRICS TABLE
-- Aggregated performance over time
-- ============================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10),  -- 'DAILY', 'WEEKLY', 'MONTHLY'

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    breakeven INTEGER DEFAULT 0,

    -- Performance metrics
    win_rate DECIMAL(5,4),
    avg_win DECIMAL(10,2),
    avg_loss DECIMAL(10,2),
    profit_factor DECIMAL(5,2),
    expectancy DECIMAL(10,2),

    -- Risk metrics
    sharpe_ratio DECIMAL(5,4),
    max_drawdown DECIMAL(5,4),
    total_profit DECIMAL(10,2),

    -- R-multiples
    avg_r_multiple DECIMAL(5,2),
    best_r_multiple DECIMAL(5,2),
    worst_r_multiple DECIMAL(5,2),

    UNIQUE(start_date, end_date, period_type)
);

-- ============================================
-- ML_TRAINING_DATA TABLE
-- Labeled data for ML model training
-- ============================================
CREATE TABLE IF NOT EXISTS ml_training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,

    -- Label (target variable)
    label INTEGER NOT NULL,  -- 1 = WIN, 0 = LOSS

    -- All features (copy from opportunities + trades)
    features JSON NOT NULL,

    -- Training metadata
    created_at DATETIME NOT NULL,
    used_in_training BOOLEAN DEFAULT 0,
    model_version VARCHAR(20),

    FOREIGN KEY (trade_id) REFERENCES trades(id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp);
CREATE INDEX IF NOT EXISTS idx_opportunities_symbol ON opportunities(symbol);
CREATE INDEX IF NOT EXISTS idx_opportunities_quality ON opportunities(quality_score);

CREATE INDEX IF NOT EXISTS idx_trades_outcome ON trades(outcome);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(action_timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_opportunity ON trades(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_performance_period ON performance_metrics(start_date, end_date);
```

#### **2.2 Trade Tracker Implementation**

**File:** `python/database/trade_tracker.py`

```python
"""
AppleTrader Pro - Trade Tracking Database Layer
Persistent storage for opportunities, trades, and ML training data
"""

import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


class TradeTracker:
    """
    Manages persistent storage of trading opportunities and results

    Responsibilities:
    1. Log every opportunity from scanner
    2. Track user actions (Take/Skip)
    3. Record trade outcomes (Win/Loss/BE)
    4. Calculate performance metrics
    5. Generate ML training datasets
    """

    def __init__(self, db_path: str = "apple_trader_data.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Create database schema"""
        schema_file = Path(__file__).parent / "schema.sql"

        if schema_file.exists():
            with open(schema_file, 'r') as f:
                schema = f.read()
            self.conn.executescript(schema)
        else:
            # Fallback: Create tables inline
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    timeframe VARCHAR(5) NOT NULL,
                    pattern_type VARCHAR(50),
                    quality_score DECIMAL(5,2),
                    entry_price DECIMAL(10,5),
                    stop_loss DECIMAL(10,5),
                    take_profit DECIMAL(10,5),
                    risk_reward DECIMAL(5,2),
                    confidence DECIMAL(5,2)
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_id INTEGER,
                    user_action VARCHAR(10) NOT NULL,
                    action_timestamp DATETIME NOT NULL,
                    actual_entry DECIMAL(10,5),
                    outcome VARCHAR(10),
                    profit_loss DECIMAL(10,2),
                    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
                );
            """)

        self.conn.commit()

    # ================================================
    # OPPORTUNITY LOGGING
    # ================================================

    def log_opportunity(self, opportunity: Dict) -> int:
        """
        Log a trading opportunity from scanner

        Args:
            opportunity: Opportunity dict from OpportunityScanner

        Returns:
            opportunity_id: Database ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO opportunities (
                timestamp, symbol, timeframe, pattern_type,
                entry_price, stop_loss, take_profit, risk_reward,
                quality_score, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            opportunity.get('symbol', 'UNKNOWN'),
            opportunity.get('timeframe', 'M15'),
            opportunity.get('pattern', 'UNKNOWN'),
            opportunity.get('entry', 0.0),
            opportunity.get('stop_loss', 0.0),
            opportunity.get('take_profit', 0.0),
            opportunity.get('risk_reward', 0.0),
            opportunity.get('quality_score', 0.0),
            opportunity.get('confidence', 0.0)
        ))

        self.conn.commit()
        return cursor.lastrowid

    # ================================================
    # TRADE TRACKING
    # ================================================

    def log_user_action(self, opportunity_id: int, action: str) -> int:
        """
        Log user action on opportunity (TAKE or SKIP)

        Args:
            opportunity_id: Database ID of opportunity
            action: 'TAKE' or 'SKIP'

        Returns:
            trade_id: Database ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                opportunity_id, user_action, action_timestamp, outcome
            ) VALUES (?, ?, ?, ?)
        """, (
            opportunity_id,
            action,
            datetime.now(),
            'PENDING' if action == 'TAKE' else 'SKIPPED'
        ))

        self.conn.commit()
        return cursor.lastrowid

    def log_trade_result(self, trade_id: int, result: Dict):
        """
        Update trade with final result

        Args:
            trade_id: Database ID of trade
            result: {
                'actual_entry': float,
                'exit_price': float,
                'outcome': 'WIN'/'LOSS'/'BE',
                'profit_loss': float
            }
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE trades
            SET actual_entry = ?,
                outcome = ?,
                profit_loss = ?
            WHERE id = ?
        """, (
            result.get('actual_entry', 0.0),
            result.get('outcome', 'UNKNOWN'),
            result.get('profit_loss', 0.0),
            trade_id
        ))

        self.conn.commit()

    # ================================================
    # PERFORMANCE METRICS
    # ================================================

    def calculate_performance_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate performance metrics for date range

        Returns:
            {
                'total_trades': int,
                'win_rate': float,
                'profit_factor': float,
                'avg_r_multiple': float,
                'expectancy': float
            }
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                AVG(CASE WHEN outcome = 'WIN' THEN profit_loss ELSE NULL END) as avg_win,
                AVG(CASE WHEN outcome = 'LOSS' THEN ABS(profit_loss) ELSE NULL END) as avg_loss,
                SUM(profit_loss) as total_profit
            FROM trades
            WHERE action_timestamp BETWEEN ? AND ?
                AND outcome IN ('WIN', 'LOSS', 'BE')
        """, (start_date, end_date))

        row = cursor.fetchone()

        total_trades = row['total_trades'] or 0
        wins = row['wins'] or 0
        losses = row['losses'] or 0
        avg_win = row['avg_win'] or 0
        avg_loss = row['avg_loss'] or 1  # Avoid division by zero
        total_profit = row['total_profit'] or 0

        win_rate = wins / total_trades if total_trades > 0 else 0
        profit_factor = (wins * avg_win) / (losses * avg_loss) if losses > 0 else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        return {
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'total_profit': total_profit
        }

    # ================================================
    # ML TRAINING DATA
    # ================================================

    def get_opportunities_for_training(self) -> List[Tuple[Dict, int]]:
        """
        Get labeled opportunities for ML training

        Returns:
            [(features_dict, label), ...]
            label: 1 = WIN, 0 = LOSS
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                o.*,
                t.outcome
            FROM opportunities o
            INNER JOIN trades t ON o.id = t.opportunity_id
            WHERE t.outcome IN ('WIN', 'LOSS')
        """)

        training_data = []

        for row in cursor.fetchall():
            features = dict(row)
            outcome = features.pop('outcome')
            label = 1 if outcome == 'WIN' else 0

            training_data.append((features, label))

        return training_data

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Global singleton
trade_tracker = TradeTracker()
```

#### **2.3 Widget Integration - Add "Take Trade" / "Skip" Buttons**

**File:** `python/widgets/opportunity_scanner_widget.py`

**Changes Required:**

```python
# In OpportunityCard class (around line 50)

def __init__(self, opportunity: Dict, parent=None):
    super().__init__(parent)
    self.opportunity = opportunity
    self.opportunity_id = None  # Database ID

    # ... existing UI code ...

    # ADD: Action buttons
    button_layout = QHBoxLayout()

    self.take_button = QPushButton("✓ Take Trade")
    self.take_button.setStyleSheet("""
        QPushButton {
            background-color: #10B981;
            color: white;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #059669;
        }
    """)
    self.take_button.clicked.connect(self.on_take_trade)

    self.skip_button = QPushButton("✗ Skip")
    self.skip_button.setStyleSheet("""
        QPushButton {
            background-color: #6B7280;
            color: white;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #4B5563;
        }
    """)
    self.skip_button.clicked.connect(self.on_skip_trade)

    button_layout.addWidget(self.take_button)
    button_layout.addWidget(self.skip_button)

    layout.addLayout(button_layout)

    # Log opportunity to database
    self.log_to_database()

def log_to_database(self):
    """Log this opportunity to database"""
    from database.trade_tracker import trade_tracker

    self.opportunity_id = trade_tracker.log_opportunity(self.opportunity)

def on_take_trade(self):
    """User clicked Take Trade"""
    from database.trade_tracker import trade_tracker

    if self.opportunity_id:
        trade_id = trade_tracker.log_user_action(self.opportunity_id, 'TAKE')

        # Visual feedback
        self.take_button.setText("✓ Trade Taken")
        self.take_button.setEnabled(False)
        self.skip_button.setEnabled(False)

        # TODO: Open trade entry dialog
        # TODO: Send order to MT5

def on_skip_trade(self):
    """User clicked Skip"""
    from database.trade_tracker import trade_tracker

    if self.opportunity_id:
        trade_tracker.log_user_action(self.opportunity_id, 'SKIP')

        # Visual feedback
        self.skip_button.setText("✗ Skipped")
        self.skip_button.setEnabled(False)
        self.take_button.setEnabled(False)
```

---

### **Phase 3: ML Training Pipeline (Week 2 - 5-7 days)**

**Objective:** Enable self-learning AI that improves based on YOUR trading results

#### **3.1 Feature Engineering**

**File:** `python/ml/feature_engineer.py`

```python
"""
Feature Engineering for ML Model Training
Extracts 50+ features from market data
"""

from typing import Dict, List
import pandas as pd
import numpy as np


class FeatureEngineer:
    """Extract ML features from opportunities"""

    def extract_features(self, opportunity: Dict, candles: pd.DataFrame) -> Dict:
        """
        Extract all ML features from opportunity

        Returns:
            {feature_name: value} dict with 50+ features
        """
        features = {}

        # === PRICE ACTION FEATURES ===
        features['atr_14'] = self.calculate_atr(candles, 14)
        features['rsi_14'] = self.calculate_rsi(candles, 14)
        features['price_to_sma_20'] = candles['close'].iloc[-1] / candles['close'].rolling(20).mean().iloc[-1]
        features['price_to_ema_50'] = candles['close'].iloc[-1] / candles['close'].ewm(span=50).mean().iloc[-1]

        # === VOLUME FEATURES ===
        features['volume_ratio'] = candles['volume'].iloc[-1] / candles['volume'].rolling(20).mean().iloc[-1]

        # === TREND FEATURES ===
        features['trend_strength'] = self.calculate_trend_strength(candles)

        # === PATTERN FEATURES ===
        features['pattern_quality'] = opportunity.get('quality_score', 0)
        features['risk_reward'] = opportunity.get('risk_reward', 0)

        # ... 40+ more features

        return features
```

#### **3.2 Model Trainer**

**File:** `python/ml/model_trainer.py`

```python
"""
ML Model Training Pipeline
Trains XGBoost classifier on labeled trade data
"""

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib
from datetime import datetime


class ModelTrainer:
    """
    Trains ML models to predict trade success

    Uses:
    - XGBoost classifier
    - 50+ engineered features
    - Walk-forward validation
    """

    def train_model(self, min_samples: int = 100):
        """
        Train new model on all available data

        Args:
            min_samples: Minimum trades required

        Returns:
            model, metrics
        """
        from database.trade_tracker import trade_tracker

        # Get training data
        training_data = trade_tracker.get_opportunities_for_training()

        if len(training_data) < min_samples:
            print(f"Not enough data: {len(training_data)}/{min_samples}")
            return None, None

        # Prepare X, y
        X = [features for features, label in training_data]
        y = [label for features, label in training_data]

        # Train/test split (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train XGBoost
        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'auc': roc_auc_score(y_test, y_proba),
            'training_samples': len(training_data),
            'timestamp': datetime.now()
        }

        # Save model
        model_path = f"models/xgboost_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        joblib.dump(model, model_path)

        return model, metrics
```

---

## 🔧 Technical Implementation Details

### **Directory Structure**

```
Python_Restart/python/
├── database/
│   ├── __init__.py
│   ├── schema.sql                # Database schema
│   ├── trade_tracker.py          # Trade tracking layer
│   └── migrations/               # Future schema changes
│
├── ml/
│   ├── __init__.py
│   ├── feature_engineer.py       # Feature extraction
│   ├── model_trainer.py          # Training pipeline
│   ├── model_predictor.py        # Prediction service
│   └── models/                   # Saved model files
│       └── .gitkeep
│
├── core/
│   ├── demo_mode_manager.py      # ✅ Already exists
│   ├── mt5_connector.py          # ✅ Already exists
│   └── data_manager.py           # ✅ Already exists
│
└── widgets/
    ├── opportunity_scanner_widget.py  # Modify for buttons
    └── ...
```

### **Data Flow**

```
┌─────────────┐
│   MT5 EA    │ Writes market_data.json every 1 second
└──────┬──────┘
       │
       v
┌─────────────┐
│MT5Connector │ Reads JSON, parses data
└──────┬──────┘
       │
       v
┌─────────────┐
│DataManager  │ Buffers in-memory, updates widgets
└──────┬──────┘
       │
       v
┌─────────────────────┐
│  All 11 Widgets     │ Display real-time data
│  - Dashboard        │
│  - Opportunity      │ ───> User clicks "Take Trade"
│  - Correlation      │           │
│  - etc.             │           v
└─────────────────────┘    ┌──────────────┐
                           │TradeTracker  │ Logs to SQLite
                           └──────┬───────┘
                                  │
                                  v
                           ┌──────────────┐
                           │   Database   │ Persistent storage
                           │ apple_trader │
                           │   _data.db   │
                           └──────┬───────┘
                                  │
                                  v
                           ┌──────────────┐
                           │ ML Trainer   │ Weekly retraining
                           └──────┬───────┘
                                  │
                                  v
                           ┌──────────────┐
                           │  AI Model    │ Improved predictions
                           └──────────────┘
```

### **Database File Location**

```
Recommended: Python_Restart/python/apple_trader_data.db

Pros:
- Same directory as application
- Easy backup
- Version control friendly (can add to .gitignore)

Alternative: User's Documents folder
- %USERPROFILE%\Documents\AppleTrader\apple_trader_data.db
- Better for multi-user systems
```

---

## 📅 Implementation Timeline

### **Week 1: Foundation**

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| Mon | Enable Live Mode, verify MT5 connection | Live data flowing |
| Tue | Create database schema, test SQLite | Database created |
| Wed | Implement TradeTracker class | Logging functional |
| Thu | Add Take/Skip buttons to opportunity cards | User actions logged |
| Fri | Test full flow (opportunity → action → database) | End-to-end working |

### **Week 2: ML Pipeline**

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| Mon | Build FeatureEngineer | 50+ features extracted |
| Tue | Implement ModelTrainer | Training pipeline ready |
| Wed | Collect 100 trades (manual or backfill) | Training dataset |
| Thu | Train first ML model | XGBoost model saved |
| Fri | Integrate predictions into widgets | AI suggestions personalized |

### **Week 3: Optimization**

- Performance analysis by pattern type
- Weekly model retraining automation
- Advanced metrics (Sharpe, max DD)
- Trade journal enhancement with ML insights

---

## 🎯 Success Metrics

### **Phase 1 Success (Live Mode):**
- ✅ All 11 widgets display real MT5 data
- ✅ Prices match MT5 terminal (< 1 pip difference)
- ✅ Account balance accurate
- ✅ No demo data visible

### **Phase 2 Success (SQL):**
- ✅ Every opportunity logged to database
- ✅ User actions (Take/Skip) recorded
- ✅ Trade results tracked
- ✅ Performance metrics calculated correctly
- ✅ 100+ opportunities in database

### **Phase 3 Success (ML):**
- ✅ Model trained on 100+ trades
- ✅ AUC score > 0.60 (better than random)
- ✅ Win rate improvement > 5% over baseline
- ✅ AI suggestions personalized to YOUR style
- ✅ Weekly automatic retraining

---

## ⚠️ Important Considerations

### **Data Quality**

**CRITICAL:** ML model quality depends on data quality!

**Requirements:**
- Minimum 100 trades (more is better)
- Balanced dataset (not 95% wins or 95% losses)
- Honest logging (log ALL trades, not just winners)
- Consistent execution (don't change strategy mid-training)

**Recommendation:** Trade manually for 2-4 weeks while collecting data before enabling ML predictions.

### **Backup Strategy**

**Database Backup:**
```bash
# Daily backup (automated)
cp apple_trader_data.db backups/apple_trader_data_$(date +%Y%m%d).db

# Weekly backup to cloud
# Upload to Google Drive, Dropbox, etc.
```

### **Model Versioning**

**Save every trained model with timestamp:**
```
models/
├── xgboost_20251217_143022.pkl  # v1.0 (100 trades)
├── xgboost_20251224_091500.pkl  # v1.1 (150 trades)
└── xgboost_20251231_120000.pkl  # v2.0 (200 trades)
```

**Compare performance before deploying new model!**

---

## 📚 Dependencies

### **Python Packages Required:**

```bash
# Already in requirements.txt:
scikit-learn>=1.3.0
xgboost>=2.0.0

# Need to add:
pip install sqlite3  # Usually comes with Python
```

### **MT5 EA Requirements:**

**EA must export:**
- `market_data.json` - Real-time market state
- `candles_EURUSD_M15.json` - OHLC data for each symbol/timeframe
- `positions.json` - Open positions

**EA must accept commands:**
- `OPEN_POSITION` - Execute trade
- `CLOSE_POSITION` - Close trade
- `GET_TRADE_HISTORY` - Export closed trades

---

## 🚀 Quick Start Commands

### **Enable Live Mode (Phase 1):**

```python
# In Python console or startup script
from core.demo_mode_manager import set_demo_mode
set_demo_mode(False)  # Switch to LIVE mode
```

### **Create Database (Phase 2):**

```python
# Run once to create database
from database.trade_tracker import trade_tracker
# Database automatically created on first import
```

### **Train First Model (Phase 3):**

```python
# After collecting 100+ trades
from ml.model_trainer import ModelTrainer

trainer = ModelTrainer()
model, metrics = trainer.train_model(min_samples=100)

print(f"Model trained!")
print(f"Accuracy: {metrics['accuracy']:.2%}")
print(f"AUC: {metrics['auc']:.3f}")
```

---

## 🔍 Testing & Validation

### **Live Mode Testing:**

```python
# Test 1: Verify MT5 connection
from core.mt5_connector import mt5_connector
assert mt5_connector.is_connection_active() == True

# Test 2: Check live data
from core.data_manager import data_manager
assert data_manager.is_data_fresh(max_age_seconds=30) == True

# Test 3: Verify NOT in demo mode
from core.demo_mode_manager import is_demo_mode
assert is_demo_mode() == False
```

### **Database Testing:**

```python
# Test 1: Log opportunity
from database.trade_tracker import trade_tracker
opp_id = trade_tracker.log_opportunity({
    'symbol': 'EURUSD',
    'pattern': 'Test Pattern',
    'quality_score': 75.0
})
assert opp_id > 0

# Test 2: Log action
trade_id = trade_tracker.log_user_action(opp_id, 'TAKE')
assert trade_id > 0

# Test 3: Calculate metrics
from datetime import date
metrics = trade_tracker.calculate_performance_metrics(
    date(2025, 12, 1),
    date(2025, 12, 31)
)
print(metrics)
```

---

## 📖 References

### **Related Documentation:**
- `/home/user/Restart/CRITICAL_ANALYSIS.md` - Original profitability analysis
- `/home/user/Restart/AI_STRATEGY_AND_PROFITABILITY_PLAN.md` - ML/AI strategy (source of SQL plan)
- `/home/user/Restart/AI_INTEGRATION_PLAN.md` - AI widget integration roadmap

### **Key Files:**
- `core/demo_mode_manager.py:29` - Demo mode toggle
- `core/mt5_connector.py:15` - MT5 data reading
- `core/data_manager.py:117` - Central data management
- `core/ai_assist_base.py` - AI integration mixin
- `widgets/opportunity_scanner_widget.py` - Opportunity cards

---

## ✅ Next Steps (Today)

1. **Review this document** ✓
2. **Commit to Git** ✓
3. **Enable Live Mode** (Phase 1 implementation)
4. **Verify real data flowing**
5. **Begin Phase 2 planning**

---

**Author:** Claude (AI Trading Systems Assistant)
**Date:** December 17, 2025
**Version:** 1.0
**Status:** Ready for Implementation
