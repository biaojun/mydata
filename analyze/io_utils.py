"""I/O 工具：读取任务、写出结果（占位）。"""

from __future__ import annotations

from typing import Iterable, List
import json
import os

from .schemas import TaskInput, ModelOutput, to_json_compatible
from .adapters import records_to_task_inputs


def read_tasks_jsonl(path: str) -> List[TaskInput]:
    """从 JSONL 文件读取任务，返回 TaskInput 列表。

    假定每行为 dict，且键包含：task(str)、good_code(list[str])、bad_code(list[str])。
    若存在 task_id/language 字段将沿用；否则自动生成。
    """
    records: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records_to_task_inputs(records)


def write_jsonl(path: str, items: Iterable[object], append: bool = False) -> None:
    """将可 JSON 序列化对象序列写入 JSONL 文件。"""
    mode = "a" if append else "w"
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, mode, encoding="utf-8") as f:
        for obj in items:
            data = to_json_compatible(obj)
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


def ensure_dir(path: str) -> None:
    """确保目录存在（等价于 mkdir -p）。"""
    if not path:
        return
    os.makedirs(path, exist_ok=True)
