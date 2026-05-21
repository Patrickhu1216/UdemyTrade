# Lecture 1：訂單簿統計、動態與建模

## 課程導論與章節架構

限價訂單簿（Limit Order Book, LOB）是電子交易（Electronic Trading）的核心基石。在實作任何高頻或量化交易策略時，深刻理解訂單簿的**統計行為（Statistical Behavior）**與**動態特徵（Dynamical Properties）**至關重要。

本章節（Section 1）共分為三大核心課程：
1. **第一課（本課）**：探索訂單簿數據，歸納出關於「訂單簿總規模分佈」與「流動性剖面（Liquidity Profile）」的兩大核心實證事實（Empirical Facts）。
2. **第二課**：引入**擴散模型（Diffusion Models）**，用以解釋並模擬我們所觀測到的訂單簿總規模現象。
3. **第三課**：深入研究著名的訂單簿動態模型，用以合理解釋訂單簿內部所呈現的流動性分佈規律。

<br>

## 1. 訂單簿的基本概念：市場參與者
訂單簿是一個虛擬的媒合平台，主要由兩大類參與者組成：
* **流動性提供者（Liquidity Providers / 市值製造商 Market Makers）**：
  他們將買賣意向（Size）主動發布（Post）在訂單簿中，並掛單等待。
* **流動性提取者（Liquidity Takers）**：
  他們不願意等待，直接與訂單簿中現有的掛單進行即時撮合（Execution）。

> **範例**：
> 若市場持倉者在訂單簿掛出：「願意在 \$20.00 買入 1000 股」以及「願意在 \$20.02 賣出 100 股」。
> 此時身為個別交易員，若想「立刻買入 200 股」，則前 100 股必須支付每股 \$20.02，而後 100 股則必須支付下一個檔位（如 \$20.03）的價格。

<br>

## 2. 實證數據觀測（以 Intel 股票為例）
以 Nasdaq 上市的 **Intel Corporation (INTC)** 單日完整交易數據（從開盤到收盤）進行 Generic（通用性）分析：
* **中間價（Mid Price）定義**：
  $$\text{Mid Price} = \frac{\text{Best Bid} + \text{Best Offer}}{2}$$
* **中間價走勢**：從約 \$34.00 開始，日內的走勢呈現出量化領域所預期的**布朗運動（Brownian Type Plot）**特徵。
* **三維動態觀測**：將以 Mid Price 為中心（0 軸）的限價訂單簿隨時間推移繪製成時間序列圖，可清晰觀察到全天候頻繁的「委託掛單（Posting）」、「取消掛單（Canceling）」與「成交（Execution）」等微觀結構活動。

<br>

## 3. 實證事實一：訂單簿總規模的直方圖分佈 (Total Size Histogram)
當我們對訂單簿的單邊（買方或賣方，基於對稱性假設進行合併）總規模計算出現頻率（Frequency）直方圖時，發現了一個極為顯著的通用特性：

* **核心現象：存在極為明確的「眾數（Mode / 最常被觀察到的數值）」**。
  在 INTC 的例子中，單邊總規模約在 **60,000 股** 附近出現高達 30% 的頻率峰值。這代表市場存在一個最受青睞的「偏好規模（Preferred Size）」。
* **極端值的直方圖行為**：
  * **極大規模（Large Sizes）**：出現頻率極低（符合直覺，市場極少長時間維持超大單）。
  * **極小規模（Small Sizes）**：出現頻率同樣較低（但比超大單頻繁）。這是因為訂單簿中隨時伴隨著密集的取消委託（Cancellation）與即時成交（Execution），這些行為會迅速縮減訂單簿的規模，使其往偏好規模拉回。

*※ 此現象將在 **Lesson 2** 透過擴散模型進行重點推導。*

<br>

## 4. 實證事實二：時間平均下的流動性剖面 (Liquidity Profile)
如果我們不看時間序列，而是將一整天以 Mid Price 為基準（Mid = 0）的訂單簿數據進行**時間平均（Time Average）**，會得到一個對稱的**鐘形（Bell-shaped）**流動性分佈圖：

* **現象 A（微觀空洞）**：緊鄰中間價（Mid Price）的兩側（Best Bid / Best Offer），流動性（掛單量）相對較少（例如 Best Offer 僅有 4,000 股，而次佳 Offer 則有 6,000 股）。
* **現象 B（流動性頂點）**：流動性並非在最貼近大盤價格處最高，而是在**訂單簿內部（Inside the Book）的某個特定距離達到巔峰**。
* **現象 C（向深處遞減）**：當價格距離中間價越來越遠、進入訂單簿深處（Deep Inside the Book）時，掛單量又會開始逐漸減少（Tells off）。

