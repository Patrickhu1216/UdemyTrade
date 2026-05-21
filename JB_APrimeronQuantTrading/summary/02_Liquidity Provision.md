# Lecture 1： 量化交易筆記：做市策略、流動性提供與常數價差模型 (Constant Spread Model)

## 📌 章節導論與核心目標
歡迎來到第二章節：**流動性提供（Liquidity Provision）、做市商（Market Making）與 Avellaneda-Stoichkov 模型**。

在本課中，我們將建立並檢驗一個最簡單、直覺的**常數價差做市策略（Constant Spread Strategy）**，藉由蒙地卡羅模擬（Monte Carlo Simulation）探討其動態特性與潛在瓶頸。隨後，我們將從該模型的失效中總結出**做市商三大基本風險管理法則**。這些法則將作為下一堂課推導工業界標準 —— **Avellaneda-Stoichkov (AS) 模型**的底層基石。

---

## 1. 常數價差做市商模型架構與數理定義

我們首先在一個最基礎、對稱的連續時間框架下建立做市商模型。

### 📐 基礎資產與價差假設
1. **中間價（Mid Price）**：假設資產的中間價 $S_t$ 服從一個標準的**布朗運動（Brownian Motion）**，其波動率為 $\sigma$：
   $$dS_t = \sigma dW_t$$
   其中 $W_t$ 為標準布朗運動，$\sigma$ 為波動率。
2. **常數半價差（Constant Half-Spread）**：做市商同時在買賣兩側掛單。假設做市商設定一個固定的半價差 $\delta$（在時間上為常數），因此：
   * **最佳賣價（Best Ask / $P^a_t$）**：$P^a_t = S_t + \delta$
   * **最佳買價（Best Bid / $P^b_t$）**：$P^b_t = S_t - \delta$

### 🎯 訂單到達機制：卜瓦松過程（Poisson Process）
市場上的流動性吃單者（Liquidity Takers）會隨機吃掉做市商的掛單。從做市商的角度來看：
* **流動性 Taker 的買單**（對應做市商**賣單 $P^a_t$ 被撮合**），由卜瓦松過程 $N^a_t$ 建模。
* **流動性 Taker 的賣單**（對應做市商**買單 $P^b_t$ 被撮合**），由卜瓦松過程 $N^b_t$ 建模。

在足夠微小的時間區間 $dt$ 內，訂單到達（增量為 1）的機率與 $dt$ 成正比，其常數強度（到達率）皆設為 $\lambda$：
$$\mathbb{P}(dN^a_t = 1) = \lambda dt, \quad \mathbb{P}(dN^b_t = 1) = \lambda dt$$

#### 💡 到達率與價差的指數遞減關係
顯而易見地，每單位時間的訂單到達率 $\lambda$ 是半價差 $\delta$ 的**遞減函數**（因為價差開得越大，報價對外顯示越不具吸引力，成交機率越低）。為了兼顧實證與計算簡便性，模型採用**指數遞減形式**：
$$\lambda(\delta) = A e^{-k \delta}$$
其中 $A$ 與 $k$ 為大於 0 的特定市場常數。

### 📊 帳戶動態演化方程式
為了計算上的簡便，我們假設市場上所有送進來的訂單每筆交易量（Order Size）皆常態化為 **1 單位**。
1. **庫存動態（Inventory / $Q_t$）**：做市商在任何給定時間持有的股票張數。
   $$dQ_t = dN^b_t - dN^a_t \implies Q_t = N^b_t - N^a_t$$
   *當流動性 Taker 執行賣單（$dN^b_t=1$）時，做市商被迫買入，庫存增加；反之，做市商賣單被吃時，庫存減少。*
2. **現金帳戶（Cash Account / $X_t$）**：
   $$dX_t = P^a_t dN^a_t - P^b_t dN^b_t = (S_t + \delta)dN^a_t - (S_t - \delta)dN^b_t$$
