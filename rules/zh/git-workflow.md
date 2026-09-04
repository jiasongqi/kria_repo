# Git 工作流

> 当你需要提交代码、写 commit message、做分支管理时，加载本文件。
> 完整开发流程（规划、TDD、代码审查）参见 [development-workflow.md](./development-workflow.md)。
> AI 编程规范主入口参见 [RULES.md](./RULES.md)。

## 提交消息格式

```
<type>(<scope>): <subject>

[可选 body]

[可选 footer]
```

### type 类型

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（不新增功能、不修复 bug） |
| `style` | 代码格式调整（不影响逻辑） |
| `docs` | 文档更新 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖变更 |
| `perf` | 性能优化 |
| `ci` | CI 配置变更 |
| `revert` | 回滚 |

### 示例

```
feat(auth): 新增手机号验证码登录功能

fix(order): 修复订单金额计算精度丢失问题
- 将 double 改为 BigDecimal
- 统一金额字段精度为 2 位小数

refactor(user): 提取公共用户校验逻辑到 UserValidator
```

注意：通过 ~/.claude/settings.json 全局禁用归属。

## 分支命名规范

```
feature/<功能描述>       新功能开发
fix/<bug描述>            bug 修复
hotfix/<紧急修复描述>    生产紧急修复
refactor/<重构描述>      代码重构
release/<版本号>         发布准备
```

示例：
- `feature/sms-login`
- `fix/order-amount-precision`
- `hotfix/payment-timeout`

## 提交前检查清单

- [ ] 代码能编译通过
- [ ] 本地自测通过（核心功能跑通）
- [ ] 没有遗留的 System.out.println / console.log 调试代码
- [ ] 没有硬编码的密钥/密码/IP
- [ ] commit message 符合规范
- [ ] 只提交与本次任务相关的文件
- [ ] 不提交 .idea/ target/ node_modules/ 等生成目录

## 禁止事项

- ❌ `fix bug`、`update`、`test` 这类无意义的 commit message
- ❌ 一个 commit 混入多个不相关的修改
- ❌ 直接 push 到 main/master 分支
- ❌ 提交带有密钥、密码的文件

## Pull Request 工作流

创建 PR 时：
1. 分析完整提交历史（不仅是最新提交）
2. 使用 `git diff [base-branch]...HEAD` 查看所有更改
3. 起草全面的 PR 摘要
4. 包含带有 TODO 的测试计划
5. 如果是新分支，使用 `-u` 标志推送
