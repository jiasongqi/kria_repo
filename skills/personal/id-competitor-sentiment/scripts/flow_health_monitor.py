#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程健康监控器 - Flow Health Monitor
专为 id-competitor-sentiment 定制

特性：
- 每个步骤都有状态追踪（PENDING/RUNNING/SUCCESS/FAILED/BLOCKED）
- 前置依赖检查：关键步骤失败时自动阻止后续步骤执行
- 清晰错误提示 + 修复建议
- 流程健康评分（0-100）
- 最终健康报告（JSON 输出）

移植自 yamaz49/analyst，并针对印尼竞品舆情分析场景定制步骤配置
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


class StepStatus(Enum):
    """步骤状态"""
    PENDING  = "待执行"
    RUNNING  = "执行中"
    SUCCESS  = "成功"
    FAILED   = "失败"
    SKIPPED  = "跳过"
    BLOCKED  = "被阻塞"   # 前置步骤失败导致无法执行


class StepImportance(Enum):
    """步骤重要性"""
    CRITICAL = "关键"    # 失败则整个流程终止
    REQUIRED = "必需"    # 失败会阻塞后续步骤
    OPTIONAL = "可选"    # 失败不影响后续步骤


@dataclass
class StepResult:
    """步骤执行结果"""
    step_name:   str
    step_number: int
    status:      StepStatus
    importance:  StepImportance
    message:     str = ""
    details:     Dict[str, Any] = field(default_factory=dict)
    error:       Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    timestamp:   str = field(default_factory=lambda: datetime.now().isoformat())