3. **累積損益（Cumulative P&L）**：假設初始時間 $t=0$ 時現金與庫存皆為 0。在期末 $T$ 時，做市商的總損益為**現金加上庫存的市值計價（Mark-to-Market, MtM）**：
   $$\text{P\&L}_T = X_T + Q_T S_T$$

---

## 2. 蒙地卡羅模擬與常數價差策略的「致命缺陷」

透過配套的 Section 2 腳本進行單日交易（One Day of Trading，從開盤到收盤）的 Monte Carlo 模擬，我們可以清晰觀察到此策略的運作瓶頸：

### 🚨 庫存積聚（Inventory Accumulation）與風險管理失效
* **實證現象**：在單一條模擬軌跡（Realization）中，由於常數價差策略是**盲目（Blindly）接受任何送進來的訂單**，做市商完全沒有任何手段去主動調控自己的庫存。這會導致**庫存位置 $Q_t$ 出現顯著的單向積聚（例如積累了大量的長部位 Long Position）**。
* **致命後果**：當庫存嚴重偏向單側，一旦中間價 $S_t$ 發生不利走勢（例如股價持續下跌），做市商會因為持有巨額庫存而暴露在巨大的定向風險（Directional Risk）中，進而導致 **P&L 劇烈崩潰**。這種缺乏庫存控制的機制會帶來極差的風險回報比。

### 📊 不同市場情境下的統計特徵對比

透過調整半價差 $\delta$，在三種不同場景下運行多條軌跡模擬，統計腳本輸出的平均損益（$\mu$）、損益標準差（$\sigma$）與夏普比率（Sharpe Ratio），可以總結出以下特徵：

| 統計特徵 | 1. 基準場景 (Base Case) | 2. 隨機跳躍場景 (Random Jump) | 3. 逆向選擇場景 (Adverse Selection) |
| :--- | :--- | :--- | :--- |
| **平均損益 ($\mu$)** | 呈現**倒 U 型**。存在一個最優半價差的「甜區（Sweet Spot）」。 | 與基準場景幾乎相同（因為跳躍方向隨機，期望值互補）。 | **劇烈下降**（利潤被知情交易者大幅侵蝕）。 |
| **損益標準差 ($\sigma$)** | 隨著 $\delta$ 變小而增加（因交易頻繁导致資產震盪暴險）。 | **大幅擴大**（外部價格跳躍衝擊帶來巨大的未實現損益波動）。 | 處於高位。 |
| **夏普比率 (Sharpe)** | 在最佳 $\delta$ 處達到最大值。 | **幾近歸零**（隨機跳躍雖未影響均值，但劇烈放大了風險波動）。 | **幾近歸零**（平均損益因對手盤擁有 Alpha 而被榨乾）。 |

#### 💡 深度解析：基準場景的倒 U 型利潤邏輯
* 當 $\delta$ 極大時，每筆成交賺取高額價差，但訂單強度 $\lambda(\delta)$ 趨近於 0（沒人願意成交），總利潤趨近 0。
* 當 $\delta$ 極小時，成交極其頻繁，但每筆利潤僅 $2\delta$（極其微薄）。
* 因此，在兩者之間存在一個利潤最大化的最佳固定半價差。

#### 💡 深度解析：逆向選擇（Adverse Selection）的威脅
在真實市場中，訂單並非總是常數卜瓦松過程。當做市商的對手盤是**知情交易者（Informed Traders）**時，對方擁有一套對中間價回報的預測算法（Alpha）。知情交易者會主動且精準地針對做市商進行逆向交易，導致做市商在沒有庫存控制的情況下徹底淪為對方的提款機。

---

## 3. 做市商的三大基本風險管理法則（Fundamental Rules）

為了打破常數價差模型的宿命，做市商必須擁有一套**能夠透過「調整報價（半價差）」來「控制庫存」的槓桿**。這是量化做市領域的核心三大鐵律：

