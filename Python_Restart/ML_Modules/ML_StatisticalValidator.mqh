//+------------------------------------------------------------------+
//| ML_StatisticalValidator.mqh                                       |
//| MODULE: Statistical Validation - Performance tracking & metrics  |
//| DEPENDENCIES: None (standalone module)                            |
//+------------------------------------------------------------------+

#property strict

//+------------------------------------------------------------------+
//| TRADE RESULT STRUCTURE                                            |
//+------------------------------------------------------------------+
struct TradeResult
{
    datetime entry_time;
    datetime exit_time;
    double entry_price;
    double exit_price;
    double stop_loss;
    double take_profit;
    bool is_buy;
    bool is_win;
    double rr_achieved;
    double pnl_dollars;
    double pnl_percent;
    double mae;  // Maximum Adverse Excursion
    double mfe;  // Maximum Favorable Excursion
};

//+------------------------------------------------------------------+
//| PERFORMANCE STATISTICS                                            |
//+------------------------------------------------------------------+
struct PerformanceStats
{
    // Basic metrics
    int total_trades;
    int winning_trades;
    int losing_trades;
    double win_rate;

    // P&L metrics
    double total_pnl;
    double avg_win;
    double avg_loss;
    double largest_win;
    double largest_loss;
    double profit_factor;

    // Risk-adjusted metrics
    double sharpe_ratio;
    double sortino_ratio;
    double calmar_ratio;
    double max_drawdown;
    double max_drawdown_percent;

    // Trade quality metrics
    double avg_rr;
    double avg_mae;
    double avg_mfe;
    double avg_trade_duration_hours;

    // Consistency metrics
    double win_streak_current;
    double loss_streak_current;
    double win_streak_max;
    double loss_streak_max;

    datetime last_updated;
};

//+------------------------------------------------------------------+
//| STATISTICAL VALIDATOR CLASS                                       |
//+------------------------------------------------------------------+
class CStatisticalValidator
{
private:
    TradeResult m_results[];
    int m_result_count;
    int m_max_results;
    PerformanceStats m_stats;
    double m_equity_curve[];
    int m_equity_count;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                       |
    //+------------------------------------------------------------------+
    CStatisticalValidator(int max_results = 10000)
    {
        m_max_results = max_results;
        m_result_count = 0;
        m_equity_count = 0;
        ArrayResize(m_results, max_results);
        ArrayResize(m_equity_curve, max_results);

        ResetStats();
    }

    //+------------------------------------------------------------------+
    //| Add trade result                                                  |
    //+------------------------------------------------------------------+
    void AddTradeResult(datetime entry_time, datetime exit_time,
                        double entry_price, double exit_price,
                        double stop_loss, double take_profit,
                        bool is_buy, double lot_size,
                        double mae, double mfe)
    {
        if(m_result_count >= m_max_results)
        {
            // Ring buffer
            for(int i = 1; i < m_max_results; i++)
                m_results[i - 1] = m_results[i];
            m_result_count--;
        }

        TradeResult result;
        result.entry_time = entry_time;
        result.exit_time = exit_time;
        result.entry_price = entry_price;
        result.exit_price = exit_price;
        result.stop_loss = stop_loss;
        result.take_profit = take_profit;
        result.is_buy = is_buy;
        result.mae = mae;
        result.mfe = mfe;

        // Calculate P&L
        if(is_buy)
            result.pnl_dollars = (exit_price - entry_price) * lot_size * 100000;  // Assuming forex
        else
            result.pnl_dollars = (entry_price - exit_price) * lot_size * 100000;

        result.is_win = (result.pnl_dollars > 0);

        // Calculate R:R achieved
        double sl_distance = MathAbs(entry_price - stop_loss);
        result.rr_achieved = MathAbs(exit_price - entry_price) / sl_distance;
        if(!result.is_win)
            result.rr_achieved = -result.rr_achieved;

        m_results[m_result_count] = result;
        m_result_count++;

        // Update equity curve
        double prev_equity = (m_equity_count > 0) ? m_equity_curve[m_equity_count - 1] : 0;
        m_equity_curve[m_equity_count] = prev_equity + result.pnl_dollars;
        m_equity_count++;

        // Recalculate statistics
        CalculateStatistics();
    }

