---
name: id-competitor-sentiment
version: "1.0.0"
description: >
  印尼金融竞品舆情分析 Skill。
  LLM 驱动的四层分析框架（本体论→问题类型→方法论→验证输出），
  支持 CSV/Excel/Parquet/JSON/SQLite 多格式数据，
  自动数据质检 + Python 脚本执行 + Markdown/HTML 双格式报告。
  专为 Adapundi & CrediNex 印尼市场风控情报体系设计。
trigger_keywords:
  - 竞品舆情
  - 竞品分析
  - app评分
  - ios竞品
  - 印尼借贷
  - competitor sentiment
  - id sentiment
  - 舆情报告
  - 高危app
  - 还款能力app
base_dir: "~/.workbuddy/skills/id-competitor-sentiment"
---

# 🏦 印尼金融竞品舆情分析 Skill

> **我方产品**：Adapundi & CrediNex（印尼借贷金融产品）
> **分析目标**：竞品 iOS App 评分舆情、用户活跃度、高危 App 风险、还款能力信号

---

## 📌 触发条件

当用户请求以下任意场景时，**立即加载本 Skill**：

- 分析竞品 App 评分 / 评论 / 舆情趋势
- 对比印尼借贷类 App 的市场表现
- 检测高危 App（贷超/博彩/黑产/越狱工具）装机行为
- 评估还款能力类 App（电商/钱包/出行）的用户活跃信号
- 批量处理 CSV/Excel/Parquet/JSON/SQLite 格式的 App 数据
- 生成图文并茂的竞品情报报告

---

## 🧠 四层分析框架

### Layer 1 · 本体论（Ontology）
- **目标**：识别数据来源、字段语义、维度结构
- **动作**：
  1. 调用 `scripts/analyze.py` 的 `detect_format()` 自动识别文件类型
  2. 调用 `ontology_detect(df)` 推断字段语义映射（app_name / rating / review_text / date / app_id）
  3. 加载 `references/apps_config.json` 获取竞品分组信息

### Layer 2 · 问题类型（Problem Classification）
- **目标**：根据字段和用户意图推断分析任务
- **分析任务类型**：
  | 任务 ID | 分析内容 | 触发条件 |
  |---------|----------|----------|
  | `rating_comparison` | 评分竞争对比 | 存在评分字段 |
  | `activity_trend` | 评论量月度趋势 | 存在日期字段 |
  | `sentiment_analysis` | 评论情感分析 | 存在评论文本字段 |
  | `keyword_extraction` | 热门关键词提取 | 存在评论文本字段 |
  | `time_series` | 时序异动检测 | 存在日期字段 |
  | `competitive_landscape` | 竞品格局分布 | 存在 App 名称字段 |
  | `risk_app_detection` | 高危 App 行为检测 | 用户问题含"高危/欺诈/风控" |

### Layer 3 · 方法论（Methodology）
- **评分分析**：均值/标准差/分位数，与我方产品横向对比
- **趋势分析**：月度评论量聚合，滚动均线平滑
- **关键词**：词频统计（含印尼语/英语停用词过滤），无需 NLP 库即可运行
- **情感分析**：优先使用已有 sentiment 字段；无字段时基于关键词词典打分
- **竞品格局**：按 `apps_config.json` 分组（头部借贷/蝌蚪贷/还款能力/高危/工具）

### Layer 4 · 验证输出（Validation & Output）
- **数据质检**：缺失值 + 重复行 + ±3σ 异常值 + 编码乱码 自动检测
- **报告格式**：Markdown + HTML 双格式，含内嵌交互式图表（Plotly 优先，降级 Matplotlib）
- **产物清单**：`report.md` / `report.html` / `*.html 图表` / `summary.json`

---

## 📱 竞品 App 库（来自 references/apps_config.json）

