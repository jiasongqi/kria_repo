#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID Competitor Sentiment Analyzer
印尼金融竞品舆情分析核心脚本

四层分析框架：
  Layer 1 - 本体论(Ontology)    : 识别数据来源、字段、维度
  Layer 2 - 问题类型(Problem)   : 分类分析目标（舆情/活跃度/评分/关键词等）
  Layer 3 - 方法论(Methodology) : 选择统计/NLP/时序分析方法
  Layer 4 - 验证输出(Validation): 数据质检 + 报告生成

支持格式：CSV / Excel(.xlsx/.xls) / Parquet / JSON / SQLite
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

# ── 可选依赖（缺失时降级处理）──────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import sqlalchemy
    HAS_SQL = True
except ImportError:
    HAS_SQL = False

# ── 日志 ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("id-competitor-sentiment")

# ── 常量 ───────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
APPS_CONFIG_PATH = SKILL_DIR / "references" / "apps_config.json"
OUR_PRODUCTS = ["Adapundi", "CrediNex"]


# ═══════════════════════════════════════════════════════════════════
# Layer 1 · 本体论 ── 数据加载与字段识别
# ═══════════════════════════════════════════════════════════════════

def load_apps_config() -> dict:
    """加载竞品配置"""
    with open(APPS_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_format(filepath: str) -> str:
    """自动检测文件格式"""
    ext = Path(filepath).suffix.lower()
    format_map = {
        ".csv": "csv", ".xlsx": "excel", ".xls": "excel",
        ".parquet": "parquet", ".json": "json",
        ".sqlite": "sqlite", ".db": "sqlite", ".sql": "sqlite"
    }
    fmt = format_map.get(ext)
    if fmt is None:
        raise ValueError(f"不支持的文件格式: {ext}，支持: {list(format_map.keys())}")
    return fmt


def load_data(source: str, table: str = None, encoding: str = "utf-8") -> pd.DataFrame:
    """
    多格式数据加载器
    source: 文件路径 或 SQLAlchemy连接字符串
    """
    fmt = detect_format(source)
    logger.info(f"[Layer1·本体论] 检测到格式: {fmt.upper()} ← {source}")

    if fmt == "csv":
        # 自动检测编码
        for enc in [encoding, "utf-8-sig", "latin-1", "gbk"]:
            try:
                df = pd.read_csv(source, encoding=enc, low_memory=False)
                logger.info(f"  CSV编码成功: {enc}")
                break
            except (UnicodeDecodeError, Exception):
                continue
        else:
            raise IOError(f"无法解码CSV文件: {source}")

    elif fmt == "excel":
        df = pd.read_excel(source, sheet_name=0)

    elif fmt == "parquet":
        df = pd.read_parquet(source)

    elif fmt == "json":
        df = pd.read_json(source, orient="records")

    elif fmt == "sqlite":
        if not HAS_SQL:
            raise ImportError("SQLAlchemy 未安装，无法读取SQL数据库")
        engine = sqlalchemy.create_engine(f"sqlite:///{source}")
        if table:
            df = pd.read_sql_table(table, engine)
        else:
            # 自动取第一张表
            from sqlalchemy import inspect as sql_inspect
            inspector = sql_inspect(engine)
            tables = inspector.get_table_names()
            if not tables:
                raise ValueError("数据库中没有找到任何表")
            logger.info(f"  数据库表列表: {tables}，自动使用: {tables[0]}")
            df = pd.read_sql_table(tables[0], engine)

    logger.info(f"  加载完成: {len(df)} 行 × {len(df.columns)} 列")
    logger.info(f"  字段列表: {list(df.columns)}")
    return df


def ontology_detect(df: pd.DataFrame) -> dict:
    """
    自动推断字段语义（本体论层）
    返回字段映射字典，例如:
      { "app_name_col": "app_name", "rating_col": "score", ... }
    """
    cols_lower = {c: c.lower() for c in df.columns}
    mapping = {}

    # App名称
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["app", "name", "app_name", "应用", "应用名"]):
            mapping["app_name_col"] = col
            break

    # 评分
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["rating", "score", "star", "评分", "分数"]):
            mapping["rating_col"] = col
            break

    # 评论数量
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["review_count", "reviews", "comment_count", "评论数", "评价数"]):
            mapping["review_count_col"] = col
            break

    # 评论内容
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["review", "comment", "content", "text", "评论", "内容"]):
            if col != mapping.get("review_count_col"):
                mapping["review_text_col"] = col
                break

    # 日期
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["date", "time", "updated", "日期", "时间"]):
            mapping["date_col"] = col
            break

    # App ID
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["app_id", "appid", "ios_id", "bundle"]):
            mapping["app_id_col"] = col
            break

    # 情感
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["sentiment", "emotion", "情感", "情绪"]):
            mapping["sentiment_col"] = col
            break

    logger.info(f"[Layer1·本体论] 字段语义映射: {mapping}")
    return mapping