### 🟢 法則一：庫存回歸控制（Inventory Controls）—— 核心風險管理
做市商必須依據當前庫存 $Q_t$ 的正負號與大小，動態不對稱地調整買賣兩側的報價。
* **情境**：當庫存積聚（$Q_t > 0$，多頭部位過重）時，做市商需要**減少買入（阻止庫存繼續增加）並刺激賣出（促進平倉）**。
* **報價行為**：做市商應**同時調降**掛在外面的買賣絕對價格（$P^a$ 與 $P^b$ 均下調）。
* **價差結構變動**：這意味著做市商縮小了賣單半價差（**$\delta_a$ 減少**，讓賣價更具吸引力以吸引吃單者）；同時擴大了買單半價差（**$\delta_b$ 增加**，讓買價極不具吸引力以勸退賣方）。
* *註：若庫存為負（$Q_t < 0$），操作完全對稱相反。此舉能讓庫存動態回歸至 0 附近。*

### 🔵 法則二：風險厭惡調整（Risk Aversion / $\gamma$）
* 當做市商的**風險厭惡係數 $\gamma$ 提高**時，意味著做市商對於承擔同等單位的庫存留倉風險，會要求更高的風險溢價補償。
* **報價行為**：做市商應主動**擴大總價差（Full Spread / $\delta_a + \delta_b$）**，以提升每筆交易的毛利潤來對沖更敏感的風險。

### 🔴 法則三：市場波動率調整（Volatility / $\sigma$）
* 當底層資產的**外部市場波動率 $\sigma$ 增加**時，意味著價格波動更劇烈，做市商面臨的外部衝擊與庫存跌價風險同步加劇。
* **報價行為**：為了在風險增加的環境下維持穩定的夏普比率（每單位風險的獲利），做市商同樣必須**擴大總價差（$\delta_a + \delta_b$）**以尋求更高的風險補償。

---

## 4. 邁向工業標準：Avellaneda-Stoichkov 模型的前瞻

上述的三大基本法則，正是隨後我們將深入推導的 **Avellaneda-Stoichkov (AS) 模型** 的理論靈魂。

在 AS 模型中，我們徹底打破了「$\delta$ 為常數」的業餘設定。做市商的買賣半價差 $\delta_a(t)$ 與 $\delta_b(t)$ 變成了**時間的動態變數與庫存 $Q_t$ 的非線性函數**。做市商將透過隨時微調這兩個半價差，動態操控兩側的卜瓦松到達率 $\lambda_a(\delta_a(t))$ 與 $\lambda_b(\delta_b(t))$，主動掌握庫存的控制權，這才是現代高頻做市策略的真正核心。

<br><br>

# # Lecture 2：Avellaneda-Stoichkov 做市商模型與隨機控制

## 📌 章節導論與核心目標
在本課中，我們正式引入並完整推導了做市商領域的工業界標準 —— **Avellaneda-Stoichkov (AS) 模型**。

在上一課中，我們看到了常數價差策略（Constant Spread Strategy）因盲目接受訂單而導致庫存大幅積聚、終端損益（P&L）極易因單邊市崩潰的致命缺陷。AS 模型透過**隨機控制理論（Stochastic Control）**，將買賣兩側的半價差（Half-Spread）變為做市商的**動態控制變數**，以最大化做市商的**期望效用函數（Expected Utility）**為目標，推導出具備自動庫存控管能力的最佳報價策略。

---

## 1. AS 模型基本架構與動態方程

模型在連續時間框架 $t \in [0, T]$ 下運行，為簡化符號，後續將省略時間下標 $t$。

### 📐 狀態變數與隨機過程
系統由三個核心狀態變數（State Variables）構成：
1. **公平中間價（Fair Mid Price / $S_t$）**：假設服從標準布朗運動（Brownian Motion），$\sigma$ 為市場波動率：
   $$dS_t = \sigma dW_t$$
