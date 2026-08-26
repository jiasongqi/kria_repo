---
name: java-coding-standards
description: >-
  Java coding standards emphasizing single responsibility, short methods, and
  clear layering for Spring Boot services. Use when writing, refactoring, or
  reviewing Java code; when a method grows long; or when the user mentions SRP,
  单一职责, method length, or Java conventions.
---

# Java Coding Standards

Apply these rules whenever writing or refactoring Java (17+ / Spring Boot).

## Method length & single responsibility（强制）

- **一个方法只做一件事**（Single Responsibility）。编排、查缓存、落库、加锁、转换结果不要堆在同一个方法里。
- **公开方法（public）建议 ≤ 20 行**；超过就要拆 private/package 方法或独立类。
- **私有方法建议 ≤ 30 行**；含业务分支的回调/lambda 体也算进“行数”，应抽成命名方法。
- **嵌套超过 2 层**（if / try / lambda）优先抽取方法，而不是继续缩进。
- 公开入口方法只保留：**参数校验 → 调用子步骤 → 组装返回值**。

### 拆法示例

```java
// ❌ BAD — 一个方法里完成校验、缓存、加锁、DB、落库、转换
public String checkWhiteGroup(Long customerId, String deviceId, String filter) {
    // 40+ lines of mixed concerns...
}

// ✅ GOOD — 入口只编排
public String checkWhiteGroup(Long customerId, String deviceId, String filter) {
    validateIdentity(customerId, deviceId);
    var filterEnum = parseFilter(filter);
    var identity = resolveIdentity(customerId, deviceId);
    var entity = resolveEntity(customerId, deviceId, identity, filterEnum);
    return toGroupName(applyFilter(entity.getWhiteGroup(), filterEnum));
}
```

拆分时按职责命名，例如：`validate*` / `parse*` / `resolve*` / `loadOrAssign*` / `saveOrReload*` / `to*`。

## Class & layering

- Controller：极薄，只提取参数并委托 ApplicationService。
- ApplicationService：编排用例，不塞复杂算法。
- Domain Service：业务规则 / 算法。
- Repository：持久化与缓存，不写业务判断。

## General style

- Prefer clarity over cleverness; immutable by default (`final`, records)。
- Fail fast with meaningful exceptions。
- Naming: types PascalCase, methods/fields camelCase, constants UPPER_SNAKE_CASE。
- Prefer `Optional` for maybe-absent finds; avoid `get()` without guard。
- Keep streams short; nested stream pipelines → use plain loops。

## Checklist before finishing a Java change

- [ ] 每个 public 方法是否单一职责、行数可控？
- [ ] 锁内 / 回调内逻辑是否已抽成命名方法？
- [ ] 业务判断是否落在 Domain，而不是 Controller / Repository？
- [ ] 是否避免复制粘贴两份相同算法（能抽公共工具就抽）？
