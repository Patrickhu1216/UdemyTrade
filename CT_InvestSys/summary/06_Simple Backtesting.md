# Lecture 1 量化回測實作：Z-Score 輪動策略與基準線評估

本篇筆記記錄如何從零建構一個穩健的策略回測函式。我們將計算每日報酬率、處理邊界狀況（NaN 處理），並實作一個基於狀態機（State-Machine）的倉位追蹤邏輯，最後與「買入並持有 SPY」的基準線進行對比。

---

## 核心觀念：回測最常見的致命錯誤

在正式進入代碼前，必須釐清一個微觀結構上的關鍵概念：
> **訊號產生價格 (Signal Price) $\ne$ 實際交易價格 (Transaction Price)**
> 許多市面上的開源回測套件常犯一個錯誤：在 **Day T** 的收盤盤後計算出 Z-Score 觸發訊號，卻直接假設策略能以 **Day T** 的收盤價（Closing Price）完成換倉。
> *   **現實情況：** 當你收盤後拿到數據並跑完演算法時，市場已經關閉。
> *   **正確作法：** Day T 盤後產生訊號，必須在 **Day T+1 的開盤（Open Price）** 執行交易。
> 
> *註：本策略由於屬於低頻輪動（平均一年僅約 5 次交易），為了教學與概念驗證（PoC）目的，此處暫時簡化為「當天觸發、隔天開盤直接享有完整報酬」的邏輯，但在實盤部署前必須將其細化至下一個交易日的 Open。*

---

## 第一步：特徵工程優化（計算每日報酬率）

在進行回測前，我們需要資產的**每日百分比變動（Daily Returns）**。為了維持數據完整性，我們不使用 `dropna()`，而是將首日的 `NaN` 以 `0` 填補。

```python
import pandas as pd
import numpy as np

# 1. 計算 SPY 與 RSP 的每日報酬率
df_prices['spy_return'] = df_prices['SPY'].pct_change().fillna(0)
df_prices['rsp_return'] = df_prices['RSP'].pct_change().fillna(0)

# 2. 重新進行訓練/測試集分割 (切換至 Out-of-Sample 區間)
# df_test = df_prices.loc[:out_of_sample_date]

```
---

## 第二步：撰寫回測主函式

```python
def backtest_zscore_with_benchmark(
    df: pd.DataFrame,
    z_col: str,
    threshold: float,
    spy_ret_col: str,
    rsp_ret_col: str,
    benchmark_ret_col: str = None,
    initial_position: str = None
) -> pd.DataFrame:
    """
    執行 Z-Score 統計套利輪動策略的回測函式。
    
    參數:
    - df: 包含價格與報酬率的原始 DataFrame
    - z_col: 用於評估的 Z-Score 欄位名稱 (例如: '1m_zscore')
    - threshold: 觸發臨界值 (正負對稱，例如: 2.0)
    - spy_ret_col: SPY 的每日報酬率欄位名稱
    - rsp_ret_col: RSP 的每日報酬率欄位名稱
    - benchmark_ret_col: 基準線報酬率欄位，預設為 None (自動指派為 SPY)
    - initial_position: 初始持倉狀態 ('SPY' 或 'RSP')
    """
    
    # 複製 DataFrame 避免改動原始數據
    df_bt = df.copy()
    
    # 1. 設定基準線 (Benchmark)
    if benchmark_ret_col is None:
        benchmark_ret_col = spy_ret_col
        
    # 2. 嚴格過濾 NaN：僅針對當前觀測的 Z-Score 欄位剔除無效行，保留其餘歷史數據
    df_bt = df_bt.dropna(subset=[z_col])
    
    # 3. 初始化持倉欄位 (Position Column)
    df_bt['position'] = np.nan
    
    # =====================================================================
    # 4. 狀態機交易邏輯 (State-Machine Logic)
    # =====================================================================
    # 規則 A：當 Z-Score 超過正向門檻，100% 換倉至 RSP
    df_bt.loc[df_bt[z_col] > threshold, 'position'] = 'RSP'
    
    # 規則 B：當 Z-Score 低於負向門檻，100% 換倉至 SPY
    df_bt.loc[df_bt[z_col] < -threshold, 'position'] = 'SPY'
    
    # =====================================================================
    # 5. 邊界條件處理與訊號連續性維持 (Forward Fill)
    # =====================================================================
    # 檢查第一筆歷史數據是否落在觸發區間內
    if pd.isna(df_bt['position'].iloc[0]):
        if initial_position is None:
            raise ValueError("【錯誤】第一筆數據未觸發任何規則，請明確指定 initial_position ('SPY' 或 'RSP')。")
        
        # 指派初始倉位給首行
        df_bt.loc[df_bt.index[0], 'position'] = initial_position
        
    # 使用 正向填充 (Forward Fill) 技術：
    # 當 Z-Score 回歸到 ±2σ 之間時，持倉狀態將完美延續前一天的決定，直到觸發反向門檻
    df_bt['position'] = df_bt['position'].ffill()
    
    # =====================================================================
    # 6. 關鍵：時間序列平移 (Shift) 防範未來函數 —— 下堂課核心
    # =====================================================================
    # 由於當天收盤才確認訊號，實際持倉部位的報酬率必須從「明天」開始生效
    # df_bt['traded_position'] = df_bt['position'].shift(1) 
    
    return df_bt

```

## 邏輯核心心法：為什麼 Forward Fill (ffill) 如此強大？

在代碼中，df_bt['position'] = df_bt['position'].ffill() 

這一行直接解決了區間內隨機震盪的持倉維持問題。

**1. 區間外觸發：** 
     當 Z-Score 飆升至 +2.3，代碼會將當天標記為 'RSP'。

**2. 均值回歸途中：** 
     隔天 Z-Score 回落至 +1.5（未觸發任何規則，理論上是 NaN）。

**3. 透過 ffill：** 
     系統會自動讀取昨天的狀態（'RSP'）並複製到今天。這意味著橡皮筋只要沒有拉扯到另一端的極限（$-2.0$），我們的輪動部位就會牢牢鎖定在 RSP，直到趨勢完全反轉。