    //+------------------------------------------------------------------+
    //| Calculate all statistics                                          |
    //+------------------------------------------------------------------+
    void CalculateStatistics()
    {
        if(m_result_count == 0)
        {
            ResetStats();
            return;
        }

        // Basic metrics
        m_stats.total_trades = m_result_count;
        m_stats.winning_trades = 0;
        m_stats.losing_trades = 0;
        m_stats.total_pnl = 0;
        m_stats.largest_win = 0;
        m_stats.largest_loss = 0;

        double total_wins_pnl = 0;
        double total_losses_pnl = 0;
        double total_rr = 0;
        double total_mae = 0;
        double total_mfe = 0;
        double total_duration = 0;

        for(int i = 0; i < m_result_count; i++)
        {
            TradeResult r = m_results[i];

            m_stats.total_pnl += r.pnl_dollars;
            total_rr += r.rr_achieved;
            total_mae += r.mae;
            total_mfe += r.mfe;
            total_duration += (r.exit_time - r.entry_time) / 3600.0;  // Hours

            if(r.is_win)
            {
                m_stats.winning_trades++;
                total_wins_pnl += r.pnl_dollars;
                if(r.pnl_dollars > m_stats.largest_win)
                    m_stats.largest_win = r.pnl_dollars;
            }
            else
            {
                m_stats.losing_trades++;
                total_losses_pnl += MathAbs(r.pnl_dollars);
                if(MathAbs(r.pnl_dollars) > m_stats.largest_loss)
                    m_stats.largest_loss = MathAbs(r.pnl_dollars);
            }
        }

        // Calculate averages
        m_stats.win_rate = (double)m_stats.winning_trades / m_stats.total_trades;
        m_stats.avg_win = (m_stats.winning_trades > 0) ? total_wins_pnl / m_stats.winning_trades : 0;
        m_stats.avg_loss = (m_stats.losing_trades > 0) ? total_losses_pnl / m_stats.losing_trades : 0;
        m_stats.avg_rr = total_rr / m_stats.total_trades;
        m_stats.avg_mae = total_mae / m_stats.total_trades;
        m_stats.avg_mfe = total_mfe / m_stats.total_trades;
        m_stats.avg_trade_duration_hours = total_duration / m_stats.total_trades;

        // Profit factor
        m_stats.profit_factor = (total_losses_pnl > 0) ? total_wins_pnl / total_losses_pnl : 0;

        // Calculate Sharpe ratio
        m_stats.sharpe_ratio = CalculateSharpeRatio();

        // Calculate Sortino ratio
        m_stats.sortino_ratio = CalculateSortinoRatio();

        // Calculate max drawdown
        CalculateMaxDrawdown();

        // Calmar ratio = Return / Max Drawdown
        m_stats.calmar_ratio = (m_stats.max_drawdown > 0) ? m_stats.total_pnl / m_stats.max_drawdown : 0;

        // Calculate streaks
        CalculateStreaks();

        m_stats.last_updated = TimeCurrent();
    }

    //+------------------------------------------------------------------+
    //| Calculate Sharpe Ratio                                            |
    //+------------------------------------------------------------------+
    double CalculateSharpeRatio()
    {
        if(m_result_count < 2)
            return 0;

        // Calculate mean return
        double mean_return = 0;
        for(int i = 0; i < m_result_count; i++)
            mean_return += m_results[i].pnl_dollars;
        mean_return /= m_result_count;

        // Calculate standard deviation
        double variance = 0;
        for(int i = 0; i < m_result_count; i++)
        {
            double diff = m_results[i].pnl_dollars - mean_return;
            variance += diff * diff;
        }
        variance /= m_result_count;
        double std_dev = MathSqrt(variance);

        // Sharpe = (Mean Return - Risk Free Rate) / Std Dev
        // Assuming risk-free rate = 0
        return (std_dev > 0) ? mean_return / std_dev : 0;
    }