2. **做市商現金帳戶（Cash Account / $X_t$）**：
   $$dX_t = P^a_t dN^a_t - P^b_t dN^b_t$$
3. **做市商現貨庫存（Inventory / $Q_t$）**：假設每筆吃單量常態化為 1 單位：
   $$dQ_t = dN^b_t - dN^a_t \implies Q_t = N^b_t - N^a_t$$

### 🎯 控制變數與動態訂單流
做市商的**控制變數**為買賣兩側的半價差 $\delta_a$ 與 $\delta_b$。報價方程定義為：
* 最佳賣價（Best Ask / $P^a$）：$P^a = S + \delta_a$
* 最佳買價（Best Bid / $P^b$）：$P^b = S - \delta_b$
* 總價差（Full Spread）：$\text{Spread} = \delta_a + \delta_b$

市場訂單流由兩個獨立的卜瓦松過程 $N^a_t$ 和 $N^b_t$ 驅動，其強度（Intensity）由半價差決定，並滿足**指數遞減形式**：
$$\lambda_a(\delta_a) = A e^{-k \delta_a}, \quad \lambda_b(\delta_b) = A e^{-k \delta_b}$$
這意味著價差開得越大（越深入訂單簿內部），預期的訂單流與成交機率就越低；而在中間價（Mid）附近的交易活動最為頻繁。

---

## 2. 最佳化目標：效用函數與 HJB 方程

做市商的目標是在期末 $T$ 最大化其**常絕對風險厭惡（CARA）效用函數**。令終端財富為 $Y_T = X_T + Q_T S_T$（現金加上庫存的市值計價 Mark-to-Market）：

$$\max_{\delta_a, \delta_b} \mathbb{E}_t \left[ - \exp\left( - \gamma (X_T + Q_T S_T) \right) \right]$$

其中 $\gamma > 0$ 為做市商的**風險厭惡係數（Risk Aversion Coefficient）**。由於效用函數的凹性（Concavity），根據詹森不等式（Jensen's Inequality），該目標在經濟學上等同於**在最大化期末財富的同時，最小化其波動性**（本質上是在有效最大化夏普比率 Sharpe Ratio）。

### 📐 價值函數與隨機控制公式
我們定義最優價值函數（Value Function） $u$ 為：
$$u(s, x, q, t) = \max_{\delta_a, \delta_b} \mathbb{E}_t \left[ -\exp\left(-\gamma(X_T + Q_T S_T)\right) \right]$$

為了對含有跳躍（Jump）與連續隨機過程的價值函數進行推導，我們需要使用隨機微積分工具：
* **標準布朗運動**：用於中間價 $S_t$，其二階泰勒展開引入了 $\frac{1}{2}\sigma^2 \frac{\partial^2 u}{\partial s^2}$ 項。
* **卜瓦松跳躍過程**：用於建模訂單流。我們引入**補償卜瓦松過程（Compensated Poisson Process）** $\tilde{N}_t = N_t - \lambda t$，其增量期望值為 0。當我們對全方程取期望值時，補償過程（隨機漂移項）會消失，僅留下與時間增量相關的確定性漂移項。

透過動態規劃原理（Dynamic Programming Principle）與驗證參數（Verification Argument），可證明該最優價值函數必然是下列 **Hamilton-Jacobi-Bellman (HJB) 偏微分方程** 的唯一解：

$$\frac{\partial u}{\partial t} + \frac{\sigma^2}{2} \frac{\partial^2 u}{\partial s^2} + \max_{\delta_b} \left\{ \lambda_b(\delta_b) \left[ u(s, x - (s - \delta_b), q + 1, t) - u(s, x, q, t) \right] \right\} + \max_{\delta_a} \left\{ \lambda_a(\delta_a) \left[ u(s, x + (s + \delta_a), q - 1, t) - u(s, x, q, t) \right] \right\} = 0$$

