# Lecture 1 量化回測實作：Z-Score 輪動策略與基準線評估

本篇筆記記錄如何從零建構一個穩健的策略回測函式。我們將計算每日報酬率、處理邊界狀況（NaN 處理），並實作一個基於狀態機（State-Machine）的倉位追蹤邏輯，最後與「買入並持有 SPY」的基準線進行對比。

<br>

## 核心觀念：回測最常見的致命錯誤

在正式進入代碼前，必須釐清一個微觀結構上的關鍵概念：
> **訊號產生價格 (Signal Price) $\ne$ 實際交易價格 (Transaction Price)**
> 許多市面上的開源回測套件常犯一個錯誤：在 **Day T** 的收盤盤後計算出 Z-Score 觸發訊號，卻直接假設策略能以 **Day T** 的收盤價（Closing Price）完成換倉。
> *   **現實情況：** 當你收盤後拿到數據並跑完演算法時，市場已經關閉。
> *   **正確作法：** Day T 盤後產生訊號，必須在 **Day T+1 的開盤（Open Price）** 執行交易。
> 
> *註：本策略由於屬於低頻輪動（平均一年僅約 5 次交易），為了教學與概念驗證（PoC）目的，此處暫時簡化為「當天觸發、隔天開盤直接享有完整報酬」的邏輯，但在實盤部署前必須將其細化至下一個交易日的 Open。*

<br>

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

<br>

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

<br>

## 邏輯核心心法：為什麼 Forward Fill (ffill) 如此強大？

在代碼中，df_bt['position'] = df_bt['position'].ffill() 

這一行直接解決了區間內隨機震盪的持倉維持問題。

**1. 區間外觸發：** 
     當 Z-Score 飆升至 +2.3，代碼會將當天標記為 'RSP'。

**2. 均值回歸途中：** 
     隔天 Z-Score 回落至 +1.5（未觸發任何規則，理論上是 NaN）。

**3. 透過 ffill：** 
     系統會自動讀取昨天的狀態（'RSP'）並複製到今天。這意味著橡皮筋只要沒有拉扯到另一端的極限（$-2.0$），我們的輪動部位就會牢牢鎖定在 RSP，直到趨勢完全反轉。

<br>

## 重點整理：門檻策略與基準線對齊 (Backtest 1)

本篇筆記記錄如何建構一個基於固定滾動視窗（Chosen Window）的 Z-Score 價差輪動策略回測系統。核心目標是確定每日的持倉狀態（Position），並以該持倉資產當天的每日報酬率（Daily Return）作為策略報酬率。

<br>

## 一、 回測設計之核心考量與三大痛點

在實作此策略的回測函式時，必須在代碼中嚴格處理以下三個量化實務問題：

### 1. 訊號延遲與時間序列平移（避免未來函數）
*   **邏輯痛點：** 我們是在**每天收盤後（End of Day）**才計算出當天的 Z-Score 並進行條件評估。如果當天收盤的 Z-Score 超過了設定門檻（Threshold），我們無法在當天盤中進行交易，也無法享有當天的收盤報酬。
*   **解決方案：** 實際的交易與持倉改變必須發生在**隔天（Next Day）**。因此，在代碼邏輯中，必須將計算出來的 `Position` 欄位**向下平移 1 列（`.shift(1)`）**。
*   **重要性：** 這是為了防範回測中最致命的「未來函數（Look-ahead bias）」，確保我們不會誤用了 market close 後才得知卻無法執行的交易報酬。

### 2. 初始倉位指派（Initial Position Inference）
*   **邏輯痛點：** 回測開始的第一天（或是尚未觸發 $\pm\sigma$ 門檻的初期區間），由於沒有歷史訊號引導，持倉欄位會呈現 `NaN`。
*   **解決方案：** 必須由外部手動指派一個 `initial_pos`。
*   **判斷技巧：** 可以透過觀察 Z-Score 的歷史走勢圖來進行方向推論。以「一個月滾動視窗（One-Month Window）」為例，若歷史曲線在起點時處於 $0$ 以下且呈現**向上趨勢（Trending Up）**，代表它剛從負向門檻（$-2$）反彈上來。依據策略邏輯，可合理推論初始倉位為 **`SPY`**。

