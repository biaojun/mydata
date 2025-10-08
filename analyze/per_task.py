"""单任务 1vN 分析的编排逻辑（基于 LLM）。"""

from __future__ import annotations

from typing import Iterable, List

from .schemas import ModelOutput, TaskInput
from .prompting import build_1vN_prompt
from .llm_runner import call_model, parse_model_response

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("[提示] 未安装 tqdm，将不显示进度条。安装命令: pip install tqdm")


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


def analyze_tasks(tasks: Iterable[TaskInput], model: str = "vllm", show_progress: bool = True) -> List[ModelOutput]:
    """批量分析任务，将 TaskInput 序列映射为 ModelOutput 列表。
    
    跳过失败的任务（返回 None 的任务不会包含在结果中）。
    
    Args:
        tasks: 任务输入的可迭代对象
        model: OpenAI client 实例
        show_progress: 是否显示进度条（需要安装 tqdm）
    
    Returns:
        成功分析的任务结果列表
    """
    # 转换为列表以获取总数
    tasks_list = list(tasks)
    total = len(tasks_list)
    
    results = []
    success_count = 0
    failed_count = 0
    
    # 创建进度条（如果可用）
    if HAS_TQDM and show_progress:
        iterator = tqdm(tasks_list, desc="分析任务", unit="任务", ncols=100)
    else:
        iterator = tasks_list
        print(f"开始分析 {total} 个任务...")
    
    for i, t in enumerate(iterator, 1):
        result = analyze_task(t, model=model)
        
        if result is not None:
            results.append(result)
            success_count += 1
        else:
            failed_count += 1
        
        # 更新进度条描述
        if HAS_TQDM and show_progress:
            iterator.set_postfix({
                '成功': success_count,
                '失败': failed_count
            })
        elif not HAS_TQDM and i % 10 == 0:
            # 没有 tqdm 时，每 10 个任务打印一次进度
            print(f"进度: {i}/{total} ({i*100//total}%) - 成功: {success_count}, 失败: {failed_count}")
    
    # 最终统计
    print(f"\n任务分析完成！总计: {total}, 成功: {success_count}, 失败: {failed_count}")
    
    return results
