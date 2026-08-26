# SDD Spec Template

> 使用说明：小任务先出首版 Spec，后续按阶段完善。模板提供单项目/多项目两种模式。

---

# [单项目模板]

**Spec 文件路径**：`mydocs/specs/YYYY-MM-DD_hh-mm_<任务名>.md`

---

## §0 Open Questions

> 待解决的关键问题，按优先级排序

- [ ] 问题1：
- [ ] 问题2：

---

## §1 Requirements

### Goal（目标）
-

### In Scope（包含）
-

### Out of Scope（不包含）
-

### Requirement Source
-

---

## §1.5 Codemap Used

> 引用的 codemap 文件路径与版本

-

---

## §1.6 Context Bundle

> 需求上下文快照

-

---

## §2 Research Findings

### 事实与现状
-

### 已知风险
-

### 技术约束
-

---

## §3 Innovate（可选）

> 方案对比与决策，复杂任务提供 2-3 个方案

### 方案 A
-

### 方案 B
-

### 决策与原因
-

---

## §4 Plan (Contract)

> 必须包含：文件变更 + 签名变化 + 原子 checklist

### §4.1 File Changes

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| | | |

### §4.2 Signatures

```
函数/接口签名变化
```

### §4.3 Execution Checklist

- [ ] Step 1：
- [ ] Step 2：
- [ ] Step 3：

### §4.4 Contract Interfaces（跨项目时填写）

| Provider | Interface | Consumer | Breaking Change | 迁移方案 |
|----------|-----------|----------|-----------------|----------|
| | | | | |

**Execution Approval**: `Pending` / `Approved`

---

## §5 Execute Log

> 执行日志，严格按 Plan 执行，发现偏差立即记录

### YYYY-MM-DD hh:mm
- 执行内容：
- 偏差说明（如有）：

---

## §6 Review Verdict

### 三轴评审结果

| 维度 | 结果 | 证据 |
|------|------|------|
| Spec 质量与目标达成 | PASS/FAIL/PARTIAL | |
| Spec-代码一致性 | PASS/FAIL/PARTIAL | |
| 代码自身质量 | PASS/FAIL/PARTIAL | |

**Overall Verdict**: `PASS` / `FAIL`

**Blocking Issues**:
-

---

## §7 Plan-Execution Diff

> 计划与实际执行的差异分析

| 计划项 | 实际执行 | 差异原因 |
|--------|----------|----------|
| | | |

---

## §8 Archive Record（推荐）

> 任务收口后填写，沉淀可复用知识

### 关键决策
-

### 踩坑与教训
-

### 可复用模式
-

---

---

# [多项目模板]

**Spec 文件路径**：`mydocs/specs/YYYY-MM-DD_hh-mm_<任务名>_multi.md`

---

## §0.1 Project Registry

| Project ID | 路径 | 类型 | 标志文件 |
|-----------|------|------|----------|
| | | | |

## §0.2 Multi-Project Config

- active_project：
- change_scope：`local` / `cross`

## §0 Open Questions

- [ ]

## §1 Requirements

（同单项目模板，补充跨项目边界说明）

---

## §4 Plan（多项目版）

### §4.1 File Changes（按项目分组）

**Project: <project-id>**

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| | | |

### §4.4 Contract Interfaces

| Provider | Interface | Consumer | Breaking Change | 迁移方案 |
|----------|-----------|----------|-----------------|----------|
| | | | | |

### §6.1 Touched Projects

| 项目 | 改动文件 | 原因 |
|------|----------|------|
| | | |

---

（其余章节同单项目模板）
