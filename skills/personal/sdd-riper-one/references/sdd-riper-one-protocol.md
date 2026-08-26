# SDD-RIPER-ONE Protocol

> SDD-RIPER-ONE 是以规格文档（Spec）为中心的严格工程流程协议，用于解决 LLM 代码生成中"先行动后思考"的关键风险。

---

## 核心法则：Spec-Centric Universe

| 法则 | 说明 |
|:---|:---|
| **单一真相源** | Spec 文件优先于对话历史；冲突时以 Spec 为准 |
| **无 Spec 不编码** | 未定义 Spec 禁止编写代码 |
| **反向同步** | 发现 Bug 时先更新 Spec，再修复代码 |
| **自动持久化** | 生成/修改 Spec 后立即保存到磁盘，无需用户确认 |
| **重载再行动** | 执行前必须从磁盘重新读取 Spec，防止上下文衰减 |

---

## RIPER 状态机（五阶段流程）

```
Pre-Research → Research → [Innovate] → Plan → Execute → Review
     ↑___________________________________________|
```

| 阶段 | 核心动作 |
|:---|:---|
| **0. Pre-Research** | 路径选择：Standard Flow vs Fast Flow |
| **1. Research** | 分析需求、生成/加载 CodeMap、构建上下文包、识别未知项 |
| **2. Innovate**（可选） | 复杂度分析、权衡利弊、架构策略 |
| **3. Plan** | 创建"像素级"蓝图：文件变更、函数签名、执行清单 |
| **3.5 Review Spec**（可选） | 预执行质量检查，GO/NO-GO 建议 |
| **4. Execute** | 严格按 Spec 执行，零偏差；支持单步/批量模式 |
| **5. Review** | 三轴评审：Spec 质量、Spec-代码保真度、代码内在质量 |
| **6. Fast** | 极速通道：跳过 Research/Plan，直接执行简单任务 |

---

## 阶段门禁

| 阶段 | 门禁规则 |
|------|----------|
| RESEARCH | 优先引用 Requirement Source + Codemap + Context |
| INNOVATE | 复杂任务默认 2-3 方案；小任务可跳过但要写明原因 |
| PLAN | 必须包含 File Changes + Signatures + Checklist |
| EXECUTE | 仅在精确字样 `Plan Approved` 后执行 |
| REVIEW | 必须输出 Review Matrix + Overall Verdict；高风险未解决不得收口 |
| ARCHIVE | 默认只归档不删源文件 |

---

## STOP-AND-WAIT 协议

Research → Plan → Execute 各阶段间**必须暂停等待用户指令**。

不允许根据语气、倾向或不完整表述推断 `Plan Approved`。

---

## Spec 文件规范

### 产物路径
```
mydocs/specs/YYYY-MM-DD_hh-mm_<任务名>.md
```

### 最小必填结构（按阶段）

| 阶段 | 必填章节 |
|:---|:---|
| Bootstrap/Research | §0 Open Questions、§1 Requirements、§1.5 Codemap Used、§2 Research Findings、Next Actions |
| Innovate（可选） | §3 Innovate（方案对比与决策） |
| Plan | §4 Plan（文件变更、签名、原子 checklist） |
| Execute | §5 Execute Log |
| Review | §6 Review Verdict、§7 Plan-Execution Diff |
| Closure | §8 Archive Record（推荐） |

---

## MULTI-PROJECT PROTOCOL

### 自动发现
- 触发：`sdd_bootstrap: mode=multi_project` 或触发词 `MULTI / 多项目`
- 自动扫描 workdir 下子目录，通过标志文件识别子项目：
  - JS/TS: `package.json` | Java/Kotlin: `pom.xml`, `build.gradle` | Go: `go.mod`
  - Python: `pyproject.toml`, `setup.py` | Rust: `Cargo.toml` | 通用: `.git`
  - Monorepo: `workspaces`、`settings.gradle`、`pnpm-workspace.yaml`
- 产出 `Project Registry`（`§0.1`），报告给用户确认后继续
- 智能降级：仅 1 个子项目 → 自动降级为单项目模式

### 作用域隔离
- 每轮先声明 `active_project` 与 `active_workdir`
- 默认 `change_scope=local`，只允许修改 `active_project` 下的文件
- 仅在显式 `change_scope=cross` 时允许跨项目改动
- 始终 `codemap-first`：切换到任何项目前，必须先加载该项目的 codemap/context

### 跨项目契约
跨项目改动时，必须在 spec `§4.4 Contract Interfaces` 记录：
```
Provider → Interface → Consumer → 是否 Breaking Change → 迁移方案
```

---

## DEBUG PROTOCOL

### 触发词
`DEBUG / 排查 / 日志分析 / 验证功能`

### 工作流
1. 读取日志文件/目录，提取关键错误、异常、调用链信息
2. 加载关联的 Spec 和 CodeMap（如有），建立"预期行为 vs 实际行为"对照
3. 定位代码中的可疑逻辑
4. 输出结论：Bug 根因分析 / 功能验证报告
5. 如需修复，走 RIPER 流程（Research → Plan → Execute → Review）

### 约束
- Debug 模式本身不直接改代码，只做分析和定位
- 分析结论回写到 Spec 的 `§ Debug Log` 段

---

## 全局约束
1. **语言强制**：所有输出使用**简体中文**（代码、路径、协议头除外）
2. **自动保存**：Spec 修改后立即持久化，禁止仅展示不保存
3. **零偏差执行**：Execute 阶段严格按 Plan 执行，发现偏差立即记录
