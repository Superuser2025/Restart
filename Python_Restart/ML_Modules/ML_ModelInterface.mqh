//+------------------------------------------------------------------+
//| ML_ModelInterface.mqh                                             |
//| MODULE: Model Interface - Abstraction layer for ML predictions   |
//| DEPENDENCIES: ML_FeatureExtractor.mqh                             |
//+------------------------------------------------------------------+

#property strict

#include "ML_FeatureExtractor.mqh"

//+------------------------------------------------------------------+
//| PREDICTION RESULT STRUCTURE                                       |
//+------------------------------------------------------------------+
struct MLPrediction
{
    double probability;        // Probability of profitable trade (0-1)
    string signal;             // "ENTER", "SKIP", "WAIT"
    double confidence;         // Model confidence (0-1)
    datetime timestamp;
    bool is_valid;
};

//+------------------------------------------------------------------+
//| MODEL PERFORMANCE METRICS                                         |
//+------------------------------------------------------------------+
struct ModelMetrics
{
    int total_predictions;
    int correct_predictions;
    double accuracy;
    double precision;
    double recall;
    double f1_score;
    double roc_auc;
    datetime last_updated;
};

//+------------------------------------------------------------------+
//| ABSTRACT MODEL INTERFACE                                          |
//+------------------------------------------------------------------+
class IMLModel
{
public:
    virtual ~IMLModel() {}

    // Core prediction method
    virtual bool Predict(MLFeatureVector &features, MLPrediction &prediction) = 0;

    // Model management
    virtual bool LoadModel(string model_file) = 0;
    virtual bool IsModelLoaded() = 0;
    virtual void GetMetrics(ModelMetrics &metrics) = 0;

    // Model information
    virtual string GetModelName() = 0;
    virtual string GetModelVersion() = 0;
};

//+------------------------------------------------------------------+
//| PYTHON MODEL (via file-based IPC)                                |
//+------------------------------------------------------------------+
class CPythonModel : public IMLModel
{
private:
    string m_model_name;
    string m_model_version;
    string m_features_file;
    string m_prediction_file;
    bool m_model_loaded;
    ModelMetrics m_metrics;
    datetime m_last_prediction_time;
    int m_prediction_timeout_ms;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CPythonModel(string model_name = "RandomForest_v1")
    {
        m_model_name = model_name;
        m_model_version = "1.0.0";
        m_features_file = "ML_Data/current_features.json";
        m_prediction_file = "ML_Data/prediction.json";
        m_model_loaded = false;
        m_prediction_timeout_ms = 1000;  // 1 second timeout
        m_last_prediction_time = 0;

        // Initialize metrics
        m_metrics.total_predictions = 0;
        m_metrics.correct_predictions = 0;
        m_metrics.accuracy = 0;
        m_metrics.precision = 0;
        m_metrics.recall = 0;
        m_metrics.f1_score = 0;
        m_metrics.roc_auc = 0;
        m_metrics.last_updated = 0;
    }

    //+------------------------------------------------------------------+
    //| Predict (main method)                                             |
    //+------------------------------------------------------------------+
    virtual bool Predict(MLFeatureVector &features, MLPrediction &prediction)
    {
        prediction.is_valid = false;

        // Write features to JSON file
        if(!WriteFeaturesToFile(features))
        {
            Print("ERROR: Failed to write features to file");
            return false;
        }

        // Wait for Python service to process and write prediction
        datetime start_time = TimeLocal();
        bool prediction_received = false;

        while((TimeLocal() - start_time) < m_prediction_timeout_ms / 1000)
        {
            if(ReadPredictionFromFile(prediction))
            {
                prediction_received = true;
                break;
            }
            Sleep(50);  // Check every 50ms
        }

        if(!prediction_received)
        {
            Print("WARNING: Prediction timeout, using default");
            prediction.probability = 0.5;  // Neutral
            prediction.signal = "SKIP";
            prediction.confidence = 0.0;
            prediction.timestamp = TimeCurrent();
            return false;
        }

        m_last_prediction_time = TimeCurrent();
        m_metrics.total_predictions++;

        return true;
    }

