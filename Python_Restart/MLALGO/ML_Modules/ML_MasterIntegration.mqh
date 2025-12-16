//+------------------------------------------------------------------+
//| ML_MasterIntegration.mqh                                          |
//| MASTER MODULE: Complete ML integration for trading EA            |
//| Ties together all ML modules into a cohesive system               |
//+------------------------------------------------------------------+

#property strict

#include "ML_FeatureExtractor.mqh"
#include "ML_DataManager.mqh"
#include "ML_ModelInterface.mqh"
#include "ML_StatisticalValidator.mqh"

//+------------------------------------------------------------------+
//| ML SYSTEM CONFIGURATION                                           |
//+------------------------------------------------------------------+
struct MLConfig
{
    bool enabled;                    // Master ML on/off switch
    bool use_for_filtering;          // Use ML to filter trades
    bool use_for_sizing;             // Use ML confidence for position sizing
    bool collect_training_data;      // Collect data for training
    double min_probability_threshold; // Min probability to enter (0-1)
    double min_confidence_threshold;  // Min confidence to enter (0-1)
    int retrain_every_n_trades;      // Retrain model every N trades
    bool auto_export_data;           // Auto-export data periodically
};

//+------------------------------------------------------------------+
//| ML TRADING SYSTEM (Main class that integrates everything)        |
//+------------------------------------------------------------------+
class CMLTradingSystem
{
private:
    // Module instances
    CFeatureExtractor* m_feature_extractor;
    CMLDataManager* m_data_manager;
    CPythonModel* m_model;
    CStatisticalValidator* m_validator;

    // Configuration
    MLConfig m_config;

    // State tracking
    int m_trades_since_retrain;
    datetime m_last_export_time;
    bool m_initialized;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CMLTradingSystem()
    {
        m_initialized = false;
        m_trades_since_retrain = 0;
        m_last_export_time = 0;

        // Default configuration
        m_config.enabled = false;  // Start disabled for safety
        m_config.use_for_filtering = true;
        m_config.use_for_sizing = false;
        m_config.collect_training_data = true;
        m_config.min_probability_threshold = 0.6;
        m_config.min_confidence_threshold = 0.5;
        m_config.retrain_every_n_trades = 100;
        m_config.auto_export_data = true;
    }

    //+------------------------------------------------------------------+
    //| Initialize ML system                                              |
    //+------------------------------------------------------------------+
    bool Initialize(MLConfig &config)
    {
        m_config = config;

        Print("=== Initializing ML Trading System ===");

        // Create module instances
        m_feature_extractor = new CFeatureExtractor();
        m_data_manager = new CMLDataManager(10000);
        m_model = new CPythonModel("RandomForest_v1");
        m_validator = new CStatisticalValidator(10000);

        // Load existing data
        m_data_manager.LoadFromDisk();
        Print("INFO: Loaded historical training data");

        // Skip Python connection test during initialization to avoid delays
        // Model will connect on first prediction attempt
        if(m_config.enabled)
        {
            Print("INFO: ML model will connect on first prediction");
            Print("INFO: Data collection mode active");
        }

        m_initialized = true;
        Print("=== ML System Initialized ===");

        return true;
    }