### 3. 現實回測限制與假設前提
本回測採用了簡化的「每日報酬率代入法」，雖足以作為教學與概念驗證（PoC），但在實際投入真金白銀（Real Money）前，需注意以下與現實市場的落差：
*   **無法完全模擬買賣行為：** 未精準模擬買入與賣出的帳戶資金變動。
*   **股利發放（Dividends）：** 簡化模型預設拿到了該資產的所有每日股利，但實際交易中不一定能完全複製。
*   **交易成本（Transaction Costs）：** 未計入實際交易時必然會遇到的**買賣價差（Bid-Ask Spread）**與手續費。
*   **本策略的防禦優勢：** 幸運的是，本輪動策略屬於**極低頻交易**（預估一年僅約 5 次交易），因此交易成本與滑點對整體回測績效的侵蝕非常微弱，此簡化方法在目前的評估階段已足夠精準（Good enough）。

<br>

# Lecture 2：Z-Score 狀態機橫斷面與資料流驗證 (Backtest 1)

本篇筆記記錄如何透過逐行執行與觀測 DataFrame，驗證 Z-Score 跨資產輪動策略（SPY/RSP）在回測時的資料流變化。重點在於理解**邊界條件處理**、**狀態連續性**以及**防範未來函數的時間平移機制**。

---

## 一、 輸入資料結構矩陣 (DF Prices Input Summary)

在進入回測主函式前，輸入的 `df_prices` 已經過特徵工程處理，基本架構如下：
*   **資產價格欄位：** `SPY`、`RSP` 原始收盤價。
*   **資產報酬率：** `spy_return`、`rsp_return`（滾動每日百分比變動）。
*   **價差特徵：** `Rolling_1M_Diff`（一個月滾動報酬率差值）。
*   **策略特徵 (Z-Score)：** `Rolling_1M_Diff_Z`（由上述差值標準化後的 Z-Score，即代碼中的 `z_col`）。

<br>

## 二、 逐步拆解：回測三大核心邏輯與欄位演變

為了看清代碼對資料結構的實質影響，以下模擬講師在 Jupyter Notebook 中逐步拆解的過程：

### 步驟 1：利用 `subset` 嚴格過濾初始 `NaN`
為了計算 1 個月的滾動指標，時間序列初期必然會產生無效值（`NaN`）。

```python
df_copy = df.dropna(subset=[z_col]).copy()
```

- 效果：系統會精準剔除該 Z-Score 欄位為 NaN 的橫斷面列。

- 關鍵：這裡不使用全域 `df.dropna()`，因為 RSP 與 SPY 的歷史上市長度不同（SPY 歷史較長）。使用 `subset` 可以完整保留所有有效的資產價格與報酬率資訊，數據起跑點成功鎖定在 2003 年 6 月。

<br>

### 步驟 2：狀態機訊號標記與「不對稱稀疏性」現象

初始化 Position 欄位並寫入交易規則：

```python
df_copy['Position'] = np.nan
df_copy.loc[df_copy[z_col] > 2.0, 'Position'] = 'RSP'
df_copy.loc[df_copy[z_col] < -2.0, 'Position'] = 'SPY'
```

- 現象觀測： 此時查看 `Position` 欄位，會發現高達 90% 以上的欄位皆為 `NaN`（數千行數據中可能僅有 143 行有訊號）。

- 原因： 因為 Z-Score 只有在極端行情（拉扯超過 $\pm 2\sigma$ 門檻）時才會被賦予 'SPY' 或 'RSP' 字串。當指標回歸到區間之內時，在未處理前皆會呈現無效值。

<br>

### 步驟 3：邊界修復與正向填充（波段持倉連續性）

為了維持倉位的連續性，必須先處理「第一天既沒超標也沒低標」的盲區，隨後進行 forward fill：

```python
# 1. 初始邊界外推 (Extrapolation)
df_copy.loc[df_copy.index[0], 'Position'] = 'SPY' 

# 2. 狀態連續性維持
df_copy['Position'] = df_copy['Position'].ffill()
```

- 實例追蹤（以 2024 年 7 月至 8 月真實歷史數據為例）：
    1. 2024-07-26： Z-Score 跌破門檻（來到 -2.49），觸發規則，該列被精確標記為 'SPY'。
    
    2. 2024-08-13： 隨後數日，Z-Score 出現均值回歸，回落至 $\pm 2$ 區間之內。此時該列原本會得到 NaN。
    
    3. ffill() 的威力： 透過正向填充，橡皮筋只要沒有拉扯到另一端（即未突破另一側的 +2.0 門檻變更為 RSP 之前），系統會自動複 製前一天的狀態，讓持倉一直接續為 'SPY'。這完美模擬了波段交易的持倉行為。


