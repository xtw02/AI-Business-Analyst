\# 业务指标定义与计算口径



本文档用于 AI 数据分析 Agent 的指标知识库。



Agent 在生成 SQL 前，应优先检索本文档，并严格按照本文档定义计算指标。



\---



\# 一、数据表粒度与基础说明



\## 1. sales 表



`sales` 是经过清洗后的正常销售明细表。



数据处理规则：



\* Quantity > 0

\* InvoiceNo 不以 `C` 开头

\* 保留正常销售记录

\* 每一行代表一个\*\*订单中的一个商品明细行（Line Item）\*\*

\* 一张订单可能包含多个商品，因此一个 InvoiceNo 可能对应多行数据



\### 重要



`sales` 表的：



```text

一行 ≠ 一张订单

一行 ≠ 一个客户

```



因此：



```text

COUNT(\*) ≠ 订单数

COUNT(\*) ≠ 客户数

```



\---



\# 二、核心指标



\## 1. 销售额（Sales）



\### 定义



所有正常销售商品的销售金额之和。



\### SQL



```sql

SUM(Amount)

```



\### Amount 定义



```text

Amount = Quantity × UnitPrice

```



\### 示例



```sql

SELECT SUM(Amount) AS TotalSales

FROM sales;

```



\---



\## 2. 订单数（Order Count）



\### 定义



不同订单号的数量。



\### 正确 SQL



```sql

COUNT(DISTINCT InvoiceNo)

```



\### 示例



```sql

SELECT COUNT(DISTINCT InvoiceNo) AS OrderCount

FROM sales;

```



\### 重要规则



\*\*禁止使用：\*\*



```sql

COUNT(\*)

```



计算订单数。



原因：



`sales` 是商品明细表，一张订单可能包含多个商品，因此一张订单可能对应多行。



\---



\## 3. 客户数（Customer Count）



\### 定义



不同 CustomerID 的客户数量。



\### 正确 SQL



```sql

COUNT(DISTINCT CustomerID)

```



\### 示例



```sql

SELECT COUNT(DISTINCT CustomerID) AS CustomerCount

FROM sales;

```



\### 注意



如果需要计算用户相关指标，应明确说明是否排除 `CustomerID IS NULL`。



通常情况下：



```sql

COUNT(DISTINCT CustomerID)

```



会自动忽略 NULL。



\---



\## 4. 商品明细行数（Line Item Count）



\### 定义



销售明细表中的记录行数。



\### SQL



```sql

COUNT(\*)

```



\### 示例



```sql

SELECT COUNT(\*) AS LineItemCount

FROM sales;

```



\### 重要



商品明细行数与订单数不是同一个指标。



```text

LineItemCount = COUNT(\*)



OrderCount = COUNT(DISTINCT InvoiceNo)

```



\---



\## 5. 销售数量（Quantity）



\### 定义



销售商品数量之和。



\### SQL



```sql

SUM(Quantity)

```



\### 示例



```sql

SELECT SUM(Quantity) AS TotalQuantity

FROM sales;

```



\---



\## 6. 客单价（Average Order Value / AOV）



\### 定义



平均每张订单产生的销售额。



\### 计算公式



```text

客单价 = 销售额 / 订单数

```



\### 正确 SQL



```sql

SUM(Amount) / COUNT(DISTINCT InvoiceNo)

```



\### 推荐写法



```sql

ROUND(

&#x20;   SUM(Amount) / COUNT(DISTINCT InvoiceNo),

&#x20;   2

) AS AvgOrderValue

```



\### 重要



不要使用：



```sql

SUM(Amount) / COUNT(\*)

```



作为客单价。



因为 `COUNT(\*)` 是商品明细行数，不是订单数。



\---



\## 7. 平均明细行金额（Average Line Value）



\### 定义



每条商品明细记录对应的平均销售金额。



\### 计算公式



```text

平均明细行金额 = 销售额 / 商品明细行数

```



\### SQL



```sql

SUM(Amount) / COUNT(\*)

```



\### 注意



该指标不是客单价。



```text

平均明细行金额 ≠ 客单价

```



\---



\## 8. 人均销售额（Sales Per Customer）



\### 定义



平均每个客户产生的销售额。



\### 计算公式



```text

人均销售额 = 销售额 / 客户数

```



