# Lecture 1：量化輪動交易系統研發筆記

## 本堂核心觀念 (Key Insights)

### 1. 從「相對報酬」到「標準分數」的邏輯躍升
在探索性數據分析（EDA）的前期階段，我們將 SPY（市值加權）與 RSP（等權重）的滾動報酬率疊加在同一個圖表上。雖然這能讓我們看出兩者存在潛在的風格轉換週期，但因為兩者皆為獨立的絕對數值，我們很難在視覺或程式邏輯上精確衡量「橡皮筋到底被拉扯得有多開」。

為了解決這個痛點，並將觀察轉化為具備可操作性的交易訊號（Signal Generation），我們的量化解法分為兩步：

* **第一步：取價差 (Differential)** —— 用 SPY 的滾動報酬率減去 RSP 的滾動報酬率（$\text{SPY Return} - \text{RSP Return}$）。如此一來，繁雜的雙線圖就會濃縮為單一線條，直觀呈現兩者的相對強弱。
* **第二步：標準化 (Z-Score)** —— 絕對價差在不同的市場時期（如高波動的金融海嘯時期與低波動的常態牛市）其波動幅度截然不同，無法設定統一的絕對值門檻。透過將價差轉換為 **Z-Score（標準分數）**，我們便能以「偏離均值幾個標準差」的統計維度來統一衡量。當偏離程度超過特定標準差邊界時，即代表橡皮筋拉扯至極端，這就構成了策略執行輪動（Switch）的觸發核心。

<br>

## 量化模型的至高原則：消滅前瞻偏差 (Look-Ahead Bias)

在計算 Z-Score 時，如果直接對整個歷史資料集計算平均值（Mean）和標準差（Standard Deviation），就會犯下量化模型與機器學習中最致命的 cardinal sin（基要原罪）—— **前瞻偏差（Look-Ahead Bias）**。


* **錯誤示範（全局標準化）：** 在歷史時間軸上的 2010 年某個交易日，使用了包含 2011 到 2024 年的未來數據來計算當時的 Z-Score。在實際交易中，你不可能預知未來。
* **正確解法（擴展視窗 Expanding Window）：** 計算歷史上某一天 $t$ 的 Z-Score 時，**只能使用從歷史起點到當天 $t$ 的數據**。隨著時間往後推移，已知數據的資料庫會像滾雪球一樣越來越大（Expanding），但絕對不允許任何 $t+1$ 之後的未來資訊滲透進來。

> **核心紀律：** 訓練集（Train Set）與測試集（Test Set）必須嚴格獨立進行標準化。絕對不能先對整個數據集做標準化，隨後才進行樣本內外的切分。

<br>

## 關鍵 Pandas 函數語法語意

*   **`series.expanding().mean()` 與 `series.expanding().std()`：**
    Pandas 內建強大的動態擴展視窗方法。它與固定長度的 `rolling()` 不同，`expanding()` 的視窗起點固定，但終點會隨著資料列天天往後延伸，完美符合「僅使用歷史至今已知資料」的量化回測邏輯。
*   **`df.where(cond)`：**
    防禦性程式碼（Defensive Coding）的重要工具。用以確保只有在滿足特定條件（如原始數據非空值 `notna()`）時才保留計算結果，避免無效的 `NaN` 破壞圖表連續性或引發策略誤判。

<br>

## Python 實作：價差計算與 Expanding Z-Score 建構

請在您的 Jupyter Notebook 或 Google Colab 中建立新儲存格，複製並執行以下完整的研發程式碼：

