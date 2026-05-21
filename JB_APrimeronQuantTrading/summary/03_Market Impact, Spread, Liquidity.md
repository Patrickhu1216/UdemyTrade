# 量化交易筆記：Section 3 市場衝擊測量與無反饋做市商模型 (Lecture 3)

## 📌 章節導論與核心目標
本課從**實盤數據**出發，重點探討並測量交易的**市場衝擊（Market Impact）**。

本課建立了一個簡單的做市商模型。在該模型中，做市商的交易**不對市場中間價產生反饋（Feedback）**。儘管這個簡化模型存在局限性，但它成功以理論解釋了實盤中觀察到的核心規律：**買賣價差（Spread）與漸進市場衝擊（Asymptotic Market Impact）之間的定量關係**。

---

## 1. 符號與量化指標定義

在整個 Section 3 中，我們將統一使用以下量化符號與定義：

*   **$\epsilon_t$（交易方向符號 / Sign of the Trade）**：從做市商的交易對手（即**流動性提取者 / Liquidity Taker**）的角度定義：
    *   $\epsilon_t = +1$：主動買單（Buy）
    *   $\epsilon_t = -1$：主動賣單（Sell）
    *   *註：在 Section 3 前期，我們主要聚焦於小額交易，暫不考慮交易量（Trade Size）的非線性結構。*
*   **$S_t$（公平中間價 / Fair Mid Price）**。
*   **$I(\tau)$（市場衝擊函數 / Market Impact Function）**：觀測時間地平線（Horizon）為 $\tau$ 的市場衝擊。定義為未來回報與交易方向相乘的**經驗期望值（時間平均值）**：
    $$I(\tau) = \mathbb{E}\left[ (S_{t+\tau} - S_t) \cdot \epsilon_t \right]$$
    由於主動買單（$\epsilon_t = +1$）預期會推升價格，主動賣單（$\epsilon_t = -1$）預期會壓低價格，因此該乘積的期望值 $I(\tau)$ 應為一個**正值函數**。
*   **$I_{\infty}$（漸進市場衝擊 / Asymptotic Market Impact）**：當觀測時間 $\tau$ 趨於無窮大（實務上指足夠長的時間地平線）時的極限值：
    $$I_{\infty} = \lim_{\tau \to \infty} I(\tau)$$

---

## 2. 實盤數據觀測與經驗規律（以 Intel 股票為例）

透過分析 Intel Corporation（INTC）單日的高頻 Tick 數據（包含最佳買賣價 Best Bid/Offer 與逐筆成交數據 Times and Sales），我們發現了以下兩個關鍵的經驗法則（Empirical Observations）：

### 🔍 規律一：市場衝擊與平均價差的幾何關係（核心聚焦）
*   數據顯示，小額交易的**漸進市場衝擊 $I_{\infty}$ 大約為 $0.6$ 美分**。
*   當日該股票的平均報價總價差（Mean Spread）略高於 $1$ 美分（多數時候在 $1$ 美分與 $2$ 美分之間跳動）。
*   **核心經驗結論**：小額交易的漸進市場衝擊，幾乎精確地等於平均**半價差（Half-Spread）**：
    $$I_{\infty} \approx \frac{1}{2} \times \text{Mean Spread}$$

### 🔍 規律二：交易方向的強自相關性
*   流動性提取者的交易方向 $\epsilon_t$ 展現出非常高的正自相關性。
*   **自相關函數（Autocorrelation Function）**隨著交易延遲（Lags）$\tau$ 的增加，表現出清晰的**指數衰減（Exponential Decay）**趨勢，高度符合以下大數法則：
    $$\text{Autocorrelation}(\tau) \sim \rho^{\tau} \quad (\text{其中 } 0 < \rho < 1)$$

---

## 3. 無反饋做市商模型的理論推導

為了從理論上解釋為什麼 $I_{\infty} \approx \frac{1}{2} \times \text{Spread}$，我們構建了一個理想化的做市商動態系統。

### 📐 狀態變數與動態方程
假設交易在**交易時間（Trade Time）**框架下運行（每次時鐘滴答代表一筆交易，每筆交易量常態化為 1）：
1. **庫存變動**：由於 $\epsilon_t$ 是對手盤的方向，對手買入則做市商現貨庫存 $Q_t$ 減少，反之亦然：
   $$dQ_t = -\epsilon_t$$