\### SQL



```sql

SUM(Amount) / COUNT(DISTINCT CustomerID)

```



\### 推荐写法



```sql

ROUND(

&#x20;   SUM(Amount) / COUNT(DISTINCT CustomerID),

&#x20;   2

) AS SalesPerCustomer

```



\---



\## 9. 人均订单数（Orders Per Customer）



\### 定义



平均每个客户产生的订单数量。



\### 计算公式



```text

人均订单数 = 订单数 / 客户数

```



\### SQL



```sql

COUNT(DISTINCT InvoiceNo) / COUNT(DISTINCT CustomerID)

```



\### 推荐写法



```sql

ROUND(

&#x20;   CAST(COUNT(DISTINCT InvoiceNo) AS FLOAT)

&#x20;   / COUNT(DISTINCT CustomerID),

&#x20;   2

) AS OrdersPerCustomer

```



\---



\## 10. 件单价（Average Unit Price）



\### 定义



销售商品的平均商品单价。



\### SQL



```sql

AVG(UnitPrice)

```



\### 注意



件单价不是客单价。



```text

件单价 = 商品层面的价格

客单价 = 订单层面的销售金额

```



\---



\# 三、复购相关指标



\## 1. 复购客户



\### 定义



在统计周期内下单次数 >= 2 的客户。



\### SQL



```sql

SELECT CustomerID

FROM sales

WHERE CustomerID IS NOT NULL

GROUP BY CustomerID

HAVING COUNT(DISTINCT InvoiceNo) >= 2;

```



\---



\## 2. 复购客户数



\### 定义



统计周期内至少购买两次的客户数量。



\### SQL



```sql

SELECT COUNT(\*) AS RepeatCustomers

FROM (

&#x20;   SELECT CustomerID

&#x20;   FROM sales

&#x20;   WHERE CustomerID IS NOT NULL

&#x20;   GROUP BY CustomerID

&#x20;   HAVING COUNT(DISTINCT InvoiceNo) >= 2

) t;

```



\---



\## 3. 复购率



\### 定义



复购客户数占全部有订单客户数的比例。



\### 计算公式



```text

复购率

=

复购客户数 / 客户总数

```



其中：



```text

复购客户 = 订单数 >= 2 的客户

客户总数 = 有效 CustomerID 的去重客户数

```



\### SQL



```sql

WITH customer\_orders AS (

&#x20;   SELECT

&#x20;       CustomerID,

&#x20;       COUNT(DISTINCT InvoiceNo) AS order\_count

&#x20;   FROM sales

&#x20;   WHERE CustomerID IS NOT NULL

&#x20;   GROUP BY CustomerID

)

SELECT

&#x20;   SUM(CASE WHEN order\_count >= 2 THEN 1 ELSE 0 END) \* 1.0

&#x20;   / COUNT(\*) AS RepeatPurchaseRate

FROM customer\_orders;

```



\### 注意



复购率必须明确统计周期。



例如：



```text

2021年8月复购率

```



不能直接使用全历史订单计算。



\---



\# 四、时间指标



\## 1. 销售额按月



\### 定义



按照 InvoiceDate 所属月份统计销售额。



\### SQL



SQLite 推荐：



```sql

SELECT

&#x20;   strftime('%Y-%m', InvoiceDate) AS Month,

&#x20;   SUM(Amount) AS TotalSales

FROM sales

GROUP BY Month

ORDER BY Month;

```



\---



\## 2. 订单数按月



```sql

SELECT

&#x20;   strftime('%Y-%m', InvoiceDate) AS Month,

&#x20;   COUNT(DISTINCT InvoiceNo) AS OrderCount

FROM sales

GROUP BY Month

ORDER BY Month;

```



\---



\## 3. 客户数按月



```sql

SELECT

&#x20;   strftime('%Y-%m', InvoiceDate) AS Month,

&#x20;   COUNT(DISTINCT CustomerID) AS CustomerCount

FROM sales

WHERE CustomerID IS NOT NULL

GROUP BY Month

ORDER BY Month;

```



\---



\# 五、销售额拆解指标



当用户询问：



```text

为什么销售额高？

为什么销售额下降？

为什么销售额增长？

```



优先考虑以下拆解：



```text

销售额

=

客户数 × 人均订单数 × 客单价

```