### 1️⃣ 头部借贷竞品（14 款）
| App 名称 | iOS App ID | 类别 |
|----------|-----------|------|
| Easycash | 1435044790 | 借贷 |
| Adakami | 1462715669 | 借贷 |
| Kredivo/Kredifazz | 1255413338 | 借贷 |
| Rupiah Cepat | 1603402758 | 借贷 |
| Kreditpintar | 6444848617 | 借贷 |
| Indodana Finance | 1485395726 | 借贷 |
| KrediOne | 6474530590 | 借贷 |
| Kredito | 1473092902 | 借贷 |
| Cairin | 6447351335 | 借贷 |
| UangMe | 1461448269 | 借贷 |
| Pinjamin | 6477149824 | 借贷 |
| JULO | 6739596452 | 借贷 |
| AmarthaFin | 6446885044 | 借贷 |
| Dana Kini | 1564045377 | 借贷 |

### 2️⃣ 长尾借贷竞品·蝌蚪贷（10 款）
| App 名称 | iOS App ID | 类别 |
|----------|-----------|------|
| Pinjam Yuk | 1350403324 | 蝌蚪贷 |
| Bantusaku | 1619483828 | 蝌蚪贷 |
| Pinjamduit | 6476541604 | 蝌蚪贷 |
| Uatas | 1610701493 | 蝌蚪贷 |
| FINPLUS | 1661244105 | 蝌蚪贷 |
| Samir | 6475002606 | 蝌蚪贷 |
| KTA KILAT | 6472646842 | 蝌蚪贷 |
| UKU | 1488050503 | 蝌蚪贷 |
| Kredinesia | 6444848364 | 蝌蚪贷 |
| Solusiku | 1486755731 | 蝌蚪贷 |

### 3️⃣ 还款能力类 App（17 款）
| App 名称 | iOS App ID | 类别 |
|----------|-----------|------|
| Shopee Indonesia | 959841443 | 电商购物 |
| ShopeePay | 6455990519 | 电子钱包/支付 |
| GoPay | 6446321594 | 电子钱包/支付 |
| DANA | 1437123008 | 电子钱包/支付 |
| Gojek | 944875099 | 出行与外卖 |
| Grab | 647268330 | 出行与外卖 |
| Alfagift | 1013717463 | 电商购物 |
| BRImo BRI | 1439730817 | 金融服务/银行 |
| Livin by Mandiri | 1555414743 | 金融服务/银行 |
| Traveloka | 898244857 | 旅游与订票 |
| Maxim | 579985456 | 出行与外卖 |
| myBCA | 1440241902 | 金融服务/银行 |
| SeaBank | 1525477806 | 金融服务/银行 |
| Access by KAI | 901804734 | 交通与票务 |
| Wondr by BNI | 6499518320 | 金融服务/银行 |
| Superbank | 6444720285 | 金融服务/银行 |
| WhatsApp | — | 社交通讯 |

### 4️⃣ 高危类 App（待补充 iOS ID）

| App 名称 | 类别 | 用途 |
|----------|------|------|
| Pintar Dana | 高危/贷超 | 反欺诈黑名单检测 |
| Dana Rahayu Mobile | 高危/贷超 | 反欺诈黑名单检测 |
| Yuk Uang - Pinjaman Uang Online | 高危/贷超 | 反欺诈黑名单检测 |
| Tunai Darurat - Instant Loan App | 高危/贷超 | 反欺诈黑名单检测 |
| Uang Pintar - Pinjaman Online | 高危/贷超 | 反欺诈黑名单检测 |
| Dompet Tunai - Pinjaman Online | 高危/贷超 | 反欺诈黑名单检测 |

### 5️⃣ 工具类高危 App（越狱/改机）
| App 名称 | 类别 | 用途 |
|----------|------|------|
| Cydia | 越狱工具 | 设备越狱检测 |
| Sileo | 越狱工具 | 设备越狱检测 |
| Royal Dream | 改机/虚拟化 | 设备伪装检测 |
| Neo Party | 改机/虚拟化 | 设备伪装检测 |

> ⚠️ 越狱类 App 通常不在 App Store 上架，以包名/第三方源为主，iOS ID 待补充

---