2. **現金變戶變動**：結合買賣兩側，做市商的現金流可統一表示為：
   $$dX_t = (S_t + \epsilon_t \delta_t) \cdot \epsilon_t = S_t \epsilon_t + \delta_t \epsilon_t^2$$
   其中 $\delta_t$ 為做市商在 $t$ 時刻掛出的**半價差（Quoted Half-Spread）**。因為 $\epsilon_t^2 \equiv 1$，上式可簡化為：
   $$dX_t = S_t \epsilon_t + \delta_t$$

### 📐 損益（P&L）公式解構
做市商從開盤到結算終端 $T$ 的累積損益為現金帳戶加上庫存的期末市值計價（Mark-to-Market）：
$$\text{P\&L}_T = X_T + Q_T S_T$$

在離散交易時間下，將動態方程展開並進行全面加總（Summation）：
*   現金帳戶累計：$X_T = \sum_{t=1}^T S_t \epsilon_t + \sum_{t=1}^T \delta_t$
*   期末庫存累計：$Q_T = -\sum_{t=1}^T \epsilon_t \implies Q_T S_T = -\sum_{t=1}^T S_T \epsilon_t$

將兩者相加，並計算**單位時間的平均損益（P&L per unit of time）**：
$$\frac{\text{P\&L}_T}{T} = \frac{1}{T} \sum_{t=1}^T \delta_t - \frac{1}{T} \sum_{t=1}^T (S_T - S_t) \epsilon_t$$

當交易筆數 $T$ 足夠大時，時間平均值將收斂至其統計期望值。此時：
1.  第一項 $\frac{1}{T} \sum \delta_t$ 收斂至**預期半價差（Expected Half-Spread）** $\mathbb{E}[\delta]$。
2.  第二項 $\frac{1}{T} \sum (S_T - S_t) \epsilon_t$ 根據定義，正是地平線足夠長時的**漸進市場衝擊（Asymptotic Market Impact）** $I_{\infty}$。

因此，做市商的預期單位損益方程為：
$$\mathbb{E}[\text{P\&L per unit of time}] = \mathbb{E}[\delta] - I_{\infty}$$

---

## 4. 經濟學含義與結論

$$\mathbb{E}[\text{P\&L}] = 0 \implies I_{\infty} = \mathbb{E}[\delta]$$

*   **完全競爭與市場效率（Perfect Competition）**：在一個沒有印花稅/手續費、且具備完全競爭的理想高效市場中，做市商之間的極致競爭會將超額利潤擠壓至零。
*   **均衡狀態（Equilibrium）**：當做市商的預期長線損益為 0 時，上式直接導出 **$I_{\infty} = \mathbb{E}[\delta]$**。
*   **理論驗證**：這完美地解釋了實盤數據中「漸進市場衝擊等於平均半價差（即總價差的一半）」的現象。做市商賺取的半價差收益，在統計上剛好用來抵消對手盤帶來的長線市場逆向衝擊成本。

---

## 🚀 後續課程預告
*   **Lecture 4 (Lesson 6)**：我們將升級此模型，引入**對市場中間價（Mid Price）具備反饋機制（Feedback）**的更完整做市商模型。
*   **Lesson 8**：我們將跳出小額交易的線性框架，邁向能夠容納**一般非線性衝擊（General Nonlinear Impact）**的全局市場衝擊模型。

<br><br>

# 量化交易筆記：Section 3 具備價格反饋的自我完備做市商模型 (Lecture 4)

## 📌 章節導論與核心目標
在上一課（Lecture 3）中建立的「無反饋做市商模型」存在一個根本性的邏輯缺陷：雖然它在結果上成功解釋了為什麼漸進市場衝擊（Asymptotic Market Impact）會等於做市商半價差的期望值，但它假設市場中間價 $S_t$ 完全由純隨機的布朗運動驅動。這意味著流動性提取者的主動交易對中間價**沒有任何物理反饋**，這在微觀結構邏輯上顯然是不自洽的。

本課旨在發展一個**「自我完備（Self-Consistent）的動態反饋模型」**。該模型不僅將交易對中間價的反饋內生化，還完美融入了我們在實盤數據中觀測到的**交易方向強自相關性（指數衰減現象）**，在邏輯自洽的前提下重新論證價差與市場衝擊的均衡關係。

---

## 1. 核心模型假設