*※ 這種「中間價附近流動性凹陷、內部見頂、深處遞減」的鐘形曲線，將在 **Lesson 3** 的動態模型中得到完整的數學與機制解釋。*

<br>

## 5. 🛠️ 本課小結
本節透過實盤數據確立了量化建模的兩大基石：
1. 訂單簿總規模分佈具有明確的**眾數（Mode）** $\rightarrow$ *下一課：擴散模型*
2. 訂單簿流動性呈現遠離中間價先升後降的**鐘形剖面（Bell-shaped Profile）** $\rightarrow$ *下下一課：動態模型*

<br><br>

# Lecture 2：訂單簿統計、動態與建模

## 課程核心目標
本課旨在建立一個數學演化方程，用以描述並理解在數據中觀測到的限價訂單簿（LOB）總規模的直方圖分佈。具體而言，我們要推導出**訂單簿單邊總規模 $V$ 在時間 $t$ 下的機率密度函數（PDF） $P(V, t)$**。
* **定義**：$P(V, t)\Delta V$ 代表在時間 $t$，訂單簿規模介於 $V$ 與 $V + \Delta V$ 之間的機率。

<br>

## 1. 離散微觀模型與簡化假設

為了建立演化方程，我們首先將時間與空間進行微觀離散化：
* **時間軸**：$t \rightarrow t + \Delta t$
* **空間軸（規模）**：$V \rightarrow V - \Delta V, \; V, \; V + \Delta V$

### 💡 關鍵簡化假設
* 假設所有市場微觀事件（新委託掛單、取消掛單、即時成交）的**每筆數量（Increment）皆固定為 $\Delta V$**。這是模型的局限性，但能大幅簡化運算。
* 系統在時間 $t$ 轉移至 $t + \Delta t$ 時，僅存在以下三種微觀可能路徑：

| 初始狀態 (時間 $t$) | 觸發事件類型 | 發生機率 | 最終狀態 (時間 $t+\Delta t$) |
| :--- | :--- | :--- | :--- |
| $V - \Delta V$ | **新增事件（Addition）**：送入限價單 | $a$ | $V$ |
| $V + \Delta V$ | **刪除事件（Deletion）**：市價單撮合或取消委託 | $d$ | $V$ |
| $V$ | **無事件（Nothing Happened）**：維持原狀 | $1 - a - d$ | $V$ |

<br>

## 2. 機率流會計（Accounting）與連續 PDE 推導

結合上述狀態轉移路徑，可寫出離散機率平衡方程：
$$P(V, t + \Delta t) = a P(V - \Delta V, t) + d P(V + \Delta V, t) + (1 - a - d) P(V, t)$$

### 泰勒展開式（Taylor Expansion）
為了將離散方程轉換為易於分析的連續偏微分方程（PDE），我們對空間項進行二階泰勒展開：
$$P(V \pm \Delta V, t) \approx P(V, t) \pm \Delta V \frac{\partial P}{\partial V} + \frac{1}{2}(\Delta V)^2 \frac{\partial^2 P}{\partial V^2}$$

將展開式代入原方程，移項並同除以 $\Delta t$ 後，取極限可得**拋物線型偏微分方程（Parabolic PDE）**：
$$\frac{\partial P}{\partial t} = \frac{(\Delta V)^2}{2 \Delta t}(a + d)\frac{\partial^2 P}{\partial V^2} + \frac{\Delta V}{\Delta t}(d - a)\frac{\partial P}{\partial V}$$

### 初步模型的致命缺陷（撞牆期）
若我們為此 PDE 設定初始條件 $P(V, 0) = P_0(V)$ 與常見的**狄利克雷邊界條件（Dirichlet Boundary Conditions）**：
$$P(0, t) = 0, \quad P(\infty, t) = 0$$

根據**最大值原理（Maximum Principle）**，若 $P$ 在 $V=0$ 處為 0 且整體非負，則其在原點的導數必須為正：$\frac{\partial P}{\partial V}(0, t) > 0$。
然而，如果我們對 PDE 的左右兩側進行全空間積分（$\int_0^\infty dV$），以檢查全機率守恆（$\int_0^\infty P dV = 1$），會推導出：
$$\frac{d}{dt}\int_0^\infty P dV = -\frac{(\Delta V)^2}{2 \Delta t}(a + d)\frac{\partial P}{\partial V}(0, t) < 0$$
這意味著**總機率會隨時間流失，無法維持守恆**。

<br>

## 3. 模型修正：引入源項（Source Terms）與邊界控制