## 📁 多格式数据支持

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| CSV | `.csv` | 自动检测编码（UTF-8 / UTF-8-BOM / Latin-1 / GBK） |
| Excel | `.xlsx` `.xls` | 自动读取第一个 Sheet |
| Parquet | `.parquet` | 高性能列存格式，推荐大批量数据使用 |
| JSON | `.json` | 支持 records 格式（列表 of dict） |
| SQLite | `.sqlite` `.db` | 自动枚举表名，支持 `--table` 指定 |

---

## 🚀 使用流程（Agent 执行 SOP）

### 场景 A：用户提供了数据文件
```
1. 确认文件路径和格式
2. 询问（或推断）分析目标：评分对比 / 趋势 / 关键词 / 高危检测
3. 执行脚本：
   python ~/.workbuddy/skills/id-competitor-sentiment/scripts/analyze.py \
     <数据文件路径> \
     --output <输出目录> \
     --question "<用户问题>"
4. 展示生成的 report.html 给用户
5. 提供 Markdown 报告摘要
```

### 场景 B：用户要求查询实时竞品数据（无本地文件）
```
1. 使用 AppFollow / data.ai / 七麦数据等渠道思路提示用户获取数据
2. 或使用 web_search 搜索公开评分数据
3. 将搜索结果整理为 JSON / CSV 格式
4. 走场景 A 流程执行分析
```

### 场景 C：用户要求生成竞品情报摘要（无需数据文件）
```
1. 加载 references/apps_config.json 中的竞品配置
2. 结合用户描述的市场信息，生成结构化 Markdown 报告
3. 按分组（头部/蝌蚪/还款能力/高危/工具）输出竞品画像
4. 提供反欺诈策略建议
```

---

## 🛡️ 数据质检规则

| 检测项 | 规则 | 处理方式 |
|--------|------|----------|
| 缺失值 | 任意字段缺失率 > 0% | 报告缺失字段和比例，不自动填充 |
| 重复行 | 完全相同的行 | 报告重复数量，提示用户确认去重 |
| 异常值 | 数值字段超出 ±3σ | 标记异常行，不自动删除 |
| 编码问题 | 出现 \ufffd 或控制字符 | 报告受影响的字段和行数 |

---

## 📊 报告产物

| 文件 | 格式 | 内容 |
|------|------|------|
| `report.md` | Markdown | 完整分析报告（质检 + 评分 + 竞品格局 + 关键词） |
| `report.html` | HTML | 美化版报告，内嵌交互图表 |
| `rating_comparison.html` | Plotly HTML | 评分对比条形图（交互） |
| `group_distribution.html` | Plotly HTML | 竞品分组饼图（交互） |
| `summary.json` | JSON | 机器可读的分析摘要 |

---

## ⚙️ 依赖安装

```bash
# 核心依赖
pip install pandas numpy openpyxl pyarrow

# 图表（推荐）
pip install plotly

# 降级图表（可选）
pip install matplotlib

# SQL 支持
pip install sqlalchemy

# Markdown 转 HTML
pip install markdown

# 全量安装
pip install pandas numpy openpyxl pyarrow plotly matplotlib sqlalchemy markdown
```

---

## 📋 直接使用示例

```bash
# 基础用法：分析 CSV 评分数据
python analyze.py app_reviews.csv

# 指定分析问题（影响任务推断）
python analyze.py reviews.xlsx --question "高危App舆情趋势"

# 自定义输出目录
python analyze.py data.parquet --output ./report_2026_04

# SQLite 数据库
python analyze.py app_data.db --table app_reviews

# 指定 CSV 编码
python analyze.py reviews.csv --encoding gbk
```

---

## 🔄 竞品数据更新说明

- **apps_config.json** 是竞品 App 的单一真实来源（SSOT）
- 高危类 App（第 4 组）和工具类（第 5 组）的 `ios_id` 待补充后更新
- 新增竞品：直接在对应分组的 `apps` 数组追加 JSON 对象即可
- 更新后无需修改分析脚本，自动生效

---

## 📝 踩坑经验

（AI 在实际调用中自动积累，请勿手动删除）

---

*由 WorkBuddy id-competitor-sentiment Skill v1.0.0 生成 · Adapundi & CrediNex 印尼市场情报体系*
