# Java 编码规范 — java.md
> 当你在编写 Java 代码时，加载本文件。
> **双规范并行**：本文件 + `JavaCode.md`（详细规范）同时生效，有冲突以本文件为准。

---

## 📖 规范层级

```
阿里巴巴 Java 开发手册（基础底线）
    ↓ 继承并补充
coding-style.md（通用代码风格）
    ↓ 继承并补充
java.md（本文件，Java 专项规范）
    ↓ 详细实施细则
JavaCode.md（命名、文档、异常处理等细节）
```

---

## 🏗️ 代码结构规范

### 类结构顺序（固定顺序）
```java
public class XxxService {

    // 1. 静态常量
    private static final Logger log = LoggerFactory.getLogger(XxxService.class);
    private static final int MAX_RETRY = 3;

    // 2. 实例变量（@Autowired 注入）
    @Autowired
    private XxxMapper xxxMapper;

    // 3. 构造方法（推荐用构造注入代替字段注入）

    // 4. 公共方法（按业务逻辑分组）

    // 5. 私有方法（被公共方法调用的工具方法）
}
```


---

## 🛡️ 异常处理规范

### 异常分层
```java
// 业务异常：可预期，返回业务错误码给前端
throw new BusinessException(ErrorCode.USER_NOT_FOUND, "用户不存在");

// 系统异常：不可预期，记录日志，返回通用错误
throw new SystemException("数据库连接失败", e);
```

### 异常捕获原则
```java
// ✅ 指定具体异常类型
try {
    userMapper.insert(user);
} catch (DuplicateKeyException e) {
    throw new BusinessException(ErrorCode.USER_ALREADY_EXISTS);
}

// ✅ 需要 catch Exception 时，必须记录日志
try {
    externalService.call();
} catch (Exception e) {
    log.error("调用外部服务失败, param={}", param, e);
    throw new SystemException("外部服务异常", e);
}

// ❌ 禁止：吞异常（catch 后什么都不做）
try { ... } catch (Exception e) { }

// ❌ 禁止：只打 e.getMessage()，丢失堆栈
log.error("error: " + e.getMessage());

// ✅ 正确：传入异常对象，保留完整堆栈
log.error("操作失败, userId={}", userId, e);
```

### 事务与异常
```java
// 必须指定 rollbackFor，否则默认只回滚 RuntimeException
@Transactional(rollbackFor = Exception.class)
public void processOrder(Order order) { ... }
```

---

## 📦 集合使用规范

```java
// 初始化集合时指定容量，避免频繁扩容
List<User> users = new ArrayList<>(expectedSize);
Map<Long, User> userMap = new HashMap<>(users.size() * 2);

// 返回空集合而不是 null
✅ return Collections.emptyList();
❌ return null;

// 判断集合非空用工具类
✅ CollectionUtils.isNotEmpty(list)
❌ list != null && list.size() > 0

// 禁止在循环中修改正在遍历的集合（ConcurrentModificationException）
✅ 用 Iterator 的 remove()，或 removeIf()
❌ for (item : list) { list.remove(item); }
```

---

## 🔤 字符串处理规范

```java
// 字符串拼接用 StringBuilder（循环场景）
✅ StringBuilder sb = new StringBuilder();
   for (String s : list) { sb.append(s); }
❌ String result = "";
   for (String s : list) { result += s; }  // 每次创建新对象

// 判空用 StringUtils
✅ StringUtils.isNotBlank(str)   // 非空且非空白字符串
✅ StringUtils.isEmpty(str)      // null 或 ""
❌ str != null && !str.equals("")

// 字符串比较，常量放前面防 NPE
✅ "expected".equals(variable)
❌ variable.equals("expected")
```

---

## ⏱️ 日期时间规范

```java
// 使用 Java 8+ 日期 API，禁止使用 java.util.Date / Calendar
✅ LocalDateTime.now()
✅ LocalDate.now()
✅ Instant.now()
❌ new Date()
❌ Calendar.getInstance()

// 时间格式化用 DateTimeFormatter（线程安全）
✅ DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
❌ new SimpleDateFormat(...)  // 非线程安全

// 数据库时间字段类型映射
数据库 datetime → Java LocalDateTime
数据库 date     → Java LocalDate
数据库 bigint   → Java Long（时间戳，毫秒）
```

---

## 🔢 数值规范

```java
// 所有金额计算必须用 BigDecimal
✅ BigDecimal fee = amount.multiply(rate).setScale(2, RoundingMode.HALF_UP);
❌ double fee = amount * rate;

// BigDecimal 初始化用 String 构造器
✅ new BigDecimal("0.1")
❌ new BigDecimal(0.1)  // 精度问题：实际值为 0.1000000000000000055511...

// 整数类型选择
主键/ID → Long
状态码  → Integer
标志位  → Boolean
金额(分)→ Long 或 BigDecimal
```

---

## 🔗 详细规范参考

> 更多细节（方法文档格式、泛型使用、线程安全等）参见同目录下的：
> **[JavaCode.md](JavaCode.md)**

---

*与 JavaCode.md 冲突时，以本文件（java.md）为准*
