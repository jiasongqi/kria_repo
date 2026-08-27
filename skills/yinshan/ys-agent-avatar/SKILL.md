---
name: ys-agent-avatar
description: Ask a colleague's digital avatar or answer inbox questions and grow a personal knowledge base via the ys CLI. Use when asking a coworker, 向同事提问, 数字分身, ys askto, inbox, 知识库沉淀, or when a teammate's question should become a reusable answer.
version: 1.3.0
tags: [ask, avatar, inbox, knowledge-base, cli]
---

# ys-agent 同事数字分身

银闪内部问答闭环：提问人问同事分身；专家回复后自动沉淀知识库，以后同类问题由分身代答。CLI 是本目录的 `ys.py`（纯标准库，跨平台）。下文 `ys` 等于 `python ys.py`。

按用户角色选流程，不要两头都跑：

- **提问人**：问某位同事 / 排查报错要人经验 → [向同事分身提问](#向同事分身提问)
- **被问人**：收件箱有待答、要沉淀知识、校准分身 → [专家回复与知识库沉淀](#专家回复与知识库沉淀)

## 前置条件

1. ys-agent 账号且**已绑定工号**（没绑找管理员在「工号管理」页绑定）。
2. 登录一次，自动续登：

```bash
python ys.py login --phone <手机号或账号> --password <密码>
python ys.py whoami
```

网页端：https://agent-web.adapundi.com （提问 `/ask`，知识库 `/kb`），与 CLI 等价。

---

# 向同事分身提问

把问题丢给同事的**数字分身**：强命中知识库**秒回答案**；接近命中返回**候选清单**；都不合适进他收件箱等真人。Agent 可多轮检索、挑选答案、带截图提问。

## 提问

```bash
python ys.py askto <对方工号> "你的问题"
# 带附件(运维排查标配:截图 + 报错日志):
python ys.py askto YS-000224 "这个报错怎么排查?" --img error.png --file app.log
# 给 agent 程序化消费:
python ys.py askto <工号> "问题" --json
```

知识库按关键词 + bigm 模糊匹配，问题里带上**核心名词**（系统名/报错原文/组件名）命中率最高。

## 三种结果与动作

| askto 返回 | 含义 | 你/agent 该做什么 |
|---|---|---|
| `AUTO_ANSWERED` | 分身强命中,已给答案 | 验证答案 → **必须反馈** `python ys.py feedback <id> helpful\|not`；要真人再答 → `python ys.py inbox escalate <id>` |
| `CANDIDATES` | 接近命中,返回 top-5 候选 | 逐条评估：合适 → `python ys.py pick <id> <kbId>` 采纳；都不合适 → 走下面的检索循环 |
| `PENDING` | 未命中,已进专家收件箱 | 可先走检索循环自助找；找不到就等专家 |

## agent 检索循环（换措辞多试几次，检索无副作用）

```bash
python ys.py kb search "索引 报错" --owner YS-000224 --json
python ys.py kb search "ES 查不到数据" --owner YS-000224 --json
```

- `--owner <工号>` 可检索该专家全部知识（与分身代答同一暴露面）
- 检索到合适条目 → `python ys.py pick <问题id> <kbId>` 采纳（不必来自候选清单，采纳即 hit_count+1）
- 全部落空 → 保持 PENDING 等专家真人回复

## 拉取回答与进度

```bash
python ys.py sent                    # 我提过的所有问题
python ys.py inbox show <id>         # 单条全文(含附件清单)
```

## 反馈（拿到答案后必做，不许静默结束）

```bash
python ys.py feedback <id> helpful
python ys.py feedback <id> not --comment "索引名写错了"
```

`helpful` 确认知识可靠；`not` 会把命中条目标「待复核」，专家会修正。`python ys.py sent` 会持续列出未反馈项。

## 提问端常见问题

- **提示无工号**：找管理员绑定，提问/收件都按工号路由。
- **一直 PENDING**：对方还没回复，钉钉催一下（提问本身不发通知，收件靠对方拉取）。
- **代答/候选都不对**：escalate 或 feedback not。

---

# 专家回复与知识库沉淀

被同事提问时，一条命令拉收件箱；带截图/日志的问题可导出材料目录交给 agent 看图读日志；回复自动沉淀进个人知识库，分身从此替你代答同类问题。**答一次，以后都不用再答。**

## 收到问题

```bash
python ys.py inbox                 # 待答 PENDING / 待挑选 CANDIDATES / 分身已答 AUTO_ANSWERED
```

平台提问不发消息。可用系统定时任务跑 `python ys.py inbox --notify`：有新问题时弹系统原生通知，已见过的不会重复弹。

**Windows**（管理员 CMD，15 分钟一次，路径换成本 skill 里 ys.py 的位置）：

```bat
schtasks /Create /TN "ys inbox" /SC MINUTE /MO 15 /TR "python C:\path\to\ys-agent-avatar\ys.py inbox --notify"
```

**macOS / Linux**：

```
*/15 * * * * /usr/bin/python3 /path/to/ys-agent-avatar/ys.py inbox --notify >/dev/null 2>&1
```

进阶：定时任务发现新问题后，让本地 agent 出草稿，人工过目再 `inbox reply`，不要自动回复。

## 带附件的问题：导出材料，交给 AI agent

```bash
python ys.py inbox show 42 --save-attachments ./q42-materials
```

把目录连同问题交给本地 agent：

> 这是同事的技术提问，materials 目录里有截图和日志。请看图读日志，给出可复用的排查步骤（命令、顺序、结论），我会存入知识库供分身复用。

agent 产出后审一眼再回复——**回复即沉淀**，写清楚点，以后分身原文代答。

## 回复

回复前先查重，避免同一问题两条答案：

```bash
python ys.py kb search "问题关键词"
```

```bash
python ys.py inbox reply <id> "答案(可直接贴 agent 生成的 markdown)"
python ys.py inbox reply <id> "结论…" --img arch.png
```

一条命令三件事：问题转 ANSWERED → 问答自动沉淀知识库（附件引用行自动剥离）→ 分身开始代答同类问题。已有相近条目就 `kb edit` 修正，不要再答一条。

## 分身代答与质量信号

- 再有人问相近问题 → 分身自动答（hits+1）或返回候选由对方 agent 挑选
- 提问人反馈 `not` → 命中条目自动标「待复核」

```bash
python ys.py kb list --status NEEDS_REVIEW
```

## 管理知识库

```bash
python ys.py kb                                  # 我的知识库(hits 即被代答次数)
python ys.py kb search "关键词"                   # 检索验证(我的 + PUBLIC)
python ys.py kb push -q "问题" -a "答案" [--tags es,排查] [--alts "变体1|变体2"]
python ys.py kb show <id>
python ys.py kb show <id> --save out.md
python ys.py kb edit <id> -a "新答案"             # --status ACTIVE 复核生效
python ys.py kb rm <id>
```

## 专家端工作节奏

1. `python ys.py inbox` 当日清 PENDING；带附件的用材料目录 + 本地 agent 提效。
2. 回复写「可复用的答案」，而不是只对当前上下文的碎片。
3. 每周过一遍「待复核」，知识库质量 = 分身质量。