機率流失的原因在於**圖表的邊界效應**：當規模退到 $V = \Delta V$ 時，仍有 $d$ 的機率觸發刪除事件而使訂單簿歸零（死亡）。
* **修正機制**：假設當訂單簿規模降至 0 時，會立刻以特定的機率分佈被重新注入市場（Re-created）。在數學上，這等同於在 PDE 中引入**源項（Source Term / 創造機制）** $\frac{\lambda(t)}{\Delta t} P$。

### 🏠 平衡狀態（Stationary / Steady State Solution）
量化實務上，我們對時間演化不感興趣，而是關注長期不隨時間改變的「靜態直方圖」。因此令 $\frac{\partial P}{\partial t} = 0$，偏微分轉為常微分（ODE）。

同除以最高階係數後，修正後的常微分方程為：
$$P''(V) + 2\mu P'(V) + \alpha P(V) = 0$$

其中兩個關鍵參數定義為：
* **$\mu$ (淨刪除偏向)**：
  $$\mu = \frac{1}{\Delta V} \frac{d - a}{d + a}$$
  * *註：為確保解在無窮遠處收斂（$P(\infty)=0$），$\mu$ 必須為正數，即 **$d > a$（刪除率必須大於新增率）**，否則訂單簿規模將無限膨脹。*
* **$\alpha$ (源項強度常數)**：由邊界控制決定。經積分檢驗，$\alpha$ 必須精確等於原點導數：**$\alpha = P'(0) > 0$**，以確保總機率積分完美守恆（等於 1）。

<br>

## 4. 兩種擴散模型 flavor 的解析解與眾數（Mode）推導

依據源項注入的形式不同，我們能推導出兩種實用的擴散模型定性解：

### 模型的特徵方程
$$x^2 + 2\mu x + \alpha = 0 \quad \rightarrow \quad x = -\mu \pm \sqrt{\mu^2 - \alpha}$$
為避免機率出現物理意義不合的震盪，根必須為實根，因此限制 **$0 < \alpha \le \mu^2$**。

<br>

### Flavor A：雙曲正弦連續模型（連續源項注入）

當 $0 < \alpha < \mu^2$ 時，結合邊界條件可得解析解：
$$P(V) = \frac{\alpha}{\sqrt{\mu^2 - \alpha}} e^{-\mu V} \sinh\left(\sqrt{\mu^2 - \alpha} \, V\right)$$

當 $\alpha \rightarrow \mu^2$ 的極限情況下（重根），解析解簡化為：
$$P(V) = \mu^2 V e^{-\mu V}$$

#### 眾數（Mode / 機率極大值點 $V_0$）推導
利用對數微分法（$\frac{d}{dV}\ln P(V_0) = 0$）：
* **當 $\alpha = \mu^2$ 時**：
  $$\frac{1}{V_0} - \mu = 0 \quad \rightarrow \quad V_0 = \frac{1}{\mu}$$
* **當 $0 < \alpha < \mu^2$ 時**：
  $$\sqrt{\mu^2 - \alpha} \coth\left(\sqrt{\mu^2 - \alpha} \, V_0\right) = \mu$$
  經雙曲正切轉換，此方程存在唯一實根 $V_0$。當 $\alpha$ 接近 $\mu^2$ 時，其極值點同樣逼近 $\frac{1}{\mu}$。

<br>

### Flavor B：狄拉克 Delta 點源模型（固定規模重新注入）

若我們不在邊界注入，而是假設訂單簿死亡後，會在一個固定的特定規模 $V_0$ 處被重新喚醒。方程轉化為：
$$P''(V) + 2\mu P'(V) = -\alpha \delta(V - V_0)$$
其中 $\delta$ 為狄拉克 delta 分佈。此模型會使一階導數在 $V_0$ 處產生跳躍（Jump），在圖形上呈現一個**拐點（Kink）**。

#### 解析解分段函數
* **當 $0 \le V \le V_0$ 時**（滿足 $P(0)=0$）：
  $$P(V) = \frac{1}{V_0} \left(1 - e^{-2\mu V}\right)$$
* **當 $V > V_0$ 時**（滿足 $P(\infty)=0$）：
  $$P(V) = \frac{1}{V_0} \left(e^{2\mu V_0} - 1\right) e^{-2\mu V}$$

<br>

## 5. Python 實盤擬合（SciPy Least Squares）與實證結論

我們使用 SciPy 的 `least_squares` 套件，將上述兩種理論模型對 Intel（INTC）股票的實盤訂單簿規模直方圖進行最小二乘法擬合（令參數量化為 $Q = e^{-2\mu} \in [0, 1]$）：