```python
import pandas as pd
import numpy as np

# ==============================================================================
# Step 1: 計算不同週期下，兩資產滾動報酬率的相對價差 (Differential)
# ==============================================================================
# 以 SPY 減去 RSP，明確定義價差方向：正值代表 SPY 走強，負值代表 RSP 走強

df_prices['Rolling_1M_diff'] = df_prices['Spy_rolling_1M'] - df_prices['Rsp_rolling_1M']
df_prices['Rolling_6M_diff'] = df_prices['Spy_rolling_6M'] - df_prices['Rsp_rolling_6M']
df_prices['Rolling_1Y_diff'] = df_prices['Spy_rolling_1Y'] - df_prices['Rsp_rolling_1Y']


# ==============================================================================
# Step 2: 撰寫擴展視窗 Z-Score 函數 (完美規避前瞻偏差)
# ==============================================================================

def expanding_z_score(series):
    """
    計算擴展視窗的 Z-Score，確保動態回測時不引入未來數據。
    公式: (當前值 - 歷史至今平均值) / 歷史至今標準差
    """
    # 1. 計算動態擴展平均值 (Expanding Mean)
    expanding_mean = series.expanding().mean()
    
    # 2. 計算動態擴展標準差 (Expanding Standard Deviation)
    expanding_std = series.expanding().std()
    
    # 3. 計算並回傳 Z-Score
    z_score = (series - expanding_mean) / expanding_std
    return z_score


# ==============================================================================
# Step 3: 生成 Z-Score 特徵與缺失值 (NaN) 防禦處理
# ==============================================================================

# 3.1 應用函數，生成 1M、6M、1Y 三個週期的 Z-Score 欄位
df_prices['Rolling_1M_diff_z'] = expanding_z_score(df_prices['Rolling_1M_diff'])
df_prices['Rolling_6M_diff_z'] = expanding_z_score(df_prices['Rolling_6M_diff'])
df_prices['Rolling_1Y_diff_z'] = expanding_z_score(df_prices['Rolling_1Y_diff'])

# 3.2 防禦性資料清理：確保 Z-Score 只保留在原始價差有效的窗口內
# 由於期初需要累積足夠的交易日（如 1年期需 252 天），期初的 NaN 必須嚴格隔離，避免污染後續圖表與策略訊號
df_prices['Rolling_1M_diff_z'] = df_prices['Rolling_1M_diff_z'].where(df_prices['Rolling_1M_diff'].notna())
df_prices['Rolling_6M_diff_z'] = df_prices['Rolling_6M_diff_z'].where(df_prices['Rolling_6M_diff'].notna())
df_prices['Rolling_1Y_diff_z'] = df_prices['Rolling_1Y_diff_z'].where(df_prices['Rolling_1Y_diff'].notna())

# 3.3 檢視最終特徵矩陣的尾端數據
print("--- 擴展 Z-Score 特徵矩陣生成完畢 ---")
print(df_prices[['Rolling_1M_diff_z', 'Rolling_6M_diff_z', 'Rolling_1Y_diff_z']].tail())

```

<br>

### 策略建構前的量化腦力激盪 (Strategy Design Brainstorming)

到目前為止，我們已經成功消除了數據的量綱（Units），將混亂的絕對報酬，凝聚成了一條在 `0` 軸上下擺動、以標準差為單位的**無量綱標準訊號線**。這意味著我們已經拿到了開啟自動化交易系統的鑰匙。

在進入下一堂課的視覺化繪圖與回溯測試之前，我們必須深入探討以下兩個決定策略生死的核心量化權衡（Quant Trade-offs）：

<br>

#### 核心問題一：最佳窗口的權衡 (Optimal Lookback Window Optimization)

我們引入了 1個月（21日）、6個月（126日）與 12個月（252日）的滾動視窗，哪一個回看窗口最適合用來捕捉這條「橡皮筋的彈回（均值回歸）」？

短視窗與長視窗在實際交易中，各自面臨不同的系統性痛點：

| 滾動視窗長度 | 優點 (Pros) | 面臨的量化痛點 (Cons) | 成本與風險特徵 |
| :--- | :--- | :--- | :--- |
| **短視窗 (如 1M)** | 訊號極為靈敏，能第一時間捕捉到風格的微小轉換。 | **高頻雜訊過多**：容易將隨機波動誤判為風格背離，導致策略被反覆「巴來巴去」（Whipsaw）。 | **交易成本高昂**：頻繁換倉將大幅累積滑點（Slippage）與手續費，侵蝕 Alpha。 |
| **長視窗 (如 12M)** | 能夠過濾掉隨機雜訊，捕捉到真正屬於總體經濟體制（Regime Shift）變更的長線趨勢。 | **訊號嚴重滯後 (Lagging)**：當 Z-Score 終於觸發訊號時，市場行情可能早已走完大半，錯失最佳進場時機。 | **交易頻率極低**：換倉成本低，但可能面臨長時間無訊號可交易的資金機會成本。 |

