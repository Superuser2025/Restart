//+------------------------------------------------------------------+
//| ML_DataManager.mqh                                                |
//| MODULE: Data Management - Stores features, labels, and results   |
//| DEPENDENCIES: ML_FeatureExtractor.mqh                             |
//+------------------------------------------------------------------+

#property strict

#include "ML_FeatureExtractor.mqh"

//+------------------------------------------------------------------+
//| TRAINING SAMPLE STRUCTURE                                         |
//+------------------------------------------------------------------+
struct TrainingSample
{
    MLFeatureVector features;
    double label;              // 0 = loss, 1 = win
    double rr_achieved;        // Actual R:R achieved
    datetime entry_time;
    datetime exit_time;
    double entry_price;
    double exit_price;
    double stop_loss;
    bool is_buy;
};

//+------------------------------------------------------------------+
//| DATA MANAGER CLASS                                                |
//+------------------------------------------------------------------+
class CMLDataManager
{
private:
    TrainingSample m_samples[];
    int m_sample_count;
    int m_max_samples;
    string m_storage_file;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CMLDataManager(int max_samples = 10000)
    {
        m_max_samples = max_samples;
        m_sample_count = 0;
        ArrayResize(m_samples, max_samples);
        m_storage_file = "ML_Data/training_data.bin";
    }

    //+------------------------------------------------------------------+
    //| Add new training sample                                           |
    //+------------------------------------------------------------------+
    bool AddSample(MLFeatureVector &features, double label, double rr_achieved,
                   datetime entry_time, datetime exit_time,
                   double entry_price, double exit_price, double stop_loss, bool is_buy)
    {
        if(m_sample_count >= m_max_samples)
        {
            // Ring buffer: overwrite oldest sample
            ShiftSamples();
        }

        TrainingSample sample;
        sample.features = features;
        sample.label = label;
        sample.rr_achieved = rr_achieved;
        sample.entry_time = entry_time;
        sample.exit_time = exit_time;
        sample.entry_price = entry_price;
        sample.exit_price = exit_price;
        sample.stop_loss = stop_loss;
        sample.is_buy = is_buy;

        m_samples[m_sample_count] = sample;
        m_sample_count++;

        return true;
    }

    //+------------------------------------------------------------------+
    //| Export data to CSV for Python                                     |
    //+------------------------------------------------------------------+
    bool ExportToCSV(string filename = "training_data.csv")
    {
        int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_COMMON);
        if(handle == INVALID_HANDLE)
        {
            Print("ERROR: Failed to create CSV file: ", filename);
            return false;
        }

        // Write header
        string header = "timestamp,";
        for(int i = 0; i < TOTAL_FEATURES; i++)
            header += "feature_" + IntegerToString(i) + ",";
        header += "label,rr_achieved,entry_price,exit_price,stop_loss,is_buy";
        FileWriteString(handle, header + "\n");

        // Write data
        for(int s = 0; s < m_sample_count; s++)
        {
            string row = TimeToString(m_samples[s].entry_time) + ",";

            for(int f = 0; f < TOTAL_FEATURES; f++)
                row += DoubleToString(m_samples[s].features.features[f], 6) + ",";

            row += DoubleToString(m_samples[s].label, 0) + ",";
            row += DoubleToString(m_samples[s].rr_achieved, 2) + ",";
            row += DoubleToString(m_samples[s].entry_price, 5) + ",";
            row += DoubleToString(m_samples[s].exit_price, 5) + ",";
            row += DoubleToString(m_samples[s].stop_loss, 5) + ",";
            row += IntegerToString(m_samples[s].is_buy ? 1 : 0);

            FileWriteString(handle, row + "\n");
        }

