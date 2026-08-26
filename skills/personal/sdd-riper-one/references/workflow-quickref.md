# SDD-RIPER Workflow Quick Reference

## 总纲
**核心流程**：`Pre-Research → RIPER`，全程按 SDD 维护 Spec。

---

## 启动顺序（按复杂度）

| 模式 | 命令 |
|------|------|
| 标准流（中大型任务） | `create_codemap → build_context_bundle → sdd_bootstrap` |
| 快速流（小任务/模糊需求） | `sdd_bootstrap` → 按需补 create_codemap/build_context_bundle |

> **RIPER 正式开始于 RESEARCH**：`Research → (Innovate, 可选) → Plan → Execute → Review`

---

## 六个动作的定位

| 动作 | 阶段 | 说明 |
|------|------|------|
| `create_codemap` | Pre-Research | 代码索引（feature 功能级 / project 项目级） |
| `build_context_bundle` | Pre-Research | 需求整理（Lite/Standard 两种输出粒度） |
| `sdd_bootstrap` | RIPER 启动 | 进入 Research 第一步，完成 Pre-Research 收口 |
| `review_spec` | Plan 后 | 建议性预审（不阻塞执行） |
| `review_execute` | Execute 后 | 质量门禁（三轴输出） |
| `archive` | 任务闭环后 | 知识沉淀（human/llm 双视角） |

---

## 产物命名规则（统一时间前缀）

```
create_codemap(feature)  → mydocs/codemap/YYYY-MM-DD_hh-mm_功能.md
create_codemap(project)  → mydocs/codemap/YYYY-MM-DD_hh-mm_项目总图.md
build_context_bundle     → mydocs/context/YYYY-MM-DD_hh-mm__context_bundle.md
sdd_bootstrap           → mydocs/specs/YYYY-MM-DD_hh-mm_<任务名>.md
archive(human)           → mydocs/archive/YYYY-MM-DD_hh-mm__human.md
archive(llm)             → mydocs/archive/YYYY-MM-DD_hh-mm__llm.md
```

⚠️ 时间前缀不可省略，业务名不可擅改

---

## 阶段完成标准（DoD）

| 阶段 | DoD 要求 |
|------|----------|
| **RESEARCH** | 明确需求边界、现状链路、已知风险，写入 spec |
| **INNOVATE** | 完成方案对比与取舍；跳过需写明原因 |
| **PLAN** | 产出文件改动清单、签名变化、原子 checklist |
| **EXECUTE** | 代码改动与 plan 对齐，执行日志回写 spec |
| **REVIEW** | 三轴评审完整 + Overall Verdict + 偏差清单 |

---

## 阶段门禁

| 阶段 | 门禁规则 |
|------|----------|
| RESEARCH | 优先引用 Requirement Source + Codemap + Context |
| INNOVATE | 复杂任务默认 2-3 方案；小任务可跳过 |
| PLAN | 必须包含 File Changes + Signatures + Checklist |
| EXECUTE | 仅在 `Plan Approved` 后执行 |
| REVIEW | 必须输出 Review Matrix + Overall Verdict；高风险项未解决不得收口 |
| ARCHIVE | 默认只归档不删源文件 |

---

## 关键约束
- **No Spec, No Code** — 没有规格说明不写代码
- **Spec is Truth** — 规格说明即真理
- **Reverse Sync** — 反向同步
- **Review FAIL** → 回到 Research/Plan

---

## 多项目协作

### 启动方式
```bash
sdd_bootstrap: mode=multi_project, task=..., goal=..., requirement=...
```

### 多项目触发词
| 触发词 | 作用 |
|--------|------|
| `MULTI` / `多项目` | 进入多项目模式 |
| `CROSS` / `跨项目` | 当前轮 change_scope=cross |
| `SWITCH` / `切换` | 切换 active_project |
| `REGISTRY` / `项目列表` | 显示 Project Registry |
| `SCOPE LOCAL` / `回到本地` | 回到本地作用域 |

---

## 常用触发词汇总

| 触发词 | 功能 |
|--------|------|
| `create_codemap: scope=<范围>` | 输出功能级 codemap |
| `PROJECT MAP` / `MAP ALL` | 输出项目级 codemap |
| `FAST` / `快速` / `>>` | 小改极速通道 |
| `REVIEW SPEC` / `评审规格` | 执行 review_spec |
| `REVIEW EXECUTE` / `代码评审` | 执行 review_execute |
| `ARCHIVE` / `归档` | 执行 archive |
| `DEBUG` / `排查` | Debug 排查模式 |
| `验证功能` | Debug 验证模式 |