*   **量化思維：** 策略研發的目標並非尋找「完美視窗」，而是尋找能平衡**「雜訊過濾」**與**「訊號滯後」**的黃金分割點（通常中線視窗如 6M 在實務上較具備橡皮筋的拉扯與回歸特性）。

<br>

#### 核心問題二：臨界值的設定 (Threshold Optimization)
我們應該將 Z-Score 的進場邊界（Trading Bands）設定在偏離均值的幾個標準差？是 $\pm 1.0\sigma$、$\pm 1.5\sigma$ 還是 $\pm 2.0\sigma$？

這本質上是一場關於**「勝率 (Win Rate)」**與**「交易次數 (Trade Frequency)」**的經典拉鋸戰（Tug of War）：

<br>

*   **低臨界值 (如 $\pm 1.0\sigma$)：**
    *   *特徵：* 只要橡皮筋稍微拉開就會觸發交易。
    *   *結果：* **交易機會次數高 (High Frequency)**，但因為市場尚未進入真正的「極端發散」狀態，**單次勝率通常較低**，容易死在動能持續發散的階段。
*   **高臨界值 (如 $\pm 2.0\sigma$)：**
    *   *特徵：* 只有當市場發生極端風格扭曲（如歷史級別的系統性危機或極端權值股暴拉）時才會觸發。
    *   *結果：* 根據統計學高斯分布，觸及此邊界的機率極低，因此**交易機會稀少 (Low Frequency)**；然而，一旦觸發，代表市場處於極度不合理的定價扭曲中，此時進場的**均值回歸勝率與獲利空間通常極高**。

<br>

> **量化拉鋸核心 (The Quant Dilemma)：**
> $$\text{High Threshold } (\pm 2.0\sigma) \longrightarrow \text{High Win Rate } \uparrow \ + \ \text{Low Low Trade Frequency } \downarrow$$
> $$\text{Low Threshold } (\pm 1.0\sigma) \longrightarrow \text{Low Win Rate } \downarrow \ + \ \text{High Trade Frequency } \uparrow$$
> 
> 在實務回測中，我們必須透過**夏普比率 (Sharpe Ratio)** 與**最大回撤 (Maximum Drawdown)** 來尋找最適合該資產特性的臨界值平衡點。

<br><br>

# Lecture 2：補充 Z-Score 核心理論

## 什麼是 Z-Score（標準分數）？

**Z-Score（標準分數）**在統計學與量化交易中，是一個用來衡量**「當前數據點，距離歷史平均值偏離了幾個標準差」**的無量綱（無單位）指標。

簡單來說，Z-Score 就像是市場的「體溫計」。它不關心絕對數值是幾元或百分之幾，它只告訴量化交易員：**「當前的市場異動，在歷史常態中到底有多罕見？」**

<br>

## 1. 數學公式與統計學含意

Z-Score 的基本統計學公式如下：

$$Z = \frac{X - \mu}{\sigma}$$

*   **$X$ (Observation)：** 當前觀測到的數值（例如：今天的 $\text{SPY 報酬率} - \text{RSP 報酬率}$ 價差）。
*   **$\mu$ (Mu / Mean)：** 歷史的**平均值**，代表橡皮筋沒被拉開時的「常態中心點」。
*   **$\sigma$ (Sigma / Standard Deviation)：** 歷史的**標準差**，代表數據常態波動的「劇烈程度（或肥厚度）」。

### 高斯常態分布（Bell Curve）下的機率對應
當我們假設市場數據分布接近常態分布時，Z-Score 的數值具有明確的機率統計含意：

*   **$Z = 0$：** 代表當前數值**完美等於**歷史平均值。
*   **$Z = \pm 1.0\sigma$：** 涵蓋了歷史上約 **68.2%** 的時間，屬於市場的正常波動區間。
*   **$Z = \pm 2.0\sigma$：** 涵蓋了歷史上約 **95.4%** 的時間。一旦突破此區間（即 $|Z| > 2$），代表市場進入了**僅有 4.6% 發生機率的極端扭曲狀態**。
*   **$Z = \pm 3.0\sigma$：** 歷史涵蓋率達 **99.7%**。突破此邊界通常意味著遭遇了極其罕見的「黑天鵝事件」。

---

