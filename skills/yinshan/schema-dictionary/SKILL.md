---
name: schema-dictionary
description: 说明 AP/HC 表字段含义，以及 AdaPundi banda 常用查询（t_loan_app、t_account、t_lpay、标签）。用户问字段含义、AP/HC 库怎么对应、或要 AP 常用 SQL 时使用。
---

# AP / HC 字段词典

权威副本在 `D:/AI-projuct/aiops-mcp/agent-kit/schema-dictionary/SKILL.md`。AP 常用 SQL：`D:/AI-projuct/aiops-mcp/agent-kit/schema-dictionary/ap-banda-sql.md`。完整字段表在 `D:/AI-projuct/aiops-mcp/agent-kit/schema/dictionary/`。

不要写整库 DDL。含义以 `schema/test/{db}.yaml` 的 `comment` 为准。

## 查法

1. 用业务地图定位库和核心表。
2. 打开 `D:/AI-projuct/aiops-mcp/agent-kit/schema/dictionary/hc_*.md`，或 Grep 同目录上一级的 `schema/test/{db}.yaml`。
3. **禁止猜列名**。写 SQL 走 `/sql-query`。
4. 生产列名以 `hc_get_schema` / `ap_get_schema` 为准。
5. 表怎么 JOIN：按国家分开查。AP：`schema.graph(product="AP", tables=["t_loan_app"], hops=1)`；HC：`product="HC"` + `t_loan_order`。不要把 AP/HC 表连在一起。

## 业务地图

| 域 | HC 库 / 实例 | AP 库 / 实例 | 核心表 |
|---|---|---|---|
| 用户 | `hc_user` | `banda` | AP `t_customer`（`id`=`customer_id`） |
| 订单借还 | `hc_order` | `banda` | AP 主单 `t_loan_app`；资金单 `t_order`；账单 `t_lpay` |
| 额度授信 | `hc_limit` | `banda` | AP `t_account` + `t_customer_product`；机审 `t_auto_review_loan` |
| 风控决策 | `hc_risk_management` | `riskmanagement` | 同名 `t_oc_order` / `t_oc_decision_log` |
| 三方 | `hc_third_party` | `thirdparty` / 印尼风控实例 | 供应商调用流水 |
| 指标特征 | 指标中心 | `lovina` / 印尼风控实例 | 数据源适配结果 |

## 额度速查

- `t_user_limits.borrowed_amount`：当前已借占用
- `max_amount`：最大可借 = total_amount − borrowed_amount
- `t_credit_transaction_log.before_borrowed_amount`：该笔操作前的已借占用
- `t_order_info`：授信单，不是借款单

重新生成：在 agent-kit 根目录执行 `python scripts/gen_field_dictionary.py`。