* 註：當買單側發生跳躍（做市商被動買入 1 單位），現貨庫存 $q \to q+1$，現金 $x \to x - (s - \delta_b)$；賣單側同理。
* 終端條件為：$u(s, x, q, T) = -\exp(-\gamma(x + qs))$。

---

## 3. 分離變數（Ansatz）與 HJB 方程解析求解

為了解決這個非線性偏微分方程，我們參考 Avellaneda 與 Stoichkov 的原始論文，提出**分離變數假設（Ansatz / 猜想解）**：
$$u(s, x, q, t) = -\exp(-\gamma x) \exp\left( -\gamma \theta(s, q, t) \right)$$

將此代入原 HJB 方程並同除以 $-\gamma u$，可將現金變數 $x$ 完美消去。接著對 $\theta$ 進行關於庫存 $q$ 的**二次泰勒展開（Quadratic Expansion）**：
$$\theta(s, q, t) = \theta_0(t) + \theta_1(s, t)q + \theta_2(t)q^2$$
*(為了大幅簡化計算，我們合理假設 $\theta_0$ 與 $\theta_2$ 僅與時間 $t$ 相關，移除其對 $s$ 的依賴。)*

### 📐 求解最優控制變數（一階導數最優化）
代入展開式後，PDE 中關於 $\max$ 的部分轉化為以下標準形式（以 $\delta_b$ 為例，令其括號內狀態變動值為 $\xi$）：
$$\max_{\delta} \left\{ e^{-k \delta} \left[ 1 - e^{-\gamma(\delta + \xi)} \right] \right\}$$

令該式對 $\delta$ 的一階導數為 0，解得最優半價差的一般控制解析式：
$$\delta^* = -\xi + \frac{1}{\gamma} \ln\left(1 + \frac{\gamma}{k}\right)$$

### 📐 提取 $q$ 與 $q^2$ 的係數方程
將最優 $\delta^*$ 通用解代回原方程，並在最優價差不太大時，對指數項進行一階線性展開（$e^{-x} \approx 1 - x$），PDE 轉化為關於 $q$ 的多項式方程。為了使方程對任意 $q$ 恆成立，各次項係數必須分別為 0：
1. **一次項 $q$ 的係數方程**：
   $$\frac{\partial \theta_1}{\partial t} + \frac{\sigma^2}{2} \frac{\partial^2 \theta_1}{\partial s^2} = 0, \quad \text{終端條件 } \theta_1(s, T) = s$$
   解得：**$\theta_1(s, t) = s$**。
2. **二次項 $q^2$ 的係數方程**：
   $$\frac{d \theta_2}{dt} = \frac{1}{2}\gamma \sigma^2, \quad \text{終端條件 } \theta_2(T) = 0$$
   直接積分得：**$\theta_2(t) = -\frac{1}{2}\gamma \sigma^2 (T - t)$**。
   *(備註：常數項與 $t$ 相關項將全部被吸補到 $\theta_0(t)$ 中。由於 $\theta_0$ 不出現在最終報價控制式中，故無需顯式求解。)*

---

## 4. AS 模型最終最優控制解析解

將求得的 $\theta_1$ 與 $\theta_2$ 重新代回報價控制方程，我們得到了 **Avellaneda-Stoichkov 模型的最終核心解析解**：

### 🎯 最優半價差（Optimal Half-Spreads）
$$\delta_a^*(q, t) = \left[ \frac{1}{2}\gamma \sigma^2 (T - t) + \frac{1}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right) \right] + \gamma \sigma^2 (T - t) q$$
$$\delta_b^*(q, t) = \left[ \frac{1}{2}\gamma \sigma^2 (T - t) + \frac{1}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right) \right] - \gamma \sigma^2 (T - t) q$$