    //+------------------------------------------------------------------+
    //| Calculate Sortino Ratio (downside deviation only)                 |
    //+------------------------------------------------------------------+
    double CalculateSortinoRatio()
    {
        if(m_result_count < 2)
            return 0;

        double mean_return = m_stats.total_pnl / m_result_count;

        // Calculate downside deviation (only negative returns)
        double downside_variance = 0;
        int downside_count = 0;

        for(int i = 0; i < m_result_count; i++)
        {
            if(m_results[i].pnl_dollars < 0)
            {
                double diff = m_results[i].pnl_dollars;
                downside_variance += diff * diff;
                downside_count++;
            }
        }

        if(downside_count == 0)
            return 0;

        downside_variance /= downside_count;
        double downside_dev = MathSqrt(downside_variance);

        return (downside_dev > 0) ? mean_return / downside_dev : 0;
    }

    //+------------------------------------------------------------------+
    //| Calculate Maximum Drawdown                                        |
    //+------------------------------------------------------------------+
    void CalculateMaxDrawdown()
    {
        if(m_equity_count == 0)
        {
            m_stats.max_drawdown = 0;
            m_stats.max_drawdown_percent = 0;
            return;
        }

        double peak = m_equity_curve[0];
        double max_dd = 0;
        double max_dd_percent = 0;

        for(int i = 1; i < m_equity_count; i++)
        {
            if(m_equity_curve[i] > peak)
                peak = m_equity_curve[i];

            double drawdown = peak - m_equity_curve[i];
            if(drawdown > max_dd)
            {
                max_dd = drawdown;
                if(peak > 0)
                    max_dd_percent = (drawdown / peak) * 100.0;
            }
        }

        m_stats.max_drawdown = max_dd;
        m_stats.max_drawdown_percent = max_dd_percent;
    }

    //+------------------------------------------------------------------+
    //| Calculate win/loss streaks                                        |
    //+------------------------------------------------------------------+
    void CalculateStreaks()
    {
        int current_streak = 0;
        int max_win_streak = 0;
        int max_loss_streak = 0;
        bool last_was_win = false;

        for(int i = 0; i < m_result_count; i++)
        {
            bool is_win = m_results[i].is_win;

            if(i == 0)
            {
                current_streak = 1;
                last_was_win = is_win;
            }
            else
            {
                if(is_win == last_was_win)
                {
                    current_streak++;
                }
                else
                {
                    if(last_was_win && current_streak > max_win_streak)
                        max_win_streak = current_streak;
                    else if(!last_was_win && current_streak > max_loss_streak)
                        max_loss_streak = current_streak;

                    current_streak = 1;
                    last_was_win = is_win;
                }
            }
        }

        // Check final streak
        if(last_was_win && current_streak > max_win_streak)
            max_win_streak = current_streak;
        else if(!last_was_win && current_streak > max_loss_streak)
            max_loss_streak = current_streak;

        m_stats.win_streak_max = max_win_streak;
        m_stats.loss_streak_max = max_loss_streak;
        m_stats.win_streak_current = (last_was_win) ? current_streak : 0;
        m_stats.loss_streak_current = (!last_was_win) ? current_streak : 0;
    }

    //+------------------------------------------------------------------+
    //| Get statistics                                                    |
    //+------------------------------------------------------------------+
    void GetStatistics(PerformanceStats &stats)
    {
        stats = m_stats;
    }

