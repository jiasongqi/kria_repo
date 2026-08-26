---
name: jasypt-nacos-spring-boot
description: >-
  Ensures Spring Boot modules decrypt Nacos ENC(...) configs via Jasypt before
  Mongo/Redis/DB beans start. Use when adding a new Spring Boot app/module,
  splitting admin from business, deploying with Nacos encrypted properties,
  or seeing "connection string is invalid" / ENC( literal / MongoURI / Jasypt
  / encryptable properties failures.
---

# Jasypt + Nacos 加密配置（Spring Boot）

Nacos 里若出现 `ENC(...)`，**每个独立启动模块**都必须完整接入 Jasypt。缺任一环 → 密文当明文 → 启动失败。

## 强制清单（新建 / 拆分模块时抄一遍）

对照同仓库已能解密的模块（如 `third-party-business`），新模块必须齐这 4 项：

1. **依赖**（`pom.xml`）
   ```xml
   <dependency>
     <groupId>com.github.ulisesbocchio</groupId>
     <artifactId>jasypt-spring-boot-starter</artifactId>
     <version>3.0.5</version>
   </dependency>
   ```
2. **bootstrap 配置**（`bootstrap.yml` 顶部）
   ```yaml
   jasypt:
     encryptor:
       bootstrap: false
       password: ${JASYPT_ENCRYPTOR_PASSWORD:test}
   ```
3. **启动类**加 `@EnableEncryptableProperties`（`com.ulisesbocchio.jasyptspringboot.annotation`）
4. **部署环境变量** `JASYPT_ENCRYPTOR_PASSWORD` 与加密该密文时的密钥一致

`bootstrap: false` 保留：与 Nacos remote config 解密时序匹配（跟已有 business 模块一致）。

## 症状 → 根因

| 日志 / 现象 | 真实原因 |
|---|---|
| Mongo: `Connection strings must start with either 'mongodb://' or 'mongodb+srv://'` | URI 仍是 `ENC(...)` 或解密乱码 |
| Redis/DB 认证失败但本地明文配置正常 | 线上 ENC 未解密 |
| 同仓库 business 正常、admin 挂 | admin 缺 jasypt 依赖/注解/bootstrap |

堆栈常停在 `mongo` / `mongoTemplate` / 某个 `*Mapper` 注入失败——那是**连带症状**，先查 URI 是否仍带 `ENC(`。

## Agent 操作规则

- 新增 Spring Boot 启动模块、或从已有模块拆出 `*-admin` / `*-api`：**先 diff 同仓库可启动模块的 jasypt 三件套**，再写业务代码。
- 排查「连接串非法 / 配置像乱码」：**先搜 `ENC(` + 模块是否有 jasypt**，不要先改 Mongo 地址。
- 修完后提醒：部署需带正确的 `JASYPT_ENCRYPTOR_PASSWORD`；密钥错也会得到非法 URI。
- 不要把解密后的真实连接串写进 skill、commit message 或聊天记录。

## 真实案例（third-party-admin）

- Nacos：`spring.data.mongodb.uri: ENC(...)`
- admin 缺 jasypt → `ConnectionString` 校验失败 → `batchListMapper` / `mongoTemplate` 创建失败
- 按 business 补齐依赖 + bootstrap + `@EnableEncryptableProperties` 后恢复

## 自检命令

在目标模块根目录：

```bash
rg -n "jasypt|EnableEncryptableProperties|ENC\\(" pom.xml src/main
```

期望：`pom.xml` 有 starter；`bootstrap.yml` 有 `jasypt.encryptor`；`*Application.java` 有注解。若 Nacos/共享配置含 `ENC(` 而上述任一缺失 → 视为部署阻断缺陷。