為了設計這個自我完備的系統，我們基於離散交易時間框架（Discrete Trade Time）提出以下兩個關鍵假設：

### 💡 假設一：交易方向的馬可夫指數衰減
實盤數據顯示交易方向符號 $\epsilon_t \in \{-1, +1\}$ 具備強烈的正自相關性。我們假設其滿足**一階馬可夫過程（Markov Process）**，使得過去的交易方向對未來的影響隨時間呈指數衰減（Exponential Decay）：
$$\mathbb{E}[\epsilon_{t+\tau} \cdot \epsilon_t] = \rho^\tau \quad (\text{其中 } 0 < \rho < 1)$$
這意味著給定當前交易方向，下一筆交易方向的條件期望值為：
$$\mathbb{E}[\epsilon_{t+1} \mid \epsilon_t] = \rho \epsilon_t$$

### 💡 假設二：內生市場衝擊的中間價動態
市場中間價的增量 $dS_t = S_{t+1} - S_t$ 不再僅僅是外生的布朗運動，而是必須實時受到**主動交易方向的衝擊**。我們將其建模為：
$$dS_t = f(\rho, I_{\infty}) \epsilon_t + \sigma dW_t$$
其中 $f(\rho, I_{\infty})$ 是一個待定函數，由系統的自我完備性（Self-Consistency）唯一決定。

---

## 2. 確定唯一的完備反饋函數 $f$

為了求出函數 $f$ 的確切數學形式，我們對遠期回報（Forward Return）進行分解，並計算市場衝擊函數 $I(\tau)$：

由於長線遠期回報可以拆解為單步回報的加總：$S_T - S_t = \sum_{\tau=t}^{T-1} dS_{\tau}$，將其與 $t$ 時刻的交易方向 $\epsilon_t$ 相乘並取期望值：
$$\mathbb{E}[(S_T - S_t) \epsilon_t] = \mathbb{E}\left[ \sum_{\tau=t}^{T-1} \left( f(\rho, I_{\infty}) \epsilon_{\tau} + \sigma dW_{\tau} \right) \epsilon_t \right]$$

根據隨機過程性質：
1. 外生隨機噪聲（布朗運動增量）$dW_{\tau}$ 與過去的交易方向 $\epsilon_t$ 獨立，因此期望值 $\mathbb{E}[dW_{\tau} \epsilon_t] = 0$，噪聲項消失。
2. 根據假設一，交易方向自相關項為 $\mathbb{E}[\epsilon_{\tau} \epsilon_t] = \rho^{\tau-t}$。

當我們令觀測地平線趨於無窮大（$T \to \infty$）時，等式左邊依定義收斂至**漸進市場衝擊 $I_{\infty}$**。等式右邊則轉化為無窮等比級數求和：
$$I_{\infty} = f(\rho, I_{\infty}) \sum_{\tau=t}^{\infty} \rho^{\tau-t} = f(\rho, I_{\infty}) \cdot \left( 1 + \rho + \rho^2 + \rho^3 + \dots \right) = f(\rho, I_{\infty}) \cdot \frac{1}{1 - \rho}$$

為了保持系統的邏輯自洽，**反饋函數 $f$ 有且僅有唯一的一種數學選擇**：
$$f(\rho, I_{\infty}) = I_{\infty}(1 - \rho)$$

> ### 🎯 自我完備模型的中間價動態方程
> $$S_{t+1} - S_t = I_{\infty}(1 - \rho) \epsilon_t + \sigma dW_t$$

---

## 3. 現實做市商行為建模：引入離散 O-U 庫存過程

為了讓做市商的模型更貼近現實，我們引入在 Section 2 中學到的 **Avellaneda-Stoichkov (AS) 模型** 的動態報價規律。做市商根據自身庫存線性調整買賣兩側的半價差：
$$\delta_t^b = \delta_0 + \kappa Q_t, \quad \delta_t^a = \delta_0 - \kappa Q_t \implies \delta_t^b - \delta_t^a = 2\kappa Q_t$$

做市商的庫存變動由兩側的卜瓦松過程驅動：$dQ_t = dN_t^b - dN_t^a$。我們可以將其拆解為**期望漂移項（強度差）**與**補償卜瓦松增量（實質上由對手盤交易方向 $\epsilon_t$ 刻畫）**：
$$dQ_t = (\lambda_b - \lambda_a)dt - \epsilon_t$$