其中：



```text

客户数

=

COUNT(DISTINCT CustomerID)



人均订单数

=

订单数 / 客户数



客单价

=

销售额 / 订单数

```



因此：



```text

Sales

≈

CustomerCount

×

OrdersPerCustomer

×

AvgOrderValue

```



\### Agent 分析规则



当分析销售额变化时，优先检查：



1\. 客户规模是否变化

2\. 人均订单数是否变化

3\. 客单价是否变化



不要直接假设某一个因素是原因。



应先查询数据进行验证。



\---



\# 六、国家维度分析



\## 1. 国家销售额



```sql

SELECT

&#x20;   Country,

&#x20;   SUM(Amount) AS TotalSales

FROM sales

GROUP BY Country

ORDER BY TotalSales DESC;

```



\---



\## 2. 国家订单数



```sql

SELECT

&#x20;   Country,

&#x20;   COUNT(DISTINCT InvoiceNo) AS OrderCount

FROM sales

GROUP BY Country

ORDER BY OrderCount DESC;

```



\### 重要



禁止使用：



```sql

COUNT(\*)

```



作为国家订单数。



\---



\## 3. 国家客户数



```sql

SELECT

&#x20;   Country,

&#x20;   COUNT(DISTINCT CustomerID) AS CustomerCount

FROM sales

GROUP BY Country

ORDER BY CustomerCount DESC;

```



\---



\## 4. 国家客单价



```sql

SELECT

&#x20;   Country,

&#x20;   ROUND(

&#x20;       SUM(Amount) / COUNT(DISTINCT InvoiceNo),

&#x20;       2

&#x20;   ) AS AvgOrderValue

FROM sales

GROUP BY Country

ORDER BY AvgOrderValue DESC;

```



\---



\## 5. 国家销售额占比



```sql

SELECT

&#x20;   Country,

&#x20;   SUM(Amount) AS TotalSales,

&#x20;   ROUND(

&#x20;       SUM(Amount)

&#x20;       / SUM(SUM(Amount)) OVER () \* 100,

&#x20;       2

&#x20;   ) AS SalesPct

FROM sales

GROUP BY Country

ORDER BY TotalSales DESC;

```



\---



\# 七、商品维度分析



\## 1. 商品销售额



```sql

SELECT

&#x20;   Description,

&#x20;   SUM(Amount) AS TotalSales

FROM sales

GROUP BY Description

ORDER BY TotalSales DESC;

```



\---



\## 2. 商品销量



```sql

SELECT

&#x20;   Description,

&#x20;   SUM(Quantity) AS TotalQuantity

FROM sales

GROUP BY Description

ORDER BY TotalQuantity DESC;

```



\---



\## 3. 商品订单数



```sql

SELECT

&#x20;   Description,

&#x20;   COUNT(DISTINCT InvoiceNo) AS OrderCount

FROM sales

GROUP BY Description

ORDER BY OrderCount DESC;

```



\### 注意



商品订单数表示：



> 包含该商品的不同订单数量



不是该商品的销售明细行数。



\---



\# 八、订单维度分析



\## 1. 单笔订单金额



```sql

SELECT

&#x20;   InvoiceNo,

&#x20;   SUM(Amount) AS OrderAmount

FROM sales

GROUP BY InvoiceNo;

```



\---



\## 2. 大额订单



```sql

SELECT

&#x20;   InvoiceNo,

&#x20;   SUM(Amount) AS OrderAmount

FROM sales

GROUP BY InvoiceNo

ORDER BY OrderAmount DESC;

```



\---



\## 3. 订单商品数量



```sql

SELECT

&#x20;   InvoiceNo,

&#x20;   SUM(Quantity) AS OrderQuantity

FROM sales

GROUP BY InvoiceNo;

```



\---



\# 九、指标对比与变化率



\## 1. 环比增长率



\### 定义



当前周期相对于上一周期的增长比例。



\### 公式



```text

环比增长率

=

(当前值 - 上期值) / 上期值

```



\### SQL示例



```sql

(CurrentValue - PreviousValue) \* 1.0 / PreviousValue

```



\---



\## 2. 同比增长率



\### 定义



当前周期相对于去年同期的增长比例。



\### 公式



```text

同比增长率

=

(当前值 - 去年同期值) / 去年同期值

```