    //+------------------------------------------------------------------+
    //| MAIN METHOD: Should I take this trade?                           |
    //+------------------------------------------------------------------+
    bool ShouldEnterTrade(MLFeatureVector &features, double &adjusted_lot_size)
    {
        if(!m_config.enabled || !m_initialized)
            return true;  // ML disabled, allow trade

        // DATA COLLECTION MODE: Always allow trades until we have enough data
        int sample_count = m_data_manager.GetSampleCount();
        if(sample_count < 50)
        {
            Print("ML: Data collection mode (", sample_count, "/50 samples) - Trade approved");
            AddMLAction("✅ DATA COLLECTION: Trade approved (" + IntegerToString(sample_count) + "/50 samples)", clrLime, true);
            return true;  // Allow all trades to collect training data
        }

        // Get ML prediction only after we have sufficient data
        MLPrediction prediction;
        if(!m_model.Predict(features, prediction))
        {
            Print("WARNING: ML prediction failed, allowing trade");
            AddMLAction("⚠️ PREDICTION FAILED: Allowing trade (fail-safe mode)", clrOrange, true);
            return true;  // On failure, don't block trade
        }

        Print("ML PREDICTION: Probability=", DoubleToString(prediction.probability, 3),
              " Confidence=", DoubleToString(prediction.confidence, 3),
              " Signal=", prediction.signal);

        // Filtering logic
        if(m_config.use_for_filtering)
        {
            if(prediction.probability < m_config.min_probability_threshold)
            {
                Print("ML FILTER: Trade blocked (low probability)");
                AddMLAction("❌ TRADE REJECTED: Low probability " + DoubleToString(prediction.probability * 100, 1) + "% (min " + DoubleToString(m_config.min_probability_threshold * 100, 0) + "%)", clrRed, false);
                return false;
            }

            if(prediction.confidence < m_config.min_confidence_threshold)
            {
                Print("ML FILTER: Trade blocked (low confidence)");
                AddMLAction("❌ TRADE REJECTED: Low confidence " + DoubleToString(prediction.confidence * 100, 1) + "% (min " + DoubleToString(m_config.min_confidence_threshold * 100, 0) + "%)", clrRed, false);
                return false;
            }
        }

        // Position sizing adjustment
        if(m_config.use_for_sizing)
        {
            // Scale lot size by confidence
            // High confidence = 100% of normal size
            // Low confidence = 50% of normal size
            double size_multiplier = 0.5 + (prediction.confidence * 0.5);
            adjusted_lot_size *= size_multiplier;

            Print("ML SIZING: Adjusted lot size by ", DoubleToString(size_multiplier * 100, 0), "%");
        }

        Print("ML DECISION: Trade APPROVED");
        AddMLAction("✅ TRADE APPROVED: Probability " + DoubleToString(prediction.probability * 100, 1) + "% | Confidence " + DoubleToString(prediction.confidence * 100, 1) + "%", clrLime, true);
        return true;
    }

    //+------------------------------------------------------------------+
    //| Extract features for current market conditions                    |
    //+------------------------------------------------------------------+
    bool ExtractCurrentFeatures(MLFeatureVector &features)
    {
        if(!m_initialized)
            return false;

        return m_feature_extractor.Extract(features, 0);
    }

    //+------------------------------------------------------------------+
    //| Record trade entry (start tracking for later labeling)            |
    //+------------------------------------------------------------------+
    void OnTradeEntry(MLFeatureVector &features, double entry_price, double stop_loss, bool is_buy)
    {
        if(!m_initialized || !m_config.collect_training_data)
            return;

        // Store features for later labeling when trade closes
        // (Implementation depends on your trade tracking system)
        Print("ML DATA: Recording trade entry for training data");
    }

    //+------------------------------------------------------------------+
    //| Record trade exit (create labeled training sample)                |
    //+------------------------------------------------------------------+
    void OnTradeExit(MLFeatureVector &features,
                     datetime entry_time, datetime exit_time,
                     double entry_price, double exit_price,
                     double stop_loss, bool is_buy, double lot_size,
                     double mae, double mfe)
    {
        if(!m_initialized)
            return;

        // Calculate label (1 = win, 0 = loss)
        double pnl = is_buy ? (exit_price - entry_price) : (entry_price - exit_price);
        double label = (pnl > 0) ? 1.0 : 0.0;

        // Calculate R:R
        double sl_distance = MathAbs(entry_price - stop_loss);
        double rr_achieved = MathAbs(exit_price - entry_price) / sl_distance;
        if(pnl < 0)
            rr_achieved = -rr_achieved;

        // Add to training data
        if(m_config.collect_training_data)
        {
            m_data_manager.AddSample(features, label, rr_achieved,
                                    entry_time, exit_time,
                                    entry_price, exit_price, stop_loss, is_buy);

            Print("ML DATA: Added training sample (Label=", label, ", R:R=", DoubleToString(rr_achieved, 2), ")");
        }

        // Add to statistical validator
        m_validator.AddTradeResult(entry_time, exit_time, entry_price, exit_price,
                                   stop_loss, 0, is_buy, lot_size, mae, mfe);

        m_trades_since_retrain++;

        // Auto-export data periodically
        if(m_config.auto_export_data && m_trades_since_retrain >= 10)
        {
            ExportTrainingData();
        }

        // Check if we should trigger retraining
        if(m_trades_since_retrain >= m_config.retrain_every_n_trades)
        {
            TriggerRetraining();
        }
    }