## 2. 為什麼量化交易必須引入 Z-Score？（解決時空波動痛點）

在實際研發回測系統時，如果不將數據「無量綱化（Standardization）」，只看絕對價差，將會面臨嚴重的**時空定價非對稱災難**。

### 傳統絕對價差的痛點：
假設我們觀察 $\text{SPY} - \text{RSP}$ 的滾動報酬率價差：
*   **2008 年金融海嘯時期：** 市場波動極度劇烈，兩者價差可能在幾天內拉開 **5%**。
*   **2017 年極低波動牛市：** 市場極度平靜，兩者價差只要拉開 **0.5%** 就已經是年度級別的極端事件。

如果你在程式中寫死硬編碼（Hard-coding）：`if price_diff > 0.02: trigger_trade()`
*   **後果：** 2008 年你的系統會因為波動被動放大而**瘋狂換倉（頻繁觸發偽訊號）**；而 2017 年你的系統會**完全死掉（一整年都捕捉不到訊號）**。

###  Z-Score 的量化解法：
透過將價差除以動態擴展標準差（Expanding Standard Deviation），數值被完美標準化：
*   2008 年的 5% 價差 $\div$ 當時極大的標準差 $\longrightarrow Z = +2.1$
*   2017 年的 0.5% 價差 $\div$ 當時極小的標準差 $\longrightarrow Z = +2.3$

經過 Z-Score 轉換後，這兩個不同時空背景的數字，在統計學上便具備了**同等權重的「極端重要性」**。量化系統這時就能使用統一的數學濾網（如 $|Z| > 2.0$）來跨越時間週期，捕捉真正的定價不合理機會。

---

## 3. 交易員如何利用 Z-Score 賺錢？（均值回歸策略應用）

在我們的 SPY/RSP 輪動系統中，Z-Score 是捕捉**「動能發散至極限後，橡皮筋彈回」**的核心驅動器：

*   **當 $Z \gg +2.0$（正向極端發散）：**
    *   *市場含意：* 市值加權的 SPY（大型權值股）強得不合理，等權重的 RSP（中小型股）被嚴重低估，橡皮筋向右拉扯至極限。
    *   *策略動作：* 預期 Z-Score 未來將向 `0` 軸回歸，執行 **「賣出 SPY，換倉/輪動至 RSP」**。
*   **當 $Z \ll -2.0$（負向極端發散）：**
    *   *市場含意：* 中小型股（RSP）異常狂飆，大盤權值股（SPY）被過度拋售，橡皮筋向左拉扯至極限。
    *   *策略動作：* 預期市場過熱情緒收斂，執行 **「賣出 RSP，換倉/輪動回 SPY」**。

> **核心結論：** 
> Z-Score 的本質就是將混亂的價格波動，收斂為一條具有統計學邊界的「訊號線」。交易員的獲利來源（Alpha），正是源於市場從「發燒（極端 Z-Score）」回歸到「正常體溫（0 軸）」的必然統計規律。


<br><br>

# Lecture 3：從數據探索到 Z-Score 訊號建構 

## 階段一：核心量化理論與策略動機

本策略的核心目標是建構一個在 **SPY（S&P 500 市值加權）** 與 **RSP（S&P 500 等權重）** 之間進行動態輪動（Rotation）的量化交易系統。

透過前期探索性數據分析（EDA），我們確認了兩者之間的市場主導權（Regime / Leadership）會隨著經濟體制轉換而交替更迭。為了捕捉此現象並生成可交易的訊號，系統引入了**橡皮筋理論（動能與均值回歸的拉鋸戰）**：

*   **動能 (Momentum)：** 當某個風格（如大型股）開始走強，橡皮筋被拉開，變動率（Rate of Change）隨之加速。
*   **均值回歸 (Mean Reversion)：** 當兩者的相對表現發散（Diverge）到歷史統計的極端水平時，橡皮筋最終會彈回，向歷史均值靠攏。

為了精確量化橡皮筋被拉扯的程度，我們必須將價格數據進行**「取價差（Differential）」**與**「無量綱化（Z-Score Standardization）」**。

<br>

## 階段二：統計學核心——擴展標準分數 (Expanding Z-Score)