### 🎯 最優掛單報價（Optimal Quotes）
$$\begin{aligned}
P^a^*(q, t) &= S + \left[ \frac{1}{2}\gamma \sigma^2 (T - t) + \frac{1}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right) \right] + \gamma \sigma^2 (T - t) q \\
P^b^*(q, t) &= S - \left[ \frac{1}{2}\gamma \sigma^2 (T - t) + \frac{1}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right) \right] + \gamma \sigma^2 (T - t) q
\end{aligned}$$

### 🎯 最優總價差（Optimal Full Spread）
$$\text{Spread}^*(t) = \delta_a^* + \delta_b^* = \gamma \sigma^2 (T - t) + \frac{2}{\gamma}\ln\left(1 + \frac{\gamma}{k}\right)$$
*注意：最優總價差與時間相關，且受各種市場參數影響，但它完全**獨立於當前庫存 $q$**（庫存項在相加時被消去了）。*

---

## 5. 理論驗證：做市商三大鐵律的完美契合

我們來檢驗 AS 模型的數學解析解是否符合前述的做市商直覺直觀規律：

1. **庫存回歸控制（Inventory Rule）**：
   在庫存報價式中，當庫存增加（$q > 0$）時，由於庫存項前面帶有正係數，**$P^a$ 和 $P^b$ 會同時被調降（Decreased）**。這使得做市商的賣價更具吸引力（刺激吃單者買，幫助做市商平倉），買價更不具吸引力（阻止做市商繼續吸籌），完美實現了庫存的動態自動回歸。
2. **風險厭惡彈性（Risk Aversion Rule）**：
   觀察總價差 $\text{Spread}^*$ 方程，風險厭惡係數 $\gamma$ 位於正項係數中。當做市商更規避風險（$\gamma$ 增大）時，**總價差會主動擴大**，要求更高的風險溢價。
3. **市場波動率適應（Volatility Rule）**：
   在總價差方程中，市場資產波動率 $\sigma$ 出現於正項係數。當市場波動加劇（$\sigma$ 升高）時，**總價差會自動變寬**，為做市商提供更厚的利潤安全墊。

---

## 6. 實盤模擬與績效對比（AS 模型 vs 常數價差）

利用相同的蒙地卡羅框架運行單日交易（One Day of Trading）模擬，AS 模型展現出壓倒性的優勢：

* **庫存控制（Inventory Management）**：常數價差策略的庫存會隨機漫步並產生巨大的單向積聚偏離；而 **AS 模型的庫存被嚴格鎖定在 0 軸附近的一個極窄通道（Narrow Band）內往復震盪**，絕無大範圍的極端風險暴露。
* **整體績效與夏普比率（Sharpe Ratio）**：在標準基準場景（Base Case）下，**AS 模型所實現的夏普比率，比優化後的常數價差策略高出整整 7 到 8 倍**。
* **風險承受力（Robustness to External Shocks）**：
  即使我們跳出 AS 模型的理論假設，施加外部衝擊：
  * **在隨機跳躍場景下**（資產價格突發隨機跳躍）：常數價差的夏普比率幾乎歸零；AS 模型雖受影響，但依然展現出驚人的強韌性。
  * **在逆向選擇場景下**（對手盤具備預測 Alpha）：常數價差徹底淪為提款機；AS 模型仍能做出良好回應，展現出穩健的績效。

---

## 📚 權威文獻指引
1. **Avellaneda, M., & Stoichkov, S. (2008)**：《*High-frequency trading in a limit order book*》 —— 量化做市領域里程碑式的原始論文，本課推導的核心依據（本課簡化了部分證明細節，但保留了核心骨架，原文包含更多關於預約價 Reservation Prices 的討論）。
2. **隨機控制理論（Stochastic Control）**：對於不熟悉隨機最優控制與 Hamilton-Jacobi-Bellman (HJB) 偏微分方程連結的同學，高度推薦閱讀經典的隨機控制教程（如本節參考文獻中提及的課程連結）。