利用 AS 模型中強度與價差的指數關係 $\lambda = A e^{-k \delta}$，並在價差較小時進行一階泰勒展開（$e^{-x} \approx 1-x$），買賣兩側強度差可近似為：
$$\lambda_b - \lambda_a \approx -Ak(\delta_t^b - \delta_t^a) = -2Ak\kappa Q_t$$

將其代入離散交易時間增量方程（令 $dt=1$）：
$$Q_{t+1} - Q_t = -2Ak\kappa Q_t - \epsilon_t \implies Q_{t+1} = (1 - 2Ak\kappa) Q_t - \epsilon_t$$

令常數 $\lambda_{\text{OU}} = 1 - 2Ak\kappa$，並合理假設做市商控制參數使得 $\lambda_{\text{OU}} \in (0, 1)$。這構成了一個標準的**離散奧恩斯坦-烏倫貝克（Ornstein-Uhlenbeck）過程**。透過對歷史遞迴展開，做市商的當前庫存可完美表達為歷史交易方向的**指數加權移動平均**：
$$Q_t = -\sum_{\tau=0}^{\infty} \lambda_{\text{OU}}^{\tau} \epsilon_{t-1-\tau}$$

---

## 4. 終端損益（P&L）的一致性推導

做市商期末的總損益恆等於現金帳戶加上庫存的期末市值計價：$\text{P\&L}_T = X_T + Q_T S_T$。利用**離散分部積分法（Discrete Integration by Parts）**，我們可以消去與邊界相關的有限常數項（當 $T \to \infty$ 時變為 $O(1)$），將累積損益改寫為：
$$\text{P\&L}_T = \sum_{t=1}^T (S_T - S_t - \epsilon_t \delta_t)(Q_{t+1} - Q_t)$$

將前述推導出的 $Q_t$ 指數加權求和式代入，並使用**離散富比尼定理（Discrete Fubini's Theorem）**交換求和順序，對兩邊取單位時間平均損益的期望值：
$$\mathbb{E}\left[\frac{\text{P\&L}_T}{T}\right] = -\sum_{\tau=0}^{\infty} \lambda_{\text{OU}}^{\tau} \cdot \mathbb{E}\Big[ (S_t - S_{t-1})\epsilon_{t-1-\tau} - \delta_{t-1}\epsilon_{t-1-\tau}\epsilon_{t-1} + \delta_t \epsilon_{t-1-\tau}\epsilon_t \Big]$$

### 📐 代入自我完備增量與自相關性
1. 由本課推導出的完備中間價方程知：$\mathbb{E}[(S_t - S_{t-1})\epsilon_{t-1-\tau}] = I_{\infty}(1-\rho)\rho^{\tau}$。
2. 根據交易符號的馬可夫自相關性，後續的價差交叉項會共同提取出 $\rho^{\tau}(1-\rho)$ 的因子。

經過代數整理與因式分解，我們得到極其優雅的**最終預期損益通式**：
$$\mathbb{E}\left[\frac{\text{P\&L}_T}{T}\right] = \left( \sum_{\tau=0}^{\infty} \lambda_{\text{OU}}^{\tau} \rho^{\tau} (1-\rho) \right) \cdot \Big( \mathbb{E}[\delta_t] - I_{\infty} \Big)$$

---

## 5. 結論：微觀結構的自我完備性

根據與前一課相同的經濟學邏輯，在一個不存在交易手續費且具備完全竞争的做市商市場中，長期來看做市商的超額預期利潤必然會被擠壓至零：

$$\mathbb{E}\left[\frac{\text{P\&L}_T}{T}\right] = 0 \implies I_{\infty} = \mathbb{E}[\delta_t]$$

### 🎯 為什麼這個模型比前一個模型更優越？
*   **消除了邏輯悖論**：中間價的變動現在是由對手盤交易方向**實時驅動並給予反饋**的，不再與布朗運動的純隨機外生性相衝突。
*   **完美擬合實盤數據**：它在底層邏輯上完美容納了交易方向的強自相關性（指數衰減現象）。
*   **提供了更強大的微觀經濟學論證**：這證明了「漸進市場衝擊等於平均半價差」這一經驗法則，在**具備價格反饋與庫存記憶的動態一般均衡市場**中依然堅固成立。做市商所賺取的報價價差，本質上是市場因逆向選擇與衝擊成本給予他們的合理風險補償。