如果僅觀察兩資產的絕對滾動報酬率，我們無法跨越不同的歷史時空（如 2008 金融海嘯的高波動期與 2017 的極低波動期）來設定統一的交易門檻。因此，系統必須引入 **Z-Score（標準分數）**。

### 1. Z-Score 數學公式
Z-Score 的本質是以**標準差（$\sigma$）**為單位，衡量當前觀測值偏離歷史均值的程度：

$$Z = \frac{X - \mu}{\sigma}$$

*   $X$：當前觀測到的報酬率價差（$\text{SPY 滾動報酬} - \text{RSP 滾動報酬}$）。
*   $\mu$ (Mu)：歷史擴展平均值（Expanding Mean），代表常態中心點。
*   $\sigma$ (Sigma)：歷史擴展標準差（Expanding Standard Deviation），代表歷史波動的厚度。

### 2. 量化最高防線：消滅前瞻偏差 (Look-Ahead Bias)
在計算 Z-Score 時，**絕對不可使用全局數據（Global Standardization）**。如果在計算歷史上 $t$ 日的 $\mu$ 與 $\sigma$ 時引入了 $t+1$ 日之後的未來資訊，將會觸犯量化模型的至高原罪——前瞻偏差。

*   **量化解法：擴展視窗（Expanding Window）**
    系統利用從歷史起點到當前計算日 $t$ 的已知數據計算動態平均與標準差。隨著時間推移，已知資料庫會像滾雪球一樣越來越大（Expanding），但絕不滲透未來資訊，從而保證回測的真實性。

<br>

## 階段三：Python 系統特徵工程實作

以下為完整的特徵工程代碼。包含建構多週期滾動報酬、計算價差、撰寫完美的防前瞻偏差 Expanding Z-Score 函數，以及防禦性的缺失值（NaN）防禦處理。

```python
import numpy as np
import pandas as pd

# ==============================================================================
# Step 1: 建構多週期滾動報酬率 (1個月、6個月、1年期)
# ==============================================================================
# 自訂函數 rolling_returns(series, period, annualized=False) 假設已於前文定義
# 美股一年約 252 個交易日，半年為 126 天，一個月為 21 天。

df_prices['Spy_rolling_1M'] = rolling_returns(df_prices['SPY'], period=21, annualized=False)
df_prices['Spy_rolling_6M'] = rolling_returns(df_prices['SPY'], period=126, annualized=False)
df_prices['Spy_rolling_1Y'] = rolling_returns(df_prices['SPY'], period=252, annualized=False)

df_prices['Rsp_rolling_1M'] = rolling_returns(df_prices['RSP'], period=21, annualized=False)
df_prices['Rsp_rolling_6M'] = rolling_returns(df_prices['RSP'], period=126, annualized=False)
df_prices['Rsp_rolling_1Y'] = rolling_returns(df_prices['RSP'], period=252, annualized=False)

# ==============================================================================
# Step 2: 計算資產相對價差特責 (Differential)
# ==============================================================================
# 價差方向明確定義：SPY - RSP。正值代表 SPY 走強，負值代表 RSP 走強。

df_prices['Rolling_1M_diff'] = df_prices['Spy_rolling_1M'] - df_prices['Rsp_rolling_1M']
df_prices['Rolling_6M_diff'] = df_prices['Spy_rolling_6M'] - df_prices['Rsp_rolling_6M']
df_prices['Rolling_1Y_diff'] = df_prices['Spy_rolling_1Y'] - df_prices['Rsp_rolling_1Y']

# ==============================================================================
# Step 3: 撰寫 Expanding Z-Score 函數 (動態擴展視窗，規避前瞻偏差)
# ==============================================================================

def expanding_z_score(series):
    """
    基於動態歷史擴展視窗計算 Z-Score。
    每往下一列，自動將最新一筆觀測值納入歷史資料庫計算 mean 與 std。
    """
    expanding_mean = series.expanding().mean()
    expanding_std = series.expanding().std()
    z_score = (series - expanding_mean) / expanding_std
    return z_score

# ==============================================================================
# Step 4: 特徵生成與防禦性資料清理 (Defensive Data Cleaning)
# ==============================================================================

# 4.1 套用函數生成 Z-Score 訊號線
df_prices['Rolling_1M_diff_z'] = expanding_z_score(df_prices['Rolling_1M_diff'])
df_prices['Rolling_6M_diff_z'] = expanding_z_score(df_prices['Rolling_6M_diff'])
df_prices['Rolling_1Y_diff_z'] = expanding_z_score(df_prices['Rolling_1Y_diff'])

# 4.2 防禦性資料對齊：確保 Z-Score 只在原始價差非 NaN 的有效視窗內保留
# 隔離期初因累積交易日不足所產生的 NaN，避免破壞圖表連續性或觸發偽交易訊號
df_prices['Rolling_1M_diff_z'] = df_prices['Rolling_1M_diff_z'].where(df_prices['Rolling_1M_diff'].notna())
df_prices['Rolling_6M_diff_z'] = df_prices['Rolling_6M_diff_z'].where(df_prices['Rolling_6M_diff'].notna())
df_prices['Rolling_1Y_diff_z'] = df_prices['Rolling_1Y_diff_z'].where(df_prices['Rolling_1Y_diff'].notna())

# ==============================================================================
# Step 5: 樣本內數據切分 (In-Sample Split for Visual Analysis)
# ==============================================================================
df_in_sample_prices = df_prices.loc[:out_of_sample_date]

```