# ═══════════════════════════════════════════════════════════════════
# Layer 2 · 问题类型分类
# ═══════════════════════════════════════════════════════════════════

def classify_problem(df: pd.DataFrame, mapping: dict, question: str = "") -> list:
    """
    根据数据字段和用户问题，推断分析类型
    返回分析任务列表
    """
    tasks = []

    if mapping.get("rating_col"):
        tasks.append("rating_comparison")       # 评分对比
    if mapping.get("review_count_col"):
        tasks.append("activity_trend")          # 活跃度趋势
    if mapping.get("review_text_col"):
        tasks.append("sentiment_analysis")      # 情感分析
        tasks.append("keyword_extraction")      # 关键词提取
    if mapping.get("date_col"):
        tasks.append("time_series")             # 时序分析
    if mapping.get("app_name_col"):
        tasks.append("competitive_landscape")   # 竞品格局分析

    # 检测高危App相关词汇
    if any(w in question.lower() for w in ["高危", "欺诈", "风控", "blacklist", "fraud"]):
        tasks.append("risk_app_detection")

    logger.info(f"[Layer2·问题类型] 识别到分析任务: {tasks}")
    return tasks


# ═══════════════════════════════════════════════════════════════════
# Layer 3 · 方法论 ── 具体分析实现
# ═══════════════════════════════════════════════════════════════════

def analyze_rating_comparison(df: pd.DataFrame, mapping: dict, config: dict) -> dict:
    """评分对比分析"""
    app_col = mapping.get("app_name_col")
    rating_col = mapping.get("rating_col")
    if not (app_col and rating_col):
        return {}

    df_clean = df[[app_col, rating_col]].dropna()
    df_clean[rating_col] = pd.to_numeric(df_clean[rating_col], errors="coerce")
    stats = df_clean.groupby(app_col)[rating_col].agg(["mean", "count", "std"]).round(3)
    stats.columns = ["平均评分", "评论数", "评分标准差"]
    stats = stats.sort_values("平均评分", ascending=False)

    # 标记我们的产品
    stats["产品类型"] = stats.index.map(
        lambda x: "🏠 我方" if any(p.lower() in str(x).lower() for p in OUR_PRODUCTS) else "🆚 竞品"
    )

    return {"rating_stats": stats, "best_app": stats.index[0], "worst_app": stats.index[-1]}


def analyze_activity_trend(df: pd.DataFrame, mapping: dict) -> dict:
    """活跃度趋势分析（评论量时序）"""
    app_col = mapping.get("app_name_col")
    date_col = mapping.get("date_col")
    if not (app_col and date_col):
        return {}

    df_clean = df[[app_col, date_col]].dropna()
    try:
        df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors="coerce")
        df_clean = df_clean.dropna(subset=[date_col])
        df_clean["month"] = df_clean[date_col].dt.to_period("M")
        monthly = df_clean.groupby([app_col, "month"]).size().reset_index(name="评论量")
        return {"monthly_activity": monthly}
    except Exception as e:
        logger.warning(f"活跃度趋势分析异常: {e}")
        return {}