    //+------------------------------------------------------------------+
    //| Load model                                                        |
    //+------------------------------------------------------------------+
    virtual bool LoadModel(string model_file)
    {
        // Check if Python service is running by attempting prediction
        MLFeatureVector test_features;
        for(int i = 0; i < TOTAL_FEATURES; i++)
            test_features.features[i] = 0;

        MLPrediction test_pred;
        if(Predict(test_features, test_pred))
        {
            m_model_loaded = true;
            Print("INFO: Python ML model connected successfully");
            return true;
        }

        Print("WARNING: Python ML service not responding");
        m_model_loaded = false;
        return false;
    }

    //+------------------------------------------------------------------+
    //| Check if model is loaded                                          |
    //+------------------------------------------------------------------+
    virtual bool IsModelLoaded()
    {
        return m_model_loaded;
    }

    //+------------------------------------------------------------------+
    //| Get model metrics                                                 |
    //+------------------------------------------------------------------+
    virtual void GetMetrics(ModelMetrics &metrics)
    {
        metrics = m_metrics;
    }

    //+------------------------------------------------------------------+
    //| Get model name                                                    |
    //+------------------------------------------------------------------+
    virtual string GetModelName()
    {
        return m_model_name;
    }

    //+------------------------------------------------------------------+
    //| Get model version                                                 |
    //+------------------------------------------------------------------+
    virtual string GetModelVersion()
    {
        return m_model_version;
    }

    //+------------------------------------------------------------------+
    //| Update metrics after trade result                                 |
    //+------------------------------------------------------------------+
    void UpdateMetrics(bool predicted_win, bool actual_win)
    {
        if(predicted_win == actual_win)
            m_metrics.correct_predictions++;

        m_metrics.accuracy = (double)m_metrics.correct_predictions / m_metrics.total_predictions;
        m_metrics.last_updated = TimeCurrent();

        // TODO: Calculate precision, recall, F1, ROC-AUC
    }

private:
    //+------------------------------------------------------------------+
    //| Write features to JSON file for Python                            |
    //+------------------------------------------------------------------+
    bool WriteFeaturesToFile(MLFeatureVector &features)
    {
        int handle = FileOpen(m_features_file, FILE_WRITE|FILE_TXT|FILE_COMMON);
        if(handle == INVALID_HANDLE)
        {
            Print("ERROR: Cannot create features file: ", m_features_file);
            return false;
        }

        string json = "{\n";
        json += "  \"timestamp\": \"" + TimeToString(TimeCurrent()) + "\",\n";
        json += "  \"features\": [";

        for(int i = 0; i < TOTAL_FEATURES; i++)
        {
            json += DoubleToString(features.features[i], 6);
            if(i < TOTAL_FEATURES - 1)
                json += ", ";
        }

        json += "]\n";
        json += "}\n";

        FileWriteString(handle, json);
        FileClose(handle);

        return true;
    }

    //+------------------------------------------------------------------+
    //| Read prediction from JSON file written by Python                  |
    //+------------------------------------------------------------------+
    bool ReadPredictionFromFile(MLPrediction &prediction)
    {
        int handle = FileOpen(m_prediction_file, FILE_READ|FILE_TXT|FILE_COMMON);
        if(handle == INVALID_HANDLE)
            return false;

        string json = "";
        while(!FileIsEnding(handle))
            json += FileReadString(handle);

        FileClose(handle);

        // Simple JSON parsing (in production, use proper parser)
        prediction.probability = ExtractJSONDouble(json, "probability");
        prediction.confidence = ExtractJSONDouble(json, "confidence", 0.5);
        prediction.signal = ExtractJSONString(json, "signal", "SKIP");
        prediction.timestamp = TimeCurrent();
        prediction.is_valid = true;

        return true;
    }

