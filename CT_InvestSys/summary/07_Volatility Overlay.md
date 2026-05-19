# Lecture 1：波動率濾網與市場體制 (Volatility Overlay & Market Regimes)

## 1. 現有策略的痛點與發現

* **資產同步下跌的盲點**：在先前的配對交易回測中（根據 Z-Score 在 SPY 與 RSP 之間切換），發現在特定的極端時期（例如 2018 年末），**兩個資產的表現都會非常糟糕**。
* **Alpha 的回吐**：由於這些市場危機發生時，並未觸發 Z-Score 的切換閾值，傳統策略無法應對，導致先前累積的 Alpha（超額收益）幾乎全部損失。
* **解決核心**：必須引入一個新機制，在市場環境惡劣時**保護並留住 Alpha**。

<br>

## 2. 核心觀念：波動率濾網 (Volatility Overlay)
> **關鍵啟示**：波動率是預測市場即將發生危機、識別**市場體制（Market Regimes）**的最佳獨立（Standalone）指標之一。

* **空手變現（Go to Cash）**：引入波動率濾網的核心目的，是讓策略在波動率過高時，發出離場訊號：「此時既不要持有 SPY，也不要持有 RSP，**請全數轉為持有現金**。」 藉此避開系統性風險，保留利潤。

<br>

## 3. 指標選擇：為什麼不用 VIX？
許多人會直覺選擇 VIX 指數，但本課程**不推薦**直接使用，原因如下：
1. **隱含 vs. 實現**：VIX 是由 S&P 500 期權價格推算出的「隱含波動率」，反映的是市場參與者的「預期」而非當前市場實際發生的狀況。
2. **雜訊過多**：VIX 走勢非常神經質（Volatile），經常出現極端的暴漲與暴跌。
3. **更佳的替代方案**：相較之下，**滾動歷史波動率（Rolling Realized Volatility）**是更穩定、容易計算且隨手可得的指標。

> **講師的小建議**：如果你堅持要用 VIX，請務必加上**移動平均（Moving Average）**來平滑數值，絕對不要直接使用 VIX 的原始值（Raw values）。

<br>

## 4. 具體實作邏輯
* **參數設定**：採用 **20 天或 21 天**的滾動視窗（因為一個月大約有 21 個交易日），計算 S&P 500 **報酬率（Returns）**的滾動標準差。
* **年化處理 (Annualization)**：為了符合業界直覺（正常低風險時期年化波動率約在 10% ~ 25% 之間），需將結果**乘以 252 的平方根** ($\sqrt{252}$)。
* **規則邏輯**：
  * 當滾動波動率**飆升超越閾值**（例如設定在 20%） $\rightarrow$ **空手持有現金**。
  * 當波動率**回落至閾值以下** $\rightarrow$ **重新進場**，恢復原本的 SPY/RSP 切換策略。

<br>

## 5. Python 程式碼實作

### 步驟 1：計算年化滾動歷史波動率
必須針對資產的**報酬率（Return）**而非價格（Price）進行滾動標準差計算。

```python
# 建立 SPY 滾動歷史波動率新欄位 (以 20 天為視窗並進行年化處理)
df_prices['SPY_rolling_volatility'] = (
    df_prices['SPY_return']
    .rolling(window=20)
    .std() * (252 ** 0.5)
)
```

<br>

### 步驟 2：快速繪圖與視覺化檢視
利用 Pandas 內建功能快速畫出波動率走勢，以觀察低谷平靜期與高溫噴發期的市場體制。
```python
import matplotlib.pyplot as plt

# 快速繪製波動率曲線
df_prices['SPY_rolling_volatility'].plot()
plt.show()
```

<br>

## 6. 下一步 (Next Steps)

接下來我們將切換回 Python，著手修改 Backtest 函式。新版的回測架構與舊版高度相似，但我們需要傳入額外的參數（例如波動率閾值與現金機制邏輯）來完成這個進階策略。

<br><br>

# 補充：金融與量化投資核心觀念：什麼是 Alpha ($\alpha$)？