def analyze_keywords(df: pd.DataFrame, mapping: dict, top_n: int = 20) -> dict:
    """关键词频率分析（不依赖NLP库，基于词频统计）"""
    text_col = mapping.get("review_text_col")
    app_col = mapping.get("app_name_col")
    if not text_col:
        return {}

    # 印尼语/英语停用词
    stopwords = {
        "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
        "tidak", "ada", "the", "a", "an", "is", "in", "of", "to", "and",
        "app", "aplikasi", "saya", "aku", "nya", "pake", "bisa", "sudah",
        "juga", "tapi", "sangat", "banget", "sekali", "kalau", "karena"
    }

    results = {}
    groups = df.groupby(app_col) if app_col else {"all": df}
    for name, group in (groups if isinstance(groups, dict) else groups):
        texts = group[text_col].dropna().astype(str).str.lower()
        words = texts.str.split().explode()
        words = words[~words.isin(stopwords) & (words.str.len() > 2)]
        freq = words.value_counts().head(top_n)
        results[name] = freq

    return {"keyword_freq": results}


def analyze_competitive_landscape(df: pd.DataFrame, mapping: dict, config: dict) -> dict:
    """竞品格局分析——结合配置文件，按分组标注"""
    app_col = mapping.get("app_name_col")
    if not app_col:
        return {}

    all_apps = df[app_col].unique()
    group_map = {}

    # 从配置文件做映射
    for grp_key, grp_val in config.get("competitor_groups", {}).items():
        for app_info in grp_val.get("apps", []):
            group_map[app_info["name"].lower()] = {
                "group": grp_val["label"],
                "category": app_info["category"]
            }

    def get_group(name):
        name_lower = str(name).lower()
        for k, v in group_map.items():
            if k in name_lower or name_lower in k:
                return v["group"], v["category"]
        if any(p.lower() in name_lower for p in OUR_PRODUCTS):
            return "🏠 我方产品", "借贷"
        return "❓ 未分类", "未知"

    df_copy = df.copy()
    df_copy["竞品分组"] = df_copy[app_col].apply(lambda x: get_group(x)[0])
    df_copy["应用类别"] = df_copy[app_col].apply(lambda x: get_group(x)[1])
    group_summary = df_copy.groupby("竞品分组").size().reset_index(name="数据条数")

    return {"landscape_df": df_copy, "group_summary": group_summary}


# ═══════════════════════════════════════════════════════════════════
# Layer 4 · 验证输出 ── 数据质检 + 报告生成
# ═══════════════════════════════════════════════════════════════════

def data_quality_check(df: pd.DataFrame) -> dict:
    """自动数据质检"""
    report = {
        "total_rows": len(df),
        "total_cols": len(df.columns),
        "missing": {},
        "duplicates": 0,
        "anomalies": {},
        "encoding_issues": []
    }

    # 缺失值检测
    missing = df.isnull().sum()
    report["missing"] = {
        col: {"count": int(cnt), "pct": round(cnt / len(df) * 100, 2)}
        for col, cnt in missing.items() if cnt > 0
    }

    # 重复行检测
    report["duplicates"] = int(df.duplicated().sum())

    # 异常值检测（数值列±3σ）
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if len(series) > 10:
            z_scores = (series - series.mean()) / (series.std() + 1e-9)
            anomaly_count = int((np.abs(z_scores) > 3).sum())
            if anomaly_count > 0:
                report["anomalies"][col] = {
                    "count": anomaly_count,
                    "pct": round(anomaly_count / len(series) * 100, 2),
                    "range": f"[{series.min():.2f}, {series.max():.2f}]"
                }

    # 编码问题检测（字符串列）
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().astype(str)
        weird = sample[sample.str.contains(r"[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]", regex=True)]
        if len(weird) > 0:
            report["encoding_issues"].append({"col": col, "affected_rows": len(weird)})

    logger.info(f"[Layer4·质检] 总行数:{report['total_rows']} 重复:{report['duplicates']} "
                f"缺失字段:{len(report['missing'])} 异常值字段:{len(report['anomalies'])}")
    return report