        FileClose(handle);
        Print("INFO: Exported ", m_sample_count, " samples to ", filename);
        return true;
    }

    //+------------------------------------------------------------------+
    //| Export to JSON format                                             |
    //+------------------------------------------------------------------+
    bool ExportToJSON(string filename = "training_data.json")
    {
        int handle = FileOpen(filename, FILE_WRITE|FILE_TXT|FILE_COMMON);
        if(handle == INVALID_HANDLE)
        {
            Print("ERROR: Failed to create JSON file: ", filename);
            return false;
        }

        FileWriteString(handle, "{\n");
        FileWriteString(handle, "  \"total_samples\": " + IntegerToString(m_sample_count) + ",\n");
        FileWriteString(handle, "  \"total_features\": " + IntegerToString(TOTAL_FEATURES) + ",\n");
        FileWriteString(handle, "  \"data\": [\n");

        for(int s = 0; s < m_sample_count; s++)
        {
            FileWriteString(handle, "    {\n");
            FileWriteString(handle, "      \"timestamp\": \"" + TimeToString(m_samples[s].entry_time) + "\",\n");

            // Features array
            FileWriteString(handle, "      \"features\": [");
            for(int f = 0; f < TOTAL_FEATURES; f++)
            {
                FileWriteString(handle, DoubleToString(m_samples[s].features.features[f], 6));
                if(f < TOTAL_FEATURES - 1)
                    FileWriteString(handle, ", ");
            }
            FileWriteString(handle, "],\n");

            FileWriteString(handle, "      \"label\": " + DoubleToString(m_samples[s].label, 0) + ",\n");
            FileWriteString(handle, "      \"rr_achieved\": " + DoubleToString(m_samples[s].rr_achieved, 2) + ",\n");
            FileWriteString(handle, "      \"entry_price\": " + DoubleToString(m_samples[s].entry_price, 5) + ",\n");
            FileWriteString(handle, "      \"exit_price\": " + DoubleToString(m_samples[s].exit_price, 5) + ",\n");
            FileWriteString(handle, "      \"stop_loss\": " + DoubleToString(m_samples[s].stop_loss, 5) + ",\n");
            FileWriteString(handle, "      \"is_buy\": " + IntegerToString(m_samples[s].is_buy ? 1 : 0) + "\n");

            FileWriteString(handle, "    }");
            if(s < m_sample_count - 1)
                FileWriteString(handle, ",\n");
            else
                FileWriteString(handle, "\n");
        }

        FileWriteString(handle, "  ]\n");
        FileWriteString(handle, "}\n");

        FileClose(handle);
        Print("INFO: Exported ", m_sample_count, " samples to ", filename);
        return true;
    }

    //+------------------------------------------------------------------+
    //| Get sample count                                                  |
    //+------------------------------------------------------------------+
    int GetSampleCount() { return m_sample_count; }

    //+------------------------------------------------------------------+
    //| Get sample by index                                               |
    //+------------------------------------------------------------------+
    bool GetSample(int index, TrainingSample &sample)
    {
        if(index < 0 || index >= m_sample_count)
            return false;

        sample = m_samples[index];
        return true;
    }

    //+------------------------------------------------------------------+
    //| Calculate statistics                                              |
    //+------------------------------------------------------------------+
    void PrintStatistics()
    {
        if(m_sample_count == 0)
        {
            Print("INFO: No samples collected yet");
            return;
        }

        int wins = 0;
        double total_rr = 0;

        for(int i = 0; i < m_sample_count; i++)
        {
            if(m_samples[i].label > 0.5)
                wins++;
            total_rr += m_samples[i].rr_achieved;
        }

        double win_rate = (double)wins / m_sample_count;
        double avg_rr = total_rr / m_sample_count;

        Print("=== ML DATA STATISTICS ===");
        Print("Total samples: ", m_sample_count);
        Print("Wins: ", wins, " (", DoubleToString(win_rate * 100, 1), "%)");
        Print("Losses: ", m_sample_count - wins, " (", DoubleToString((1 - win_rate) * 100, 1), "%)");
        Print("Average R:R: ", DoubleToString(avg_rr, 2));
        Print("Expected Value: ", DoubleToString(win_rate * avg_rr - (1 - win_rate), 2), "R");
    }

    //+------------------------------------------------------------------+
    //| Save samples to binary file                                       |
    //+------------------------------------------------------------------+
    bool SaveToDisk()
    {
        int handle = FileOpen(m_storage_file, FILE_WRITE|FILE_BIN|FILE_COMMON);
        if(handle == INVALID_HANDLE)
        {
            Print("ERROR: Failed to save data to disk");
            return false;
        }

        // Write sample count
        FileWriteInteger(handle, m_sample_count);

        // Write samples
        for(int i = 0; i < m_sample_count; i++)
        {
            // Write features
            for(int f = 0; f < TOTAL_FEATURES; f++)
                FileWriteDouble(handle, m_samples[i].features.features[f]);

            // Write labels and metadata
            FileWriteDouble(handle, m_samples[i].label);
            FileWriteDouble(handle, m_samples[i].rr_achieved);
            FileWriteLong(handle, m_samples[i].entry_time);
            FileWriteLong(handle, m_samples[i].exit_time);
            FileWriteDouble(handle, m_samples[i].entry_price);
            FileWriteDouble(handle, m_samples[i].exit_price);
            FileWriteDouble(handle, m_samples[i].stop_loss);
            FileWriteInteger(handle, m_samples[i].is_buy ? 1 : 0);
        }

        FileClose(handle);
        Print("INFO: Saved ", m_sample_count, " samples to disk");
        return true;
    }

    //+------------------------------------------------------------------+
    //| Load samples from binary file                                     |
    //+------------------------------------------------------------------+
    bool LoadFromDisk()
    {
        int handle = FileOpen(m_storage_file, FILE_READ|FILE_BIN|FILE_COMMON);
        if(handle == INVALID_HANDLE)
        {
            Print("INFO: No saved data found on disk");
            return false;
        }

        // Read sample count
        m_sample_count = FileReadInteger(handle);

        if(m_sample_count > m_max_samples)
            m_sample_count = m_max_samples;

        // Read samples
        for(int i = 0; i < m_sample_count; i++)
        {
            // Read features
            for(int f = 0; f < TOTAL_FEATURES; f++)
                m_samples[i].features.features[f] = FileReadDouble(handle);

            // Read labels and metadata
            m_samples[i].label = FileReadDouble(handle);
            m_samples[i].rr_achieved = FileReadDouble(handle);
            m_samples[i].entry_time = (datetime)FileReadLong(handle);
            m_samples[i].exit_time = (datetime)FileReadLong(handle);
            m_samples[i].entry_price = FileReadDouble(handle);
            m_samples[i].exit_price = FileReadDouble(handle);
            m_samples[i].stop_loss = FileReadDouble(handle);
            m_samples[i].is_buy = (FileReadInteger(handle) == 1);
        }

        FileClose(handle);
        Print("INFO: Loaded ", m_sample_count, " samples from disk");
        return true;
    }

    //+------------------------------------------------------------------+
    //| Clear all data                                                    |
    //+------------------------------------------------------------------+
    void Clear()
    {
        m_sample_count = 0;
        ArrayResize(m_samples, m_max_samples);
        Print("INFO: Data manager cleared");
    }

private:
    //+------------------------------------------------------------------+
    //| Shift samples (for ring buffer)                                   |
    //+------------------------------------------------------------------+
    void ShiftSamples()
    {
        for(int i = 1; i < m_max_samples; i++)
            m_samples[i - 1] = m_samples[i];
        m_sample_count--;
    }
};