## 三、 進階：對齊實盤交易時間軸（.shift(1) 核心詳解）

這是整個回測模型能否對接現實的關鍵。

```python
df_copy['Position'] = df_copy['Position'].shift(1)
```

<br>

|交易日期 (Date)|當日盤後 Z-Score|未平移持倉 (Raw Position)|平移後實際持倉 (Shifted)|說明 / 現實交易行為對齊|
| ---- | ---- | ---- | ---- | ---- |
|07-26 (五)|-2.49 (觸發)|'SPY'|'RSP' (舊持倉)|盤後才算出訊號，當天已收盤，無法執行。當天你依然持有舊部位。|
|07-29 (一)|-1.80|NaN → 'SPY'|'SPY' (新持倉)|下一個交易日開盤執行交易。從今天起，策略才開始享有 SPY 的報酬。|

<br>

- 如果不執行 .shift(1)，代表你預知了 7 月 26 日收盤後才會產生的訊號，並在 7 月 26 日當天盤中提前偷看並享受了 SPY 的報酬。這在量化領域稱為未來函數（Look-ahead bias）。

- 透過 .shift(1) 將部位完美推遲到下一個交易日，回測曲線雖然在短期內可能看起來沒那麼驚人，但這才是實盤部署時，你雙眼能真正看到的真實損益（Realistic Performance）。

# Lecture 3： 量化回測實作筆記：策略收益計算與連續複利累積 (Backtest 1 - 完結篇)

## 一、 核心邏輯與資料清理

在完成時間軸平移（`.shift(1)`）後，回測系統進入邏輯清算階段。必須嚴格遵循以下順序，否則會導致報酬率與持倉錯配。

### 1. 清除平移造成的首列無效值 (Edge Case Handling)

*   **背景：** 由於 `Position` 欄位向下平移了一列（`shift(1)`），這會釋放出回測序列的第一行（Row 0），使其變成 `NaN`。
*   **解決方案：** 

    ```python
    df_copy = df_copy.dropna(subset=['Position'])
    '''

利用 `dropna` 精準將 `Position` 為 `NaN` 的首行刪除，確保後續計算報酬率時，每一行都有明確的持倉依據（`SPY` 或 `RSP`）。

<br>

### 2. 使用 np.where 進行條件廣播 (Vectorized Conditional Assignment)

為了高效計算策略的每日收益，我們使用 Numpy 的向量化條件判斷（效能等同於 Excel 中的 IF 函數），避免使用低效的 Python 循環（For-loop）：

```python
df_copy['Strategy_Return'] = np.where(
    df_copy['Position'] == 'RSP', # 條件 (Condition)
    df_copy[rsp_return_col],      # True: 指派 RSP 當日報酬
    df_copy[spy_return_col]       # False: 指派 SPY 當日報酬
)
```

*  **優勢：** 透過對齊後的 Position 欄位，Python 會自動執行矩陣廣播（Broadcasting），將當天持倉對應的資產日報酬率精準寫入 Strategy_Return。

<br>

### 3. 防禦性編程：填補潛在缺失值 (Safety Mechanism)

*  **作法：** 雖然經過清洗後不應再有 NaN，但為了防止極端數據或除錯時代碼崩潰，加入防禦性填補：

```python
df_copy['Strategy_Return'] = df_copy['Strategy_Return'].fillna(0.0)
```

將任何潛在的無效報酬率設為 `0.0`，使其不影響後續的複利計算。

<br>

## 二、 連續複利（幾何累積報酬率）數學公式與實作

為了評估策略與基準線自「第一天」以來的總體表現，我們必須將每日的百分比報酬率進行**連續複利（Compounding）**計算。

### 1. 幾何收益率公式 (Geometric Return Formula)

累積報酬率並非將每日報酬率直接相加（算術加總），而是透過幾何相乘。公式如下：

$$Cumulative\ Return_t = \prod_{i=1}^{t} (1 + R_i) - 1$$

*   **步驟解構：**
    1. 將每日報酬率 $R_i$ 加上 $1$，代表當天的本利和（例如：當日報酬率 2% $\rightarrow$ 本利和 1.02）。
    2. 使用 `cumprod()` 將歷史上每一天的本利和連續相乘。
    3. 最終乘積結果減去 $1$（扣除初始本金），還原為累積百分比報酬率。

### 2. Pandas 向量化實作

```python
# 計算策略累積報酬率
df_copy['Cumulative_Strategy_Return'] = (1 + df_copy['Strategy_Return']).cumprod() - 1