    //+------------------------------------------------------------------+
    //| Export training data to Python                                    |
    //+------------------------------------------------------------------+
    void ExportTrainingData()
    {
        if(!m_initialized)
            return;

        Print("=== Exporting Training Data ===");

        // Export to both CSV and JSON
        m_data_manager.ExportToCSV("ML_Data/training_data.csv");
        m_data_manager.ExportToJSON("ML_Data/training_data.json");

        // Save to disk
        m_data_manager.SaveToDisk();

        // Print statistics
        m_data_manager.PrintStatistics();

        m_last_export_time = TimeCurrent();

        Print("=== Export Complete ===");
    }

    //+------------------------------------------------------------------+
    //| Trigger model retraining (signal to Python service)               |
    //+------------------------------------------------------------------+
    void TriggerRetraining()
    {
        if(!m_initialized)
            return;

        Print("=== Triggering Model Retraining ===");

        // Export latest data
        ExportTrainingData();

        // Create trigger file for Python service
        int handle = FileOpen("ML_Data/retrain_trigger.txt", FILE_WRITE|FILE_TXT|FILE_COMMON);
        if(handle != INVALID_HANDLE)
        {
            FileWriteString(handle, "RETRAIN_REQUESTED\n");
            FileWriteString(handle, "Timestamp: " + TimeToString(TimeCurrent()) + "\n");
            FileWriteString(handle, "Total samples: " + IntegerToString(m_data_manager.GetSampleCount()) + "\n");
            FileClose(handle);
        }

        m_trades_since_retrain = 0;

        Print("INFO: Retraining triggered. Python service should detect and start training.");
        Print("=== Retraining Trigger Complete ===");
    }

    //+------------------------------------------------------------------+
    //| Get sample count                                                  |
    //+------------------------------------------------------------------+
    int GetSampleCount()
    {
        if(!m_initialized)
            return 0;
        return m_data_manager.GetSampleCount();
    }

    //+------------------------------------------------------------------+
    //| Get performance report                                            |
    //+------------------------------------------------------------------+
    void PrintPerformanceReport()
    {
        if(!m_initialized)
            return;

        Print("\n");
        Print("╔══════════════════════════════════════════════════════════╗");
        Print("║           ML TRADING SYSTEM PERFORMANCE REPORT           ║");
        Print("╚══════════════════════════════════════════════════════════╝");
        Print("");

        // Model information
        Print("--- Model Information ---");
        Print("Model: ", m_model.GetModelName(), " v", m_model.GetModelVersion());
        Print("Status: ", m_model.IsModelLoaded() ? "ACTIVE" : "INACTIVE");
        Print("");

        // Training data statistics
        Print("--- Training Data ---");
        m_data_manager.PrintStatistics();
        Print("");

        // Performance statistics
        Print("--- Performance Statistics ---");
        m_validator.PrintReport();
        Print("");

        // Configuration
        Print("--- Configuration ---");
        Print("ML Enabled: ", m_config.enabled ? "YES" : "NO");
        Print("Use for Filtering: ", m_config.use_for_filtering ? "YES" : "NO");
        Print("Use for Sizing: ", m_config.use_for_sizing ? "YES" : "NO");
        Print("Min Probability: ", DoubleToString(m_config.min_probability_threshold, 2));
        Print("Min Confidence: ", DoubleToString(m_config.min_confidence_threshold, 2));
        Print("Retrain Every: ", m_config.retrain_every_n_trades, " trades");
        Print("Trades Since Last Retrain: ", m_trades_since_retrain);
        Print("");
    }