在金融與量化投資的領域中，**Alpha（$\alpha$，中文常譯為「阿爾法」）** 代表的是一個策略或投資組合所賺取的**「超額收益」**（Excess Return）。

簡單來說，它用來衡量**一個投資經理人或交易策略，究竟有沒有擊敗市場大盤的能力**。我們可以從以下三個核心層面來理解：

---

## 1. 超額收益的組成：Alpha vs. Beta

市場上的投資收益通常可以被拆解為兩種主要來源：

*   **Beta ($\beta$) 收益（市場收益）**：
    *   這是「隨波逐流的收益」。
    *   例如：你買進 S&P 500 指數基金（如 SPY），若大盤今年漲了 10%，你的資產也跟著漲 10%。這種不需要高超技術、只要承擔市場整體風險就能拿到的回報，就叫做 Beta 收益。
*   **Alpha ($\alpha$) 收益（絕對實力收益）**：
    *   這是「超越大盤的絕對實力」。
    *   例如：如果今年大盤（Beta）只漲了 10%，但你的量化策略透過精準的主動操作賺到了 15%，那麼多出來的 **5%** 就是這個策略幫你創造的 **Alpha**。

---

## 2. 在配對交易（Pairs Trading）中的角色

在本課程的脈絡中（SPY 與 RSP 的配對交易），Alpha 更是衡量策略成功與否的關鍵：

*   **策略的目標**：我們利用 SPY 和 RSP 之間的價差（Z-Score）進行來回切換，目的就是要在無論大盤漲跌的情況下，都比「單純死抱著大盤」賺得更多。這個高出來的獲利曲線，就是策略的 Alpha。
*   **為什麼課程提到要「保護 Alpha」？** 
    當 2018 年末或系統性危機發生時，SPY 和 RSP 會同步暴跌。如果策略此時還盲目地在兩者之間切換，先前靠實力賺來的超額收益（Alpha）就會被大盤的系統性風險給無情吞噬。
    因此，我們需要加入**波動率濾網（Volatility Overlay）**。在危機發生時「空手持有現金」，目的就是為了**把先前辛苦賺到的 Alpha 牢牢鎖住，不還給市場**。

---

## 3. 金融經典公式：資本資產定價模型 (CAPM)

在學術界與投資業界，Alpha 通常透過以下公式進行精準的數學定義：

$$R_p = R_f + \beta_p (R_m - R_f) + \alpha_p$$

### 參數說明：
*   $R_p$：你的投資組合總回報率
*   $R_f$：無風險利率（例如：美國國債收益率）
*   $R_m$：市場大盤的回報率（例如：S&P 500 指數回報率）
*   $\beta_p$：你的投資組合對市場的敏感度（Beta 係數）
*   $\alpha_p$：**投資組合的 Alpha（超額收益）**

---

## 總結

> **Beta** 是「跟著風口飛的收益」，只要站在風口上，誰都能拿到；
> **Alpha** 則是「風停了、甚至逆風時，你憑真本事飛得比別人高的那段距離」。
> 
> 作為一名優秀的量化交易員，終極目標就是去尋找、開發並在危機中保護這珍貴的 Alpha 來源。

<br><br>

# Lecture 2：打造進階回測函式（雙閾值波動率濾網）

在本次課程中，我們正式將「波動率濾網」寫入 Python 回測函式。為了避免不必要的交易成本，我們引入了**雙閾值（緩衝區）邏輯**，並使用精準、動態的 Pandas 技巧來更新持倉狀態。


## 1. 核心邏輯設計：為什麼要用「雙閾值」？
如果只設定單一波動率閾值（例如 25%），當市場波動率在 25% 上下微幅震盪時（第一天 25.01%、第二天 24.99%），策略就會陷入**天天频繁進出、瘋狂換倉**的窘境（被稱作 Whipsaws 雙向洗盤），這會產生極高的交易手續費。