# 計算基準線累積報酬率
df_copy['Cumulative_Benchmark_Return'] = (1 + df_copy[benchmark_return_col]).cumprod() - 1
```

<br>

## 三、 分析矩陣過濾與最終輸出 (Final Output Extraction)

回測模型內部包含了大量的 Z-Score 中間運算過程（Diff、Standard Deviation 等），在函式結束時，我們不需要將這些雜訊全部回傳。

必須使用雙重方括號 [[...]] 從 DataFrame 中提取出我們關心的核心分析維度：

```Python
return df_copy[[
    'Position',                     # 每日持倉狀態 (SPY / RSP)
    'Strategy_Return',              # 策略每日報酬率
    'Cumulative_Strategy_Return',   # 策略累積複利報酬率 (主線績效)
    benchmark_return_col,           # 基準線每日報酬率
    'Cumulative_Benchmark_Return'   # 基準線累積複利報酬率 (對照組)
]]
```

<br>

## 四、 實戰思維總結

### 嚴格的順序依賴性（Sequence Dependency）：

在量化工程中，「先平移時間軸（.shift(1)），才能對齊報酬率」的順序絕對不能顛倒。如果先指派了 Strategy_Return 才去做 shift，將會導致嚴重的未來函數，讓回測結果完全失真。

### 基於基準線（Benchmark）的相對優勢評估：
    
本策略的獲利核心在於捕捉 SPY（市值加權）與 RSP（等權重）之間的統計均值回歸特徵。單看策略的累積報酬率沒有意義，必須透過 Cumulative_Benchmark_Return（通常預設為大盤 SPY）作為對照組，才能清晰看見策略在何時產生超額報酬（Alpha），這也是下堂課圖表視覺化觀測的重點。

<br><br>

# Lecture 4：動態傳參、指標萃取與參數初步盲測 (Backtest 1 - Execution)


本篇記錄如何正確呼叫先前寫好的回測函式，利用 Python 的 F-string 機制建立可動態擴充的參數架構，並透過終端點（Terminal Node）資料萃取，美化策略績效輸出，最後進行初步的參數敏感度分析（Sensitivity Analysis）。

<br>

## 一、 函式呼叫與動態參數配置 (Dynamic Parameter Config)

為了方便未來進行**網格搜索（Grid Search）**或優化參數，我們不應在程式碼中將欄位名稱或超參數（Hyperparameters）硬編碼（Hard-code）。

### 1. 修正 Typo 與 F-string 自動化命名

*   **除錯修正：** 確認回測函式定義與回傳字典中的 `benchmark_return_col` 拼字正確（修正先前影片中的 `bench mark` 錯誤）。
*   **動態命名：** 透過定義 `z_score_window` 變數，配合 F-string 彈性組裝 DataFrame 的特徵欄位名稱。

```python
# 設定滾動視窗變數 (可自由更換為 '1M', '6M', '11M' 等)
z_score_window = "1M" 

# 呼叫回測主函式 (未傳入 benchmark_return_col 則預設以 SPY 為基準)
result_with_benchmark = backtest_zscore_strategy_with_benchmark(
    df=df_prices,
    z_col=f"rolling_{z_score_window}_diff_z", # 動態拼接：rolling_1M_diff_z
    threshold=1.5,                             # 初步設定 Z-Score 門檻
    spy_return_col="spy_return",
    rsp_return_col="rsp_return",
    initial_pos="SPY"                          # 透過圖表外推得到的初始倉位
)
```

<br>

## 二、 終端績效指標萃取與格式化輸出 (Performance Metrics)

在觀測回測結果 DataFrame 時，我們最關心的是整個歷史序列最後一天（Terminal Node）的累積複利成果。

### 1. 利用 .iloc[-1] 鎖定歷史終點

使用 .iloc[-1] 準確提取時間序列最後一列的累積收益率（本範例樣本內數據統計至 2019 年底，歷時約 21 年）：

```python
# 萃取策略與基準線的最終累積報酬率
cum_strategy_ret = result_with_benchmark['Cumulative_Strategy_Return'].iloc[-1]
cum_benchmark_ret = result_with_benchmark['Cumulative_Benchmark_Return'].iloc[-1]
```

### 2. 百分比轉換與格式化美化輸出

由於 DataFrame 內部儲存的報酬率為純小數（如 3.58 代表 358%），輸出時需乘以 100，並使用 np.round() 保留兩位小數：

```python
import numpy as np