### 擬合結果與比較
* **眾數捕捉**：兩套模型皆精準預測出市場最常觀察到的訂單簿單邊規模（Mode）在 **65,000 股**（$V_0 \approx 6.5$）附近。
* **模型表現對比**：
  * **點源模型（Flavor B, 藍線）**：擬合效果顯著優於連續模型。它能更好地捕捉峰值（Mode）出現的真實頻率，且對兩側長尾（Tails）的控制也較好。
  * **連續模型（Flavor A, 紅線）**：會出現明顯高估肥尾（Overestimating the tails）的現象。

### 擴散模型的局限性
作為標準擴散模型（Diffusion Model），其本質很難完全捕捉金融高頻數據中的**高狹峰特徵（Leptokurtic Character / 尖峰肥尾）**。但以如此精簡的單參數或雙參數模型而言，它已具備極佳的**定性解釋力（Qualitative Fit）**，成功解釋了為什麼市場訂單簿會自發性地維持一個「偏好的核心規模」。

<br><br>

# 量化交易筆記：限價訂單簿（LOB）總規模的擴散模型與分佈推導

## 📌 章節導論與實證背景
限價訂單簿（Limit Order Book, LOB）是電子交易與高頻交易的微觀基石。為了優化交易策略，我們必須掌握其統計行為。

本課的核心目標是推導出**訂單簿單邊總規模 $V$ 在時間 $t$ 下的機率密度函數（PDF） $P(V, t)$**，用以解釋實盤數據中觀測到的核心現象：
1. **訂單簿總規模存在明確的「眾數（Mode）」**：市場存在一個最常被觀察到的「偏好核心規模」。
2. **極端規模出現頻率極低**：大單極少長時間維持，而規模過小時會因市場密集的取消與撮合而迅速被拉回。

---

## 1. 離散微觀模型與簡化假設
為了建立演化方程，我們首先將時間與空間進行微觀離散化：
* **時間軸**：$t \rightarrow t + \Delta t$
* **空間軸（規模）**：$V \rightarrow V - \Delta V, \; V, \; V + \Delta V$

### 💡 核心簡化假設
* 假設所有市場微觀事件（新委託掛單、取消掛單、即時成交）的**每筆變動數量（Increment）皆固定為 $\Delta V$**。
* 系統在時間 $t$ 轉移至 $t + \Delta t$ 時，僅存在以下三種微觀可能路徑：

| 初始狀態 (時間 $t$) | 觸發事件類型 | 發生機率 | 最終狀態 (時間 $t+\Delta t$) |
| :--- | :--- | :--- | :--- |
| $V - \Delta V$ | **新增事件（Addition）**：送入限價單 | $a$ | $V$ |
| $V + \Delta V$ | **刪除事件（Deletion）**：市價單撮合或取消委託 | $d$ | $V$ |
| $V$ | **無事件（Nothing Happened）**：維持原狀 | $1 - a - d$ | $V$ |

---

## 2. 機率流會計與連續偏微分方程（PDE）推導
結合上述狀態轉移路徑，可寫出離散機率平衡方程：
$$P(V, t + \Delta t) = a P(V - \Delta V, t) + d P(V + \Delta V, t) + (1 - a - d) P(V, t)$$

### 📐 泰勒展開與連續化
對空間項進行二階泰勒展開：
$$P(V \pm \Delta V, t) \approx P(V, t) \pm \Delta V \frac{\partial P}{\partial V} + \frac{1}{2}(\Delta V)^2 \frac{\partial^2 P}{\partial V^2}$$

將展開式代入原方程，移項並同除以 $\Delta t$ 後，取極限可得**拋物線型偏微分方程（Parabolic PDE）**：
$$\frac{\partial P}{\partial t} = \frac{(\Delta V)^2}{2 \Delta t}(a + d)\frac{\partial^2 P}{\partial V^2} + \frac{\Delta V}{\Delta t}(d - a)\frac{\partial P}{\partial V}$$

### ⚠️ 初步模型的物理衝突（邊界效應）
若為此 PDE 設定初始條件 $P(V, 0) = P_0(V)$ 與狄利克雷邊界條件（Dirichlet Boundary Conditions）：
$$P(0, t) = 0, \quad P(\infty, t) = 0$$

根據數學上的**最大值原理（Maximum Principle）**，若 $P$ 在邊界 $V=0$ 處為 0 且整體非負，則其在原點的導數必須為正（$\frac{\partial P}{\partial V}(0, t) > 0$）。
然而，若對 PDE 進行全空間積分（$\int_0^\infty dV$），會推導出：
$$\frac{d}{dt}\int_0^\infty P dV = -\frac{(\Delta V)^2}{2 \Delta t}(a + d)\frac{\partial P}{\partial V}(0, t) < 0$$
這意味著**總機率會隨時間向外流失，無法維持全機率守恆（等於 1）**。在物理意義上，這是因為當訂單簿規模降至 0 時，模型缺乏一個讓它「重新甦醒」的機制。

