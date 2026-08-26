# Conventions

> 仅在需要落盘 spec / codemap 时查看本文件。不是常驻协议，不应在每轮任务中重复注入。

## 落盘目录

| 类型 | 目录 |
|------|------|
| micro-spec | `mydocs/micro_specs/` |
| standard spec | `mydocs/specs/` |
| codemap | `mydocs/codemap/` |

## 文件命名格式

```
时间前缀：YYYY-MM-DD_hh-mm_

micro-spec:   mydocs/micro_specs/YYYY-MM-DD_hh-mm_<TaskName>.md
standard spec: mydocs/specs/YYYY-MM-DD_hh-mm_<TaskName>.md
codemap:      mydocs/codemap/YYYY-MM-DD_hh-mm_<TaskName>.md
```

## micro-spec vs 正式 spec 分流规则

### 使用 micro-spec（fast 级别）
- 小范围代码修改
- 单文件或少量文件改动
- 需求相对明确
- 不需要显式方案权衡

### 升级为正式 spec（standard / deep 级别）
- 架构设计或大范围重构
- 跨模块/跨项目任务
- 复杂迁移
- 需求模糊，需要方案权衡
- 需要显式评审与回写

## TaskName 命名建议
- 使用简短英文、拼音或稳定短语
- 聚焦任务目标，不写长句
- 一个文件名只表达一个主要任务

## 重要原则
1. spec 是真相源，不是聊天记录转储
2. codemap 是索引，不是源码拷贝
3. 默认优先使用 micro-spec
