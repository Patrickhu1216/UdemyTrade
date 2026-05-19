
Building an Investment Trading Strategy – Quick Reference Sheet

1. Hypothesis Development

- Hypothesis: Periods exist when either SPY or RSP outperforms based on market

conditions.

- SPY: Market-cap weighted; favors large-cap stocks.

- RSP: Equal-weighted; favors small- and mid-cap stocks.

- Objective: Identify signals to determine which ETF to invest in.

2. Exploratory Data Analysis (EDA)

- Retrieve historical prices (e.g., from Yahoo Finance).

- Analyze cumulative returns to observe long-term trends.

- Calculate rolling returns to capture performance over different overlapping periods.

3. Rolling Returns

- Definition: Rolling returns are calculated over a specified time window (e.g., 1 month, 6

months, 1 year).

- Purpose: Identify consistency and performance trends across various market conditions.

- Key Metrics: Percentage of periods RSP outperforms SPY, maximum return, minimum

return.

4. Z-Score Analysis

- Z-Score: Measures the relative performance of SPY vs. RSP in terms of standard deviations

from the mean.

- Expanding Z-Scores: Prevent look-ahead bias by using only past data.

- Use Cases:

- Mean-reversion: Switch when z-scores exceed a threshold.

- Momentum: Identify sustained performance trends.

5. Train-Test Split

- Split the dataset into:

- In-Sample (Training): Historical data for parameter optimization.

- Out-of-Sample (Testing): New data for validating the strategy's robustness.

- Avoid look-ahead bias: Perform normalization and standardization independently on train

and test sets.

6. Volatility Overlay

- Purpose: Mitigate extreme downside risk and enhance stability.

- Method:

- High volatility threshold: Move to cash.

- Low volatility threshold: Re-enter the market

- Benefits: Preserve capital, improve risk-adjusted returns, and adapt to changing market

conditions.

7. Backtesting

- Process:

- Evaluate positions based on z-scores and thresholds.

- Use daily returns to calculate strategy performance.

- Incorporate a volatility filter for enhanced risk management.

- Metrics:

- Strategy returns vs. benchmark (SPY).

- Cumulative returns over time.

8. Performance Metrics

- Rolling Sharpe Ratio: Evaluate risk-adjusted returns over a rolling window.

- Rolling Maximum Drawdown: Assess the largest declines in portfolio value within a

specified window.

- Objective: Understand the trade-offs between return and risk.

9. Out-of-Sample Testing

- Purpose: Validate strategy robustness on unseen data.

- Use the last position from in-sample testing as the starting point.

- Compare out-of-sample performance to benchmark returns.

-------------------------------------------------------------------------------

# 一、 策略核心與資料探索（步驟 1-3）

此階段的核心在於驗證假設。利用「市值權重」與「等權重」的結構差異，尋找市場風格輪動的超額收益。

- 核心假設：
    - SPY（市值權重）： 動能集中在大型權值股（如巨頭行情、牛市後期）。
    - RSP（等權重）： 資金分散在中小型股（如普漲行情、經濟復甦期）。
    - 目標：尋找兩者切換的訊號。

- EDA 關鍵工具：
    - 累積報酬率： 看歷史大趨勢（定性分析）。
    - 滾動報酬率： 消除進場時間的擇時偏差（定量分析）。透過統計 「RSP 勝過 SPY 的時間比例」，
      確認這個策略是否存在統計優勢（Edge）。

# 二、 訊號生成與防止過度擬合（步驟 4-5）

此階段的核心在於將統計學應用於訊號觸發，並嚴格切分資料以防「作弊」（看未來）。

- Z-Score（相對強度指標）：
    - 用來衡量 SPY 相對於 RSP 是「超漲」還是「超跌」。
    - 擴展 Z-Score (Expanding Z-Score)： 隨著時間推進，計算範圍只包含「過去到現在」的資料。
     （極重要：防止 Look-ahead bias / 引入未來資料）。
    - 兩大交易邏輯：
        - 均值回歸 (Mean-Reversion)： Z-Score 太高或太低時，預期會修正，進行反向操作。
        - 動能 (Momentum)： Z-Score 突破臨界值時，順勢追擊。

- 回測的黃金法則 (Train-Test Split)：
    - In-Sample (訓練集)： 用來調整 Z-Score 參數（如：買入門檻設在 1.5 還是 2.0）。
    - Out-of-Sample (測試集)： 絕對不能參與參數調整，僅用於最後的「盲測」。
    - 標準化防禦： 訓練集與測試集的平均值、標準差必須獨立計算。

# 三、 風險控管與動態濾網（步驟 6）

這是策略能否在實戰中存活的關鍵。單純靠 Z-Score 可能會遇到市場系統性崩盤（雙殺），
因此需要加上波動率濾網 (Volatility Overlay)。

- 運作機制：
    - 市場恐慌（高波動）： 策略失效風險高，強制清倉持有現金（保本）。
    - 市場平穩（低波動）： 重新啟動 Z-Score 輪動策略。

- 目的： 犧牲一點牛市的潛在報酬，換取避開極端下行風險（Tail Risk）的能力。

# 四、 回測與多維度評估（步驟 7-9）

此階段的核心是全面檢驗策略的健康度。一個好的策略不能只看「總報酬率」，更要看「賺得穩不穩」。

- 回測執行細節：
    結合 Z-Score 訊號 + 波動率濾網，計算每日部位價值。

- 動態風險指標（比看單一數值更重要）：
    - 滾動夏普值 (Rolling Sharpe Ratio)： 
      觀察策略的「風險報酬比」是否在不同年份都能維持穩定（例如：不能只有 2020 年很高，其他年份都很低）。

    - 滾動最大回撤 (Rolling Max Drawdown)：
      掌握策略在任何連續期間內，可能面臨的最大虧損幅度。

- Out-of-Sample Testing：
    - 在未知的測試集數據上執行。
    - 部位連續性： 訓練集結束時的最後一個部位持倉，必須直接作為測試集的起點，確保回測連續性。
    - 指標對決： 最終的 OOS 績效必須擊敗基準（SPY 買入持有策略），且風險指標更優，策略才算開發成功。

五、 Flow

1. 發展假設 (SPY vs RSP)
2. 滾動報酬 EDA
3. 計算 Expanding Z-Score
4. 加入波動率濾網
5. 樣本內優化
6. 樣本外盲測 (Rolling Metrics 評估)