為了建立**緩衝區（Buffer Zone）**，講師設計了兩個閾值：
*   **高波動閾值（High Vol Threshold）**：預設為 `0.26` (26%)。波動率必須**突破高線**，策略才會判定進入危險體制，全面清倉轉為**持有現金**。
*   **低波動閾值（Low Vol Threshold）**：預設為 `0.24` (24%)。進入現金狀態後，波動率必須**跌破低線**，策略才會判定市場冷卻，重新進場。

<br>

## 2. 函式定義與參數說明
為了教學清晰、拒絕含糊的簡寫，我們建立了一個名稱優雅且長度完整的函式：`backtest_zscore_strategy_with_volatility`。

### 參數清單
| 參數名稱 | 型態 | 說明 | 預設值 |
| :--- | :--- | :--- | :--- |
| `df` | DataFrame | 包含價格、報酬率、Z-Score、波動率的資料表 | *必填* |
| `z_col` | str | 儲存 Z-Score 的欄位名稱 | *必填* |
| `z_thresh` | float | 觸發 SPY/RSP 切換的 Z-Score 閾值 | *必填* |
| `spy_ret_col` | str | SPY 的報酬率欄位名稱 | *必填* |
| `rsp_ret_col` | str | RSP 的報酬率欄位名稱 | *必填* |
| `vol_col` | str | 儲存滾動歷史波動率的欄位名稱 | *必填* |
| `high_vol_thresh`| float | 觸發變現（Go to Cash）的高波動率閾值 | `0.26` |
| `low_vol_thresh` | float | 重新進場的低波動率閾值 | `0.24` |
| `benchmark_col`  | str | 基準大盤報酬率欄位 | `None` (預設同 SPY) |
| `initial_pos`    | str | 初始第一天的持倉（用於填補盲區） | `None` |
| `plot` | bool | 是否在函式結束時繪製回測圖表（便於教學） | `False` |

<br>

## 3. Python 程式碼實作與拆解

### 階段一：初始化與基礎 Z-Score 邏輯（同前一版）
此段落直接延用上一個回測函式的基礎邏輯，清理無效 Z-Score 並根據閾值初步標記 `position` 欄位（SPY 或 RSP），再利用 `ffill()` 向下填充。

```python
import numpy as np
import pandas as pd

def backtest_zscore_strategy_with_volatility(
    df, z_col, z_thresh, spy_ret_col, rsp_ret_col, vol_col,
    high_vol_thresh=0.26, low_vol_thresh=0.24, 
    benchmark_col=None, initial_pos=None, plot=False
):
    # 處理基準大盤
    if benchmark_col is None:
        benchmark_col = spy_ret_col
        
    # 清理資料：移除沒有有效 Z-Score 的行
    df = df.dropna(subset=[z_col]).copy()
    
    # 基礎 Z-Score 定位邏輯
    df['position'] = np.nan
    df.loc[df[z_col] > z_thresh, 'position'] = 'RSP'
    df.loc[df[z_col] <= -z_thresh, 'position'] = 'SPY'
    
    # 填補初始位置並向下填充
    if initial_pos is not None:
        df.iloc[0, df.columns.get_loc('position')] = initial_pos
    df['position'] = df['position'].ffill()
```

### 階段二：動態波動率濾網迴圈（核心精華）

我們在進入迴圈前，必須先透過第 0 天（第一筆數據）初始化一個名為 in_cash 的布林追蹤變數。

* **進階技巧：避免 Hardcoding 欄位索引**
為了防止未來欄位順序更動導致 `iloc` 報錯，我們使用 `df.columns.get_loc('position')` 動態獲取 `position` 的整數索引，從而安全地與 `iloc` 搭配使用。

```Python
# 評估第 0 天（第一天）是否一開始就處於高波動率環境
    in_cash = df[vol_col].iloc[0] > high_vol_thresh
    
    # 逐行（按天）掃描波動率體制
    for i in range(1, len(df)):
        current_vol = df[vol_col].iloc[i]
        
        if in_cash:
            # 如果目前是現金狀態，檢查是否跌破低閾值以重新進場
            if current_vol < low_vol_thresh:
                in_cash = False
        else:
            # 如果目前在市場內，檢查是否突破高閾值以全面變現
            if current_vol > high_vol_thresh:
                in_cash = True
                
        # 如果判定為 in_cash，動態將該行的 position 改寫為 'cash'
        if in_cash:
            pos_idx = df.columns.get_loc('position')
            df.iloc[i, pos_idx] = 'cash'
```

