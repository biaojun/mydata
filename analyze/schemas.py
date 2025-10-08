from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional


class Dimension(str, Enum):
    """固定的 9 个评估维度。"""

    correctness = "correctness"
    robustness = "robustness"
    readability = "readability"
    maintainability = "maintainability"
    complexity = "complexity"
    performance = "performance"
    testing = "testing"
    security_dependency = "security_dependency"
    style_consistency = "style_consistency"


@dataclass
class BadCode:
    bad_id: str
    code: str


@dataclass
class TaskInput:
    task_id: str
    language: str
    prompt: str
    good_code: str
    bad_codes: List[BadCode] = field(default_factory=list)


@dataclass
class ScoreDetail:
    good: int
    bad: int
    evidence: Optional[str] = None
    # 模型端不再需要返回 delta；为兼容旧数据保留为可选
    delta: Optional[int] = None


@dataclass
class DiscriminativeKeyword:
    phrase: str
    dimension: Dimension
    weight: float


@dataclass
class PerBadComparison:
    bad_id: str
    dimension_scores: Dict[Dimension, ScoreDetail] = field(default_factory=dict)
    discriminative_keywords: List[DiscriminativeKeyword] = field(default_factory=list)
    # 为兼容旧数据，保留 per-bad 级别的 positive_patterns，但推荐使用任务级 positive_patterns
    positive_patterns: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    actionable_rules_local: List[str] = field(default_factory=list)


@dataclass
class DimensionAggStats:
    mean_delta: float
    median_delta: float
    min_delta: float
    max_delta: float
    consistency: float


@dataclass
class TaskLevelAggregation:
    dimension_agg: Dict[Dimension, DimensionAggStats] = field(default_factory=dict)
    top_positive_patterns: List[str] = field(default_factory=list)
    top_anti_patterns: List[str] = field(default_factory=list)
    aggregated_keywords: List[DiscriminativeKeyword] = field(default_factory=list)
    task_actionable_rules: List[str] = field(default_factory=list)


@dataclass
class ModelOutput:
    task_id: str
    prompt_brief: str
    per_bad_comparisons: List[PerBadComparison] = field(default_factory=list)
    # 新增：任务级别的正向模式，仅生成一次（对应用户需求）。
    positive_patterns: List[str] = field(default_factory=list)
    task_level_agg: Optional[TaskLevelAggregation] = None


# Lightweight helpers for later (placeholders, to be implemented as needed)
def validate_task_input(task: TaskInput) -> None:
    """校验 TaskInput 的必要字段。"""
    if not task.task_id:
        raise ValueError("task_id 不能为空")
    if not task.language:
        raise ValueError("language 不能为空")
    if task.good_code is None:
        raise ValueError("good_code 不能为空（可为空串）")
    if task.bad_codes is None:
        raise ValueError("bad_codes 不能为空列表（可为空列表）")


def to_json_compatible(obj):  # pragma: no cover
    """将数据类/枚举转换为可 JSON 序列化的结构。

    - Enum 转换为其 value
    - dataclass 递归转换
    - 字典若以 Enum 作为键，转换为字符串键
    """
    if obj is None:
        return None
    # Enum
    if isinstance(obj, Enum):
        return obj.value
    # Dataclass
    if is_dataclass(obj):
        d = {}
        for k, v in asdict(obj).items():
            d[k] = to_json_compatible(v)
        return d
    # Dict（处理枚举键）
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key = k.value if isinstance(k, Enum) else str(k)
            out[key] = to_json_compatible(v)
        return out
    # List/Tuple
    if isinstance(obj, (list, tuple)):
        return [to_json_compatible(x) for x in obj]
    # 基本类型
    return obj