---

## 3. 模型修正：引入源項（Source Terms）與平衡狀態
為了修正邊界流失，我們假設當訂單簿規模歸零死亡後，會立刻以特定的機率分佈被重新注入（Re-created）市場。在數學上，這等同於在 PDE 中引入**源項（Source Term）**。

### 🏠 平衡狀態（Stationary / Steady State Solution）
量化實務中，我們關注的是長期不隨時間改變的靜態直方圖。令 $\frac{\partial P}{\partial t} = 0$，偏微分方程轉化為常微分方程（ODE）。同除以最高階係數後，修正後的方程為：
$$P''(V) + 2\mu P'(V) + S(V) = 0$$

其中關鍵參數與結構定義如下：
1. **$\mu$ (淨刪除偏向)**：
   $$\mu = \frac{1}{\Delta V} \frac{d - a}{d + a}$$
   *註：為確保解在無窮遠處收斂，$\mu$ 必須為正數，即 **$d > a$（刪除率大於新增率）**，否則訂單簿將無限膨脹。*
2. **$S(V)$ (源項分佈)**：依據重新注入市場的形式不同，衍生出以下兩種擴散模型 Flavor。

---

## 4. 兩種擴散模型 Flavor 的解析解與眾數（Mode）推導

常微分方程的特徵方程為：$x^2 + 2\mu x + \dots = 0$，其基本特徵根形式與 $-\mu \pm \sqrt{\mu^2 - \dots}$ 相關。為避免機率分佈出現物理意義不合的虛數震盪，根必須為實根。

### 🔹 Flavor A：雙曲正弦連續模型（連續源項注入）
此模型假設源項以正比於自身機率的方式連續注入：$S(V) = \alpha P(V)$。
$$P''(V) + 2\mu P'(V) + \alpha P(V) = 0$$

經全空間積分檢驗，此方程存在**一致性關係**：$\alpha = P'(0)$。然而在數學上，只要參數滿足 **$0 < \alpha \le \mu^2$**，全機率積分就必然守恆為 1。因此，**$\alpha$ 在此是一個自由參數（Free Parameter）**，用來控制分佈的形狀與峰值高度。

#### 📐 解析解
* **當 $0 < \alpha < \mu^2$ 時（相異實根）**：
  $$P(V) = \frac{\alpha}{\sqrt{\mu^2 - \alpha}} e^{-\mu V} \sinh\left(\sqrt{\mu^2 - \alpha} \, V\right)$$
* **當 $\alpha = \mu^2$ 時（重根極限）**：
  $$P(V) = \mu^2 V e^{-\mu V}$$

#### 🎯 眾數（Mode / 機率極大值點 $V_0$）
利用對數微分法（$\frac{d}{dV}\ln P(V_0) = 0$）：
* **當 $\alpha = \mu^2$ 時**：
  $$\frac{1}{V_0} - \mu = 0 \quad \rightarrow \quad V_0 = \frac{1}{\mu}$$
* **當 $0 < \alpha < \mu^2$ 時**，唯一極值點滿足：
  $$\sqrt{\mu^2 - \alpha} \coth\left(\sqrt{\mu^2 - \alpha} \, V_0\right) = \mu$$
  當 $\alpha$ 逼近 $\mu^2$ 時，眾數位置同樣收斂至 $\frac{1}{\mu}$。這完美解釋了為什麼偏好規模由新增與刪除的相對速率（$\mu$）所決定。

---

### 🔹 Flavor B：狄拉克 Delta 點源模型（固定規模重新注入）
此模型假設訂單簿死亡後，會精確地在一個固定的特定規模 $V_0$ 處被重新喚醒：$S(V) = \alpha \delta(V - V_0)$。
$$P''(V) + 2\mu P'(V) = -\alpha \delta(V - V_0)$$

此模型會導致一階導數在 $V_0$ 處產生跳躍（Jump），在圖形上呈現一個**拐點（Kink）**。
經由邊界條件 $P(0)=0$、$P(\infty)=0$、全空間積分守恆以及導數跳躍條件（$P'(V_0^+) - P'(V_0^-) = -\alpha$）的嚴謹約束，推導出**核心參數對應關係：$\alpha = \frac{2\mu}{V_0}$**。

#### 📐 嚴謹常態化分段解析解
* **當 $0 \le V \le V_0$ 時**：
  $$P(V) = \frac{1}{V_0} \left(1 - e^{-2\mu V}\right)$$