    //+------------------------------------------------------------------+
    //| Print statistics report                                           |
    //+------------------------------------------------------------------+
    void PrintReport()
    {
        Print("=====================================================");
        Print("     STATISTICAL VALIDATION REPORT");
        Print("=====================================================");
        Print("Total Trades: ", m_stats.total_trades);
        Print("Wins: ", m_stats.winning_trades, " (", DoubleToString(m_stats.win_rate * 100, 1), "%)");
        Print("Losses: ", m_stats.losing_trades, " (", DoubleToString((1 - m_stats.win_rate) * 100, 1), "%)");
        Print("");
        Print("--- P&L Metrics ---");
        Print("Total P&L: $", DoubleToString(m_stats.total_pnl, 2));
        Print("Average Win: $", DoubleToString(m_stats.avg_win, 2));
        Print("Average Loss: $", DoubleToString(m_stats.avg_loss, 2));
        Print("Largest Win: $", DoubleToString(m_stats.largest_win, 2));
        Print("Largest Loss: $", DoubleToString(m_stats.largest_loss, 2));
        Print("Profit Factor: ", DoubleToString(m_stats.profit_factor, 2));
        Print("");
        Print("--- Risk-Adjusted Metrics ---");
        Print("Sharpe Ratio: ", DoubleToString(m_stats.sharpe_ratio, 2));
        Print("Sortino Ratio: ", DoubleToString(m_stats.sortino_ratio, 2));
        Print("Calmar Ratio: ", DoubleToString(m_stats.calmar_ratio, 2));
        Print("Max Drawdown: $", DoubleToString(m_stats.max_drawdown, 2),
              " (", DoubleToString(m_stats.max_drawdown_percent, 1), "%)");
        Print("");
        Print("--- Trade Quality ---");
        Print("Average R:R: ", DoubleToString(m_stats.avg_rr, 2));
        Print("Average MAE: ", DoubleToString(m_stats.avg_mae, 5));
        Print("Average MFE: ", DoubleToString(m_stats.avg_mfe, 5));
        Print("Avg Trade Duration: ", DoubleToString(m_stats.avg_trade_duration_hours, 1), " hours");
        Print("");
        Print("--- Streaks ---");
        Print("Max Win Streak: ", (int)m_stats.win_streak_max);
        Print("Max Loss Streak: ", (int)m_stats.loss_streak_max);
        Print("Current Streak: ", (m_stats.win_streak_current > 0) ?
              DoubleToString(m_stats.win_streak_current, 0) + " wins" :
              DoubleToString(m_stats.loss_streak_current, 0) + " losses");
        Print("=====================================================");
    }

    //+------------------------------------------------------------------+
    //| Export equity curve to CSV                                        |
    //+------------------------------------------------------------------+
    bool ExportEquityCurve(string filename = "equity_curve.csv")
    {
        int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_COMMON);
        if(handle == INVALID_HANDLE)
            return false;

        FileWriteString(handle, "Trade,Equity\n");

        for(int i = 0; i < m_equity_count; i++)
        {
            FileWriteString(handle, IntegerToString(i + 1) + "," +
                          DoubleToString(m_equity_curve[i], 2) + "\n");
        }

        FileClose(handle);
        return true;
    }

private:
    //+------------------------------------------------------------------+
    //| Reset statistics                                                  |
    //+------------------------------------------------------------------+
    void ResetStats()
    {
        m_stats.total_trades = 0;
        m_stats.winning_trades = 0;
        m_stats.losing_trades = 0;
        m_stats.win_rate = 0;
        m_stats.total_pnl = 0;
        m_stats.avg_win = 0;
        m_stats.avg_loss = 0;
        m_stats.largest_win = 0;
        m_stats.largest_loss = 0;
        m_stats.profit_factor = 0;
        m_stats.sharpe_ratio = 0;
        m_stats.sortino_ratio = 0;
        m_stats.calmar_ratio = 0;
        m_stats.max_drawdown = 0;
        m_stats.max_drawdown_percent = 0;
        m_stats.avg_rr = 0;
        m_stats.avg_mae = 0;
        m_stats.avg_mfe = 0;
        m_stats.avg_trade_duration_hours = 0;
        m_stats.win_streak_current = 0;
        m_stats.loss_streak_current = 0;
        m_stats.win_streak_max = 0;
        m_stats.loss_streak_max = 0;
        m_stats.last_updated = 0;
    }
};