    //+------------------------------------------------------------------+
    //| Export equity curve                                               |
    //+------------------------------------------------------------------+
    void ExportEquityCurve()
    {
        if(!m_initialized)
            return;

        m_validator.ExportEquityCurve("ML_Data/equity_curve.csv");
        Print("INFO: Equity curve exported to ML_Data/equity_curve.csv");
    }

    //+------------------------------------------------------------------+
    //| Enable/disable ML system                                          |
    //+------------------------------------------------------------------+
    void SetEnabled(bool enabled)
    {
        m_config.enabled = enabled;
        Print("ML System ", enabled ? "ENABLED" : "DISABLED");
    }

    //+------------------------------------------------------------------+
    //| Get current configuration                                         |
    //+------------------------------------------------------------------+
    void GetConfig(MLConfig &config)
    {
        config = m_config;
    }

    //+------------------------------------------------------------------+
    //| Update configuration                                              |
    //+------------------------------------------------------------------+
    void SetConfig(MLConfig &config)
    {
        m_config = config;
        Print("ML System configuration updated");
    }

    //+------------------------------------------------------------------+
    //| Destructor                                                        |
    //+------------------------------------------------------------------+
    ~CMLTradingSystem()
    {
        if(m_initialized)
        {
            // Save data before shutdown
            m_data_manager.SaveToDisk();

            // Cleanup
            delete m_feature_extractor;
            delete m_data_manager;
            delete m_model;
            delete m_validator;
        }
    }
};

//+------------------------------------------------------------------+
//| USAGE EXAMPLE                                                     |
//+------------------------------------------------------------------+

/*
// In your EA's OnInit():

CMLTradingSystem* ml_system;

int OnInit()
{
    ml_system = new CMLTradingSystem();

    MLConfig config;
    config.enabled = true;
    config.use_for_filtering = true;
    config.use_for_sizing = true;
    config.collect_training_data = true;
    config.min_probability_threshold = 0.6;
    config.min_confidence_threshold = 0.5;
    config.retrain_every_n_trades = 100;
    config.auto_export_data = true;

    ml_system.Initialize(config);

    return INIT_SUCCEEDED;
}

// In your trading logic (before executing trade):

void OnTick()
{
    // Your pattern detection logic here...

    if(pattern_detected)
    {
        // Extract features
        MLFeatureVector features;
        ml_system.ExtractCurrentFeatures(features);

        // Check with ML system
        double lot_size = CalculateLotSize();
        if(ml_system.ShouldEnterTrade(features, lot_size))
        {
            // ML approved, place trade
            int ticket = OrderSend(...);

            if(ticket > 0)
            {
                // Record entry for training
                ml_system.OnTradeEntry(features, entry_price, stop_loss, is_buy);
            }
        }
        else
        {
            // ML filtered out this trade
            Print("Trade filtered by ML system");
        }
    }
}

// When trade closes:

void OnTradeClose(int ticket)
{
    // Get trade info
    if(OrderSelect(ticket, SELECT_BY_TICKET))
    {
        datetime entry_time = OrderOpenTime();
        datetime exit_time = OrderCloseTime();
        double entry_price = OrderOpenPrice();
        double exit_price = OrderClosePrice();
        double stop_loss = OrderStopLoss();
        bool is_buy = (OrderType() == OP_BUY);
        double lot_size = OrderLots();

        // Calculate MAE/MFE (you need to track this during trade)
        double mae = CalculateMAE(ticket);
        double mfe = CalculateMFE(ticket);

        // Extract features that were used for entry
        MLFeatureVector features;
        ml_system.ExtractCurrentFeatures(features);

        // Record result
        ml_system.OnTradeExit(features, entry_time, exit_time,
                             entry_price, exit_price, stop_loss,
                             is_buy, lot_size, mae, mfe);
    }
}

// Periodic reporting (e.g., once per day):

void OnTimer()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);

    if(dt.hour == 0 && dt.min == 0)  // Midnight
    {
        ml_system.PrintPerformanceReport();
        ml_system.ExportEquityCurve();
    }
}

// OnDeinit:

void OnDeinit(const int reason)
{
    ml_system.PrintPerformanceReport();
    delete ml_system;
}

*/