### 階段三：訊號遞延、報酬率計算（巢狀 if 轉換）

由於我們是在當天收盤後評估波動率與 Z-Score，實際交易必須在隔天（下一交易日）執行，因此持倉欄位必須向下 shift(1)。
在計算報酬率時，我們使用 np.where 來實作類似 Excel 巢狀 IF 的效果：

1. 判斷是否為 RSP $\rightarrow$ 給予 RSP 報酬率
2. 否則判斷是否為 SPY $\rightarrow$ 給予 SPY 報酬率
3. 皆非（即 cash） $\rightarrow$ 報酬率給予 0

```Python
# 交易訊號遞延一天（今天收盤做決定，明天開盤才交易）
    df['position'] = df['position'].shift(1)
    df = df.dropna(subset=['position']) # 移除 shift 產生的第一行 NaN
    
    # 計算策略報酬率 (巢狀 np.where 結構)
    df['strategy_return'] = np.where(
        df['position'] == 'RSP', 
        df[rsp_ret_col],
        np.where(df['position'] == 'SPY', df[spy_ret_col], 0)
    )
    
    # 講師個人的雙重保險小習慣（確保 cash 一定為 0）
    df['strategy_return'] = np.where(df['position'] == 'cash', 0, df['strategy_return'])
    
    # 計算策略累積報酬率
    df['cum_strategy_return'] = (df['strategy_return'] + 1).cumprod() - 1
```

### 階段四：基準大盤公平比對與輸出

**關鍵細節：**
因為第一天（第 0 行）是我們剛開始評估數據、尚未實際建立策略持倉的日子（策略報酬率在 shift 後已不包含第一天），為了做到基準大盤與策略「基準線一致（Apples to Apples）」，必須手動將基準大盤第一天的報酬率強行覆蓋為 0。否則，大盤第一天的漲跌就會被計入累積報酬中，導致比較基準不公平。

```Python
    # 確保基準大盤在起跑點公平（第一天不計入報酬）
    df['benchmark_return'] = df[benchmark_col].copy()
    df.iloc[0, df.columns.get_loc('benchmark_return')] = 0
    
    # 計算基準大盤累積報酬率
    df['cum_benchmark_return'] = (df['benchmark_return'] + 1).cumprod() - 1
    
    # 註：後續將在下一堂課加入 Plot 功能程式碼...
    return df
```

## 4. 亮點總結與後續
* **動態欄位定位法：**
利用 df.columns.get_loc('欄位名') 完美融合了標籤的靈活性與 iloc 的整數要求，是避免 hardcoding 的高階寫法。

* **基準線校準：**
手動將大盤第一天報酬歸零，體現了量化回測中對「細節（Attention to detail）」的極致追求，防止回測結果產生偏誤。

* **下一步：**
本段課程在此暫停，下一節我們將繼續在該函式內編寫 Plot 繪圖邏輯，並正式執行這個精妙的雙閾值波動率回測！

# Lecture 3：回測函式之波動率視覺化與資料輸出

在本節中，我們完成了進階回測函式的最後一塊拼圖：**動態圖表繪製（Plotting）與最終資料欄位的篩選輸出**。此圖表能直觀地呈現雙閾值緩衝區，並精準標記出策略轉為「持有現金（In Cash）」的歷史時段。

<br>

## 1. 視覺化設計核心與亮點
為了驗證波動率濾網的效果，我們利用 Matplotlib 建立了一個功能強大的圖表：
1.  **藍色實線**：代表 SPY 的年化滾動歷史波動率走勢。
2.  **紅色虛線（高閾值）**：代表危險警戒線（High Vol Threshold）。
3.  **綠色虛線（低閾值）**：代表安全進場線（Low Vol Threshold）。
4.  **橘色垂直虛線（現金狀態）**：高亮標示出策略因波動率過高而**全面空手、持有現金**的特定日期。

