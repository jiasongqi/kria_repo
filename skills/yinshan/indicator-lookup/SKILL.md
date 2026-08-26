---
name: indicator-lookup
description: Look up AP/HC/CN risk variable meaning, calculation logic, Adapter, and runtime SQL. Use when the user asks what a 变量/指标/nid means, how it is calculated, or which Adapter produces it.
---

# AP / HC 变量查询

用 `aiops-mcp` 的 `indicator.*` 工具，不要先翻 Java 或打 DMS。

## 查法

1. 已有 nid：`indicator.describe(nid, product)`。product 为 `HC` / `AP` / `CN`；nid 全局唯一时可省略 product。
2. 只有中文或关键词：`indicator.search(query, product)`，再对命中项 `describe`。
3. 要看源码：用 describe 返回的 `evidence_ref` 调 `indicator.code`。
4. 工具不可用时，先 `indicator.kb_status` / `ping`。不要猜列名或计算口径。

## 怎么读结果

- `coverage=both`：代码和库配置都有，优先信 `calc_logic` + Adapter。
- `in_code_only`：只有 Adapter/注释。
- `in_db_only`：只有 `t_ic_*`；`calc_logic` 往往是 `query_config` 里的 SQL。
- `dict_only`：只有指标字典。

直接回答含义、计算逻辑、Adapter、覆盖态。用户不用指定工具名。