\---



\# 十、异常分析规则



当用户询问：



```text

为什么某个指标下降？

为什么某个指标增长？

为什么某个国家/商品/月份表现异常？

```



Agent 应优先遵循以下分析逻辑：



```text

① 明确指标

↓

② 明确统计周期

↓

③ 查询当前指标

↓

④ 与对比周期进行比较

↓

⑤ 拆解指标

↓

⑥ 找出变化最大的因素

↓

⑦ 按关键维度继续下钻

↓

⑧ 查询数据验证

↓

⑨ 输出结论

```



\---



\# 十一、因果判断规则



仅根据销售交易数据进行分析时：



\### 可以说



```text

与……相关

可能与……有关

主要表现为……

数据表明……

从数据来看……

```



\### 不可以直接说



```text

因为……

导致……

根本原因是……

一定是……

```



除非数据中存在明确的因果识别设计，例如：



\* A/B 实验

\* 随机对照实验

\* 准实验

\* 明确的因果推断设计



否则只能说明相关关系，不能直接认定因果关系。



\---



\# 十二、数据不足时的处理规则



如果现有数据无法支持某个结论，Agent 必须明确说明：



```text

现有数据无法判断。

```



不得自行补充：



\* 行业背景

\* 市场情况

\* 公司战略

\* 用户偏好

\* 营销投入

\* 品牌影响力

\* 渠道情况

\* 竞争对手情况



除非这些信息存在于知识库或数据库中。



\---



\# 十三、SQL 生成强制规则



Agent 生成 SQL 时必须遵守：



\## 规则1：订单数



必须使用：



```sql

COUNT(DISTINCT InvoiceNo)

```



不能使用：



```sql

COUNT(\*)

```



\---



\## 规则2：客户数



必须使用：



```sql

COUNT(DISTINCT CustomerID)

```



\---



\## 规则3：客单价



必须使用：



```sql

SUM(Amount) / COUNT(DISTINCT InvoiceNo)

```



不能使用：



```sql

SUM(Amount) / COUNT(\*)

```



\---



\## 规则4：商品明细行数



如果用户明确询问：



```text

明细行数

商品记录数

商品明细数量

```



才使用：



```sql

COUNT(\*)

```



\---



\## 规则5：销售额



使用：



```sql

SUM(Amount)

```



不要重新计算：



```sql

SUM(Quantity \* UnitPrice)

```



除非 Amount 字段不存在。



\---



\## 规则6：客户相关指标



涉及客户数、复购率、人均销售额等指标时，应注意：



```sql

CustomerID IS NOT NULL

```



\---



\## 规则7：时间分析



涉及：



```text

月

周

日

同比

环比

某个月

某个季度

```



必须首先确认统计时间范围。



时间字段：



```text

InvoiceDate

```



\---



\## 规则8：排序



如果用户询问：



```text

最高

最低

Top N

排名

前几名

```



应使用：



```sql

ORDER BY

```



并根据需求使用：



```sql

LIMIT

```



\---



\# 十四、分析输出规范



最终回答优先采用：



```text

现象

↓

原因/驱动因素

↓

数据证据

↓

建议

```



但需要注意：



如果数据只能证明相关关系，则应写成：



```text

可能驱动因素

```



而不是：



```text

根本原因

```



\---



\# 十五、Agent 分析优先级



当一个问题存在多个可能分析方向时，优先按照以下顺序分析：



\### 第一优先级：指标本身的数学拆解



例如：



```text

销售额

→ 客户数

→ 购买频次

→ 客单价

```



\### 第二优先级：时间维度



例如：



```text

月份

→ 周

→ 日

```



\### 第三优先级：核心业务维度



例如：



```text

国家

商品

客户

订单

```



\### 第四优先级：进一步下钻



只有在前面的分析发现明显异常后，才继续深入分析。



避免无目的地查询大量维度。



\---



\# 十六、核心原则



Agent 必须遵循：



```text

先定义指标

↓

再生成 SQL

↓

先看整体

↓

再做拆解

↓

发现异常

↓

继续下钻

↓

用数据验证

↓

最后总结

```



不要：



```text

先猜原因

↓

再找数据证明

```



应该：



```text

先看数据

↓

发现现象

↓

提出可能解释

↓

查询验证

↓

形成结论

```