### 程式碼優化技巧：防止圖例（Legend）爆炸
在繪製橘色現金日（`axvline`）時，由於策略可能會有多達數百天處於現金狀態，如果每一次畫線都加上標籤（Label），圖例（Legend）就會出現數百個重複的 "In Cash"。
*   **講師的解決方案**：在迴圈中加入一個 `if` 條件判斷，**只針對第一個現金日賦予圖例標籤**，其餘日期則給予空字串（`""`），確保圖例乾淨整潔、只顯示一次。

<br>

## 2. Python 程式碼實作：圖表與輸出

請將以下程式碼接續在上一節回測函式的 `if plot:` 條件控制項下：

```python
    # === 階段五：波動率與持倉狀態視覺化 ===
    if plot:
        plt.figure(figsize=(10, 6))
        
        # 1. 繪製滾動歷史波動率主線
        plt.plot(
            df.index, 
            df[vol_col], 
            color='blue', 
            label='SPY Rolling Volatility'
        )
        
        # 2. 繪製高/低波動率閾值橫線 (f-string 動態顯示數值)
        plt.axhline(
            high_vol_thresh, 
            color='red', 
            linestyle='--', 
            label=f'High Vol Threshold ({high_vol_thresh})'
        )
        plt.axhline(
            low_vol_thresh, 
            color='green', 
            linestyle='--', 
            label=f'Low Vol Threshold ({low_vol_thresh})'
        )
        
        # 3. 提取所有持倉為現金的日期索引
        cash_days = df[df['position'] == 'cash'].index
        
        # 4. 逐日繪製橘色垂直虛線以標記現金期
        for cash_day in cash_days:
            # 關鍵技巧：只為第一個現金日設定圖例標籤，避免圖例重疊爆炸
            if cash_day == cash_days[0]:
                legend_label = 'In Cash'
            else:
                legend_label = ''
                
            plt.axvline(
                x=cash_day, 
                color='orange', 
                linestyle=':',  # 粗點狀或特殊虛線樣式
                label=legend_label
            )
            
        # 5. 圖表格式化優化
        plt.title('Volatility and Strategy Positioning')
        plt.xlabel('Date')
        plt.ylabel('Rolling Volatility (Annualized)')
        plt.legend(frameon=False) # 關閉圖例的外框
        plt.show()

    # === 階段六：篩選關鍵欄位並輸出 ===
    # 使用雙重方括號，僅隔離出回測分析所需的關鍵核心欄位
    return df[[
        'position', 
        'strategy_return', 
        'cum_strategy_return',
        'benchmark_return',  # 即原始的 benchmark_col
        'cum_benchmark_return', 
        vol_col
    ]]
```

<br>

## 3. 重點回顧與核心觀念
### 雙閾值緩衝區的效果：
透過圖表可以清晰看到，紅線與綠線之間構成了一個穩定的緩衝體制。這能有效過濾掉波動率在臨界點反覆震盪時帶來的「一日頻繁更換持倉」訊號，大幅降低交易成本與雙向洗盤（Whipsaws）的風險。

### 動態變數繪圖：
圖表中的 X 軸、Y 軸以及橫線數值完全基於函式傳入的變數（如 vol_col, high_vol_thresh），沒有任何硬編碼（Hardcoding），這使得該函式具備極高的複用性，未來可以輕鬆測試不同的波動率參數。


# 策略優化：加入波動率濾網 (Backtest 2: Adding a Volatility Overlay)

在第二版的回測中，我們在原有策略的基礎上引入了**波動率濾網（Volatility Overlay）**。其核心邏輯是設定特定的波動率閾值，一旦市場波動率超越該門檻，策略將主動清倉並**轉換為持有現金（Switch to Cash）**。

此項進階優化具備以下四大核心效益：

<br>

## 核心效益與設計原理

