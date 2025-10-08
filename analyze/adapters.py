"""适配器：将你的 JSONL 记录映射为内部 TaskInput。

输入记录约定：
- 字段名：
  - task: str                      -> 映射为 prompt
  - good_code: list[str] (1 个元素) -> 取第一个作为 good_code
  - bad_code:  list[str] (1~3 个)   -> 逐个生成 BadCode（bad_id: b1..bN）
- 可选：task_id、language（如未提供将使用默认或生成）
"""

from __future__ import annotations

from typing import Iterable, List, Optional
import uuid as _uuid

from .schemas import TaskInput, BadCode


def _as_list_str(value) -> List[str]:
    """将输入值规范化为字符串列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def record_to_task_input(
    rec: dict,
    *,
    idx: Optional[int] = None,
    default_language: str = "python",
) -> TaskInput:
    """将单条 JSONL 记录转换为 TaskInput。

    优先使用记录内的 task_id / language；缺失时回退：
    - task_id: 若提供 idx 则为 f"T{idx:04d}"，否则使用 UUID4
    - language: 使用 default_language 参数
    """
    if "task" not in rec:
        raise KeyError("记录缺少必需字段: task")

    good_list = _as_list_str(rec.get("good_code"))
    bad_list = _as_list_str(rec.get("bad_code"))

    # 任务 ID 与语言
    task_id = str(rec.get("task_id") or (f"T{idx:04d}" if idx is not None else _uuid.uuid4().hex[:8]))
    language = str(rec.get("language") or default_language)

    return TaskInput(
        task_id=task_id,
        language=language,
        prompt=str(rec["task"]),
        good_code=good_list[0] if good_list else "",
        bad_codes=[BadCode(bad_id=f"b{i+1}", code=code) for i, code in enumerate(bad_list)],
    )


def records_to_task_inputs(
    records: Iterable[dict],
    *,
    default_language: str = "python",
) -> List[TaskInput]:
    """批量将记录序列转换为 TaskInput 列表，并自动生成 task_id。"""
    tasks: List[TaskInput] = []
    for i, rec in enumerate(records):
        tasks.append(
            record_to_task_input(
                rec,
                idx=i + 1,
                default_language=default_language,
            )
        )
    return tasks