* **當 $V > V_0$ 時**：
  $$P(V) = \frac{1}{V_0} \left(e^{2\mu V_0} - 1\right) e^{-2\mu V}$$
*(註：此處 $A = \frac{1}{V_0}$ 的化簡形式，是在高頻實務中忽略了微小的指數殘差常態化因子的優雅近似解。)*

---

## 5. Python 實盤擬合與量化結論
我們使用 SciPy 的 `least_squares` 套件，將上述兩套理論模型對 Intel（INTC）股票的實盤訂單簿規模直方圖進行最小二乘法擬合（參數量化為 $Q = e^{-2\mu}$）：

### 📊 擬合表現對比
* **眾數捕捉**：兩套模型皆能精準指出市場最常觀察到的訂單簿單邊規模（Mode）在 **65,000 股**（$V_0 \approx 6.5$）附近。
* **Flavor A (連續模型 - 紅線)**：會出現明顯**高估肥尾（Overestimating the tails）**的現象，對峰值的捕捉稍顯無力。
* **Flavor B (點源模型 - 藍線)**：擬合效果**顯著優於連續模型**。它能精準鎖定眾數出現的真實頻率（Peak），且對兩側長尾的控制也更貼近實盤。

### ⚠️ 模型的量化局限性
作為標準擴散模型（Diffusion Model），其流體連續性的本質很難 100% 完美捕捉金融高頻數據中的**高狹峰特徵（Leptokurtic Character / 尖峰肥尾）**。然而，以如此精簡的單/雙參數模型而言，它已具備極佳的**定性解釋力（Qualitative Fit）**，成功從數學機制上證明了訂單簿規模自我穩定的動態平衡。


# Lecture 3：限價訂單簿（LOB）幾何形狀的微觀建模 —— BMP 模型

## 📌 章節導論與實證背景
在本課中，我們聚焦於一個核心問題：**如何建模限價訂單簿的幾何形狀（Shape of the Book）？**

正如我們在實盤數據的數值實驗中所觀察到的，不論是買單側（Bid Size）還是賣單側（Offer Size），每個相對價格水平上的訂單數量都呈現出一種非常特殊的形狀：**最佳報價（Best Bid/Offer）附近的流動性（Liquidity）較低，流動性在訂單簿內部達到峰值（眾數），隨後向深處劇烈衰減。**

為了理解其背後的微觀機制，本課將推導經典的 **Bouchaud-Mezard-Potters 模型（簡稱 BMP 模型）**。由於買賣兩側具備高度對稱性，以下推導將完全聚焦於**買單側（Bid Side）**。

---

## 1. BMP 模型的微觀框架與基本假設

### 📐 符號與坐標定義
* **$\rho(D)$**：相對於最佳買價的**深度 $D$ 處的訂單密度（Density of Orders）**。由於我們最終會對全空間進行常態化（Normalization），使總積分為 1，因此在推導過程中，$\rho(D)$ 只需要精確到相差一個乘法常數即可。
* **$\pi(x)$**：新訂單的**到達率（Rate of Arrival）**，它取決於絕對價格。
* **$B(t)$**：時間 $t$ 時的**最佳買價（Best Bid）**。
  * 假設在初始時間 $t=0$，最佳買價位於原點：$B(0) = 0$。
  * 在時間 $t$，最佳買價波動到了某個絕對價格位置 $x$，即 $B(t) = x$。

### 💡 機率貢獻的疊加邏輯
如果我們坐在相對於當前最佳買價深度為 $D$ 的位置（即價格為 $B(t) - D$）：
1. 當時間 $t$ 且 $B(t) = x$ 時，該位置對應的絕對價格為 $x - D$（或依變數對稱性寫作 $\pi(x + D)$）。新訂單將以 $\pi(x + D)$ 的速率送入該位置，這構成了時間 $t$ 對深度 $D$ 處訂單密度的貢獻。
2. 我們必須將此到達率乘以系統處於該狀態的機率，即 $B(t) = x$ 的機率密度 $P_D(x, t)$。
3. **邊界約束（Boundary Constraint）**：當最佳買價向左劇烈波動，甚至跌破 $-D$（即 $x < -D$）時，這個特定的價格水平將不再屬於買單訂單簿的內部（It drops out of the book），該處積存的訂單將不復存在。因此，必須施加限制 $x + D \ge 0$，這使得我們對 $x$ 的積分範圍被約束在 $[-D, \infty)$。
4. **歷史權重**：BMP 模型對歷史上所有時間 $t$ 的機率貢獻給予一個指數衰減權重 $e^{-\gamma t}$ 進行加權整合。

