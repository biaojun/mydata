"""单任务 1vN 分析的编排逻辑（基于 LLM）。"""

from __future__ import annotations

from typing import Iterable, List

from .schemas import ModelOutput, TaskInput
from .prompting import build_1vN_prompt
from .llm_runner import call_model, parse_model_response


def analyze_task(task: TaskInput, model: str = "vllm") -> ModelOutput:
    """对单个任务执行一次性 1vN 分析（通过 LLM）。

    步骤：
    - 由 TaskInput 构造 Prompt；
    - 调用模型一次；
    - 解析响应为 ModelOutput。

    """
    prompt = build_1vN_prompt(task)
    raw = call_model(prompt, model=model)
    return parse_model_response(raw)


def analyze_tasks(tasks: Iterable[TaskInput], model: str = "vllm") -> List[ModelOutput]:
    """批量分析任务，将 TaskInput 序列映射为 ModelOutput 列表。"""
    return [analyze_task(t, model=model) for t in tasks]
