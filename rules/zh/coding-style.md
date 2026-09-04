# 编码风格

> 当你在编写任何代码时，加载本文件。基础规范遵循**阿里巴巴 Java 开发手册**，本文件为通用约定与项目定制补充。
> Java 专项规范见 [../java/java.md](../java/java.md)。

## 不可变性（关键）

始终创建新对象，永远不要修改现有对象：

```
// 伪代码
错误:  modify(original, field, value) → 就地修改 original
正确: update(original, field, value) → 返回带有更改的新副本
```

原理：不可变数据防止隐藏的副作用，使调试更容易，并启用安全的并发。

> **语言说明**：此规则可能会被语言特定规则覆盖；对于某些语言，该模式可能并不符合惯用写法。

## 文件组织

多个小文件 > 少量大文件：
- 高内聚，低耦合
- 典型 200-400 行，最多 800 行
- 从大模块中提取工具函数
- 按功能/领域组织，而非按类型

## 错误处理

始终全面处理错误：
- 在每一层显式处理错误
- 在面向 UI 的代码中提供用户友好的错误消息
- 在服务器端记录详细的错误上下文
- 永远不要静默吞掉错误

## 输入验证

始终在系统边界验证：
- 处理前验证所有用户输入
- 在可用的情况下使用基于模式的验证
- 快速失败并给出清晰的错误消息
- 永远不要信任外部数据（API 响应、用户输入、文件内容）

## 代码质量检查清单

在标记工作完成前：
- [ ] 代码可读且命名良好
- [ ] 函数很小（<50 行）
- [ ] 文件聚焦（<800 行）
- [ ] 没有深层嵌套（>4 层）
- [ ] 正确的错误处理
- [ ] 没有硬编码值（使用常量或配置）
- [ ] 没有变更（使用不可变模式）

---

## 基础规范来源

> 本项目代码风格以 **[阿里巴巴 Java 开发手册（泰山版）](https://github.com/alibaba/p3c)** 为基准。
> 以下为项目定制的关键摘要和补充约定，与手册冲突时以本文件为准。

## 命名规范

### 通用原则
- 所有命名做到**见名知意**，禁止拼音混用（除专有名词如 `Pinyin`）
- 禁止使用单字母变量（循环计数器 `i/j/k` 除外）
- 禁止使用 `temp`、`obj`、`data`、`info` 等无意义命名

### 类命名
```
✅ UserAccountService    // 业务服务类
✅ OrderQueryController  // 控制器
✅ PaymentStatusEnum     // 枚举类
✅ UserAccountDTO        // 数据传输对象
✅ OrderDO               // 数据库实体（Data Object）
✅ UserConverter         // 转换器
❌ UserInfo              // 过于模糊
❌ ManageUtils           // 动词前置命名混乱
```

### 方法命名
```
获取单个：getXxx()
获取列表：listXxx() / queryXxx()
统计数量：countXxx()
新增：    saveXxx() / createXxx()
修改：    updateXxx()
删除：    removeXxx() / deleteXxx()
判断：    isXxx() / hasXxx() / checkXxx()
```

### 常量命名
```java
// 全大写 + 下划线分隔
public static final int MAX_RETRY_COUNT = 3;
public static final String ORDER_STATUS_PAID = "PAID";

// 禁止魔法值，数字和字符串都必须定义为常量
❌ if (status == 2)
✅ if (status == OrderStatus.APPROVED.getCode())
```

### 包命名
```
com.credinex.account.controller    // 控制层
com.credinex.account.service       // 业务层
com.credinex.account.service.impl  // 业务实现
com.credinex.account.mapper        // 数据访问层
com.credinex.account.domain        // 领域模型（DO/DTO/VO）
com.credinex.account.common        // 公共工具
com.credinex.account.config        // 配置类
```

## 格式规范

### 缩进与空格
- 使用 **4 个空格**缩进，禁止 Tab（IDE 统一配置）
- 运算符两侧各留一个空格：`a = b + c`
- 方法参数逗号后加空格：`method(a, b, c)`
- 左大括号不换行，右大括号独占一行

### 行长度
- 单行不超过 **120 字符**
- 超长时在合适位置换行，换行后缩进 8 个空格

### 空行规范
- 类内方法之间：1 个空行
- 方法内逻辑段之间：1 个空行（不超过 2 个）
- 禁止连续 2 个以上空行

### 大括号
```java
// 即使只有一行也必须加大括号
✅ if (condition) {
       doSomething();
   }

❌ if (condition)
       doSomething();
```

## 注释规范

### 什么时候写注释
```
✅ 复杂业务逻辑（说明"为什么"）
✅ 非直觉的算法或数据结构选择
✅ 外部系统的特殊约定
✅ 已知的限制或 TODO（必须附 owner 和时间）
❌ 翻译代码（说明"是什么"）
❌ 废弃的注释代码块（直接删除）
```

### 类和方法注释（公共 API 必须）
```java
/**
 * 用户账户查询服务
 * <p>
 * 提供账户基本信息查询、余额查询等功能。
 * 涉及金额字段均以分为单位存储，返回时转换为元。
 *
 * @author 贾松琪
 * @since 1.0.0
 */
public class UserAccountService { ... }
```

### 行内注释
```java
// 金额计算必须用 BigDecimal，避免浮点精度问题
BigDecimal amount = new BigDecimal(amountStr);

// TODO(name, 2026-04-03): 待接入风控系统后补充风险校验
```

## 项目特殊约定

### 💰 金额计算（强制）
```java
// 所有涉及金额的计算，必须使用 BigDecimal
✅ BigDecimal total = price.multiply(quantity);
❌ double total = price * quantity;  // 禁止！精度丢失

// 金额比较用 compareTo，不用 equals
✅ amount.compareTo(BigDecimal.ZERO) > 0
❌ amount.equals(BigDecimal.ZERO)
```

### 🗄️ 数据库操作（强制）
```java
// 写操作必须有事务注解
@Transactional(rollbackFor = Exception.class)
public void updateAccount(...) { ... }

// 禁止在循环中查数据库（N+1 问题）
❌ for (Long id : idList) {
       User user = userMapper.selectById(id);  // 禁止！
   }
✅ List<User> users = userMapper.selectBatchIds(idList);
```

### 🔒 敏感操作（强制）
- 删除数据 / 金额调整类操作 → **必须双人 Review 后才能合并**
- 涉及用户隐私字段（身份证/手机号）→ 日志中必须脱敏处理
- 对外接口入参 → 必须做参数校验（`@Valid` + 自定义 Validator）

## 代码坏味道（发现必须指出）

| 坏味道 | 说明 |
|--------|------|
| 方法超过 50 行 | 拆分职责 |
| if-else 嵌套超过 3 层 | 用卫语句/策略模式重构 |
| 同一逻辑出现 2 次以上 | 提取公共方法 |
| 方法参数超过 5 个 | 封装为参数对象 |
| 直接 `catch (Exception e) {}` 吞异常 | 必须记录日志或向上抛出 |
| `System.out.println` 调试代码 | 提交前必须清除 |
