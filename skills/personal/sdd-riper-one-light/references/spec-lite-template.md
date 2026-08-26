# Spec Lite Template

> spec 是持久化上下文与压缩记忆层。没有最小 spec，不进入代码实现。

---

## Goal
- 要解决什么问题：
- 验收结果：

## Done Contract
> 保持 1-3 行：什么算完成 + 由什么证明 + 哪些情况仍算未完成

-

## Scope
- In：
- Out：

## Facts / Constraints
- 已确认事实：
- 技术/业务约束：
- 已知风险：

## Open Questions
- [ ]

## Restated Understanding
> 用户输入任务后，先写此区块再进入后续动作

- 我理解当前任务是：
- 当前核心目标是：
- 当前边界是：
- 暂不处理：

## Goal Alignment Check
> 出现日志、测试或人工反馈后，优先更新此区块

- 当前动作是否仍服务于核心目标：
- 若否，偏差在哪里：
- 是否需要调整本轮目标或范围：

## Checkpoint Summary
> 执行前必须填写，明确区分"任务理解"、"核心目标"、"当前进度"

- 当前任务理解：
- 核心目标：
- 当前进度：
- 下一步 1：
- 下一步 2：
- 涉及文件/模块：
- 风险：
- 验证方式：
- Execution Approval: `Pending` / `Approved`

## Change Log
> YYYY-MM-DD: 决策/改动摘要

-

## Validation
- Self-check（自检）：
- Static checks（静态检查）：
- Runtime / Test（运行/测试）：
- Human confirmation（人工确认）：
- 结果汇总：
  - 核心目标是否达成：
  - 剩余差距：
  - 剩余风险：

## Resume / Handoff
- 当前状态：
- 当前卡点：
- 下一步唯一动作：
- 下一轮核心目标：

---

## 使用规则

### 分级使用
| 级别 | 必填区块 |
|------|----------|
| fast | Goal、Done Contract、Restated Understanding、Checkpoint Summary、Approval、Change Log、Validation、Resume/Handoff |
| standard | 补齐全部 |
| deep | 可扩展，但避免写成巨型 spec |

### 执行纪律
- spec 形成或更新后应尽快落盘
- 用户输入任务后，**先写 Restated Understanding**，再进入后续动作
- Done Contract 保持 1-3 行，不写成长计划
- Checkpoint Summary 必须明确区分"任务理解"、"核心目标"、"当前进度"
- 执行前 Execution Approval 置为 Pending，获批后才改为 Approved
- Validation 优先记录外部证据，模型自检只能作为补充
- 暂停、切换任务或准备交接前，必须更新 Resume / Handoff
- 编码前、切换任务前、收尾前，只回读当前相关区块，不要整份重载