<br>

## 階段四：進階視覺化與網格圖表實作

   利用 Matplotlib Subplots 建構一個 3 橫列、1 直欄（3 Rows, 1 Column） 的畫布網格，將不同時間窗口的 Z-Score 訊號重疊對齊，並在各子圖中繪製一條 $Z=0$ 的紅色虛線原點基準軸。

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 初始化 3x1 子圖網格
fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 18))

# --- Plot 1: 1個月視窗 Z-Score (短線高頻) ---
sns.lineplot(data=df_in_sample_prices, x=df_in_sample_prices.index, y='Rolling_1M_diff_z', ax=axes[0], label='1M Diff Z-Score')
axes[0].set_title('1-Month Rolling Return Differences Z-Scores')
axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.3)

# --- Plot 2: 6個月視窗 Z-Score (中線週期) ---
sns.lineplot(data=df_in_sample_prices, x=df_in_sample_prices.index, y='Rolling_6M_diff_z', ax=axes[1], label='6M Diff Z-Score')
axes[1].set_title('6-Month Rolling Return Differences Z-Scores')
axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.3)

# --- Plot 3: 1年期視窗 Z-Score (長線趨勢) ---
sns.lineplot(data=df_in_sample_prices, x=df_in_sample_prices.index, y='Rolling_1Y_diff_z', ax=axes[2], label='1Y Diff Z-Score')
axes[2].set_title('1-Year Rolling Return Differences Z-Scores')
axes[2].axhline(y=0, color='red', linestyle='--', alpha=0.3)

# --- 統一多圖格式優化 ---
for ax in axes:
    ax.set_ylabel('Z-Score (Standard Deviations)')
    ax.set_xlabel('Date')
    ax.legend(frameon=False)

plt.tight_layout()
plt.show()

```

<br>

## 階段五：圖表特徵解讀與量化交易藍圖擬定

透過視覺化圖表分析（Visual Inspection），我們可為策略提煉出決定性的統計特徵：

**1. 1個月視窗（1M Z-Score）的統計優勢：**

雖然 1M 訊號屬於高頻率數據且雜訊較多，但其展現出了極其強烈的帶狀區間受限（Constrained Band）與均值回歸行為。圖表顯示，數據在上下觸及 $\pm 2.0\sigma$ 後，幾乎必然向 $0$ 軸強烈彈回。這為頻繁輪動的策略提供了絕佳的溫床。

**2. 6個月與 1年期視窗的特徵：**

隨著時間視窗拉長，訊號週期變長。1年期（1Y）圖表呈現明顯的右偏特徵（長期牛市 Beta 溢價導致多數時間報酬為正），但由於訊號存在嚴重滯後（Lagging），在捕捉橡皮筋快速彈回時顯得不夠敏銳。

<br>

### 初始自動化策略規則藍圖（Trading Rules）

基於 1M Z-Score 圖表的直覺規律，我們將交易進場門檻（Thresholds）設定在 $\pm 2.0\sigma$：

# 策略核心模組：1M Z-Score 交易規則藍圖

本策略屬於 **100% 全額滿倉（Fully Invested）** 的雙向輪動系統。系統不持有現金，純粹依據 **1M Z-Score 訊號線** 偏離常態分佈的程度，在 **SPY（市值加權）** 與 **RSP（等權重）** 之間進行二元切換（Binary Switching）。


```diff
[ 1M Z-Score 訊號線 ]
   
   +2.0σ  -------------------------------------------------- 橡皮筋拉扯極限 (SPY過強)
          ▲ 觸發規則 A：賣出 SPY，全額輪動換倉至 RSP
          
    0.0軸 -------------------------------------------------- 歷史平衡常態中心點
          
          ▼ 觸發規則 B：賣出 RSP，全額輪動換倉回 SPY
   -2.0σ  -------------------------------------------------- 橡皮筋拉扯極限 (RSP過強)