### 1. 降低極端下行風險 (Mitigating Extreme Downside Risk)
*   **避開市場壓力區**：高波動率通常與市場壓力（Market Stress）及不確定性高度相關。
*   **資產保護機制**：透過在這些高風險時期果斷轉為現金，策略能成功避開潛在的大幅回撤（Large Drawdowns），進而達到保護本金（Preserving Capital）的效果。

### 2. 提升風險調整後收益 (Enhancing Risk-Adjusted Returns)
*   **平滑收益曲線**：在市場劇烈波動時退場守候，能有效平滑策略的整體收益輪廓（Return Profile）。
*   **優化效率指標**：降低投資組合的整體波動度後，將能顯著提升衡量策略品質的關鍵指標，例如**夏普比率（Sharpe Ratio）**與**索提諾比率（Sortino Ratio）**。

### 3. 優化跨市場體制的穩定性 (Improved Stability Across Market Regimes)
*   **動態環境適應**：波動率濾網確保了策略具備動態適應不同市場環境（Market Conditions）的能力。
*   **現金避風港**：當市場進入避險（Risk-off）或動盪不安的體制時，現金能作為最佳的避風港，為整體投資組合提供堅實的穩定度。

### 4. 保留資金的選擇權與靈活性 (Preserving Optionality)
*   **維持流動性**：在高波動時期鎖定現金，意味著策略保留了極佳的流動性與未來操作的選擇權（Optionality）。
*   **高效重新進場**：當波動率回落、市場重新恢復穩定時，策略擁有充足的彈藥能在第一時間進行高效率的重新投資（Reinvest）。

---

## 總結

加入波動率濾網是配對交易策略中非常關鍵的一步技術精煉。它**將「下行風險防禦」放在首位**，同時又保留了在市場相對平靜、健康時參與增長的獲利能力。

透過這種基於波動率框架的主動風險管理，策略在面對不利的市場環境時，將展現出更高的**穩健性（Robustness）**與**抗風險韌性（Resilience）**。

<br><br>

# Lecture 4：執行雙閾值波動率回測與實證結果

在本節課程中，我們正式代入參數來執行先前寫好的進階回測函式（包含雙閾值波動率濾網），並深入分析回測圖表、探討量化交易中「波動率特徵」的關鍵不變性。

<br>

## 1. 回測設定與參數配置 (In-Sample Backtest)

為了確保測試基準一致，我們首先重新隔離出**樣本內（In-Sample）**的價格數據，並維持原有的 1 個月滾動 Z-Score 視窗與 1.5 倍標準差閾值。

### 雙閾值緩衝區設定值
根據先前的測試經驗，本次回測將目標波動率鎖定在 **30%** 左右，並建立上下各 2% 的緩衝空間以防範一日頻繁換倉（Whipsaws）：
*   **高波動閾值 (`high_vol_thresh`)**：設定為 `0.32` (32%)。
*   **低波動閾值 (`low_vol_thresh`)**：設定為 `0.28` (28%)。

### Python 實作程式碼

```python
# 1. 重新隔離出樣本內數據 (因為先前持續新增了波動率等欄位)
df_in_sample = df_prices.loc[:"2018"].copy() # 依據課程設定隔離樣本內

# 2. 定義 Z-Score 欄位名稱與視窗大小
window = 21 # 一個月約 21 個交易日
z_col_name = f"rolling_z_score_{window}_diff_Z"

# 3. 呼叫進階回測函式
result_with_vol_filter = backtest_zscore_strategy_with_volatility(
    df=df_in_sample,
    z_col=z_col_name,
    z_thresh=1.5,
    spy_ret_col="SPY_Return",
    rsp_ret_col="RSP_Return",
    vol_col="SPY_rolling_volatility",
    high_vol_thresh=0.32,   # 高波動警戒線
    low_vol_thresh=0.28,    # 低波動安全線
    initial_pos="SPY",      # 初始持倉
    plot=True               # 開啟視覺化圖表
)

# 4. 提取並輸出最終的策略累積報酬率與大盤累積報酬率
final_strategy_return = result_with_vol_filter['cum_strategy_return'].iloc[-1]
final_benchmark_return = result_with_vol_filter['cum_benchmark_return'].iloc[-1]

print(f"策略最終累積報酬率: {final_strategy_return:.2%}")
print(f"基準大盤累積報酬率: {final_benchmark_return:.2%}")
```