---

## 2. 熱方程（Heat Equation）與鏡像法（Method of Images）求解

BMP 模型給出了一個經典的隨機假設：**最佳買價 $B(t)$ 服從標準布朗運動（Brownian Motion）**。

因此，其受限機率密度 $P_D(x, t)$ 必須滿足隨機微積分在 PDE 中的對應形式 —— **熱方程（Heat Equation）**：
$$\frac{\partial P}{\partial t} = \frac{\sigma^2}{2} \frac{\partial^2 P}{\partial x^2}$$
其中 $\sigma$ 為最佳買價的波動率（Volatility）。

### 🏠 初始條件與邊界條件
1. **初始條件**：在 $t=0$ 時，系統從原點出發，表現為狄拉克 Delta 函數：$P_D(x, 0) = \delta(0)$（對於 $x > -D$）。
2. **狄利克雷邊界條件（Dirichlet Boundary Condition）**：一旦 $x$ 觸及 $-D$，該層級即移出訂單簿，機率密度必須歸零：
   $$P_D(-D, t) = 0 \quad (\forall t)$$

### 📐 鏡像法（Method of Images）
如果沒有邊界約束，單純滿足狄拉克初始條件的解就是經典的高斯熱核（Heat Kernel）。為了在 $x = -D$ 處強行構造一個零點，我們在 **$x = -2D$ 處放置一個虛擬的負狄拉克源**。

利用線性 PDE 的疊加原理，將這兩個對稱的高斯鐘形曲線相減，即可得到滿足所有條件的精確解：
$$P_D(x, t) = \frac{1}{\sqrt{2\pi \sigma^2 t}} \left[ \exp\left(-\frac{x^2}{2\sigma^2 t}\right) - \exp\left(-\frac{(x + 2D)^2}{2\sigma^2 t}\right) \right]$$

---

## 3. 空間與時間分離：構造常微分方程（ODE）

根據富比尼定理（Fubini's Theorem），我們可以交換空間（$x$）與時間（$t$）的積分順序：
$$\rho(D) \propto \int_{-D}^{\infty} \pi(x + D) \left( \int_0^\infty P_D(x, t) e^{-\gamma t} \, dt \right) \, dx$$

我們首先單獨計算內層關於時間的積分項，定義一個純粹關於空間的函數 $I(x)$：
$$I(x) = \int_0^\infty P_D(x, t) e^{-\gamma t} \, dt$$
為了後續消項的便利，我們巧妙地選擇時間衰減常數為 $\gamma = \frac{\lambda^2 \sigma^2}{2}$。

### 📐 將 PDE 轉化為 ODE
由於 $P_D$ 滿足熱方程，我們對 $I(x)$ 求二階空間導數：
$$\frac{\sigma^2}{2} \frac{d^2 I}{dx^2} = \int_0^\infty \frac{\sigma^2}{2} \frac{\partial^2 P}{\partial x^2} e^{-\gamma t} \, dt = \int_0^\infty \frac{\partial P}{\partial t} e^{-\gamma t} \, dt$$

對右側進行**分部積分（Integration by Parts）**：
$$\int_0^\infty \frac{\partial P}{\partial t} e^{-\gamma t} \, dt = \left[ P e^{-\gamma t} \right]_0^\infty + \gamma \int_0^\infty P e^{-\gamma t} \, dt$$
* 在 $t \rightarrow \infty$ 處，項因指數衰減而歸零。
* 在 $t = 0$ 處，帶入雙狄拉克初始條件：$-P_D(x, 0) = -\delta(0) + \delta(-2D)$。

兩邊同除以 $\frac{\sigma^2}{2}$，並搬移項，我們得到一個**簡單的二階線性常微分方程（ODE）**：
$$\frac{d^2 I}{dx^2} - \lambda^2 I(x) = -\frac{2}{\sigma^2}\delta(0) + \frac{2}{\sigma^2}\delta(-2D)$$
同步繼承邊界條件：$I(-D) = 0$。

### 📐 求解 $I(x)$
此特徵方程的根為 $\pm\lambda$。由於右側存在狄拉克 Delta 函數，這會在 $x=0$ 與 $x=-2D$ 處產生尖點（Kink）。利用指數函數與絕對值對稱減法，可直接寫出滿足邊界條件的解析解：
$$I(x) = \frac{1}{\lambda \sigma^2} \left[ e^{-\lambda |x|} - e^{-\lambda |x + 2D|} \right]$$

---

## 4. 訂單密度 $\rho(D)$ 的解析解與冪律特定解