```

### 權衡一：回看視窗的選擇（Optimal Lookback Window）
我們應該選擇 **1個月（1M）**、**6個月（6M）** 還是 **1年期（1Y）** 的滾動報酬差來作為 Z-Score 的輸入特徵？

*   **選擇短視窗（如 1M 訊號）：**
    *   *優點：* 系統具備極高的**靈敏度（Sensitivity）**，能在一種風格（Regime）剛開始衰退時，第一時間捕捉到微小的拐點並切換頭寸。
    *   *缺點：* 隱含嚴重的**微觀噪音（Microstructure Noise）**。容易在市場震盪期產生偽訊號，導致策略在短時間內频繁發出反向換倉指令（俗稱：被反覆巴來巴去，Whipsaw），從而累積巨大的**滑點（Slippage）與交易手續費**，吞噬潛在 Alpha。
*   **選擇長視窗（如 12M 訊號）：**
    *   *優點：* 數據經過一整年的平滑，**統計穩定性極佳**，能夠完美過濾隨機波動，每一次換倉都代表市場大趨勢的真正逆轉。
    *   *缺點：* 存在嚴重的**時間滯後性（Lagging Effect）**。當 12M 訊號終於觸及 $\pm 2.0\sigma$ 時，均值回歸的行情可能早已走完大半，策略往往會「追高殺低」在非最優節點上。

### 權衡二：交易臨界值的設定（Threshold Optimization）
將臨界值設定在 $\pm 2.0\sigma$ 是最佳選擇嗎？這是**單次交易勝率（Win Rate）**與**資產周轉率（Trade Frequency）**的經典博弈：

*   **極端寬門檻（如 $\pm 2.0\sigma$ 或 $\pm 2.5\sigma$）：**
    *   根據高斯分佈，數據落在 $\pm 2.0\sigma$ 之外的機率僅約 $4.55\%$。這意味著系統在等待**統計學上的極端尾部事件（Tail Events）**。
    *   *結果：* 橡皮筋被拉到極限，一旦出手，**單次交易的勝率極高**。但缺點是**交易機會極其稀少**，策略可能長達數年沒有任何動作，導致隱含資金時間成本。
*   **縮窄門檻（如 $\pm 1.0\sigma$ 或 $\pm 1.5\sigma$）：**
    *   數據落在 $\pm 1.0\sigma$ 之外的機率高達 $31.73\%$。
    *   *結果：* 交易頻次大幅提升，資金周轉率高。但因為信號並未達到真正的歷史極端值，均值回歸的動能不足，**單次勝率會顯著下降**，策略極易在常態波動中被雜訊洗出場。

<br>

## 下階段回測實作觀測指標（Backtest KPIs）

在自動化回測系統中，我們將透過以下三大指標來對上述權衡進行微調（Tuning），尋找回測的「甜蜜點（Sweet Spot）」：

1.  **夏普比率（Sharpe Ratio）：** 

    檢驗提高交易頻次所帶來的超額報酬，是否能覆蓋波動風險。

2.  **最大回撤（Maximum Drawdown, MDD）：** 

    觀察在風格極端延續（如 2020 年科技股極端牛市下，橡皮筋長期不回彈）時，策略所面臨的痛苦期有多長。

3.  **換手率與成本扣除（Turnover & Friction Cost）：** 

    將手續費與滑點加入扣除，評估 1M 高頻訊號的利潤是否會被券商完全吞噬。