<br>

## 2. 實證結果觀測與分析
執行回測後，觀察產生的波動率定位圖表，可以得出以下核心結論：

* **績效顯著提升（Huge Outperformance）：**
加入波動率濾網後，策略表現出現了大幅度的增長。這印證了講師先前的觀點：「波動率」應該作為幾乎每一個量化交易模型中的核心特徵（Feature）。

* **現金觸發頻率低：**
當高波動閾值設在 32% 這樣的高位時，策略轉為現金的次數並不會太頻繁。

* **尋找臨界點的平衡（Sweet Spot）：**
    * 設得太低：策略會過於頻繁地進出現金，增加交易成本並侵蝕正常市況下的獲利。
    * 設得太高：濾網形同虛設，在市場大跌時完全無法觸發變現機制。

<br>

## 3. 進階量化觀念：波動率的波動率 (Vol of Vol) 具有常態性

對於質疑「歷史波動率閾值在未來是否會失效」的同學，講師分享了在業界（2015 年紐約資產配置工作坊中向 Andreas Steiner 學習並實證）的重要核心知識：

* **核心定理：**
波動率的波動率（Volatility of Volatility）在長期來看是非常穩定的。

雖然市場價格在變，但波動率的行為模式與結構（Volatility Patterns）在絕大多數資產類別中，隨著時間推移幾乎不會有太大改變。
因此，你大可充滿信心：今天在歷史數據（如 2004-2020 年）中所設定的合理波動率閾值，在未來 20 年（如 2020-2040 年）通常依然有效。（除非該資產類別的底層架構、組成或全球經濟發生根本性的結構轉變）。

<br>

## 4. 下一步：

目前為止，我們展示了波動率濾網帶來的驚人超額回報。在接下來的課程中，我們將學習如何客觀評估與分析回測結果。
雖然參數優化與防止過度擬合（Overfitting）的統計檢定屬於進階課程的範疇，但下一堂課講師會先介紹幾項量化交易員必備的關鍵統計指標，幫助你全面理解一個交易策略的真實行為與風險特徵。

<br><br>

# Lecture 5： 策略行為分析——月度重採樣與滾動年化報酬率實作

在本節中，我們正式對「加入波動率濾網後」的回測結果進行深度行為分析。為了消除日資料（Daily Data）過多的雜訊並平滑數據，我們將利用 Pandas 的重採樣機制（Resample）與 Lambda 幾何連結函數，將日報酬率轉換為月報酬率，並計算高階量化分析不可或缺的 **3年（36個月）滾動年化報酬率與統計表**。

<br>

## 1. 為什麼要分析「滾動 3 年期（Rolling 3-Year）」？
量化交易員不能只看「單一歷史區間」的總報酬率，因為：
1.  **墨菲定律（Murphy's Law）**：實務上，不論是你自己還是客戶，往往會在策略表現的「最高點（最糟糕的時機）」進場，隨後立即面臨虧損。
2.  **進場時機的公平性**：滾動 3 年分析能讓我們知道，**無論客戶在過去歷史的哪一個時間點開始執行此策略，他們在任意 3 年後的真實行為與報酬率表現會是如何**。
3.  *講師建議*：為了避免一口氣套牢在最高點，實務投資時建議採用**分批進場（例如分 4 個月、4 筆資金等額進場）**來平均成本，避免給客戶留下糟糕的第一印象。

<br>

## 2. 資料重採樣：日報酬率轉換為月報酬率
當我們處理**價格（Prices）**數據時，只需使用 `df.resample('ME').last()` 即可取每月最後一天價格；但我們目前處理的是**報酬率（Returns）**，必須透過**幾何連結（Geometrically Link / 複利複合成交）**的方式將每日報酬串聯起來。