# 計算超額報酬 (Alpha)
outperformance = (cum_strategy_ret - cum_benchmark_ret) * 100

print(f"Cumulative Strategy Return  : {np.round(cum_strategy_ret * 100, 2)}%")
print(f"Cumulative Benchmark Return : {np.round(cum_benchmark_ret * 100, 2)}%")
print(f"Outperformance (Alpha)      : {np.round(outperformance, 2)}%")
```

<br>

## 三、 參數敏感度盲測結果 (Parameter Sensitivity Testing)

透過動態更換 threshold（門檻值）與 z_score_window（時間視窗），展示了策略對不同超參數的敏感度。在忽略交易佣金的前提下（低頻交易受佣金影響極小），初步測試結果如下：

<br>

|測試組別|時間視窗 (Window)|Z-Score 門檻 (Threshold)|策略累積報酬|基準線累積報酬 (SPY)|超額報酬 (Alpha)|
|---|---|---|---|---|---|
|基準組|1 個月 (1M)|1.5|410.00%|358.00%|+52.00%|
|測試 B|1 個月 (1M)|2.0|19.00%|358.00%|-339.00% (失效)|
|測試 C|6 個月 (6M)|1.5|131.00%|358.00%|-227.00% (失效)|


### 數據背後的量化觀點

*  **門檻過高導致的「策略飢餓」（測試 B）：** 當門檻提高到 2.0 時，績效大幅滑落至 19%。這是因為 $\pm 2\sigma$ 的條件過於嚴苛，導致策略長期觸發不到訊號，狀態機無法及時換倉，錯失了大部分的均值回歸紅利。

* **視窗過長導致的「訊號鈍化」（測試 C）：** 將視窗拉長至 6M 時，策略績效同樣顯著落後大盤。這代表大盤（SPY）與等權重（RSP）之間的價差輪動屬於偏向中短期的統計套利機會，一旦特徵觀測期拉長到 6 個月，訊號會被過度平滑（Smoothed out），失去預測力。

<br>

## 四、 實戰思維總結

### 嚴防「樣本內過度擬合」（In-Sample Overfitting / Data Snooping）：

目前我們看到的 $410\%$ 對決 $358\%$ 的驚人超額報酬，純屬樣本內測試（In-Sample Testing）。這代表我們是在「已知歷史答案」的情況下調整參數。找出 1M 與 1.5 表現最好並不代表實盤能賺錢。

### 走向下一階段：樣本外驗證（Out-of-Sample）：
    
完美的優化參數必須經歷未曾參與過運算的樣本外數據（Out-of-Sample / Walk-forward Testing）洗禮，才能驗證該統計套利 Alpha 是否具備未來泛化能力（Generalization Power）。這也是我們建立這套高彈性回測架構的終極目的。

<br><br>

# Lecture 5：回測結果 Plotly 互動圖表與 Seaborn 雙色持倉狀態視覺化

本篇筆記記錄如何將 Backtest 1 的成果轉化為直觀的視覺化圖表。內容涵蓋：利用 Plotly 繪製基本的策略與基準線累積複利對照圖，以及利用 Pandas 的 `melt`（寬表轉長表）技術，重塑資料流，最終以 Seaborn Scatter Plot 實現「依持倉狀態（SPY/RSP）動態變色」的進階績效圖表。

<br>

## 一、 基礎對照：Plotly 互動式累積報酬率圖表

為了觀測策略在歷史大波段中何時產生超額報酬（Alpha），我們首先將策略日報酬與基準線日報酬抽出，送入封裝好的 Plotly 繪圖模組中。

```python
# 呼叫全域封裝的 Plotly 幾何累積收益圖表函式
cumulative_return_graph_Plotly(
    result_with_benchmark[['Strategy_Return', 'spy_return']]
)
```

### 核心觀測與 Patrick 的思考種子：

* **超額收益確認：** 在樣本內（In-Sample）期間，策略最終斬獲 410% 的累積收益，大幅跑贏大盤基準線（SPY）的 358%（超額報酬高達 52%）。

* **留白思考：** 仔細觀察策略與大盤拉開差距的「關鍵時間點」。究竟是什麼樣的市場環境（例如 2008 年金融海嘯），導致 Z-Score 頻繁觸發換倉？這個策略是否存在潛在的結構性缺陷？我們該如何優化？（此為下一章節的優化伏筆）。


<br>

## 二、 進階視覺化關鍵：Pandas melt() 寬表轉長表

我們的終極目標是繪製一張累積收益率曲線圖，但曲線上每一個點的顏色必須根據當天是持倉 SPY（如藍點）還是 RSP（如紅點）動態切換。

### 資料結構的阻礙 (Wide Form vs. Long Form)

原始的回測結果 `result_with_benchmark` 屬於寬表（Wide Form），日期在 Index，各指標獨立成欄。然而，Seaborn 等高階繪圖庫在處理分類顏色（hue）時，要求資料必須是長表（Long Form）。因此我們必須進行以下三步驟的資料洗滌與重塑：

### 1. 整理 Index 並重新命名

```Python
# 將 Date 從 Index 釋放出來變成普通欄位，並將預設的名稱 'index' 重新命名為 'date'
df_log = result_with_benchmark.reset_index().rename(columns={'index': 'date'})
```

### 2. 執行 pd.melt() 矩陣重塑

```Python
df_long = pd.melt(
    df_log,
    id_vars=['date', 'Position'],              # 保持不動的身份識別標籤
    value_vars=['Cumulative_Strategy_Return'], # 要被拆解壓平的數值欄位
    var_name='return_type',                    # 新增的分類標籤欄位名稱
    value_name='cumulative_return'             # 新增的數值欄位名稱
)
```

<br>

### 欄位重塑微觀矩陣對照圖解：

透過 melt，Pandas 將原本橫向展開的寬表格，縱向「壓扁」拉長，使每一列都成為一個獨立的觀測樣本：

```Plaintext
【變換前：Wide Form (df_log)】
date        Position    Cumulative_Strategy_Return    spy_return
2024-07-26  'RSP'       0.0144                        0.0050