將求得的 $I(x)$ 代回，並透過變數平移（將 $x + D$ 替換為 $x$，使積分下界從 $-D$ 變為 $0$），我們得到 $\rho(D)$ 的積分解（此處已略去乘法常數 $C$）：
$$\rho(D) \propto \int_0^\infty \pi(x) \left[ e^{-\lambda |x - D|} - e^{-\lambda |x + D|} \right] \, dx$$

為了消除絕對值符號，我們將積分區間以 $D$ 為界拆分為二：
$$\rho(D) \propto \int_0^D \pi(x) \left[ e^{-\lambda (D - x)} - e^{-\lambda (x + D)} \right] \, dx + \int_D^\infty \pi(x) \left[ e^{-\lambda (x - D)} - e^{-\lambda (x + D)} \right] \, dx$$

透過代數化簡，將指數項提項：
* 第一部分可以提出 $e^{-\lambda D}$，剩餘項化為**雙曲正弦函數 $\sinh(\lambda x)$**。
* 第二部分可以提出 $e^{\lambda D} - e^{-\lambda D}$，化為 **$\sinh(\lambda D)$**。

### 🔹 引入冪律到達率（Power Law Choice）
BMP 模型提供了一個最符合微觀市場實證的到達率假設 —— **冪律分佈（Power Law）**：
$$\pi(x) = \frac{1}{x^{1 + \mu}} \quad (\text{為確保可積性，約束 } 0 < \mu < 1)$$

帶入並進行無因次化變數代換（令 $\bar{D} = \lambda D$, $\bar{x} = \lambda x$），消去所有 $\lambda$ 參數後，可定義出標準核心函數 $\rho_0(\bar{D})$：
$$\rho_0(\bar{D}) = e^{-\bar{D}} \int_0^{\bar{D}} \bar{x}^{-1-\mu} \sinh(\bar{x}) \, d\bar{x} + \sinh(\bar{D}) \int_{\bar{D}}^\infty \bar{x}^{-1-\mu} e^{-\bar{x}} \, d\bar{x}$$

#### 🎯 最終理論結論
$$\rho(D) = C_{norm} \cdot \rho_0(\lambda D)$$
這意味著，任何資產的訂單簿形狀 $\rho(D)$，在經過尺度縮放（$\lambda$）與常態化因子（$C_{norm}$）調整後，**皆會收斂至相同的通用理論曲線**。

---

## 5. 實盤擬合、模擬數據驗證與模型局限性

### 📊 實盤數據（如 INTC 股票）擬合結論
透過 Python 的非線性最小二乘法（Least Squares）程序對實盤數據直方圖進行擬合：
* **優點（Qualitative Fit）**：BMP 模型非常成功地從數理機制上解釋了為什麼**最佳報價附近的流動性存在凹陷**。它完美捕捉了流動性在簿內聚集成峰、隨後向深處衰減的特徵。
* **缺點（Systematic Bias）**：作為一種本質上基於連續流體（布朗運動）的擴散模型變體，它會表現出系統性偏差 —— **傾向於低估真實的峰值（Underestimate the peak）並高估兩側的長尾（Overestimate the tails）**。

### 🤖 蒙地卡羅模擬數據（Synthetic Data）的驚人反思
當我們使用基於標準卜瓦松過程（Poisson Process）建立的蒙地卡羅模擬訂單簿數據（隨機進行 Add, Cancel, Execute）來檢驗此模型時：
* **擬合結果**：BMP 模型在模擬數據上的表現**顯著優於實盤數據**，殘差極小，且對尾部的預測極其精準。
* **量化啟示**：這說明了為什麼實盤擬合會有偏差。因為在簡化建模時，我們將真實市場中的**訂單聚集效應（Clustering）**、**自相關性**以及**尖峰肥尾**等複雜微觀特徵「掃到了地毯下」（忽略了）。這體現了量化建模中**模型簡潔性（Complexity）與擬合精準度（Goodness of fit）之間的經典權衡（Trade-off）**。

---

## 📚 權威文獻指引
1. **Bouchaud, Mezard, Potters (2002)**：《*Statistical properties of stock order books: empirical results and models*》 —— 本課推導所依據的經典 BMP 模型原始論文。
2. **Bouchaud, Bonart, Donier, Gould (2018)**：《*Trades, Quotes and Prices: Financial Market Microstructure and Empirical Rules*》 —— 內有對限價訂單簿動態流體建模、擴散模型更廣泛且先進的延伸探討。
3. **偏微分方程最大值原理**：若需深入研究 Lecture 2 中全機率流失所依據的邊界控制定理，可查閱經典 PDE 教科書中有關 Parabolic Equations 的 Maximum Principle 章節。