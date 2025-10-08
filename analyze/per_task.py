"""单任务 1vN 分析的编排逻辑（基于 LLM）。"""

from __future__ import annotations

from typing import Iterable, List

from .schemas import ModelOutput, TaskInput
from .prompting import build_1vN_prompt
from .llm_runner import call_model, parse_model_response


def analyze_task(task: TaskInput, model) -> ModelOutput | None:
    """对单个任务执行一次性 1vN 分析（通过 LLM）。

    步骤：
    - 由 TaskInput 构造 Prompt；
    - 调用模型一次；
    - 解析响应为 ModelOutput。
    
    Returns:
        ModelOutput 或 None（如果调用失败或无法解析）

    """
    prompt = build_1vN_prompt(task)
    raw = call_model(prompt, model=model)
    
    # 如果调用失败（返回 None），直接返回 None
    if raw is None:
        print(f"[跳过] 任务 {getattr(task, 'task_id', 'unknown')} - 无法获得有效响应")
        return None
    
    try:
        return parse_model_response(raw)
    except Exception as e:
        print(f"[错误] 任务 {getattr(task, 'task_id', 'unknown')} - 解析响应失败: {e}")
        return None


def analyze_tasks(tasks: Iterable[TaskInput], model: str = "vllm") -> List[ModelOutput]:
    """批量分析任务，将 TaskInput 序列映射为 ModelOutput 列表。
    
    跳过失败的任务（返回 None 的任务不会包含在结果中）。
    """
    results = []
    for t in tasks:
        result = analyze_task(t, model=model)
        if result is not None:
            results.append(result)
    return results