def generate_charts(results: dict, output_dir: Path) -> list:
    """生成图表，优先 Plotly（交互式），降级 Matplotlib（静态）"""
    chart_files = []

    if HAS_PLOTLY:
        # 评分对比条形图
        if "rating_stats" in results.get("rating_comparison", {}):
            stats = results["rating_comparison"]["rating_stats"]
            fig = px.bar(
                stats.reset_index(),
                x=stats.index.name or "index",
                y="平均评分",
                color="产品类型",
                title="竞品 App 平均评分对比（印尼借贷市场）",
                color_discrete_map={"🏠 我方": "#FF4B4B", "🆚 竞品": "#636EFA"},
                height=500,
                text="平均评分"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_tickangle=-45)
            fpath = output_dir / "rating_comparison.html"
            fig.write_html(str(fpath))
            chart_files.append(str(fpath))

        # 分组舆情量饼图
        if "group_summary" in results.get("competitive_landscape", {}):
            gs = results["competitive_landscape"]["group_summary"]
            fig = px.pie(gs, names="竞品分组", values="数据条数",
                         title="竞品舆情数据分布（按分组）",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fpath = output_dir / "group_distribution.html"
            fig.write_html(str(fpath))
            chart_files.append(str(fpath))

    elif HAS_MPL:
        # 降级：Matplotlib 静态图
        if "rating_stats" in results.get("rating_comparison", {}):
            stats = results["rating_comparison"]["rating_stats"]
            fig, ax = plt.subplots(figsize=(14, 6))
            colors = ["#FF4B4B" if "我方" in t else "#636EFA"
                      for t in stats["产品类型"].values]
            ax.bar(stats.index, stats["平均评分"], color=colors)
            ax.set_title("竞品 App 平均评分对比（印尼借贷市场）")
            ax.set_xlabel("App 名称")
            ax.set_ylabel("平均评分")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            fpath = output_dir / "rating_comparison.png"
            plt.savefig(str(fpath), dpi=150)
            plt.close()
            chart_files.append(str(fpath))

    return chart_files


def generate_markdown_report(
    df: pd.DataFrame,
    quality: dict,
    results: dict,
    chart_files: list,
    output_dir: Path,
    input_source: str
) -> str:
    """生成 Markdown 格式报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 🏦 印尼竞品舆情分析报告",
        f"\n> **生成时间**: {now}  ",
        f"> **数据来源**: `{input_source}`  ",
        f"> **我方产品**: {', '.join(OUR_PRODUCTS)}",
        "\n---\n",
        "## 📋 一、数据概览",
        f"- **总行数**: {quality['total_rows']:,}",
        f"- **总列数**: {quality['total_cols']}",
        f"- **重复行**: {quality['duplicates']} 行",
    ]

    # 缺失值
    if quality["missing"]:
        lines.append("\n### 缺失值情况")
        lines.append("| 字段 | 缺失数 | 缺失率 |")
        lines.append("|------|--------|--------|")
        for col, info in quality["missing"].items():
            lines.append(f"| {col} | {info['count']:,} | {info['pct']}% |")

    # 异常值
    if quality["anomalies"]:
        lines.append("\n### ⚠️ 异常值检测（±3σ）")
        lines.append("| 字段 | 异常数 | 异常率 | 数值范围 |")
        lines.append("|------|--------|--------|----------|")
        for col, info in quality["anomalies"].items():
            lines.append(f"| {col} | {info['count']} | {info['pct']}% | {info['range']} |")

    # 编码问题
    if quality["encoding_issues"]:
        lines.append("\n### 🔠 编码异常字段")
        for ei in quality["encoding_issues"]:
            lines.append(f"- `{ei['col']}`: {ei['affected_rows']} 行存在编码乱码")

    # 评分对比
    if "rating_comparison" in results and "rating_stats" in results["rating_comparison"]:
        stats = results["rating_comparison"]["rating_stats"]
        lines.append("\n---\n")
        lines.append("## ⭐ 二、评分竞争分析")
        lines.append("\n" + stats.reset_index().to_markdown(index=False))
        best = results["rating_comparison"].get("best_app", "N/A")
        lines.append(f"\n🏆 **评分最高**: {best}")

    # 竞品格局
    if "competitive_landscape" in results and "group_summary" in results["competitive_landscape"]:
        gs = results["competitive_landscape"]["group_summary"]
        lines.append("\n---\n")
        lines.append("## 🗺️ 三、竞品格局分布")
        lines.append("\n" + gs.to_markdown(index=False))

    # 关键词
    if "keywords" in results and "keyword_freq" in results["keywords"]:
        lines.append("\n---\n")
        lines.append("## 🔑 四、热门关键词 Top 20")
        for app_name, freq in list(results["keywords"]["keyword_freq"].items())[:5]:
            lines.append(f"\n**{app_name}**")
            lines.append("| 关键词 | 频次 |")
            lines.append("|--------|------|")
            for word, cnt in freq.items():
                lines.append(f"| {word} | {cnt} |")

    # 图表附件
    if chart_files:
        lines.append("\n---\n")
        lines.append("## 📊 五、可视化图表")
        for cf in chart_files:
            fname = Path(cf).name
            lines.append(f"- [{fname}](./{fname})")

    # 结论
    lines.append("\n---\n")
    lines.append("## 💡 六、分析结论与建议")
    lines.append("\n> ⚠️ 以下为模板占位，请根据实际分析数据补充专家结论\n")
    lines.append("1. **评分竞争**: 建议重点关注评分领先竞品的功能差异")
    lines.append("2. **舆情监控**: 高危类App（贷超/博彩）的舆情需每周更新，用于反欺诈策略")
    lines.append("3. **还款能力类App**: 关注Shopee/GoPay/DANA的月活变化，作为用户信用代理指标")
    lines.append("4. **越狱/改机工具**: Cydia/Sileo装机率变化需纳入设备风控特征池")

    md_content = "\n".join(lines)
    md_path = output_dir / "report.md"
    md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"[Layer4·输出] Markdown 报告已生成: {md_path}")
    return str(md_path)


def generate_html_report(md_path: str, chart_files: list, output_dir: Path) -> str:
    """将 Markdown 报告转为 HTML（内嵌 chart iframe）"""
    try:
        import markdown
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_body = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc"]
        )
    except ImportError:
        # 降级：简单包装
        with open(md_path, "r", encoding="utf-8") as f:
            raw = f.read().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_body = f"<pre>{raw}</pre>"

    # 内嵌交互式图表 iframe
    chart_iframes = ""
    for cf in chart_files:
        if cf.endswith(".html"):
            fname = Path(cf).name
            chart_iframes += (
                f'<div style="margin:20px 0;">'
                f'<iframe src="./{fname}" width="100%" height="520" '
                f'frameborder="0" scrolling="no"></iframe></div>\n'
            )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>印尼竞品舆情分析报告</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 1100px; margin: 0 auto; padding: 24px; background: #f8f9fa; color: #212529; }}
    h1 {{ color: #0d47a1; border-bottom: 3px solid #1976d2; padding-bottom: 12px; }}
    h2 {{ color: #1565c0; margin-top: 40px; }}
    h3 {{ color: #1976d2; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
    th {{ background: #1976d2; color: white; padding: 10px 14px; text-align: left; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #dee2e6; }}
    tr:hover td {{ background: #e3f2fd; }}
    blockquote {{ border-left: 4px solid #1976d2; margin: 0; padding: 12px 20px;
                  background: #e3f2fd; border-radius: 0 8px 8px 0; }}
    code {{ background: #e8eaf6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
    pre {{ background: #263238; color: #cfd8dc; padding: 16px; border-radius: 8px; overflow-x: auto; }}
    .badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    .badge-ours {{ background: #ffebee; color: #c62828; }}
    .badge-competitor {{ background: #e8eaf6; color: #283593; }}
    .toc {{ background: #fff; padding: 16px 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.08); margin-bottom: 24px; }}
  </style>
</head>
<body>
  {html_body}
  {chart_iframes}
  <footer style="margin-top:60px;padding-top:20px;border-top:1px solid #dee2e6;
                 color:#6c757d;font-size:13px;text-align:center;">
    印尼竞品舆情分析系统 · Adapundi &amp; CrediNex 风控情报平台 · {datetime.now().strftime("%Y")}
  </footer>
</body>
</html>"""

    html_path = output_dir / "report.html"
    html_path.write_text(html, encoding="utf-8")
    logger.info(f"[Layer4·输出] HTML 报告已生成: {html_path}")
    return str(html_path)


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

def run_analysis(
    input_source: str,
    output_dir: str = None,
    table: str = None,
    question: str = "",
    encoding: str = "utf-8"
) -> dict:
    """
    完整四层分析流程
    返回: { "quality": ..., "results": ..., "reports": [...] }
    """
    if output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = str(Path(input_source).parent / f"sentiment_report_{ts}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    config = load_apps_config()

    # Layer 1 · 本体论
    df = load_data(input_source, table=table, encoding=encoding)
    mapping = ontology_detect(df)

    # Layer 2 · 问题分类
    tasks = classify_problem(df, mapping, question)

    # Layer 3 · 方法论执行
    results = {}
    if "rating_comparison" in tasks:
        results["rating_comparison"] = analyze_rating_comparison(df, mapping, config)
    if "activity_trend" in tasks:
        results["activity_trend"] = analyze_activity_trend(df, mapping)
    if "keyword_extraction" in tasks:
        results["keywords"] = analyze_keywords(df, mapping)
    if "competitive_landscape" in tasks:
        results["competitive_landscape"] = analyze_competitive_landscape(df, mapping, config)

    # Layer 4 · 质检 + 输出
    quality = data_quality_check(df)
    chart_files = generate_charts(results, out)
    md_path = generate_markdown_report(df, quality, results, chart_files, out, input_source)
    html_path = generate_html_report(md_path, chart_files, out)

    # 输出 JSON 摘要
    summary = {
        "quality": {k: v for k, v in quality.items() if k not in ["missing", "anomalies", "encoding_issues"]},
        "tasks_executed": tasks,
        "reports": [md_path, html_path] + chart_files,
        "output_dir": str(out)
    }
    summary_path = out / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅ 分析完成！输出目录: {out}")
    print(f"  📄 Markdown 报告: {md_path}")
    print(f"  🌐 HTML   报告: {html_path}")
    for cf in chart_files:
        print(f"  📊 图表: {cf}")
    print(f"{'='*60}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="印尼金融竞品舆情分析 · id-competitor-sentiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze.py reviews.csv
  python analyze.py reviews.xlsx --question "高危App舆情趋势"
  python analyze.py data.parquet --output ./my_report
  python analyze.py app_data.db --table reviews --encoding utf-8
        """
    )
    parser.add_argument("input", help="输入数据文件路径（CSV/Excel/Parquet/JSON/SQLite）")
    parser.add_argument("--output", "-o", default=None, help="输出目录（默认自动生成）")
    parser.add_argument("--table", default=None, help="SQL数据库表名（SQLite专用）")
    parser.add_argument("--question", "-q", default="", help="分析问题（影响任务选择）")
    parser.add_argument("--encoding", default="utf-8", help="CSV编码（默认utf-8）")
    args = parser.parse_args()

    run_analysis(
        input_source=args.input,
        output_dir=args.output,
        table=args.table,
        question=args.question,
        encoding=args.encoding
    )


if __name__ == "__main__":
    main()