    //+------------------------------------------------------------------+
    //| Extract double from JSON (simple parser)                          |
    //+------------------------------------------------------------------+
    double ExtractJSONDouble(string json, string key, double default_value = 0)
    {
        string search_pattern = "\"" + key + "\":";
        int pos = StringFind(json, search_pattern);

        if(pos < 0)
            return default_value;

        int start = pos + StringLen(search_pattern);
        int end = start;

        // Find end of number
        while(end < StringLen(json))
        {
            string ch = StringSubstr(json, end, 1);
            if(StringCompare(ch, " ") != 0 &&
               StringCompare(ch, ",") != 0 &&
               StringCompare(ch, "\n") != 0 &&
               StringCompare(ch, "}") != 0)
                end++;
            else
                break;
        }

        string value_str = StringSubstr(json, start, end - start);
        StringTrimLeft(value_str);
        StringTrimRight(value_str);

        return StringToDouble(value_str);
    }

    //+------------------------------------------------------------------+
    //| Extract string from JSON (simple parser)                          |
    //+------------------------------------------------------------------+
    string ExtractJSONString(string json, string key, string default_value = "")
    {
        string search_pattern = "\"" + key + "\":";
        int pos = StringFind(json, search_pattern);

        if(pos < 0)
            return default_value;

        int start = StringFind(json, "\"", pos + StringLen(search_pattern)) + 1;
        int end = StringFind(json, "\"", start);

        if(start < 0 || end < 0)
            return default_value;

        return StringSubstr(json, start, end - start);
    }
};

//+------------------------------------------------------------------+
//| ENSEMBLE MODEL (combines multiple models)                        |
//+------------------------------------------------------------------+
class CEnsembleModel : public IMLModel
{
private:
    IMLModel* m_models[];
    int m_model_count;
    string m_ensemble_name;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CEnsembleModel(string name = "Ensemble_v1")
    {
        m_ensemble_name = name;
        m_model_count = 0;
        ArrayResize(m_models, 0);
    }

    //+------------------------------------------------------------------+
    //| Add model to ensemble                                             |
    //+------------------------------------------------------------------+
    void AddModel(IMLModel* model)
    {
        ArrayResize(m_models, m_model_count + 1);
        m_models[m_model_count] = model;
        m_model_count++;
    }

    //+------------------------------------------------------------------+
    //| Predict (average of all models)                                   |
    //+------------------------------------------------------------------+
    virtual bool Predict(MLFeatureVector &features, MLPrediction &prediction)
    {
        if(m_model_count == 0)
        {
            Print("ERROR: No models in ensemble");
            return false;
        }

        double total_probability = 0;
        double total_confidence = 0;
        int valid_predictions = 0;

        for(int i = 0; i < m_model_count; i++)
        {
            MLPrediction model_pred;
            if(m_models[i].Predict(features, model_pred) && model_pred.is_valid)
            {
                total_probability += model_pred.probability;
                total_confidence += model_pred.confidence;
                valid_predictions++;
            }
        }

        if(valid_predictions == 0)
        {
            prediction.is_valid = false;
            return false;
        }

        // Average predictions
        prediction.probability = total_probability / valid_predictions;
        prediction.confidence = total_confidence / valid_predictions;
        prediction.timestamp = TimeCurrent();

        // Determine signal
        if(prediction.probability >= 0.6 && prediction.confidence >= 0.5)
            prediction.signal = "ENTER";
        else if(prediction.probability >= 0.5)
            prediction.signal = "WAIT";
        else
            prediction.signal = "SKIP";

        prediction.is_valid = true;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Load all models                                                   |
    //+------------------------------------------------------------------+
    virtual bool LoadModel(string model_file)
    {
        bool all_loaded = true;
        for(int i = 0; i < m_model_count; i++)
        {
            if(!m_models[i].LoadModel(model_file))
                all_loaded = false;
        }
        return all_loaded;
    }

    virtual bool IsModelLoaded()
    {
        for(int i = 0; i < m_model_count; i++)
        {
            if(!m_models[i].IsModelLoaded())
                return false;
        }
        return m_model_count > 0;
    }

    virtual void GetMetrics(ModelMetrics &metrics)
    {
        // Return metrics from first model (simplified)
        if(m_model_count > 0)
            m_models[0].GetMetrics(metrics);
    }

    virtual string GetModelName() { return m_ensemble_name; }
    virtual string GetModelVersion() { return "1.0.0"; }
};