↓ 經過 pd.melt() 縱向壓扁

【變換後：Long Form (df_long)】
date        Position    return_type                   cumulative_return
2024-07-26  'RSP'       'Cumulative_Strategy_Return'  0.0144
```

<br>

## 三、 Seaborn 動態雙色持倉圖表實作

### 為什麼要用 Scatter Plot（散點圖）代替 Line Plot（折線圖）？

在 Matplotlib 與 Seaborn 的底層架構中，`plt.plot()` 或 `sns.lineplot()` 不支援在同一條連續折線中根據條件（`hue`）動態切換顏色。

* **工程解決方案：** 我們改用 sns.scatterplot()。當我們將點的密度提高（每日一個點）、並將點的尺寸（s）微調放大時，無數個連續的散點在視覺上就會匯聚成一條極其平滑、且能精準隨持倉變色的「動態高亮收益曲線」。

```Python
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 初始化畫布
plt.figure(figsize=(10, 6))

# 2. 繪製動態持倉散點圖
sns.scatterplot(
    data=df_long,
    x='date',
    y='cumulative_return',
    hue='Position',          # 核心關鍵：根據持倉狀態 (SPY / RSP) 自動著色
    palette='Set1',          # 使用標準紅藍配色陣列
    s=5                      # 控制散點尺寸，使其緊密相連成線
)

# 3. 複製並套用標準技術圖表格式化 (生產級美化)
plt.title('Strategy Cumulative Return Colored by Position (In-Sample)', fontsize=14, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Cumulative Return (Decimal)', fontsize=12)
plt.xticks(rotation=45)     # 旋轉日期標籤避免重疊
plt.legend(frameon=False)   # 移除圖例周圍的黑框（美化視覺）
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

plt.show()
```

<br>

## 四、 2008 年金融海嘯實戰觀測與邏輯稽核

產出圖表後，經由歷史重大事件（Market Crises）對策略進行邏輯審查（Audit）是量化分析師的重要工作：

### 2008 年空頭市場觀測：
在 2008 年金融海嘯大崩盤期間，圖表顯示策略長期切換並鎖定在 RSP（等權重）狀態。

### 背後量化邏輯：
這代表在市場崩潰時，權值股（SPY 的核心，如大型金融、科技股）跌幅遠比其餘中小型股（RSP 的成分）更為慘烈。這導致 SPY 的報酬率嚴重落後 RSP，將兩者報酬率差值的 Z-Score 瘋狂推向正向極端值（突破 +1.5 或 +2.0），進而成功觸發狀態機全面進駐 RSP。

### 結論：
這種視覺化能讓我們一眼看出策略在面對系統性風險時的真實行為，為後續導入樣本外測試（Out-of-Sample Testing）與風控機制（Stop-Loss）提供了無可替代的直覺依據。