### Python 程式碼實作

```python
# 1. 提取回測結果中的日策略報酬與日大盤報酬
strategy_returns = result_with_vol_filter['strategy_return']
benchmark_returns = result_with_vol_filter['spy_return'] # 即 SPY 的日報酬

# 2. 利用幾何連結 (1 + r1)*(1 + r2)... - 1 將日報酬重採樣至月報酬 ('M' 或 'ME')
monthly_strategy_returns = strategy_returns.resample('M').apply(
    lambda x: np.prod(x + 1) - 1
)

monthly_benchmark_returns = benchmark_returns.resample('M').apply(
    lambda x: np.prod(x + 1) - 1
)

# 3. 將兩者水平成份合併 (axis=1) 形成月報酬 DataFrame
df_monthly_returns = pd.concat(
    [monthly_strategy_returns, monthly_benchmark_returns], 
    axis=1
)
# 修改欄位名稱以便識別
df_monthly_returns.columns = ['strategy_return', 'spy_return']
```

## 3. 計算滾動年化報酬率函數
我們需要編寫一個動態函數，將上述得到的月報酬率 DataFrame 傳入，並計算出指定視窗（預設 36 個月）的滾動年化報酬率。

$$\text{Annualized Return} = (1 + \text{Compound Return})^{\frac{12}{\text{window}}} - 1$$

```python
def calculate_rolling_annualized_return(df_returns, window=36):
    """
    計算月度報酬率資料的滾動年化報酬率。
    注意：本函數專為『月資料』設計，公式中的 12 代表一年有 12 個月。
    """
    # 步驟 A：計算指定視窗內的幾何累積報酬率 (Compound Return)
    # raw=True 參數是為了加快 Pandas 的運算速度
    compound_return = (df_returns + 1).rolling(window=window).apply(
        lambda x: np.prod(x) - 1, 
        raw=True
    )
    
    # 步驟 B：將累積報酬率進行年化處理
    annualized_return = (compound_return + 1) ** (12 / window) - 1
    
    return annualized_return

# 執行函數：計算樣本內 36 個月 (3年) 的滾動年化報酬率
df_rr_in_sample = calculate_rolling_annualized_return(df_monthly_returns, window=36)
```

## 4. 滾動績效統計表分析 (Rolling Return Stats)

我們將滾動報酬率數據乘以 100（轉換為百分比模式）並四捨五入至小數點後兩位，代入先前的統計函數中，產出以下這張對交易員而言最重要的統計分析表：

```python
# 呼叫統計函數（注意：欄位名稱需與 DataFrame 對應，此處 benchmark_col 為 'spy_return'）
df_rr_stats_in_sample = rolling_return_stats(
    df_rr_in_sample * 100, 
    benchmark_col='spy_return'
).round(2)

print(df_rr_stats_in_sample)
```

## 5. 統計實證

根據回測產出的表格數據，我們可以看到加入波動率濾網後的巨大優勢：

* **勝率高達 61%：**
在所有歷史上任意的「滾動 3 年區間」中，我們的策略有 61% 的時間都擊敗了單純死抱大盤（SPY） 的表現。

* **最大報酬不落人後：**
策略的最佳 3 年年化報酬率非常接近大盤最狂熱時的表現。

* **下行防禦極度驚人（最核心的發現）：**
    * 單純買入並持有 SPY：在最慘的 3 年期間，平均每年要虧損 -15%。
    * 本課的量化交易策略：在歷史最慘烈的 3 年期間（經歷金融海嘯等），最糟糕的年化回報僅僅只有 -5%。

## 6. 結論

「波動率濾網」在下行風險防禦上的強大威力。它向我們證明：量化策略不一定要寫得極其複雜或使用瘋狂的數學模型，光是透過 SPY/RSP 這對簡單的資產結合一個設計優良的波動率停損機制，就能創造出極度穩健的超額 Alpha，將下行風險控制在非常舒服的範疇。

<br><br>