class FlowHealthMonitor:
    """
    流程健康监控器

    追踪每个步骤的执行状态，在失败时提供清晰的错误提示和修复建议。

    印尼竞品舆情分析专属步骤：
      1. load        - 数据加载（多格式 + 编码容错）
      2. ontology    - 数据本体识别（字段语义映射）
      3. validation  - 数据质量校验（缺失/异常/重复/编码）
      4. planning    - 分析方案规划（LLM 提示词生成）
      5. analysis    - 竞品分析执行（评分/关键词/格局/趋势）
      6. charts      - 可视化图表生成（Plotly/Matplotlib）
      7. report      - 报告输出（Markdown + HTML）
    """

    STEPS_CONFIG = {
        "load": {
            "number": 1,
            "name": "数据加载",
            "importance": StepImportance.CRITICAL,
            "dependencies": [],
            "description": "从文件加载数据（CSV/Excel/Parquet/JSON/SQLite），自动编码容错"
        },
        "ontology": {
            "number": 2,
            "name": "数据本体识别",
            "importance": StepImportance.REQUIRED,
            "dependencies": ["load"],
            "description": "识别字段语义（App名/评分/评论/日期/AppID），映射到竞品配置"
        },
        "validation": {
            "number": 3,
            "name": "数据质量校验",
            "importance": StepImportance.REQUIRED,
            "dependencies": ["load"],
            "description": "检查缺失值、重复行、±3σ异常值、编码乱码"
        },
        "planning": {
            "number": 4,
            "name": "分析方案规划",
            "importance": StepImportance.REQUIRED,
            "dependencies": ["ontology", "validation"],
            "description": "根据字段和用户意图推断分析任务组合（评分/趋势/关键词/高危等）"
        },
        "analysis": {
            "number": 5,
            "name": "竞品分析执行",
            "importance": StepImportance.REQUIRED,
            "dependencies": ["planning"],
            "description": "执行评分对比、活跃度趋势、关键词提取、竞品格局、高危检测"
        },
        "charts": {
            "number": 6,
            "name": "可视化图表生成",
            "importance": StepImportance.OPTIONAL,
            "dependencies": ["analysis"],
            "description": "生成交互式 Plotly 图表（降级 Matplotlib 静态图）"
        },
        "report": {
            "number": 7,
            "name": "报告输出",
            "importance": StepImportance.OPTIONAL,
            "dependencies": ["analysis"],
            "description": "生成 Markdown + HTML 双格式竞品舆情报告"
        }
    }

    # ── 错误类型 → 修复建议模板 ────────────────────────────────────────
    ERROR_SUGGESTIONS = {
        "encoding": [
            "文件编码可能不是 UTF-8，尝试 --encoding gbk / gb2312 / latin-1",
            "可先用文本编辑器打开，另存为 UTF-8 格式",
            "如是 Windows Excel 导出的 CSV，通常是 gbk 编码"
        ],
        "parser": [
            "CSV 分隔符可能不是逗号，检查是否为制表符或分号",
            "尝试用文本编辑器确认文件内容",
            "Excel 文件请先另存为 CSV"
        ],
        "permission": [
            "检查文件读取权限",
            "尝试将文件复制到其他目录后再分析"
        ],
        "memory": [
            "数据文件可能过大，尝试先抽样分析（--sample 10000）",
            "使用 Parquet 格式替代 CSV 以节省内存"
        ],
        "missing_col": [
            "数据缺少预期字段，请确认导出的数据包含 App 名称、评分、日期等关键列",
            "检查 apps_config.json 的字段名与实际数据是否一致"
        ],
        "default": [
            "检查文件路径是否正确",
            "确认文件格式是否为支持的格式（CSV/Excel/Parquet/JSON/SQLite）",
            "检查系统内存是否充足"
        ]
    }

    def __init__(self):
        self.step_results: Dict[str, StepResult] = {}
        self.flow_interrupted = False
        self.interrupt_reason = None
        self.health_score = 100

    # ── 核心方法 ──────────────────────────────────────────────────────

    def record_step_start(self, step_id: str) -> bool:
        """
        记录步骤开始，并检查前置依赖。
        返回 True 表示可以执行，False 表示被阻塞。
        """
        if step_id not in self.STEPS_CONFIG:
            return False

        config = self.STEPS_CONFIG[step_id]

        # 检查前置依赖
        for dep in config["dependencies"]:
            dep_result = self.step_results.get(dep)
            if not dep_result:
                self._record_blocked(step_id, f"前置步骤 '{dep}' 尚未执行")
                return False
            if dep_result.status == StepStatus.FAILED:
                self._record_blocked(
                    step_id,
                    f"前置步骤 '{dep}' 执行失败",
                    suggestions=[
                        f"请检查步骤 '{dep}' 的错误信息并修复问题",
                        "修复后重新运行完整流程"
                    ]
                )
                return False
            if dep_result.status == StepStatus.BLOCKED:
                self._record_blocked(
                    step_id,
                    f"前置步骤 '{dep}' 被阻塞，可能是更前置的步骤失败",
                    suggestions=["从流程开始处检查错误并修复"]
                )
                return False

        # 可以执行
        self.step_results[step_id] = StepResult(
            step_name=config["name"],
            step_number=config["number"],
            status=StepStatus.RUNNING,
            importance=config["importance"]
        )
        return True

    def record_step_success(self, step_id: str, message: str = "", details: Dict = None):
        """记录步骤成功"""
        if step_id in self.step_results:
            self.step_results[step_id].status = StepStatus.SUCCESS
            self.step_results[step_id].message = message
            if details:
                self.step_results[step_id].details = details

    def record_step_failure(
        self,
        step_id: str,
        error: str,
        suggestions: List[str] = None,
        is_critical: bool = False
    ):
        """记录步骤失败，自动推断修复建议"""
        if step_id not in self.STEPS_CONFIG:
            return

        config = self.STEPS_CONFIG[step_id]

        # 确保有 step_result 对象（可能 start 没有被调用）
        if step_id not in self.step_results:
            self.step_results[step_id] = StepResult(
                step_name=config["name"],
                step_number=config["number"],
                status=StepStatus.FAILED,
                importance=config["importance"]
            )

        self.step_results[step_id].status = StepStatus.FAILED
        self.step_results[step_id].error = error

        # 自动推断建议（如果没有传入）
        if suggestions is None:
            suggestions = self._infer_suggestions(error)
        self.step_results[step_id].suggestions = suggestions

        # 更新健康分数
        importance = config["importance"]
        if importance == StepImportance.CRITICAL:
            self.health_score -= 50
        elif importance == StepImportance.REQUIRED:
            self.health_score -= 30
        else:
            self.health_score -= 10

        # 关键步骤失败 → 标记流程中断
        if is_critical or importance == StepImportance.CRITICAL:
            self.flow_interrupted = True
            self.interrupt_reason = f"关键步骤 '{config['name']}' 失败: {error}"

    def can_proceed(self, step_id: str) -> bool:
        """检查是否可以执行指定步骤"""
        if step_id not in self.STEPS_CONFIG:
            return False
        config = self.STEPS_CONFIG[step_id]
        for dep in config["dependencies"]:
            dep_result = self.step_results.get(dep)
            if not dep_result or dep_result.status != StepStatus.SUCCESS:
                return False
        return not self.flow_interrupted

    # ── 输出方法 ──────────────────────────────────────────────────────

    def print_flow_status(self, full_report: bool = True):
        """打印流程状态报告（控制台友好格式）"""
        print("\n" + "=" * 70)
        print("📊 竞品舆情分析 · 流程健康监控报告")
        print("=" * 70)

        total = len(self.STEPS_CONFIG)
        success = sum(1 for r in self.step_results.values() if r.status == StepStatus.SUCCESS)
        failed  = sum(1 for r in self.step_results.values() if r.status == StepStatus.FAILED)
        blocked = sum(1 for r in self.step_results.values() if r.status == StepStatus.BLOCKED)

        print(f"\n执行摘要:")
        print(f"  总步骤: {total}")
        print(f"  成功:   {success} ✅")
        print(f"  失败:   {failed} ❌")
        print(f"  被阻塞: {blocked} ⛔")
        print(f"  健康分: {max(0, self.health_score)}/100")

        if self.flow_interrupted:
            print(f"\n⚠️  流程已中断!")
            print(f"   原因: {self.interrupt_reason}")

        if full_report:
            print(f"\n步骤详情:")
            for step_id, cfg in sorted(self.STEPS_CONFIG.items(), key=lambda x: x[1]["number"]):
                result = self.step_results.get(step_id)
                icon, status_text = self._get_status_icon(result)
                imp_icon = {"关键": "🔴", "必需": "🟡", "可选": "⚪"}.get(cfg["importance"].value, "⚪")

                print(f"\n  {icon} 步骤{cfg['number']}: {cfg['name']}")
                print(f"     重要性: {imp_icon} {cfg['importance'].value}")
                print(f"     状态: {status_text}")

                if result:
                    if result.message:
                        print(f"     信息: {result.message}")
                    if result.error:
                        print(f"     错误: {result.error}")
                    if result.suggestions:
                        print(f"     建议:")
                        for i, s in enumerate(result.suggestions, 1):
                            print(f"       {i}. {s}")

        # 最终结论
        print("\n" + "=" * 70)
        if self.flow_interrupted:
            print("🔴 流程执行失败，请查看上述错误信息并修复问题")
            print("=" * 70)
            print("\n问题汇总:")
            for step_id, r in self.step_results.items():
                if r.status == StepStatus.FAILED:
                    print(f"  - {r.step_name}: {r.error}")
            print("\n修复建议:")
            shown = set()
            for r in self.step_results.values():
                if r.status == StepStatus.FAILED:
                    for s in r.suggestions:
                        if s not in shown:
                            print(f"  • {s}")
                            shown.add(s)
        elif success == total:
            print("✅ 流程执行成功！所有步骤已完成")
            print("=" * 70)
        else:
            print(f"🟡 流程部分完成（{success}/{total} 步骤成功）")
            print("=" * 70)
        print()

    def get_final_report(self) -> Dict[str, Any]:
        """获取最终报告（JSON 格式，可保存到文件）"""
        return {
            "health_score": max(0, self.health_score),
            "flow_completed": not self.flow_interrupted,
            "flow_interrupted": self.flow_interrupted,
            "interrupt_reason": self.interrupt_reason,
            "steps_summary": {
                step_id: {
                    "name": r.step_name,
                    "number": r.step_number,
                    "status": r.status.value,
                    "importance": r.importance.value,
                    "message": r.message,
                    "error": r.error,
                    "suggestions": r.suggestions,
                    "timestamp": r.timestamp
                }
                for step_id, r in self.step_results.items()
            }
        }

    # ── 私有方法 ──────────────────────────────────────────────────────

    def _record_blocked(self, step_id: str, reason: str, suggestions: List[str] = None):
        """记录步骤被阻塞"""
        config = self.STEPS_CONFIG[step_id]
        self.step_results[step_id] = StepResult(
            step_name=config["name"],
            step_number=config["number"],
            status=StepStatus.BLOCKED,
            importance=config["importance"],
            message=reason,
            suggestions=suggestions or []
        )
        self.health_score -= 10

    def _infer_suggestions(self, error: str) -> List[str]:
        """根据错误信息关键词推断修复建议"""
        error_lower = error.lower()
        if any(k in error_lower for k in ["encoding", "codec", "unicode", "decode"]):
            return self.ERROR_SUGGESTIONS["encoding"]
        if any(k in error_lower for k in ["parser", "tokeniz", "delimiter"]):
            return self.ERROR_SUGGESTIONS["parser"]
        if any(k in error_lower for k in ["permission", "access", "denied"]):
            return self.ERROR_SUGGESTIONS["permission"]
        if any(k in error_lower for k in ["memory", "memoryerror", "ram"]):
            return self.ERROR_SUGGESTIONS["memory"]
        if any(k in error_lower for k in ["column", "keyerror", "not found"]):
            return self.ERROR_SUGGESTIONS["missing_col"]
        return self.ERROR_SUGGESTIONS["default"]

    @staticmethod
    def _get_status_icon(result: Optional[StepResult]):
        """返回步骤状态对应的图标和文字"""
        if not result:
            return "⏳", "待执行"
        icons = {
            StepStatus.SUCCESS: ("✅", "成功"),
            StepStatus.FAILED:  ("❌", "失败"),
            StepStatus.BLOCKED: ("⛔", "被阻塞"),
            StepStatus.RUNNING: ("🔄", "执行中"),
            StepStatus.SKIPPED: ("⏭️", "跳过"),
            StepStatus.PENDING: ("⏳", "待执行"),
        }
        return icons.get(result.status, ("⏳", "待执行"))


def create_monitor() -> FlowHealthMonitor:
    """快捷创建监控器"""
    return FlowHealthMonitor()
